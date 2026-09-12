from pathlib import Path

path = Path('templates/tv.html')
text = path.read_text(encoding='utf-8')
marker = 'GP_ANNOUNCEMENT_SERIAL_QUEUE_V1'
if marker in text:
    print('announcement serial queue fix already applied')
    raise SystemExit(0)

def replace_once(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f'missing expected TV source fragment:\n{old[:220]}')
    text = text.replace(old, new, 1)

replace_once(
    "    let gpManualAnnouncementPollInFlight = false;\n    let gpManualAnnouncementGeneration = 0;\n",
    "    let gpManualAnnouncementPollInFlight = false;\n    let gpManualAnnouncementGeneration = 0;\n\n    // GP_ANNOUNCEMENT_SERIAL_QUEUE_V1\n    // Never let an older unexpired announcement come back and replace a newer one.\n    // Announcement IDs begin with Date.now(), so the timestamp is stable across reloads.\n    const GP_MANUAL_ANNOUNCEMENT_TS_KEY = 'gpManualAnnouncementLastTsV1';\n    let gpManualAnnouncementLastTs = (() => {\n        try {\n            const saved = Number(localStorage.getItem(GP_MANUAL_ANNOUNCEMENT_TS_KEY) || 0);\n            if (saved > 0) return saved;\n            const match = String(gpManualAnnouncementLastId || '').match(/^(\\d{10,})-/);\n            return match ? Number(match[1]) : 0;\n        } catch (_) { return 0; }\n    })();\n    let gpManualAnnouncementActive = false;\n\n    function gpManualAnnouncementEpoch(item) {\n        const created = Number(item && item.created_at);\n        if (created > 0) return created * 1000;\n        const match = String((item && item.id) || '').match(/^(\\d{10,})-/);\n        return match ? Number(match[1]) : 0;\n    }\n"
)

replace_once(
    "        const overlay = document.getElementById('manualAnnouncementOverlay');\n        if (overlay) overlay.classList.remove('show');\n    }\n",
    "        const overlay = document.getElementById('manualAnnouncementOverlay');\n        if (overlay) overlay.classList.remove('show');\n        gpManualAnnouncementActive = false;\n    }\n"
)

replace_once(
    "        const voiceEnabled = item.voice_enabled !== false;\n        if (!text) return;\n\n        stopTeamVoiceAudio();\n",
    "        const voiceEnabled = item.voice_enabled !== false;\n        if (!text) return;\n        if (gpManualAnnouncementActive) return;\n        gpManualAnnouncementActive = true;\n\n        stopTeamVoiceAudio();\n"
)

replace_once(
    "                ackBtn.classList.add('done');\n                ackBtn.textContent = lang === 'ar' ? '✅ تم تأكيد الاطلاع' : '✅ Acknowledged';\n                setTimeout(() => gpHideManualAnnouncement(generation), 1400);\n",
    "                // A human acknowledgement closes this announcement cleanly before\n                // the next one is allowed to start, so voices can never overlap.\n                stopTeamVoiceAudio();\n                teamVoicePlaying = false;\n                setVoiceCaption('', false);\n                ackBtn.classList.add('done');\n                ackBtn.textContent = lang === 'ar' ? '✅ تم تأكيد الاطلاع' : '✅ Acknowledged';\n                setTimeout(() => gpHideManualAnnouncement(generation), 1400);\n"
)

replace_once(
    "    async function gpPollManualAnnouncement() {\n        if (detailMode || gpManualAnnouncementPollInFlight || document.hidden) return;\n",
    "    async function gpPollManualAnnouncement() {\n        // Keep one announcement on screen until it is acknowledged or its own\n        // display/audio lifecycle finishes. Do not replace it every 500 ms.\n        if (detailMode || gpManualAnnouncementPollInFlight || document.hidden || gpManualAnnouncementActive) return;\n"
)

replace_once(
    "            const item = payload && payload.announcement;\n            if (!item || !item.id || String(item.id) === gpManualAnnouncementLastId) return;\n            gpManualAnnouncementLastId = String(item.id);\n            try { localStorage.setItem(GP_MANUAL_ANNOUNCEMENT_STORAGE_KEY, gpManualAnnouncementLastId); } catch (_) {}\n            gpPlayManualAnnouncement(item);\n",
    "            const item = payload && payload.announcement;\n            if (!item || !item.id || String(item.id) === gpManualAnnouncementLastId) return;\n            const itemTs = gpManualAnnouncementEpoch(item);\n            // The backend keeps announcements alive for several minutes. Its current\n            // latest?after= contract can return an older row after a newer row. Ignore\n            // anything at or behind the newest timestamp this TV has already shown.\n            if (itemTs && itemTs <= gpManualAnnouncementLastTs) return;\n            gpManualAnnouncementLastId = String(item.id);\n            if (itemTs) gpManualAnnouncementLastTs = itemTs;\n            try {\n                localStorage.setItem(GP_MANUAL_ANNOUNCEMENT_STORAGE_KEY, gpManualAnnouncementLastId);\n                if (itemTs) localStorage.setItem(GP_MANUAL_ANNOUNCEMENT_TS_KEY, String(itemTs));\n            } catch (_) {}\n            gpPlayManualAnnouncement(item);\n"
)

path.write_text(text, encoding='utf-8')
print('applied announcement serial queue fix')
# Trigger marker: v1.1
