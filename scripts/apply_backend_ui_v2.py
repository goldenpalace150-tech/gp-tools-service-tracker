from pathlib import Path

path = Path('tools_tracker.py')
src = path.read_text(encoding='utf-8')

if 'GP_BACKEND_UI_V2' in src:
    print('Backend UI V2 already applied')
    raise SystemExit(0)

insert_marker = "# ==========================================\n# DATABASE ORM (DocType Engine)\n# =========================================="
if insert_marker not in src:
    raise SystemExit('Database ORM marker not found')

ui_block = r'''
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


'''

src = src.replace(insert_marker, ui_block + insert_marker, 1)

# Login: cleaner centred shell, same credential logic.
login_start = src.find("if st.session_state['logged_in_user'] is None:")
login_end_marker = "\n\ncurrent_user = st.session_state['logged_in_user']"
login_end = src.find(login_end_marker, login_start)
if login_start < 0 or login_end < 0:
    raise SystemExit('Login block markers not found')
new_login = r'''if st.session_state['logged_in_user'] is None:
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
    st.stop()'''
src = src[:login_start] + new_login + src[login_end:]

# Sidebar: brand + user identity + clear active module state.
side_start = src.find("if not is_tv_mode:\n    with st.sidebar:", login_start)
side_end_marker = "\n# Load only what the selected module needs. This avoids four Google calls on every rerun."
side_end = src.find(side_end_marker, side_start)
if side_start < 0 or side_end < 0:
    raise SystemExit('Sidebar block markers not found')
new_sidebar = r'''if not is_tv_mode:
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
'''
src = src[:side_start] + new_sidebar + src[side_end:]

# Replace plain module titles with the shared branded header.
replacements = {
    "    hero_text = \"لوحة تشغيل سريعة وواضحة لكل مهام القصر الذهبي\" if st.session_state.get(\"ui_language\") == \"ar\" else \"A faster, clearer operating view for Golden Palace\"\n    st.markdown(f\"\"\"<section class=\"gp-app-hero\"><h1>🏢 {tr('workspace_title')}</h1><p>{hero_text}</p><span class=\"gp-app-chip\">{tr('user')}: {current_user}</span></section>\"\"\", unsafe_allow_html=True)": "    gp_render_module_header('Workspace')",
    "    st.title(\"🛠️ وحدة الدعم والصيانة (Support Desk)\")": "    gp_render_module_header('Support')",
    "    st.title(tr(\"stock_title\"))": "    gp_render_module_header('Stock')",
    "    st.title(\"🚚 وحدة الشحن واللوجستيات (Logistics)\")": "    gp_render_module_header('Logistics')",
    "    st.title(\"💰 الإدارة المالية والمحاسبة (Accounting)\")": "    gp_render_module_header('Accounting')",
}
for old, new in replacements.items():
    if old not in src:
        raise SystemExit(f'Expected UI target not found: {old[:70]}')
    src = src.replace(old, new, 1)

# Add quick-access actions under the workspace KPIs without changing data logic.
workspace_anchor = "    with col3: st.markdown(f\"<div class='erp-card'><h3>{tr('sales_total')}</h3><h1>${total_rev:,.2f}</h1></div>\", unsafe_allow_html=True)"
if workspace_anchor not in src:
    raise SystemExit('Workspace KPI anchor not found')
quick_actions = workspace_anchor + r'''

    st.markdown(f"<div class='gp-section-label'>{'وصول سريع' if st.session_state.get('ui_language','ar') == 'ar' else 'Quick access'}</div>", unsafe_allow_html=True)
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button(tr('support'), key='gp_quick_support', use_container_width=True):
            st.session_state['current_module'] = 'Support'; st.rerun()
    with qa2:
        if st.button(tr('stock'), key='gp_quick_stock', use_container_width=True):
            st.session_state['current_module'] = 'Stock'; st.rerun()
    with qa3:
        if st.button(tr('logistics'), key='gp_quick_logistics', use_container_width=True):
            st.session_state['current_module'] = 'Logistics'; st.rerun()
    with qa4:
        if st.button(tr('accounting'), key='gp_quick_accounting', use_container_width=True):
            st.session_state['current_module'] = 'Accounting'; st.rerun()'''
src = src.replace(workspace_anchor, quick_actions, 1)

path.write_text(src, encoding='utf-8')
print('Backend UI V2 applied successfully')
