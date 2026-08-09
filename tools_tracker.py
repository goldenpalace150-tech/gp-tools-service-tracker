import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
import re

# ==========================================
# PAGE CONFIGURATION & ARABIC RTL STYLING
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

st.title("🛠️ نظام إدارة مركز الصيانة والمحاسبة الذكي")

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
DB_NAME = 'customer_service_center.db'

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
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
# HELPER: STATUS MAPPING
# ==========================================
def map_document_to_status(doc_string):
    doc = str(doc_string).strip()
    if "اد خ ص" in doc: return "قيد المعالجة (In Progress)"
    if "مبيع خ ص" in doc: return "جاهز للتسليم (Ready)"
    if "قبض د" in doc: return "تم التسليم (Completed)"
    if "خ صيانة" in doc: return "حساب وكيل / شركة (Partner Charge)"
    return "قيد الانتظار"

# ==========================================
# MAIN APPLICATION TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📥 1. استلام صيانة (Intake)", "🔧 2. فحص ومحاسبة (Ledger)", "📊 3. السجلات والاستيراد (Data)", "⏱️ 4. المتابعة والتأخير (Alerts)"])

# --- TAB 1: NEW SERVICE INTAKE ---
with tab1:
    st.subheader("تسجيل جهاز جديد للصيانة")
    with st.form("intake_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            s_id = st.text_input("رقم الحساب / السند (مثال: D758)")
            c_name = st.text_input("اسم الزبون")
            c_phone = st.text_input("رقم الهاتف")
        with col2:
            t_name = st.text_input("اسم الأداة / الموديل")
            w_status = st.selectbox("حالة الكفالة", ["خارج الكفالة", "ضمن كفالة", "ضمن كفالة يومين"])
            doc_origin = st.selectbox("أصل السند (يحدد الحالة تلقائياً)", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)", "أخرى"])
        with col3:
            issue = st.text_area("العطل / الشكوى")
            tech_assigned = st.text_input("الفني المستلم", value=current_user)
            
        if st.form_submit_button("حفظ واستخراج إيصال استلام", use_container_width=True):
            if s_id and c_name and t_name:
                try:
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    auto_status = map_document_to_status(doc_origin)
                    run_query('''INSERT INTO service_ledger 
                                (service_id, tool_name, customer_name, phone_number, warranty_status, 
                                 document_origin, reported_issue, technician, status, date_logged) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                              (s_id, t_name, c_name, c_phone, w_status, doc_origin, issue, tech_assigned, auto_status, date_now), fetch=False)
                    st.success(f"✅ تم فتح حساب صيانة وحالته الآن: {auto_status}")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("رقم السند/الحساب موجود مسبقاً.")
            else:
                st.warning("يرجى تعبئة رقم الحساب، اسم الزبون، واسم الأداة كحد أدنى.")

# --- TAB 2: PROCESSING & LEDGER (FINANCIALS) ---
with tab2:
    st.subheader("تحديث حالة الصيانة والمحاسبة")
    
    pending_services = run_query("SELECT service_id, customer_name, tool_name FROM service_ledger WHERE status NOT LIKE '%تم التسليم%'")
    if pending_services:
        options = {f"{row[0]} - {row[1]} ({row[2]})": row[0] for row in pending_services}
        selected_option = st.selectbox("اختر ملف الصيانة", list(options.keys()))
        selected_id = options[selected_option]
        
        curr_data = run_query("SELECT cost_debit, payment_credit, resolution_notes, status, document_origin FROM service_ledger WHERE service_id = ?", (selected_id,))[0]
        
        with st.form("update_service_form"):
            st.info("قم بإدخال التكلفة والدفعات. تحديث 'أصل السند' سيغير حالة الجهاز تلقائياً.")
            
            new_doc_origin = st.selectbox("تحديث أصل السند (يغير الحالة):", 
                                          ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"],
                                          index=0) # Default to first, user should select appropriately
                                          
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                new_cost = st.number_input("تكلفة الصيانة (مدين - Debit)", value=float(curr_data[0]), step=1.0)
            with col_f2:
                new_payment = st.number_input("الدفعة المستلمة (دائن - Credit)", value=float(curr_data[1]), step=1.0)
            with col_f3:
                calc_balance = new_cost - new_payment
                st.metric("الرصيد المتبقي (Balance)", f"{calc_balance:.2f}")
                
            new_notes = st.text_area("البيان / ملاحظات الصيانة", value=curr_data[2] if curr_data[2] else "")
            
            if st.form_submit_button("تحديث الحساب", use_container_width=True):
                auto_new_status = map_document_to_status(new_doc_origin)
                date_res = datetime.now().strftime("%Y-%m-%d") if "تم التسليم" in auto_new_status else ""
                run_query('''UPDATE service_ledger SET 
                             cost_debit = ?, payment_credit = ?, balance = ?, resolution_notes = ?, 
                             document_origin = ?, status = ?, date_resolved = ? WHERE service_id = ?''',
                          (new_cost, new_payment, calc_balance, new_notes, new_doc_origin, auto_new_status, date_res, selected_id), fetch=False)
                st.success(f"✅ تم التحديث! الحالة الجديدة: {auto_new_status}")
                st.rerun()
    else:
        st.info("لا توجد أجهزة قيد الصيانة حالياً.")

# --- TAB 3: LEDGER REPORTS & EXCEL IMPORT ---
with tab3:
    st.subheader("كشف الحساب واستيراد البيانات التاريخية")
    
    if is_admin:
        with st.expander("📥 استيراد ملف الإكسل القديم (تهيئة التطبيق)"):
            st.warning("ارفع ملف `service tools inventory .xlsx`. سيقوم النظام تلقائياً بتفكيك النصوص، استخراج الأسماء والأرقام والمحاسبة وإضافتها للقاعدة.")
            uploaded_legacy = st.file_uploader("رفع ملف كشف الحساب (Excel)", type=["xlsx"])
            if uploaded_legacy and st.button("بدء الاستيراد والمعالجة"):
                with st.spinner("جاري معالجة وتفكيك البيانات..."):
                    df = pd.read_excel(uploaded_legacy, sheet_name='كشف حساب')
                    df = df.dropna(subset=['اسم الزبون'])
                    
                    inserted_count = 0
                    for index, row in df.iterrows():
                        raw_text = str(row['اسم الزبون'])
                        parts = [p.strip() for p in raw_text.split('-')]
                        
                        s_id = parts[0] if len(parts) > 0 else f"SYS-{index}"
                        t_name = parts[1] if len(parts) > 1 else "غير محدد"
                        c_name = parts[2] if len(parts) > 2 else "غير محدد"
                        
                        phone = ""
                        for p in parts:
                            if len(re.sub(r'\D', '', p)) >= 9:
                                phone = p
                                break
                                
                        doc_org = str(row['أصل السند']) if pd.notna(row['أصل السند']) else ""
                        status = map_document_to_status(doc_org)
                        
                        res_notes = str(row['البيان']) if pd.notna(row['البيان']) else ""
                        dt_logged = str(row['التاريخ']).split(' ')[0] if pd.notna(row['التاريخ']) else datetime.now().strftime("%Y-%m-%d")
                        
                        debit = float(row['مدين']) if pd.notna(row['مدين']) else 0.0
                        credit = float(row['دائن']) if pd.notna(row['دائن']) else 0.0
                        bal = float(row['الرصيد الحالي']) if pd.notna(row['الرصيد الحالي']) else 0.0
                        
                        try:
                            run_query('''INSERT OR REPLACE INTO service_ledger 
                                (service_id, tool_name, customer_name, phone_number, document_origin, 
                                 resolution_notes, status, cost_debit, payment_credit, balance, date_logged) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                (s_id, t_name, c_name, phone, doc_org, res_notes, status, debit, credit, bal, dt_logged), fetch=False)
                            inserted_count += 1
                        except Exception as e:
                            pass
                    st.success(f"✅ تمت معالجة واستيراد {inserted_count} سجل بنجاح!")
                    st.rerun()

    query = "SELECT service_id, tool_name, customer_name, phone_number, cost_debit, payment_credit, balance, document_origin, status, date_logged FROM service_ledger"
    ledger_df = pd.DataFrame(run_query(query), columns=['الحساب', 'الأداة', 'الزبون', 'الهاتف', 'مدين', 'دائن', 'الرصيد', 'أصل السند', 'الحالة', 'التاريخ'])
    st.markdown(ledger_df.to_html(index=False), unsafe_allow_html=True)

# --- TAB 4: TIMELINE & ALERTS (SLA FOLLOW-UP) ---
with tab4:
    st.subheader("⏱️ المتابعة وتنبيهات التأخير (Follow-up & Alerts)")
    
    st.info("يقوم النظام تلقائياً بحساب عدد الأيام منذ استلام الجهاز لتنبيهك بالتأخيرات.")
    
    # Query all unfinished jobs
    open_jobs = run_query("SELECT service_id, customer_name, tool_name, phone_number, status, date_logged, balance FROM service_ledger WHERE status NOT LIKE '%تم التسليم%'")
    
    if open_jobs:
        alerts_data = []
        for job in open_jobs:
            s_id, c_name, t_name, phone, status, d_logged, bal = job
            try:
                date_obj = datetime.strptime(d_logged, "%Y-%m-%d")
                days_in_shop = (datetime.now() - date_obj).days
            except:
                days_in_shop = 0
                
            alert_type = "✅ طبيعي"
            if "المعالجة" in status or "الانتظار" in status:
                if days_in_shop > 5: alert_type = "🔴 متأخر جداً في الصيانة"
                elif days_in_shop > 3: alert_type = "🟠 متأخر في الصيانة"
            elif "جاهز" in status:
                if days_in_shop > 7: alert_type = "🔴 العميل تأخر في الاستلام"
                
            alerts_data.append({
                "التنبيه": alert_type,
                "أيام الانتظار": days_in_shop,
                "الزبون": c_name,
                "الهاتف": phone,
                "الحالة الحالية": status,
                "الرصيد المطلوب": bal,
                "رقم السند": s_id
            })
            
        alerts_df = pd.DataFrame(alerts_data).sort_values(by="أيام الانتظار", ascending=False)
        
        # Color coding function for pandas
        def color_alerts(val):
            if "🔴" in str(val): return 'background-color: #ffcccc'
            if "🟠" in str(val): return 'background-color: #ffe4b5'
            return ''
            
        st.dataframe(alerts_df.style.map(color_alerts, subset=['التنبيه']), use_container_width=True)
    else:
        st.success("🎉 لا توجد أي أجهزة قيد الصيانة. جميع الأعمال مكتملة!")
