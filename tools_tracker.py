import streamlit as st
import pandas as pd
from datetime import datetime
import io
import re
from streamlit_gsheets import GSheetsConnection

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="مركز الصيانة - القصر الذهبي", layout="wide", page_icon="🛠️")

st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
            direction: rtl; 
            text-align: right;
        }
        h1, h2, h3, h4, p, span, label, div { overflow-wrap: break-word !important; text-align: right; }
        .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }
        table { width: 100% !important; font-size: 13px !important; background-color: white; }
    </style>
""", unsafe_allow_html=True)

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
        df = conn.read(worksheet="Ledger", ttl=0)
        if df.empty or len(df.columns) < len(EXPECTED_COLUMNS):
            return pd.DataFrame(columns=EXPECTED_COLUMNS)
        for col in EXPECTED_COLUMNS:
            if col not in ['cost_debit', 'payment_credit', 'balance']:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str).replace({'nan': '', 'None': ''})
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
# AUTHENTICATION & SIDEBAR NAVIGATION
# ==========================================
if 'logged_in_user' not in st.session_state: st.session_state['logged_in_user'] = None

USERS = {"admin": {"pass": "123", "role": "مدير النظام (Admin)"}, "tech": {"pass": "123", "role": "فني صيانة (Technician)"}}

st.sidebar.title("🛠️ مركز الصيانة")
if st.session_state['logged_in_user'] is None:
    st.sidebar.subheader("🔐 تسجيل الدخول")
    with st.sidebar.form("login_form"):
        username_input = st.text_input("اسم المستخدم")
        password_input = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول", use_container_width=True):
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

st.sidebar.divider()
st.sidebar.subheader("📌 التنقل السريع")
menu = st.sidebar.radio("اختر القسم:", [
    "📊 لوحة القيادة (Dashboard)",
    "📥 استلام جهاز جديد",
    "🔧 فحص وتحديث الأجهزة",
    "⏱️ تنبيهات التأخير والمتابعة",
    "📊 كشف الحساب العام والاستيراد"
])

live_df = get_ledger()

# ==========================================
# 1. DASHBOARD / KPI VIEW
# ==========================================
if menu == "📊 لوحة القيادة (Dashboard)":
    st.title("📊 لوحة قيادة مركز الصيانة")
    st.markdown("مراجعة سريعة لأداء المركز والأجهزة النشطة.")
    
    if not live_df.empty:
        total_jobs = len(live_df)
        active_jobs = len(live_df[~live_df['status'].astype(str).str.contains('تم التسليم', na=False)])
        ready_jobs = len(live_df[live_df['status'].astype(str).str.contains('جاهز', na=False)])
        
        try:
            total_balance = live_df['balance'].astype(float).sum()
        except:
            total_balance = 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("إجمالي السجلات", total_jobs)
        col2.metric("أجهزة قيد العمل", active_jobs)
        col3.metric("جاهزة للاستلام", ready_jobs)
        col4.metric("إجمالي الأرصدة المعلقة ($)", f"{total_balance:.2f}")
        
        st.divider()
        st.subheader("📍 توزيع الأجهزة حسب الفروع")
        if 'service_id' in live_df.columns:
            temp_df = live_df.copy()
            temp_df['الفرع'] = temp_df['service_id'].apply(get_branch)
            branch_counts = temp_df['الفرع'].value_counts()
            st.bar_chart(branch_counts)
    else:
        st.info("لا توجد بيانات سحابية مسجلة حتى الآن.")

# ==========================================
# 2. NEW INTAKE
# ==========================================
elif menu == "📥 استلام جهاز جديد":
    st.title("📥 استلام جهاز صيانة جديد")
    
    with st.form("intake_form"):
        col1, col2 = st.columns(2)
        with col1:
            s_id = st.text_input("رقم الحساب / السند (يبدأ بـ S لصيدا، D لدرعا، V لـ وكيل)")
            c_name = st.text_input("اسم الزبون")
            c_phone = st.text_input("رقم الهاتف")
            w_status = st.selectbox("حالة الكفالة", ["خارج الكفالة", "ضمن كفالة", "ضمن كفالة يومين"])
        with col2:
            t_name = st.text_input("اسم الأداة / الموديل")
            doc_origin = st.selectbox("أصل السند (يحدد الحالة تلقائياً)", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "خ صيانة: (تحميل على الوكيل)"])
            issue = st.text_area("العطل / الشكوى المرصودة")
            tech_assigned = st.text_input("الفني المستلم", value=current_user)
            
        submitted = st.form_submit_button("حفظ وحفظ سحابياً", use_container_width=True)
        if submitted:
            if s_id and c_name and t_name:
                if not live_df.empty and s_id in live_df['service_id'].values:
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
                    
                    updated_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_ledger(updated_df)
                    st.success(f"✅ تم فتح حساب صيانة وحفظه بنجاح! الحالة: {auto_status}")
            else:
                st.warning("يرجى تعبئة الحقول الأساسية (رقم السند، اسم الزبون، الأداة).")

# ==========================================
# 3. PROCESSING & LEDGER
# ==========================================
elif menu == "🔧 فحص وتحديث الأجهزة":
    st.title("🔧 فحص وتحديث كشف الحساب")
    
    if is_admin:
        pending_mask = pd.Series([True] * len(live_df))
    else:
        pending_mask = ~live_df['status'].astype(str).str.contains('تم التسليم', na=False)
        
    filtered_df = live_df[pending_mask] if not live_df.empty else pd.DataFrame()
    
    if not filtered_df.empty:
        options = {f"{row['service_id']} - {row['customer_name']} ({row['tool_name']})": row['service_id'] for _, row in filtered_df.iterrows()}
        selected_option = st.selectbox("اختر ملف الصيانة للتحديث:", list(options.keys()))
        selected_id = options[selected_option]
        
        curr_data = live_df[live_df['service_id'] == selected_id].iloc[0]
        
        with st.form("update_service_form"):
            st.info(f"الزبون: {curr_data['customer_name']} | الأداة: {curr_data['tool_name']}")
            
            doc_options = ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"]
            try:
                curr_idx = [i for i, opt in enumerate(doc_options) if str(curr_data['document_origin']) in opt][0]
            except IndexError:
                curr_idx = 0
                
            new_doc_origin = st.selectbox("تحديث أصل السند (يغير الحالة):", doc_options, index=curr_idx)
            auto_new_status = map_document_to_status(new_doc_origin)
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                new_cost = st.number_input("تكلفة الصيانة (مدين - Debit)", value=float(curr_data['cost_debit']) if pd.notna(curr_data['cost_debit']) and str(curr_data['cost_debit']).strip() != "" else 0.0, step=1.0)
            with col_f2:
                new_payment = st.number_input("الدفعة المستلمة (دائن - Credit)", value=float(curr_data['payment_credit']) if pd.notna(curr_data['payment_credit']) and str(curr_data['payment_credit']).strip() != "" else 0.0, step=1.0)
            with col_f3:
                calc_balance = new_cost - new_payment
                st.metric("الرصيد المتبقي (Balance)", f"{calc_balance:.2f}")
                
            new_notes = st.text_area("البيان / ملاحظات الصيانة", value=str(curr_data['resolution_notes']) if pd.notna(curr_data['resolution_notes']) else "")
            
            confirm_collection = True
            if "تم التسليم" in auto_new_status:
                st.warning("⚠️ إقفال الملف: سيتم تأكيد التسليم وإخفاء الجهاز ولن يمكن التراجع (إلا بواسطة المدير).")
                confirm_collection = st.checkbox("✅ أؤكد استلام المبلغ وتسليم الجهاز للعميل.")

            if st.form_submit_button("حفظ التحديثات سحابياً", use_container_width=True):
                if "تم التسليم" in auto_new_status and not confirm_collection:
                    st.error("❌ يجب تحديد مربع تأكيد التسليم لإتمام العملية وإقفال الملف.")
                else:
                    date_res = datetime.now().strftime("%Y-%m-%d") if "تم التسليم" in auto_new_status else ""
                    idx = live_df.index[live_df['service_id'] == selected_id][0]
                    live_df.at[idx, 'cost_debit'] = new_cost
                    live_df.at[idx, 'payment_credit'] = new_payment
                    live_df.at[idx, 'balance'] = calc_balance
                    live_df.at[idx, 'resolution_notes'] = new_notes
                    live_df.at[idx, 'document_origin'] = new_doc_origin
                    live_df.at[idx, 'status'] = auto_new_status
                    live_df.at[idx, 'date_resolved'] = date_res
                    
                    save_ledger(live_df)
                    st.success("✅ تم تحديث كشف الحساب وحفظه بنجاح!")
                    st.rerun()
    else:
        st.info("لا توجد أجهزة قيد الصيانة حالياً.")

# ==========================================
# 4. ALERTS & TIMELINE
# ==========================================
elif menu == "⏱️ تنبيهات التأخير والمتابعة":
    st.title("⏱️ متابعة التأخير وحالة الأجهزة")
    
    if not live_df.empty:
        open_jobs = live_df[~live_df['status'].astype(str).str.contains('تم التسليم', na=False)]
        
        if not open_jobs.empty:
            alerts_data = []
            for _, row in open_jobs.iterrows():
                try:
                    date_obj = datetime.strptime(str(row['date_logged']).split(' ')[0], "%Y-%m-%d")
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
                    "الحالة الحالية": row['status'],
                    "الزبون": row['customer_name'],
                    "الهاتف": row['phone_number'],
                    "الرصيد المطلوب": format_currency(row['balance']), 
                    "رقم السند": row['service_id']
                })
                
            alerts_df = pd.DataFrame(alerts_data)

            col_filt1, col_filt2, col_filt3 = st.columns(3)
            with col_filt1:
                selected_branches = st.multiselect("📍 الفرع:", options=alerts_df['الفرع (Branch)'].unique().tolist(), default=alerts_df['الفرع (Branch)'].unique().tolist())
            with col_filt2:
                selected_statuses = st.multiselect("📋 الحالة:", options=alerts_df['الحالة الحالية'].unique().tolist(), default=alerts_df['الحالة الحالية'].unique().tolist())
            with col_filt3:
                selected_alerts = st.multiselect("⚠️ التنبيه:", options=alerts_df['التنبيه'].unique().tolist(), default=alerts_df['التنبيه'].unique().tolist())
                
            filtered_alerts_df = alerts_df[
                (alerts_df['الفرع (Branch)'].isin(selected_branches)) &
                (alerts_df['الحالة الحالية'].isin(selected_statuses)) &
                (alerts_df['التنبيه'].isin(selected_alerts))
            ].sort_values(by="أيام الانتظار", ascending=False)
            
            def color_alerts(val):
                if "🔴" in str(val): return 'background-color: #ffcccc; font-weight: bold;'
                if "🟠" in str(val): return 'background-color: #ffe4b5; font-weight: bold;'
                return ''
                
            st.dataframe(filtered_alerts_df.style.map(color_alerts, subset=['التنبيه']), use_container_width=True)
        else:
            st.success("🎉 لا توجد أي أجهزة متأخرة أو قيد الانتظار.")

# ==========================================
# 5. REPORTS & LEGACY IMPORT
# ==========================================
elif menu == "📊 كشف الحساب العام والاستيراد":
    st.title("📊 كشف الحساب العام وسجلات الإدارة")
    
    if is_admin:
        with st.expander("📥 استيراد ملف الإكسل القديم إلى Google Sheets"):
            st.warning("رفع ملف الإكسل القديم لتفكيكه ودمجه في السحابة.")
            uploaded_legacy = st.file_uploader("رفع ملف كشف الحساب (Excel)", type=["xlsx"])
            if uploaded_legacy and st.button("بدء الاستيراد السحابي"):
                with st.spinner("جاري تفكيك ورفع البيانات..."):
                    df = pd.read_excel(uploaded_legacy, sheet_name='كشف حساب')
                    df = df.dropna(subset=['اسم الزبون'])
                    
                    new_records = []
                    for index, row in df.iterrows():
                        raw_text = str(row['اسم الزبون'])
                        parts = [p.strip() for p in raw_text.split('-')]
                        s_id = parts[0] if len(parts) > 0 else f"SYS-{index}"
                        if not live_df.empty and s_id in live_df['service_id'].values: continue 
                        
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
                        st.success(f"✅ تمت المزامنة بنجاح! تم رفع {len(new_records)} سجل جديد.")
                        st.rerun()

    display_df = live_df.copy()
    if not display_df.empty:
        display_df.insert(1, 'Branch', display_df['service_id'].apply(get_branch))
        display_df['cost_debit'] = display_df['cost_debit'].apply(format_currency)
        display_df['payment_credit'] = display_df['payment_credit'].apply(format_currency)
        display_df['balance'] = display_df['balance'].apply(format_currency)

    st.markdown(display_df.to_html(index=False), unsafe_allow_html=True)
