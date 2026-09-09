import streamlit as st
import pandas as pd
from datetime import datetime
import re
import io
import requests
import base64
import urllib.parse
import os
import hashlib
from contextlib import contextmanager
from streamlit_gsheets import GSheetsConnection

# ==========================================
# SYSTEM CONFIGURATION & API
# ==========================================
def get_runtime_secret(name):
    """Load deployment secrets without committing them to the public repository."""
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return str(os.environ.get(name, "")).strip()


IMGBB_API_KEY = get_runtime_secret("IMGBB_API_KEY")

st.set_page_config(page_title="Al-Qasr Al-Zahabi ERP", layout="wide", page_icon="🏢")

query_params = st.query_params
is_tv_mode = "tv" in query_params or query_params.get("mode") == "tv"

if "ui_language" not in st.session_state:
    requested_language = str(query_params.get("lang", "ar") or "ar").lower()
    st.session_state["ui_language"] = requested_language if requested_language in {"ar", "en"} else "ar"


UI_TEXT = {
    "ar": {
        "loading_data": "جارٍ تحميل البيانات مباشرة من المصدر...",
        "saving_data": "جارٍ حفظ البيانات...",
        "language": "اللغة",
        "workspace_title": "مساحة العمل الموحدة",
        "sidebar_title": "مساحة عمل ERPNext",
        "user": "المستخدم",
        "role": "الدور",
        "core_modules": "العمليات الأساسية",
        "workspace": "🏠 مساحة العمل",
        "tv": "📺 شاشة الورشة",
        "support": "🛠️ الدعم والصيانة",
        "stock": "📦 المخزون",
        "logistics": "🚚 اللوجستيات",
        "accounting": "💰 المحاسبة",
        "logout": "🚪 تسجيل الخروج",
        "stock_title": "📦 وحدة المستودعات والمخزون",
        "stock_reorder": "⚠️ يوجد {count} أصناف تتطلب إعادة طلب.",
        "stock_export": "📥 تصدير السجل",
        "stock_import_expander": "📤 استيراد تقرير المخزون / الأسعار",
        "stock_upload": "رفع تقرير Excel أو CSV",
        "stock_import": "استيراد",
        "stock_imported": "✅ تم استيراد {count} صنف بنجاح.",
        "stock_invalid": "❌ لم أتمكن من تحديد عمود كود المادة واسم المادة في التقرير.",
        "stock_import_error": "❌ فشل استيراد تقرير المخزون",
        "stock_save": "💾 حفظ التعديلات",
        "stock_saved": "✅ تم حفظ المخزون.",
        "open_repairs": "🛠️ صيانة مفتوحة",
        "ready_tools": "✅ أجهزة جاهزة للتسليم",
        "sales_total": "💰 إجمالي المبيعات",
    },
    "en": {
        "loading_data": "Loading live data directly from the source...",
        "saving_data": "Saving data...",
        "language": "Language",
        "workspace_title": "Unified Workspace",
        "sidebar_title": "ERPNext Workspace",
        "user": "User",
        "role": "Role",
        "core_modules": "CORE MODULES",
        "workspace": "🏠 Workspace",
        "tv": "📺 TV Display",
        "support": "🛠️ Support & Maintenance",
        "stock": "📦 Stock",
        "logistics": "🚚 Logistics",
        "accounting": "💰 Accounting",
        "logout": "🚪 Logout",
        "stock_title": "📦 Stock & Inventory",
        "stock_reorder": "⚠️ {count} items require reordering.",
        "stock_export": "📥 Export Stock",
        "stock_import_expander": "📤 Import Stock / Price Report",
        "stock_upload": "Upload Excel or CSV report",
        "stock_import": "Import",
        "stock_imported": "✅ Imported {count} stock items successfully.",
        "stock_invalid": "❌ I could not identify the item-code and item-name columns in this report.",
        "stock_import_error": "❌ Stock report import failed",
        "stock_save": "💾 Save Stock Changes",
        "stock_saved": "✅ Stock saved.",
        "open_repairs": "🛠️ Open Repairs",
        "ready_tools": "✅ Ready for Collection",
        "sales_total": "💰 Total Sales",
    },
}


def tr(key, **kwargs):
    lang = st.session_state.get("ui_language", "ar")
    value = UI_TEXT.get(lang, UI_TEXT["ar"]).get(key, key)
    return value.format(**kwargs) if kwargs else value


@contextmanager
def golden_loading(message=None):
    """Consistent Golden Palace waiting indicator without stacking nested spinners."""
    depth = int(st.session_state.get("_golden_loading_depth", 0) or 0)
    st.session_state["_golden_loading_depth"] = depth + 1
    try:
        if depth:
            yield
        else:
            with st.spinner(f"🏢 Golden Palace · {message or tr('loading_data')}"):
                yield
    finally:
        st.session_state["_golden_loading_depth"] = depth


if is_tv_mode:
    st.markdown("""
        <style>
            [data-testid='stSidebar'] {display: none !important;}
            header {visibility: hidden !important;}
            .stApp { background-color: #f8f9fa; direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            h1, h2, h3, h4, p, span, label, div { text-align: right; }
        </style>
    """, unsafe_allow_html=True)
else:
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

ui_is_ar = st.session_state.get("ui_language", "ar") == "ar"
ui_direction = "rtl" if ui_is_ar else "ltr"
ui_align = "right" if ui_is_ar else "left"
st.markdown(
    f"""
    <style>
        .stApp {{ direction: {ui_direction} !important; text-align: {ui_align} !important; }}
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp span,
        .stApp label, .stApp div {{ text-align: {ui_align}; }}
        div[data-testid="stSpinner"] {{
            position: fixed !important;
            left: 50% !important;
            top: 50% !important;
            transform: translate(-50%, -50%) !important;
            z-index: 999999 !important;
            min-width: 300px;
            max-width: min(520px, calc(100vw - 32px));
            padding: 22px 26px !important;
            border: 1px solid #c89b2c;
            border-radius: 18px;
            background: #06182a;
            color: #ffffff;
            box-shadow: 0 18px 60px rgba(0,0,0,.35);
        }}
        div[data-testid="stSpinner"]::before {{
            content: "GP";
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            margin-inline-end: 12px;
            border-radius: 50%;
            border: 2px solid #e7bd58;
            color: #f4bd2d;
            font-weight: 900;
            letter-spacing: .04em;
            background: #0b2238;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# GP_APP_UI_REFRESH_2026_09_08
if not is_tv_mode:
    st.markdown("""
    <style>
      :root{--gp-navy:#071a2d;--gp-navy2:#0d2c49;--gp-gold:#d5a62e}
      .stApp{background:radial-gradient(circle at 8% 0%,#edf4ff 0,#f6f8fb 34%,#eef2f7 100%)!important}
      .block-container{max-width:1500px;padding-top:1.35rem;padding-bottom:3rem}
      [data-testid="stSidebar"]{background:linear-gradient(180deg,var(--gp-navy),var(--gp-navy2))!important;border-inline-end:1px solid rgba(213,166,46,.35)}
      [data-testid="stSidebar"] *{color:#f8fafc}[data-testid="stSidebar"] button{min-height:44px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.07);color:#fff;font-weight:750}
      .erp-card{border:1px solid rgba(148,163,184,.28)!important;border-radius:18px!important;box-shadow:0 10px 30px rgba(15,23,42,.07)!important;padding:22px!important;background:rgba(255,255,255,.96)!important}
      div[data-testid="stMetric"]{background:#fff;border:1px solid rgba(148,163,184,.28);border-radius:16px;padding:16px;box-shadow:0 7px 22px rgba(15,23,42,.05)}
      .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{min-height:44px;border-radius:12px;font-weight:750}
      input,textarea,[data-baseweb="select"]>div{border-radius:12px!important}
      .gp-app-hero{background:linear-gradient(120deg,var(--gp-navy),var(--gp-navy2));color:#fff;border:1px solid rgba(213,166,46,.55);border-radius:20px;padding:22px 24px;margin:.2rem 0 1.1rem;box-shadow:0 14px 38px rgba(7,26,45,.18)}
      .gp-app-hero h1{color:#fff!important;margin:0 0 6px!important;font-size:clamp(28px,3vw,42px)}.gp-app-hero p{color:#dbe7f3!important;margin:0}.gp-app-chip{display:inline-flex;margin-top:12px;padding:6px 10px;border-radius:999px;background:rgba(213,166,46,.18);border:1px solid rgba(213,166,46,.55);color:#fff;font-size:12px;font-weight:800}
      button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid #f0be3f!important;outline-offset:2px!important}
    </style>
    """,unsafe_allow_html=True)


# GP_BACKEND_UI_V2
# Modern staff-facing shell. This layer intentionally changes presentation only;
# service workflow, accounting rules, Google Sheets I/O, and state transitions stay untouched.
if not is_tv_mode:
    st.markdown("""
    <style>
      :root{
        --gp-bg:#f4f7fb;--gp-surface:#ffffff;--gp-surface-2:#f8fafc;
        --gp-navy:#06182a;--gp-navy-2:#0b2945;--gp-navy-3:#123957;
        --gp-gold:#d6a62f;--gp-gold-2:#f0c85b;--gp-text:#152033;
        --gp-muted:#6b7a90;--gp-line:#dfe6ef;--gp-good:#16794d;
        --gp-warn:#b86a00;--gp-danger:#b42318;--gp-radius:18px;
        --gp-shadow:0 12px 34px rgba(15,23,42,.08);
      }

      html,body,[class*="css"]{font-family:"Segoe UI",Tahoma,Arial,sans-serif}
      [data-testid="stAppViewContainer"]{background:
        radial-gradient(circle at 85% -10%,rgba(214,166,47,.12),transparent 28%),
        linear-gradient(180deg,#f8fafc 0%,var(--gp-bg) 100%)!important}
      [data-testid="stHeader"]{background:rgba(244,247,251,.82)!important;backdrop-filter:blur(12px);border-bottom:1px solid rgba(223,230,239,.75)}
      [data-testid="stToolbar"]{right:1rem}
      footer{visibility:hidden}
      .block-container{max-width:1540px!important;padding-top:1.25rem!important;padding-bottom:4rem!important}

      /* Sidebar */
      [data-testid="stSidebar"]{background:linear-gradient(180deg,var(--gp-navy) 0%,var(--gp-navy-2) 66%,#0a2239 100%)!important;border-inline-end:1px solid rgba(214,166,47,.32)!important}
      [data-testid="stSidebar"]>div:first-child{padding-top:.7rem}
      [data-testid="stSidebar"] .block-container{padding-top:.75rem!important}
      [data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.12)!important;margin:.8rem 0!important}
      [data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#9fb2c7!important;font-weight:800;letter-spacing:.09em;text-transform:uppercase;font-size:.69rem}
      [data-testid="stSidebar"] label,[data-testid="stSidebar"] p,[data-testid="stSidebar"] span{color:#eef4fa}
      [data-testid="stSidebar"] [data-baseweb="select"]>div{background:rgba(255,255,255,.08)!important;border:1px solid rgba(255,255,255,.15)!important;color:#fff!important}
      [data-testid="stSidebar"] .stButton>button{width:100%;justify-content:flex-start;min-height:46px;border-radius:13px!important;border:1px solid transparent!important;box-shadow:none!important;padding:.7rem .9rem!important;font-weight:750!important;transition:.16s ease}
      [data-testid="stSidebar"] .stButton>button[kind="secondary"]{background:transparent!important;color:#e8f0f7!important}
      [data-testid="stSidebar"] .stButton>button[kind="secondary"]:hover{background:rgba(255,255,255,.08)!important;border-color:rgba(255,255,255,.12)!important;transform:translateX(-2px)}
      [data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--gp-gold),var(--gp-gold-2))!important;color:#162334!important;border-color:#f3d77f!important;box-shadow:0 7px 18px rgba(214,166,47,.18)!important}
      .gp-side-brand{padding:16px 15px 13px;border:1px solid rgba(214,166,47,.38);background:linear-gradient(135deg,rgba(214,166,47,.13),rgba(255,255,255,.045));border-radius:18px;margin:3px 0 14px}
      .gp-side-brand-top{display:flex;align-items:center;gap:11px}.gp-side-mark{width:42px;height:42px;display:flex;align-items:center;justify-content:center;border-radius:13px;background:linear-gradient(145deg,var(--gp-gold-2),var(--gp-gold));color:#10233a;font-weight:950;letter-spacing:.03em;box-shadow:0 7px 18px rgba(214,166,47,.2)}
      .gp-side-brand strong{display:block;color:#fff;font-size:1.02rem}.gp-side-brand small{display:block;color:#aabed0;margin-top:2px;font-size:.75rem}
      .gp-user-card{display:grid;grid-template-columns:36px 1fr;align-items:center;gap:10px;padding:11px 12px;border-radius:14px;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);margin:8px 0 15px}
      .gp-user-avatar{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#153a59;color:#f0c85b;font-weight:900}.gp-user-card strong{color:#fff!important;font-size:.88rem}.gp-user-card small{color:#9eb3c7!important;font-size:.7rem}

      /* Hero / module header */
      .gp-module-hero{position:relative;overflow:hidden;display:flex;justify-content:space-between;align-items:flex-end;gap:20px;background:linear-gradient(118deg,var(--gp-navy) 0%,var(--gp-navy-2) 72%,#123a59 100%);border:1px solid rgba(214,166,47,.46);border-radius:24px;padding:25px 28px;margin:2px 0 20px;box-shadow:0 18px 48px rgba(7,26,45,.16)}
      .gp-module-hero:after{content:"";position:absolute;width:230px;height:230px;border-radius:50%;right:-75px;top:-115px;border:42px solid rgba(214,166,47,.08)}
      .gp-module-eyebrow{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:#e8c66e;font-weight:900;margin-bottom:8px}
      .gp-module-hero h1{position:relative;z-index:1;margin:0!important;color:#fff!important;font-size:clamp(1.75rem,2.7vw,2.65rem)!important;line-height:1.1}.gp-module-hero p{position:relative;z-index:1;color:#c7d6e4!important;margin:8px 0 0!important;max-width:830px;line-height:1.55}
      .gp-module-user{position:relative;z-index:2;white-space:nowrap;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.13);border-radius:14px;padding:10px 13px;color:#dce7f2;font-size:.76rem}.gp-module-user strong{display:block;color:#fff;font-size:.92rem;margin-top:2px}

      /* Core surfaces */
      .erp-card{background:rgba(255,255,255,.97)!important;border:1px solid var(--gp-line)!important;border-radius:var(--gp-radius)!important;padding:22px!important;margin-bottom:18px!important;box-shadow:var(--gp-shadow)!important}
      .locked-card{background:linear-gradient(180deg,#fff8f7,#fff)!important;border:1px solid #f5c8c3!important;border-radius:18px!important;padding:22px!important;box-shadow:0 10px 28px rgba(180,35,24,.07)!important}
      [data-testid="stForm"]{background:#fff;border:1px solid var(--gp-line);border-radius:18px;padding:18px 18px 8px;box-shadow:0 9px 26px rgba(15,23,42,.055)}
      [data-testid="stExpander"]{background:#fff;border:1px solid var(--gp-line)!important;border-radius:15px!important;overflow:hidden;box-shadow:0 5px 18px rgba(15,23,42,.04)}
      [data-testid="stExpander"] details summary{font-weight:800}

      /* Metrics */
      div[data-testid="stMetric"]{position:relative;overflow:hidden;background:#fff!important;border:1px solid var(--gp-line)!important;border-radius:18px!important;padding:18px 18px 16px!important;box-shadow:0 9px 27px rgba(15,23,42,.06)!important}
      div[data-testid="stMetric"]:before{content:"";position:absolute;inset:0 0 auto 0;height:4px;background:linear-gradient(90deg,var(--gp-gold),#f1d47c)}
      div[data-testid="stMetricLabel"]{color:var(--gp-muted)!important;font-weight:800!important}div[data-testid="stMetricValue"]{color:var(--gp-navy)!important;font-weight:900!important}

      /* Inputs */
      .stTextInput input,.stNumberInput input,.stTextArea textarea,[data-baseweb="select"]>div,[data-baseweb="base-input"]{border-radius:12px!important;border-color:#cfd9e5!important;background:#fff!important}
      .stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus,[data-baseweb="select"]>div:focus-within{border-color:var(--gp-gold)!important;box-shadow:0 0 0 3px rgba(214,166,47,.13)!important}
      [data-testid="stFileUploader"]{border-radius:15px;background:#fafbfd}
      label{font-weight:720!important;color:#344259!important}

      /* Buttons */
      .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{min-height:44px;border-radius:12px!important;font-weight:800!important;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease}
      .stButton>button:hover,.stDownloadButton>button:hover,.stFormSubmitButton>button:hover{transform:translateY(-1px)}
      .stFormSubmitButton>button,.stDownloadButton>button{border-color:#c99b29!important}
      .stFormSubmitButton>button[kind="primary"],.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--gp-navy-2),var(--gp-navy-3))!important;border-color:#234e70!important;color:#fff!important}

      /* Tabs */
      .stTabs [data-baseweb="tab-list"]{gap:7px!important;border:0!important;background:#eaf0f6;padding:6px;border-radius:15px;margin-bottom:14px}
      .stTabs [data-baseweb="tab"]{height:auto!important;min-height:42px;border-radius:10px!important;padding:9px 15px!important;color:#55657a!important;font-weight:800!important;background:transparent!important;border:0!important}
      .stTabs [aria-selected="true"]{background:#fff!important;color:var(--gp-navy)!important;box-shadow:0 3px 10px rgba(15,23,42,.08)!important;border:1px solid #dbe3ec!important}
      .stTabs [data-baseweb="tab-highlight"]{display:none!important}

      /* Data */
      [data-testid="stDataFrame"],[data-testid="stDataEditor"]{border:1px solid var(--gp-line);border-radius:15px;overflow:hidden;box-shadow:0 5px 18px rgba(15,23,42,.04)}
      [data-testid="stTable"]{border-radius:14px;overflow:hidden}
      hr{border-color:#e3e9f0!important}

      /* Feedback boxes */
      [data-testid="stAlert"]{border-radius:14px!important;border-width:1px!important;box-shadow:0 5px 16px rgba(15,23,42,.035)}

      /* Login */
      .gp-login-brand{text-align:center;margin:7vh auto 24px;max-width:760px}.gp-login-logo{width:64px;height:64px;display:inline-flex;align-items:center;justify-content:center;border-radius:20px;background:linear-gradient(145deg,var(--gp-gold-2),var(--gp-gold));color:#0d2238;font-size:1.3rem;font-weight:950;box-shadow:0 12px 28px rgba(214,166,47,.24);margin-bottom:13px}.gp-login-brand h1{margin:0!important;color:var(--gp-navy)!important;font-size:clamp(2rem,4vw,3rem)!important}.gp-login-brand p{color:var(--gp-muted)!important;margin:7px 0 0!important}.gp-login-card-title{text-align:center;margin:2px 0 14px}.gp-login-card-title strong{display:block;color:var(--gp-navy);font-size:1.12rem}.gp-login-card-title small{color:var(--gp-muted)}

      /* Workspace legacy cards */
      .gp-app-hero{display:none!important}
      .gp-section-label{font-size:.76rem;font-weight:900;letter-spacing:.09em;text-transform:uppercase;color:#7a8798;margin:4px 0 10px}

      @media(max-width:900px){
        .block-container{padding-inline:1rem!important}.gp-module-hero{padding:20px;align-items:flex-start;flex-direction:column}.gp-module-user{white-space:normal}.stTabs [data-baseweb="tab"]{padding:8px 10px!important;font-size:.8rem}
      }
      @media(max-width:600px){
        .block-container{padding-top:.8rem!important}.gp-module-hero{border-radius:18px;padding:18px}.gp-module-hero h1{font-size:1.7rem!important}div[data-testid="stMetric"]{padding:14px!important}
      }
    </style>
    """, unsafe_allow_html=True)


def gp_ui_copy(ar_text, en_text):
    return ar_text if st.session_state.get('ui_language', 'ar') == 'ar' else en_text


GP_MODULE_META = {
    'Workspace': {
        'icon': '🏠',
        'ar_title': 'مساحة العمل الموحدة', 'en_title': 'Unified Workspace',
        'ar_desc': 'نظرة تشغيلية سريعة على الصيانة والاستلام والمبيعات، مع وصول مباشر لأهم وحدات النظام.',
        'en_desc': 'A fast operational overview of repairs, collections, and sales with direct access to the core modules.',
    },
    'Support': {
        'icon': '🛠️',
        'ar_title': 'الدعم والصيانة', 'en_title': 'Support & Maintenance',
        'ar_desc': 'استقبال الأجهزة، تحديث الحالات، متابعة التأخير وإغلاق دورة الصيانة من مكان واحد.',
        'en_desc': 'Intake, case updates, delay tracking, and repair-cycle closure in one focused workspace.',
    },
    'Stock': {
        'icon': '📦',
        'ar_title': 'المخزون والمستودعات', 'en_title': 'Stock & Inventory',
        'ar_desc': 'متابعة الكميات والأسعار والتنبيهات والاستيراد مع واجهة أبسط وأوضح.',
        'en_desc': 'Track quantities, prices, reorder alerts, imports, and edits in a cleaner inventory workspace.',
    },
    'Logistics': {
        'icon': '🚚',
        'ar_title': 'الشحن واللوجستيات', 'en_title': 'Logistics & Dispatch',
        'ar_desc': 'طلبات الموردين والشحنات والتوصيل المحلي وربطها بسندات الصيانة.',
        'en_desc': 'Supplier orders, shipments, local dispatch, and repair-ticket linkage.',
    },
    'Accounting': {
        'icon': '💰',
        'ar_title': 'المالية والمحاسبة', 'en_title': 'Accounting & Finance',
        'ar_desc': 'الفواتير ودفتر الأستاذ وذمم الشركاء واستيراد كشوفات الأمين ضمن واجهة مالية موحدة.',
        'en_desc': 'Invoices, general ledger, partner balances, and Ameen imports in one finance workspace.',
    },
}


def gp_render_module_header(module):
    meta = GP_MODULE_META.get(module, GP_MODULE_META['Workspace'])
    is_ar = st.session_state.get('ui_language', 'ar') == 'ar'
    title = meta['ar_title'] if is_ar else meta['en_title']
    desc = meta['ar_desc'] if is_ar else meta['en_desc']
    current_user_label = st.session_state.get('logged_in_user') or '—'
    user_label = 'المستخدم الحالي' if is_ar else 'Current user'
    st.markdown(
        f"""
        <section class="gp-module-hero">
          <div>
            <div class="gp-module-eyebrow">GOLDEN PALACE · OPERATIONS ERP</div>
            <h1>{meta['icon']} {title}</h1>
            <p>{desc}</p>
          </div>
          <div class="gp-module-user">{user_label}<strong>{current_user_label}</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def gp_nav_button(module, label, key):
    active = st.session_state.get('current_module') == module
    if st.button(label, key=key, use_container_width=True, type='primary' if active else 'secondary'):
        if not active:
            st.session_state['current_module'] = module
            st.rerun()



# GP_BACKEND_UI_V3
# Presentation-only refinement: stronger navy identity, aligned tabs and equal quick actions.
if not is_tv_mode:
    st.markdown("""
    <style>
      :root{
        --gp-v3-navy:#06182a;
        --gp-v3-navy-2:#0b2945;
        --gp-v3-navy-3:#123957;
        --gp-v3-gold:#d6a62f;
        --gp-v3-gold-2:#f0c85b;
      }

      /* Strong navy shell across the staff backend. White working surfaces stay readable. */
      [data-testid="stAppViewContainer"]{
        background:
          radial-gradient(circle at 88% -5%,rgba(240,200,91,.15),transparent 28%),
          linear-gradient(145deg,#071a2d 0%,#0b2945 50%,#102f4b 100%)!important;
      }
      [data-testid="stHeader"]{
        background:rgba(6,24,42,.95)!important;
        border-bottom:1px solid rgba(214,166,47,.30)!important;
        backdrop-filter:blur(12px);
      }
      [data-testid="stDecoration"]{
        background:linear-gradient(90deg,var(--gp-v3-gold),var(--gp-v3-gold-2))!important;
      }
      .block-container{background:transparent!important}
      .gp-section-label{color:#dce7f2!important;letter-spacing:.11em!important}

      /* Workspace KPI cards become true navy cards instead of white tiles. */
      .gp-kpi-card{
        position:relative;
        overflow:hidden;
        min-height:132px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        background:linear-gradient(135deg,var(--gp-v3-navy) 0%,var(--gp-v3-navy-2) 72%,var(--gp-v3-navy-3) 100%)!important;
        border:1px solid rgba(214,166,47,.48)!important;
        box-shadow:0 16px 34px rgba(0,0,0,.24)!important;
      }
      .gp-kpi-card:before{
        content:"";
        position:absolute;
        inset:0 0 auto 0;
        height:4px;
        background:linear-gradient(90deg,var(--gp-v3-gold),var(--gp-v3-gold-2));
      }
      .gp-kpi-card:after{
        content:"";
        position:absolute;
        width:120px;
        height:120px;
        border-radius:50%;
        inset-inline-end:-55px;
        top:-58px;
        border:22px solid rgba(214,166,47,.07);
      }
      .gp-kpi-card h3{
        color:#dce7f2!important;
        font-size:.95rem!important;
        margin:0 0 8px!important;
        font-weight:800!important;
      }
      .gp-kpi-card h1{
        color:#fff!important;
        font-size:2.15rem!important;
        margin:0!important;
        font-weight:950!important;
        letter-spacing:-.02em;
      }

      /* Native Streamlit metrics use the same navy/gold system. */
      div[data-testid="stMetric"]{
        background:linear-gradient(135deg,var(--gp-v3-navy),var(--gp-v3-navy-2))!important;
        border:1px solid rgba(214,166,47,.42)!important;
        box-shadow:0 12px 28px rgba(0,0,0,.18)!important;
      }
      div[data-testid="stMetric"]:before{
        background:linear-gradient(90deg,var(--gp-v3-gold),var(--gp-v3-gold-2))!important;
      }
      div[data-testid="stMetricLabel"],
      div[data-testid="stMetricLabel"] p{color:#c9d8e6!important}
      div[data-testid="stMetricValue"],
      div[data-testid="stMetricValue"] *{color:#fff!important}
      div[data-testid="stMetricDelta"]{color:#e8eef5!important}

      /* Equal-width, equal-height tab strip. */
      .stTabs [data-baseweb="tab-list"]{
        display:grid!important;
        grid-template-columns:repeat(auto-fit,minmax(180px,1fr))!important;
        align-items:stretch!important;
        gap:8px!important;
        width:100%!important;
        background:linear-gradient(135deg,var(--gp-v3-navy),var(--gp-v3-navy-2))!important;
        border:1px solid rgba(214,166,47,.36)!important;
        border-radius:16px!important;
        padding:7px!important;
        overflow:visible!important;
      }
      .stTabs [data-baseweb="tab"]{
        width:100%!important;
        min-width:0!important;
        min-height:54px!important;
        height:100%!important;
        display:flex!important;
        align-items:center!important;
        justify-content:center!important;
        text-align:center!important;
        white-space:normal!important;
        line-height:1.2!important;
        padding:9px 13px!important;
        color:#dbe7f3!important;
        background:rgba(255,255,255,.045)!important;
        border:1px solid rgba(255,255,255,.07)!important;
        border-radius:11px!important;
      }
      .stTabs [data-baseweb="tab"] p{
        width:100%!important;
        margin:0!important;
        color:inherit!important;
        text-align:center!important;
        font-weight:850!important;
      }
      .stTabs [aria-selected="true"]{
        background:linear-gradient(135deg,var(--gp-v3-gold),var(--gp-v3-gold-2))!important;
        color:#10233a!important;
        border-color:#f2d57c!important;
        box-shadow:0 7px 18px rgba(214,166,47,.20)!important;
      }
      .stTabs [data-baseweb="tab-highlight"]{display:none!important}

      /* Main quick-action buttons are centered and identical in height. */
      .stButton>button[kind="primary"]{
        min-height:54px!important;
        display:flex!important;
        align-items:center!important;
        justify-content:center!important;
        text-align:center!important;
        white-space:normal!important;
        line-height:1.2!important;
        border:1px solid rgba(214,166,47,.50)!important;
        background:linear-gradient(135deg,var(--gp-v3-navy-2),var(--gp-v3-navy-3))!important;
        box-shadow:0 9px 20px rgba(0,0,0,.17)!important;
      }
      .stButton>button[kind="primary"] p{
        width:100%!important;
        text-align:center!important;
        margin:0!important;
        color:#fff!important;
      }
      .stButton>button[kind="primary"]:hover{
        border-color:var(--gp-v3-gold-2)!important;
        box-shadow:0 12px 24px rgba(0,0,0,.22)!important;
      }

      /* White work surfaces remain crisp against the navy shell. */
      [data-testid="stForm"],
      [data-testid="stExpander"],
      [data-testid="stDataFrame"],
      [data-testid="stDataEditor"]{
        box-shadow:0 12px 30px rgba(0,0,0,.16)!important;
      }

      @media(max-width:900px){
        .stTabs [data-baseweb="tab-list"]{
          grid-template-columns:repeat(auto-fit,minmax(145px,1fr))!important;
        }
      }
      @media(max-width:560px){
        .stTabs [data-baseweb="tab-list"]{grid-template-columns:1fr!important}
        .stTabs [data-baseweb="tab"]{min-height:48px!important}
        .gp-kpi-card{min-height:112px}
      }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# DATABASE ORM (DocType Engine)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

CASE_STATUS_OPEN = "مفتوح"
CASE_STATUS_CLOSED = "مغلق"
COLLECTION_NOT_READY = "لم يجهز للتسليم بعد"
COLLECTION_AWAITING = "بانتظار تأكيد الاستلام"
COLLECTION_PAID_AWAITING_CLOSE = "تم تسجيل القبض - بانتظار إغلاق الحالة"  # legacy value
COLLECTION_SPECIAL_AWAITING = "حالة خاصة - بانتظار الاستلام"
COLLECTION_CLOSED = "تم الاستلام وإغلاق الحالة"
COLLECTION_ZERO_NOT_REQUIRED = "لا يحتاج تأكيد الاستلام - فاتورة صفر"
COLLECTION_PARTNER_NOT_APPLICABLE = "غير منطبق - حالة شريك"

# Machine-readable workflow states. These are deliberately separate from the
# Arabic display text so all three applications use the same state machine.
WF_WAITING = "WAITING"
WF_IN_REPAIR = "IN_REPAIR"
WF_WAIT_COLLECTION = "WAIT_COLLECTION"
WF_WAIT_PARTNER = "WAIT_PARTNER"
WF_CLOSED_ZERO = "CLOSED_ZERO_INVOICE"
WF_CLOSED_COLLECTED = "CLOSED_COLLECTED"
WF_CLOSED_PARTNER = "CLOSED_PARTNER_SETTLED"
WF_CLOSED_TV = "CLOSED_TV_CONFIRMED"

CLOSED_WORKFLOW_STATES = {
    WF_CLOSED_ZERO,
    WF_CLOSED_COLLECTED,
    WF_CLOSED_PARTNER,
    WF_CLOSED_TV,
}

NO_CHARGE_SPECIAL_CASES = {
    "يعمل من المصدر",
    "الزبون رفض الإصلاح",
    "مكلف",
    "كفالة",
    "غير قابل للإصلاح",
    "لا يوجد عطل",
}

SCHEMA = {
    "Ledger": [
        "service_id", "cycle_no", "cycle_key", "cycle_started_at", "cycle_last_event_date",
        "cycle_last_event", "cycle_document_count", "cycle_sales_total", "cycle_zero_sales_confirmed", "cycle_payment_total",
        "cycle_partner_settlement_total", "cycle_history", "workflow_state", "financial_status",
        "tool_name", "customer_name", "phone_number", "warranty_status", "document_origin",
        "reported_issue", "technician", "status", "cost_debit", "payment_credit", "balance",
        "spare_parts", "resolution_notes", "remarks", "date_logged", "date_resolved",
        "accessories", "loaner_item", "priority", "tool_photo_link",
        "source_account", "source_account_g", "source_document_count", "document_history",
        "repair_stage", "collection_status", "special_case", "partner_claim_status", "partner_claim_amount",
        "case_status", "closed_at", "closed_by", "close_note"
    ],
    "Stock": ["item_code", "item_name", "quantity", "price"],
    "Hawara": ["order_id", "order_type", "linked_service_id", "courier", "delivery_note", "document_link", "status", "date_logged"],
    "Dispatch": ["dispatch_id", "service_id", "customer_name", "courier", "delivery_note", "document_link", "date"]
}

STOCK_COLUMNS = SCHEMA["Stock"]


def normalize_doc_string(val):
    return re.sub(r'\s+', ' ', str(val or '')).strip()


def get_status_rank(val):
    """Ranking used only to order Ameen events that occur on the same date."""
    kind = ameen_event_kind(val)
    return {
        "entry": 1,
        "sale": 2,
        "partner_settlement": 3,
        "collect": 4,
    }.get(kind, 0)


def ameen_event_kind(value):
    """Return the normalized Ameen event type without guessing physical collection."""
    s = normalize_doc_string(value)
    if "قبض" in s or "Collected" in s:
        return "collect"
    if "خ صيانة" in s or "حساب وكيل" in s:
        return "partner_settlement"
    if "مبيع خ ص" in s or "جاهز" in s:
        return "sale"
    if "اد خ ص" in s or "المعالجة" in s:
        return "entry"
    return "other"


def status_from_workflow(workflow_state, special_case=""):
    wf = normalize_doc_string(workflow_state)
    special = normalize_doc_string(special_case)

    if wf == WF_CLOSED_ZERO:
        return "مغلق - فاتورة صفر (Closed)"
    if wf in {WF_CLOSED_COLLECTED, WF_CLOSED_TV}:
        return "مغلق - تم الاستلام (Closed)"
    if wf == WF_CLOSED_PARTNER:
        return "مغلق - تمت تسوية الشريك (Closed)"
    if wf == WF_WAIT_COLLECTION:
        return f"حالة خاصة - بانتظار الاستلام ({special})" if special else "جاهز للتسليم - بانتظار الاستلام (Ready / Awaiting Collection)"
    if wf == WF_WAIT_PARTNER:
        return "جاهز - بانتظار مطالبة الشريك (Partner Action)"
    if wf == WF_IN_REPAIR:
        return "قيد المعالجة (In Progress)"
    return "قيد الانتظار (Waiting)"


def map_document_to_status(doc_string, cost=0.0, collection_status="", special_case="", partner_claim_status="", case_status="", workflow_state=""):
    """Compatibility mapper for manual rows; Ameen imports should use workflow_state."""
    wf = normalize_doc_string(workflow_state)
    if wf:
        return status_from_workflow(wf, special_case)

    doc = normalize_doc_string(doc_string)
    special = normalize_doc_string(special_case)
    collection = normalize_doc_string(collection_status)
    partner = normalize_doc_string(partner_claim_status)
    case = normalize_doc_string(case_status)

    if case == CASE_STATUS_CLOSED or COLLECTION_CLOSED in collection or collection == "تم التحصيل والتسليم":
        return "مغلق - تم الاستلام (Closed)"
    if "قبض" in doc:
        return "مغلق - تم الاستلام (Closed)"
    if special:
        return f"حالة خاصة - بانتظار الاستلام ({special})"
    if "خ صيانة" in doc and "بانتظار" not in partner:
        return "مغلق محاسبياً - حساب شريك (Partner Claimed)"
    if "مبيع خ ص" in doc or "جاهز" in doc:
        return "جاهز للتسليم - بانتظار الاستلام (Ready / Awaiting Collection)"
    if "اد خ ص" in doc or "المعالجة" in doc:
        return "قيد المعالجة (In Progress)"
    return "قيد الانتظار (Waiting)"


def parse_excel_date(value):
    try:
        if value is None or str(value).strip() in ("", "nan", "NaT"):
            return ""
        if isinstance(value, (int, float)) and not pd.isna(value):
            return (pd.Timestamp("1899-12-30") + pd.to_timedelta(float(value), unit="D")).strftime("%Y-%m-%d")
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
        return parsed.strftime("%Y-%m-%d") if pd.notna(parsed) else ""
    except Exception:
        return ""


def extract_service_id(account_value, account_g_value=""):
    text = f"{account_g_value} {account_value}"
    m = re.search(r'\b([SDV]\d+)\b', text, re.IGNORECASE)
    return m.group(1).upper() if m else ""


def clean_text(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).replace("\n", " ").strip()


def parse_account_details(account_text, service_id=""):
    """Best-effort parsing of Ameen account description without assuming a fixed customer position."""
    text = clean_text(account_text)
    if not text:
        return "", "", "", "", ""
    parts = [p.strip() for p in re.split(r'[-–—]+', text) if p.strip()]
    if service_id and parts and parts[0].upper() == service_id.upper():
        parts = parts[1:]

    phone = ""
    phone_idx = None
    for i, p in enumerate(parts):
        digits = re.sub(r'\D', '', p)
        if 8 <= len(digits) <= 15:
            phone = digits
            phone_idx = i
            break

    known_code_idx = None
    for i, p in enumerate(parts):
        if re.fullmatch(r'[A-Za-z]{2,}\d+[A-Za-z0-9]*', p) or re.fullmatch(r'[A-Za-z0-9]{5,}', p):
            if re.search(r'[A-Za-z]', p) and re.search(r'\d', p):
                known_code_idx = i
                break

    warranty = "ضمن كفالة" if any(k in text for k in ["كفالة", "ضمان", "مجاني"]) else "خارج الكفالة"

    item = ""
    customer = ""
    issue = ""
    if known_code_idx is not None:
        item_parts = parts[:known_code_idx]
        if item_parts:
            if len(item_parts) >= 2:
                customer = item_parts[-1]
                item = " - ".join(item_parts[:-1])
            else:
                item = item_parts[0]
        tail_start = known_code_idx + 1
        tail = parts[tail_start:]
        if phone_idx is not None and phone_idx >= tail_start:
            if phone_idx + 1 < len(parts):
                issue = " - ".join(parts[phone_idx + 1:])
        elif tail:
            issue = " - ".join(tail)
    else:
        pre = parts[:phone_idx] if phone_idx is not None else parts
        if len(pre) >= 2:
            item = pre[0]
            customer = " - ".join(pre[1:])
        elif len(pre) == 1:
            item = pre[0]
        if phone_idx is not None and phone_idx + 1 < len(parts):
            issue = " - ".join(parts[phone_idx + 1:])

    issue = issue or text
    return item or "غير محدد", customer or "غير محدد", phone, warranty, issue


def special_case_from_remarks(text):
    t = normalize_doc_string(text)
    if any(k in t for k in ["رفض الإصلاح", "رفض الاصلاح", "الزبون رفض", "رفض الصيانة", "رفض التصليح", "لم يوافق على الإصلاح", "لم يوافق على الاصلاح"]):
        return "الزبون رفض الإصلاح"
    if any(k in t for k in ["يعمل من المصدر", "يعمل على المصدر"]):
        return "يعمل من المصدر"
    if "مكلف" in t:
        return "مكلف"
    if any(k in t for k in ["كفالة", "ضمان"]) and not any(k in t for k in ["خارج الكفالة", "خارج كفالة", "خارج الضمان"]):
        return "كفالة"
    if any(k in t for k in ["غير قابل للإصلاح", "غير قابل للاصلاح", "غير قابل للصيانة", "لاتصلح", "لا تصلح", "لا يمكن إصلاح", "لا يمكن اصلاح"]):
        return "غير قابل للإصلاح"
    if "لايوجد عطل" in t or "لا يوجد عطل" in t:
        return "لا يوجد عطل"
    return ""


def is_no_charge_special_case(value):
    return normalize_doc_string(value) in NO_CHARGE_SPECIAL_CASES


def is_zero_amount(value, tolerance=0.000001):
    """True only for a numeric value that was explicitly parsed as zero."""
    try:
        number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        return pd.notna(number) and abs(float(number)) <= tolerance
    except Exception:
        return False


def _cycle_key(service_id, cycle_no, cycle_started_at):
    start = normalize_doc_string(cycle_started_at) or "unknown"
    return f"{service_id}:C{int(cycle_no)}:{start}"


def _derive_financial_status(has_sale, sale_total, has_collect, has_partner_settlement, zero_sales_confirmed=False):
    if has_collect:
        return "قبض مسجل"
    if has_partner_settlement:
        return "خ صيانة مسجلة"
    if has_sale and zero_sales_confirmed:
        return "فاتورة مبيع صفر"
    if has_sale:
        return f"فاتورة مبيع: {float(sale_total):.3f}"
    return "لا توجد فاتورة مبيع"


def normalize_ameen_dataframe(raw_excel):
    """Normalize Ameen A:L into one CURRENT repair-cycle row per service ID.

    A service ID can be reused after a return/re-repair. Repeated اد خ ص rows before
    the first sale remain in the same cycle (for example inventory corrections).
    A new اد خ ص after a sale/collection/partner-settlement starts a new cycle.
    """
    df = raw_excel.copy()
    if df.empty:
        return pd.DataFrame()

    expected = [
        "account", "prev_balance", "debit", "credit", "uncolllected", "current_balance",
        "account_name", "date", "origin", "debit_line", "credit_line", "statement"
    ]
    if df.shape[1] < 12:
        return pd.DataFrame()

    df = df.iloc[:, :12].copy()
    df.columns = expected
    df = df[df["origin"].astype(str).str.strip().str.lower() != "أصل السند"].copy()
    df["_source_order"] = range(len(df))
    df["service_id"] = [extract_service_id(a, g) for a, g in zip(df["account"], df["account_name"])]
    df = df[df["service_id"].str.strip() != ""].copy()
    if df.empty:
        return pd.DataFrame()

    df["date_parsed"] = df["date"].apply(parse_excel_date)
    # Keep explicit numeric parsing separate from display totals so a blank amount
    # can never be mistaken for a genuine zero-value sales invoice.
    df["_debit_line_numeric"] = pd.to_numeric(df["debit_line"], errors="coerce")
    for c in ["debit_line", "credit_line", "debit", "credit"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["origin_clean"] = df["origin"].apply(normalize_doc_string)
    df["event_kind"] = df["origin_clean"].apply(ameen_event_kind)
    df["statement_clean"] = df["statement"].apply(clean_text)
    df["source_account"] = df["account"].apply(clean_text)
    df["source_account_g"] = df["account_name"].apply(clean_text)

    records = []
    for sid, grp in df.groupby("service_id", sort=False):
        grp = grp.copy()
        grp["sort_date"] = pd.to_datetime(grp["date_parsed"], errors="coerce")
        grp["origin_rank"] = grp["origin_clean"].apply(get_status_rank)
        grp = grp.sort_values(["sort_date", "origin_rank", "_source_order"], kind="stable").reset_index(drop=True)

        # Assign repair cycles. A second intake before a sale is treated as a correction
        # inside the same repair cycle; a new intake after a release-stage event reopens it.
        cycle_no = 1
        cycle_has_release_event = False
        cycle_numbers = []
        for _, event in grp.iterrows():
            kind = event["event_kind"]
            if kind == "entry" and cycle_numbers and cycle_has_release_event:
                cycle_no += 1
                cycle_has_release_event = False
            cycle_numbers.append(cycle_no)
            if kind in {"sale", "collect", "partner_settlement"}:
                cycle_has_release_event = True
        grp["cycle_no"] = cycle_numbers

        current_cycle_no = int(grp["cycle_no"].max())
        cycle = grp[grp["cycle_no"] == current_cycle_no].copy().reset_index(drop=True)

        header_text = next((x for x in grp["source_account_g"] if x), "") or next((x for x in grp["source_account"] if x), "")
        item, customer, phone, warranty, issue = parse_account_details(header_text, sid)

        current_statements = [x for x in cycle["statement_clean"].tolist() if x and x not in ("13", "nan")]
        special_cases = [special_case_from_remarks(x) for x in current_statements]
        special_case = next((x for x in special_cases if x), "")

        sale_mask = cycle["event_kind"].eq("sale")
        collect_mask = cycle["event_kind"].eq("collect")
        settlement_mask = cycle["event_kind"].eq("partner_settlement")
        entry_mask = cycle["event_kind"].eq("entry")

        has_sale = bool(sale_mask.any())
        has_collect = bool(collect_mask.any())
        has_partner_settlement = bool(settlement_mask.any())
        has_entry = bool(entry_mask.any())
        is_partner = sid.upper().startswith("V")

        cycle_sales_total = float(cycle.loc[sale_mask, "debit_line"].sum())
        sale_amount_values = cycle.loc[sale_mask, "_debit_line_numeric"]
        cycle_zero_sales_confirmed = bool(
            has_sale
            and sale_amount_values.notna().all()
            and sale_amount_values.apply(lambda value: is_zero_amount(value)).all()
        )
        cycle_payment_total = float(cycle.loc[collect_mask, "credit_line"].sum())
        cycle_partner_settlement_total = float(cycle.loc[settlement_mask, "credit_line"].sum())

        # Explicit state machine, in order of strongest evidence.
        # User rule: ANY genuine zero-value sales cycle closes immediately,
        # including V partner cases. A missing amount is not treated as zero.
        if has_collect:
            workflow_state = WF_CLOSED_COLLECTED
            close_note = "قبض في كشف الأمين - تم الاستلام"
        elif cycle_zero_sales_confirmed:
            workflow_state = WF_CLOSED_ZERO
            close_note = "فاتورة مبيع خ ص بقيمة صفر ضمن الدورة الحالية - إغلاق تلقائي"
        elif is_partner and has_partner_settlement:
            workflow_state = WF_CLOSED_PARTNER
            close_note = "إغلاق شريك - خ صيانة ضمن الدورة الحالية"
        elif is_partner and is_no_charge_special_case(special_case):
            workflow_state = WF_CLOSED_PARTNER
            close_note = f"إغلاق شريك - حالة خاصة: {special_case}"
        elif is_partner and has_sale:
            workflow_state = WF_WAIT_PARTNER
            close_note = ""
        elif (not is_partner) and has_sale:
            workflow_state = WF_WAIT_COLLECTION
            close_note = ""
        elif has_entry:
            workflow_state = WF_IN_REPAIR
            close_note = ""
        else:
            workflow_state = WF_WAITING
            close_note = ""

        case_status = CASE_STATUS_CLOSED if workflow_state in CLOSED_WORKFLOW_STATES else CASE_STATUS_OPEN

        if workflow_state in {WF_CLOSED_COLLECTED, WF_CLOSED_TV}:
            collection_status = COLLECTION_CLOSED
        elif workflow_state == WF_CLOSED_ZERO:
            collection_status = COLLECTION_ZERO_NOT_REQUIRED
        elif workflow_state in {WF_CLOSED_PARTNER, WF_WAIT_PARTNER}:
            collection_status = COLLECTION_PARTNER_NOT_APPLICABLE
        elif workflow_state == WF_WAIT_COLLECTION:
            collection_status = COLLECTION_SPECIAL_AWAITING if special_case else COLLECTION_AWAITING
        else:
            collection_status = COLLECTION_NOT_READY

        if is_partner:
            if workflow_state == WF_CLOSED_PARTNER:
                partner_claim_status = "تمت تسوية الشريك"
            elif workflow_state == WF_WAIT_PARTNER:
                partner_claim_status = "بانتظار مطالبة الشريك"
            elif workflow_state == WF_CLOSED_ZERO:
                partner_claim_status = "لا مطالبة - فاتورة صفر"
            elif is_no_charge_special_case(special_case):
                partner_claim_status = "لا مطالبة - حالة خاصة"
            else:
                partner_claim_status = "قيد الصيانة"
        else:
            partner_claim_status = "غير منطبق"

        if workflow_state in CLOSED_WORKFLOW_STATES:
            repair_stage = CASE_STATUS_CLOSED
        elif workflow_state == WF_WAIT_COLLECTION:
            repair_stage = "جاهز للتسليم"
        elif workflow_state == WF_WAIT_PARTNER:
            repair_stage = "جاهز - بانتظار تسوية الشريك"
        elif workflow_state == WF_IN_REPAIR:
            repair_stage = "قيد المعالجة"
        else:
            repair_stage = "قيد الانتظار"

        first_cycle_date = next((x for x in cycle["date_parsed"].tolist() if x), datetime.now().strftime("%Y-%m-%d"))
        first_entry_date = next((x for x in cycle.loc[entry_mask, "date_parsed"].tolist() if x), "")
        cycle_started_at = first_entry_date or first_cycle_date
        cycle_last_event_date = next((x for x in reversed(cycle["date_parsed"].tolist()) if x), cycle_started_at)
        latest = cycle.iloc[-1]
        cycle_last_event = latest["origin_clean"]

        def latest_event_date(mask=None):
            values = cycle.loc[mask, "date_parsed"].tolist() if mask is not None else cycle["date_parsed"].tolist()
            valid = [x for x in values if x]
            return valid[-1] if valid else cycle_last_event_date

        closure_date = ""
        if workflow_state == WF_CLOSED_COLLECTED:
            closure_date = latest_event_date(collect_mask)
        elif workflow_state == WF_CLOSED_ZERO:
            closure_date = latest_event_date(sale_mask)
        elif workflow_state == WF_CLOSED_PARTNER:
            closure_date = latest_event_date(settlement_mask) if has_partner_settlement else cycle_last_event_date

        full_history = " | ".join(
            f"{d} :: {o}" for d, o in zip(grp["date_parsed"], grp["origin_clean"]) if o
        )
        cycle_history = " | ".join(
            f"{d} :: {o}" for d, o in zip(cycle["date_parsed"], cycle["origin_clean"]) if o
        )
        remarks = " | ".join(dict.fromkeys(current_statements))
        financial_status = _derive_financial_status(
            has_sale, cycle_sales_total, has_collect, has_partner_settlement, cycle_zero_sales_confirmed
        )
        status = status_from_workflow(workflow_state, special_case)

        records.append({
            "service_id": sid,
            "cycle_no": current_cycle_no,
            "cycle_key": _cycle_key(sid, current_cycle_no, cycle_started_at),
            "cycle_started_at": cycle_started_at,
            "cycle_last_event_date": cycle_last_event_date,
            "cycle_last_event": cycle_last_event,
            "cycle_document_count": int(len(cycle)),
            "cycle_sales_total": cycle_sales_total,
            "cycle_zero_sales_confirmed": int(cycle_zero_sales_confirmed),
            "cycle_payment_total": cycle_payment_total,
            "cycle_partner_settlement_total": cycle_partner_settlement_total,
            "cycle_history": cycle_history,
            "workflow_state": workflow_state,
            "financial_status": financial_status,
            "tool_name": item,
            "customer_name": customer,
            "phone_number": phone,
            "warranty_status": warranty,
            "document_origin": cycle_last_event,
            "reported_issue": issue,
            "technician": "Ameen Import",
            "status": status,
            "cost_debit": cycle_sales_total,
            "payment_credit": cycle_payment_total,
            "balance": max(cycle_sales_total - cycle_payment_total, 0.0),
            "spare_parts": "لا حاجة / متوفرة",
            "resolution_notes": "",
            "remarks": remarks,
            "date_logged": cycle_started_at,
            "date_resolved": closure_date,
            "accessories": "",
            "loaner_item": "",
            "priority": "عادي",
            "tool_photo_link": "",
            "source_account": next((x for x in grp["source_account"] if x), ""),
            "source_account_g": next((x for x in grp["source_account_g"] if x), ""),
            "source_document_count": int(len(grp)),
            "document_history": full_history,
            "repair_stage": repair_stage,
            "collection_status": collection_status,
            "special_case": special_case,
            "partner_claim_status": partner_claim_status,
            "partner_claim_amount": cycle_partner_settlement_total,
            "case_status": case_status,
            "closed_at": closure_date,
            "closed_by": "Ameen Import" if workflow_state in CLOSED_WORKFLOW_STATES else "",
            "close_note": close_note,
        })

    return pd.DataFrame(records)


def apply_workflow_columns(df):
    """Backfill the new cycle-aware workflow while preserving explicit current states."""
    if df.empty:
        return df

    defaults = {
        "cycle_no": 0,
        "cycle_key": "",
        "cycle_started_at": "",
        "cycle_last_event_date": "",
        "cycle_last_event": "",
        "cycle_document_count": 0,
        "cycle_sales_total": 0.0,
        "cycle_zero_sales_confirmed": 0,
        "cycle_payment_total": 0.0,
        "cycle_partner_settlement_total": 0.0,
        "cycle_history": "",
        "workflow_state": "",
        "financial_status": "",
        "source_account": "",
        "source_account_g": "",
        "source_document_count": 1,
        "document_history": "",
        "repair_stage": "",
        "collection_status": "",
        "special_case": "",
        "partner_claim_status": "غير منطبق",
        "partner_claim_amount": 0.0,
        "case_status": CASE_STATUS_OPEN,
        "closed_at": "",
        "closed_by": "",
        "close_note": "",
    }
    for c, default in defaults.items():
        if c not in df.columns:
            df[c] = default

    for c in ["cycle_no", "cycle_document_count", "cycle_zero_sales_confirmed", "source_document_count"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    for c in ["cycle_sales_total", "cycle_payment_total", "cycle_partner_settlement_total", "partner_claim_amount"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    valid_states = {
        WF_WAITING, WF_IN_REPAIR, WF_WAIT_COLLECTION, WF_WAIT_PARTNER,
        WF_CLOSED_ZERO, WF_CLOSED_COLLECTED, WF_CLOSED_PARTNER, WF_CLOSED_TV,
    }

    for idx, r in df.iterrows():
        sid = normalize_doc_string(r.get("service_id", "")).upper()
        is_partner = sid.startswith("V")
        wf = normalize_doc_string(r.get("workflow_state", ""))
        case_status = normalize_doc_string(r.get("case_status", "")) or CASE_STATUS_OPEN
        closed_by = normalize_doc_string(r.get("closed_by", ""))
        close_note = normalize_doc_string(r.get("close_note", ""))

        special = normalize_doc_string(r.get("special_case", "")) or special_case_from_remarks(r.get("remarks", ""))
        df.at[idx, "special_case"] = special

        # Manual/TV closure has priority only for the SAME cycle. A later Ameen import
        # decides whether the service ID has moved to a new cycle before this function.
        if case_status == CASE_STATUS_CLOSED and closed_by and closed_by != "Ameen Import":
            wf = WF_CLOSED_TV

        if wf not in valid_states:
            # Legacy row migration. Prefer cycle_history when it exists because full
            # document_history can contain several historical repair cycles.
            docs = normalize_doc_string(r.get("cycle_history", "")) or normalize_doc_string(
                f"{r.get('document_origin', '')} {r.get('document_history', '')}"
            )
            has_collect = "قبض" in docs
            has_sale = "مبيع خ ص" in docs
            has_entry = "اد خ ص" in docs
            has_partner_settlement = "خ صيانة" in docs
            is_ameen = normalize_doc_string(r.get("technician", "")) == "Ameen Import"
            sale_total = r.get("cycle_sales_total", r.get("cost_debit", 0.0))
            if not normalize_doc_string(r.get("cycle_history", "")):
                sale_total = r.get("cost_debit", 0.0)

            if case_status == CASE_STATUS_CLOSED and closed_by and closed_by != "Ameen Import":
                wf = WF_CLOSED_TV
            elif "فاتورة" in close_note and "صفر" in close_note:
                wf = WF_CLOSED_ZERO
            elif has_collect:
                wf = WF_CLOSED_COLLECTED
            elif is_ameen and has_sale and int(pd.to_numeric(pd.Series([r.get("cycle_zero_sales_confirmed", 0)]), errors="coerce").fillna(0).iloc[0]) == 1:
                wf = WF_CLOSED_ZERO
            elif is_partner and has_partner_settlement:
                wf = WF_CLOSED_PARTNER
            elif is_partner and has_sale:
                wf = WF_WAIT_PARTNER
            elif (not is_partner) and has_sale:
                wf = WF_WAIT_COLLECTION
            elif has_entry:
                wf = WF_IN_REPAIR
            else:
                wf = WF_WAITING

        case_status = CASE_STATUS_CLOSED if wf in CLOSED_WORKFLOW_STATES else CASE_STATUS_OPEN
        df.at[idx, "workflow_state"] = wf
        df.at[idx, "case_status"] = case_status

        if wf in {WF_CLOSED_COLLECTED, WF_CLOSED_TV}:
            df.at[idx, "collection_status"] = COLLECTION_CLOSED
            df.at[idx, "repair_stage"] = CASE_STATUS_CLOSED
        elif wf == WF_CLOSED_ZERO:
            df.at[idx, "collection_status"] = COLLECTION_ZERO_NOT_REQUIRED
            df.at[idx, "repair_stage"] = CASE_STATUS_CLOSED
        elif wf == WF_CLOSED_PARTNER:
            df.at[idx, "collection_status"] = COLLECTION_PARTNER_NOT_APPLICABLE
            df.at[idx, "repair_stage"] = CASE_STATUS_CLOSED
        elif wf == WF_WAIT_PARTNER:
            df.at[idx, "collection_status"] = COLLECTION_PARTNER_NOT_APPLICABLE
            df.at[idx, "repair_stage"] = "جاهز - بانتظار تسوية الشريك"
        elif wf == WF_WAIT_COLLECTION:
            df.at[idx, "collection_status"] = COLLECTION_SPECIAL_AWAITING if special else COLLECTION_AWAITING
            df.at[idx, "repair_stage"] = "جاهز للتسليم"
        elif wf == WF_IN_REPAIR:
            df.at[idx, "collection_status"] = COLLECTION_NOT_READY
            df.at[idx, "repair_stage"] = "قيد المعالجة"
        else:
            df.at[idx, "collection_status"] = COLLECTION_NOT_READY
            df.at[idx, "repair_stage"] = "قيد الانتظار"

        if is_partner:
            if wf == WF_CLOSED_PARTNER:
                df.at[idx, "partner_claim_status"] = "تمت تسوية الشريك"
            elif wf == WF_WAIT_PARTNER:
                df.at[idx, "partner_claim_status"] = "بانتظار مطالبة الشريك"
            elif wf == WF_CLOSED_ZERO:
                df.at[idx, "partner_claim_status"] = "لا مطالبة - فاتورة صفر"
            elif is_no_charge_special_case(special):
                df.at[idx, "partner_claim_status"] = "لا مطالبة - حالة خاصة"
            elif not normalize_doc_string(r.get("partner_claim_status", "")):
                df.at[idx, "partner_claim_status"] = "قيد الصيانة"
        else:
            df.at[idx, "partner_claim_status"] = "غير منطبق"

        if not normalize_doc_string(r.get("financial_status", "")):
            docs = normalize_doc_string(r.get("cycle_history", "")) or normalize_doc_string(r.get("document_origin", ""))
            df.at[idx, "financial_status"] = _derive_financial_status(
                "مبيع خ ص" in docs,
                r.get("cycle_sales_total", r.get("cost_debit", 0.0)),
                "قبض" in docs,
                "خ صيانة" in docs,
                bool(int(pd.to_numeric(pd.Series([r.get("cycle_zero_sales_confirmed", 0)]), errors="coerce").fillna(0).iloc[0])),
            )

        if wf in CLOSED_WORKFLOW_STATES:
            if not normalize_doc_string(r.get("closed_at", "")):
                fallback_date = normalize_doc_string(r.get("date_resolved", "")) or normalize_doc_string(r.get("cycle_last_event_date", "")) or normalize_doc_string(r.get("date_logged", ""))
                df.at[idx, "closed_at"] = fallback_date
            if not normalize_doc_string(r.get("date_resolved", "")):
                df.at[idx, "date_resolved"] = str(df.at[idx, "closed_at"]).split(" ")[0]
            if not closed_by:
                df.at[idx, "closed_by"] = "Ameen Import"

        df.at[idx, "status"] = status_from_workflow(wf, special)

    return df


def preserve_manual_closures(imported_df, existing_df):
    """Preserve manual/TV closure only when the Ameen import is still the same repair cycle."""
    if imported_df is None or imported_df.empty or existing_df is None or existing_df.empty:
        return imported_df

    result = imported_df.copy()
    existing = existing_df.copy()
    for frame in (result, existing):
        for col, default in {
            "cycle_no": 0, "cycle_key": "", "cycle_started_at": "", "workflow_state": "",
            "case_status": CASE_STATUS_OPEN, "closed_at": "", "closed_by": "", "close_note": ""
        }.items():
            if col not in frame.columns:
                frame[col] = default

    manual_closed = existing[
        existing["case_status"].astype(str).eq(CASE_STATUS_CLOSED)
        & (
            existing["workflow_state"].astype(str).eq(WF_CLOSED_TV)
            | (
                existing["closed_by"].astype(str).str.strip().ne("")
                & ~existing["closed_by"].astype(str).eq("Ameen Import")
            )
        )
    ].copy()
    if manual_closed.empty:
        return result

    manual_closed["_cycle_sort"] = pd.to_numeric(manual_closed["cycle_no"], errors="coerce").fillna(0)
    manual_closed["_closed_sort"] = pd.to_datetime(manual_closed["closed_at"], errors="coerce")
    manual_closed = manual_closed.sort_values(["service_id", "_cycle_sort", "_closed_sort"], kind="stable")
    manual_closed = manual_closed.drop_duplicates("service_id", keep="last").set_index("service_id")

    for idx, row in result.iterrows():
        sid = str(row.get("service_id", ""))
        if sid not in manual_closed.index:
            continue

        previous = manual_closed.loc[sid]
        current_key = normalize_doc_string(row.get("cycle_key", ""))
        previous_key = normalize_doc_string(previous.get("cycle_key", ""))
        current_no = int(pd.to_numeric(pd.Series([row.get("cycle_no", 0)]), errors="coerce").fillna(0).iloc[0])
        previous_no = int(pd.to_numeric(pd.Series([previous.get("cycle_no", 0)]), errors="coerce").fillna(0).iloc[0])

        same_cycle = False
        if current_key and previous_key:
            same_cycle = current_key == previous_key
        elif current_no and previous_no:
            same_cycle = current_no == previous_no
        else:
            current_start = pd.to_datetime(row.get("cycle_started_at", row.get("date_logged", "")), errors="coerce")
            previous_closed = pd.to_datetime(previous.get("closed_at", previous.get("date_resolved", "")), errors="coerce")
            if pd.notna(current_start) and pd.notna(previous_closed):
                same_cycle = current_start <= previous_closed
            else:
                # Legacy fallback: preserve once, but future cycle-aware imports will
                # have keys/numbers and will no longer be trapped by this fallback.
                same_cycle = True

        if not same_cycle:
            continue

        result.at[idx, "workflow_state"] = WF_CLOSED_TV
        result.at[idx, "case_status"] = CASE_STATUS_CLOSED
        result.at[idx, "closed_at"] = previous.get("closed_at", "")
        result.at[idx, "closed_by"] = previous.get("closed_by", "TV") or "TV"
        result.at[idx, "close_note"] = previous.get("close_note", "") or "Manual collection confirmation"
        result.at[idx, "collection_status"] = COLLECTION_CLOSED
        result.at[idx, "repair_stage"] = CASE_STATUS_CLOSED
        result.at[idx, "status"] = status_from_workflow(WF_CLOSED_TV)
        if previous.get("closed_at", ""):
            result.at[idx, "date_resolved"] = str(previous.get("closed_at", "")).split(" ")[0]

    return result


def deduplicate_ledger(df):
    """Keep the newest repair cycle, then the furthest state inside that cycle."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df

    work = df.copy()
    if "service_id" not in work.columns:
        return work

    work["service_id"] = work["service_id"].astype(str).replace({"nan": "", "None": ""})
    work = work[work["service_id"].str.strip() != ""].copy()
    if work.empty:
        return work

    if "cycle_no" not in work.columns:
        work["cycle_no"] = 0
    work["_cycle_no"] = pd.to_numeric(work["cycle_no"], errors="coerce").fillna(0)

    state_rank = {
        WF_WAITING: 0,
        WF_IN_REPAIR: 1,
        WF_WAIT_COLLECTION: 2,
        WF_WAIT_PARTNER: 2,
        WF_CLOSED_ZERO: 4,
        WF_CLOSED_PARTNER: 4,
        WF_CLOSED_COLLECTED: 5,
        WF_CLOSED_TV: 5,
    }
    if "workflow_state" in work.columns:
        work["_workflow_rank"] = work["workflow_state"].map(state_rank).fillna(0)
    elif "document_origin" in work.columns:
        work["_workflow_rank"] = work["document_origin"].apply(get_status_rank)
    else:
        work["_workflow_rank"] = 0

    date_series = pd.Series(pd.NaT, index=work.index, dtype="datetime64[ns]")
    for col in ("cycle_last_event_date", "date_resolved", "date_logged"):
        if col in work.columns:
            date_series = date_series.fillna(pd.to_datetime(work[col], dayfirst=True, errors="coerce"))
    work["_workflow_date"] = date_series

    work = work.sort_values(
        ["service_id", "_cycle_no", "_workflow_date", "_workflow_rank"],
        ascending=[True, True, True, True],
        kind="stable",
        na_position="first",
    )
    work = work.groupby("service_id", as_index=False, sort=False).tail(1)
    return work.drop(columns=["_cycle_no", "_workflow_rank", "_workflow_date"], errors="ignore").reset_index(drop=True)


def _worksheet_missing_error(exc, worksheet_name=""):
    name = type(exc).__name__.lower()
    message = str(exc).strip().lower()
    target = str(worksheet_name or "").strip().lower()
    return (
        "worksheetnotfound" in name
        or ("worksheet" in message and ("not found" in message or "does not exist" in message))
        or (target and message == target)
    )


def get_doctype(doctype_name):
    """Read the requested worksheet directly from Google Sheets (no stale app cache)."""
    try:
        df = conn.read(worksheet=doctype_name, ttl=0)
        df = df.dropna(how='all')

        for col in SCHEMA[doctype_name]:
            if col not in df.columns:
                df[col] = ""

        if doctype_name == "Ledger":
            df['service_id'] = df['service_id'].astype(str).replace({'nan': '', 'None': ''})
            df = df[df['service_id'].str.strip() != ""]

            for col in SCHEMA["Ledger"]:
                if col not in ['cost_debit', 'payment_credit', 'balance']:
                    df[col] = df[col].fillna("").astype(str).replace({'nan': '', 'None': ''})

            for col in ['cost_debit', 'payment_credit', 'balance', 'cycle_sales_total', 'cycle_payment_total', 'cycle_partner_settlement_total', 'partner_claim_amount']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            for col in ['cycle_no', 'cycle_document_count', 'cycle_zero_sales_confirmed', 'source_document_count']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            df.loc[df['spare_parts'] == "", 'spare_parts'] = "لا حاجة / متوفرة"
            df = apply_workflow_columns(df)
            return deduplicate_ledger(df)

        return df
    except Exception as e:
        error_msg = str(e).strip()
        if not _worksheet_missing_error(e, doctype_name) and "HTTPError" in error_msg:
            st.error(f"⚠️ خطأ في الاتصال (Connection Error): {error_msg}")
        return pd.DataFrame(columns=SCHEMA[doctype_name])


def save_doctype(doctype_name, df):
    """Update a worksheet; create it automatically on the first write if missing."""
    if doctype_name == "Ledger":
        df = apply_workflow_columns(df)
        df = deduplicate_ledger(df)
        df = df[df['service_id'].astype(str).str.strip() != ""]

    with golden_loading(tr("saving_data")):
        try:
            conn.update(worksheet=doctype_name, data=df)
        except Exception as exc:
            if not _worksheet_missing_error(exc, doctype_name):
                raise
            # First-ever import: create the missing worksheet with the same schema/data.
            conn.create(worksheet=doctype_name, data=df)
        # GSheetsConnection uses Streamlit's data cache internally; clear it after writes.
        try:
            st.cache_data.clear()
        except Exception:
            pass


def _canonical_stock_header(value):
    text = normalize_doc_string(value).lower().replace("ـ", "")
    return re.sub(r"[^0-9a-zA-Z\u0600-\u06FF]+", "", text)


def _clean_item_code(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, (int, float)) and not pd.isna(value) and float(value).is_integer():
        return str(int(value))
    text = str(value).strip()
    return re.sub(r"\.0$", "", text)


def _stock_column_map(columns):
    aliases = {
        "item_code": {"mtcode", "itemcode", "code", "materialcode", "productcode", "كودالمادة", "رمزالمادة", "رقمالمادة", "كودالصنف", "رمزالصنف"},
        "item_name": {"اسمالمادة", "itemname", "name", "description", "materialname", "productname", "اسمالصنف", "وصفالمادة", "الوصف"},
        "quantity": {"quantity", "qty", "stock", "balance", "available", "onhand", "الكمية", "كمية", "الرصيد", "رصيد", "الرصيدالحالي", "الكميةالحالية", "المتوفر"},
        "price": {"الجملة", "سعرالجملة", "wholesale", "wholesaleprice", "price", "unitprice", "السعر", "سعر", "سعرالبيع", "المبيع"},
    }
    normalized = {_canonical_stock_header(col): col for col in columns}
    result = {}
    for target, names in aliases.items():
        for alias in names:
            if alias in normalized:
                result[target] = normalized[alias]
                break
    return result


def read_stock_report(uploaded_file):
    """Read Excel/CSV stock reports and auto-detect the actual header row/sheet."""
    filename = str(getattr(uploaded_file, "name", "") or "").lower()
    try:
        file_bytes = uploaded_file.getvalue()
    except Exception:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()

    if filename.endswith(".csv"):
        last_error = None
        for encoding in ("utf-8-sig", "utf-8", "cp1256", "latin1"):
            try:
                return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding=encoding)
            except Exception as exc:
                last_error = exc
        raise last_error or ValueError(tr("stock_invalid"))

    excel = pd.ExcelFile(io.BytesIO(file_bytes))
    fallback = None
    for sheet_name in excel.sheet_names:
        preview = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=None, nrows=30)
        if fallback is None:
            fallback = (sheet_name, 0)
        for idx, row in preview.iterrows():
            mapping = _stock_column_map(row.tolist())
            # Ameen stock reports may omit the code; name + quantity/price is still usable.
            if "item_name" in mapping and any(key in mapping for key in ("item_code", "quantity", "price")):
                return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=int(idx))

    sheet_name, header_row = fallback or (excel.sheet_names[0], 0)
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet_name, header=header_row)


def _normalized_stock_name(value):
    return _canonical_stock_header(value)


def _generated_stock_code(item_name):
    """Stable internal code used only when a report genuinely has no item-code column."""
    key = _normalized_stock_name(item_name)
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12].upper()
    return f"AUTO-{digest}"

def normalize_stock_report(raw, existing_stock=None):
    """Normalize common stock/price reports without losing existing quantity or price."""
    if raw is None or raw.empty:
        raise ValueError(tr("stock_invalid"))

    mapping = _stock_column_map(raw.columns)
    if "item_name" not in mapping or not any(key in mapping for key in ("item_code", "quantity", "price")):
        raise ValueError(tr("stock_invalid"))

    existing_source = existing_stock.copy() if existing_stock is not None else pd.DataFrame(columns=STOCK_COLUMNS)
    for col in STOCK_COLUMNS:
        if col not in existing_source.columns:
            existing_source[col] = "" if col in {"item_code", "item_name"} else 0.0

    # Reuse an existing real code when a code-less report has one unambiguous name match.
    existing_name_codes = {}
    if not existing_source.empty:
        name_groups = existing_source.assign(
            _name_key=existing_source["item_name"].map(_normalized_stock_name),
            _clean_code=existing_source["item_code"].map(_clean_item_code),
        ).groupby("_name_key")["_clean_code"].agg(lambda values: [v for v in dict.fromkeys(values) if v])
        existing_name_codes = {key: values[0] for key, values in name_groups.items() if key and len(values) == 1}

    work = pd.DataFrame(index=raw.index)
    work["item_name"] = raw[mapping["item_name"]].fillna("").astype(str).str.strip().str.strip('"')
    if "item_code" in mapping:
        work["item_code"] = raw[mapping["item_code"]].apply(_clean_item_code)
    else:
        work["item_code"] = work["item_name"].map(
            lambda name: existing_name_codes.get(_normalized_stock_name(name), "") or _generated_stock_code(name)
        )
    work = work[work["item_name"].map(_normalized_stock_name).ne("")].copy()
    work["item_code"] = work["item_code"].replace({"nan": "", "None": ""})
    missing_code = work["item_code"].astype(str).str.strip().eq("")
    work.loc[missing_code, "item_code"] = work.loc[missing_code, "item_name"].map(
        lambda name: existing_name_codes.get(_normalized_stock_name(name), "") or _generated_stock_code(name)
    )

    has_quantity = "quantity" in mapping
    has_price = "price" in mapping
    if has_quantity:
        quantity_text = raw.loc[work.index, mapping["quantity"]].astype(str).str.replace(",", "", regex=False)
        work["quantity"] = pd.to_numeric(quantity_text, errors="coerce")
    if has_price:
        price_text = raw.loc[work.index, mapping["price"]].astype(str).str.replace(",", "", regex=False)
        work["price"] = pd.to_numeric(price_text, errors="coerce")

    # Consolidate reports that repeat one item across locations/batches.
    aggregations = {"item_name": "last"}
    if has_quantity:
        aggregations["quantity"] = lambda s: s.sum(min_count=1)
    if has_price:
        aggregations["price"] = "last"
    work = work.groupby("item_code", as_index=False, sort=False).agg(aggregations)

    existing = existing_source.copy()
    for col in STOCK_COLUMNS:
        if col not in existing.columns:
            existing[col] = "" if col in {"item_code", "item_name"} else 0.0
    if not existing.empty:
        existing["item_code"] = existing["item_code"].apply(_clean_item_code)
        existing["quantity"] = pd.to_numeric(existing["quantity"], errors="coerce").fillna(0.0)
        existing["price"] = pd.to_numeric(existing["price"], errors="coerce").fillna(0.0)
    existing = existing.drop_duplicates("item_code", keep="last").set_index("item_code", drop=False)

    rows = []
    for _, incoming in work.iterrows():
        code = incoming["item_code"]
        old = existing.loc[code] if code in existing.index else None
        old_name = normalize_doc_string(old.get("item_name", "")) if old is not None else ""
        old_quantity = float(old.get("quantity", 0.0)) if old is not None else 0.0
        old_price = float(old.get("price", 0.0)) if old is not None else 0.0
        qty = incoming.get("quantity") if has_quantity else None
        price = incoming.get("price") if has_price else None
        rows.append({
            "item_code": code,
            "item_name": normalize_doc_string(incoming.get("item_name", "")) or old_name,
            "quantity": float(qty) if has_quantity and pd.notna(qty) else old_quantity,
            "price": float(price) if has_price and pd.notna(price) else old_price,
        })

    imported = pd.DataFrame(rows, columns=STOCK_COLUMNS)

    # Keep existing items that were not present in this particular report.
    if not existing.empty:
        untouched = existing[~existing.index.isin(imported["item_code"])][STOCK_COLUMNS].reset_index(drop=True)
        imported = pd.concat([untouched, imported], ignore_index=True)

    imported = imported.drop_duplicates("item_code", keep="last").reset_index(drop=True)
    return imported, {"has_quantity": has_quantity, "has_price": has_price, "imported_count": len(work)}


def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False, sheet_name='Export')
    return output.getvalue()


def upload_to_cloud(file_buffer):
    if not IMGBB_API_KEY:
        st.warning("⚠️ رفع الصور متوقف حتى يتم ضبط IMGBB_API_KEY في إعدادات التطبيق الآمنة.")
        return ""
    try:
        b64_img = base64.b64encode(file_buffer.getvalue()).decode("utf-8")
        res = requests.post(f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}", data={"image": b64_img}, timeout=20)
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

if is_tv_mode:
    st.session_state['logged_in_user'] = "TV_Guest"
    st.session_state['current_module'] = 'TV_Display'

USERS = {}
admin_password = get_runtime_secret("APP_ADMIN_PASSWORD")
tech_password = get_runtime_secret("APP_TECH_PASSWORD")
if admin_password:
    USERS["admin"] = {"pass": admin_password, "role": "System Administrator"}
if tech_password:
    USERS["tech"] = {"pass": tech_password, "role": "Support Agent"}

if not is_tv_mode and not USERS:
    st.error("⚠️ يجب ضبط APP_ADMIN_PASSWORD أو APP_TECH_PASSWORD في إعدادات التطبيق الآمنة قبل تسجيل الدخول.")
    st.stop()

if st.session_state['logged_in_user'] is None:
    st.markdown(
        """
        <div class="gp-login-brand">
          <div class="gp-login-logo">GP</div>
          <h1>Golden Palace ERP</h1>
          <p>القصر الذهبي للمعدات · Operations Workspace</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, login_col, _ = st.columns([1, 1.05, 1])
    with login_col:
        st.markdown(
            f"<div class='gp-login-card-title'><strong>{'تسجيل الدخول' if st.session_state.get('ui_language','ar') == 'ar' else 'Sign in'}</strong><small>{'استخدم حساب العمل للمتابعة' if st.session_state.get('ui_language','ar') == 'ar' else 'Use your work account to continue'}</small></div>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            u_in = st.text_input("اسم المستخدم / Username")
            p_in = st.text_input("كلمة المرور / Password", type="password")
            submit_text = "دخول إلى النظام" if st.session_state.get('ui_language','ar') == 'ar' else "Sign in to ERP"
            if st.form_submit_button(submit_text, use_container_width=True, type="primary"):
                if u_in in USERS and USERS[u_in]["pass"] == p_in:
                    st.session_state['logged_in_user'] = u_in
                    st.rerun()
                else:
                    st.error("بيانات الدخول غير صحيحة. / Invalid credentials.")
    st.stop()

current_user = st.session_state['logged_in_user']
is_admin = current_user in USERS and "Administrator" in USERS[current_user]["role"]

if not is_tv_mode:
    with st.sidebar:
        st.markdown(
            """
            <div class="gp-side-brand">
              <div class="gp-side-brand-top">
                <div class="gp-side-mark">GP</div>
                <div><strong>Golden Palace ERP</strong><small>Operations Workspace</small></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("LANGUAGE / اللغة")
        st.selectbox(
            "🌐 اللغة / Language",
            options=["ar", "en"],
            key="ui_language",
            format_func=lambda value: "العربية" if value == "ar" else "English",
            label_visibility="collapsed",
        )

        role_text = USERS.get(current_user, {}).get('role', 'Viewer')
        st.markdown(
            f"""
            <div class="gp-user-card">
              <div class="gp-user-avatar">{str(current_user)[:1].upper()}</div>
              <div><strong>{current_user}</strong><small>{role_text}</small></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(tr("core_modules"))
        gp_nav_button('Workspace', tr("workspace"), 'gp_nav_workspace')
        gp_nav_button('Support', tr("support"), 'gp_nav_support')
        gp_nav_button('Stock', tr("stock"), 'gp_nav_stock')
        gp_nav_button('Logistics', tr("logistics"), 'gp_nav_logistics')

        st.caption("ACCOUNTING" if st.session_state.get("ui_language") == "en" else "المالية والتقارير")
        gp_nav_button('Accounting', tr("accounting"), 'gp_nav_accounting')

        st.caption("DISPLAY" if st.session_state.get("ui_language") == "en" else "الشاشات")
        gp_nav_button('TV_Display', tr("tv"), 'gp_nav_tv')

        st.divider()
        if st.button(tr("logout"), use_container_width=True, key='gp_logout'):
            st.session_state['logged_in_user'] = None
            st.rerun()

# Load only what the selected module needs. This avoids four Google calls on every rerun.
ledger_df = pd.DataFrame(columns=SCHEMA["Ledger"])
stock_df = pd.DataFrame(columns=SCHEMA["Stock"])
hawara_df = pd.DataFrame(columns=SCHEMA["Hawara"])
dispatch_df = pd.DataFrame(columns=SCHEMA["Dispatch"])
current_module = st.session_state['current_module']
module_sources = {
    "Workspace": {"Ledger"},
    "TV_Display": {"Ledger"},
    "Support": {"Ledger", "Stock"},
    "Stock": {"Stock"},
    "Logistics": {"Ledger", "Hawara", "Dispatch"},
    "Accounting": {"Ledger"},
}
needed_sources = module_sources.get(current_module, set())
if needed_sources:
    with golden_loading(tr("loading_data")):
        if "Ledger" in needed_sources:
            ledger_df = get_doctype("Ledger")
        if "Stock" in needed_sources:
            stock_df = get_doctype("Stock")
        if "Hawara" in needed_sources:
            hawara_df = get_doctype("Hawara")
        if "Dispatch" in needed_sources:
            dispatch_df = get_doctype("Dispatch")

stock_list = stock_df['item_name'].dropna().unique().tolist() if not stock_df.empty else []

if st.session_state['current_module'] == 'Workspace':
    gp_render_module_header('Workspace')
    active_count = len(ledger_df[~ledger_df['case_status'].astype(str).eq(CASE_STATUS_CLOSED)]) if not ledger_df.empty else 0
    ready_count = len(ledger_df[ledger_df['status'].str.contains('جاهز', na=False)]) if not ledger_df.empty else 0
    total_rev = float(ledger_df['cost_debit'].sum()) if not ledger_df.empty else 0.0

    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='erp-card gp-kpi-card'><h3>{tr('open_repairs')}</h3><h1>{active_count}</h1></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='erp-card gp-kpi-card'><h3>{tr('ready_tools')}</h3><h1>{ready_count}</h1></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='erp-card gp-kpi-card'><h3>{tr('sales_total')}</h3><h1>${total_rev:,.2f}</h1></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='gp-section-label'>{'وصول سريع' if st.session_state.get('ui_language','ar') == 'ar' else 'Quick access'}</div>", unsafe_allow_html=True)
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button(tr('support'), key='gp_quick_support', use_container_width=True, type='primary'):
            st.session_state['current_module'] = 'Support'; st.rerun()
    with qa2:
        if st.button(tr('stock'), key='gp_quick_stock', use_container_width=True, type='primary'):
            st.session_state['current_module'] = 'Stock'; st.rerun()
    with qa3:
        if st.button(tr('logistics'), key='gp_quick_logistics', use_container_width=True, type='primary'):
            st.session_state['current_module'] = 'Logistics'; st.rerun()
    with qa4:
        if st.button(tr('accounting'), key='gp_quick_accounting', use_container_width=True, type='primary'):
            st.session_state['current_module'] = 'Accounting'; st.rerun()

# ==========================================
# MODULE 2: TV WORKSHOP DISPLAY (KIOSK MODE)
# ==========================================
elif st.session_state['current_module'] == 'TV_Display':

    if is_tv_mode:
        # Smooth auto-scrolling engine (Voice completely removed)
        html_injection = """
        <script>
            let goingDown = true;
            const scrollSpeed = 1;
            const intervalTime = 30;

            let scrollInterval = setInterval(() => {
                if (goingDown) {
                    window.parent.scrollBy(0, scrollSpeed);
                    if ((window.parent.innerHeight + window.parent.scrollY) >= window.parent.document.body.offsetHeight - 5) {
                        goingDown = false;
                        setTimeout(() => {}, 2000);
                    }
                } else {
                    window.parent.scrollBy(0, -scrollSpeed);
                    if (window.parent.scrollY <= 0) {
                        goingDown = true;
                        setTimeout(() => {}, 2000);
                    }
                }
            }, intervalTime);

            setInterval(() => {
                fetch(window.parent.location.href)
                    .then(res => res.text())
                    .then(html => {}).catch(err => {});
            }, 30000);
        </script>
        """
        st.components.v1.html(html_injection, height=0)

    st.markdown("""
        <style>
            .tv-card-urgent { background: #ffe5e5; border-right: 15px solid #e53e3e; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .tv-card-delayed { background: #fffaf0; border-right: 15px solid #dd6b20; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .tv-card-normal { background: #ebf8ff; border-right: 15px solid #3182ce; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .tv-title { font-size: 32px; font-weight: bold; color: #1a202c; margin-bottom: 10px; }
            .tv-details { font-size: 24px; color: #4a5568; }
            .tv-days { font-size: 35px; font-weight: bold; float: left; margin-top: -10px; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; font-size: 60px; margin-bottom: 40px;'>شاشة متابعة الورشة (Live Queue)</h1>", unsafe_allow_html=True)

    if not ledger_df.empty:
        open_jobs = ledger_df[~ledger_df['case_status'].astype(str).eq(CASE_STATUS_CLOSED)]
        waiting_collection_df = ledger_df[ledger_df['collection_status'].isin([COLLECTION_AWAITING, COLLECTION_SPECIAL_AWAITING])] if not ledger_df.empty else pd.DataFrame()
        partner_claim_df = ledger_df[ledger_df['partner_claim_status'].eq('بانتظار مطالبة الشريك')] if not ledger_df.empty else pd.DataFrame()
        special_df = ledger_df[ledger_df['special_case'].astype(str).str.strip() != ''] if not ledger_df.empty else pd.DataFrame()

        display_items = []
        for _, r in open_jobs.iterrows():
            try:
                logged_dt = pd.to_datetime(str(r['date_logged']).split(' ')[0])
                if logged_dt > datetime.now(): logged_dt = datetime.now() - pd.Timedelta(days=2)
                days = (datetime.now() - logged_dt).days
                if days < 0: days = 0
            except:
                days = 0

            is_urgent = "عاجل" in str(r.get('priority', ''))

            display_items.append({
                "days": days,
                "urgent": is_urgent,
                "sid": r['service_id'],
                "tool": r['tool_name'],
                "issue": r['reported_issue'],
                "status": r['status'],
                "remarks": r.get('remarks', ''),
                "collection_status": r.get('collection_status', ''),
                "partner_claim_status": r.get('partner_claim_status', ''),
                "special_case": r.get('special_case', '')
            })

        display_items = sorted(display_items, key=lambda x: (not x['urgent'], -x['days']))

        if display_items:
            for item in display_items:
                if item['urgent']:
                    card_class = "tv-card-urgent"
                    tag = "🔥 عاجل جداً"
                    color = "#e53e3e"
                elif item['days'] >= 3:
                    card_class = "tv-card-delayed"
                    tag = "⚠️ متأخر"
                    color = "#dd6b20"
                else:
                    card_class = "tv-card-normal"
                    tag = "⚙️ قيد العمل"
                    color = "#3182ce"

                st.markdown(f"""
                <div class="{card_class}">
                    <div class="tv-days" style="color: {color};">{item['days']}<br><span style="font-size:16px;">أيام</span></div>
                    <div class="tv-title">{tag} | {item['sid']} - {item['tool']}</div>
                    <div class="tv-details"><b>العطل:</b> {item['issue']} <br> <b>الحالة:</b> {item['status']} <br> <b>الاستلام:</b> {item['collection_status']} <br> <b>ملاحظة خاصة:</b> {item['special_case']} <br> <b>مطالبة الشريك:</b> {item['partner_claim_status']} <br> <b>ملاحظات:</b> {item['remarks']}</div>
                </div>
                """, unsafe_allow_html=True)

                # Interactive Workshop Quick-Update Form
                with st.expander(f"⚡ تحديث سريع للسند ({item['sid']})"):
                    with st.form(f"quick_form_{item['sid']}"):
                        q_action = st.selectbox("الإجراء:", ["تحديث الملاحظات فقط", "إنجاز وجاهز للتسليم (Ready)"], key=f"act_{item['sid']}")
                        q_remark = st.text_input("إضافة ملاحظة ورشة:", value=item['remarks'], key=f"rem_{item['sid']}")

                        if st.form_submit_button("حفظ التحديث (Save)", use_container_width=True):
                            idx = ledger_df.index[ledger_df['service_id'] == item['sid']][0]
                            ledger_df.at[idx, 'remarks'] = q_remark
                            if "إنجاز" in q_action:
                                ledger_df.at[idx, 'document_origin'] = "مبيع خ ص: (جاهز ومفوتر)"
                                ledger_df.at[idx, 'status'] = "جاهز للتسليم (Ready)"
                                ledger_df.at[idx, 'date_resolved'] = datetime.now().strftime("%Y-%m-%d")
                            save_doctype("Ledger", ledger_df)
                            st.success("✅ تم التحديث بنجاح!")
                            st.rerun()

        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("📦 بانتظار تأكيد الاستلام", len(waiting_collection_df))
        with c2: st.metric("💼 مطالبات شركاء معلقة", len(partner_claim_df))
        with c3: st.metric("⚠️ حالات خاصة", len(special_df))
        if not partner_claim_df.empty:
            st.warning("💼 توجد حالات V لم تُسجّل لها خ صيانة بعد — راجع مطالبة الشريك.")
        if not special_df.empty:
            st.info("ℹ️ الحالات الخاصة مثل كفالة/رفض/مكلف/يعمل من المصدر لا تنتظر قبضاً؛ حالات العملاء تنتظر تأكيد الاستلام من الشاشة، وحالات الشريك تغلق تلقائياً.")
        else:
            st.markdown("<h1 style='text-align: center; color: #38a169; margin-top: 100px;'>✅ لا توجد أجهزة قيد الصيانة. الورشة خالية!</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #38a169; margin-top: 100px;'>✅ العمل ممتاز! لا توجد مهام حالياً.</h1>", unsafe_allow_html=True)

# ==========================================
# MODULE 3: SUPPORT & MAINTENANCE
# ==========================================
elif st.session_state['current_module'] == 'Support':
    gp_render_module_header('Support')
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
                        "accessories": accessories, "loaner_item": loaner, "priority": priority, "tool_photo_link": photo_url,
                        "source_account": "", "source_account_g": "", "source_document_count": 1, "document_history": doc_origin,
                        "repair_stage": "قيد المعالجة", "collection_status": COLLECTION_NOT_READY, "special_case": "", "partner_claim_status": "غير منطبق", "partner_claim_amount": 0.0,
                        "case_status": CASE_STATUS_OPEN, "closed_at": "", "closed_by": "", "close_note": ""
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

            is_locked = str(row_data.get('case_status', CASE_STATUS_OPEN)) == CASE_STATUS_CLOSED
            is_warranty = "ضمن" in str(row_data.get('warranty_status', ''))
            is_partner_ticket = str(sel_id).upper().startswith("V")

            if is_locked:
                st.markdown("<div class='locked-card'>", unsafe_allow_html=True)
                st.markdown(f"### 🔒 مستند مغلق (Submitted/Locked)")
                st.write(f"**رقم السند:** {sel_id} | **الزبون:** {row_data['customer_name']}")
                st.write(f"**حالة الملف:** {row_data['status']}")
                st.write(f"**أغلق بواسطة:** {row_data.get('closed_by', 'غير مسجل')} في {row_data.get('closed_at', row_data.get('date_resolved', ''))}")
                if row_data.get('close_note'): st.write(f"**ملاحظة الإغلاق:** {row_data.get('close_note')}")
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
                    doc_options = ["اد خ ص: (استلام للصيانة)", "مبيع خ ص: (جاهز ومفوتر)", "قبض د: (مدفوع ومسلم)", "قبض م: (مدفوع ومسلم)", "خ صيانة: (تحميل على الوكيل)"]
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

                    current_collection = str(row_data.get("collection_status", ""))
                    st.info(f"📄 حالة كشف الأمين: {current_collection or COLLECTION_NOT_READY}")
                    special_options = ["", "يعمل من المصدر", "الزبون رفض الإصلاح", "مكلف", "كفالة", "غير قابل للإصلاح", "لا يوجد عطل"]
                    current_special = str(row_data.get("special_case", ""))
                    try: special_i = special_options.index(current_special)
                    except: special_i = 0
                    new_special = st.selectbox("حالة خاصة (Special Case):", special_options, index=special_i)
                    partner_options = ["غير منطبق", "بانتظار مطالبة الشريك", "تمت مطالبة الشريك / تم التحصيل", "لا مطالبة - حالة خاصة"]
                    current_partner = str(row_data.get("partner_claim_status", "غير منطبق"))
                    try: partner_i = partner_options.index(current_partner)
                    except: partner_i = 0
                    new_partner_claim = st.selectbox("حالة مطالبة الشريك (Partner Claim):", partner_options, index=partner_i)

                    if "قبض" in new_doc:
                        new_collection = COLLECTION_CLOSED
                    elif new_special:
                        new_collection = COLLECTION_SPECIAL_AWAITING
                    elif "مبيع خ ص" in new_doc:
                        new_collection = COLLECTION_AWAITING
                    else:
                        new_collection = current_collection or COLLECTION_NOT_READY

                    new_status = map_document_to_status(new_doc, cost, new_collection, new_special, new_partner_claim, CASE_STATUS_OPEN)
                    c_n1, c_n2 = st.columns(2)
                    with c_n1: notes = st.text_area("ملاحظات الإصلاح (Resolution)", value=str(row_data.get('resolution_notes', '')))
                    with c_n2: remarks_update = st.text_area("تحديثات إضافية (Remarks)", value=str(row_data.get('remarks', '')))

                    if st.form_submit_button("تحديث السجل (Update Document)", use_container_width=True):
                        idx = ledger_df.index[ledger_df['service_id'] == sel_id][0]
                        ledger_df.at[idx, 'cost_debit'] = cost
                        ledger_df.at[idx, 'payment_credit'] = pay
                        ledger_df.at[idx, 'balance'] = cost - pay
                        ledger_df.at[idx, 'resolution_notes'] = notes
                        ledger_df.at[idx, 'remarks'] = remarks_update
                        ledger_df.at[idx, 'document_origin'] = new_doc
                        ledger_df.at[idx, 'status'] = new_status
                        ledger_df.at[idx, 'spare_parts'] = new_spare
                        ledger_df.at[idx, 'collection_status'] = new_collection
                        ledger_df.at[idx, 'special_case'] = new_special
                        ledger_df.at[idx, 'partner_claim_status'] = new_partner_claim
                        ledger_df.at[idx, 'repair_stage'] = 'جاهز للتسليم' if 'مبيع خ ص' in new_doc or 'قبض' in new_doc or new_special else 'قيد المعالجة'
                        save_doctype("Ledger", ledger_df)
                        st.success("✅ تم التحديث بنجاح!")
                        st.rerun()

                # Any S/D case that is genuinely waiting for collection may be closed
                # manually. The closure is preserved only for this repair cycle; a later
                # اد خ ص creates a new cycle and reopens the service ID automatically.
                collection_eligible = (
                    not is_partner_ticket
                    and normalize_doc_string(row_data.get('workflow_state', '')) == WF_WAIT_COLLECTION
                )
                if collection_eligible:
                    st.markdown("### ✅ تأكيد استلام الزبون")
                    st.caption("أغلق الحالة فقط بعد الاستلام الفعلي. إذا عاد الجهاز لاحقاً بسند اد خ ص جديد فسيبدأ دورة صيانة جديدة تلقائياً.")
                    with st.form("close_case_form"):
                        close_note = st.text_input("ملاحظة الإغلاق (اختياري)")
                        if st.form_submit_button("تم الاستلام — إغلاق الحالة", use_container_width=True):
                            idx = ledger_df.index[ledger_df['service_id'] == sel_id][0]
                            closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ledger_df.at[idx, 'case_status'] = CASE_STATUS_CLOSED
                            ledger_df.at[idx, 'workflow_state'] = WF_CLOSED_TV
                            ledger_df.at[idx, 'closed_at'] = closed_at
                            ledger_df.at[idx, 'closed_by'] = current_user
                            ledger_df.at[idx, 'close_note'] = close_note or f"استلام يدوي - {row_data.get('special_case', 'كفالة')}"
                            ledger_df.at[idx, 'collection_status'] = COLLECTION_CLOSED
                            ledger_df.at[idx, 'repair_stage'] = CASE_STATUS_CLOSED
                            ledger_df.at[idx, 'status'] = "مغلق - تم الاستلام (Closed)"
                            ledger_df.at[idx, 'date_resolved'] = closed_at.split(" ")[0]
                            save_doctype("Ledger", ledger_df)
                            st.success("✅ تم إغلاق الحالة نهائياً بعد تأكيد الاستلام.")
                            st.rerun()
                elif not is_partner_ticket:
                    st.info("ℹ️ الإغلاق الآلي يتم عند قبض أو عند فاتورة مبيع صفر. أما الفاتورة غير الصفرية فتنتظر تأكيد الاستلام.")

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
            open_jobs = ledger_df[~ledger_df['case_status'].astype(str).eq(CASE_STATUS_CLOSED)]
            alerts = []
            for _, r in open_jobs.iterrows():
                try:
                    logged_dt = pd.to_datetime(str(r['date_logged']).split(' ')[0])
                    if logged_dt > datetime.now(): logged_dt = datetime.now() - pd.Timedelta(days=2)
                    days = (datetime.now() - logged_dt).days
                    if days < 0: days = 0
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
    gp_render_module_header('Stock')
    st.markdown("<div class='erp-card'>", unsafe_allow_html=True)
    if not stock_df.empty:
        stock_df['quantity'] = pd.to_numeric(stock_df['quantity'], errors='coerce').fillna(0)
        stock_df['price'] = pd.to_numeric(stock_df['price'], errors='coerce').fillna(0.0)
        low_stock = stock_df[stock_df['quantity'] <= 2]
        if not low_stock.empty:
            st.error(tr("stock_reorder", count=len(low_stock)))

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            tr("stock_export"),
            data=convert_df_to_excel(stock_df) if not stock_df.empty else b"",
            file_name="Stock_Master.xlsx",
            use_container_width=True,
        )
    with c2:
        with st.expander(tr("stock_import_expander")):
            uploaded_stock = st.file_uploader(tr("stock_upload"), type=["xlsx", "xls", "csv"], key="stock_report_upload")
            if uploaded_stock and st.button(tr("stock_import"), key="stock_report_import"):
                try:
                    with golden_loading(tr("loading_data")):
                        raw = read_stock_report(uploaded_stock)
                        merged_stock, import_meta = normalize_stock_report(raw, stock_df)
                        save_doctype("Stock", merged_stock[STOCK_COLUMNS])
                    st.success(tr("stock_imported", count=import_meta["imported_count"]))
                    st.rerun()
                except Exception as exc:
                    st.error(f"{tr('stock_import_error')}: {exc}")

    if not stock_df.empty:
        edited_stock = st.data_editor(stock_df[STOCK_COLUMNS], num_rows="dynamic", use_container_width=True)
        if st.button(tr("stock_save"), use_container_width=True):
            try:
                save_doctype("Stock", edited_stock[STOCK_COLUMNS])
                st.success(tr("stock_saved"))
                st.rerun()
            except Exception as exc:
                st.error(f"{tr('stock_import_error')}: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MODULE 5: LOGISTICS (HAWARA & DISPATCH)
# ==========================================
elif st.session_state['current_module'] == 'Logistics':
    gp_render_module_header('Logistics')
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
                ready_list = ledger_df[ledger_df['status'].str.contains('جاهز', na=False) & ~ledger_df['case_status'].astype(str).eq(CASE_STATUS_CLOSED)] if not ledger_df.empty else pd.DataFrame()
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
    gp_render_module_header('Accounting')

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
                with golden_loading("Processing Ameen repair ledger..." if st.session_state.get("ui_language") == "en" else "جارٍ معالجة كشف الأمين..."):
                    raw_excel = pd.read_excel(uploaded_legacy, sheet_name=0, header=0)
                    imported_df = normalize_ameen_dataframe(raw_excel)

                    if imported_df.empty:
                        st.error("❌ لم يتم العثور على سجلات صيانة صالحة في أعمدة A:L.")
                    else:
                        # Merge by service_id so repeated Ameen lines become one repair case.
                        existing = ledger_df.copy()
                        if not existing.empty:
                            existing = apply_workflow_columns(existing)
                            imported_df = preserve_manual_closures(imported_df, existing)
                            existing = existing[~existing["service_id"].astype(str).isin(imported_df["service_id"].astype(str))]
                        merged = pd.concat([existing, imported_df], ignore_index=True)
                        merged = apply_workflow_columns(merged)
                        save_doctype("Ledger", merged)

                        st.success(f"✅ تم استيراد {len(imported_df)} حالات صيانة من كشف الأمين.")
                        c1, c2, c3, c4, c5, c6 = st.columns(6)
                        c1.metric("قيد المعالجة", int((imported_df["workflow_state"] == WF_IN_REPAIR).sum()))
                        c2.metric("بانتظار الاستلام", int((imported_df["workflow_state"] == WF_WAIT_COLLECTION).sum()))
                        c3.metric("مطالبة شريك", int((imported_df["workflow_state"] == WF_WAIT_PARTNER).sum()))
                        c4.metric("مغلق - فاتورة صفر", int((imported_df["workflow_state"] == WF_CLOSED_ZERO).sum()))
                        c5.metric("مغلق - استلام", int((imported_df["workflow_state"] == WF_CLOSED_COLLECTED).sum()))
                        c6.metric("مغلق - تسوية شريك", int((imported_df["workflow_state"] == WF_CLOSED_PARTNER).sum()))
                        st.dataframe(imported_df[["service_id", "cycle_no", "cycle_key", "cycle_started_at", "cycle_last_event_date", "cycle_last_event", "workflow_state", "financial_status", "cycle_sales_total", "cycle_payment_total", "collection_status", "case_status", "closed_at", "closed_by", "close_note", "special_case", "partner_claim_status", "cycle_history"]], use_container_width=True)
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
