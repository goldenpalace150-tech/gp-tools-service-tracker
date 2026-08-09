import streamlit as st
import pandas as pd
from datetime import datetime
import re
from streamlit_gsheets import GSheetsConnection

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="مركز الصيانة - القصر الذهبي", layout="wide", page_icon="🛠️")

st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; direction: rtl; text-align: right; }
        h1, h2, h3, h4, p, span, label, div { text-align: right; }
        table { width: 100% !important; background-color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ نظام إدارة الصيانة السريع (مزامنة سحابية مباشرة)")

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

@st.cache_data(ttl=0)
def load_data():
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

def save_data(df):
    conn.update(worksheet="Ledger", data=df)

# Helpers
def get_branch(s_id):
    if not s_id: return "أخرى"
    char = str(s_id).strip().upper()[0]
    if char == 'S': return "صيدا (Saida)"
    if char == 'D': return "درعا (Daraa)"
    if char == 'V': return "شريك (Partner)"
    return "أخرى"

def map_status(doc):
    doc = str(doc)
    if "اد خ ص" in doc: return "قيد المعالجة"
    if "مبيع خ ص" in doc: return "جاهز للتسليم"
    if "قبض د" in doc: return "تم التسليم"
    if "خ صيانة" in doc: return "حساب وكيل"
    return "قيد الانتظار"

live_df = load_data()

# ==========================================
# QUICK METRICS BAR
# ==========================================
if not live_df.empty:
    active_count = len(live_df[~live_df['status'].str.contains('تم التسليم', na=False)])
    ready_count = len(live_df[live_df['status'].str.contains('جاهز', na=False)])
    try: total_bal = live_df['balance'].astype(float).sum()
    except: total_bal = 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("📦 الأجهزة النشطة", active_count)
    m2.metric("✅ جاهزة للاستلام", ready_count)
    m3.metric("💰 إجمالي الأرصدة ($)", f"{total_bal:.2f}")
    st.divider()

# ==========================================
# SIMPLE FORM: QUICK INTAKE
# ==========================================
with st.expander("➕ اضغط هنا لإضافة جهاز صيانة جديد"):
    with st.form("quick_intake"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: s_id = st.text_input("رقم السند (S/D/V)")
        with c2: c_name = st.text_input("اسم الزبون")
        with c3: phone = st.text_input("رقم الهاتف")
        with c4: t_name = st.text_input("اسم الأداة / الموديل")
        
        c5, c6 = st.columns(2)
        with c5: doc_org = st.selectbox("أصل السند", ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "خ صيانة: (تحميل على الوكيل)"])
        with c6: issue = st.text_input("العطل أو ملاحظات الاستلام")

        if st.form_submit_button("حفظ وإضافة فورية", use_container_width=True):
            if s_id and c_name and t_name:
                if not live_df.empty and s_id in live_df['service_id'].values:
                    st.error("رقم السند موجود مسبقاً.")
                else:
                    new_row = {
                        "service_id": s_id, "tool_name": t_name, "customer_name": c_name, "phone_number": phone,
                        "warranty_status": "خارج الكفالة", "document_origin": doc_org, "reported_issue": issue,
                        "technician": "Admin", "status": map_status(doc_org), "cost_debit": 0.0, "payment_credit": 0.0,
                        "balance": 0.0, "resolution_notes": "", "date_logged": datetime.now().strftime("%Y-%m-%d"), "date_resolved": ""
                    }
                    updated_df = pd.concat([live_df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(updated_df)
                    st.success("✅ تم الحفظ بنجاح!")
                    st.rerun()
            else:
                st.warning("يرجى تعبئة الحقول الأساسية.")

st.subheader("📋 سجل كشف الحساب والأجهزة المباشر")
st.info("💡 يمكنك تعديل الملاحظات، التكاليف، أو أصل السند مباشرة من الجدول أدناه وسيتم الحفظ سحابياً فورياً.")

if not live_df.empty:
    # Prepare view
    display_df = live_df.copy()
    display_df.insert(1, 'الفرع', display_df['service_id'].apply(get_branch))
    
    # Interactive Table Editor for smooth updates
    edited_df = st.data_editor(
        display_df,
        num_rows="dynamic",
        use_container_width=True,
        key="ledger_editor",
        column_config={
            "service_id": "رقم السند",
            "Branch": st.column_config.TextColumn("الفرع", disabled=True),
            "tool_name": "الأداة",
            "customer_name": "الزبون",
            "phone_number": "الهاتف",
            "document_origin": st.column_config.SelectboxColumn("أصل السند", options=["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"]),
            "cost_debit": "مدين (التكلفة)",
            "payment_credit": "دائن (الدفعة)",
            "balance": st.column_config.NumberColumn("الرصيد", disabled=True),
            "resolution_notes": "البيان / ملاحظات الصيانة",
            "status": st.column_config.TextColumn("الحالة", disabled=True)
        }
    )
    
    if st.button("💾 حفظ التعديلات على الجدول", type="primary", use_container_width=True):
        # Recalculate balances and status automatically before saving back to Google Sheets
        try:
            edited_df['cost_debit'] = pd.to_numeric(edited_df['cost_debit'], errors='coerce').fillna(0.0)
            edited_df['payment_credit'] = pd.to_numeric(edited_df['payment_credit'], errors='coerce').fillna(0.0)
            edited_df['balance'] = edited_df['cost_debit'] - edited_df['payment_credit']
            edited_df['status'] = edited_df['document_origin'].apply(map_status)
            
            # Drop temporary display column before saving
            clean_save_df = edited_df.drop(columns=['الفرع'])
            save_data(clean_save_df)
            st.success("✅ تم حفظ وتحديث جميع التعديلات سحابياً بنجاح!")
            st.rerun()
        except Exception as e:
            st.error(f"حدث خطأ أثناء حفظ البيانات: {e}")
else:
    st.info("لا توجد بيانات مسجلة.")
