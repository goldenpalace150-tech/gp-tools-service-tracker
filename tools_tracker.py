import streamlit as st
import pandas as pd
from datetime import datetime
import re
import io
import requests
import base64
import urllib.parse
from streamlit_gsheets import GSheetsConnection

# ImgBB API Key
IMGBB_API_KEY = "c6e484b83af4bb39c92e1782cc6ce5e6"

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="ERP System - القصر الذهبي", layout="wide", page_icon="🎛️")

st.markdown("""
    <style>
        .stApp { background-color: #f4f6f9; direction: rtl; text-align: right; }
        h1, h2, h3, h4, p, span, label, div { text-align: right; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
        table { width: 100% !important; background-color: white; }
        .tile-button > button { height: 120px !important; border-radius: 15px !important; font-size: 20px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s; }
        .tile-button > button:hover { transform: translateY(-5px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# GOOGLE SHEETS CONNECTION & DATA
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

EXPECTED_COLUMNS = [
    "service_id", "tool_name", "customer_name", "phone_number", 
    "warranty_status", "document_origin", "reported_issue", 
    "technician", "status", "cost_debit", "payment_credit", 
    "balance", "spare_parts", "resolution_notes", "remarks", "date_logged", "date_resolved"
]
STOCK_COLUMNS = ["item_code", "item_name", "quantity", "price"]
HAWARA_COLUMNS = ["order_id", "order_type", "linked_service_id", "courier", "delivery_note", "document_link", "status", "date_logged"]
DISPATCH_COLUMNS = ["dispatch_id", "service_id", "customer_name", "courier", "delivery_note", "document_link", "date"]

def get_status_rank(val):
    s = str(val)
    if "قبض" in s or "Collected" in s: return 4
    if "خ صيانة" in s or "حساب وكيل" in s: return 3
    if "مبيع خ ص" in doc_normalize(s) or "جاهز" in s: return 2
    if "اد خ ص" in doc_normalize(s) or "المعالجة" in s: return 1
    return 0

def doc_normalize(text):
    return re.sub(r'\s+', ' ', str(text)).strip()

def map_document_to_status(doc_string, cost=0.0):
    doc = doc_normalize(doc_string)
    try: cost_val = float(cost)
    except: cost_val = 0.0
    
    if "قبض" in doc: return "تم التسليم للزبون (Customer Collected)"
    if "خ صيانة" in doc: return "تم التسليم - حساب وكيل (Partner Collected)"
    if "مبيع خ ص" in doc: 
        if cost_val == 0.0: return "جاهز للتسليم (بدون تكلفة/كفالة)"
        return "جاهز للتسليم (Ready)"
    if "اد خ ص" in doc: return "قيد المعالجة (In Progress)"
    return "قيد الانتظار"

def deduplicate_ledger(df):
    if df.empty or 'service_id' not in df.columns: return df
    df['rank'] = df['document_origin'].apply(get_status_rank)
    df = df.sort_values(by=['service_id', 'rank'], ascending=[True, True])
    deduped = df.groupby('service_id', as_index=False).last()
    return deduped.drop(columns=['rank'], errors='ignore')

def get_ledger():
    try:
        df = conn.read(worksheet="Ledger", ttl=0)
        for col in EXPECTED_COLUMNS:
            if col not in df.columns: df[col] = ""
        for col in EXPECTED_COLUMNS:
            if col not in ['cost_debit', 'payment_credit', 'balance']:
                df[col] = df[col].fillna("").astype(str).replace({'nan': '', 'None': ''})
        df.loc[df['spare_parts'] == "", 'spare_parts'] = "لا حاجة / متوفرة"
        return deduplicate_ledger(df)
    except: return pd.DataFrame(columns=EXPECTED_COLUMNS)

def save_ledger(df): conn.update(worksheet="Ledger", data=deduplicate_ledger(df))

def get_stock():
    try:
        df = conn.read(worksheet="Stock", ttl=0)
        if df.empty or len(df.columns) < len(STOCK_COLUMNS): return pd.DataFrame(columns=STOCK_COLUMNS)
        return df
    except: return pd.DataFrame(columns=STOCK_COLUMNS)

def save_stock(df): conn.update(worksheet="Stock", data=df)

def get_hawara():
    try:
        df = conn.read(worksheet="Hawara", ttl=0)
        for col in HAWARA_COLUMNS:
            if col not in df.columns: df[col] = ""
        return df
    except: return pd.DataFrame(columns=HAWARA_COLUMNS)

def save_hawara(df): conn.update(worksheet="Hawara", data=df)

def get_dispatch():
    try:
        df = conn.read(worksheet="Dispatch", ttl=0)
        for col in DISPATCH_COLUMNS:
            if col not in df.columns: df[col] = ""
        return df
    except: return pd.DataFrame(columns=DISPATCH_COLUMNS)

def save_dispatch(df): conn.update(worksheet="Dispatch", data=df)

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name='Export')
    return output.getvalue()

def get_branch(s_id):
    if not s_id: return "أخرى"
    char = str(s_id).strip().upper()[0]
    if char == 'S': return "صيدا (Saida)"
    if char == 'D': return "درعا (Daraa)"
    if char == 'V': return "شريك (Partner)"
    return "أخرى"

# ==========================================
# AUTHENTICATION & SESSION STATE
# ==========================================
if 'logged_in_user' not in st.session_state: st.session_state['logged_in_user'] = None
if 'current_module' not in st.session_state: st.session_state['current_module'] = 'Home'

USERS = {"admin": {"pass": "123", "role": "مدير النظام (Admin)"}, "tech": {"pass": "123", "role": "فني صيانة (Technician)"}}

if st.session_state['logged_in_user'] is None:
    st.title("🎛️ نظام إدارة الموارد المتكامل (ERP)")
    st.subheader("🔐 تسجيل الدخول")
    with st.form("login_form"):
        u_in = st.text_input("اسم المستخدم")
        p_in = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            if u_in in USERS and USERS[u_in]["pass"] == p_in:
                st.session_state['logged_in_user'] = u_in
                st.rerun()
            else: st.error("خطأ في البيانات.")
    st.stop()

current_user = st.session_state['logged_in_user']
is_admin = ("Admin" in USERS[current_user]["role"])

live_df = get_ledger()
stock_df = get_stock()
hawara_df = get_hawara()
dispatch_df = get_dispatch()

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("🎛️ القائمة الرئيسية")
st.sidebar.write(f"👤 مرحباً: **{current_user}**")
st.sidebar.divider()

if st.sidebar.button("🏠 لوحة التحكم (Dashboard)", use_container_width=True): st.session_state['current_module'] = 'Home'
if st.sidebar.button("🛠️ قسم الصيانة (Service Desk)", use_container_width=True): st.session_state['current_module'] = 'Services'
if st.sidebar.button("📦 المستودعات (Warehouse)", use_container_width=True): st.session_state['current_module'] = 'Warehouse'
if st.sidebar.button("🚚 اللوجستيات (Logistics)", use_container_width=True): st.session_state['current_module'] = 'Logistics'
if st.sidebar.button("⚙️ النظام والتقارير (Admin & Reports)", use_container_width=True): st.session_state['current_module'] = 'Admin'

st.sidebar.divider()
if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state['logged_in_user'] = None
    st.rerun()

# ==========================================
# MODULE 1: HOME DASHBOARD & ANALYTICS
# ==========================================
if st.session_state['current_module'] == 'Home':
    st.title("🎛️ لوحة التحكم التحليلية (Executive Dashboard)")
    st.write("نظرة عامة على حالة العمليات في القصر الذهبي:")
    
    active_count = len(live_df[~live_df['status'].str.contains('تم التسليم', na=False)]) if not live_df.empty else 0
    ready_count = len(live_df[live_df['status'].str.contains('جاهز', na=False)]) if not live_df.empty else 0
    hawara_pending = len(hawara_df[~hawara_df['status'].str.contains('تم الاستلام', na=False)]) if not hawara_df.empty else 0
    total_rev = float(live_df['cost_debit'].astype(float).sum()) if not live_df.empty else 0.0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 صيانة نشطة", active_count)
    m2.metric("✅ أجهزة جاهزة", ready_count)
    m3.metric("🚚 طلبيات حوارة معلقة", hawara_pending)
    m4.metric("💰 إجمالي المبيعات/التكاليف", f"${total_rev:.2f}")
    st.divider()

    # Visual Analytics Chart
    if not live_df.empty:
        st.subheader("📊 توزع حالات الصيانة الحالية")
        status_counts = live_df['status'].value_counts()
        st.bar_chart(status_counts)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="tile-button">', unsafe_allow_html=True)
        if st.button("🛠️\nالصيانة\n(Service Desk)", use_container_width=True):
            st.session_state['current_module'] = 'Services'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="tile-button">', unsafe_allow_html=True)
        if st.button("📦\nالمستودعات\n(Warehouse)", use_container_width=True):
            st.session_state['current_module'] = 'Warehouse'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="tile-button">', unsafe_allow_html=True)
        if st.button("🚚\nالشحن والتوريد\n(Logistics)", use_container_width=True):
            st.session_state['current_module'] = 'Logistics'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="tile-button">', unsafe_allow_html=True)
        if st.button("⚙️\nالتقارير والإدارة\n(Admin & Reports)", use_container_width=True):
            st.session_state['current_module'] = 'Admin'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# MODULE 2: SERVICE DESK 
# ==========================================
elif st.session_state['current_module'] == 'Services':
    st.title("🛠️ قسم الصيانة (Service Desk)")
    tab1, tab2, tab3 = st.tabs(["📥 استلام جهاز", "🔧 تحديث وتسليم", "⏱️ المتابعة والتأخير"])
    
    with tab1:
        with st.form("intake_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                s_id = st.text_input("رقم السند (S صيدا / D درعا / V وكيل)")
                c_name = st.text_input("اسم الزبون")
            with c2:
                c_phone = st.text_input("رقم الهاتف")
                t_name = st.text_input("كود/اسم الأداة")
            with c3:
                doc_origin = st.selectbox("أصل السند", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "خ صيانة: (تحميل على الوكيل)"])
                spare_parts = st.selectbox("حالة قطع الغيار", ["لا حاجة / متوفرة", "بانتظار شحن مجاني (Free Shipment)", "بانتظار شحن عادي (Normal Shipment)"])
                
            c4, c5 = st.columns(2)
            with c4: issue = st.text_input("العطل المرصود")
            with c5: remarks = st.text_input("ملاحظات إضافية (Remarks)")

            if st.form_submit_button("حفظ السجل", use_container_width=True):
                if s_id and c_name:
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    new_row = {
                        "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": c_phone,
                        "warranty_status": "خارج الكفالة", "document_origin": doc_origin, "reported_issue": issue,
                        "technician": current_user, "status": map_document_to_status(doc_origin, 0.0), "cost_debit": 0.0, "payment_credit": 0.0,
                        "balance": 0.0, "spare_parts": spare_parts, "resolution_notes": "", "remarks": remarks, "date_logged": date_now, "date_resolved": ""
                    }
                    save_ledger(pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.success("✅ تم الحفظ بنجاح!")
                    st.rerun()
                else: st.warning("يرجى تعبئة السند واسم الزبون.")

    with tab2:
        filtered = live_df[~live_df['status'].str.contains('تم التسليم', na=False)] if not live_df.empty else pd.DataFrame()
        if not filtered.empty:
            opts = {f"{r['service_id']} - {r['customer_name']} ({r['tool_name']})": r['service_id'] for _, r in filtered.iterrows()}
            sel_id = opts[st.selectbox("اختر الجهاز:", list(opts.keys()))]
            row_data = live_df[live_df['service_id'] == sel_id].iloc[0]
            
            with st.form("update_form"):
                doc_options = ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"]
                try: curr_i = [i for i, o in enumerate(doc_options) if str(row_data['document_origin']) in o][0]
                except: curr_i = 0
                
                c_a, c_b = st.columns(2)
                with c_a: new_doc = st.selectbox("تحديث أصل السند:", doc_options, index=curr_i)
                with c_b: 
                    sp_opts = ["لا حاجة / متوفرة", "بانتظار شحن مجاني (Free Shipment)", "بانتظار شحن عادي (Normal Shipment)"]
                    try: sp_i = sp_opts.index(str(row_data['spare_parts']))
                    except: sp_i = 0
                    new_spare = st.selectbox("تحديث حالة قطع الغيار:", sp_opts, index=sp_i)
                
                col1, col2, col3 = st.columns(3)
                with col1: cost = st.number_input("تكلفة الصيانة (مدين)", value=float(row_data['cost_debit'] or 0), step=1.0)
                with col2: pay = st.number_input("الدفعة (دائن)", value=float(row_data['payment_credit'] or 0), step=1.0)
                with col3: st.metric("الرصيد", f"{cost - pay:.2f}")
                    
                new_status = map_document_to_status(new_doc, cost)
                
                c_n1, c_n2 = st.columns(2)
                with c_n1: notes = st.text_input("ملاحظات الصيانة والحل (Resolution)", value=str(row_data.get('resolution_notes', '')))
                with c_n2: remarks_update = st.text_input("تحديثات إضافية (Remarks)", value=str(row_data.get('remarks', '')))
                
                confirm = True
                if "تم التسليم" in new_status: confirm = st.checkbox("✅ أؤكد إقفال الملف (تسليم للزبون أو تحميل على الوكيل).")

                if st.form_submit_button("تحديث السجل", use_container_width=True):
                    if "تم التسليم" in new_status and not confirm: st.error("❌ يرجى تأكيد الإقفال.")
                    else:
                        idx = live_df.index[live_df['service_id'] == sel_id][0]
                        live_df.at[idx, 'cost_debit'] = cost
                        live_df.at[idx, 'payment_credit'] = pay
                        live_df.at[idx, 'balance'] = cost - pay
                        live_df.at[idx, 'resolution_notes'] = notes
                        live_df.at[idx, 'remarks'] = remarks_update
                        live_df.at[idx, 'document_origin'] = new_doc
                        live_df.at[idx, 'status'] = new_status
                        live_df.at[idx, 'spare_parts'] = new_spare
                        live_df.at[idx, 'date_resolved'] = datetime.now().strftime("%Y-%m-%d") if "تم التسليم" in new_status else ""
                        save_ledger(live_df)
                        st.success("✅ تم التحديث بنجاح!")
                        st.rerun()

            # WhatsApp Notification Integration Button
            if row_data['phone_number']:
                phone_clean = re.sub(r'\D', '', str(row_data['phone_number']))
                wa_msg = f"مرحباً {row_data['customer_name']}, جهازك ({row_data['tool_name']}) أصبح جاهزاً للاستلام في مركز صيانة القصر الذهبي. يرجى مراجعتنا."
                wa_link = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(wa_msg)}"
                st.markdown(f"### 💬 [إرسال إشعار جاهزية عبر واتساب للزبون]({wa_link})", unsafe_allow_html=True)
        else: st.info("لا توجد أجهزة قيد الصيانة.")

    with tab3:
        st.markdown("#### ⏱️ الأجهزة المتأخرة والجاهزة")
        if not live_df.empty:
            open_jobs = live_df[~live_df['status'].str.contains('تم التسليم', na=False)]
            if not open_jobs.empty:
                alerts = []
                for _, r in open_jobs.iterrows():
                    try: days = (datetime.now() - datetime.strptime(str(r['date_logged']).split(' ')[0], "%Y-%m-%d")).days
                    except: days = 0
                    alert = "✅ طبيعي"
                    if "المعالجة" in str(r['status']) or "الانتظار" in str(r['status']):
                        if days > 5: alert = "🔴 متأخر جداً"
                        elif days > 3: alert = "🟠 متأخر"
                    elif "جاهز" in str(r['status']) and days > 7: alert = "🔴 تأخر بالاستلام"
                    alerts.append({"التنبيه": alert, "أيام": days, "الفرع": get_branch(r['service_id']), "الحالة": r['status'], "الزبون": r['customer_name'], "الأداة": r['tool_name'], "الملاحظات": r.get('remarks', ''), "السند": r['service_id']})
                st.dataframe(pd.DataFrame(alerts).sort_values(by="أيام", ascending=False), use_container_width=True)

# ==========================================
# MODULE 3: WAREHOUSE (WITH REORDER ALERTS)
# ==========================================
elif st.session_state['current_module'] == 'Warehouse':
    st.title("📦 إدارة المستودعات والمخزون")
    
    # Low stock alert banner
    if not stock_df.empty:
        stock_df['quantity'] = pd.to_numeric(stock_df['quantity'], errors='coerce').fillna(0)
        low_stock_items = stock_df[stock_df['quantity'] <= 2]
        if not low_stock_items.empty:
            st.warning(f"⚠️ تنبيه: يوجد {len(low_stock_items)} أصناف بحاجة لإعادة طلب (الكمية منخفضة أو منتهية).")
            with st.expander("🔍 عرض الأصناف المنخفضة في المخزون"):
                st.dataframe(low_stock_items, use_container_width=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.download_button("📥 تصدير المخزون (Export to Excel)", data=convert_df_to_excel(stock_df) if not stock_df.empty else b"", file_name=f"Stock_{datetime.now().strftime('%Y-%m-%d')}.xlsx", use_container_width=True)
    with col_btn2:
        with st.expander("📤 تحديث كتالوج الأسعار (Import Price List)"):
            uploaded_stock = st.file_uploader("رفع ملف لائحة الأسعار", type=["xlsx"])
            if uploaded_stock and st.button("تحديث الأسعار سحابياً"):
                try:
                    raw_stock = pd.read_excel(uploaded_stock)
                    if 'MtCode' in raw_stock.columns and 'اسم المادة' in raw_stock.columns:
                        price_col = 'الجملة' if 'الجملة' in raw_stock.columns else raw_stock.columns[-1]
                        new_items = raw_stock[['MtCode', 'اسم المادة', price_col]].copy()
                        new_items.columns = ['item_code', 'item_name', 'price']
                        new_items = new_items.dropna(subset=['item_code'])
                        new_items['price'] = pd.to_numeric(new_items['price'], errors='coerce').fillna(0.0)
                        new_items['quantity'] = 0 
                        if not stock_df.empty:
                            qty_dict = dict(zip(stock_df['item_code'], stock_df['quantity']))
                            new_items['quantity'] = new_items['item_code'].map(qty_dict).fillna(0)
                        save_stock(new_items[STOCK_COLUMNS])
                        st.success("✅ تم تحديث الأسعار بنجاح!")
                        st.rerun()
                    else: st.error("❌ تأكد من اختيار لائحة الأسعار الصحيحة.")
                except Exception as e: st.error(f"خطأ: {e}")

    if not stock_df.empty:
        edited_stock = st.data_editor(stock_df, num_rows="dynamic", use_container_width=True, column_config={
            "item_code": "كود المادة", "item_name": "الاسم", "quantity": st.column_config.NumberColumn("الكمية", step=1), "price": st.column_config.NumberColumn("السعر", format="%.2f")
        })
        if st.button("💾 حفظ التعديلات", use_container_width=True):
            save_stock(edited_stock)
            st.success("✅ تم الحفظ!")
            st.rerun()

# ==========================================
# MODULE 4: LOGISTICS (HAWARA & LOCAL DISPATCH WITH UPLOAD)
# ==========================================
elif st.session_state['current_module'] == 'Logistics':
    st.title("🚚 اللوجستيات وإدارة الموردين والشحن")
    tab1, tab2 = st.tabs(["📑 طلبيات المورد (حوارة - HAWARA)", "📦 شحن وتوصيل محلي (مع رفع البوليصة)"])
    
    with tab1:
        st.markdown("#### إنشاء طلبية / إرسالية حوارة جديدة")
        with st.form("hawara_form"):
            c1, c2, c3 = st.columns(3)
            with c1: 
                h_id = st.text_input("معرف الطلب (مثال: HAW-001)")
                h_type = st.selectbox("نوع العملية", ["طلب قطع غيار", "إرسال أجهزة للصيانة", "استرجاع بضاعة"])
                linked_sid = st.selectbox("ربط بسند صيانة (اختياري)", options=["بدون ربط"] + live_df['service_id'].tolist() if not live_df.empty else ["بدون ربط"])
            with c2: 
                courier = st.selectbox("شركة الشحن / الساعي", ["شركة أرامكس", "نقل قدموس", "ساعي داخلي", "شركة حوارة الخاصة"])
                h_note = st.text_input("رقم بوليصة الشحن (Delivery Note)")
            with c3:
                h_status = st.selectbox("حالة الطلبية", ["قيد الطلب / التجهيز", "في الطريق (شحن)", "تم الاستلام"])
                uploaded_doc = st.file_uploader("إرفاق صورة الفاتورة (Upload Invoice)", type=["png", "jpg", "jpeg"])
                
            if st.form_submit_button("حفظ الطلبية ورفع المستند", use_container_width=True):
                if h_id:
                    file_url = ""
                    if uploaded_doc is not None:
                        with st.spinner("جاري رفع الفاتورة للسحابة..."):
                            try:
                                b64_img = base64.b64encode(uploaded_doc.getvalue()).decode("utf-8")
                                res = requests.post(f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}", data={"image": b64_img})
                                if res.status_code == 200:
                                    file_url = res.json()["data"]["url"]
                            except: pass

                    new_hawara = {
                        "order_id": h_id, "order_type": h_type, 
                        "linked_service_id": linked_sid if linked_sid != "بدون ربط" else "",
                        "courier": courier, "delivery_note": h_note, 
                        "document_link": file_url, "status": h_status, "date_logged": datetime.now().strftime("%Y-%m-%d")
                    }
                    save_hawara(pd.concat([hawara_df, pd.DataFrame([new_hawara])], ignore_index=True))
                    st.success("✅ تم حفظ الطلبية بنجاح!")
                    st.rerun()
                else: st.warning("يرجى إدخال معرف الطلب.")

        st.divider()
        st.markdown("#### سجل طلبيات حوارة")
        if not hawara_df.empty:
            edited_hawara = st.data_editor(
                hawara_df, num_rows="dynamic", use_container_width=True, 
                column_config={
                    "order_id": "معرف الطلب", "order_type": "النوع", "linked_service_id": "رقم سند الصيانة",
                    "courier": "شركة الشحن", "delivery_note": "بوليصة الشحن", 
                    "document_link": st.column_config.LinkColumn("رابط الفاتورة", display_text="🔗 عرض الفاتورة (View Invoice)"),
                    "status": st.column_config.SelectboxColumn("الحالة", options=["قيد الطلب / التجهيز", "في الطريق (شحن)", "تم الاستلام"]), "date_logged": "التاريخ"
                }
            )
            if st.button("💾 حفظ تعديلات طلبيات حوارة", use_container_width=True):
                save_hawara(edited_hawara)
                st.success("✅ تم التحديث بنجاح!")
                st.rerun()

    with tab2:
        st.markdown("#### تسجيل إرسالية وشحن محلي للأجهزة الجاهزة")
        with st.form("dispatch_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                disp_id = st.text_input("رقم الإرسالية (مثال: DISP-01)")
                ready_list = live_df[live_df['status'].str.contains('جاهز', na=False)] if not live_df.empty else pd.DataFrame()
                sel_service = st.selectbox("اختر الجهاز الجاهز للشحن", options=ready_list['service_id'].tolist() if not ready_list.empty else [])
            with c2:
                disp_courier = st.selectbox("شركة الشحن المحلي", ["شركة أرامكس", "نقل قدموس", "ساعي داخلي", "النقل السريع"])
                disp_note = st.text_input("رقم بوليصة الشحن المحلية")
            with c3:
                disp_file = st.file_uploader("إرفاق صورة بوليصة الشحن المحلية", type=["png", "jpg", "jpeg"])
                
            if st.form_submit_button("حفظ وحفظ إيصال الشحن سحابياً", use_container_width=True):
                if disp_id and sel_service:
                    file_url = ""
                    if disp_file is not None:
                        with st.spinner("جاري رفع بوليصة الشحن..."):
                            try:
                                b64_img = base64.b64encode(disp_file.getvalue()).decode("utf-8")
                                res = requests.post(f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}", data={"image": b64_img})
                                if res.status_code == 200: file_url = res.json()["data"]["url"]
                            except: pass
                    
                    cust_row = live_df[live_df['service_id'] == sel_service].iloc[0] if not live_df.empty else {}
                    new_disp = {
                        "dispatch_id": disp_id, "service_id": sel_service, "customer_name": cust_row.get('customer_name', ''),
                        "courier": disp_courier, "delivery_note": disp_note, "document_link": file_url, "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    save_dispatch(pd.concat([dispatch_df, pd.DataFrame([new_disp])], ignore_index=True))
                    st.success("✅ تم تسجيل إرسالية الشحن المحلي بنجاح!")
                    st.rerun()
                else: st.warning("يرجى إدخال رقم الإرسالية وسند الصيانة.")

        st.divider()
        st.markdown("#### سجل الشحنات المحلية السابقة")
        if not dispatch_df.empty:
            st.data_editor(dispatch_df, use_container_width=True, column_config={
                "dispatch_id": "رقم الإرسالية", "service_id": "سند الصيانة", "customer_name": "اسم الزبون",
                "courier": "شركة الشحن", "delivery_note": "بوليصة الشحن",
                "document_link": st.column_config.LinkColumn("إيصال الشحن", display_text="🔗 عرض البوليصة"), "date": "التاريخ"
            })

# ==========================================
# MODULE 5: ADMIN, FINANCE, REPORTS & STATEMENTS
# ==========================================
elif st.session_state['current_module'] == 'Admin':
    st.title("⚙️ الإدارة والتقارير المالية وحسابات الوكلاء")
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 تقارير الصيانة والتصدير", "🧾 كشف حساب الزبون الفردي", "👥 حسابات الوكلاء والشركاء (V)"])
    
    with admin_tab1:
        st.markdown("#### استخراج وتصدير تقارير الصيانة المفصلة")
        if not live_df.empty:
            all_statuses = live_df['status'].unique().tolist()
            selected_statuses = st.multiselect("🔍 تصفية السجل حسب الحالة:", options=all_statuses, default=all_statuses)
            filtered_ledger = live_df[live_df['status'].isin(selected_statuses)]
            
            st.download_button(
                label="📥 تصدير التقرير المفلتر إلى Excel", 
                data=convert_df_to_excel(filtered_ledger), 
                file_name=f"Service_Report_{datetime.now().strftime('%Y-%m-%d')}.xlsx", 
                use_container_width=True
            )
            st.dataframe(filtered_ledger, use_container_width=True)
            
        st.divider()
        if is_admin:
            with st.expander("📥 استيراد كشف حساب الأمين الشامل (Smart Auto-Parser)"):
                uploaded_legacy = st.file_uploader("رفع كشف الحساب", type=["xlsx"])
                if uploaded_legacy and st.button("بدء الاستيراد والدمج الذكي"):
                    with st.spinner("جاري مسح جميع سطور وسندات الأمين..."):
                        raw_excel = pd.read_excel(uploaded_legacy, header=None)
                        records = {}
                        curr_sid = None
                        
                        for r_idx, row in raw_excel.iterrows():
                            row_vals = [str(x).strip() for x in row.dropna().tolist()]
                            row_text = " ".join(row_vals)
                            
                            header_cell = ""
                            for val in row_vals:
                                if re.search(r'\b[SDV]\d+\b', val, re.IGNORECASE) and '-' in val:
                                    header_cell = val
                                    break
                            
                            if header_cell:
                                curr_sid_match = re.search(r'\b([SDV]\d+)\b', header_cell, re.IGNORECASE)
                                if curr_sid_match:
                                    curr_sid = curr_sid_match.group(1).upper()
                                    clean_header = re.sub(r'^(الزبون:|الحساب:|الزبون|الحساب)\s*', '', header_cell).strip()
                                    parts = [p.strip() for p in re.split(r'[-–]', clean_header) if p.strip()]
                                    
                                    c_name, phone, t_name, issue, w_status = "غير محدد", "", "غير محدد", "", "خارج الكفالة"
                                    
                                    for p in parts[1:]:
                                        digits = re.sub(r'\D', '', p)
                                        if any(kw in p for kw in ['كفالة', 'ضمان', 'مجاني']): w_status = "ضمن كفالة"
                                        elif 8 <= len(digits) <= 15 and len(p) < 20: phone = digits
                                        elif any(kw in p for kw in ['فولت', 'فولط', 'واط', 'امبير', 'مثقب', 'صاروخ', 'مضخة', 'جلخ', 'كسارة', 'هوا', 'بطارية', 'شاحن', 'ماكينة', 'غطاس', 'غاطسة', 'رجاج', 'sds']): t_name = p
                                        elif any(kw in p for kw in ['عطل', 'لايعمل', 'لا يعمل', 'تبديل', 'صيانة', 'ماس', 'صوت', 'فواشة', 'كبسة', 'حرامي']): issue = p
                                        elif len(p) > 2:
                                            if c_name == "غير محدد": c_name = p
                                            elif t_name == "غير محدد": t_name = p
                                            else: issue = p

                                    if curr_sid not in records:
                                        records[curr_sid] = {
                                            "service_id": curr_sid, "tool_name": t_name, "customer_name": c_name, "phone_number": phone,
                                            "warranty_status": w_status, "document_origin": "", "reported_issue": issue,
                                            "technician": "Admin Import", "status": "قيد الانتظار", "cost_debit": 0.0,
                                            "payment_credit": 0.0, "balance": 0.0, "spare_parts": "لا حاجة / متوفرة",
                                            "resolution_notes": "", "remarks": "", "date_logged": datetime.now().strftime("%Y-%m-%d"), "date_resolved": ""
                                        }

                            if curr_sid and curr_sid in records:
                                rec = records[curr_sid]
                                c_origin = rec["document_origin"]
                                c_rank = get_status_rank(c_origin)
                                nums = []
                                for v in row_vals:
                                    try: nums.append(float(v))
                                    except: pass
                                
                                if "قبض" in row_text:
                                    if c_rank < 4: rec["document_origin"] = "قبض د: (مدفوع ومسلم)"
                                    if nums: rec["payment_credit"] = max(nums)
                                elif "خ صيانة" in row_text:
                                    if c_rank < 3: rec["document_origin"] = "خ صيانة: (تحميل على الوكيل)"
                                elif "مبيع خ ص" in row_text:
                                    if c_rank < 2: rec["document_origin"] = "مبيع خ ص: (جاهز ومفوتر)"
                                    if nums: rec["cost_debit"] = max(nums)
                                elif "اد خ ص" in row_text and c_rank < 1:
                                    rec["document_origin"] = "اد خ ص: (استلام للصيانة)"

                        imported_list = []
                        for sid, rec in records.items():
                            rec["balance"] = float(rec["cost_debit"]) - float(rec["payment_credit"])
                            rec["status"] = map_document_to_status(rec["document_origin"], rec["cost_debit"])
                            if "تم التسليم" in rec["status"]: rec["date_resolved"] = datetime.now().strftime("%Y-%m-%d")
                            imported_list.append(rec)

                        if imported_list:
                            new_imp_df = pd.DataFrame(imported_list)
                            merged = pd.concat([live_df, new_imp_df], ignore_index=True)
                            final_df = deduplicate_ledger(merged)
                            save_ledger(final_df)
                            st.success(f"✅ تم استيراد وتحديث {len(final_df)} سجل بنجاح!")
                            st.rerun()

    with admin_tab2:
        st.markdown("#### طباعة وتوليد كشف حساب الزبون")
        if not live_df.empty:
            cust_opts = live_df['customer_name'].unique().tolist()
            sel_cust = st.selectbox("اختر اسم الزبون للتقرير المخصص:", options=cust_opts)
            cust_records = live_df[live_df['customer_name'] == sel_cust]
            
            st.markdown(f"### كشف حساب: {sel_cust}")
            st.dataframe(cust_records[['service_id', 'tool_name', 'warranty_status', 'status', 'cost_debit', 'payment_credit', 'balance', 'date_logged']], use_container_width=True)
            
            total_cust_balance = cust_records['balance'].astype(float).sum()
            st.metric("الرصيد الإجمالي المتبقي على الزبون", f"${total_cust_balance:.2f}")

    with admin_tab3:
        st.markdown("#### حسابات الوكلاء والشركاء (الفروع و V)")
        if not live_df.empty:
            partners_df = live_df[live_df['service_id'].str.startswith('V', na=False) | live_df['document_origin'].str.contains('خ صيانة', na=False)]
            if not partners_df.empty:
                st.dataframe(partners_df[['service_id', 'customer_name', 'tool_name', 'status', 'cost_debit', 'balance']], use_container_width=True)
                partner_total = partners_df['balance'].astype(float).sum()
                st.metric("إجمالي حسابات الوكلاء المستحقة", f"${partner_total:.2f}")
            else:
                st.info("لا توجد حسابات وكلاء مسجلة حالياً.")
