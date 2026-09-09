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
# Streamlit backend: manual announcement publisher inside Follow-Up Center.
# -----------------------------------------------------------------------------
if "GP_MANUAL_TV_ANNOUNCEMENT_V1" not in tools:
    tools_anchor = 'IMGBB_API_KEY = get_runtime_secret("IMGBB_API_KEY")\n'
    tools_insert = r'''

# GP_MANUAL_TV_ANNOUNCEMENT_V1
GP_TV_BACKEND_URL = get_runtime_secret("GP_TV_BACKEND_URL") or "https://golden-palace-service-tracker.onrender.com"
GP_TV_ANNOUNCEMENT_KEY = get_runtime_secret("GP_TV_ANNOUNCEMENT_KEY")


def publish_manual_tv_announcement(text, language="auto", published_by=""):
    message = re.sub(r"\s+", " ", str(text or "")).strip()
    if not message:
        raise ValueError("Announcement text is empty")
    payload = {
        "text": message[:700],
        "lang": str(language or "auto").strip().lower(),
        "published_by": str(published_by or "").strip(),
    }
    headers = {"Accept": "application/json"}
    if GP_TV_ANNOUNCEMENT_KEY:
        headers["X-GP-Announcement-Key"] = GP_TV_ANNOUNCEMENT_KEY
    response = requests.post(
        f"{GP_TV_BACKEND_URL.rstrip('/')}/api/manual-announcement",
        json=payload,
        headers=headers,
        timeout=(5, 15),
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error") or "TV announcement publish failed")
    return data
'''
    tools = replace_once(tools, tools_anchor, tools_anchor + tools_insert, "tools announcement helper")

if "GP_MANUAL_TV_ANNOUNCEMENT_UI_V1" not in tools:
    followup_anchor = "elif st.session_state['current_module'] == 'FollowUp':\n    gp_render_module_header('FollowUp')\n    followup_df = normalize_followup_dataframe(followup_df)\n"
    followup_replacement = r'''elif st.session_state['current_module'] == 'FollowUp':
    gp_render_module_header('FollowUp')

    # GP_MANUAL_TV_ANNOUNCEMENT_UI_V1
    with st.expander("📣 إعلان مباشر إلى شاشة الورشة (Live TV Announcement)", expanded=False):
        st.caption("اكتب المهمة أو الرسالة هنا. ستظهر على شاشة التلفزيون فوراً وتُقرأ بنفس صوت إعلانات المتابعة الحالي.")
        with st.form("gp_manual_tv_announcement_form", clear_on_submit=True):
            manual_announcement_text = st.text_area(
                "نص الإعلان (Announcement text)",
                placeholder="مثال: أبو عدنان، الرجاء إنهاء فحص الجهاز S125 قبل الساعة 2.",
                height=110,
            )
            lang_choice = st.selectbox(
                "لغة الصوت (Voice language)",
                ["auto", "ar", "en"],
                format_func=lambda x: {"auto": "تلقائي / Auto", "ar": "العربية", "en": "English"}[x],
            )
            manual_announcement_submit = st.form_submit_button("📡 نشر الآن على التلفزيون (Publish Now)", use_container_width=True)
        if manual_announcement_submit:
            if not str(manual_announcement_text or "").strip():
                st.warning("يرجى كتابة نص الإعلان أولاً.")
            else:
                try:
                    with golden_loading("جارٍ نشر الإعلان إلى شاشة الورشة..."):
                        published = publish_manual_tv_announcement(
                            manual_announcement_text,
                            language=lang_choice,
                            published_by=current_user,
                        )
                    st.success(f"✅ تم نشر الإعلان إلى التلفزيون · {published.get('id', '')}")
                except Exception as exc:
                    st.error(f"❌ تعذر نشر الإعلان إلى التلفزيون: {exc}")

    followup_df = normalize_followup_dataframe(followup_df)
'''
    tools = replace_once(tools, followup_anchor, followup_replacement, "Follow-Up announcement UI")

# -----------------------------------------------------------------------------
# Flask backend: cross-worker latest-message mailbox. Voice itself is intentionally
# NOT duplicated here; the TV calls the existing /api/followup-voice endpoint.
# -----------------------------------------------------------------------------
if "GP_MANUAL_TV_ANNOUNCEMENT_API_V1" not in flask:
    flask_anchor = '@app.route("/api/voice-audio/<token>.mp3")\ndef api_voice_audio(token):\n'
    flask_insert = r'''
# GP_MANUAL_TV_ANNOUNCEMENT_API_V1
GP_MANUAL_ANNOUNCEMENT_FILE = os.path.join(tempfile.gettempdir(), "gp_manual_tv_announcement_v1.json")
GP_MANUAL_ANNOUNCEMENT_LOCK = threading.RLock()
GP_TV_ANNOUNCEMENT_KEY = os.environ.get("GP_TV_ANNOUNCEMENT_KEY", "").strip()


def gp_detect_announcement_language(text, requested="auto"):
    requested = str(requested or "auto").lower().strip()
    if requested in {"ar", "en"}:
        return requested
    return "ar" if re.search(r"[\u0600-\u06ff]", str(text or "")) else "en"


def gp_read_manual_announcement():
    try:
        with GP_MANUAL_ANNOUNCEMENT_LOCK:
            if not os.path.exists(GP_MANUAL_ANNOUNCEMENT_FILE):
                return None
            with open(GP_MANUAL_ANNOUNCEMENT_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        if float(data.get("expires_at", 0) or 0) < time.time():
            return None
        return data
    except Exception as exc:
        print("Manual announcement read error:", repr(exc))
        return None


def gp_write_manual_announcement(data):
    temp_path = f"{GP_MANUAL_ANNOUNCEMENT_FILE}.{os.getpid()}.tmp"
    with GP_MANUAL_ANNOUNCEMENT_LOCK:
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False)
            os.replace(temp_path, GP_MANUAL_ANNOUNCEMENT_FILE)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass


def gp_manual_announcement_authorized():
    if not GP_TV_ANNOUNCEMENT_KEY:
        return True
    return request.headers.get("X-GP-Announcement-Key", "").strip() == GP_TV_ANNOUNCEMENT_KEY


@app.route("/api/manual-announcement", methods=["POST", "OPTIONS"])
def api_manual_announcement():
    if request.method == "OPTIONS":
        return ("", 204)
    if not gp_manual_announcement_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 403
    payload = request.get_json(silent=True) or {}
    text = re.sub(r"\s+", " ", str(payload.get("text", ""))).strip()
    if not text:
        return jsonify({"ok": False, "error": "missing_text"}), 400
    text = text[:700]
    lang = gp_detect_announcement_language(text, payload.get("lang", "auto"))
    now = time.time()
    announcement_id = f"{int(now * 1000)}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:8]}"
    announcement = {
        "id": announcement_id,
        "text": text,
        "lang": lang,
        "published_by": re.sub(r"\s+", " ", str(payload.get("published_by", ""))).strip()[:80],
        "created_at": now,
        "expires_at": now + 600,
    }
    gp_write_manual_announcement(announcement)
    response = jsonify({"ok": True, **announcement})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.route("/api/manual-announcement/latest")
def api_manual_announcement_latest():
    announcement = gp_read_manual_announcement()
    after = str(request.args.get("after", "")).strip()
    if not announcement or (after and after == str(announcement.get("id", ""))):
        response = jsonify({"ok": True, "announcement": None})
    else:
        response = jsonify({"ok": True, "announcement": announcement})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


'''
    flask = replace_once(flask, flask_anchor, flask_insert + flask_anchor, "manual announcement API")

# -----------------------------------------------------------------------------
# TV: urgent overlay + 1-second mailbox polling + exact existing follow-up voice.
# -----------------------------------------------------------------------------
if "GP_MANUAL_TV_ANNOUNCEMENT_UI_V1" not in tv:
    head_anchor = "</head>"
    head_insert = r'''
    <!-- GP_MANUAL_TV_ANNOUNCEMENT_UI_V1 -->
    <style id="gp-manual-tv-announcement-v1">
      .gp-manual-announcement-overlay{position:fixed;inset:0;z-index:250000;display:none;align-items:center;justify-content:center;padding:4vw;background:rgba(2,10,19,.91);backdrop-filter:blur(7px)}
      .gp-manual-announcement-overlay.show{display:flex}
      .gp-manual-announcement-card{width:min(1380px,94vw);min-height:420px;border:2px solid #d5a62e;border-radius:30px;background:linear-gradient(145deg,#071a2d 0%,#0b2741 58%,#102f4b 100%);box-shadow:0 30px 90px rgba(0,0,0,.55);color:#fff;padding:38px 48px;display:flex;flex-direction:column;justify-content:center;text-align:center;position:relative;overflow:hidden}
      .gp-manual-announcement-card::before{content:"";position:absolute;left:0;right:0;top:0;height:7px;background:linear-gradient(90deg,#8e6a13,#f1d16c,#8e6a13)}
      .gp-manual-announcement-label{font-size:clamp(18px,1.5vw,26px);font-weight:950;color:#f1d16c;letter-spacing:.04em;margin-bottom:18px}
      .gp-manual-announcement-text{font-size:clamp(34px,3.4vw,62px);line-height:1.32;font-weight:950;overflow-wrap:anywhere;text-wrap:balance}
      .gp-manual-announcement-meta{margin-top:24px;color:#a9bdd0;font-size:clamp(13px,1vw,18px);font-weight:750}
      .gp-manual-announcement-wave{display:flex;justify-content:center;align-items:flex-end;gap:7px;height:42px;margin-top:22px}
      .gp-manual-announcement-wave span{display:block;width:7px;border-radius:8px;background:#d5a62e;animation:gp-manual-wave .8s ease-in-out infinite alternate}.gp-manual-announcement-wave span:nth-child(1){height:14px}.gp-manual-announcement-wave span:nth-child(2){height:28px;animation-delay:.12s}.gp-manual-announcement-wave span:nth-child(3){height:40px;animation-delay:.24s}.gp-manual-announcement-wave span:nth-child(4){height:24px;animation-delay:.36s}.gp-manual-announcement-wave span:nth-child(5){height:34px;animation-delay:.48s}
      @keyframes gp-manual-wave{from{transform:scaleY(.45);opacity:.55}to{transform:scaleY(1);opacity:1}}
    </style>
'''
    tv = replace_once(tv, head_anchor, head_insert + head_anchor, "manual announcement TV style")

    body_anchor = '<div id="voiceCaption" class="voice-caption" aria-live="polite"></div>\n'
    body_insert = r'''
<div id="manualAnnouncementOverlay" class="gp-manual-announcement-overlay" role="alert" aria-live="assertive">
  <div id="manualAnnouncementCard" class="gp-manual-announcement-card">
    <div id="manualAnnouncementLabel" class="gp-manual-announcement-label">📣 LIVE ANNOUNCEMENT</div>
    <div id="manualAnnouncementText" class="gp-manual-announcement-text"></div>
    <div id="manualAnnouncementMeta" class="gp-manual-announcement-meta"></div>
    <div class="gp-manual-announcement-wave" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
  </div>
</div>
'''
    tv = replace_once(tv, body_anchor, body_anchor + body_insert, "manual announcement TV overlay")

    js_anchor = "    async function refreshDashboard(force=false) {\n"
    js_insert = r'''
    // GP_MANUAL_TV_ANNOUNCEMENT_RUNTIME_V1
    const GP_MANUAL_ANNOUNCEMENT_POLL_MS = 1000;
    const GP_MANUAL_ANNOUNCEMENT_STORAGE_KEY = 'gpManualAnnouncementLastIdV1';
    let gpManualAnnouncementLastId = (() => { try { return localStorage.getItem(GP_MANUAL_ANNOUNCEMENT_STORAGE_KEY) || ''; } catch (_) { return ''; } })();
    let gpManualAnnouncementPollInFlight = false;
    let gpManualAnnouncementGeneration = 0;

    function gpHideManualAnnouncement(generation) {
        if (generation != null && generation !== gpManualAnnouncementGeneration) return;
        const overlay = document.getElementById('manualAnnouncementOverlay');
        if (overlay) overlay.classList.remove('show');
    }

    async function gpPlayManualAnnouncement(item) {
        if (!item || detailMode) return;
        const generation = ++gpManualAnnouncementGeneration;
        const lang = item.lang === 'en' ? 'en' : 'ar';
        const text = String(item.text || '').trim();
        if (!text) return;

        stopTeamVoiceAudio();
        teamVoicePlaying = true;

        const overlay = document.getElementById('manualAnnouncementOverlay');
        const card = document.getElementById('manualAnnouncementCard');
        const label = document.getElementById('manualAnnouncementLabel');
        const textEl = document.getElementById('manualAnnouncementText');
        const meta = document.getElementById('manualAnnouncementMeta');
        if (card) {
            card.dir = lang === 'ar' ? 'rtl' : 'ltr';
            card.style.textAlign = 'center';
        }
        if (label) label.textContent = lang === 'ar' ? '📣 إعلان مباشر من الإدارة' : '📣 LIVE MANAGEMENT ANNOUNCEMENT';
        if (textEl) textEl.textContent = text;
        if (meta) {
            const by = String(item.published_by || '').trim();
            meta.textContent = by ? (lang === 'ar' ? `نُشر بواسطة: ${by}` : `Published by: ${by}`) : 'Golden Palace';
        }
        if (overlay) overlay.classList.add('show');
        setVoiceCaption(text, true);

        try {
            const voiceResponse = await fetch(apiUrl(`/api/followup-voice?lang=${encodeURIComponent(lang)}&text=${encodeURIComponent(text)}&t=${Date.now()}`), {cache:'no-store'});
            if (!voiceResponse.ok || generation !== gpManualAnnouncementGeneration) throw new Error(`Voice API ${voiceResponse.status}`);
            const track = await voiceResponse.json();
            if (!track || !track.ok || !track.audio_url || generation !== gpManualAnnouncementGeneration) throw new Error('Voice track unavailable');

            stopTeamVoiceAudio();
            if (generation !== gpManualAnnouncementGeneration) return;
            const audio = new Audio(apiUrl(track.audio_url));
            audio.preload = 'auto';
            audio.volume = TEAM_VOICE_VOLUME;
            teamVoiceAudio = audio;
            teamVoicePlaying = true;
            setVoiceCaption(text, true);

            const finish = () => {
                if (generation !== gpManualAnnouncementGeneration) return;
                if (teamVoiceAudio === audio) teamVoiceAudio = null;
                teamVoicePlaying = false;
                setVoiceCaption('', false);
                setTimeout(() => gpHideManualAnnouncement(generation), 1600);
            };
            audio.addEventListener('ended', finish, {once:true});
            audio.addEventListener('error', finish, {once:true});
            const promise = audio.play();
            if (promise && typeof promise.catch === 'function') {
                promise.catch(() => {
                    if (generation !== gpManualAnnouncementGeneration) return;
                    teamVoicePlaying = false;
                    setVoiceCaption('', false);
                    showToast(tr('audioBlocked'), 7000);
                    setTimeout(() => gpHideManualAnnouncement(generation), 9000);
                });
            }
        } catch (err) {
            if (generation !== gpManualAnnouncementGeneration) return;
            teamVoicePlaying = false;
            setVoiceCaption('', false);
            console.warn('Manual TV announcement voice failed:', err);
            setTimeout(() => gpHideManualAnnouncement(generation), 10000);
        }
    }

    async function gpPollManualAnnouncement() {
        if (detailMode || gpManualAnnouncementPollInFlight || document.hidden) return;
        gpManualAnnouncementPollInFlight = true;
        try {
            const response = await fetch(apiUrl(`/api/manual-announcement/latest?after=${encodeURIComponent(gpManualAnnouncementLastId)}&t=${Date.now()}`), {cache:'no-store'});
            if (!response.ok) return;
            const payload = await response.json();
            const item = payload && payload.announcement;
            if (!item || !item.id || String(item.id) === gpManualAnnouncementLastId) return;
            gpManualAnnouncementLastId = String(item.id);
            try { localStorage.setItem(GP_MANUAL_ANNOUNCEMENT_STORAGE_KEY, gpManualAnnouncementLastId); } catch (_) {}
            gpPlayManualAnnouncement(item);
        } catch (_) {
            // Manual announcements are independent from dashboard refresh.
        } finally {
            gpManualAnnouncementPollInFlight = false;
        }
    }

'''
    tv = replace_once(tv, js_anchor, js_insert + js_anchor, "manual announcement TV runtime")

    startup_anchor = "    setTimeout(() => { try { initialiseTeamVoice(); } catch (_) {} }, 800);\n    setInterval(() => refreshDashboard(false), 15000);\n"
    startup_replacement = "    setTimeout(() => { try { initialiseTeamVoice(); } catch (_) {} }, 800);\n    setTimeout(gpPollManualAnnouncement, 500);\n    setInterval(gpPollManualAnnouncement, GP_MANUAL_ANNOUNCEMENT_POLL_MS);\n    setInterval(() => refreshDashboard(false), 15000);\n"
    tv = replace_once(tv, startup_anchor, startup_replacement, "manual announcement startup polling")

tools_path.write_text(tools, encoding="utf-8")
flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
print("Manual TV announcement feature patched")
