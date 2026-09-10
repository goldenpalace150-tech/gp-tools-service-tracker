from pathlib import Path


def replace_required(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing repair target: {label}")
    return text.replace(old, new, 1)


announce_path = Path('templates/announce.html')
flask_path = Path('flask_app.py')
announce = announce_path.read_text(encoding='utf-8')
flask = flask_path.read_text(encoding='utf-8')

# Keep the V4 wording cleanup idempotent.
if 'GP_ANNOUNCE_V4_COPY_FIX' not in announce:
    announce = announce.replace('<!-- GP_ANNOUNCE_V4 -->', '<!-- GP_ANNOUNCE_V4 -->\n  <!-- GP_ANNOUNCE_V4_COPY_FIX -->', 1)
announce = announce.replace('تم الاطلاعd', 'تم الاطلاع')
announce = announce.replace('Seen / Acknowledged', 'تم الاطلاع')
announce = announce.replace('“تم الاطلاع” appears only after a person presses the button on the workshop TV.', '“تم الاطلاع” يظهر فقط بعد أن يضغط شخص زر التأكيد على شاشة الورشة.')

# GP_ANNOUNCE_DELIVERY_RELIABILITY_V5
# The five-second target is ONLY for technical TV display confirmation.
# Human acknowledgment remains a separate real-person action and may happen later.
if 'GP_ANNOUNCE_DELIVERY_RELIABILITY_V5' not in announce:
    announce = announce.replace(
        '<!-- GP_ANNOUNCE_V4_COPY_FIX -->',
        '<!-- GP_ANNOUNCE_V4_COPY_FIX -->\n  <!-- GP_ANNOUNCE_DELIVERY_RELIABILITY_V5 -->',
        1,
    )
    announce = replace_required(
        announce,
        "    let attempts = 0;\n    let finished = false;\n    let policePlayed = false;",
        "    let attempts = 0;\n    let finished = false;\n    let policePlayed = false;\n    let technicalWarningShown = false;\n    const statusStartedAt = Date.now();",
        'announcement status state',
    )
    announce = replace_required(
        announce,
        "            if (displayed) {\n              displayStep.classList.add('on');",
        "            if (displayed) {\n              box.classList.remove('fail');\n              technicalWarningShown = false;\n              displayStep.classList.add('on');",
        'late TV delivery recovery',
    )
    old_timeout = """      if (!finished && attempts >= 180) {
        if (displayStep && displayStep.classList.contains('on')) {
          title.textContent = '⚠️ وصل للتلفزيون ولم يتم تأكيد الاطلاع';
          text.textContent = 'التلفزيون عرض الإعلان، لكن لم يضغط أحد زر تم الاطلاع خلال 5 ثوانٍ.';
        } else {
          box.classList.add('fail');
          title.textContent = '⚠️ لم يصل تأكيد من التلفزيون · No TV confirmation';
          text.textContent = 'الخادم استلم الإعلان، لكن لم تؤكد أي شاشة عرضه خلال 5 ثوانٍ. قد تكون شاشة الورشة مطفأة أو غير متصلة.';
        }
        finished = true;
      }
      if (!finished) setTimeout(check, 250);"""
    new_timeout = """      const tvDisplayed = Boolean(displayStep && displayStep.classList.contains('on'));
      const elapsedMs = Date.now() - statusStartedAt;
      if (!finished && !technicalWarningShown && !tvDisplayed && elapsedMs >= 5000) {
        box.classList.add('fail');
        title.textContent = '⚠️ لم يصل تأكيد من التلفزيون خلال 5 ثوانٍ · No TV confirmation';
        text.textContent = 'الخادم استلم الإعلان، لكن لم تؤكد أي شاشة عرضه خلال 5 ثوانٍ. قد تكون شاشة الورشة مطفأة أو غير متصلة. سأستمر بمحاولة التحقق.';
        technicalWarningShown = true;
      }
      // The announcement itself expires after ten minutes. Until then a late TV
      // delivery can recover the warning and a real human acknowledgment can arrive.
      if (!finished && elapsedMs >= 600000) finished = true;
      if (!finished) setTimeout(check, tvDisplayed ? 1000 : 250);"""
    announce = replace_required(announce, old_timeout, new_timeout, 'five-second technical receipt semantics')

# GP_MANUAL_ANNOUNCEMENT_ACK_RELIABILITY_V5
# Gunicorn runs multiple threads/workers. The old status writer used only the PID
# in its temp filename, so two threads in one worker could collide and corrupt ACKs.
# Use unique temp names and an OS-level flock around the ACK read-modify-write.
if 'GP_MANUAL_ANNOUNCEMENT_ACK_RELIABILITY_V5' not in flask:
    flask = replace_required(
        flask,
        'import tempfile\nimport threading\n',
        'import tempfile\nimport threading\nimport fcntl\n',
        'fcntl import',
    )
    flask = replace_required(
        flask,
        'GP_MANUAL_DELIVERY_DIR = os.path.join(tempfile.gettempdir(), "gp_manual_delivery_v1")\nos.makedirs(GP_MANUAL_DELIVERY_DIR, exist_ok=True)\n',
        'GP_MANUAL_DELIVERY_DIR = os.path.join(tempfile.gettempdir(), "gp_manual_delivery_v1")\nos.makedirs(GP_MANUAL_DELIVERY_DIR, exist_ok=True)\n\n# GP_MANUAL_ANNOUNCEMENT_ACK_RELIABILITY_V5\n',
        'delivery reliability marker',
    )
    flask = replace_required(
        flask,
        '    temp_path = f"{path}.{os.getpid()}.tmp"\n    with open(temp_path, "w", encoding="utf-8") as handle:\n        json.dump(status, handle, ensure_ascii=False)\n    os.replace(temp_path, path)\n',
        '    temp_path = f"{path}.{os.getpid()}.{threading.get_ident()}.{time.time_ns()}.tmp"\n    try:\n        with open(temp_path, "w", encoding="utf-8") as handle:\n            json.dump(status, handle, ensure_ascii=False)\n            handle.flush()\n            os.fsync(handle.fileno())\n        os.replace(temp_path, path)\n    finally:\n        try:\n            if os.path.exists(temp_path):\n                os.remove(temp_path)\n        except Exception:\n            pass\n',
        'unique atomic delivery status writer',
    )
    lock_helpers = '''\n\ndef gp_lock_manual_delivery_status(announcement_id):\n    """Serialize one announcement ACK across Gunicorn processes and threads."""\n    lock_path = gp_manual_delivery_path(announcement_id) + ".lock"\n    handle = open(lock_path, "a+", encoding="utf-8")\n    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)\n    return handle\n\n\ndef gp_unlock_manual_delivery_status(handle):\n    if handle is None:\n        return\n    try:\n        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)\n    finally:\n        handle.close()\n'''
    flask = replace_required(
        flask,
        '\n\ndef gp_read_manual_delivery_status(announcement_id):',
        lock_helpers + '\n\ndef gp_read_manual_delivery_status(announcement_id):',
        'delivery lock helpers',
    )
    # Initialize the receipt before publishing the mailbox item, so the TV cannot
    # observe a new announcement before its status record exists.
    flask = replace_required(
        flask,
        '    gp_write_manual_announcement(announcement)\n    gp_init_manual_delivery_status(announcement)\n',
        '    gp_init_manual_delivery_status(announcement)\n    gp_write_manual_announcement(announcement)\n',
        'announcement publish ordering',
    )
    old_ack = '''    status = gp_read_manual_delivery_status(announcement_id)\n    if status is None:\n        current = gp_read_manual_announcement()\n        if not current or str(current.get("id", "")) != announcement_id:\n            return jsonify({"ok": False, "error": "unknown_announcement"}), 404\n        status = gp_init_manual_delivery_status(current)\n\n    now = time.time()\n    key = {\n        "displayed": "displayed_at",\n        "human_acknowledged": "human_acknowledged_at",\n        "audio_started": "audio_started_at",\n        "audio_finished": "audio_finished_at",\n        "audio_failed": "audio_failed_at",\n    }[event]\n    if not float(status.get(key, 0) or 0):\n        status[key] = now\n    if event in {"human_acknowledged", "audio_started", "audio_finished", "audio_failed"} and not float(status.get("displayed_at", 0) or 0):\n        status["displayed_at"] = now\n    status["last_tv_ack_at"] = now\n    status["tv_client"] = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("client", "")))[:64]\n    gp_write_manual_delivery_status(status)\n    response = jsonify({"ok": True, "status": status})'''
    new_ack = '''    delivery_lock = gp_lock_manual_delivery_status(announcement_id)\n    try:\n        status = gp_read_manual_delivery_status(announcement_id)\n        if status is None:\n            current = gp_read_manual_announcement()\n            if not current or str(current.get("id", "")) != announcement_id:\n                return jsonify({"ok": False, "error": "unknown_announcement"}), 404\n            status = gp_init_manual_delivery_status(current)\n\n        now = time.time()\n        key = {\n            "displayed": "displayed_at",\n            "human_acknowledged": "human_acknowledged_at",\n            "audio_started": "audio_started_at",\n            "audio_finished": "audio_finished_at",\n            "audio_failed": "audio_failed_at",\n        }[event]\n        if not float(status.get(key, 0) or 0):\n            status[key] = now\n        if event in {"human_acknowledged", "audio_started", "audio_finished", "audio_failed"} and not float(status.get("displayed_at", 0) or 0):\n            status["displayed_at"] = now\n        status["last_tv_ack_at"] = now\n        status["tv_client"] = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("client", "")))[:64]\n        gp_write_manual_delivery_status(status)\n    finally:\n        gp_unlock_manual_delivery_status(delivery_lock)\n    response = jsonify({"ok": True, "status": status})'''
    flask = replace_required(flask, old_ack, new_ack, 'serialized announcement ACK update')

announce_path.write_text(announce, encoding='utf-8')
flask_path.write_text(flask, encoding='utf-8')
print('Announcement V5 reliability fixed: atomic ACKs and correct 5-second technical receipt semantics')
