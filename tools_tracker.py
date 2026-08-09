import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import json

# ==========================================
# PAGE CONFIGURATION & ARABIC RTL STYLING
# ==========================================
st.set_page_config(page_title="مركز الصيانة - القصر الذهبي", layout="wide")

st.markdown("""
    <style>
        .stApp {
            background-image: linear-gradient(rgba(248, 249, 250, 0.95), rgba(248, 249, 250, 0.95)), 
                              url("https://images.unsplash.com/photo-1581092160562-40aa08e78837?q=80&w=1920&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            direction: rtl;
            text-align: right;
        }
        h1, h2, h3, h4, p, span, label, div { overflow-wrap: break-word !important; text-align: right; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; flex-wrap: wrap; }
        .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 4px; padding: 8px 16px; font-size: 14px; font-weight: bold; }
        table { width: 100% !important; font-size: 13px !important; background-color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ نظام إدارة مركز الصيانة والمحاسبة (كشف الحساب)")

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
DB_NAME = 'customer_service_center.db'

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    # Service Tickets & Ledger table (Mirrors your Excel structure)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_ledger (
            service_id TEXT PRIMARY KEY,
            tool_name TEXT,
            customer_name TEXT,
            phone_number TEXT,
            warranty_status TEXT,
            document_origin TEXT,
            reported_issue TEXT,
            technician TEXT,
            status TEXT DEFAULT 'قيد الانتظار',
            cost_debit REAL DEFAULT 0.0,
            payment_credit REAL DEFAULT 0.0,
            balance REAL DEFAULT 0.0,
            resolution_notes TEXT,
            date_logged TEXT,
            date_resolved TEXT,
            photo_incoming BLOB
        )
    ''')
    
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES ('admin', '123', 'مدير النظام (Admin)')")
        cursor.execute("INSERT INTO users VALUES ('tech', '123', 'فني صيانة (Technician)')")
        
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return result

# ==========================================
# AUTHENTICATION
# ==========================================
if 'logged_in_user' not in st.session_state: st.session_state['logged_in_user'] = None
st.sidebar.header("🔐 نظام تسجيل الدخول")

if st.session_state['logged_in_user'] is None:
    with st.sidebar.form("login_form"):
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("تسجيل الدخول", use_container_width=True):
            user_record = run_query("SELECT password, role FROM users WHERE username = ?", (username_input,))
            if user_record and user_record[0][0] == password_input:
                st.session_state['logged_in_user'] = username_input
                st.rerun()
            else:
                st.sidebar.error("بيانات الدخول غير صحيحة.")
    st.stop()
else:
    current_user = st.session_state['logged_in_user']
    current_role = run_query("SELECT role FROM users WHERE username = ?", (current_user,))[0][0]
    st.sidebar.success(f"مرحباً: {current_user}")
    if st.sidebar.button("تسجيل الخروج", use_container_width=True):
        st.session_state['logged_in_user'] = None
        st.rerun()

is_admin = ("Admin" in current_role)
st.divider()

# ==========================================
# MAIN APPLICATION TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["📥 1. استلام صيانة جديدة (Intake)", "🔧 2. الفحص والمحاسبة (Processing & Ledger)", "📊 3. كشف الحساب والتقارير (Reports)"])

# --- TAB 1: NEW SERVICE INTAKE ---
with tab1:
    st.subheader("تسجيل جهاز جديد للصيانة")
    with st.form("intake_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_id = st.text_input("رقم الحساب / السند (مثال: D758)", help="Service ID")
            c_name = st.text_input("اسم الزبون")
            c_phone = st.text_input("رقم الهاتف")
        with col2:
            t_name = st.text_input("اسم الأداة / الموديل (مثال: مضخة ١ بنزين)")
            w_status = st.selectbox("حالة الكفالة", ["خارج الكفالة", "ضمن كفالة", "ضمن كفالة يومين"])
            doc_origin = st.text_input("أصل السند (مثال: اد خ ص: 851)")
        with col3:
            issue = st.text_area("العطل / الشكوى (مثال: عدم ضغط ماء)")
            tech_assigned = st.text_input("الفني المستلم", value=current_user)
            
        st.write("📸 التقاط صورة للجهاز عند الاستلام (اختياري)")
        enable_camera = st.checkbox("تفعيل الكاميرا")
        photo_data = None
        if enable_camera:
            cam_pic = st.camera_input("التقط صورة")
            if cam_pic: photo_data = cam_pic.getvalue()

        if st.form_submit_button("حفظ واستخراج إيصال استلام", use_container_width=True):
            if s_id and c_name and t_name:
                try:
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    run_query('''INSERT INTO service_ledger 
                                (service_id, tool_name, customer_name, phone_number, warranty_status, 
                                 document_origin, reported_issue, technician, date_logged, photo_incoming) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                              (s_id, t_name, c_name, c_phone, w_status, doc_origin, issue, tech_assigned, date_now, photo_data), fetch=False)
                    st.success(f"✅ تم فتح حساب صيانة للزبون {c_name} بنجاح!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("رقم السند/الحساب موجود مسبقاً. يرجى استخدام رقم مختلف.")
            else:
                st.warning("يرجى تعبئة رقم الحساب، اسم الزبون، واسم الأداة كحد أدنى.")

# --- TAB 2: PROCESSING & LEDGER (FINANCIALS) ---
with tab2:
    st.subheader("تحديث حالة الصيانة والمحاسبة")
    
    pending_services = run_query("SELECT service_id, customer_name, tool_name FROM service_ledger WHERE status != 'تم التسليم (Completed)'")
    if pending_services:
        options = {f"{row[0]} - {row[1]} ({row[2]})": row[0] for row in pending_services}
        selected_option = st.selectbox("اختر ملف الصيانة", list(options.keys()))
        selected_id = options[selected_option]
        
        # Load current financial data for this service
        curr_data = run_query("SELECT cost_debit, payment_credit, resolution_notes, status FROM service_ledger WHERE service_id = ?", (selected_id,))[0]
        
        with st.form("update_service_form"):
            st.info("قم بإدخال تكلفة الصيانة والدفعات لتحديث الرصيد التلقائي.")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                new_cost = st.number_input("تكلفة الصيانة (مدين - Debit)", value=float(curr_data[0]), step=1.0)
            with col_f2:
                new_payment = st.number_input("الدفعة المستلمة (دائن - Credit)", value=float(curr_data[1]), step=1.0)
            with col_f3:
                calc_balance = new_cost - new_payment
                st.metric("الرصيد المتبقي (Balance)", f"{calc_balance:.2f}")
                
            new_notes = st.text_area("البيان / ملاحظات الصيانة (مثال: لا يوجد عطل، تم تبديل قطعة)", value=curr_data[2] if curr_data[2] else "")
            new_status = st.selectbox("حالة الجهاز", ["قيد المعالجة (In Progress)", "جاهز للتسليم (Ready)", "تم التسليم (Completed)"], 
                                      index=0 if curr_data[3] == 'قيد الانتظار' else (2 if curr_data[3] == 'تم التسليم (Completed)' else 1))
            
            if st.form_submit_button("تحديث الحساب وحالة الجهاز", use_container_width=True):
                date_res = datetime.now().strftime("%Y-%m-%d") if "Completed" in new_status else ""
                run_query('''UPDATE service_ledger SET 
                             cost_debit = ?, payment_credit = ?, balance = ?, resolution_notes = ?, 
                             status = ?, date_resolved = ? WHERE service_id = ?''',
                          (new_cost, new_payment, calc_balance, new_notes, new_status, date_res, selected_id), fetch=False)
                st.success("✅ تم تحديث كشف الحساب وحالة الصيانة بنجاح!")
                st.rerun()
    else:
        st.info("لا توجد أجهزة قيد الصيانة حالياً.")

# --- TAB 3: LEDGER REPORTS & EXCEL EXPORT ---
with tab3:
    st.subheader("كشف الحساب العام (Ledger & Reports)")
    
    search_term = st.text_input("🔍 بحث في كشف الحساب (حسب اسم الزبون، رقم الحساب، الهاتف، أو الأداة):")
    
    query = """
    SELECT service_id AS 'الحساب', tool_name AS 'اسم الأداة', customer_name AS 'اسم الزبون', 
           phone_number AS 'رقم الهاتف', warranty_status AS 'الكفالة', 
           cost_debit AS 'مدين', payment_credit AS 'دائن', balance AS 'الرصيد الحالي',
           resolution_notes AS 'البيان', document_origin AS 'أصل السند', 
           status AS 'الحالة', date_logged AS 'التاريخ'
    FROM service_ledger
    """
    ledger_data = run_query(query)
    ledger_df = pd.DataFrame(ledger_data, columns=['الحساب', 'اسم الأداة', 'اسم الزبون', 'رقم الهاتف', 'الكفالة', 'مدين', 'دائن', 'الرصيد الحالي', 'البيان', 'أصل السند', 'الحالة', 'التاريخ'])
    
    if search_term:
        mask = ledger_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        display_df = ledger_df[mask]
    else:
        display_df = ledger_df
        
    st.markdown(display_df.to_html(index=False), unsafe_allow_html=True)
    
    st.divider()
    if st.button("📥 تصدير كشف الحساب إلى Excel", type="primary"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            ledger_df.to_excel(writer, index=False, sheet_name='كشف حساب')
        excel_data = output.getvalue()
        
        st.download_button(
            label="💾 تحميل التقرير (Excel)",
            data=excel_data,
            file_name="Customer_Service_Ledger.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # Session Backup mechanism
    with st.expander("💾 حفظ واستعادة قاعدة البيانات بالكامل (نسخة احتياطية JSON)"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            json_export = ledger_df.to_json(orient='records', force_ascii=False).encode('utf-8')
            st.download_button("📥 تحميل نسخة احتياطية (JSON)", data=json_export, file_name="service_ledger_backup.json", mime="application/json", use_container_width=True)
        with col_s2:
            st.info("ميزة الاستعادة تتطلب مدير نظام لضمان عدم الكتابة فوق البيانات الحالية بالخطأ.")
