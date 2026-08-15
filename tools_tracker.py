import streamlit as st
import pandas as pd
from datetime import datetime
import re
import io
from streamlit_gsheets import GSheetsConnection

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
    "balance", "spare_parts", "resolution_notes", "date_logged", "date_resolved"
]
STOCK_COLUMNS = ["item_code", "item_name", "quantity", "price"]
HAWARA_COLUMNS = ["order_id", "order_type", "delivery_note", "document_link", "status", "date_logged"]

def get_status_rank(val):
    s = str(val)
    if "قبض" in s or "Collected" in s: return 4
    if "خ صيانة" in s or "حساب وكيل" in s: return 3
    if "مبيع خ ص" in s or "جاهز" in s: return 2
    if "اد خ ص" in s or "المعالجة" in s: return 1
    return 0

def map_document_to_status(doc_string, cost=0.0):
    doc = str(doc_string).strip()
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
    if df.empty or 'service_id' not in df.columns:
        return df
    
    df['rank'] = df['document_origin'].apply(get_status_rank)
    df = df.sort_values(by=['service_id', 'rank'], ascending=[True, True])
    
    # Keep the last entry (highest rank) per service_id
    deduped = df.groupby('service_id', as_index=False).last()
    deduped = deduped.drop(columns=['rank'], errors='ignore')
    return deduped

def get_ledger():
    try:
        df = conn.read(worksheet="Ledger", ttl=0)
        for col in EXPECTED_COLUMNS:
            if col not in df.columns: df[col] = ""
        for col in EXPECTED_COLUMNS:
            if col not in ['cost_debit', 'payment_credit', 'balance']:
                df[col] = df[col].fillna("").astype(str).replace({'nan': '', 'None': ''})
        df.loc[df['spare_parts'] == "", 'spare_parts'] = "لا حاجة / متوفرة"
        
        # Deduplicate on load
        return deduplicate_ledger(df)
    except:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

def save_ledger(df):
    clean_df = deduplicate_ledger(df)
    conn.update(worksheet="Ledger", data=clean_df)

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
        if df.empty or len(df.columns) < len(HAWARA_COLUMNS): return pd.DataFrame(columns=HAWARA_COLUMNS)
        return df
    except: return pd.DataFrame(columns=HAWARA_COLUMNS)

def save_hawara(df): conn.update(worksheet="Hawara", data=df)

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

# ==========================================
# "START MENU" (SIDEBAR)
# ==========================================
st.sidebar.title("🎛️ القائمة الرئيسية")
st.sidebar.write(f"👤 مرحباً: **{current_user}**")
st.sidebar.divider()

if st.sidebar.button("🏠 لوحة التحكم (Dashboard)", use_container_width=True): st.session_state['current_module'] = 'Home'
if st.sidebar.button("🛠️ قسم الصيانة (Service Desk)", use_container_width=True): st.session_state['current_module'] = 'Services'
if st.sidebar.button("📦 المستودعات (Warehouse)", use_container_width=True): st.session_state['current_module'] = 'Warehouse'
if st.sidebar.button("🚚 اللوجستيات (Logistics)", use_container_width=True): st.session_state['current_module'] = 'Logistics'
if st.sidebar.button("⚙️ النظام والمالية (Admin & Finance)", use_container_width=True): st.session_state['current_module'] = 'Admin'

st.sidebar.divider()
if st.sidebar.button("🚪 تسجيل الخروج", use_container_width=True):
    st.session_state['logged_in_user'] = None
    st.rerun()

# ==========================================
# MODULE 1: HOME DASHBOARD
# ==========================================
if st.session_state['current_module'] == 'Home':
    st.title("🎛️ لوحة التحكم الرئيسية (ERP Dashboard)")
    st.write("اختر النظام الفرعي للبدء بالعمل:")
    
    active_count = len(live_df[~live_df['status'].str.contains('تم التسليم', na=False)]) if not live_df.empty else 0
    ready_count = len(live_df[live_df['status'].str.contains('جاهز', na=False)]) if not live_df.empty else 0
    hawara_pending = len(hawara_df[~hawara_df['status'].str.contains('تم الاستلام', na=False)]) if not hawara_df.empty else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 صيانة نشطة", active_count)
    m2.metric("✅ أجهزة جاهزة", ready_count)
    m3.metric("🚚 طلبيات حوارة معلقة", hawara_pending)
    m4.metric("🧩 أصناف المستودع", len(stock_df) if not stock_df.empty else 0)
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
        if st.button("⚙️\nالإعدادات والمالية\n(Admin & Finance)", use_container_width=True):
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
                
            issue = st.text_input("العطل المرصود")
            if st.form_submit_button("حفظ السجل", use_container_width=True):
                if s_id and c_name:
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    new_row = {
                        "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": c_phone,
                        "warranty_status": "خارج الكفالة", "document_origin": doc_origin, "reported_issue": issue,
                        "technician": current_user, "status": map_document_to_status(doc_origin, 0.0), "cost_debit": 0.0, "payment_credit": 0.0,
                        "balance": 0.0, "spare_parts": spare_parts, "resolution_notes": "", "date_logged": date_now, "date_resolved": ""
                    }
                    updated_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_ledger(updated_df)
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
                notes = st.text_input("ملاحظات الصيانة", value=str(row_data['resolution_notes']))
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
                        live_df.at[idx, 'document_origin'] = new_doc
                        live_df.at[idx, 'status'] = new_status
                        live_df.at[idx, 'spare_parts'] = new_spare
                        live_df.at[idx, 'date_resolved'] = datetime.now().strftime("%Y-%m-%d") if "تم التسليم" in new_status else ""
                        save_ledger(live_df)
                        st.success("✅ تم التحديث بنجاح!")
                        st.rerun()
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
                    alerts.append({"التنبيه": alert, "أيام": days, "الفرع": get_branch(r['service_id']), "الحالة": r['status'], "الزبون": r['customer_name'], "الأداة": r['tool_name'], "السند": r['service_id']})
                st.dataframe(pd.DataFrame(alerts).sort_values(by="أيام", ascending=False), use_container_width=True)

# ==========================================
# MODULE 3: WAREHOUSE 
# ==========================================
elif st.session_state['current_module'] == 'Warehouse':
    st.title("📦 إدارة المستودعات (Warehouse)")
    
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
# MODULE 4: LOGISTICS & HAWARA ORDERS
# ==========================================
elif st.session_state['current_module'] == 'Logistics':
    st.title("🚚 اللوجستيات وإدارة الموردين")
    tab1, tab2 = st.tabs(["📑 طلبيات المورد (حوارة - HAWARA)", "📦 شحن وتوصيل محلي"])
    
    with tab1:
        st.markdown("#### إنشاء طلبية / إرسالية حوارة جديدة")
        with st.form("hawara_form"):
            c1, c2, c3 = st.columns(3)
            with c1: 
                h_id = st.text_input("معرف الطلب (مثال: HAW-001)")
                h_type = st.selectbox("نوع العملية", ["طلب قطع غيار", "إرسال أجهزة للصيانة", "استرجاع بضاعة"])
            with c2: 
                h_note = st.text_input("رقم بوليصة الشحن (Delivery Note)")
                h_link = st.text_input("رابط المستند/الفاتورة (Google Drive Link)")
            with c3:
                h_status = st.selectbox("حالة الطلبية", ["قيد الطلب / التجهيز", "في الطريق (شحن)", "تم الاستلام"])
                
            if st.form_submit_button("حفظ الطلبية", use_container_width=True):
                if h_id:
                    new_hawara = {
                        "order_id": h_id, "order_type": h_type, "delivery_note": h_note, 
                        "document_link": h_link, "status": h_status, "date_logged": datetime.now().strftime("%Y-%m-%d")
                    }
                    updated_hawara = pd.concat([hawara_df, pd.DataFrame([new_hawara])], ignore_index=True)
                    save_hawara(updated_hawara)
                    st.success("✅ تم إضافة الطلبية بنجاح!")
                    st.rerun()
                else: st.warning("يرجى إدخال معرف الطلب.")

        st.divider()
        st.markdown("#### سجل طلبيات حوارة (تحديث مباشر)")
        if not hawara_df.empty:
            edited_hawara = st.data_editor(hawara_df, use_container_width=True, column_config={
                "order_id": "معرف الطلب", "order_type": "النوع", "delivery_note": "بوليصة الشحن", 
                "document_link": st.column_config.LinkColumn("مستند الفاتورة (Link)"), "status": st.column_config.SelectboxColumn("الحالة", options=["قيد الطلب / التجهيز", "في الطريق (شحن)", "تم الاستلام"]), "date_logged": "التاريخ"
            })
            if st.button("💾 حفظ تعديلات الطلبيات", use_container_width=True):
                save_hawara(edited_hawara)
                st.success("✅ تم التحديث بنجاح!")
                st.rerun()
        else: st.info("لا توجد طلبيات مسجلة حالياً.")

    with tab2:
        st.markdown("#### أجهزة جاهزة تتطلب شحن محلي")
        if not live_df.empty:
            ready_for_dispatch = live_df[live_df['status'].str.contains('جاهز|وكيل', na=False, regex=True)]
            if not ready_for_dispatch.empty:
                dispatch_view = ready_for_dispatch[['service_id', 'tool_name', 'customer_name', 'phone_number', 'status']].copy()
                dispatch_view.columns = ["السند", "الجهاز", "الزبون", "الهاتف", "حالة النظام"]
                st.dataframe(dispatch_view, use_container_width=True)
                
                with st.expander("📄 إصدار بوليصة شحن (Delivery Note)"):
                    opts = {f"{r['service_id']} - {r['customer_name']}": r['service_id'] for _, r in ready_for_dispatch.iterrows()}
                    sel_id = opts[st.selectbox("اختر الجهاز لإنشاء البوليصة:", list(opts.keys()))]
                    c_comp = st.selectbox("شركة التوصيل:", ["البريد السريع", "شركة أرامكس", "نقل داخلي (الفروع)"])
                    if st.button("🖨️ تسجيل طلب الشحن"):
                        st.success(f"تم تسجيل طلب الشحن عبر {c_comp} للسند {sel_id}.")
            else: st.success("لا توجد أجهزة جاهزة تحتاج إلى شحن حالياً.")

# ==========================================
# MODULE 5: ADMIN & FINANCE (AUTO-CONSOLIDATION)
# ==========================================
elif st.session_state['current_module'] == 'Admin':
    st.title("⚙️ إعدادات النظام والمالية")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 تنظيف وتوحيد السجلات الحالية (Clean Duplicates Now)", use_container_width=True):
            clean_df = deduplicate_ledger(live_df)
            save_ledger(clean_df)
            st.success("✅ تم دمج وتوحيد جميع التكرارات بناءً على الحالة الأحدث!")
            st.rerun()

    if is_admin:
        with st.expander("📥 استيراد وتصحيح ذكي (Excel Import & Sync)"):
            st.markdown("يقوم بدمج كل مراحل الجهاز في سجل واحد واختيار الحالة الأحدث تلقائياً.")
            uploaded_legacy = st.file_uploader("رفع كشف الحساب", type=["xlsx"])
            if uploaded_legacy and st.button("بدء الاستيراد الموحد"):
                with st.spinner("جاري قراءة وتوحيد بيانات كل جهاز..."):
                    df = pd.read_excel(uploaded_legacy)
                    records_by_id = {}
                    current_sid = None
                    cust_col = 'اسم الزبون' if 'اسم الزبون' in df.columns else 'الحساب' if 'الحساب' in df.columns else None

                    for index, row in df.iterrows():
                        row_str = " ".join(str(val) for val in row.values)
                        cust_name_raw = str(row[cust_col]) if cust_col and pd.notna(row[cust_col]) else ""
                        
                        if cust_name_raw and '-' in cust_name_raw and any(c in cust_name_raw.upper() for c in ['S', 'D', 'V']):
                            parts = [p.strip() for p in cust_name_raw.split('-')]
                            current_sid = parts[0] if len(parts) > 0 else f"SYS-{index}"
                            
                            c_name, phone, t_name = "غير محدد", "", "غير محدد"
                            for p in parts[1:]:
                                p_clean = p.strip()
                                if re.match(r'^[\d\s\+\-]{8,}$', p_clean) and not any(c.isalpha() for c in p_clean): phone = p_clean
                                elif re.search(r'[a-zA-Z]', p_clean) and re.search(r'\d', p_clean): t_name = p_clean
                                elif len(p_clean) > 2: c_name = p_clean
                            
                            cost_val = float(row.get('مدين', 0) if pd.notna(row.get('مدين')) else 0)
                            payment_val = float(row.get('دائن', 0) if pd.notna(row.get('دائن')) else 0)
                            balance_val = float(row.get('الرصيد الحالي', 0) if pd.notna(row.get('الرصيد الحالي')) else 0)
                            
                            if current_sid not in records_by_id:
                                records_by_id[current_sid] = {
                                    "service_id": current_sid, "tool_name": t_name, "customer_name": c_name, "phone_number": phone,
                                    "warranty_status": "", "document_origin": "", "reported_issue": "", "technician": "Admin Import", 
                                    "status": "قيد الانتظار", "cost_debit": cost_val, "payment_credit": payment_val, "balance": balance_val, 
                                    "spare_parts": "لا حاجة / متوفرة", "resolution_notes": "", "date_logged": datetime.now().strftime("%Y-%m-%d"), "date_resolved": ""
                                }
                        
                        if current_sid and current_sid in records_by_id:
                            # Keep the highest-ranked document origin for this service ticket
                            current_origin = records_by_id[current_sid]["document_origin"]
                            current_rank = get_status_rank(current_origin)
                            
                            if "قبض" in row_str and current_rank < 4:
                                records_by_id[current_sid]["document_origin"] = "قبض د: (مدفوع ومسلم)"
                            elif "خ صيانة" in row_str and current_rank < 3:
                                records_by_id[current_sid]["document_origin"] = "خ صيانة: (تحميل على الوكيل)"
                            elif "مبيع خ ص" in row_str and current_rank < 2:
                                records_by_id[current_sid]["document_origin"] = "مبيع خ ص: (جاهز ومفوتر)"
                            elif "اد خ ص" in row_str and current_rank < 1:
                                records_by_id[current_sid]["document_origin"] = "اد خ ص: (استلام للصيانة)"
                                
                    new_records = list(records_by_id.values())
                    for rec in new_records:
                        rec['status'] = map_document_to_status(rec['document_origin'], rec['cost_debit'])
                        if "تم التسليم" in rec['status']: rec['date_resolved'] = datetime.now().strftime("%Y-%m-%d")
                    
                    combined_df = pd.concat([live_df, pd.DataFrame(new_records)], ignore_index=True)
                    final_df = deduplicate_ledger(combined_df)
                    save_ledger(final_df)
                    st.success(f"✅ تم دمج وتحديث {len(new_records)} جهاز بنجاح دون أي تكرار!")
                    st.rerun()

    st.markdown("#### 📊 السجل المالي العام (General Ledger)")
    st.dataframe(live_df, use_container_width=True)
