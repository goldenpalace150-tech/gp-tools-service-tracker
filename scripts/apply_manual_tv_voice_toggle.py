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
# Streamlit: per-announcement Voice notification ON/OFF.
# -----------------------------------------------------------------------------
if "GP_MANUAL_TV_VOICE_TOGGLE_V1" not in tools:
    tools = replace_once(
        tools,
        'def publish_manual_tv_announcement(text, language="auto", published_by=""):\n',
        'def publish_manual_tv_announcement(text, language="auto", published_by="", voice_enabled=True):\n',
        "publisher signature",
    )
    tools = replace_once(
        tools,
        '        "published_by": str(published_by or "").strip(),\n',
        '        "published_by": str(published_by or "").strip(),\n        "voice_enabled": bool(voice_enabled),\n',
        "publisher voice payload",
    )
    tools = replace_once(
        tools,
        '''            lang_choice = st.selectbox(\n                "لغة الصوت (Voice language)",\n                ["auto", "ar", "en"],\n                format_func=lambda x: {"auto": "تلقائي / Auto", "ar": "العربية", "en": "English"}[x],\n            )\n            manual_announcement_submit = st.form_submit_button("📡 نشر الآن على التلفزيون (Publish Now)", use_container_width=True)\n''',
        '''            lang_choice = st.selectbox(\n                "لغة الصوت (Voice language)",\n                ["auto", "ar", "en"],\n                format_func=lambda x: {"auto": "تلقائي / Auto", "ar": "العربية", "en": "English"}[x],\n            )\n            # GP_MANUAL_TV_VOICE_TOGGLE_V1\n            manual_voice_enabled = st.checkbox(\n                "🔊 تشغيل التنبيه الصوتي (Enable voice notification)",\n                value=True,\n                help="عند إيقافه سيظهر الإعلان على التلفزيون فوراً بدون أي صوت.",\n            )\n            manual_announcement_submit = st.form_submit_button("📡 نشر الآن على التلفزيون (Publish Now)", use_container_width=True)\n''',
        "announcement voice checkbox",
    )
    tools = replace_once(
        tools,
        '''                            language=lang_choice,\n                            published_by=current_user,\n                        )\n''',
        '''                            language=lang_choice,\n                            published_by=current_user,\n                            voice_enabled=manual_voice_enabled,\n                        )\n''',
        "publisher voice argument",
    )

# -----------------------------------------------------------------------------
# Flask mailbox: carry the voice preference to every TV.
# -----------------------------------------------------------------------------
if "GP_MANUAL_TV_VOICE_TOGGLE_V1" not in flask:
    flask = replace_once(
        flask,
        '''        "published_by": re.sub(r"\\s+", " ", str(payload.get("published_by", ""))).strip()[:80],\n        "created_at": now,\n''',
        '''        "published_by": re.sub(r"\\s+", " ", str(payload.get("published_by", ""))).strip()[:80],\n        # GP_MANUAL_TV_VOICE_TOGGLE_V1\n        "voice_enabled": payload.get("voice_enabled", True) is not False,\n        "created_at": now,\n''',
        "announcement mailbox voice flag",
    )

# -----------------------------------------------------------------------------
# TV: silent announcements still take over visually, but never call TTS.
# -----------------------------------------------------------------------------
if "GP_MANUAL_TV_VOICE_TOGGLE_V1" not in tv:
    tv = replace_once(
        tv,
        '''        const lang = item.lang === 'en' ? 'en' : 'ar';\n        const text = String(item.text || '').trim();\n        if (!text) return;\n''',
        '''        const lang = item.lang === 'en' ? 'en' : 'ar';\n        const text = String(item.text || '').trim();\n        // GP_MANUAL_TV_VOICE_TOGGLE_V1\n        const voiceEnabled = item.voice_enabled !== false;\n        if (!text) return;\n''',
        "TV voice flag",
    )
    tv = replace_once(
        tv,
        '''        if (meta) {\n            const by = String(item.published_by || '').trim();\n            meta.textContent = by ? (lang === 'ar' ? `نُشر بواسطة: ${by}` : `Published by: ${by}`) : 'Golden Palace';\n        }\n        if (overlay) overlay.classList.add('show');\n        setVoiceCaption(text, true);\n\n        try {\n''',
        '''        if (meta) {\n            const by = String(item.published_by || '').trim();\n            const source = by ? (lang === 'ar' ? `نُشر بواسطة: ${by}` : `Published by: ${by}`) : 'Golden Palace';\n            meta.textContent = voiceEnabled ? source : `${source} · ${lang === 'ar' ? '🔇 بدون صوت' : '🔇 Silent'}`;\n        }\n        const wave = card ? card.querySelector('.gp-manual-announcement-wave') : null;\n        if (wave) wave.style.display = voiceEnabled ? 'flex' : 'none';\n        if (overlay) overlay.classList.add('show');\n\n        if (!voiceEnabled) {\n            setVoiceCaption('', false);\n            setTimeout(() => {\n                if (generation !== gpManualAnnouncementGeneration) return;\n                teamVoicePlaying = false;\n                gpHideManualAnnouncement(generation);\n            }, 8000);\n            return;\n        }\n\n        setVoiceCaption(text, true);\n        try {\n''',
        "TV silent announcement branch",
    )

tools_path.write_text(tools, encoding="utf-8")
flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
print("Manual TV voice toggle patched")
