import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re
from streamlit_gsheets import GSheetsConnection

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="مركز الصيانة - القصر الذهبي", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background-image: linear-gradient(rgba(248, 249, 250, 0.95), rgba(248, 249, 250, 0.95)), 
                              url("https://images.unsplash.com/photo-1581092160562-40aa08e78837?q=80&w=1920&auto=format&fit=crop");
            background-size: cover; background-position: center; background-attachment: fixed;
            direction: rtl; text-align: right;
        }
        h1, h2, h3, h4, p, span, label, div { overflow-wrap: break-word !important; text-align: right; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; flex-wrap: wrap; }
        .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 4px; padding: 8px 16px; font-weight: bold; }
        table { width: 100% !important; font-size: 13px !important; background-color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ نظام إدارة مركز الصيانة والمحاسبة الذكي (مزامنة سحابية)")

# ==========================================
# GOOGLE SHEETS DATABASE INITIALIZATION
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

EXPECTED_COLUMNS = [
    "service_id", "tool_name", "customer_name", "phone_number", 
    "warranty_status", "document_origin", "reported_issue", 
    "technician", "status", "cost_debit", "payment_credit", 
    "balance", "resolution_notes", "date_logged", "date_resolved"
]

def get_ledger():
    try:
        # ttl=0 forces a fresh pull from Google Sheets every single time (Live Sync)
        df = conn.read(worksheet="Ledger", ttl=0)
        if df.empty or len(df.columns) < len(EXPECTED_COLUMNS):
            return pd.DataFrame(columns=EXPECTED_COLUMNS)
        return df
    except Exception as e:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

def save_ledger(df):
    conn.update(worksheet="Ledger", data=df)

# ==========================================
# HELPERS
# ==========================================
def format_currency(val):
    try: return f"{float(val):.2f}"
    except (ValueError, TypeError): return "0.00"

def get_branch(s_id):
    if not s_id: return "أخرى"
    char = str(s_id).strip().upper()[0]
    if char == 'S': return "صيدا (Saida)"
    if char == 'D': return "درعا (Daraa)"
    if char == 'V': return "شريك/وكيل (Partner)"
    return "أخرى"

def map_document_to_status(doc_string):
    doc = str(doc_string).strip()
    if "اد خ ص" in doc: return "قيد المعالجة (In Progress)"
    if "مبيع خ ص" in doc: return "جاهز للتسليم (Ready)"
    if "قبض د" in doc: return "تم التسليم (Collected)"
    if "خ صيانة" in doc: return "حساب وكيل / شركة (Partner Charge)"
    return "قيد الانتظار"

# ==========================================
# AUTHENTICATION (Hardcoded for Sheets Version)
# ==========================================
if 'logged_in_user' not in st.session_state: st.session_state['logged_in_user'] = None
st.sidebar.header("🔐 نظام تسجيل الدخول")

USERS = {"admin": {"pass": "123", "role": "مدير النظام (Admin)"}, "tech": {"pass": "123", "role": "فني صيانة (Technician)"}}

if st.session_state['logged_in_user'] is None:
    with st.sidebar.form("login_form"):
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("تسجيل الدخول", use_container_width=True):
            if username_input in USERS and USERS[username_input]["pass"] == password_input:
                st.session_state['logged_in_user'] = username_input
                st.rerun()
            else:
                st.sidebar.error("بيانات الدخول غير صحيحة.")
    st.stop()
else:
    current_user = st.session_state['logged_in_user']
    current_role = USERS[current_user]["role"]
    st.sidebar.success(f"مرحباً: {current_user}")
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        st.session_state['logged_in_user'] = None
        st.rerun()

is_admin = ("Admin" in current_role)
st.divider()

# ==========================================
# MAIN APPLICATION TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📥 1. استلام صيانة", "🔧 2. فحص وتسليم (Ledger & Delivery)", "📊 3. السجلات والاستيراد", "⏱️ 4. المتابعة والتأخير"])

# Fetch live data immediately for the session
live_df = get_ledger()

# --- TAB 1: NEW SERVICE INTAKE ---
with tab1:
    st.subheader("تسجيل جهاز جديد للصيانة")
    with st.form("intake_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_id = st.text_input("رقم الحساب / السند (يبدأ بـ S, D, أو V)")
            c_name = st.text_input("اسم الزبون")
            c_phone = st.text_input("رقم الهاتف")
        with col2:
            t_name = st.text_input("اسم الأداة / الموديل")
            w_status = st.selectbox("حالة الكفالة", ["خارج الكفالة", "ضمن كفالة", "ضمن كفالة يومين"])
            doc_origin = st.selectbox("أصل السند (يحدد الحالة تلقائياً)", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "خ صيانة: (تحميل على الوكيل)"])
        with col3:
            issue = st.text_area("العطل / الشكوى")
            tech_assigned = st.text_input("الفني المستلم", value=current_user)
            
        if st.form_submit_button("حفظ مباشرة إلى Google Sheets", use_container_width=True):
            if s_id and c_name and t_name:
                if s_id in live_df['service_id'].values:
                    st.error("رقم السند/الحساب موجود مسبقاً.")
                else:
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    auto_status = map_document_to_status(doc_origin)
                    
                    new_row = {
                        "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": c_phone,
                        "warranty_status": w_status, "document_origin": doc_origin, "reported_issue": issue,
                        "technician": tech_assigned, "status": auto_status, "cost_debit": 0.0, "payment_credit": 0.0,
                        "balance": 0.0, "resolution_notes": "", "date_logged": date_now, "date_resolved": ""
                    }
                    
                    # Live Append and Save
                    updated_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_ledger(updated_df)
                    
                    st.success(f"✅ تم فتح حساب صيانة وحفظه سحابياً بنجاح. الحالة الآن: {auto_status}")
                    st.rerun()
            else:
                st.warning("يرجى تعبئة رقم الحساب، اسم الزبون، واسم الأداة كحد أدنى.")

# --- TAB 2: PROCESSING, LEDGER & DELIVERY LOCK ---
with tab2:
    st.subheader("تحديث حالة الصيانة وتأكيد التسليم")
    
    # Filter pending based on live data
    if is_admin:
        pending_mask = pd.Series([True] * len(live_df))
    else:
        pending_mask = ~live_df['status'].astype(str).str.contains('تم التسليم', na=False)
        
    filtered_df = live_df[pending_mask]
    
    if not filtered_df.empty:
        options = {f"{row['service_id']} - {row['customer_name']} ({row['tool_name']})": row['service_id'] for _, row in filtered_df.iterrows()}
        selected_option = st.selectbox("اختر ملف الصيانة", list(options.keys()))
        selected_id = options[selected_option]
        
        curr_data = live_df[live_df['service_id'] == selected_id].iloc[0]
        
        with st.form("update_service_form"):
            if "تم التسليم" in str(curr_data['status']) and is_admin:
                st.error("🔒 تنبيه: هذا الجهاز تم تسليمه وإقفاله. أنت تقوم بتعديله بصلاحيات (مدير النظام) لفك القفل.")
            
            doc_options = ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"]
            try:
                curr_idx = [i for i, opt in enumerate(doc_options) if str(curr_data['document_origin']) in opt][0]
            except IndexError:
                curr_idx = 0
                
            new_doc_origin = st.selectbox("تحديث أصل السند (يغير الحالة تلقائياً):", doc_options, index=curr_idx)
            auto_new_status = map_document_to_status(new_doc_origin)
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                new_cost = st.number_input("تكلفة الصيانة (مدين - Debit)", value=float(curr_data['cost_debit']) if pd.notna(curr_data['cost_debit']) else 0.0, step=1.0)
            with col_f2:
                new_payment = st.number_input("الدفعة المستلمة (دائن - Credit)", value=float(curr_data['payment_credit']) if pd.notna(curr_data['payment_credit']) else 0.0, step=1.0)
            with col_f3:
                calc_balance = new_cost - new_payment
                st.metric("الرصيد المتبقي (Balance)", f"{calc_balance:.2f}")
                
            new_notes = st.text_area("البيان / ملاحظات الصيانة", value=str(curr_data['resolution_notes']) if pd.notna(curr_data['resolution_notes']) else "")
            
            confirm_collection = True
            if "تم التسليم" in auto_new_status:
                st.warning("⚠️ إقفال الملف: سيتم تأكيد التسليم وإخفاء الجهاز ولن يمكن التراجع (إلا بواسطة المدير).")
                confirm_collection = st.checkbox("✅ أؤكد أنني استلمت المبلغ المتبقي (إن وجد) وسلمت الجهاز للعميل.")

            if st.form_submit_button("تحديث السجل في Google Sheets", use_container_width=True):
                if "تم التسليم" in auto_new_status and not confirm_collection:
                    st.error("❌ يرجى تحديد مربع تأكيد التسليم لإتمام العملية وإقفال الملف.")
                else:
                    date_res = datetime.now().strftime("%Y-%m-%d") if "تم التسليم" in auto_new_status else ""
                    
                    # Update DataFrame exactly at the correct row index
                    idx = live_df.index[live_df['service_id'] == selected_id][0]
                    live_df.at[idx, 'cost_debit'] = new_cost
                    live_df.at[idx, 'payment_credit'] = new_payment
                    live_df.at[idx, 'balance'] = calc_balance
                    live_df.at[idx, 'resolution_notes'] = new_notes
                    live_df.at[idx, 'document_origin'] = new_doc_origin
                    live_df.at[idx, 'status'] = auto_new_status
                    live_df.at[idx, 'date_resolved'] = date_res
                    
                    save_ledger(live_df)
                    st.success(f"✅ تم مزامنة التحديث بنجاح! الحالة الجديدة: {auto_new_status}")
                    st.rerun()
    else:
        st.info("لا توجد أجهزة قيد الصيانة حالياً (جميع الملفات مقفلة).")

# --- TAB 3: LEDGER REPORTS & EXCEL IMPORT ---
with tab3:
    st.subheader("كشف الحساب والمزامنة السحابية")
    
    if is_admin:
        with st.expander("📥 استيراد ملف الإكسل القديم إلى Google Sheets"):
            st.warning("رفع ملف سيقوم بإضافته مباشرة إلى ورقة العمل السحابية.")
            uploaded_legacy = st.file_uploader("رفع ملف كشف الحساب (Excel)", type=["xlsx"])
            if uploaded_legacy and st.button("تفكيك ورفع البيانات سحابياً"):
                with st.spinner("جاري تفكيك ورفع البيانات..."):
                    df = pd.read_excel(uploaded_legacy, sheet_name='كشف حساب')
                    df = df.dropna(subset=['اسم الزبون'])
                    
                    new_records = []
                    for index, row in df.iterrows():
                        raw_text = str(row['اسم الزبون'])
                        parts = [p.strip() for p in raw_text.split('-')]
                        
                        s_id = parts[0] if len(parts) > 0 else f"SYS-{index}"
                        if s_id in live_df['service_id'].values: continue # Skip existing
                        
                        t_name = parts[1] if len(parts) > 1 else "غير محدد"
                        c_name = parts[2] if len(parts) > 2 else "غير محدد"
                        phone = next((p for p in parts if len(re.sub(r'\D', '', p)) >= 9), "")
                                
                        doc_org = str(row['أصل السند']) if pd.notna(row['أصل السند']) else ""
                        status = map_document_to_status(doc_org)
                        res_notes = str(row['البيان']) if pd.notna(row['البيان']) else ""
                        dt_logged = str(row['التاريخ']).split(' ')[0] if pd.notna(row['التاريخ']) else datetime.now().strftime("%Y-%m-%d")
                        
                        new_records.append({
                            "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": phone,
                            "warranty_status": "", "document_origin": doc_org, "reported_issue": "",
                            "technician": "Admin Import", "status": status, "cost_debit": float(row.get('مدين', 0.0) or 0.0), 
                            "payment_credit": float(row.get('دائن', 0.0) or 0.0), "balance": float(row.get('الرصيد الحالي', 0.0) or 0.0), 
                            "resolution_notes": res_notes, "date_logged": dt_logged, "date_resolved": ""
                        })
                    
                    if new_records:
                        updated_df = pd.concat([live_df, pd.DataFrame(new_records)], ignore_index=True)
                        save_ledger(updated_df)
                        st.success(f"✅ تمت المزامنة بنجاح! تم رفع {len(new_records)} سجل جديد إلى Google Sheets.")
                        st.rerun()
                    else:
                        st.info("لا توجد سجلات جديدة لإضافتها.")

    display_df = live_df.copy()
    if not display_df.empty:
        display_df.insert(1, 'Branch', display_df['service_id'].apply(get_branch))
        
        display_df['cost_debit'] = display_df['cost_debit'].apply(format_currency)
        display_df['payment_credit'] = display_df['payment_credit'].apply(format_currency)
        display_df['balance'] = display_df['balance'].apply(format_currency)

    st.markdown(display_df.to_html(index=False), unsafe_allow_html=True)

# --- TAB 4: TIMELINE & ALERTS (SLA FOLLOW-UP) ---
with tab4:
    st.subheader("⏱️ المتابعة وتنبيهات التأخير (Follow-up & Alerts)")
    st.info("البيانات مسحوبة مباشرة من السحابة لضمان الدقة.")
    
    if not live_df.empty:
        open_jobs = live_df[~live_df['status'].astype(str).str.contains('تم التسليم', na=False)]
        
        if not open_jobs.empty:
            alerts_data = []
            for _, row in open_jobs.iterrows():
                try:
                    date_obj = datetime.strptime(str(row['date_logged']), "%Y-%m-%d")
                    days_in_shop = (datetime.now() - date_obj).days
                except:
                    days_in_shop = 0
                    
                alert_type = "✅ طبيعي"
                if "المعالجة" in str(row['status']) or "الانتظار" in str(row['status']):
                    if days_in_shop > 5: alert_type = "🔴 متأخر جداً في الصيانة"
                    elif days_in_shop > 3: alert_type = "🟠 متأخر في الصيانة"
                elif "جاهز" in str(row['status']):
                    if days_in_shop > 7: alert_type = "🔴 العميل تأخر في الاستلام"
                    
                alerts_data.append({
                    "التنبيه": alert_type,
                    "أيام الانتظار": days_in_shop,
                    "الفرع (Branch)": get_branch(row['service_id']),
                    "الزبون": row['customer_name'],
                    "الهاتف": row['phone_number'],
                    "الحالة الحالية": row['status'],
                    "الرصيد المطلوب": format_currency(row['balance']), 
                    "رقم السند": row['service_id']
                })
                
            alerts_df = pd.DataFrame(alerts_data).sort_values(by="أيام الانتظار", ascending=False)
            
            def color_alerts(val):
                if "🔴" in str(val): return 'background-color: #ffcccc'
                if "🟠" in str(val): return 'background-color: #ffe4b5'
                return ''
                
            st.dataframe(alerts_df.style.map(color_alerts, subset=['التنبيه']), use_container_width=True)
        else:
            st.success("🎉 لا توجد أي أجهزة قيد الصيانة أو جاهزة للتسليم.")
