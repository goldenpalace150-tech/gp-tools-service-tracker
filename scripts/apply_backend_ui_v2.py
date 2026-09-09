from pathlib import Path

path = Path('tools_tracker.py')
src = path.read_text(encoding='utf-8')

if 'GP_BACKEND_UI_V3' in src:
    print('Backend UI V3 already applied')
    raise SystemExit(0)

insert_marker = "# ==========================================\n# DATABASE ORM (DocType Engine)\n# =========================================="
if insert_marker not in src:
    raise SystemExit('Database ORM marker not found')

ui_v3 = r'''
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


'''

src = src.replace(insert_marker, ui_v3 + insert_marker, 1)

replacements = {
    "<div class='erp-card'><h3>{tr('open_repairs')}</h3>": "<div class='erp-card gp-kpi-card'><h3>{tr('open_repairs')}</h3>",
    "<div class='erp-card'><h3>{tr('ready_tools')}</h3>": "<div class='erp-card gp-kpi-card'><h3>{tr('ready_tools')}</h3>",
    "<div class='erp-card'><h3>{tr('sales_total')}</h3>": "<div class='erp-card gp-kpi-card'><h3>{tr('sales_total')}</h3>",
    "st.button(tr('support'), key='gp_quick_support', use_container_width=True)": "st.button(tr('support'), key='gp_quick_support', use_container_width=True, type='primary')",
    "st.button(tr('stock'), key='gp_quick_stock', use_container_width=True)": "st.button(tr('stock'), key='gp_quick_stock', use_container_width=True, type='primary')",
    "st.button(tr('logistics'), key='gp_quick_logistics', use_container_width=True)": "st.button(tr('logistics'), key='gp_quick_logistics', use_container_width=True, type='primary')",
    "st.button(tr('accounting'), key='gp_quick_accounting', use_container_width=True)": "st.button(tr('accounting'), key='gp_quick_accounting', use_container_width=True, type='primary')",
}

for old, new in replacements.items():
    if old not in src:
        raise SystemExit(f'Expected UI target not found: {old[:80]}')
    src = src.replace(old, new, 1)

# Guardrail: this script is presentation-only and must leave workflow symbols present.
required = [
    'GP_BACKEND_UI_V2', 'WF_WAITING', 'WF_IN_REPAIR', 'WF_WAIT_COLLECTION',
    'WF_WAIT_PARTNER', 'WF_CLOSED_ZERO', 'WF_CLOSED_COLLECTED',
    'WF_CLOSED_PARTNER', 'WF_CLOSED_TV', 'preserve_manual_closures',
    'apply_workflow_columns', 'save_doctype', 'get_doctype', 'GSheetsConnection'
]
missing = [item for item in required if item not in src]
if missing:
    raise SystemExit('Core guardrail failed: ' + str(missing))

compile(src, str(path), 'exec')
path.write_text(src, encoding='utf-8')
print('Backend UI V3 applied and Python syntax validated')
