from pathlib import Path
import re

repo = Path('.')
tv_path = repo / 'templates' / 'tv.html'
tools_path = repo / 'tools_tracker.py'

tv = tv_path.read_text(encoding='utf-8')
tools = tools_path.read_text(encoding='utf-8')

# Fix the broken Streamlit iframe that drifted to an unconfigured GitHub Pages URL.
broken_control = 'https://goldenpalace150-tech.github.io/gp-tools-service-tracker/control.html'
working_control = 'https://gp.18-232-7-146.sslip.io/control.html'
if broken_control in tools:
    tools = tools.replace(broken_control, working_control)
elif working_control not in tools:
    raise SystemExit('Could not locate TV Control iframe URL')

marker = 'GP_RECORDED_ANNOUNCEMENT_AUDIO_V1'
if marker not in tv:
    voice_decl = "const GP_VOICE_API = 'https://cqpmcqypwzlunskeeoml.supabase.co/functions/v1/gp-voice';"
    if voice_decl not in tv:
        raise SystemExit('GP_VOICE_API declaration not found')
    tv = tv.replace(
        voice_decl,
        voice_decl + "\n    // GP_RECORDED_ANNOUNCEMENT_AUDIO_V1\n    const GP_ANNOUNCEMENT_API = 'https://cqpmcqypwzlunskeeoml.supabase.co/functions/v1/gp-announcement';",
        1,
    )

    # Manual announcement delivery acknowledgements now use the announcement service
    # so recorded and TTS announcements share one receipt pipeline.
    old_ack = "fetch(apiUrl('/api/manual-announcement/ack'), {"
    new_ack = "fetch(`${GP_ANNOUNCEMENT_API}/api/manual-announcement/ack`, {"
    if old_ack not in tv:
        raise SystemExit('Manual announcement ACK call not found')
    tv = tv.replace(old_ack, new_ack, 1)

    # Route latest-announcement polling to the new service while preserving query params.
    latest_pattern = re.compile(r"apiUrl\((`/api/manual-announcement/latest[^`]*`)\)")
    m = latest_pattern.search(tv)
    if not m:
        raise SystemExit('Manual announcement latest call not found')
    inner = m.group(1)
    replacement = inner.replace('`/api/manual-announcement/latest', '`${GP_ANNOUNCEMENT_API}/api/manual-announcement/latest', 1)
    tv = tv[:m.start()] + replacement + tv[m.end():]

    # Prefer a real recorded WAV supplied with the announcement. If none exists,
    # retain the existing generated voice behavior.
    old_voice = """            const voiceResponse = await fetch(\n                `${GP_VOICE_API}?live=1&lang=${encodeURIComponent(lang)}&text=${encodeURIComponent(text)}&sender=${encodeURIComponent(sender)}&t=${Date.now()}`,\n                {cache:'no-store'}\n            );\n            if (!voiceResponse.ok || generation !== gpManualAnnouncementGeneration) throw new Error(`Voice API ${voiceResponse.status}`);\n            const track = await voiceResponse.json();\n            if (!track || !track.ok || !track.audio_url || generation !== gpManualAnnouncementGeneration) throw new Error('Voice track unavailable');\n"""
    new_voice = """            const recordedAudioUrl = String(item.audio_url || '').trim();\n            let track;\n            if (recordedAudioUrl) {\n                track = {ok:true, audio_url:recordedAudioUrl, voice_quality:'recorded'};\n            } else {\n                const voiceResponse = await fetch(\n                    `${GP_VOICE_API}?live=1&lang=${encodeURIComponent(lang)}&text=${encodeURIComponent(text)}&sender=${encodeURIComponent(sender)}&t=${Date.now()}`,\n                    {cache:'no-store'}\n                );\n                if (!voiceResponse.ok || generation !== gpManualAnnouncementGeneration) throw new Error(`Voice API ${voiceResponse.status}`);\n                track = await voiceResponse.json();\n            }\n            if (!track || !track.ok || !track.audio_url || generation !== gpManualAnnouncementGeneration) throw new Error('Voice track unavailable');\n"""
    if old_voice not in tv:
        raise SystemExit('Manual announcement voice block not found')
    tv = tv.replace(old_voice, new_voice, 1)

# Ensure the latest endpoint is no longer routed through the generic API helper.
if "apiUrl(`/api/manual-announcement/latest" in tv or "apiUrl('/api/manual-announcement/latest" in tv:
    raise SystemExit('Old manual-announcement latest route remains')
if "fetch(apiUrl('/api/manual-announcement/ack')" in tv:
    raise SystemExit('Old manual-announcement ACK route remains')

# Required final markers.
for required in [marker, 'GP_ANNOUNCEMENT_API', 'voice_quality:\'recorded\'', working_control]:
    haystack = tv if required != working_control else tools
    if required not in haystack:
        raise SystemExit(f'Missing required marker: {required}')

tv_path.write_text(tv, encoding='utf-8')
tools_path.write_text(tools, encoding='utf-8')
print('Applied recorded announcement playback and TV Control iframe fix')
