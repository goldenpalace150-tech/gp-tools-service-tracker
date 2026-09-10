from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing patch target: {label}")
    return text.replace(old, new, 1)


flask_path = Path("flask_app.py")
tv_path = Path("templates/tv.html")
flask = flask_path.read_text(encoding="utf-8")
tv = tv_path.read_text(encoding="utf-8")

# -----------------------------------------------------------------------------
# Flask: live-announcement speech preparation + durable short-lived delivery ACK.
# -----------------------------------------------------------------------------
if "GP_ANNOUNCEMENT_DELIVERY_ACK_V1" not in flask:
    voice_anchor = '''# GP_FOLLOWUP_VOICE_V2\n@app.route("/api/followup-voice")\ndef api_followup_voice():\n    lang = "en" if str(request.args.get("lang", "ar")).lower().startswith("en") else "ar"\n    text = re.sub(r"\\s+", " ", str(request.args.get("text", ""))).strip()\n    if not text:\n        return jsonify({"ok": False, "error": "missing_text"}), 400\n    text = text[:500]\n    voice = GP_AR_VOICE if lang == "ar" else GP_EN_VOICE\n    try:\n        token, _ = gp_ensure_voice_file(text, voice, "-3%" if lang == "ar" else "-5%", "+1Hz")\n    except Exception as exc:\n        print("FollowUp voice generation error:", repr(exc))\n        return jsonify({"ok": False, "error": "voice_generation_failed"}), 503\n    return jsonify({"ok": True, "text": text, "lang": lang, "voice": voice, "audio_url": f"/api/voice-audio/{token}.mp3"})\n'''
    voice_replacement = r'''# GP_ANNOUNCEMENT_DELIVERY_ACK_V1
GP_LIVE_AR_TASHKEEL = [
    ("أبو عدنان", "أَبُو عَدْنان"),
    ("أبو آدم", "أَبُو آدَم"),
    ("أبو نقطة", "أَبُو نُقْطَة"),
    ("أبو غسان", "أَبُو غَسّان"),
    ("عمر", "عُمَر"),
    ("حازم", "حازِم"),
    ("حريري", "حَريري"),
    ("الإدارة", "الإِدارَة"),
    ("إعلان", "إِعْلان"),
    ("الرجاء", "الرَّجاء"),
    ("يرجى", "يُرْجى"),
    ("إنهاء", "إِنْهاء"),
    ("الصيانة", "الصِّيانَة"),
    ("الجهاز", "الجِهاز"),
    ("الأجهزة", "الأَجْهِزَة"),
    ("الفحص", "الفَحْص"),
    ("فحص", "فَحْص"),
    ("الساعة", "السّاعَة"),
    ("اليوم", "اليَوْم"),
    ("بكرا", "بُكْرا"),
    ("غدا", "غَدًا"),
    ("غداً", "غَدًا"),
    ("قبل", "قَبْل"),
    ("بعد", "بَعْد"),
    ("شكرا", "شُكْرًا"),
    ("شكراً", "شُكْرًا"),
]


def gp_live_arabic_tashkeel(text):
    value = str(text or "")
    # Targeted vocalisation improves the Lebanese/Syrian neural voice without
    # rewriting management's visible message or risking aggressive full diacritisation.
    for plain, vocalized in sorted(GP_LIVE_AR_TASHKEEL, key=lambda item: len(item[0]), reverse=True):
        pattern = rf"(?<![\\u0621-\\u064A]){re.escape(plain)}(?![\\u0621-\\u064A])"
        value = re.sub(pattern, vocalized, value)
    return value


def gp_prepare_live_announcement_speech(text, sender, lang):
    message = re.sub(r"\\s+", " ", str(text or "")).strip()
    sender = re.sub(r"\\s+", " ", str(sender or "")).strip()[:80]
    if lang == "ar":
        prefix = f"إِعْلان مِنْ {sender}." if sender else "إِعْلان مِنَ الإِدارَة."
        return gp_live_arabic_tashkeel(f"{prefix} {message}")[:850]
    prefix = f"Announcement from {sender}." if sender else "Management announcement."
    return f"{prefix} {message}"[:850]


# GP_FOLLOWUP_VOICE_V2
@app.route("/api/followup-voice")
def api_followup_voice():
    lang = "en" if str(request.args.get("lang", "ar")).lower().startswith("en") else "ar"
    raw_text = re.sub(r"\s+", " ", str(request.args.get("text", ""))).strip()
    if not raw_text:
        return jsonify({"ok": False, "error": "missing_text"}), 400
    is_live = str(request.args.get("live", "0")).strip() == "1"
    sender = re.sub(r"\s+", " ", str(request.args.get("sender", ""))).strip()[:80]
    if is_live:
        text = gp_prepare_live_announcement_speech(raw_text[:700], sender, lang)
        rate = "-7%" if lang == "ar" else "-5%"
        pitch = "0Hz" if lang == "ar" else "+1Hz"
    else:
        text = raw_text[:500]
        rate = "-3%" if lang == "ar" else "-5%"
        pitch = "+1Hz"
    voice = GP_AR_VOICE if lang == "ar" else GP_EN_VOICE
    try:
        token, _ = gp_ensure_voice_file(text, voice, rate, pitch)
    except Exception as exc:
        print("FollowUp voice generation error:", repr(exc))
        return jsonify({"ok": False, "error": "voice_generation_failed"}), 503
    return jsonify({"ok": True, "text": text, "lang": lang, "voice": voice, "audio_url": f"/api/voice-audio/{token}.mp3"})
'''
    flask = replace_once(flask, voice_anchor, voice_replacement, "live announcement TTS")

    status_anchor = '''GP_TV_ANNOUNCEMENT_KEY = os.environ.get("GP_TV_ANNOUNCEMENT_KEY", "").strip()\n\n\ndef gp_detect_announcement_language(text, requested="auto"):\n'''
    status_insert = r'''GP_TV_ANNOUNCEMENT_KEY = os.environ.get("GP_TV_ANNOUNCEMENT_KEY", "").strip()

# Per-announcement delivery receipts are separate from the latest-message mailbox,
# so a sender can still see whether their own announcement reached the TV.
GP_MANUAL_DELIVERY_DIR = os.path.join(tempfile.gettempdir(), "gp_manual_delivery_v1")
os.makedirs(GP_MANUAL_DELIVERY_DIR, exist_ok=True)


def gp_manual_delivery_path(announcement_id):
    safe_id = str(announcement_id or "").strip()
    token = hashlib.sha256(safe_id.encode("utf-8")).hexdigest()
    return os.path.join(GP_MANUAL_DELIVERY_DIR, f"{token}.json")


def gp_write_manual_delivery_status(status):
    announcement_id = str(status.get("id", "") or "").strip()
    if not announcement_id:
        return
    path = gp_manual_delivery_path(announcement_id)
    temp_path = f"{path}.{os.getpid()}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(status, handle, ensure_ascii=False)
    os.replace(temp_path, path)


def gp_read_manual_delivery_status(announcement_id):
    announcement_id = str(announcement_id or "").strip()
    if not announcement_id:
        return None
    try:
        path = gp_manual_delivery_path(announcement_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            status = json.load(handle)
        if str(status.get("id", "")) != announcement_id:
            return None
        # Keep receipts useful for one day; Render restarts may clear /tmp earlier.
        if time.time() - float(status.get("server_accepted_at", 0) or 0) > 86400:
            return None
        return status
    except Exception as exc:
        print("Manual announcement delivery read error:", repr(exc))
        return None


def gp_init_manual_delivery_status(announcement):
    now = time.time()
    status = {
        "id": str(announcement.get("id", "")),
        "server_accepted_at": float(announcement.get("created_at", now) or now),
        "displayed_at": 0,
        "audio_started_at": 0,
        "audio_finished_at": 0,
        "audio_failed_at": 0,
        "last_tv_ack_at": 0,
        "voice_enabled": bool(announcement.get("voice_enabled", True)),
        "published_by": str(announcement.get("published_by", "") or "")[:80],
    }
    gp_write_manual_delivery_status(status)
    return status


def gp_detect_announcement_language(text, requested="auto"):
'''
    flask = replace_once(flask, status_anchor, status_insert, "delivery status helpers")

    context_anchor = '''        "form_voice_enabled": True,\n        "published_text": "",\n    }\n'''
    context_replacement = '''        "form_voice_enabled": True,\n        "published_text": "",\n        "published_id": "",\n        "published_voice_enabled": False,\n        "published_sender": "",\n    }\n'''
    flask = replace_once(flask, context_anchor, context_replacement, "management status context")

    management_publish_anchor = '''        gp_write_manual_announcement(announcement)\n        context.update({\n            "success": True,\n            "form_text": "",\n            "published_text": message,\n        })\n'''
    management_publish_replacement = '''        gp_write_manual_announcement(announcement)\n        gp_init_manual_delivery_status(announcement)\n        context.update({\n            "success": True,\n            "form_text": "",\n            "published_text": message,\n            "published_id": announcement_id,\n            "published_voice_enabled": voice_enabled,\n            "published_sender": published_by,\n        })\n'''
    flask = replace_once(flask, management_publish_anchor, management_publish_replacement, "management delivery receipt init")

    api_publish_anchor = '''    gp_write_manual_announcement(announcement)\n    response = jsonify({"ok": True, **announcement})\n'''
    api_publish_replacement = '''    gp_write_manual_announcement(announcement)\n    gp_init_manual_delivery_status(announcement)\n    response = jsonify({"ok": True, **announcement})\n'''
    flask = replace_once(flask, api_publish_anchor, api_publish_replacement, "API delivery receipt init")

    latest_anchor = '''@app.route("/api/manual-announcement/latest")\ndef api_manual_announcement_latest():\n'''
    latest_insert = r'''
@app.route("/api/manual-announcement/status")
def api_manual_announcement_status():
    announcement_id = str(request.args.get("id", "") or "").strip()
    if not announcement_id:
        return jsonify({"ok": False, "error": "missing_id"}), 400
    status = gp_read_manual_delivery_status(announcement_id)
    response = jsonify({"ok": True, "found": bool(status), "status": status})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@app.route("/api/manual-announcement/ack", methods=["POST", "OPTIONS"])
def api_manual_announcement_ack():
    if request.method == "OPTIONS":
        return ("", 204)
    payload = request.get_json(silent=True) or {}
    announcement_id = str(payload.get("id", "") or "").strip()
    event = str(payload.get("event", "") or "").strip().lower()
    if not announcement_id or event not in {"displayed", "audio_started", "audio_finished", "audio_failed"}:
        return jsonify({"ok": False, "error": "invalid_ack"}), 400

    status = gp_read_manual_delivery_status(announcement_id)
    if status is None:
        current = gp_read_manual_announcement()
        if not current or str(current.get("id", "")) != announcement_id:
            return jsonify({"ok": False, "error": "unknown_announcement"}), 404
        status = gp_init_manual_delivery_status(current)

    now = time.time()
    key = {
        "displayed": "displayed_at",
        "audio_started": "audio_started_at",
        "audio_finished": "audio_finished_at",
        "audio_failed": "audio_failed_at",
    }[event]
    if not float(status.get(key, 0) or 0):
        status[key] = now
    if event in {"audio_started", "audio_finished", "audio_failed"} and not float(status.get("displayed_at", 0) or 0):
        status["displayed_at"] = now
    status["last_tv_ack_at"] = now
    status["tv_client"] = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("client", "")))[:64]
    gp_write_manual_delivery_status(status)
    response = jsonify({"ok": True, "status": status})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


'''
    flask = replace_once(flask, latest_anchor, latest_insert + latest_anchor, "delivery ACK endpoints")

# -----------------------------------------------------------------------------
# TV: send positive receipt only when the visible TV actually displays the card.
# -----------------------------------------------------------------------------
if "GP_ANNOUNCEMENT_DELIVERY_ACK_V1" not in tv:
    play_anchor = '''    async function gpPlayManualAnnouncement(item) {\n        if (!item || detailMode) return;\n        const generation = ++gpManualAnnouncementGeneration;\n        const lang = item.lang === 'en' ? 'en' : 'ar';\n        const text = String(item.text || '').trim();\n        // GP_MANUAL_TV_VOICE_TOGGLE_V1\n        const voiceEnabled = item.voice_enabled !== false;\n'''
    play_replacement = r'''    // GP_ANNOUNCEMENT_DELIVERY_ACK_V1
    const GP_TV_ACK_CLIENT_KEY = 'gpTvAckClientV1';
    let gpTvAckClient = (() => {
        try {
            let value = localStorage.getItem(GP_TV_ACK_CLIENT_KEY) || '';
            if (!value) {
                value = `tv-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;
                localStorage.setItem(GP_TV_ACK_CLIENT_KEY, value);
            }
            return value;
        } catch (_) { return 'tv-browser'; }
    })();

    function gpAckManualAnnouncement(item, event) {
        if (!item || !item.id || !event) return;
        fetch(apiUrl('/api/manual-announcement/ack'), {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            cache: 'no-store',
            keepalive: true,
            body: JSON.stringify({id:String(item.id), event:String(event), client:gpTvAckClient})
        }).catch(() => {});
    }

    async function gpPlayManualAnnouncement(item) {
        if (!item || detailMode || document.hidden) return;
        const generation = ++gpManualAnnouncementGeneration;
        const lang = item.lang === 'en' ? 'en' : 'ar';
        const text = String(item.text || '').trim();
        const sender = String(item.published_by || '').trim();
        // GP_MANUAL_TV_VOICE_TOGGLE_V1
        const voiceEnabled = item.voice_enabled !== false;
'''
    tv = replace_once(tv, play_anchor, play_replacement, "TV ACK helper")

    label_anchor = '''        if (label) label.textContent = lang === 'ar' ? '📣 إعلان مباشر من الإدارة' : '📣 LIVE MANAGEMENT ANNOUNCEMENT';\n        if (textEl) textEl.textContent = text;\n        if (meta) {\n            const by = String(item.published_by || '').trim();\n            const source = by ? (lang === 'ar' ? `نُشر بواسطة: ${by}` : `Published by: ${by}`) : 'Golden Palace';\n            meta.textContent = voiceEnabled ? source : `${source} · ${lang === 'ar' ? '🔇 بدون صوت' : '🔇 Silent'}`;\n        }\n'''
    label_replacement = '''        if (label) label.textContent = lang === 'ar'\n            ? (sender ? `📣 إعلان من ${sender}` : '📣 إعلان مباشر من الإدارة')\n            : (sender ? `📣 ANNOUNCEMENT FROM ${sender}` : '📣 LIVE MANAGEMENT ANNOUNCEMENT');\n        if (textEl) textEl.textContent = text;\n        if (meta) {\n            const source = sender ? (lang === 'ar' ? `المرسل: ${sender}` : `Sender: ${sender}`) : 'Golden Palace';\n            meta.textContent = voiceEnabled ? source : `${source} · ${lang === 'ar' ? '🔇 بدون صوت' : '🔇 Silent'}`;\n        }\n'''
    tv = replace_once(tv, label_anchor, label_replacement, "sender on TV")

    display_anchor = '''        if (wave) wave.style.display = voiceEnabled ? 'flex' : 'none';\n        if (overlay) overlay.classList.add('show');\n\n        if (!voiceEnabled) {\n'''
    display_replacement = '''        if (wave) wave.style.display = voiceEnabled ? 'flex' : 'none';\n        if (overlay) overlay.classList.add('show');\n        // This is the first trustworthy delivery point: the TV page is visible and the overlay is on screen.\n        gpAckManualAnnouncement(item, 'displayed');\n\n        if (!voiceEnabled) {\n'''
    tv = replace_once(tv, display_anchor, display_replacement, "displayed ACK")

    voice_url_anchor = '''            const voiceResponse = await fetch(apiUrl(`/api/followup-voice?lang=${encodeURIComponent(lang)}&text=${encodeURIComponent(text)}&t=${Date.now()}`), {cache:'no-store'});\n'''
    voice_url_replacement = '''            const voiceResponse = await fetch(apiUrl(`/api/followup-voice?live=1&lang=${encodeURIComponent(lang)}&sender=${encodeURIComponent(sender)}&text=${encodeURIComponent(text)}&t=${Date.now()}`), {cache:'no-store'});\n'''
    tv = replace_once(tv, voice_url_anchor, voice_url_replacement, "live sender TTS")

    finish_anchor = '''            const finish = () => {\n                if (generation !== gpManualAnnouncementGeneration) return;\n                if (teamVoiceAudio === audio) teamVoiceAudio = null;\n                teamVoicePlaying = false;\n                setVoiceCaption('', false);\n                setTimeout(() => gpHideManualAnnouncement(generation), 1600);\n            };\n            audio.addEventListener('ended', finish, {once:true});\n            audio.addEventListener('error', finish, {once:true});\n            const promise = audio.play();\n'''
    finish_replacement = '''            const finish = (eventName) => {\n                if (generation !== gpManualAnnouncementGeneration) return;\n                if (eventName) gpAckManualAnnouncement(item, eventName);\n                if (teamVoiceAudio === audio) teamVoiceAudio = null;\n                teamVoicePlaying = false;\n                setVoiceCaption('', false);\n                setTimeout(() => gpHideManualAnnouncement(generation), 1600);\n            };\n            audio.addEventListener('playing', () => gpAckManualAnnouncement(item, 'audio_started'), {once:true});\n            audio.addEventListener('ended', () => finish('audio_finished'), {once:true});\n            audio.addEventListener('error', () => finish('audio_failed'), {once:true});\n            const promise = audio.play();\n'''
    tv = replace_once(tv, finish_anchor, finish_replacement, "audio ACK lifecycle")

    blocked_anchor = '''                    teamVoicePlaying = false;\n                    setVoiceCaption('', false);\n                    showToast(tr('audioBlocked'), 7000);\n'''
    blocked_replacement = '''                    teamVoicePlaying = false;\n                    setVoiceCaption('', false);\n                    gpAckManualAnnouncement(item, 'audio_failed');\n                    showToast(tr('audioBlocked'), 7000);\n'''
    tv = replace_once(tv, blocked_anchor, blocked_replacement, "blocked audio ACK")

    catch_anchor = '''            teamVoicePlaying = false;\n            setVoiceCaption('', false);\n            console.warn('Manual TV announcement voice failed:', err);\n'''
    catch_replacement = '''            teamVoicePlaying = false;\n            setVoiceCaption('', false);\n            gpAckManualAnnouncement(item, 'audio_failed');\n            console.warn('Manual TV announcement voice failed:', err);\n'''
    tv = replace_once(tv, catch_anchor, catch_replacement, "voice generation failure ACK")

flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
print("Announcement sender speech, Arabic tashkeel, and TV delivery ACK patched")
