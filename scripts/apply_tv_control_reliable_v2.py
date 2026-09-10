from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing patch target: {label}")
    return text.replace(old, new, 1)


tools_path = Path("tools_tracker.py")
flask_path = Path("flask_app.py")
tv_path = Path("templates/tv.html")
kiosk_path = Path("GP-TV-Fullscreen.cmd")

tools = tools_path.read_text(encoding="utf-8")
flask = flask_path.read_text(encoding="utf-8")
tv = tv_path.read_text(encoding="utf-8")
kiosk = kiosk_path.read_text(encoding="utf-8")

# =============================================================================
# Streamlit backend: one button per operation; every click also force-pushes TV
# data and waits for a real TV-side "applied" ACK.
# =============================================================================
if "GP_TV_CONTROL_RELIABLE_V2" not in tools:
    tools = replace_once(tools, "import os\nimport hashlib\n", "import os\nimport time\nimport hashlib\n", "import time")

    helper_anchor = '''def publish_manual_tv_announcement(text, language="auto", published_by="", voice_enabled=True):\n'''
    helper = r'''
# GP_TV_CONTROL_RELIABLE_V2

def gp_apply_tv_control_and_wait(reason, **fields):
    """Send one TV command, force fresh data, and wait briefly for TV ACK."""
    payload = dict(fields)
    payload["refresh_now"] = True
    payload["reason"] = str(reason or "backend_tv_control")[:120]
    sent = gp_tv_control_request("POST", **payload)
    command_id = str(sent.get("command_id", "") or "")
    if not command_id:
        return sent, False

    deadline = time.time() + 6.0
    latest = sent
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            latest = gp_tv_control_request("GET")
        except Exception:
            continue
        if str(latest.get("last_applied_command_id", "") or "") == command_id:
            return latest, True
    return latest, False


def gp_tv_online(state, within_seconds=12):
    try:
        seen = float(state.get("last_tv_seen_at", 0) or 0)
        return bool(seen and (time.time() - seen) <= within_seconds)
    except Exception:
        return False

'''
    tools = replace_once(tools, helper_anchor, helper + helper_anchor, "reliable TV helper")

    old_ui = '''        # GP_DELAYED_VOICE_CONTROL_V1
        gp_staff_voice_choice = st.toggle(
            "🔊 الإعلانات العشوائية للموظفين (Random staff encouragement voice)",
            value=gp_staff_voice_current,
            help="يشغّل أو يوقف رسائل التشجيع العشوائية للموظفين فقط.",
            key="gp_staff_random_voice_backend_toggle",
        )
        gp_delayed_voice_choice = st.toggle(
            "⏰ تنبيه الحالات المتأخرة (Delayed follow-up announcement)",
            value=gp_delayed_voice_current,
            help="مستقل عن صوت تشجيع الموظفين. عند إيقافه تبقى الحالة المتأخرة ظاهرة على الشاشة بدون إعلان صوتي.",
            key="gp_delayed_voice_backend_toggle",
        )

        c_staff_voice, c_delayed_voice = st.columns(2)
        with c_staff_voice:
            if st.button("✅ تطبيق صوت الموظفين", use_container_width=True, key="gp_apply_staff_voice_tv"):
                try:
                    gp_tv_control_request(
                        "POST",
                        staff_voice_enabled=bool(gp_staff_voice_choice),
                        reason="backend_staff_voice_change",
                    )
                    st.success("✅ تم تحديث صوت تشجيع الموظفين فوراً.")
                except Exception as exc:
                    st.error(f"❌ تعذر تحديث صوت الموظفين: {exc}")
        with c_delayed_voice:
            if st.button("✅ تطبيق تنبيه التأخير", use_container_width=True, key="gp_apply_delayed_voice_tv"):
                try:
                    gp_tv_control_request(
                        "POST",
                        delayed_voice_enabled=bool(gp_delayed_voice_choice),
                        reason="backend_delayed_voice_change",
                    )
                    st.success("✅ تم تحديث تنبيه الحالات المتأخرة فوراً.")
                except Exception as exc:
                    st.error(f"❌ تعذر تحديث تنبيه التأخير: {exc}")

        if st.button("⚡ دفع أحدث البيانات إلى التلفزيون الآن", use_container_width=True, key="gp_push_tv_now"):
            try:
                gp_tv_control_request("POST", refresh_now=True, reason="manual_backend_push")
                st.success("✅ تم إرسال أمر تحديث فوري إلى التلفزيون.")
            except Exception as exc:
                st.error(f"❌ تعذر إرسال أمر التحديث: {exc}")
        st.caption("صوت الموظفين وتنبيه الحالات المتأخرة أصبحا مستقلين. أي حفظ جديد يرسل أيضاً أمر تحديث فوري للتلفزيون.")
'''
    new_ui = '''        # GP_DELAYED_VOICE_CONTROL_V1
        # GP_TV_CONTROL_RELIABLE_V2
        flash = st.session_state.pop("_gp_tv_control_flash", None)
        if flash:
            level, message = flash
            if level == "success":
                st.success(message)
            elif level == "warning":
                st.warning(message)
            else:
                st.error(message)

        if gp_tv_online(gp_tv_state):
            age = max(0, int(time.time() - float(gp_tv_state.get("last_tv_seen_at", 0) or 0)))
            st.success(f"🟢 التلفزيون متصل · آخر استجابة منذ {age} ثانية")
        else:
            st.warning("🔴 لا توجد استجابة حديثة من التلفزيون. الأمر سيُحفظ، لكن النجاح لن يُعتبر مؤكداً حتى يرد التلفزيون.")

        c_staff_voice, c_delayed_voice = st.columns(2)
        with c_staff_voice:
            staff_target = not gp_staff_voice_current
            staff_label = (
                "🔴 إيقاف صوت تشجيع الموظفين + تحديث TV الآن"
                if gp_staff_voice_current
                else "🟢 تشغيل صوت تشجيع الموظفين + تحديث TV الآن"
            )
            if st.button(staff_label, use_container_width=True, key="gp_oneclick_staff_voice_tv"):
                try:
                    state, confirmed = gp_apply_tv_control_and_wait(
                        "backend_staff_voice_toggle",
                        staff_voice_enabled=staff_target,
                    )
                    if confirmed:
                        status_word = "تم التشغيل" if staff_target else "تم الإيقاف"
                        st.session_state["_gp_tv_control_flash"] = (
                            "success",
                            f"✅ {status_word} لصوت الموظفين، وتم تحديث البيانات، والتلفزيون أكد تنفيذ الأمر.",
                        )
                    else:
                        st.session_state["_gp_tv_control_flash"] = (
                            "warning",
                            "⚠️ تم حفظ أمر صوت الموظفين وتحديث البيانات على الخادم، لكن التلفزيون لم يؤكد التنفيذ خلال 6 ثوانٍ.",
                        )
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ تعذر إرسال أمر صوت الموظفين: {exc}")

        with c_delayed_voice:
            delayed_target = not gp_delayed_voice_current
            delayed_label = (
                "🔴 إيقاف تنبيه الحالات المتأخرة + تحديث TV الآن"
                if gp_delayed_voice_current
                else "🟢 تشغيل تنبيه الحالات المتأخرة + تحديث TV الآن"
            )
            if st.button(delayed_label, use_container_width=True, key="gp_oneclick_delayed_voice_tv"):
                try:
                    state, confirmed = gp_apply_tv_control_and_wait(
                        "backend_delayed_voice_toggle",
                        delayed_voice_enabled=delayed_target,
                    )
                    if confirmed:
                        status_word = "تم التشغيل" if delayed_target else "تم الإيقاف"
                        st.session_state["_gp_tv_control_flash"] = (
                            "success",
                            f"✅ {status_word} لتنبيه التأخير، وتم تحديث البيانات، والتلفزيون أكد تنفيذ الأمر.",
                        )
                    else:
                        st.session_state["_gp_tv_control_flash"] = (
                            "warning",
                            "⚠️ تم حفظ أمر تنبيه التأخير وتحديث البيانات على الخادم، لكن التلفزيون لم يؤكد التنفيذ خلال 6 ثوانٍ.",
                        )
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ تعذر إرسال أمر تنبيه التأخير: {exc}")

        if st.button("⚡ تحديث بيانات التلفزيون الآن", use_container_width=True, key="gp_push_tv_now_v2"):
            try:
                _, confirmed = gp_apply_tv_control_and_wait("manual_backend_push")
                if confirmed:
                    st.session_state["_gp_tv_control_flash"] = (
                        "success",
                        "✅ تم دفع أحدث البيانات والتلفزيون أكد تنفيذ التحديث.",
                    )
                else:
                    st.session_state["_gp_tv_control_flash"] = (
                        "warning",
                        "⚠️ تم طلب تحديث البيانات من الخادم، لكن التلفزيون لم يؤكد التنفيذ خلال 6 ثوانٍ.",
                    )
                st.rerun()
            except Exception as exc:
                st.error(f"❌ تعذر إرسال أمر تحديث البيانات: {exc}")

        st.caption("كل زر ينفذ العملية ويطلب تحديث البيانات في نفس اللحظة. الأخضر يظهر فقط بعد أن يؤكد التلفزيون تنفيذ الأمر.")
'''
    tools = replace_once(tools, old_ui, new_ui, "one-click TV control UI")

# =============================================================================
# Flask: command IDs + TV heartbeat/applied ACK + forced synchronous live refresh.
# =============================================================================
if "GP_TV_COMMAND_ACK_V2" not in flask:
    flask = replace_once(
        flask,
        '''        "data_revision": "",\n        "updated_at": 0,\n        "reason": "",\n''',
        '''        "data_revision": "",\n        # GP_TV_COMMAND_ACK_V2\n        "command_id": "",\n        "command_created_at": 0,\n        "last_applied_command_id": "",\n        "last_applied_at": 0,\n        "last_tv_seen_at": 0,\n        "last_tv_client": "",\n        "updated_at": 0,\n        "reason": "",\n''',
        "TV command state defaults",
    )
    flask = replace_once(
        flask,
        '''    state["data_revision"] = str(state.get("data_revision", "") or "")\n    return state\n''',
        '''    state["data_revision"] = str(state.get("data_revision", "") or "")\n    state["command_id"] = str(state.get("command_id", "") or "")\n    state["last_applied_command_id"] = str(state.get("last_applied_command_id", "") or "")\n    return state\n''',
        "TV command state normalization",
    )

    old_control = '''@app.route("/api/tv-control", methods=["GET", "POST", "OPTIONS"])
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
        if "delayed_voice_enabled" in payload:
            state["delayed_voice_enabled"] = bool(payload.get("delayed_voice_enabled"))
        if payload.get("refresh_now"):
            # String form preserves nanosecond uniqueness in JavaScript.
            state["data_revision"] = str(time.time_ns())
        state["updated_at"] = time.time()
        state["reason"] = re.sub(r"\\s+", " ", str(payload.get("reason", ""))).strip()[:120]
        gp_write_tv_control(state)
    response = jsonify({"ok": True, **state})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response
'''
    new_control = '''@app.route("/api/tv-control", methods=["GET", "POST", "OPTIONS"])
def api_tv_control():
    if request.method == "OPTIONS":
        return ("", 204)
    state = gp_read_tv_control()
    if request.method == "POST":
        if not gp_manual_announcement_authorized():
            return jsonify({"ok": False, "error": "unauthorized"}), 403
        payload = request.get_json(silent=True) or {}
        changed = False
        if "staff_voice_enabled" in payload:
            state["staff_voice_enabled"] = bool(payload.get("staff_voice_enabled"))
            changed = True
        if "delayed_voice_enabled" in payload:
            state["delayed_voice_enabled"] = bool(payload.get("delayed_voice_enabled"))
            changed = True

        refresh_now = bool(payload.get("refresh_now"))
        if changed or refresh_now:
            command_id = str(time.time_ns())
            state["command_id"] = command_id
            state["command_created_at"] = time.time()
            # Every control command also carries an immediate data refresh revision.
            state["data_revision"] = command_id

        state["updated_at"] = time.time()
        state["reason"] = re.sub(r"\\s+", " ", str(payload.get("reason", ""))).strip()[:120]
        gp_write_tv_control(state)
    response = jsonify({"ok": True, **state})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@app.route("/api/tv-control/ack", methods=["POST", "OPTIONS"])
def api_tv_control_ack():
    if request.method == "OPTIONS":
        return ("", 204)
    payload = request.get_json(silent=True) or {}
    state = gp_read_tv_control()
    now = time.time()
    client = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("client", "")))[:64]
    command_id = str(payload.get("command_id", "") or "")

    state["last_tv_seen_at"] = now
    if client:
        state["last_tv_client"] = client
    if command_id and command_id == str(state.get("command_id", "") or ""):
        state["last_applied_command_id"] = command_id
        state["last_applied_at"] = now
        state["tv_staff_voice_enabled"] = bool(payload.get("staff_voice_enabled", state.get("staff_voice_enabled", True)))
        state["tv_delayed_voice_enabled"] = bool(payload.get("delayed_voice_enabled", state.get("delayed_voice_enabled", True)))
    gp_write_tv_control(state)
    response = jsonify({"ok": True, **state})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response
'''
    flask = replace_once(flask, old_control, new_control, "command ACK control API")

    # A force request previously only STARTED the background refresh and then
    # returned the old cache.  For a PC push command we need the response to be
    # freshly rebuilt before the TV acknowledges the command.
    old_force = '''        age = max(now - saved_at, 0) if saved_at else None
        stale = (not cached) or force or (age is not None and age >= TV_CACHE_TTL_SECONDS)
        if stale:
            start_tv_refresh(force=force)

        if cached:
'''
    new_force = '''        age = max(now - saved_at, 0) if saved_at else None
        if force:
            try:
                fresh = build_tv_api_payload()
                has_any_queue_data = any(fresh.get(key) for key in (
                    "progress_list", "collection_list", "partner_list",
                    "zero_list", "collected_list", "partner_closed_list",
                ))
                if has_any_queue_data or not cached:
                    fresh["loading"] = False
                    fresh["refreshing"] = False
                    save_tv_cache(fresh)
                    cached, saved_at = load_tv_cache()
                    age = max(time.time() - saved_at, 0) if saved_at else None
                else:
                    start_tv_refresh(force=True)
            except Exception as exc:
                print("Forced TV refresh error:", repr(exc))
                start_tv_refresh(force=True)
        else:
            stale = (not cached) or (age is not None and age >= TV_CACHE_TTL_SECONDS)
            if stale:
                start_tv_refresh(force=False)

        if cached:
'''
    flask = replace_once(flask, old_force, new_force, "synchronous forced data refresh")

# =============================================================================
# TV: never ignore control commands just because tab is backgrounded.  Apply
# latest state, force fresh data once per command, then ACK it.  Heartbeat makes
# the PC show true online/offline status.
# =============================================================================
if "GP_TV_COMMAND_ACK_RUNTIME_V2" not in tv:
    tv = replace_once(
        tv,
        '''    let gpTvControlPollInFlight = false;\n    let gpTvControlRevision = null;\n    let gpRemoteStaffVoiceEnabled = null;\n    // GP_DELAYED_VOICE_RUNTIME_V1\n    let gpRemoteDelayedVoiceEnabled = true;\n''',
        '''    let gpTvControlPollInFlight = false;\n    let gpTvControlRevision = null;\n    let gpRemoteStaffVoiceEnabled = null;\n    // GP_DELAYED_VOICE_RUNTIME_V1\n    let gpRemoteDelayedVoiceEnabled = true;\n    // GP_TV_COMMAND_ACK_RUNTIME_V2\n    let gpTvLastCommandId = '';\n    let gpTvLastHeartbeatAt = 0;\n    const GP_TV_CONTROL_CLIENT_KEY = 'gpTvControlClientV2';\n    const gpTvControlClient = (() => {\n        try {\n            let value = localStorage.getItem(GP_TV_CONTROL_CLIENT_KEY) || '';\n            if (!value) {\n                value = `tv-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;\n                localStorage.setItem(GP_TV_CONTROL_CLIENT_KEY, value);\n            }\n            return value;\n        } catch (_) { return 'tv-browser'; }\n    })();\n''',
        "TV command runtime state",
    )

    old_poll = '''    async function gpPollTvControl() {
        if (gpTvControlPollInFlight || document.hidden) return;
        gpTvControlPollInFlight = true;
        try {
            const response = await fetch(apiUrl(`/api/tv-control?t=${Date.now()}`), {cache:'no-store'});
            if (!response.ok) return;
            const state = await response.json();
            if (!state || !state.ok) return;

            gpApplyRemoteStaffVoice(state.staff_voice_enabled !== false);
            gpRemoteDelayedVoiceEnabled = state.delayed_voice_enabled !== false;

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
    new_poll = '''    async function gpSendTvControlAck(state) {
        try {
            await fetch(apiUrl('/api/tv-control/ack'), {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                cache: 'no-store',
                keepalive: true,
                body: JSON.stringify({
                    command_id: String(state?.command_id || ''),
                    client: gpTvControlClient,
                    staff_voice_enabled: gpRemoteStaffVoiceEnabled !== false,
                    delayed_voice_enabled: gpRemoteDelayedVoiceEnabled !== false
                })
            });
            gpTvLastHeartbeatAt = Date.now();
        } catch (_) {}
    }

    async function gpPollTvControl() {
        // Do not skip PC commands when the browser tab is backgrounded. Browsers
        // may throttle timers, but the TV will still process the latest command.
        if (gpTvControlPollInFlight) return;
        gpTvControlPollInFlight = true;
        try {
            const response = await fetch(apiUrl(`/api/tv-control?t=${Date.now()}`), {cache:'no-store'});
            if (!response.ok) return;
            const state = await response.json();
            if (!state || !state.ok) return;

            gpApplyRemoteStaffVoice(state.staff_voice_enabled !== false);
            gpRemoteDelayedVoiceEnabled = state.delayed_voice_enabled !== false;

            const commandId = String(state.command_id || '');
            const revision = String(state.data_revision || '');
            const newCommand = Boolean(commandId && commandId !== gpTvLastCommandId);
            const newRevision = Boolean(revision && revision !== gpTvControlRevision);

            if (newRevision) {
                gpTvControlRevision = revision;
                // force=1 now waits for a fresh backend rebuild before returning.
                await refreshDashboard(true);
                await refreshRemarks();
            }

            if (newCommand) {
                gpTvLastCommandId = commandId;
                await gpSendTvControlAck(state);
            } else if (Date.now() - gpTvLastHeartbeatAt >= 5000) {
                // Heartbeat lets the backend distinguish a live TV from an
                // accepted command sitting on the server while the TV is off.
                await gpSendTvControlAck(state);
            }
        } catch (_) {
            // 15-second dashboard polling remains the fallback for data.
        } finally {
            gpTvControlPollInFlight = false;
        }
    }
'''
    tv = replace_once(tv, old_poll, new_poll, "reliable TV command poll")

# =============================================================================
# Kiosk launcher: use the SAME Render service that owns the command mailbox.
# This removes drift between gp-tv and the backend deployment.
# =============================================================================
if "golden-palace-service-tracker.onrender.com/tv?lang=ar" not in kiosk:
    kiosk = kiosk.replace(
        'set "TVURL=https://gp-tv.onrender.com/?lang=ar"',
        'set "TVURL=https://golden-palace-service-tracker.onrender.com/tv?lang=ar"',
    )

# Persist patched files.
tools_path.write_text(tools, encoding="utf-8")
flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
kiosk_path.write_text(kiosk, encoding="utf-8")
print("Reliable TV controls, synchronous push, ACK heartbeat, and unified kiosk URL patched")
