from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing patch target: {label}")
    return text.replace(old, new, 1)


tools_path = Path("tools_tracker.py")
flask_path = Path("flask_app.py")
tv_path = Path("templates/tv.html")

tools = tools_path.read_text(encoding="utf-8")
flask = flask_path.read_text(encoding="utf-8")
tv = tv_path.read_text(encoding="utf-8")

# -----------------------------------------------------------------------------
# Streamlit backend: global TV control + automatic refresh signal after any save.
# -----------------------------------------------------------------------------
if "GP_TV_CONTROL_AND_PUSH_V1" not in tools:
    helper_anchor = '''def publish_manual_tv_announcement(text, language="auto", published_by="", voice_enabled=True):\n'''
    helper_insert = r'''
# GP_TV_CONTROL_AND_PUSH_V1

def gp_tv_control_request(method="GET", **fields):
    headers = {"Accept": "application/json"}
    if GP_TV_ANNOUNCEMENT_KEY:
        headers["X-GP-Announcement-Key"] = GP_TV_ANNOUNCEMENT_KEY
    url = f"{GP_TV_BACKEND_URL.rstrip('/')}/api/tv-control"
    if str(method).upper() == "POST":
        response = requests.post(url, json=fields, headers=headers, timeout=(3, 6))
    else:
        response = requests.get(url, headers=headers, timeout=(3, 6))
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error") or "TV control request failed")
    return data


def gp_signal_tv_refresh(reason="backend_save"):
    """Tell every open TV to force-refresh immediately. Never block a successful save."""
    try:
        return gp_tv_control_request(
            "POST",
            refresh_now=True,
            reason=str(reason or "backend_save")[:120],
        )
    except Exception:
        return None

'''
    tools = replace_once(tools, helper_anchor, helper_insert + helper_anchor, "TV control helper")

    save_anchor = '''        try:\n            st.cache_data.clear()\n        except Exception:\n            pass\n\n\ndef _canonical_stock_header(value):\n'''
    save_replacement = '''        try:\n            st.cache_data.clear()\n        except Exception:\n            pass\n        # Any successful backend write tells the TV to reload immediately.\n        gp_signal_tv_refresh(f"{doctype_name}_saved")\n\n\ndef _canonical_stock_header(value):\n'''
    tools = replace_once(tools, save_anchor, save_replacement, "save_doctype instant TV signal")

    ui_anchor = '''    # GP_MANUAL_TV_ANNOUNCEMENT_UI_V1\n    with st.expander("📣 إعلان مباشر إلى شاشة الورشة (Live TV Announcement)", expanded=False):\n'''
    ui_insert = r'''    # GP_TV_CONTROL_AND_PUSH_UI_V1
    with st.expander("📺 تحكم شاشة الورشة (TV Control)", expanded=False):
        try:
            gp_tv_state = gp_tv_control_request("GET")
            gp_staff_voice_current = bool(gp_tv_state.get("staff_voice_enabled", True))
        except Exception:
            gp_tv_state = {"ok": False}
            gp_staff_voice_current = True

        gp_staff_voice_choice = st.toggle(
            "🔊 الإعلانات العشوائية للموظفين (Random staff voice announcements)",
            value=gp_staff_voice_current,
            help="هذا المفتاح يتحكم بالصوت العشوائي الدوري للموظفين على شاشة التلفزيون، ولا يلغي خيار الصوت الخاص بالإعلان اليدوي.",
            key="gp_staff_random_voice_backend_toggle",
        )
        c_tv_voice, c_tv_push = st.columns(2)
        with c_tv_voice:
            if st.button("✅ تطبيق الصوت فوراً على التلفزيون", use_container_width=True, key="gp_apply_staff_voice_tv"):
                try:
                    gp_tv_control_request(
                        "POST",
                        staff_voice_enabled=bool(gp_staff_voice_choice),
                        reason="backend_staff_voice_change",
                    )
                    st.success("✅ تم تحديث صوت الموظفين على التلفزيون فوراً.")
                except Exception as exc:
                    st.error(f"❌ تعذر تحديث إعداد الصوت: {exc}")
        with c_tv_push:
            if st.button("⚡ دفع أحدث البيانات إلى التلفزيون الآن", use_container_width=True, key="gp_push_tv_now"):
                try:
                    gp_tv_control_request("POST", refresh_now=True, reason="manual_backend_push")
                    st.success("✅ تم إرسال أمر تحديث فوري إلى التلفزيون.")
                except Exception as exc:
                    st.error(f"❌ تعذر إرسال أمر التحديث: {exc}")
        st.caption("أي حفظ جديد داخل النظام يرسل أمر تحديث للتلفزيون تلقائياً أيضاً. التحديث الدوري كل 15 ثانية يبقى كنسخة احتياطية فقط.")

'''
    tools = replace_once(tools, ui_anchor, ui_insert + ui_anchor, "TV control backend UI")

# -----------------------------------------------------------------------------
# Flask: lightweight TV control mailbox. TV polls this once per second.
# -----------------------------------------------------------------------------
if "GP_TV_CONTROL_AND_PUSH_V1" not in flask:
    flask_anchor = '''@app.route("/api/manual-announcement", methods=["POST", "OPTIONS"])\ndef api_manual_announcement():\n'''
    flask_insert = r'''
# GP_TV_CONTROL_AND_PUSH_V1
GP_TV_CONTROL_FILE = os.path.join(tempfile.gettempdir(), "gp_tv_control_v1.json")
GP_TV_CONTROL_LOCK = threading.RLock()


def gp_default_tv_control():
    return {
        "staff_voice_enabled": True,
        "data_revision": "",
        "updated_at": 0,
        "reason": "",
    }


def gp_read_tv_control():
    state = gp_default_tv_control()
    try:
        with GP_TV_CONTROL_LOCK:
            if os.path.exists(GP_TV_CONTROL_FILE):
                with open(GP_TV_CONTROL_FILE, "r", encoding="utf-8") as handle:
                    saved = json.load(handle)
                if isinstance(saved, dict):
                    state.update(saved)
    except Exception as exc:
        print("TV control read error:", repr(exc))
    state["staff_voice_enabled"] = bool(state.get("staff_voice_enabled", True))
    state["data_revision"] = str(state.get("data_revision", "") or "")
    return state


def gp_write_tv_control(state):
    temp_path = f"{GP_TV_CONTROL_FILE}.{os.getpid()}.tmp"
    with GP_TV_CONTROL_LOCK:
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False)
            os.replace(temp_path, GP_TV_CONTROL_FILE)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass


@app.route("/api/tv-control", methods=["GET", "POST", "OPTIONS"])
def api_tv_control():
    if request.method == "OPTIONS":
        return ("", 204)
    state = gp_read_tv_control()
    if request.method == "POST":
        if not gp_manual_announcement_authorized():
            return jsonify({"ok": False, "error": "unauthorized"}), 403
        payload = request.get_json(silent=True) or {}
        if "staff_voice_enabled" in payload:
            state["staff_voice_enabled"] = bool(payload.get("staff_voice_enabled"))
        if payload.get("refresh_now"):
            # String form preserves nanosecond uniqueness in JavaScript.
            state["data_revision"] = str(time.time_ns())
        state["updated_at"] = time.time()
        state["reason"] = re.sub(r"\s+", " ", str(payload.get("reason", ""))).strip()[:120]
        gp_write_tv_control(state)
    response = jsonify({"ok": True, **state})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


'''
    flask = replace_once(flask, flask_anchor, flask_insert + flask_anchor, "TV control API")

# -----------------------------------------------------------------------------
# TV: enforce backend random-voice state + react to refresh revisions in ~1 sec.
# -----------------------------------------------------------------------------
if "GP_TV_CONTROL_AND_PUSH_V1" not in tv:
    tv_anchor = '''    async function refreshDashboard(force=false) {\n'''
    tv_insert = r'''
    // GP_TV_CONTROL_AND_PUSH_V1
    const GP_TV_CONTROL_POLL_MS = 1000;
    let gpTvControlPollInFlight = false;
    let gpTvControlRevision = null;
    let gpRemoteStaffVoiceEnabled = null;

    function gpManualAnnouncementVisible() {
        const overlay = document.getElementById('manualAnnouncementOverlay');
        return Boolean(overlay && overlay.classList.contains('show'));
    }

    function gpApplyRemoteStaffVoice(enabled) {
        enabled = enabled !== false;
        const priorRemote = gpRemoteStaffVoiceEnabled;
        gpRemoteStaffVoiceEnabled = enabled;

        if (!enabled) {
            clearTimeout(teamVoiceTimer);
            teamVoiceTimer = null;
            teamVoiceEnabled = false;
            // Do not cut off a manually published announcement just because random voices are disabled.
            if (!gpManualAnnouncementVisible()) stopTeamVoiceAudio();
            updateVoiceButton();
            return;
        }

        const wasDisabled = !teamVoiceEnabled || priorRemote === false;
        teamVoiceEnabled = true;
        updateVoiceButton();
        if (wasDisabled && !detailMode) scheduleNextTeamVoice(1800);
    }

    async function gpPollTvControl() {
        if (gpTvControlPollInFlight || document.hidden) return;
        gpTvControlPollInFlight = true;
        try {
            const response = await fetch(apiUrl(`/api/tv-control?t=${Date.now()}`), {cache:'no-store'});
            if (!response.ok) return;
            const state = await response.json();
            if (!state || !state.ok) return;

            gpApplyRemoteStaffVoice(state.staff_voice_enabled !== false);

            const revision = String(state.data_revision || '');
            if (gpTvControlRevision === null) {
                gpTvControlRevision = revision;
            } else if (revision && revision !== gpTvControlRevision) {
                gpTvControlRevision = revision;
                // Force bypass of the backend summary cache; remarks are refreshed in parallel.
                refreshDashboard(true);
                refreshRemarks();
            }
        } catch (_) {
            // 15-second dashboard polling remains the fallback if the control channel is unavailable.
        } finally {
            gpTvControlPollInFlight = false;
        }
    }

'''
    tv = replace_once(tv, tv_anchor, tv_insert + tv_anchor, "TV control runtime")

    startup_anchor = '''    setTimeout(gpPollManualAnnouncement, 500);\n    setInterval(gpPollManualAnnouncement, GP_MANUAL_ANNOUNCEMENT_POLL_MS);\n    setInterval(() => refreshDashboard(false), 15000);\n'''
    startup_replacement = '''    setTimeout(gpPollManualAnnouncement, 500);\n    setInterval(gpPollManualAnnouncement, GP_MANUAL_ANNOUNCEMENT_POLL_MS);\n    setTimeout(gpPollTvControl, 250);\n    setInterval(gpPollTvControl, GP_TV_CONTROL_POLL_MS);\n    setInterval(() => refreshDashboard(false), 15000);\n'''
    tv = replace_once(tv, startup_anchor, startup_replacement, "TV control startup")

tools_path.write_text(tools, encoding="utf-8")
flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
print("TV control and instant push feature patched")
