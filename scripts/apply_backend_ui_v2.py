from pathlib import Path

TOOLS = Path('tools_tracker.py')
FLASK = Path('flask_app.py')
TV = Path('templates/tv.html')

tools = TOOLS.read_text(encoding='utf-8')
flask = FLASK.read_text(encoding='utf-8')
tv = TV.read_text(encoding='utf-8')

if 'GP_FOLLOWUP_CENTER_V1' in tools:
    print('Unified Follow-Up Center already applied')
    raise SystemExit(0)


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'Missing patch target: {label}')
    return text.replace(old, new, 1)

# ------------------------------------------------------------------
# STREAMLIT: unified Follow-Up Center
# ------------------------------------------------------------------
tools = replace_once(
    tools,
    "    'Accounting': {\n        'icon': '💰',",
    "    'FollowUp': {\n        'icon': '📌',\n        'ar_title': 'مركز المتابعة', 'en_title': 'Follow-Up Center',\n        'ar_desc': 'مكان واحد للتأخير وقطع الغيار والاستفسارات، مع مسؤول واضح وخطوة وموعد متابعة إلزامي.',\n        'en_desc': 'One queue for delays, spare parts, and inquiries with clear ownership, next action, and follow-up date.',\n    },\n    'Accounting': {\n        'icon': '💰',",
    'module metadata',
)

tools = replace_once(
    tools,
    '    "Dispatch": ["dispatch_id", "service_id", "customer_name", "courier", "delivery_note", "document_link", "date"]\n}',
    '    "Dispatch": ["dispatch_id", "service_id", "customer_name", "courier", "delivery_note", "document_link", "date"],\n    "FollowUp": ["followup_id", "type", "related_id", "title", "owner", "waiting_on", "priority", "status", "created_at", "next_followup", "last_update", "next_action", "history", "source", "closed_at", "closed_by"]\n}',
    'FollowUp schema',
)

helper_marker = "# ==========================================\n# AUTHENTICATION & WORKSPACE ROUTING\n# =========================================="
followup_helpers = r'''
# GP_FOLLOWUP_CENTER_V1
FOLLOWUP_OPEN_STATUSES = {"Open", "Waiting", "Escalated", "مفتوح", "انتظار", "مصعّد"}
FOLLOWUP_CLOSED_STATUSES = {"Done", "Closed", "مغلق", "منجز"}
FOLLOWUP_TYPES = ["Delay", "Spare Part", "Customer Inquiry", "Supplier Inquiry", "Internal"]
FOLLOWUP_PRIORITIES = ["Normal", "Important", "Urgent"]
FOLLOWUP_STATUSES = ["Open", "Waiting", "Escalated", "Done"]


def normalize_followup_dataframe(df):
    work = df.copy() if df is not None else pd.DataFrame(columns=SCHEMA["FollowUp"])
    for col in SCHEMA["FollowUp"]:
        if col not in work.columns:
            work[col] = ""
        work[col] = work[col].fillna("").astype(str).replace({"nan": "", "None": ""})
    work = work[SCHEMA["FollowUp"]].copy()
    work = work[work["followup_id"].str.strip().ne("")].copy()
    return work.reset_index(drop=True)


def _new_followup_id(existing):
    today = datetime.now().strftime("%Y%m%d")
    existing_ids = set(existing.get("followup_id", pd.Series(dtype=str)).astype(str)) if existing is not None else set()
    seq = 1
    while f"F{today}-{seq:03d}" in existing_ids:
        seq += 1
    return f"F{today}-{seq:03d}"


def _followup_history_line(user, action):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"{stamp} · {user} · {normalize_doc_string(action)}"


def _followup_date_state(value):
    date = pd.to_datetime(value, errors="coerce")
    if pd.isna(date):
        return "unscheduled"
    today = pd.Timestamp(datetime.now().date())
    date = pd.Timestamp(date.date())
    if date < today:
        return "overdue"
    if date == today:
        return "today"
    return "future"


def build_missing_operational_followups(ledger, followups, default_owner=""):
    """Suggest only objective blockers from the repair ledger; never duplicate an open tracker item."""
    existing = normalize_followup_dataframe(followups)
    open_existing = existing[~existing["status"].isin(FOLLOWUP_CLOSED_STATUSES)] if not existing.empty else existing
    keys = set(
        zip(
            open_existing["type"].astype(str),
            open_existing["related_id"].astype(str),
            open_existing["source"].astype(str),
        )
    )
    rows = []
    if ledger is None or ledger.empty:
        return pd.DataFrame(columns=SCHEMA["FollowUp"])
    today = datetime.now().strftime("%Y-%m-%d")
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for _, row in ledger.iterrows():
        sid = normalize_doc_string(row.get("service_id", ""))
        if not sid or normalize_doc_string(row.get("case_status", "")) == CASE_STATUS_CLOSED:
            continue
        owner = normalize_doc_string(row.get("technician", "")) or default_owner
        try:
            started = pd.to_datetime(row.get("date_logged", ""), errors="coerce")
            days = max((pd.Timestamp(datetime.now().date()) - pd.Timestamp(started.date())).days, 0) if pd.notna(started) else 0
        except Exception:
            days = 0
        spare = normalize_doc_string(row.get("spare_parts", ""))
        urgent = "عاجل" in normalize_doc_string(row.get("priority", "")) or days >= 6
        candidates = []
        if days >= 3:
            candidates.append((
                "Delay", f"Delayed repair · {sid}", "Workshop / Technician",
                "Review blocker and move the repair to the next concrete step",
                "Urgent" if urgent else "Important", "AUTO_DELAY"
            ))
        if "بانتظار" in spare or "waiting" in spare.lower():
            candidates.append((
                "Spare Part", f"Spare part blocker · {sid}", "Supplier / Stock",
                f"Confirm availability or ETA for: {spare}",
                "Urgent" if urgent else "Important", "AUTO_SPARE"
            ))
        for item_type, title, waiting_on, next_action, priority, source in candidates:
            key = (item_type, sid, source)
            if key in keys:
                continue
            new_id = _new_followup_id(pd.concat([existing, pd.DataFrame(rows)], ignore_index=True))
            rows.append({
                "followup_id": new_id,
                "type": item_type,
                "related_id": sid,
                "title": title,
                "owner": owner,
                "waiting_on": waiting_on,
                "priority": priority,
                "status": "Open",
                "created_at": now_text,
                "next_followup": today,
                "last_update": now_text,
                "next_action": next_action,
                "history": _followup_history_line("System", f"Auto-created from {source}"),
                "source": source,
                "closed_at": "",
                "closed_by": "",
            })
            keys.add(key)
    return pd.DataFrame(rows, columns=SCHEMA["FollowUp"])


'''
tools = replace_once(tools, helper_marker, followup_helpers + helper_marker, 'follow-up helpers')

tools = replace_once(
    tools,
    "        gp_nav_button('Support', tr(\"support\"), 'gp_nav_support')\n        gp_nav_button('Stock', tr(\"stock\"), 'gp_nav_stock')",
    "        gp_nav_button('Support', tr(\"support\"), 'gp_nav_support')\n        gp_nav_button('FollowUp', '📌 مركز المتابعة' if st.session_state.get('ui_language') == 'ar' else '📌 Follow-Up Center', 'gp_nav_followup')\n        gp_nav_button('Stock', tr(\"stock\"), 'gp_nav_stock')",
    'sidebar follow-up nav',
)

tools = replace_once(
    tools,
    'dispatch_df = pd.DataFrame(columns=SCHEMA["Dispatch"])\ncurrent_module = st.session_state[\'current_module\']',
    'dispatch_df = pd.DataFrame(columns=SCHEMA["Dispatch"])\nfollowup_df = pd.DataFrame(columns=SCHEMA["FollowUp"])\ncurrent_module = st.session_state[\'current_module\']',
    'follow-up dataframe',
)

tools = replace_once(
    tools,
    '    "Support": {"Ledger", "Stock"},\n    "Stock": {"Stock"},',
    '    "Support": {"Ledger", "Stock"},\n    "FollowUp": {"Ledger", "FollowUp"},\n    "Stock": {"Stock"},',
    'module sources',
)

tools = replace_once(
    tools,
    '        if "Dispatch" in needed_sources:\n            dispatch_df = get_doctype("Dispatch")',
    '        if "Dispatch" in needed_sources:\n            dispatch_df = get_doctype("Dispatch")\n        if "FollowUp" in needed_sources:\n            followup_df = normalize_followup_dataframe(get_doctype("FollowUp"))',
    'load FollowUp',
)

stock_marker = "# ==========================================\n# MODULE 4: STOCK & INVENTORY\n# ==========================================\nelif st.session_state['current_module'] == 'Stock':"
followup_module = r'''# ==========================================
# MODULE: UNIFIED FOLLOW-UP CENTER
# ==========================================
elif st.session_state['current_module'] == 'FollowUp':
    gp_render_module_header('FollowUp')
    followup_df = normalize_followup_dataframe(followup_df)

    # Objective repair blockers are synced automatically when this module opens.
    auto_rows = build_missing_operational_followups(ledger_df, followup_df, current_user)
    if not auto_rows.empty:
        followup_df = normalize_followup_dataframe(pd.concat([followup_df, auto_rows], ignore_index=True))
        save_doctype("FollowUp", followup_df)

    open_mask = ~followup_df["status"].isin(FOLLOWUP_CLOSED_STATUSES) if not followup_df.empty else pd.Series(dtype=bool)
    open_df = followup_df[open_mask].copy() if not followup_df.empty else followup_df.copy()
    if not open_df.empty:
        open_df["_date_state"] = open_df["next_followup"].apply(_followup_date_state)
    else:
        open_df["_date_state"] = pd.Series(dtype=str)

    overdue_count = int((open_df["_date_state"] == "overdue").sum()) if not open_df.empty else 0
    today_count = int((open_df["_date_state"] == "today").sum()) if not open_df.empty else 0
    spare_count = int(open_df["type"].eq("Spare Part").sum()) if not open_df.empty else 0
    inquiry_count = int(open_df["type"].isin(["Customer Inquiry", "Supplier Inquiry"]).sum()) if not open_df.empty else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔴 متأخر / Overdue", overdue_count)
    m2.metric("🟠 اليوم / Due Today", today_count)
    m3.metric("🟡 قطع غيار / Spare Parts", spare_count)
    m4.metric("🔵 استفسارات / Inquiries", inquiry_count)
    m5.metric("📌 مفتوح / Open", len(open_df))

    create_tab, queue_tab, update_tab = st.tabs([
        "➕ متابعة جديدة / New Follow-Up",
        "📋 قائمة المتابعة / Follow-Up Queue",
        "✏️ تحديث وإغلاق / Update & Close",
    ])

    with create_tab:
        with st.form("followup_create_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                f_type = st.selectbox("النوع / Type", FOLLOWUP_TYPES)
                f_related = st.text_input("رقم مرتبط / Related ID", placeholder="S155 / Order / Customer")
            with c2:
                f_owner = st.text_input("المسؤول / Owner", value=current_user)
                f_waiting = st.text_input("بانتظار / Waiting On", placeholder="Supplier / Technician / Customer")
            with c3:
                f_priority = st.selectbox("الأولوية / Priority", FOLLOWUP_PRIORITIES, index=0)
                f_date = st.date_input("موعد المتابعة القادم / Next Follow-Up")
            f_title = st.text_input("الموضوع / Description")
            f_action = st.text_area("الخطوة القادمة / Next Action", placeholder="Exactly what must happen next")
            if st.form_submit_button("إنشاء المتابعة / Create Follow-Up", use_container_width=True, type="primary"):
                if not f_title.strip() or not f_owner.strip() or not f_action.strip():
                    st.error("الموضوع والمسؤول والخطوة القادمة مطلوبة. / Description, owner, and next action are required.")
                else:
                    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_id = _new_followup_id(followup_df)
                    row = {
                        "followup_id": new_id, "type": f_type, "related_id": f_related.strip(), "title": f_title.strip(),
                        "owner": f_owner.strip(), "waiting_on": f_waiting.strip(), "priority": f_priority, "status": "Open",
                        "created_at": now_text, "next_followup": str(f_date), "last_update": now_text,
                        "next_action": f_action.strip(), "history": _followup_history_line(current_user, f"Created · {f_action.strip()}"),
                        "source": "MANUAL", "closed_at": "", "closed_by": "",
                    }
                    save_doctype("FollowUp", pd.concat([followup_df, pd.DataFrame([row])], ignore_index=True))
                    st.success(f"✅ تم إنشاء المتابعة {new_id}")
                    st.rerun()

    with queue_tab:
        if open_df.empty:
            st.success("✅ لا توجد متابعات مفتوحة حالياً. / No open follow-ups.")
        else:
            type_options = sorted(open_df["type"].dropna().unique().tolist())
            c1, c2, c3 = st.columns(3)
            with c1:
                selected_types = st.multiselect("النوع / Type", type_options, default=type_options)
            with c2:
                owners = sorted([x for x in open_df["owner"].dropna().unique().tolist() if str(x).strip()])
                selected_owners = st.multiselect("المسؤول / Owner", owners, default=owners)
            with c3:
                timing = st.selectbox("الموعد / Timing", ["All", "Overdue", "Due Today", "Future", "Unscheduled"])
            view = open_df[open_df["type"].isin(selected_types)].copy()
            if owners:
                view = view[view["owner"].isin(selected_owners)]
            state_map = {"Overdue":"overdue", "Due Today":"today", "Future":"future", "Unscheduled":"unscheduled"}
            if timing in state_map:
                view = view[view["_date_state"].eq(state_map[timing])]
            state_rank = {"overdue":0, "today":1, "unscheduled":2, "future":3}
            priority_rank = {"Urgent":0, "Important":1, "Normal":2}
            view["_state_rank"] = view["_date_state"].map(state_rank).fillna(9)
            view["_priority_rank"] = view["priority"].map(priority_rank).fillna(9)
            view = view.sort_values(["_state_rank", "_priority_rank", "next_followup", "created_at"], kind="stable")
            display_cols = ["followup_id", "type", "related_id", "title", "owner", "waiting_on", "priority", "status", "next_followup", "last_update", "next_action"]
            st.dataframe(view[display_cols], use_container_width=True, hide_index=True)

    with update_tab:
        if open_df.empty:
            st.info("لا توجد متابعة مفتوحة للتحديث. / No open follow-up to update.")
        else:
            option_map = {f"{r['followup_id']} · {r['type']} · {r['related_id']} · {r['title']}": r['followup_id'] for _, r in open_df.iterrows()}
            selected_id = option_map[st.selectbox("اختر المتابعة / Select Follow-Up", list(option_map.keys()))]
            selected = followup_df[followup_df["followup_id"].eq(selected_id)].iloc[0]
            with st.form("followup_update_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    u_owner = st.text_input("المسؤول / Owner", value=selected["owner"])
                    u_waiting = st.text_input("بانتظار / Waiting On", value=selected["waiting_on"])
                with c2:
                    try: p_idx = FOLLOWUP_PRIORITIES.index(selected["priority"])
                    except Exception: p_idx = 0
                    u_priority = st.selectbox("الأولوية / Priority", FOLLOWUP_PRIORITIES, index=p_idx)
                    try: s_idx = FOLLOWUP_STATUSES.index(selected["status"])
                    except Exception: s_idx = 0
                    u_status = st.selectbox("الحالة / Status", FOLLOWUP_STATUSES, index=s_idx)
                with c3:
                    parsed_date = pd.to_datetime(selected["next_followup"], errors="coerce")
                    default_date = parsed_date.date() if pd.notna(parsed_date) else datetime.now().date()
                    u_date = st.date_input("المتابعة القادمة / Next Follow-Up", value=default_date)
                u_action = st.text_area("الخطوة القادمة / Next Action", value=selected["next_action"])
                u_note = st.text_area("تحديث اليوم / Update Note", placeholder="What happened since the last follow-up?")
                if st.form_submit_button("حفظ التحديث / Save Update", use_container_width=True, type="primary"):
                    idx = followup_df.index[followup_df["followup_id"].eq(selected_id)][0]
                    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    followup_df.at[idx, "owner"] = u_owner.strip()
                    followup_df.at[idx, "waiting_on"] = u_waiting.strip()
                    followup_df.at[idx, "priority"] = u_priority
                    followup_df.at[idx, "status"] = u_status
                    followup_df.at[idx, "next_followup"] = str(u_date)
                    followup_df.at[idx, "next_action"] = u_action.strip()
                    followup_df.at[idx, "last_update"] = now_text
                    note = u_note.strip() or f"Status={u_status}; next action={u_action.strip()}"
                    old_history = normalize_doc_string(followup_df.at[idx, "history"])
                    followup_df.at[idx, "history"] = " | ".join(x for x in [old_history, _followup_history_line(current_user, note)] if x)
                    if u_status == "Done":
                        followup_df.at[idx, "closed_at"] = now_text
                        followup_df.at[idx, "closed_by"] = current_user
                    save_doctype("FollowUp", followup_df)
                    st.success("✅ تم تحديث المتابعة.")
                    st.rerun()

'''
tools = replace_once(tools, stock_marker, followup_module + stock_marker, 'FollowUp module')

# ------------------------------------------------------------------
# FLASK: optional FollowUp worksheet + TV payload
# ------------------------------------------------------------------
flask = replace_once(flask, 'remarks_sheet = None\nmain_sheet = None\nspreadsheet_obj = None', 'remarks_sheet = None\nmain_sheet = None\nfollowup_sheet = None\nspreadsheet_obj = None', 'followup global')
flask = replace_once(flask, '    global remarks_sheet, main_sheet, spreadsheet_obj', '    global remarks_sheet, main_sheet, followup_sheet, spreadsheet_obj', 'followup init global')
flask = replace_once(flask, '    remarks_sheet = None\n    main_sheet = None\n    spreadsheet_obj = None', '    remarks_sheet = None\n    main_sheet = None\n    followup_sheet = None\n    spreadsheet_obj = None', 'followup reset')

followup_lookup_target = '''        if main_sheet is None:\n            LAST_WRITE_ERROR = "Ledger/Main worksheet was not found."'''
followup_lookup_new = '''        # FollowUp is optional so TV/collection writes remain available before the new sheet exists.\n        try:\n            followup_sheet = spreadsheet_obj.worksheet("FollowUp")\n        except Exception:\n            followup_sheet = None\n\n        if main_sheet is None:\n            LAST_WRITE_ERROR = "Ledger/Main worksheet was not found."'''
flask = replace_once(flask, followup_lookup_target, followup_lookup_new, 'FollowUp sheet lookup')

flask_followup_marker = "# ==========================================================\n# ENCOURAGING ARABIC ANNOUNCEMENT\n# =========================================================="
flask_followup_code = r'''
# GP_FOLLOWUP_TV_API_V1
FOLLOWUP_CLOSED_STATUSES = {"Done", "Closed", "مغلق", "منجز"}


def get_tv_followups():
    """Read structured FollowUp items from the same editable spreadsheet when available."""
    global followup_sheet
    try:
        if followup_sheet is None:
            maybe_reconnect_google_sheets(force=True)
            if spreadsheet_obj is not None and followup_sheet is None:
                try:
                    followup_sheet = spreadsheet_obj.worksheet("FollowUp")
                except Exception:
                    return []
        if followup_sheet is None:
            return []
        df = dataframe_from_worksheet(followup_sheet).dropna(how="all")
        if df.empty or "followup_id" not in df.columns:
            return []
        defaults = {
            "type":"", "related_id":"", "title":"", "owner":"", "waiting_on":"", "priority":"Normal",
            "status":"Open", "created_at":"", "next_followup":"", "last_update":"", "next_action":"",
            "history":"", "source":"", "closed_at":"", "closed_by":"",
        }
        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default
        records = []
        today = pd.Timestamp(datetime.now().date())
        for _, row in df.iterrows():
            status = normalize_doc_string(row.get("status", "")) or "Open"
            if status in FOLLOWUP_CLOSED_STATUSES:
                continue
            due_raw = normalize_doc_string(row.get("next_followup", ""))
            due = pd.to_datetime(due_raw, errors="coerce")
            timing = "unscheduled"
            days_overdue = 0
            if pd.notna(due):
                due_day = pd.Timestamp(due.date())
                if due_day < today:
                    timing = "overdue"
                    days_overdue = int((today - due_day).days)
                elif due_day == today:
                    timing = "today"
                else:
                    timing = "future"
            records.append({
                "followup_id": normalize_doc_string(row.get("followup_id", "")),
                "type": normalize_doc_string(row.get("type", "")),
                "related_id": normalize_doc_string(row.get("related_id", "")),
                "title": normalize_doc_string(row.get("title", "")),
                "owner": normalize_doc_string(row.get("owner", "")),
                "waiting_on": normalize_doc_string(row.get("waiting_on", "")),
                "priority": normalize_doc_string(row.get("priority", "")) or "Normal",
                "status": status,
                "created_at": normalize_doc_string(row.get("created_at", "")),
                "next_followup": due_raw,
                "last_update": normalize_doc_string(row.get("last_update", "")),
                "next_action": normalize_doc_string(row.get("next_action", "")),
                "history": normalize_doc_string(row.get("history", "")),
                "source": normalize_doc_string(row.get("source", "")),
                "timing": timing,
                "days_overdue": days_overdue,
            })
        priority_rank = {"Urgent":0, "Important":1, "Normal":2}
        timing_rank = {"overdue":0, "today":1, "unscheduled":2, "future":3}
        records.sort(key=lambda x: (timing_rank.get(x["timing"], 9), priority_rank.get(x["priority"], 9), x["next_followup"], x["followup_id"]))
        return records
    except Exception as exc:
        print("FollowUp TV read error:", repr(exc))
        return []


'''
flask = replace_once(flask, flask_followup_marker, flask_followup_code + flask_followup_marker, 'TV follow-up API helper')

empty_payload_target = '        "special_count": 0,\n        "progress_list": [],'
empty_payload_new = '        "special_count": 0,\n        "followup_open_count": 0,\n        "followup_overdue_count": 0,\n        "followup_due_today_count": 0,\n        "followup_spare_parts_count": 0,\n        "followup_inquiry_count": 0,\n        "followup_list": [],\n        "followup_overdue_list": [],\n        "followup_due_today_list": [],\n        "followup_spare_parts_list": [],\n        "followup_inquiry_list": [],\n        "progress_list": [],'
flask = replace_once(flask, empty_payload_target, empty_payload_new, 'empty follow-up payload')

build_target = 'def build_tv_api_payload():\n    records, _ = get_tv_queue(include_remarks=False)\n    groups = separate_jobs(records)\n\n    data = {'
build_new = 'def build_tv_api_payload():\n    records, _ = get_tv_queue(include_remarks=False)\n    groups = separate_jobs(records)\n    followups = get_tv_followups()\n    followup_overdue = [x for x in followups if x.get("timing") == "overdue"]\n    followup_today = [x for x in followups if x.get("timing") == "today"]\n    followup_spares = [x for x in followups if x.get("type") == "Spare Part"]\n    followup_inquiries = [x for x in followups if x.get("type") in {"Customer Inquiry", "Supplier Inquiry"}]\n\n    data = {'
flask = replace_once(flask, build_target, build_new, 'build follow-up payload')

payload_insert_target = '        "special_count": len(groups["special"]),\n        "progress_list": groups["progress"],'
payload_insert_new = '        "special_count": len(groups["special"]),\n        "followup_open_count": len(followups),\n        "followup_overdue_count": len(followup_overdue),\n        "followup_due_today_count": len(followup_today),\n        "followup_spare_parts_count": len(followup_spares),\n        "followup_inquiry_count": len(followup_inquiries),\n        "followup_list": followups,\n        "followup_overdue_list": followup_overdue,\n        "followup_due_today_list": followup_today,\n        "followup_spare_parts_list": followup_spares,\n        "followup_inquiry_list": followup_inquiries,\n        "progress_list": groups["progress"],'
flask = replace_once(flask, payload_insert_target, payload_insert_new, 'follow-up payload fields')

# ------------------------------------------------------------------
# TV HTML: compact follow-up strip + detail lists
# ------------------------------------------------------------------
style_close = '    </style>\n\n    <!-- GP_UI_REFRESH_2026_09_08 -->'
tv_followup_css = r'''    /* GP_FOLLOWUP_TV_UI_V1 */
    .followup-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:8px 0;flex:0 0 auto;direction:ltr}
    .followup-mini{border:1px solid #315472;border-radius:14px;background:linear-gradient(135deg,#0b2238,#102f4b);color:#fff;min-height:66px;padding:8px 13px;display:flex;align-items:center;justify-content:space-between;gap:10px;text-align:left;box-shadow:0 6px 16px rgba(0,0,0,.14)}
    body.lang-ar .followup-mini{direction:rtl;text-align:right}
    .followup-mini span{font-weight:850;font-size:clamp(12px,.9vw,16px)}
    .followup-mini b{font-size:clamp(27px,2vw,38px);line-height:1;color:#f4bd2d}
    .followup-mini.overdue{border-color:#a83b42}.followup-mini.overdue b{color:#ff7078}
    .followup-mini.today{border-color:#9a6a19}.followup-mini.today b{color:#ffc553}
    .followup-mini.spares{border-color:#917628}.followup-mini.inquiries{border-color:#316c96}
    .followup-row{background:#0b2238;border:1px solid #294b69;border-radius:15px;padding:14px 16px;display:grid;grid-template-columns:130px 150px minmax(200px,1.4fr) 150px 170px minmax(210px,1fr);gap:12px;align-items:center;color:#f8fafc}
    .followup-row small{display:block;color:#aebfd0;font-size:11px;margin-bottom:3px}.followup-row .value{font-weight:800;overflow-wrap:anywhere}.followup-row.overdue{border-color:#8f3239;background:#261921}.followup-row.today{border-color:#8a6416}
    @media(max-width:1100px){.followup-row{grid-template-columns:120px 130px minmax(180px,1fr) 140px}.followup-row .followup-hide{display:none}}
    @media(max-width:700px){.followup-strip{grid-template-columns:1fr 1fr}.followup-row{grid-template-columns:1fr}.followup-row .followup-hide{display:block}}
'''
tv = replace_once(tv, style_close, tv_followup_css + style_close, 'follow-up TV CSS')

main_target = '    <main id="mainView">\n        <section class="dashboard-grid">'
main_new = '''    <main id="mainView">\n        <section class="followup-strip" aria-label="Follow-up queue">\n            <button class="followup-mini overdue" data-category="followup_overdue" type="button"><span id="label-followup-overdue">🔴 Overdue follow-ups</span><b id="followup-count-overdue">0</b></button>\n            <button class="followup-mini today" data-category="followup_today" type="button"><span id="label-followup-today">🟠 Due today</span><b id="followup-count-today">0</b></button>\n            <button class="followup-mini spares" data-category="followup_spares" type="button"><span id="label-followup-spares">🟡 Spare parts</span><b id="followup-count-spares">0</b></button>\n            <button class="followup-mini inquiries" data-category="followup_inquiries" type="button"><span id="label-followup-inquiries">🔵 Inquiries</span><b id="followup-count-inquiries">0</b></button>\n        </section>\n        <section class="dashboard-grid">'''
tv = replace_once(tv, main_target, main_new, 'follow-up strip markup')

tv = replace_once(tv, "            connecting:'Connecting to Google Sheets…'", "            connecting:'Connecting to Google Sheets…', followupOverdue:'🔴 Overdue follow-ups', followupToday:'🟠 Due today', followupSpares:'🟡 Spare parts', followupInquiries:'🔵 Inquiries', owner:'Owner', waitingOn:'Waiting on', nextAction:'Next action', nextFollowup:'Next follow-up', priority:'Priority', related:'Related ID', daysOverdue:'Days overdue'", 'English follow-up translations')
tv = replace_once(tv, "            syncReady:'اتصال Google Sheets للقراءة والكتابة جاهز.', syncNotReady:'اتصال الكتابة إلى Google Sheets غير جاهز.', checking:'جارٍ الفحص…', closeFailed:'فشل الإغلاق', remarkFail:'تعذر إغلاق الملاحظة', loading:'جارٍ تحميل بيانات القصر الذهبي مباشرة…', refreshing:'جارٍ التحديث مباشرة من المصدر…', connecting:'جارٍ الاتصال بـ Google Sheets…'", "            syncReady:'اتصال Google Sheets للقراءة والكتابة جاهز.', syncNotReady:'اتصال الكتابة إلى Google Sheets غير جاهز.', checking:'جارٍ الفحص…', closeFailed:'فشل الإغلاق', remarkFail:'تعذر إغلاق الملاحظة', loading:'جارٍ تحميل بيانات القصر الذهبي مباشرة…', refreshing:'جارٍ التحديث مباشرة من المصدر…', connecting:'جارٍ الاتصال بـ Google Sheets…', followupOverdue:'🔴 متابعات متأخرة', followupToday:'🟠 متابعة اليوم', followupSpares:'🟡 قطع غيار', followupInquiries:'🔵 استفسارات', owner:'المسؤول', waitingOn:'بانتظار', nextAction:'الخطوة القادمة', nextFollowup:'المتابعة القادمة', priority:'الأولوية', related:'المرجع', daysOverdue:'أيام التأخير'", 'Arabic follow-up translations')

summary_target = '            urgent_count:num(data.urgent_count), delayed_count:num(data.delayed_count), special_count:num(data.special_count),\n            remarks_list:Array.isArray(data.remarks_list) ? data.remarks_list.slice(0,100) : [],'
summary_new = '            urgent_count:num(data.urgent_count), delayed_count:num(data.delayed_count), special_count:num(data.special_count),\n            followup_overdue_count:num(data.followup_overdue_count), followup_due_today_count:num(data.followup_due_today_count),\n            followup_spare_parts_count:num(data.followup_spare_parts_count), followup_inquiry_count:num(data.followup_inquiry_count),\n            remarks_list:Array.isArray(data.remarks_list) ? data.remarks_list.slice(0,100) : [],'
tv = replace_once(tv, summary_target, summary_new, 'follow-up snapshot counts')

meta_en_target = "            remarks:{title:'📝 Workshop Remarks',description:'Live remarks from the remarks worksheet.',listKey:'remarks_list'}"
meta_en_new = "            followup_overdue:{title:'🔴 Overdue Follow-Ups',description:'Open follow-ups whose required follow-up date has passed.',listKey:'followup_overdue_list'},\n            followup_today:{title:'🟠 Due Today',description:'Follow-ups that require action today.',listKey:'followup_due_today_list'},\n            followup_spares:{title:'🟡 Spare Parts',description:'Open spare-part blockers affecting operations.',listKey:'followup_spare_parts_list'},\n            followup_inquiries:{title:'🔵 Inquiries',description:'Open customer and supplier inquiries.',listKey:'followup_inquiry_list'},\n            remarks:{title:'📝 Workshop Remarks',description:'Live remarks from the remarks worksheet.',listKey:'remarks_list'}"
tv = replace_once(tv, meta_en_target, meta_en_new, 'English follow-up category meta')
meta_ar_target = "            remarks:{title:'📝 ملاحظات الورشة',description:'الملاحظات المفتوحة مباشرة من ورقة الملاحظات.',listKey:'remarks_list'}"
meta_ar_new = "            followup_overdue:{title:'🔴 متابعات متأخرة',description:'متابعات مفتوحة تجاوزت موعد المتابعة المطلوب.',listKey:'followup_overdue_list'},\n            followup_today:{title:'🟠 متابعة اليوم',description:'المتابعات التي تتطلب إجراء اليوم.',listKey:'followup_due_today_list'},\n            followup_spares:{title:'🟡 قطع غيار',description:'عوائق قطع الغيار المفتوحة التي تؤثر على العمل.',listKey:'followup_spare_parts_list'},\n            followup_inquiries:{title:'🔵 استفسارات',description:'استفسارات الزبائن والموردين المفتوحة.',listKey:'followup_inquiry_list'},\n            remarks:{title:'📝 ملاحظات الورشة',description:'الملاحظات المفتوحة مباشرة من ورقة الملاحظات.',listKey:'remarks_list'}"
tv = replace_once(tv, meta_ar_target, meta_ar_new, 'Arabic follow-up category meta')

language_target = "        set('footerSlogan', tr('footerSlogan'));"
language_new = "        set('footerSlogan', tr('footerSlogan'));\n        set('label-followup-overdue', tr('followupOverdue')); set('label-followup-today', tr('followupToday'));\n        set('label-followup-spares', tr('followupSpares')); set('label-followup-inquiries', tr('followupInquiries'));"
tv = replace_once(tv, language_target, language_new, 'follow-up labels')

update_main_target = "        if (remarks) remarks.textContent = (data.remarks_list || []).length;\n    }"
update_main_new = "        if (remarks) remarks.textContent = (data.remarks_list || []).length;\n        const fuOverdue=document.getElementById('followup-count-overdue'); const fuToday=document.getElementById('followup-count-today');\n        const fuSpares=document.getElementById('followup-count-spares'); const fuInquiries=document.getElementById('followup-count-inquiries');\n        if(fuOverdue) fuOverdue.textContent=num(data.followup_overdue_count); if(fuToday) fuToday.textContent=num(data.followup_due_today_count);\n        if(fuSpares) fuSpares.textContent=num(data.followup_spare_parts_count); if(fuInquiries) fuInquiries.textContent=num(data.followup_inquiry_count);\n    }"
tv = replace_once(tv, update_main_target, update_main_new, 'follow-up main counts')

render_target = "    function renderTicketList() {\n        if (!detailMode || !latestData) return;\n        if (activeCategory === 'remarks') { renderRemarks(); return; }"
render_new = r'''    function renderFollowupList() {
        const list=currentList();
        const q=document.getElementById('searchBox').value.trim().toLowerCase();
        const filtered=list.filter(item=>!q||[item.followup_id,item.type,item.related_id,item.title,item.owner,item.waiting_on,item.next_action,item.priority,item.status].join(' ').toLowerCase().includes(q));
        const overdue=filtered.filter(x=>x.timing==='overdue').length;
        const urgent=filtered.filter(x=>x.priority==='Urgent').length;
        document.getElementById('detailStats').innerHTML=`<div class="stat"><span>${esc(tr('total'))}</span><b>${filtered.length}</b></div><div class="stat"><span>${esc(tr('followupOverdue'))}</span><b>${overdue}</b></div><div class="stat"><span>${esc(tr('urgentStat'))}</span><b>${urgent}</b></div><div class="stat"><span>${esc(tr('followupToday'))}</span><b>${filtered.filter(x=>x.timing==='today').length}</b></div>`;
        const container=document.getElementById('ticketList');
        document.getElementById('ticketPanel').style.display='none';
        if(!filtered.length){container.innerHTML=`<div class="empty">${esc(tr('noCases'))}</div>`;return;}
        container.innerHTML=filtered.map(item=>`<div class="followup-row ${item.timing==='overdue'?'overdue':item.timing==='today'?'today':''}">
          <div><small>ID</small><div class="ticket-id">${esc(item.followup_id)}</div><span class="badge">${esc(item.type)}</span></div>
          <div><small>${esc(tr('related'))}</small><div class="value">${esc(item.related_id)}</div><div>${esc(item.priority)}</div></div>
          <div><small>${esc(item.title)}</small><div class="value">${esc(item.next_action)}</div></div>
          <div><small>${esc(tr('owner'))}</small><div class="value">${esc(item.owner)}</div><div>${esc(item.status)}</div></div>
          <div class="followup-hide"><small>${esc(tr('waitingOn'))}</small><div class="value">${esc(item.waiting_on)}</div></div>
          <div class="followup-hide"><small>${esc(tr('nextFollowup'))}</small><div class="value">${esc(item.next_followup)}</div>${item.timing==='overdue'?`<span class="badge danger">${num(item.days_overdue)} ${esc(tr('dayShort'))}</span>`:''}</div>
        </div>`).join('');
    }

    function renderTicketList() {
        if (!detailMode || !latestData) return;
        if (activeCategory === 'remarks') { renderRemarks(); return; }
        if (activeCategory.startsWith('followup_')) { renderFollowupList(); return; }'''
tv = replace_once(tv, render_target, render_new, 'follow-up detail renderer')

event_target = "    document.querySelectorAll('.workflow-card').forEach(btn => btn.addEventListener('click', () => openCategory(btn.dataset.category)));"
event_new = "    document.querySelectorAll('.workflow-card').forEach(btn => btn.addEventListener('click', () => openCategory(btn.dataset.category)));\n    document.querySelectorAll('.followup-mini').forEach(btn => btn.addEventListener('click', () => openCategory(btn.dataset.category)));"
tv = replace_once(tv, event_target, event_new, 'follow-up card events')

# Syntax guardrails before writing.
compile(tools, str(TOOLS), 'exec')
compile(flask, str(FLASK), 'exec')
for marker, text in [('GP_FOLLOWUP_CENTER_V1', tools), ('GP_FOLLOWUP_TV_API_V1', flask), ('GP_FOLLOWUP_TV_UI_V1', tv)]:
    if text.count(marker) != 1:
        raise SystemExit(f'Expected exactly one {marker}, got {text.count(marker)}')

TOOLS.write_text(tools, encoding='utf-8')
FLASK.write_text(flask, encoding='utf-8')
TV.write_text(tv, encoding='utf-8')
print('Unified Follow-Up Center + TV integration staged successfully')
