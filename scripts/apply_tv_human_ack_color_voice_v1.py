from pathlib import Path
import re


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing patch target: {label}")
    return text.replace(old, new, 1)


def sub_once(text, pattern, replacement, label, flags=0):
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"Missing/ambiguous regex patch target: {label} ({count})")
    return new_text


tools_path = Path("tools_tracker.py")
flask_path = Path("flask_app.py")
tv_path = Path("templates/tv.html")
announce_path = Path("templates/announce.html")

tools = tools_path.read_text(encoding="utf-8")
flask = flask_path.read_text(encoding="utf-8")
tv = tv_path.read_text(encoding="utf-8")
announce = announce_path.read_text(encoding="utf-8")

# =============================================================================
# STREAMLIT BACKEND: separate overdue/delayed announcement voice control.
# =============================================================================
if "GP_DELAYED_VOICE_CONTROL_V1" not in tools:
    tools = replace_once(
        tools,
        '''            gp_tv_state = gp_tv_control_request("GET")\n            gp_staff_voice_current = bool(gp_tv_state.get("staff_voice_enabled", True))\n        except Exception:\n            gp_tv_state = {"ok": False}\n            gp_staff_voice_current = True\n''',
        '''            gp_tv_state = gp_tv_control_request("GET")\n            gp_staff_voice_current = bool(gp_tv_state.get("staff_voice_enabled", True))\n            gp_delayed_voice_current = bool(gp_tv_state.get("delayed_voice_enabled", True))\n        except Exception:\n            gp_tv_state = {"ok": False}\n            gp_staff_voice_current = True\n            gp_delayed_voice_current = True\n''',
        "TV control state load",
    )

    old_ui = r'''        gp_staff_voice_choice = st\.toggle\(\n            "🔊 الإعلانات العشوائية للموظفين \(Random staff voice announcements\)",\n            value=gp_staff_voice_current,\n            help="هذا المفتاح يتحكم بالصوت العشوائي الدوري للموظفين على شاشة التلفزيون، ولا يلغي خيار الصوت الخاص بالإعلان اليدوي\.",\n            key="gp_staff_random_voice_backend_toggle",\n        \)\n        c_tv_voice, c_tv_push = st\.columns\(2\)\n        with c_tv_voice:\n            if st\.button\("✅ تطبيق الصوت فوراً على التلفزيون", use_container_width=True, key="gp_apply_staff_voice_tv"\):\n                try:\n                    gp_tv_control_request\(\n                        "POST",\n                        staff_voice_enabled=bool\(gp_staff_voice_choice\),\n                        reason="backend_staff_voice_change",\n                    \)\n                    st\.success\("✅ تم تحديث صوت الموظفين على التلفزيون فوراً\."\)\n                except Exception as exc:\n                    st\.error\(f"❌ تعذر تحديث إعداد الصوت: \{exc\}"\)\n        with c_tv_push:\n            if st\.button\("⚡ دفع أحدث البيانات إلى التلفزيون الآن", use_container_width=True, key="gp_push_tv_now"\):\n                try:\n                    gp_tv_control_request\("POST", refresh_now=True, reason="manual_backend_push"\)\n                    st\.success\("✅ تم إرسال أمر تحديث فوري إلى التلفزيون\."\)\n                except Exception as exc:\n                    st\.error\(f"❌ تعذر إرسال أمر التحديث: \{exc\}"\)\n        st\.caption\("أي حفظ جديد داخل النظام يرسل أمر تحديث للتلفزيون تلقائياً أيضاً\. التحديث الدوري كل 15 ثانية يبقى كنسخة احتياطية فقط\."\)'''
    new_ui = '''        # GP_DELAYED_VOICE_CONTROL_V1\n        gp_staff_voice_choice = st.toggle(\n            "🔊 الإعلانات العشوائية للموظفين (Random staff encouragement voice)",\n            value=gp_staff_voice_current,\n            help="يشغّل أو يوقف رسائل التشجيع العشوائية للموظفين فقط.",\n            key="gp_staff_random_voice_backend_toggle",\n        )\n        gp_delayed_voice_choice = st.toggle(\n            "⏰ تنبيه الحالات المتأخرة (Delayed follow-up announcement)",\n            value=gp_delayed_voice_current,\n            help="مستقل عن صوت تشجيع الموظفين. عند إيقافه تبقى الحالة المتأخرة ظاهرة على الشاشة بدون إعلان صوتي.",\n            key="gp_delayed_voice_backend_toggle",\n        )\n\n        c_staff_voice, c_delayed_voice = st.columns(2)\n        with c_staff_voice:\n            if st.button("✅ تطبيق صوت الموظفين", use_container_width=True, key="gp_apply_staff_voice_tv"):\n                try:\n                    gp_tv_control_request(\n                        "POST",\n                        staff_voice_enabled=bool(gp_staff_voice_choice),\n                        reason="backend_staff_voice_change",\n                    )\n                    st.success("✅ تم تحديث صوت تشجيع الموظفين فوراً.")\n                except Exception as exc:\n                    st.error(f"❌ تعذر تحديث صوت الموظفين: {exc}")\n        with c_delayed_voice:\n            if st.button("✅ تطبيق تنبيه التأخير", use_container_width=True, key="gp_apply_delayed_voice_tv"):\n                try:\n                    gp_tv_control_request(\n                        "POST",\n                        delayed_voice_enabled=bool(gp_delayed_voice_choice),\n                        reason="backend_delayed_voice_change",\n                    )\n                    st.success("✅ تم تحديث تنبيه الحالات المتأخرة فوراً.")\n                except Exception as exc:\n                    st.error(f"❌ تعذر تحديث تنبيه التأخير: {exc}")\n\n        if st.button("⚡ دفع أحدث البيانات إلى التلفزيون الآن", use_container_width=True, key="gp_push_tv_now"):\n            try:\n                gp_tv_control_request("POST", refresh_now=True, reason="manual_backend_push")\n                st.success("✅ تم إرسال أمر تحديث فوري إلى التلفزيون.")\n            except Exception as exc:\n                st.error(f"❌ تعذر إرسال أمر التحديث: {exc}")\n        st.caption("صوت الموظفين وتنبيه الحالات المتأخرة أصبحا مستقلين. أي حفظ جديد يرسل أيضاً أمر تحديث فوري للتلفزيون.")'''
    tools = sub_once(tools, old_ui, new_ui, "separate delayed voice UI", flags=re.S)

# =============================================================================
# FLASK: delayed voice state + true human acknowledgment event.
# =============================================================================
if "GP_HUMAN_ACK_AND_DELAYED_CONTROL_V1" not in flask:
    flask = replace_once(
        flask,
        '''    return {\n        "staff_voice_enabled": True,\n        "data_revision": "",\n''',
        '''    return {\n        "staff_voice_enabled": True,\n        # GP_HUMAN_ACK_AND_DELAYED_CONTROL_V1\n        "delayed_voice_enabled": True,\n        "data_revision": "",\n''',
        "TV control default delayed state",
    )
    flask = replace_once(
        flask,
        '''    state["staff_voice_enabled"] = bool(state.get("staff_voice_enabled", True))\n    state["data_revision"] = str(state.get("data_revision", "") or "")\n''',
        '''    state["staff_voice_enabled"] = bool(state.get("staff_voice_enabled", True))\n    state["delayed_voice_enabled"] = bool(state.get("delayed_voice_enabled", True))\n    state["data_revision"] = str(state.get("data_revision", "") or "")\n''',
        "TV control read delayed state",
    )
    flask = replace_once(
        flask,
        '''        if "staff_voice_enabled" in payload:\n            state["staff_voice_enabled"] = bool(payload.get("staff_voice_enabled"))\n        if payload.get("refresh_now"):\n''',
        '''        if "staff_voice_enabled" in payload:\n            state["staff_voice_enabled"] = bool(payload.get("staff_voice_enabled"))\n        if "delayed_voice_enabled" in payload:\n            state["delayed_voice_enabled"] = bool(payload.get("delayed_voice_enabled"))\n        if payload.get("refresh_now"):\n''',
        "TV control post delayed state",
    )
    flask = replace_once(
        flask,
        '''        "displayed_at": 0,\n        "audio_started_at": 0,\n''',
        '''        "displayed_at": 0,\n        "human_acknowledged_at": 0,\n        "audio_started_at": 0,\n''',
        "human acknowledgement initial timestamp",
    )
    flask = replace_once(
        flask,
        '''    if not announcement_id or event not in {"displayed", "audio_started", "audio_finished", "audio_failed"}:\n''',
        '''    if not announcement_id or event not in {"displayed", "human_acknowledged", "audio_started", "audio_finished", "audio_failed"}:\n''',
        "human acknowledgement accepted event",
    )
    flask = replace_once(
        flask,
        '''        "displayed": "displayed_at",\n        "audio_started": "audio_started_at",\n''',
        '''        "displayed": "displayed_at",\n        "human_acknowledged": "human_acknowledged_at",\n        "audio_started": "audio_started_at",\n''',
        "human acknowledgement event mapping",
    )
    flask = replace_once(
        flask,
        '''    if event in {"audio_started", "audio_finished", "audio_failed"} and not float(status.get("displayed_at", 0) or 0):\n''',
        '''    if event in {"human_acknowledged", "audio_started", "audio_finished", "audio_failed"} and not float(status.get("displayed_at", 0) or 0):\n''',
        "human acknowledgement implies display",
    )

# =============================================================================
# TV VISUALS: PC color parity, robust title/icon spacing, short browser tab title.
# =============================================================================
if "GP_PC_COLOR_PARITY_AND_TAB_FIX_V1" not in tv:
    tv = replace_once(
        tv,
        '''    <title>Service Workshop Tracker - Golden Palace</title>\n''',
        '''    <title>GP Workshop TV</title>\n    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='12' fill='%23071a2d'/%3E%3Ctext x='32' y='42' text-anchor='middle' font-size='28' font-family='Arial' font-weight='700' fill='%23f0bd08'%3EGP%3C/text%3E%3C/svg%3E">\n''',
        "short browser tab title and favicon",
    )
    parity_css = r'''
    <!-- GP_PC_COLOR_PARITY_AND_TAB_FIX_V1 -->
    <style id="gp-pc-color-parity-v1">
      /* Keep the TV palette identical to the approved PC dashboard screenshot. */
      body.main-view-body{background:#f3f5f8 !important;color:#172033 !important}
      body.main-view-body .workflow-card{border:1px solid rgba(255,255,255,.18) !important;color:#fff !important;overflow:hidden !important}
      body.main-view-body .workflow-card.progress{background:linear-gradient(135deg,#087be7 0%,#0751ad 100%) !important}
      body.main-view-body .workflow-card.collection{background:linear-gradient(135deg,#ff7a10 0%,#dc4b00 100%) !important}
      body.main-view-body .workflow-card.partner{background:linear-gradient(135deg,#6b2be5 0%,#3c1199 100%) !important}
      body.main-view-body .workflow-card.zero{background:linear-gradient(135deg,#1db74c 0%,#087e2c 100%) !important}
      body.main-view-body .workflow-card.collected{background:linear-gradient(135deg,#10a9b4 0%,#087985 100%) !important}
      body.main-view-body .workflow-card.partner_closed{background:linear-gradient(135deg,#f0bd08 0%,#c78b00 100%) !important}
      body.main-view-body .workflow-card .count,
      body.main-view-body .workflow-card h2,
      body.main-view-body .workflow-card .icon{color:#fff !important}
      body.main-view-body .workflow-card p,
      body.main-view-body .workflow-card .open-hint{color:rgba(255,255,255,.92) !important}
      /* Reserve a fixed corner for the icon so long translated titles never sit on it. */
      body.main-view-body .workflow-card .icon{position:absolute !important;top:15px !important;right:18px !important;left:auto !important;line-height:1 !important;z-index:2 !important;pointer-events:none}
      body.lang-ar.main-view-body .workflow-card .icon{right:18px !important;left:auto !important}
      body.main-view-body .workflow-card h2{max-width:calc(100% - 72px) !important;overflow-wrap:anywhere !important;line-height:1.15 !important}
      body.lang-ar.main-view-body .workflow-card h2{margin-right:0 !important;margin-left:auto !important}
      body.main-view-body .top-actions .action-btn,
      body.main-view-body .top-actions .pill,
      body.main-view-body .top-actions .language-select,
      body.main-view-body .top-actions .status-chip{display:inline-flex !important;align-items:center !important;justify-content:center !important;gap:7px !important;white-space:nowrap !important;line-height:1.15 !important}
      @media(max-width:1350px){
        body.main-view-body .workflow-card .icon{font-size:40px !important;top:12px !important;right:14px !important}
        body.main-view-body .workflow-card h2{max-width:calc(100% - 58px) !important;font-size:clamp(20px,1.9vw,30px) !important}
      }
    </style>
'''
    tv = replace_once(tv, "</head>\n", parity_css + "</head>\n", "PC color parity CSS")

# =============================================================================
# TV HUMAN ACK: button + real human confirmation, no auto-hide before response.
# =============================================================================
if "GP_HUMAN_ACK_BUTTON_V1" not in tv:
    tv = replace_once(
        tv,
        '''      .gp-manual-announcement-wave span{display:block;width:7px;border-radius:8px;background:#d5a62e;animation:gp-manual-wave .8s ease-in-out infinite alternate}.gp-manual-announcement-wave span:nth-child(1){height:14px}.gp-manual-announcement-wave span:nth-child(2){height:28px;animation-delay:.12s}.gp-manual-announcement-wave span:nth-child(3){height:40px;animation-delay:.24s}.gp-manual-announcement-wave span:nth-child(4){height:24px;animation-delay:.36s}.gp-manual-announcement-wave span:nth-child(5){height:34px;animation-delay:.48s}\n''',
        '''      .gp-manual-announcement-wave span{display:block;width:7px;border-radius:8px;background:#d5a62e;animation:gp-manual-wave .8s ease-in-out infinite alternate}.gp-manual-announcement-wave span:nth-child(1){height:14px}.gp-manual-announcement-wave span:nth-child(2){height:28px;animation-delay:.12s}.gp-manual-announcement-wave span:nth-child(3){height:40px;animation-delay:.24s}.gp-manual-announcement-wave span:nth-child(4){height:24px;animation-delay:.36s}.gp-manual-announcement-wave span:nth-child(5){height:34px;animation-delay:.48s}\n      /* GP_HUMAN_ACK_BUTTON_V1 */\n      .gp-manual-ack{margin:26px auto 0;min-width:min(620px,82vw);border:2px solid #86efac;border-radius:18px;background:linear-gradient(135deg,#22c55e,#15803d);color:#fff;padding:16px 24px;font-size:clamp(20px,1.7vw,30px);font-weight:950;box-shadow:0 12px 30px rgba(21,128,61,.32);cursor:pointer}\n      .gp-manual-ack:hover{filter:brightness(1.06)}.gp-manual-ack:disabled{cursor:default;opacity:.88}.gp-manual-ack.done{background:#166534;border-color:#bbf7d0}\n''',
        "human ack button CSS",
    )
    tv = replace_once(
        tv,
        '''    <div id="manualAnnouncementMeta" class="gp-manual-announcement-meta"></div>\n    <div class="gp-manual-announcement-wave" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>\n''',
        '''    <div id="manualAnnouncementMeta" class="gp-manual-announcement-meta"></div>\n    <div class="gp-manual-announcement-wave" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>\n    <button id="manualAnnouncementAck" class="gp-manual-ack" type="button">✅ تم الاطلاع · Seen / Acknowledge</button>\n''',
        "human ack button HTML",
    )

    old_ack_fn = '''    function gpAckManualAnnouncement(item, event) {\n        if (!item || !item.id || !event) return;\n        fetch(apiUrl('/api/manual-announcement/ack'), {\n            method: 'POST',\n            headers: {'Content-Type':'application/json'},\n            cache: 'no-store',\n            keepalive: true,\n            body: JSON.stringify({id:String(item.id), event:String(event), client:gpTvAckClient})\n        }).catch(() => {});\n    }\n'''
    new_ack_fn = '''    async function gpAckManualAnnouncement(item, event) {\n        if (!item || !item.id || !event) return false;\n        try {\n            const response = await fetch(apiUrl('/api/manual-announcement/ack'), {\n                method: 'POST',\n                headers: {'Content-Type':'application/json'},\n                cache: 'no-store',\n                keepalive: true,\n                body: JSON.stringify({id:String(item.id), event:String(event), client:gpTvAckClient})\n            });\n            return response.ok;\n        } catch (_) { return false; }\n    }\n'''
    tv = replace_once(tv, old_ack_fn, new_ack_fn, "async acknowledgment helper")

    tv = replace_once(
        tv,
        '''        const meta = document.getElementById('manualAnnouncementMeta');\n        if (card) {\n''',
        '''        const meta = document.getElementById('manualAnnouncementMeta');\n        const ackBtn = document.getElementById('manualAnnouncementAck');\n        if (ackBtn) {\n            ackBtn.disabled = false;\n            ackBtn.classList.remove('done');\n            ackBtn.textContent = lang === 'ar' ? '✅ تم الاطلاع · Seen / Acknowledge' : '✅ Seen / Acknowledge';\n            ackBtn.onclick = async () => {\n                ackBtn.disabled = true;\n                ackBtn.textContent = lang === 'ar' ? 'جاري إرسال التأكيد...' : 'Sending acknowledgment...';\n                const ok = await gpAckManualAnnouncement(item, 'human_acknowledged');\n                if (!ok) {\n                    ackBtn.disabled = false;\n                    ackBtn.textContent = lang === 'ar' ? '⚠️ تعذر التأكيد · اضغط مرة أخرى' : '⚠️ Could not confirm · Try again';\n                    return;\n                }\n                ackBtn.classList.add('done');\n                ackBtn.textContent = lang === 'ar' ? '✅ تم تأكيد الاطلاع' : '✅ Acknowledged';\n                setTimeout(() => gpHideManualAnnouncement(generation), 1400);\n            };\n        }\n        if (card) {\n''',
        "human ack button runtime",
    )

    # Keep the overlay available long enough for a real person to acknowledge it.
    tv = replace_once(
        tv,
        '''            }, 8000);\n            return;\n        }\n\n        setVoiceCaption(text, true);\n''',
        '''            }, 30000);\n            return;\n        }\n\n        setVoiceCaption(text, true);\n''',
        "silent overlay acknowledgment window",
    )
    tv = replace_once(
        tv,
        '''                setTimeout(() => gpHideManualAnnouncement(generation), 1600);\n''',
        '''                setTimeout(() => gpHideManualAnnouncement(generation), 30000);\n''',
        "voice overlay acknowledgment window",
    )
    tv = replace_once(
        tv,
        '''                    setTimeout(() => gpHideManualAnnouncement(generation), 9000);\n''',
        '''                    setTimeout(() => gpHideManualAnnouncement(generation), 30000);\n''',
        "blocked audio acknowledgment window",
    )
    tv = replace_once(
        tv,
        '''            setTimeout(() => gpHideManualAnnouncement(generation), 10000);\n''',
        '''            setTimeout(() => gpHideManualAnnouncement(generation), 30000);\n''',
        "failed audio acknowledgment window",
    )

# =============================================================================
# LIVE ANNOUNCEMENT VOICE: same approved Crisp voice as staff encouragement.
# The approved Crisp catalog is prerecorded; therefore the live voice is a
# consistent Crisp attention prompt while the exact sender/message stays visible
# until a human presses Acknowledge. This avoids the mismatched Lebanese TTS.
# =============================================================================
if "GP_LIVE_CRISP_VOICE_V1" not in tv:
    crisp_constants = '''\n    // GP_LIVE_CRISP_VOICE_V1\n    // Exact same approved Crisp voice family used by staff encouragement clips.\n    const GP_LIVE_CRISP_ALERT_AR = 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/3c4c9622-dca4-4698-9861-5c931dbbddd0.mp3';\n    const GP_LIVE_CRISP_ALERT_EN = 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/2ac78b6a-b049-4ef0-9839-fb4915f82db1.mp3';\n'''
    tv = replace_once(
        tv,
        '''    const GP_MANUAL_ANNOUNCEMENT_POLL_MS = 1000;\n''',
        '''    const GP_MANUAL_ANNOUNCEMENT_POLL_MS = 1000;\n''' + crisp_constants,
        "Crisp live alert constants",
    )
    old_dynamic = '''        setVoiceCaption(text, true);\n        try {\n            const voiceResponse = await fetch(apiUrl(`/api/followup-voice?live=1&lang=${encodeURIComponent(lang)}&sender=${encodeURIComponent(sender)}&text=${encodeURIComponent(text)}&t=${Date.now()}`), {cache:'no-store'});\n            if (!voiceResponse.ok || generation !== gpManualAnnouncementGeneration) throw new Error(`Voice API ${voiceResponse.status}`);\n            const track = await voiceResponse.json();\n            if (!track || !track.ok || !track.audio_url || generation !== gpManualAnnouncementGeneration) throw new Error('Voice track unavailable');\n\n            stopTeamVoiceAudio();\n            if (generation !== gpManualAnnouncementGeneration) return;\n            const audio = new Audio(apiUrl(track.audio_url));\n'''
    new_crisp = '''        setVoiceCaption(text, true);\n        try {\n            stopTeamVoiceAudio();\n            if (generation !== gpManualAnnouncementGeneration) return;\n            const crispUrl = lang === 'ar' ? GP_LIVE_CRISP_ALERT_AR : GP_LIVE_CRISP_ALERT_EN;\n            const audio = new Audio(crispUrl);\n'''
    tv = replace_once(tv, old_dynamic, new_crisp, "replace live Lebanese TTS with Crisp alert")

# =============================================================================
# TV delayed voice is independent of random staff encouragement voice.
# =============================================================================
if "GP_DELAYED_VOICE_RUNTIME_V1" not in tv:
    tv = replace_once(
        tv,
        '''    let gpTvControlRevision = null;\n    let gpRemoteStaffVoiceEnabled = null;\n''',
        '''    let gpTvControlRevision = null;\n    let gpRemoteStaffVoiceEnabled = null;\n    // GP_DELAYED_VOICE_RUNTIME_V1\n    let gpRemoteDelayedVoiceEnabled = true;\n''',
        "remote delayed voice state",
    )
    tv = replace_once(
        tv,
        '''            gpApplyRemoteStaffVoice(state.staff_voice_enabled !== false);\n\n            const revision = String(state.data_revision || '');\n''',
        '''            gpApplyRemoteStaffVoice(state.staff_voice_enabled !== false);\n            gpRemoteDelayedVoiceEnabled = state.delayed_voice_enabled !== false;\n\n            const revision = String(state.data_revision || '');\n''',
        "poll delayed voice state",
    )
    old_fu = '''    async function gpAnnounceFu(item,meta){if(!item||detailMode||!teamVoiceEnabled||document.hidden||teamVoicePlaying)return;const text=gpFuSpeech(item,meta),key=`${currentLanguage}|${item._gpKey}|${item.next_action||''}|${item.waiting_on||''}`;'''
    new_fu = '''    async function gpAnnounceFu(item,meta){if(!item||detailMode||document.hidden||teamVoicePlaying)return;const isDelayed=item._gpCategory==='followup_overdue';if(isDelayed?!gpRemoteDelayedVoiceEnabled:!teamVoiceEnabled)return;const text=gpFuSpeech(item,meta),key=`${currentLanguage}|${item._gpKey}|${item.next_action||''}|${item.waiting_on||''}`;'''
    tv = replace_once(tv, old_fu, new_fu, "independent delayed follow-up gate")

# =============================================================================
# MANAGEMENT PAGE: technical delivery != human acknowledgment.
# =============================================================================
if "GP_HUMAN_ACK_STATUS_UI_V1" not in announce:
    announce = replace_once(
        announce,
        '''<div class="steps"><span id="stepServer" class="step on">✓ Server</span><span id="stepDisplay" class="step">TV display</span>{% if published_voice_enabled %}<span id="stepAudio" class="step">Voice</span>{% endif %}</div>\n''',
        '''<div class="steps"><span id="stepServer" class="step on">✓ Server</span><span id="stepDisplay" class="step">TV received</span>{% if published_voice_enabled %}<span id="stepAudio" class="step">Voice alert</span>{% endif %}<span id="stepHuman" class="step">Seen / Acknowledge</span></div>\n''',
        "human ack status step",
    )
    announce = replace_once(
        announce,
        '''      <div class="privacy">“Sent” means the server accepted the announcement. “Observed on TV” appears only after an active TV browser reports that it displayed it.</div>\n''',
        '''      <div class="privacy">“Sent” means the server accepted it. “TV received” is technical delivery. “Seen / Acknowledged” appears only after a person presses the button on the workshop TV.</div>\n''',
        "human acknowledgment explanation",
    )
    announce = replace_once(
        announce,
        '''    const audioStep = document.getElementById('stepAudio');\n    let attempts = 0;\n''',
        '''    const audioStep = document.getElementById('stepAudio');\n    const humanStep = document.getElementById('stepHuman');\n    // GP_HUMAN_ACK_STATUS_UI_V1\n    let attempts = 0;\n''',
        "human ack JS element",
    )
    announce = replace_once(
        announce,
        '''            const displayed = Number(s.displayed_at || 0);\n            const started = Number(s.audio_started_at || 0);\n''',
        '''            const displayed = Number(s.displayed_at || 0);\n            const acknowledged = Number(s.human_acknowledged_at || 0);\n            const started = Number(s.audio_started_at || 0);\n''',
        "human ack timestamp JS",
    )

    old_status = r'''            if \(displayed\) \{\n              box\.classList\.add\('seen'\);\n              displayStep\.classList\.add\('on'\);\n              title\.textContent = '✅ تمت مشاهدة الإعلان على شاشة التلفزيون · Observed on TV';\n              text\.textContent = `أكدت شاشة التلفزيون عرض الإعلان\$\{fmt\(displayed\) \? ` الساعة \$\{fmt\(displayed\)\}` : ''\}\.`;\n              if \(voiceEnabled && started && audioStep\) \{\n                audioStep\.classList\.add\('on'\);\n                audioStep\.textContent = completed \? '✓ Voice finished' : '✓ Voice started';\n              \}\n              if \(voiceEnabled && failed && audioStep\) \{\n                audioStep\.classList\.remove\('on'\);\n                audioStep\.classList\.add\('bad'\);\n                audioStep\.textContent = 'Voice failed';\n                text\.textContent \+= ' ظهر الإعلان بصرياً لكن تشغيل الصوت لم يكتمل\.';\n              \}\n              meta\.textContent = s\.tv_client \? `TV acknowledgment: \$\{s\.tv_client\}` : 'TV acknowledgment received';\n              if \(!voiceEnabled \|\| completed \|\| failed\) finished = true;\n            \}'''
    new_status = '''            if (displayed) {\n              displayStep.classList.add('on');\n              title.textContent = '📺 وصل الإعلان إلى شاشة التلفزيون · Delivered to TV';\n              text.textContent = `الشاشة استلمت وعرضت الإعلان${fmt(displayed) ? ` الساعة ${fmt(displayed)}` : ''}. بانتظار ضغط الموظف على زر تم الاطلاع.`;\n              if (voiceEnabled && started && audioStep) {\n                audioStep.classList.add('on');\n                audioStep.textContent = completed ? '✓ Voice alert finished' : '✓ Voice alert started';\n              }\n              if (voiceEnabled && failed && audioStep) {\n                audioStep.classList.remove('on');\n                audioStep.classList.add('bad');\n                audioStep.textContent = 'Voice alert failed';\n                text.textContent += ' وصل الإعلان بصرياً لكن التنبيه الصوتي لم يكتمل.';\n              }\n              meta.textContent = s.tv_client ? `TV: ${s.tv_client}` : 'TV delivery confirmed';\n            }\n            if (acknowledged) {\n              box.classList.remove('fail');\n              box.classList.add('seen');\n              humanStep.classList.add('on');\n              humanStep.textContent = '✓ Seen / Acknowledged';\n              title.textContent = '✅ تم تأكيد الاطلاع · Seen / Acknowledged';\n              text.textContent = `تم ضغط زر الاطلاع على شاشة الورشة${fmt(acknowledged) ? ` الساعة ${fmt(acknowledged)}` : ''}.`;\n              finished = true;\n            }'''
    announce = sub_once(announce, old_status, new_status, "management human acknowledgment state", flags=re.S)

    old_timeout = '''      if (!finished && attempts >= 20) {\n        box.classList.add('fail');\n        title.textContent = '⚠️ لم يصل تأكيد من التلفزيون · No TV confirmation';\n        text.textContent = 'الخادم استلم الإعلان، لكن لم تؤكد أي شاشة عرضه خلال 20 ثانية. قد تكون شاشة الورشة مطفأة أو غير متصلة.';\n        finished = true;\n      }\n'''
    new_timeout = '''      if (!finished && attempts >= 45) {\n        if (displayStep && displayStep.classList.contains('on')) {\n          title.textContent = '⚠️ وصل للتلفزيون ولم يتم تأكيد الاطلاع';\n          text.textContent = 'التلفزيون عرض الإعلان، لكن لم يضغط أحد زر Seen / Acknowledge خلال 45 ثانية.';\n        } else {\n          box.classList.add('fail');\n          title.textContent = '⚠️ لم يصل تأكيد من التلفزيون · No TV confirmation';\n          text.textContent = 'الخادم استلم الإعلان، لكن لم تؤكد أي شاشة عرضه خلال 45 ثانية. قد تكون شاشة الورشة مطفأة أو غير متصلة.';\n        }\n        finished = true;\n      }\n'''
    announce = replace_once(announce, old_timeout, new_timeout, "human ack timeout state")

# Write outputs.
tools_path.write_text(tools, encoding="utf-8")
flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
announce_path.write_text(announce, encoding="utf-8")
print("Human acknowledgement, Crisp live alert, color parity, and delayed voice control patched")
