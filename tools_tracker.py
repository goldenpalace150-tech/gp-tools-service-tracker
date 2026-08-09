import streamlit as st
import pandas as pd
from datetime import datetime
import re
import io
from streamlit_gsheets import GSheetsConnection

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="مركز الصيانة - القصر الذهبي", layout="wide", page_icon="🛠️")

st.markdown("""
    <style>
        .stApp { background-color: #f4f6f9; direction: rtl; text-align: right; }
        h1, h2, h3, h4, p, span, label, div { text-align: right; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 6px; padding: 10px 20px; font-weight: bold; }
        table { width: 100% !important; background-color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ نظام إدارة الصيانة والمحاسبة")

# ==========================================
# GOOGLE SHEETS CONNECTION
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

EXPECTED_COLUMNS = [
    "service_id", "tool_name", "customer_name", "phone_number", 
    "warranty_status", "document_origin", "reported_issue", 
    "technician", "status", "cost_debit", "payment_credit", 
    "balance", "spare_parts", "resolution_notes", "date_logged", "date_resolved"
]

STOCK_COLUMNS = ["item_code", "item_name", "quantity", "price"]

def get_ledger():
    try:
        df = conn.read(worksheet="Ledger", ttl=0)
        for col in EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        for col in EXPECTED_COLUMNS:
            if col not in ['cost_debit', 'payment_credit', 'balance']:
                df[col] = df[col].fillna("").astype(str).replace({'nan': '', 'None': ''})
        df.loc[df['spare_parts'] == "", 'spare_parts'] = "لا حاجة / متوفرة"
        return df
    except:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

def save_ledger(df):
    conn.update(worksheet="Ledger", data=df)

def get_stock():
    try:
        df = conn.read(worksheet="Stock", ttl=0)
        if df.empty or len(df.columns) < len(STOCK_COLUMNS):
            return pd.DataFrame(columns=STOCK_COLUMNS)
        return df
    except:
        return pd.DataFrame(columns=STOCK_COLUMNS)

def save_stock(df):
    conn.update(worksheet="Stock", data=df)

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Stock')
    return output.getvalue()

# Helpers
def get_branch(s_id):
    if not s_id: return "أخرى"
    char = str(s_id).strip().upper()[0]
    if char == 'S': return "صيدا (Saida)"
    if char == 'D': return "درعا (Daraa)"
    if char == 'V': return "شريك (Partner)"
    return "أخرى"

def map_document_to_status(doc_string):
    doc = str(doc_string).strip()
    if "اد خ ص" in doc: return "قيد المعالجة (In Progress)"
    if "مبيع خ ص" in doc: return "جاهز للتسليم (Ready)"
    # Both of these now contain "تم التسليم" so the system knows to close the ticket
    if "قبض د" in doc: return "تم التسليم للزبون (Customer Collected)"
    if "خ صيانة" in doc: return "تم التسليم - حساب وكيل (Partner Collected)"
    return "قيد الانتظار"

# ==========================================
# AUTHENTICATION
# ==========================================
if 'logged_in_user' not in st.session_state: st.session_state['logged_in_user'] = None
USERS = {"admin": {"pass": "123", "role": "مدير النظام (Admin)"}, "tech": {"pass": "123", "role": "فني صيانة (Technician)"}}

if st.session_state['logged_in_user'] is None:
    st.sidebar.subheader("🔐 تسجيل الدخول")
    with st.sidebar.form("login_form"):
        u_in = st.text_input("اسم المستخدم")
        p_in = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول", use_container_width=True):
            if u_in in USERS and USERS[u_in]["pass"] == p_in:
                st.session_state['logged_in_user'] = u_in
                st.rerun()
            else:
                st.sidebar.error("خطأ في البيانات.")
    st.stop()
else:
    current_user = st.session_state['logged_in_user']
    is_admin = ("Admin" in USERS[current_user]["role"])
    st.sidebar.success(f"مرحباً: {current_user}")
    if st.sidebar.button("خروج", use_container_width=True):
        st.session_state['logged_in_user'] = None
        st.rerun()

st.divider()
live_df = get_ledger()

# ==========================================
# TABS NAVIGATION
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 1. استلام صيانة", 
    "🔧 2. تحديث وتسليم", 
    "⏱️ 3. تنبيهات التأخير",
    "📦 4. مخزون قطع الغيار (استيراد/تصدير)", 
    "📊 5. كشف الحساب العام"
])

# --- TAB 1: INTAKE ---
with tab1:
    st.subheader("تسجيل جهاز جديد")
    with st.form("intake_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            s_id = st.text_input("رقم السند (S صيدا / D درعا / V وكيل)")
            c_name = st.text_input("اسم الزبون")
        with c2:
            c_phone = st.text_input("رقم الهاتف")
            t_name = st.text_input("كود/اسم الأداة (مثال: TGT11376)")
        with c3:
            doc_origin = st.selectbox("أصل السند", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "خ صيانة: (تحميل على الوكيل)"])
            spare_parts = st.selectbox("حالة قطع الغيار للمستودع", ["لا حاجة / متوفرة", "بانتظار شحن مجاني (Free Shipment)", "بانتظار شحن عادي (Normal Shipment)"])
            
        issue = st.text_input("العطل المرصود")
        
        if st.form_submit_button("حفظ السجل سحابياً", use_container_width=True):
            if s_id and c_name:
                date_now = datetime.now().strftime("%Y-%m-%d")
                auto_status = map_document_to_status(doc_origin)
                new_row = {
                    "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": c_phone,
                    "warranty_status": "خارج الكفالة", "document_origin": doc_origin, "reported_issue": issue,
                    "technician": current_user, "status": auto_status, "cost_debit": 0.0, "payment_credit": 0.0,
                    "balance": 0.0, "spare_parts": spare_parts, "resolution_notes": "", "date_logged": date_now, "date_resolved": ""
                }
                updated_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
                save_ledger(updated_df)
                st.success("✅ تم الحفظ بنجاح!")
                st.rerun()
            else:
                st.warning("يرجى تعبئة السند واسم الزبون.")

# --- TAB 2: UPDATE & DELIVERY ---
with tab2:
    st.subheader("تحديث حالة الصيانة")
    filtered = live_df[~live_df['status'].str.contains('تم التسليم', na=False)] if not live_df.empty else pd.DataFrame()
        
    if not filtered.empty:
        # Tool name is now successfully added back into the dropdown
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
            
            new_status = map_document_to_status(new_doc)
            
            col1, col2, col3 = st.columns(3)
            with col1: cost = st.number_input("تكلفة الصيانة (مدين)", value=float(row_data['cost_debit'] or 0), step=1.0)
            with col2: pay = st.number_input("الدفعة (دائن)", value=float(row_data['payment_credit'] or 0), step=1.0)
            with col3: st.metric("الرصيد", f"{cost - pay:.2f}")
                
            notes = st.text_input("ملاحظات الصيانة", value=str(row_data['resolution_notes']))
            
            confirm = True
            # Will trigger for both Normal Delivery and Partner Collection
            if "تم التسليم" in new_status:
                confirm = st.checkbox("✅ أؤكد إقفال الملف (تسليم للزبون أو تحميل على الوكيل).")

            if st.form_submit_button("تحديث السجل", use_container_width=True):
                if "تم التسليم" in new_status and not confirm:
                    st.error("❌ يرجى تأكيد إقفال الملف بالمربع أعلاه.")
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
    else:
        st.info("لا توجد أجهزة قيد الصيانة.")


# --- TAB 3: DELAY ALERTS & SHIPMENTS ---
with tab3:
    st.subheader("تنبيهات التأخير ومتابعة الشحنات")
    
    st.markdown("#### 📦 الأجهزة بانتظار شحنات قطع الغيار")
    if not live_df.empty:
        shipment_df = live_df[live_df['spare_parts'].str.contains('شحن', na=False, regex=False)]
        if not shipment_df.empty:
            ship_disp = shipment_df[['service_id', 'tool_name', 'customer_name', 'spare_parts', 'status']].copy()
            ship_disp.columns = ["السند", "الأداة/الكود", "الزبون", "نوع الشحنة المطلوبة", "الحالة الحالية"]
            st.dataframe(ship_disp, use_container_width=True)
        else:
            st.info("لا توجد أجهزة بانتظار شحنات حالياً.")
            
    st.divider()
    st.markdown("#### ⏱️ الأجهزة المتأخرة")
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
                elif "جاهز" in str(r['status']) and days > 7:
                    alert = "🔴 تأخر بالاستلام"
                    
                # Tool Name added to the Alert Tracking
                alerts.append({"التنبيه": alert, "أيام": days, "الفرع": get_branch(r['service_id']), "الحالة": r['status'], "الزبون": r['customer_name'], "الأداة": r['tool_name'], "السند": r['service_id']})
                
            st.dataframe(pd.DataFrame(alerts).sort_values(by="أيام", ascending=False), use_container_width=True)

# --- TAB 4: SPARE PARTS INVENTORY ---
with tab4:
    st.subheader("📦 إدارة ومخزون قطع الغيار")
    st.markdown("استيراد لائحة الأسعار (لائحة أسعار المواد) لإنشاء أو تحديث الكتالوج.")
    
    stock_df = get_stock()
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.download_button(
            label="📥 تصدير المخزون الحالي (Export to Excel)",
            data=convert_df_to_excel(stock_df) if not stock_df.empty else b"",
            file_name=f"Spare_Parts_Stock_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col_btn2:
        with st.expander("📤 استيراد لائحة أسعار المواد (Import Excel)"):
            uploaded_stock = st.file_uploader("رفع ملف لائحة الأسعار", type=["xlsx"])
            if uploaded_stock and st.button("تحديث الأسعار والمواد سحابياً"):
                with st.spinner("جاري استيراد لائحة الأسعار..."):
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
                            
                            final_stock = new_items[STOCK_COLUMNS]
                            save_stock(final_stock)
                            
                            st.success(f"✅ تم تحديث {len(final_stock)} مادة بنجاح! تم حفظ الكميات السابقة وتحديث الأسعار فقط.")
                            st.rerun()
                        else:
                            st.error("❌ خطأ: الملف المرفوع لا يحتوي على أعمدة 'MtCode' و 'اسم المادة'. يرجى التأكد من اختيار لائحة الأسعار الصحيحة.")
                    except Exception as e:
                        st.error(f"حدث خطأ غير متوقع: {e}")

    if not stock_df.empty:
        st.write("يمكنك تعديل الكميات مباشرة في الجدول بالأسفل للضبط اليدوي:")
        edited_stock = st.data_editor(
            stock_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "item_code": "كود المادة (MtCode)",
                "item_name": "اسم المادة",
                "quantity": st.column_config.NumberColumn("الكمية المتوفرة", step=1),
                "price": st.column_config.NumberColumn("السعر (الجملة)", format="%.2f")
            }
        )
        if st.button("💾 حفظ التعديلات اليدوية", use_container_width=True):
            save_stock(edited_stock)
            st.success("✅ تم الحفظ سحابياً!")
            st.rerun()
    else:
        st.info("لا توجد بيانات مخزون حالياً. يرجى رفع ملف لائحة أسعار المواد.")

# --- TAB 5: LEDGER IMPORT ---
with tab5:
    st.subheader("استيراد وكشف حساب عام")
    if is_admin:
        with st.expander("📥 استيراد ملف صيانة قديم (تفكيك ذكي)"):
            uploaded_legacy = st.file_uploader("رفع كشف الحساب (Excel)", type=["xlsx"])
            if uploaded_legacy and st.button("بدء الاستيراد"):
                df = pd.read_excel(uploaded_legacy, sheet_name='كشف حساب').dropna(subset=['اسم الزبون'])
                new_records = []
                for index, row in df.iterrows():
                    raw_text = str(row['اسم الزبون'])
                    parts = [p.strip() for p in raw_text.split('-')]
                    s_id = parts[0] if len(parts) > 0 else f"SYS-{index}"
                    if not live_df.empty and s_id in live_df['service_id'].values: continue 
                    
                    c_name, phone, t_name = "غير محدد", "", "غير محدد"
                    for p in parts[1:]:
                        p_clean = p.strip()
                        if re.match(r'^[\d\s\+\-]{8,}$', p_clean) and not any(c.isalpha() for c in p_clean):
                            phone = p_clean
                        elif re.search(r'[a-zA-Z]', p_clean) and re.search(r'\d', p_clean):
                            t_name = p_clean
                        elif len(p_clean) > 2:
                            c_name = p_clean

                    doc_org = str(row['أصل السند']) if pd.notna(row['أصل السند']) else ""
                    new_records.append({
                        "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": phone,
                        "warranty_status": "", "document_origin": doc_org, "reported_issue": "",
                        "technician": "Admin Import", "status": map_document_to_status(doc_org), 
                        "cost_debit": float(row.get('مدين', 0) or 0), "payment_credit": float(row.get('دائن', 0) or 0), 
                        "balance": float(row.get('الرصيد الحالي', 0) or 0), "spare_parts": "لا حاجة / متوفرة",
                        "resolution_notes": str(row.get('البيان', "")), "date_logged": datetime.now().strftime("%Y-%m-%d"), "date_resolved": ""
                    })
                
                if new_records:
                    updated_df = pd.concat([live_df, pd.DataFrame(new_records)], ignore_index=True)
                    save_ledger(updated_df)
                    st.success(f"✅ تم رفع {len(new_records)} سجل بنجاح!")
                    st.rerun()

    st.dataframe(live_df, use_container_width=True)
