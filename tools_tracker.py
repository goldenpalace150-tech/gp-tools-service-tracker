import streamlit as st
import pandas as pd
from datetime import datetime
import re
from streamlit_gsheets import GSheetsConnection

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="مركز الصيانة - القصر الذهبي", layout="wide", page_icon="🛠️")

st.markdown("""
    <style>
        .stApp { background-color: #f4f6f9; direction: rtl; text-align: right; }
        h1, h2, h3, h4, p, span, label, div { text-align: right; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 6px; padding: 10px 20px; font-weight: bold; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        table { width: 100% !important; background-color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ نظام إدارة مركز الصيانة والمحاسبة")

# ==========================================
# GOOGLE SHEETS CONNECTION
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
        df = conn.read(worksheet="Ledger", ttl=0)
        if df.empty or len(df.columns) < len(EXPECTED_COLUMNS):
            return pd.DataFrame(columns=EXPECTED_COLUMNS)
        for col in EXPECTED_COLUMNS:
            if col not in ['cost_debit', 'payment_credit', 'balance']:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str).replace({'nan': '', 'None': ''})
        return df
    except:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

def save_ledger(df):
    conn.update(worksheet="Ledger", data=df)

# Helpers
def format_currency(val):
    try: return f"{float(val):.2f}"
    except: return "0.00"

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
    if "قبض د" in doc: return "تم التسليم (Collected)"
    if "خ صيانة" in doc: return "حساب وكيل (Partner Charge)"
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
    current_role = USERS[current_user]["role"]
    st.sidebar.success(f"مرحباً: {current_user}")
    if st.sidebar.button("خروج", use_container_width=True):
        st.session_state['logged_in_user'] = None
        st.rerun()

is_admin = ("Admin" in current_role)
st.divider()

live_df = get_ledger()

# ==========================================
# TABS NAVIGATION
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📥 1. استلام جديد", 
    "🔧 2. فحص وتسليم الأجهزة", 
    "⏱️ 3. تنبيهات التأخير", 
    "📊 4. كشف الحساب العام"
])

# --- TAB 1: INTAKE ---
with tab1:
    st.subheader("استلام جهاز صيانة جديد")
    with st.form("intake_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            s_id = st.text_input("رقم السند (S صيدا / D درعا / V وكيل)")
            c_name = st.text_input("اسم الزبون")
        with c2:
            c_phone = st.text_input("رقم الهاتف")
            t_name = st.text_input("اسم الأداة / الموديل")
        with c3:
            w_status = st.selectbox("الكفالة", ["خارج الكفالة", "ضمن كفالة", "ضمن كفالة يومين"])
            doc_origin = st.selectbox("أصل السند", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "خ صيانة: (تحميل على الوكيل)"])
            
        issue = st.text_area("العطل / الشكوى المرصودة")
        
        if st.form_submit_button("حفظ وحفظ سحابياً", use_container_width=True):
            if s_id and c_name and t_name:
                if not live_df.empty and s_id in live_df['service_id'].values:
                    st.error("رقم السند موجود مسبقاً.")
                else:
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    auto_status = map_document_to_status(doc_origin)
                    new_row = {
                        "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": c_phone,
                        "warranty_status": w_status, "document_origin": doc_origin, "reported_issue": issue,
                        "technician": current_user, "status": auto_status, "cost_debit": 0.0, "payment_credit": 0.0,
                        "balance": 0.0, "resolution_notes": "", "date_logged": date_now, "date_resolved": ""
                    }
                    updated_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_ledger(updated_df)
                    st.success("✅ تم فتح الحساب بنجاح!")
                    st.rerun()
            else:
                st.warning("يرجى تعبئة الحقول الأساسية.")

# --- TAB 2: PROCESSING & DELIVERY ---
with tab2:
    st.subheader("تحديث الصيانة وتسليم الأجهزة")
    
    if is_admin:
        filtered = live_df.copy()
    else:
        filtered = live_df[~live_df['status'].str.contains('تم التسليم', na=False)] if not live_df.empty else pd.DataFrame()
        
    if not filtered.empty:
        opts = {f"{r['service_id']} - {r['customer_name']} ({r['tool_name']})": r['service_id'] for _, r in filtered.iterrows()}
        sel_opt = st.selectbox("اختر الجهاز للتحديث:", list(opts.keys()))
        sel_id = opts[sel_opt]
        
        row_data = live_df[live_df['service_id'] == sel_id].iloc[0]
        
        with st.form("update_form"):
            st.info(f"الزبون: {row_data['customer_name']} | الأداة: {row_data['tool_name']}")
            
            doc_options = ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"]
            try: curr_i = [i for i, o in enumerate(doc_options) if str(row_data['document_origin']) in o][0]
            except: curr_i = 0
            
            new_doc = st.selectbox("تحديث أصل السند (يغير الحالة):", doc_options, index=curr_i)
            new_status = map_document_to_status(new_doc)
            
            col1, col2, col3 = st.columns(3)
            with col1: cost = st.number_input("تكلفة الصيانة (مدين)", value=float(row_data['cost_debit'] or 0), step=1.0)
            with col2: pay = st.number_input("الدفعة المستلمة (دائن)", value=float(row_data['payment_credit'] or 0), step=1.0)
            with col3:
                bal = cost - pay
                st.metric("الرصيد المتبقي", f"{bal:.2f}")
                
            notes = st.text_area("ملاحظات الصيانة / البيان", value=str(row_data['resolution_notes']))
            
            confirm_deliv = True
            if "تم التسليم" in new_status:
                st.warning("⚠️ تنبيه: سيتم إقفال الملف نهائياً ولن يظهر للفنيين مجدداً.")
                confirm_deliv = st.checkbox("✅ أؤكد استلام المبلغ وتسليم الجهاز للعميل.")

            if st.form_submit_button("حفظ التحديثات سحابياً", use_container_width=True):
                if "تم التسليم" in new_status and not confirm_deliv:
                    st.error("❌ يرجى تأكيد التسليم بالمربع أعلاه.")
                else:
                    date_res = datetime.now().strftime("%Y-%m-%d") if "تم التسليم" in new_status else ""
                    idx = live_df.index[live_df['service_id'] == sel_id][0]
                    
                    live_df.at[idx, 'cost_debit'] = cost
                    live_df.at[idx, 'payment_credit'] = pay
                    live_df.at[idx, 'balance'] = bal
                    live_df.at[idx, 'resolution_notes'] = notes
                    live_df.at[idx, 'document_origin'] = new_doc
                    live_df.at[idx, 'status'] = new_status
                    live_df.at[idx, 'date_resolved'] = date_res
                    
                    save_ledger(live_df)
                    st.success("✅ تم التحديث بنجاح!")
                    st.rerun()
    else:
        st.info("لا توجد أجهزة قيد الصيانة.")

# --- TAB 3: DELAY ALERTS ---
with tab3:
    st.subheader("تنبيهات ومتابعة التأخير")
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
                    
                alerts.append({"التنبيه": alert, "أيام": days, "الفرع": get_branch(r['service_id']), "الحالة": r['status'], "الزبون": r['customer_name'], "الهاتف": r['phone_number'], "الرصيد": format_currency(r['balance']), "السند": r['service_id']})
                
            adf = pd.DataFrame(alerts).sort_values(by="أيام", ascending=False)
            st.dataframe(adf, use_container_width=True)
        else:
            st.success("🎉 لا توجد أجهزة معلقة.")

# --- TAB 4: GENERAL LEDGER ---
with tab4:
    st.subheader("كشف الحساب العام وسجلات الأجهزة")
    if not live_df.empty:
        ddf = live_df.copy()
        ddf.insert(1, 'الفرع', ddf['service_id'].apply(get_branch))
        st.dataframe(ddf, use_container_width=True)
    else:
        st.info("لا توجد سجلات.")
