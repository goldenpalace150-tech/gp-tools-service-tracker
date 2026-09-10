from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing patch target: {label}")
    return text.replace(old, new, 1)


path = Path("flask_app.py")
text = path.read_text(encoding="utf-8")

if "GP_MANAGEMENT_ANNOUNCE_PAGE_V1" not in text:
    anchor = '''@app.route("/api/manual-announcement", methods=["POST", "OPTIONS"])\ndef api_manual_announcement():\n'''
    insert = r'''
# GP_MANAGEMENT_ANNOUNCE_PAGE_V1
@app.route("/announce", methods=["GET", "POST"])
def management_announce_page():
    requires_code = bool(GP_TV_ANNOUNCEMENT_KEY)
    context = {
        "success": False,
        "error": "",
        "requires_code": requires_code,
        "form_text": "",
        "form_lang": "auto",
        "form_published_by": "",
        "form_voice_enabled": True,
        "published_text": "",
    }

    if request.method == "POST":
        raw_text = str(request.form.get("text", ""))
        message = re.sub(r"\s+", " ", raw_text).strip()[:700]
        lang_requested = str(request.form.get("lang", "auto") or "auto").strip().lower()
        published_by = re.sub(r"\s+", " ", str(request.form.get("published_by", ""))).strip()[:80]
        voice_enabled = request.form.get("voice_enabled") == "on"
        access_code = str(request.form.get("access_code", ""))

        context.update({
            "form_text": raw_text,
            "form_lang": lang_requested if lang_requested in {"auto", "ar", "en"} else "auto",
            "form_published_by": published_by,
            "form_voice_enabled": voice_enabled,
        })

        if requires_code and access_code != GP_TV_ANNOUNCEMENT_KEY:
            context["error"] = "❌ Access code is incorrect. · رمز الدخول غير صحيح."
            return render_template("announce.html", **context), 403

        if not message:
            context["error"] = "❌ Please enter an announcement. · يرجى كتابة نص الإعلان."
            return render_template("announce.html", **context), 400

        lang = gp_detect_announcement_language(message, lang_requested)
        now = time.time()
        announcement_id = f"{int(now * 1000)}-{hashlib.sha1(message.encode('utf-8')).hexdigest()[:8]}"
        announcement = {
            "id": announcement_id,
            "text": message,
            "lang": lang,
            "published_by": published_by,
            "voice_enabled": voice_enabled,
            "created_at": now,
            "expires_at": now + 600,
        }
        gp_write_manual_announcement(announcement)
        context.update({
            "success": True,
            "form_text": "",
            "published_text": message,
        })

    response = app.make_response(render_template("announce.html", **context))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    return response


'''
    text = replace_once(text, anchor, insert + anchor, "manual announcement API route")

path.write_text(text, encoding="utf-8")
print("Management announcement page route patched")
