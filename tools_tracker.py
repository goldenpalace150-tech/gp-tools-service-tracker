import streamlit as st
import pandas as pd
from datetime import datetime
import re
import io
import requests
import base64
import urllib.parse
from streamlit_gsheets import GSheetsConnection

# ==========================================
# SYSTEM CONFIGURATION & API
# ==========================================
IMGBB_API_KEY = "c6e484b83af4bb39c92e1782cc6ce5e6"

st.set_page_config(page_title="Al-Qasr Al-Zahabi ERP", layout="wide", page_icon="🏢")

st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        h1, h2, h3, h4, p, span, label, div { text-align: right; }
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 2px solid #e2e8f0; }
        .stTabs [data-baseweb="tab"] { background-color: transparent; border-radius: 4px 4px 0 0; padding: 10px 20px; font-weight: 600; color: #4a5568; }
        .stTabs [aria-selected="true"] { border-bottom: 3px solid #3182ce; color: #2b6cb0; background-color: #ebf8ff; }
        .erp-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .locked-card { background: #fff5f5; padding: 20px; border: 1px solid #feb2b2; border-radius: 8px; margin-bottom: 20px; }
        .invoice-box { background: white; padding: 30px; border: 1px solid #e2e8f0; border-radius: 8px; max-width: 800px; margin: auto; }
        .invoice-header { text-align: center; border-bottom: 2px solid #2b6cb0; padding-bottom: 15px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE ORM (DocType Engine)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

SCHEMA = {
    "Ledger": [
        "service_id", "tool_name", "customer_name", "phone_number", "warranty_status", "document_origin", 
        "reported_issue", "technician", "status", "cost_debit", "payment_credit", "balance", 
        "spare_parts", "resolution_notes", "remarks", "date_logged", "date_resolved",
        "accessories", "loaner_item", "priority", "tool_photo_link"
    ],
    "Stock": ["item_code", "item_name", "quantity", "price"],
    "Hawara": ["order_id", "order_type", "linked_service_id", "courier", "delivery_note", "document_link", "status", "date_logged"],
    "Dispatch": ["dispatch_id", "service_id", "customer_name", "courier", "delivery_note", "document_link", "date"]
}

def get_status_rank(val):
    s = str(val)
    if "قبض" in s or "Collected" in s: return 4
    if "خ صيانة" in s or "حساب وكيل" in s: return 3
    if "مبيع خ ص" in re.sub(r'\s+', ' ', s).strip() or "جاهز" in s: return 2
    if "اد خ ص" in re.sub(r'\s+', ' ', s).strip() or "المعالجة" in s: return 1
    return 0

def map_document_to_status(doc_string, cost=0.0):
    doc = re.sub(r'\s+', ' ', str(doc_string)).strip()
    try: cost_val = float(cost)
    except: cost_val = 0.0
    if "قبض" in doc: return "تم التسليم للزبون (Customer Collected)"
    if "خ صيانة" in doc: return "تم التسليم - حساب وكيل (Partner Collected)"
    if "مبيع خ ص" in doc: return "جاهز للتسليم (بدون تكلفة/كفالة)" if cost_val == 0.0 else "جاهز للتسليم (Ready)"
    if "اد خ ص" in doc: return "قيد المعالجة (In Progress)"
    return "قيد الانتظار"

def deduplicate_ledger(df):
    if df.empty or 'service_id' not in df.columns: return df
    df['service_id'] = df['service_id'].astype(str) # Double protection against Pandas float sorting crashes
    df['rank'] = df['document_origin'].apply(get_status_rank)
    df = df.sort_values(by=['service_id', 'rank'], ascending=[True, True])
    return df.groupby('service_id', as_index=False).last().drop(columns=['rank'], errors='ignore')

def get_doctype(doctype_name):
    try:
        df = conn.read(worksheet=doctype_name, ttl=0)
        
        # FIX: Drop phantom blank rows returned by Google Sheets to prevent math crashes
        df = df.dropna(how='all')
        
        for col in SCHEMA[doctype_name]:
            if col not in df.columns: df[col] = ""
            
        if doctype_name == "Ledger":
            # FIX: Clean empty/NaN service IDs BEFORE processing
            df['service_id'] = df['service_id'].astype(str).replace({'nan': '', 'None': ''})
            df = df[df['service_id'].str.strip() != ""]
            
            for col in SCHEMA["Ledger"]:
                if col not in ['cost_debit', 'payment_credit', 'balance']:
                    df[col] = df[col].fillna("").astype(str).replace({'nan': '', 'None': ''})
            
            # FIX: Force strict numeric types for financial fields so the dashboard never crashes
            for col in ['cost_debit', 'payment_credit', 'balance']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                
            df.loc[df['spare_parts'] == "", 'spare_parts'] = "لا حاجة / متوفرة"
            return deduplicate_ledger(df)
            
        return df
    except Exception as e: 
        # FIX: Never fail silently again. Show the exact error if Google Sheets rejects the connection.
        st.error(f"⚠️ خطأ في قراءة قاعدة البيانات ({doctype_name}): {str(e)}")
        return pd.DataFrame(columns=SCHEMA[doctype_name])

def save_doctype(doctype_name, df):
    if doctype_name == "Ledger": 
        df = deduplicate_ledger(df)
        df = df[df['service_id'].astype(str).str.strip() != ""] # Clean before saving
    conn.update(worksheet=doctype_name, data=df)

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name='Export')
    return output.getvalue()

def upload_to_cloud(file_buffer):
    try:
        b64_img = base64.b64encode(file_buffer.getvalue()).decode("utf-8")
        res = requests.post(f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}", data={"image": b64_img})
        if res.status_code == 200: return res.json()["data"]["url"]
    except: return ""
    return ""

def generate_next_id(branch_code, df):
    if df.empty: return f"{branch_code}1"
    branch_records = df[df['service_id'].astype(str).str.startswith(branch_code, na=False)]
    if branch_records.empty: return f"{branch_code}1"
    
    max_num = 0
    for sid in branch_records['service_id']:
        num_part = re.sub(r'\D', '', str(sid))
        if num_part: max_num = max(max_num, int(num_part))
    return f"{branch_code}{max_num + 1}"

# ==========================================
# AUTHENTICATION & WORKSPACE ROUTING
# ==========================================
if 'logged_in_user' not in st.session_state: st.session_state['logged_in_user'] = None
if 'current_module' not in st.session_state: st.session_state['current_module'] = 'Workspace'

USERS = {"admin": {"pass": "123", "role": "System Administrator"}, "tech": {"pass": "123", "role": "Support Agent"}}

if st.session_state['logged_in_user'] is None:
    st.markdown("<div class='erp-card' style='max-width: 400px; margin: 100px auto; text-align: center;'>", unsafe_allow_html=True)
    st.title("🏢 ERP Login")
    st.subheader("القصر الذهبي للمعدات")
    with st.form("login_form"):
        u_in = st.text_input("اسم المستخدم (Username)")
        p_in = st.text_input("كلمة المرور (Password)", type="password")
        if st.form_submit_button("تسجيل الدخول", use_container_width=True):
            if u_in in USERS and USERS[u_in]["pass"] == p_in:
                st.session_state['logged_in_user'] = u_in
                st.rerun()
            else: st.error("بيانات الدخول غير صحيحة.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

current_user = st.session_state['logged_in_user']
is_admin = ("Administrator" in USERS[current_user]["role"])

# Load all DocTypes
ledger_df = get_doctype("Ledger")
stock_df = get_doctype("Stock")
hawara_df = get_doctype("Hawara")
dispatch_df = get_doctype("Dispatch")

stock_list = stock_df['item_name'].dropna().unique().tolist() if not stock_df.empty else []

# ==========================================
# ERP SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.title("🏢 ERPNext Workspace")
    st.markdown(f"**المستخدم:** {current_user} <br> **الدور:** {USERS[current_user]['role']}", unsafe_allow_html=True)
    st.divider()
    
    st.caption("العمليات الأساسية (CORE MODULES)")
    if st.button("🏠 مساحة العمل (Workspace)", use_container_width=True): st.session_state['current_module'] = 'Workspace'
    if st.button("📺 شاشة الورشة (TV Display)", use_container_width=True): st.session_state['current_module'] = 'TV_Display'
    if st.button("🛠️ الدعم والصيانة (Support)", use_container_width=True): st.session_state['current_module'] = 'Support'
    if st.button("📦 المخزون (Stock)", use_container_width=True): st.session_state['current_module'] = 'Stock'
    if st.button("🚚 اللوجستيات (Logistics)", use_container_width=True): st.session_state['current_module'] = 'Logistics'
    
    st.caption("المالية والتقارير (ACCOUNTING)")
    if st.button("💰 المحاسبة (Accounting)", use_container_width=True): st.session_state['current_module'] = 'Accounting'
    
    st.divider()
    if st.button("🚪 تسجيل الخروج (Logout)", use_container_width=True):
        st.session_state['logged_in_user'] = None
        st.rerun()

# ==========================================
# MODULE 1: WORKSPACE (DASHBOARD)
# ==========================================
if st.session_state['current_module'] == 'Workspace':
    st.title("مساحة العمل الموحدة (Workspace)")
    
    active_count = len(ledger_df[~ledger_df['status'].str.contains('تم التسليم', na=False)]) if not ledger_df.empty else 0
    ready_count = len(ledger_df[ledger_df['status'].str.contains('جاهز', na=False)]) if not ledger_df.empty else 0
    total_rev = float(ledger_df['cost_debit'].sum()) if not ledger_df.empty else 0.0

    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='erp-card'><h3>🛠️ صيانة مفتوحة</h3><h1>{active_count}</h1></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='erp-card'><h3>✅ أجهزة جاهزة للتسليم</h3><h1>{ready_count}</h1></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='erp-card'><h3>💰 إجمالي المبيعات</h3><h1>${total_rev:,.2f}</h1></div>", unsafe_allow_html=True)

    c_chart1, c_chart2 = st.columns(2)
    if not ledger_df.empty:
        with c_chart1:
            st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
            st.subheader("📊 توزع حالات الصيانة")
            st.bar_chart(ledger_df['status'].value_counts())
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_chart2:
            st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
            st.subheader("👨‍🔧 أداء الفنيين (الأجهزة المسلمة)")
            completed_df = ledger_df[ledger_df['status'].str.contains('تم التسليم', na=False)]
            if not completed_df.empty:
                tech_perf = completed_df['technician'].value_counts()
                st.bar_chart(tech_perf, color="#38A169")
            else:
                st.info("لا توجد أجهزة مسلمة بعد لحساب الأداء.")
            st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MODULE 2: TV WORKSHOP DISPLAY (KIOSK MODE)
# ==========================================
elif st.session_state['current_module'] == 'TV_Display':
    st.components.v1.html("<script>setTimeout(function(){window.parent.location.reload();}, 60000);</script>", height=0)
    
    st.markdown("""
        <style>
            header {visibility: hidden;}
            .tv-card-urgent { background: #ffe5e5; border-right: 15px solid #e53e3e; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .tv-card-delayed { background: #fffaf0; border-right: 15px solid #dd6b20; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .tv-title { font-size: 32px; font-weight: bold; color: #1a202c; margin-bottom: 10px; }
            .tv-details { font-size: 24px; color: #4a5568; }
            .tv-days { font-size: 35px; font-weight: bold; float: left; margin-top: -10px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 40px;'>شاشة متابعة الورشة (Live Queue)</h1>", unsafe_allow_html=True)

    if not ledger_df.empty:
        open_jobs = ledger_df[~ledger_df['status'].str.contains('تم التسليم', na=False)]
        display_items = []
        for _, r in open_jobs.iterrows():
            try: 
                days = (datetime.now() - pd.to_datetime(str(r['date_logged']).split(' ')[0])).days
            except: 
                days = 0
            
            is_urgent = "عاجل" in str(r.get('priority', ''))
            
            if is_urgent or days >= 3:
                display_items.append({
                    "days": days,
                    "urgent": is_urgent,
                    "sid": r['service_id'],
                    "tool": r['tool_name'],
                    "issue": r['reported_issue'],
                    "status": r['status']
                })
        
        display_items = sorted(display_items, key=lambda x: (not x['urgent'], -x['days']))
        
        if display_items:
            for item in display_items:
                card_class = "tv-card-urgent" if item['urgent'] else "tv-card-delayed"
                tag = "🔥 عاجل جداً" if item['urgent'] else "⚠️ متأخر"
                color = "#e53e3e" if item['urgent'] else "#dd6b20"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="tv-days" style="color: {color};">{item['days']}<br><span style="font-size:16px;">أيام</span></div>
                    <div class="tv-title">{tag} | {item['sid']} - {item['tool']}</div>
                    <div class="tv-details"><b>العطل:</b> {item['issue']} <br> <b>الحالة الآن:</b> {item['status']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align: center; color: #38a169; margin-top: 100px;'>✅ العمل ممتاز! جميع الأجهزة جاهزة.</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #38a169; margin-top: 100px;'>✅ العمل ممتاز! لا توجد مهام حالياً.</h1>", unsafe_allow_html=True)

# ==========================================
# MODULE 3: SUPPORT & MAINTENANCE
# ==========================================
elif st.session_state['current_module'] == 'Support':
    st.title("🛠️ وحدة الدعم والصيانة (Support Desk)")
    tab1, tab2, tab3 = st.tabs(["➕ بطاقة صيانة جديدة (New Ticket)", "🔄 تحديث الملف (Update & View)", "⚠️ قائمة المهام (SLA / Queue)"])
    
    with tab1:
        st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
        with st.form("intake_form", clear_on_submit=True):
            st.subheader("تفاصيل استلام جهاز (Intake Form)")
            
            c_amn1, c_amn2, c_amn3 = st.columns(3)
            with c_amn1:
                warranty = st.selectbox("حالة الكفالة (Warranty)", ["خارج الكفالة", "ضمن كفالة"])
            with c_amn2:
                priority = st.selectbox("أولوية العمل (Priority)", ["عادي (Normal)", "عاجل 🔥 (Rush Job)"])
            with c_amn3:
                loaner = st.text_input("جهاز بديل معار للزبون (Loaner Item S/N - اختياري)")
            
            st.divider()
            
            c1, c2, c3 = st.columns(3)
            with c1:
                branch_select = st.selectbox("الفرع (Branch Prefix)", ["صيدا (S)", "درعا (D)", "وكيل / شريك (V)"])
                c_name = st.text_input("اسم الزبون (Customer Name)")
            with c2:
                c_phone = st.text_input("رقم الهاتف (Phone)")
                t_name_dropdown = st.selectbox("الجهاز (Item Lookup)", options=["أخرى (إدخال يدوي)"] + stock_list)
                t_name_manual = st.text_input("اسم الجهاز اليدوي (Manual Entry)")
            with c3:
                doc_origin = st.selectbox("الحالة المحاسبية (Origin)", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "خ صيانة: (تحميل على الوكيل)"])
                accessories = st.text_input("الملحقات المستلمة (Accessories) ⚠️ إلزامي", placeholder="مثال: بطارية، شاحن، حقيبة أو 'لا يوجد'")
                
            issue = st.text_area("العطل المرصود (Reported Issue)")
            
            st.markdown("📷 **التوثيق البصري (Media Documentation)**")
            photo_buffer = st.camera_input("التقاط صورة للجهاز أو الملحقات كإثبات حالة (Take Photo)")

            if st.form_submit_button("إنشاء السند (Create Document)", use_container_width=True):
                final_t_name = t_name_manual if t_name_dropdown == "أخرى (إدخال يدوي)" and t_name_manual else t_name_dropdown
                
                if not accessories.strip():
                    st.error("❌ حقل 'الملحقات المستلمة' إلزامي لمنع فقدان الأغراض. (اكتب 'لا يوجد' إن لم يسلمك شيء).")
                elif c_name and final_t_name and final_t_name != "أخرى (إدخال يدوي)":
                    branch_code = "S" if "S" in branch_select else "D" if "D" in branch_select else "V"
                    auto_id = generate_next_id(branch_code, ledger_df)
                    date_now = datetime.now().strftime("%Y-%m-%d")
                    
                    photo_url = upload_to_cloud(photo_buffer) if photo_buffer else ""
                    
                    new_row = {
                        "service_id": auto_id, "tool_name": final_t_name, "customer_name": c_name, "phone_number": c_phone,
                        "warranty_status": warranty, "document_origin": doc_origin, "reported_issue": issue,
                        "technician": current_user, "status": map_document_to_status(doc_origin, 0.0), "cost_debit": 0.0, "payment_credit": 0.0,
                        "balance": 0.0, "spare_parts": "لا حاجة / متوفرة", "resolution_notes": "", "remarks": "", 
                        "date_logged": date_now, "date_resolved": "",
                        "accessories": accessories, "loaner_item": loaner, "priority": priority, "tool_photo_link": photo_url
                    }
                    save_doctype("Ledger", pd.concat([ledger_df, pd.DataFrame([new_row])], ignore_index=True))
                    st.success(f"✅ تم إنشاء السند بنجاح برقم: {auto_id}")
                else: 
                    st.error("❌ يرجى تعبئة اسم الزبون واسم الجهاز.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        if not ledger_df.empty:
            opts = {f"{r.get('priority', '')} {r['service_id']} - {r['customer_name']}": r['service_id'] for _, r in ledger_df.iterrows()}
            sel_id = opts[st.selectbox("ابحث عن السند (Search Document):", list(opts.keys()))]
            row_data = ledger_df[ledger_df['service_id'] == sel_id].iloc[0]
            
            is_locked = "تم التسليم" in str(row_data['status'])
            is_warranty = "ضمن" in str(row_data.get('warranty_status', ''))
            
            if is_locked:
                st.markdown("<div class='locked-card'>", unsafe_allow_html=True)
                st.markdown(f"### 🔒 مستند مغلق (Submitted/Locked)")
                st.write(f"**رقم السند:** {sel_id} | **الزبون:** {row_data['customer_name']}")
                st.write(f"**حالة التسليم:** {row_data['status']} في تاريخ {row_data.get('date_resolved', '')}")
                st.write(f"**التكلفة النهائية:** ${float(row_data['cost_debit']):.2f}")
                if row_data.get('tool_photo_link'): st.markdown(f"[📸 عرض صورة الجهاز عند الاستلام]({row_data['tool_photo_link']})")
                st.write("هذا الملف مغلق نهائياً لحماية القيود المالية. للطباعة يرجى التوجه لقسم المحاسبة.")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
                
                c_info1, c_info2 = st.columns(2)
                with c_info1:
                    st.caption("الملحقات المستلمة (Accessories):")
                    st.write(f"🎒 {row_data.get('accessories', 'غير مسجل')}")
                with c_info2:
                    if row_data.get('tool_photo_link'): st.markdown(f"📸 [عرض الصورة المرفقة للصيانة]({row_data['tool_photo_link']})")
                
                with st.form("update_form"):
                    doc_options = ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"]
                    try: curr_i = [i for i, o in enumerate(doc_options) if str(row_data['document_origin']) in o][0]
                    except: curr_i = 0
                    
                    c_a, c_b = st.columns(2)
                    with c_a: new_doc = st.selectbox("تحديث الحالة المحاسبية:", doc_options, index=curr_i)
                    with c_b: 
                        sp_opts = ["لا حاجة / متوفرة", "بانتظار شحن مجاني", "بانتظار شحن عادي"]
                        try: sp_i = sp_opts.index(str(row_data['spare_parts']))
                        except: sp_i = 0
                        new_spare = st.selectbox("حالة قطع الغيار:", sp_opts, index=sp_i)
                    
                    if is_warranty:
                        st.info("🛡️ هذا الجهاز ضمن الكفالة، تم تصفير التكلفة تلقائياً.")
                        cost = 0.0
                        pay = 0.0
                    else:
                        col1, col2, col3 = st.columns(3)
                        with col1: cost = st.number_input("التكلفة (Debit)", value=float(row_data['cost_debit'] or 0), step=1.0)
                        with col2: pay = st.number_input("الدفعة (Credit)", value=float(row_data['payment_credit'] or 0), step=1.0)
                        with col3: st.metric("الرصيد المتبقي (Balance)", f"${cost - pay:.2f}")
                        
                    new_status = map_document_to_status(new_doc, cost)
                    c_n1, c_n2 = st.columns(2)
                    with c_n1: notes = st.text_area("ملاحظات الإصلاح (Resolution)", value=str(row_data.get('resolution_notes', '')))
                    with c_n2: remarks_update = st.text_area("تحديثات إضافية (Remarks)", value=str(row_data.get('remarks', '')))
                    
                    confirm = True
                    if "تم التسليم" in new_status: confirm = st.checkbox("✅ تأكيد إغلاق الملف نهائياً (Confirm Lock)")

                    if st.form_submit_button("تحديث السجل (Update Document)", use_container_width=True):
                        if "تم التسليم" in new_status and not confirm: st.error("❌ يرجى تأكيد الإغلاق النهائي للملف.")
                        else:
                            idx = ledger_df.index[ledger_df['service_id'] == sel_id][0]
                            ledger_df.at[idx, 'cost_debit'] = cost
                            ledger_df.at[idx, 'payment_credit'] = pay
                            ledger_df.at[idx, 'balance'] = cost - pay
                            ledger_df.at[idx, 'resolution_notes'] = notes
                            ledger_df.at[idx, 'remarks'] = remarks_update
                            ledger_df.at[idx, 'document_origin'] = new_doc
                            ledger_df.at[idx, 'status'] = new_status
                            ledger_df.at[idx, 'spare_parts'] = new_spare
                            ledger_df.at[idx, 'date_resolved'] = datetime.now().strftime("%Y-%m-%d") if "تم التسليم" in new_status else ""
                            save_doctype("Ledger", ledger_df)
                            st.success("✅ تم التحديث بنجاح!")
                            st.rerun()

                if row_data['phone_number']:
                    phone_clean = re.sub(r'\D', '', str(row_data['phone_number']))
                    wa_msg = f"مرحباً {row_data['customer_name']}, جهازك ({row_data['tool_name']}) جاهز للاستلام من القصر الذهبي."
                    wa_link = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(wa_msg)}"
                    st.markdown(f"<a href='{wa_link}' target='_blank'><button style='background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; width:100%; font-size:16px; font-weight:bold;'>💬 إرسال إشعار للزبون (WhatsApp)</button></a>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("لا توجد ملفات حالياً. يرجى إنشاء سند صيانة جديد.")

    with tab3:
        st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
        if not ledger_df.empty:
            open_jobs = ledger_df[~ledger_df['status'].str.contains('تم التسليم', na=False)]
            alerts = []
            for _, r in open_jobs.iterrows():
                try: 
                    days = (datetime.now() - pd.to_datetime(str(r['date_logged']).split(' ')[0])).days
                except: 
                    days = 0
                
                is_urgent = "عاجل" in str(r.get('priority', ''))
                
                alert = "✅ طبيعي"
                if "المعالجة" in str(r['status']) or "الانتظار" in str(r['status']):
                    if days > 5: alert = "🔴 متأخر جداً"
                    elif days > 3: alert = "🟠 متأخر"
                elif "جاهز" in str(r['status']) and days > 7: alert = "🔴 تأخر بالاستلام"
                
                alerts.append({
                    "أولوية": "عاجل 🔥" if is_urgent else "عادي",
                    "الحالة (SLA)": alert, 
                    "أيام التوقف": days, 
                    "السند": r['service_id'], 
                    "الزبون": r['customer_name'], 
                    "الجهاز": r['tool_name'],
                    "الوضع": r['status']
                })
            
            df_alerts = pd.DataFrame(alerts)
            if not df_alerts.empty:
                c_filt1, c_filt2 = st.columns([3, 1])
                with c_filt1:
                    all_statuses = df_alerts['الوضع'].unique().tolist()
                    selected_statuses = st.multiselect("🔍 تصفية حسب الوضع (Filter by Status):", options=all_statuses, default=all_statuses)
                
                filtered_alerts = df_alerts[df_alerts['الوضع'].isin(selected_statuses)]
                
                with c_filt2:
                    st.metric("العدد (Count)", len(filtered_alerts))
                
                filtered_alerts = filtered_alerts.sort_values(by=["أولوية", "أيام التوقف"], ascending=[False, False])
                st.dataframe(filtered_alerts, use_container_width=True)
            else:
                st.success("✅ ممتاز! جميع الأجهزة جاهزة أو تم تسليمها، ولا توجد مهام متأخرة أو قيد المعالجة.")
        else:
            st.info("📂 قاعدة البيانات فارغة. يرجى إنشاء سند جديد أو استيراد ملف الأمين.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MODULE 4: STOCK & INVENTORY
# ==========================================
elif st.session_state['current_module'] == 'Stock':
    st.title("📦 وحدة المستودعات والمخزون (Stock Module)")
    
    st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
    if not stock_df.empty:
        stock_df['quantity'] = pd.to_numeric(stock_df['quantity'], errors='coerce').fillna(0)
        low_stock = stock_df[stock_df['quantity'] <= 2]
        if not low_stock.empty:
            st.error(f"⚠️ يوجد {len(low_stock)} أصناف تتطلب إعادة طلب (Reorder Alert).")
    
    c1, c2 = st.columns(2)
    with c1: st.download_button("📥 تصدير السجل (Export)", data=convert_df_to_excel(stock_df) if not stock_df.empty else b"", file_name="Stock_Master.xlsx", use_container_width=True)
    with c2:
        with st.expander("📤 استيراد لائحة الأسعار (Import List)"):
            uploaded_stock = st.file_uploader("رفع ملف Excel", type=["xlsx"])
            if uploaded_stock and st.button("استيراد (Import)"):
                raw = pd.read_excel(uploaded_stock)
                if 'MtCode' in raw.columns and 'اسم المادة' in raw.columns:
                    p_col = 'الجملة' if 'الجملة' in raw.columns else raw.columns[-1]
                    new_items = raw[['MtCode', 'اسم المادة', p_col]].copy()
                    new_items.columns = ['item_code', 'item_name', 'price']
                    new_items = new_items.dropna(subset=['item_code'])
                    new_items['price'] = pd.to_numeric(new_items['price'], errors='coerce').fillna(0.0)
                    new_items['quantity'] = 0 
                    if not stock_df.empty:
                        q_dict = dict(zip(stock_df['item_code'], stock_df['quantity']))
                        new_items['quantity'] = new_items['item_code'].map(q_dict).fillna(0)
                    save_doctype("Stock", new_items[STOCK_COLUMNS])
                    st.success("✅ اكتمل الاستيراد.")
                    st.rerun()

    if not stock_df.empty:
        edited_stock = st.data_editor(stock_df, num_rows="dynamic", use_container_width=True)
        if st.button("💾 حفظ التعديلات (Save Stock)", use_container_width=True):
            save_doctype("Stock", edited_stock)
            st.success("تم الحفظ!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MODULE 5: LOGISTICS (HAWARA & DISPATCH)
# ==========================================
elif st.session_state['current_module'] == 'Logistics':
    st.title("🚚 وحدة الشحن واللوجستيات (Logistics)")
    tab1, tab2 = st.tabs(["📑 مشتريات وشحن حوارة (Supplier Orders)", "📦 التوصيل المحلي (Local Dispatch)"])
    
    with tab1:
        st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
        with st.form("hawara_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1: 
                h_id = st.text_input("معرف الطلب (Order ID)")
                h_type = st.selectbox("نوع العملية (Type)", ["طلب قطع غيار", "إرسال للصيانة", "استرجاع بضاعة"])
                linked_sid = st.selectbox("ارتباط بسند (Link to Ticket)", options=["بدون ربط"] + ledger_df['service_id'].tolist() if not ledger_df.empty else ["بدون ربط"])
            with c2: 
                courier = st.selectbox("شركة الشحن (Courier)", ["شركة أرامكس", "نقل قدموس", "ساعي داخلي", "شركة حوارة"])
                h_note = st.text_input("بوليصة الشحن (Delivery Note)")
            with c3:
                h_status = st.selectbox("الحالة (Status)", ["قيد الطلب", "في الطريق", "تم الاستلام"])
                uploaded_doc = st.file_uploader("مرفق الفاتورة (Invoice Image)", type=["png", "jpg", "jpeg"])
                
            if st.form_submit_button("حفظ الطلبية (Submit Order)", use_container_width=True):
                if h_id:
                    file_url = upload_to_cloud(uploaded_doc) if uploaded_doc else ""
                    new_hawara = {
                        "order_id": h_id, "order_type": h_type, "linked_service_id": linked_sid if linked_sid != "بدون ربط" else "",
                        "courier": courier, "delivery_note": h_note, "document_link": file_url, "status": h_status, "date_logged": datetime.now().strftime("%Y-%m-%d")
                    }
                    save_doctype("Hawara", pd.concat([hawara_df, pd.DataFrame([new_hawara])], ignore_index=True))
                    st.success("✅ تم حفظ طلبية حوارة بنجاح!")
                else: st.error("يرجى إدخال معرف الطلب.")
        
        if not hawara_df.empty:
            st.subheader("سجل الطلبيات (Order Log)")
            edited_hawara = st.data_editor(hawara_df, num_rows="dynamic", use_container_width=True, column_config={"document_link": st.column_config.LinkColumn("المرفق", display_text="🔗 عرض")})
            if st.button("حفظ التعديلات (Save Edits)"): save_doctype("Hawara", edited_hawara); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
        with st.form("dispatch_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                disp_id = st.text_input("رقم الإرسالية (Dispatch ID)")
                ready_list = ledger_df[ledger_df['status'].str.contains('جاهز', na=False)] if not ledger_df.empty else pd.DataFrame()
                sel_service = st.selectbox("الجهاز (Ready Tool)", options=ready_list['service_id'].tolist() if not ready_list.empty else [])
            with c2:
                disp_courier = st.selectbox("شركة النقل (Courier)", ["شركة أرامكس", "نقل قدموس", "ساعي داخلي"])
                disp_note = st.text_input("رقم البوليصة (Tracking No)")
            with c3:
                disp_file = st.file_uploader("مرفق البوليصة (Receipt Image)", type=["png", "jpg", "jpeg"])
                
            if st.form_submit_button("حفظ الإرسالية (Submit Dispatch)", use_container_width=True):
                if disp_id and sel_service:
                    file_url = upload_to_cloud(disp_file) if disp_file else ""
                    cust = ledger_df[ledger_df['service_id'] == sel_service].iloc[0]['customer_name'] if not ledger_df.empty else ''
                    new_disp = {
                        "dispatch_id": disp_id, "service_id": sel_service, "customer_name": cust,
                        "courier": disp_courier, "delivery_note": disp_note, "document_link": file_url, "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    save_doctype("Dispatch", pd.concat([dispatch_df, pd.DataFrame([new_disp])], ignore_index=True))
                    st.success("✅ تم تسجيل الإرسالية وحفظ المرفق بنجاح!")
                else: st.error("يرجى إدخال رقم الإرسالية وسند الصيانة.")
                    
        if not dispatch_df.empty:
            st.data_editor(dispatch_df, num_rows="dynamic", use_container_width=True, column_config={"document_link": st.column_config.LinkColumn("الإيصال", display_text="🔗 عرض")})
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MODULE 6: ACCOUNTING & INVOICING
# ==========================================
elif st.session_state['current_module'] == 'Accounting':
    st.title("💰 الإدارة المالية والمحاسبة (Accounting)")
    
    tab1, tab2, tab3 = st.tabs(["🧾 طباعة الفواتير (Print Invoices)", "📊 التقارير ودفتر الأستاذ (General Ledger)", "⚙️ استيراد البيانات (Data Import)"])
    
    with tab1:
        st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
        if not ledger_df.empty:
            inv_opts = ledger_df['service_id'].unique().tolist()
            sel_inv = st.selectbox("اختر رقم السند لتوليد الفاتورة (Select Ticket for Invoice):", options=inv_opts)
            
            if st.button("🖨️ توليد الفاتورة (Generate Invoice)", use_container_width=True):
                inv_data = ledger_df[ledger_df['service_id'] == sel_inv].iloc[0]
                
                invoice_html = f"""
                <div class="invoice-box">
                    <div class="invoice-header">
                        <h2>القصر الذهبي للمعدات الصناعية</h2>
                        <p>Al-Qasr Al-Zahabi | صيانة - بيع - تأجير</p>
                    </div>
                    <table style="width:100%; margin-bottom:20px; text-align:right; direction:rtl;">
                        <tr>
                            <td><b>رقم السند:</b> {inv_data['service_id']}</td>
                            <td><b>التاريخ:</b> {datetime.now().strftime("%Y-%m-%d")}</td>
                        </tr>
                        <tr>
                            <td><b>الزبون:</b> {inv_data['customer_name']}</td>
                            <td><b>الهاتف:</b> {inv_data['phone_number']}</td>
                        </tr>
                    </table>
                    <hr>
                    <table style="width:100%; text-align:right; direction:rtl; border-collapse: collapse; margin-top:20px;">
                        <tr style="background:#f7fafc; border-bottom:1px solid #cbd5e0;">
                            <th style="padding:10px;">البيان (Description)</th>
                            <th style="padding:10px;">المبلغ (Amount)</th>
                        </tr>
                        <tr style="border-bottom:1px solid #edf2f7;">
                            <td style="padding:10px;">صيانة أداة: {inv_data['tool_name']}<br><small>ملاحظات: {inv_data['resolution_notes']}</small></td>
                            <td style="padding:10px;">${float(inv_data['cost_debit']):.2f}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #edf2f7;">
                            <td style="padding:10px;">الدفعة المقدمة (Credit)</td>
                            <td style="padding:10px;">${float(inv_data['payment_credit']):.2f}</td>
                        </tr>
                        <tr style="font-weight:bold; background:#ebf8ff;">
                            <td style="padding:10px;">الرصيد المتبقي (Total Due)</td>
                            <td style="padding:10px;">${float(inv_data['balance']):.2f}</td>
                        </tr>
                    </table>
                    <div style="text-align:center; margin-top:40px; font-size:12px; color:#718096;">
                        شكراً لتعاملكم معنا. (Thank you for your business.)<br>
                        <i>يمكن طباعة هذه الصفحة باستخدام (Ctrl + P)</i>
                    </div>
                </div>
                """
                st.components.v1.html(invoice_html, height=600, scrolling=True)
                st.info("💡 اضغط `Ctrl + P` أو `Cmd + P` في المتصفح لطباعة الفاتورة أو حفظها كـ PDF.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
        if not ledger_df.empty:
            view_type = st.radio("نوع العرض (View Type)", ["دفتر الأستاذ العام (General Ledger)", "حسابات الشركاء والوكلاء (Partner Ledger)"])
            
            if view_type == "دفتر الأستاذ العام (General Ledger)":
                st.dataframe(ledger_df, use_container_width=True)
                st.download_button("📥 تصدير الدفتر (Export Ledger)", data=convert_df_to_excel(ledger_df), file_name="General_Ledger.xlsx")
            else:
                partners_df = ledger_df[ledger_df['service_id'].str.startswith('V', na=False) | ledger_df['document_origin'].str.contains('خ صيانة', na=False)]
                st.dataframe(partners_df[['service_id', 'customer_name', 'tool_name', 'cost_debit', 'balance']], use_container_width=True)
                st.metric("مجموع ذمم الوكلاء", f"${partners_df['balance'].astype(float).sum():.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        if is_admin:
            st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
            st.subheader("📥 استيراد كشوفات الأمين (Legacy Import Tool)")
            uploaded_legacy = st.file_uploader("رفع ملف Excel", type=["xlsx"])
            if uploaded_legacy and st.button("تنفيذ الاستيراد (Run Import)"):
                with st.spinner("Processing documents..."):
                    raw_excel = pd.read_excel(uploaded_legacy, header=None)
                    records = {}
                    curr_sid = None
                    
                    for r_idx, row in raw_excel.iterrows():
                        row_vals = [str(x).strip() for x in row.dropna().tolist()]
                        row_text = " ".join(row_vals)
                        
                        row_date = ""
                        for v in row_vals:
                            date_match = re.search(r'\b(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})\b', v)
                            if date_match:
                                try:
                                    date_str = date_match.group(1).replace('/', '-')
                                    parsed = pd.to_datetime(date_str, format='%d-%m-%Y', errors='coerce')
                                    if pd.isna(parsed):
                                        parsed = pd.to_datetime(date_str, format='%d-%m-%y', errors='coerce')
                                    if pd.isna(parsed):
                                        parsed = pd.to_datetime(date_str, dayfirst=True, errors='coerce')
                                        
                                    if pd.notna(parsed):
                                        row_date = parsed.strftime("%Y-%m-%d")
                                        break
                                except:
                                    pass
                        
                        header_cell = next((val for val in row_vals if re.search(r'\b[SDV]\d+\b', val, re.IGNORECASE) and '-' in val), "")
                        
                        if header_cell:
                            curr_sid_match = re.search(r'\b([SDV]\d+)\b', header_cell, re.IGNORECASE)
                            if curr_sid_match:
                                curr_sid = curr_sid_match.group(1).upper()
                                clean_header = re.sub(r'^(الزبون:|الحساب:|الزبون|الحساب)\s*', '', header_cell).strip()
                                parts = [p.strip() for p in re.split(r'[-–]', clean_header) if p.strip()]
                                
                                c_name, phone, t_name, issue, w_status = "غير محدد", "", "غير محدد", "", "خارج الكفالة"
                                
                                if len(parts) > 1:
                                    for p in parts[1:]:
                                        digits = re.sub(r'\D', '', p)
                                        if any(kw in p for kw in ['كفالة', 'ضمان', 'مجاني']): w_status = "ضمن كفالة"
                                        elif 8 <= len(digits) <= 15 and len(p) < 20: phone = digits
                                        elif any(kw in p for kw in ['فولت', 'فولط', 'واط', 'امبير', 'مثقب', 'صاروخ', 'مضخة', 'جلخ', 'كسارة', 'دباسة']): t_name = p
                                        elif any(kw in p for kw in ['عطل', 'لايعمل', 'تبديل', 'صيانة', 'ماس', 'صوت', 'فواشة']): issue = p
                                        elif len(p) > 2:
                                            if c_name == "غير محدد": c_name = p
                                            elif t_name == "غير محدد": t_name = p
                                            else: issue = p
                                else:
                                    t_name = clean_header.replace(curr_sid, '').strip()
                                    if not t_name: t_name = "غير محدد"

                                if curr_sid not in records:
                                    records[curr_sid] = {
                                        "service_id": curr_sid, "tool_name": t_name, "customer_name": c_name, "phone_number": phone,
                                        "warranty_status": w_status, "document_origin": "", "reported_issue": issue,
                                        "technician": "Admin Import", "status": "قيد الانتظار", "cost_debit": 0.0,
                                        "payment_credit": 0.0, "balance": 0.0, "spare_parts": "لا حاجة / متوفرة",
                                        "resolution_notes": "", "remarks": "", 
                                        "date_logged": row_date if row_date else datetime.now().strftime("%Y-%m-%d"), "date_resolved": "",
                                        "accessories": "", "loaner_item": "", "priority": "عادي", "tool_photo_link": ""
                                    }

                        if curr_sid and curr_sid in records:
                            rec = records[curr_sid]
                            c_origin = rec["document_origin"]
                            c_rank = get_status_rank(c_origin)
                            nums = [float(v) for v in row_vals if str(v).replace('.','',1).isdigit()]
                            
                            if "قبض" in row_text:
                                if c_rank < 4: 
                                    rec["document_origin"] = "قبض د: (مدفوع ومسلم)"
                                    if row_date: rec["date_resolved"] = row_date
                                if nums: rec["payment_credit"] = max(nums)
                            elif "خ صيانة" in row_text:
                                if c_rank < 3: 
                                    rec["document_origin"] = "خ صيانة: (تحميل على الوكيل)"
                                    if row_date: rec["date_resolved"] = row_date
                            elif "مبيع خ ص" in row_text:
                                if c_rank < 2: rec["document_origin"] = "مبيع خ ص: (جاهز ومفوتر)"
                                if nums: rec["cost_debit"] = max(nums)
                            elif "اد خ ص" in row_text and c_rank < 1:
                                rec["document_origin"] = "اد خ ص: (استلام للصيانة)"
                                if row_date: rec["date_logged"] = row_date

                    imported_list = []
                    for sid, rec in records.items():
                        rec["balance"] = float(rec["cost_debit"]) - float(rec["payment_credit"])
                        rec["status"] = map_document_to_status(rec["document_origin"], rec["cost_debit"])
                        if "تم التسليم" in rec["status"] and not rec["date_resolved"]:
                            rec["date_resolved"] = datetime.now().strftime("%Y-%m-%d")
                        imported_list.append(rec)

                    if imported_list:
                        save_doctype("Ledger", pd.concat([ledger_df, pd.DataFrame(imported_list)], ignore_index=True))
                        st.success(f"✅ تم استيراد {len(imported_list)} سجل بنجاح.")
                        st.rerun()
                    else:
                        st.warning("⚠️ لم يتم العثور على أي قيود صالحة تحتوي على أرقام بطاقات صيانة في الملف المرفوع.")
            st.markdown("</div>", unsafe_allow_html=True)
