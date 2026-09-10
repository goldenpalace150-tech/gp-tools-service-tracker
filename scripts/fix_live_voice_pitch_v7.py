from pathlib import Path

path = Path('flask_app.py')
text = path.read_text(encoding='utf-8')
old = '''    if is_live:\n        text = gp_prepare_live_announcement_speech(raw_text[:700], sender, lang)\n        rate = "-7%" if lang == "ar" else "-5%"\n        pitch = "0Hz" if lang == "ar" else "+1Hz"\n'''
new = '''    if is_live:\n        text = gp_prepare_live_announcement_speech(raw_text[:700], sender, lang)\n        rate = "-7%" if lang == "ar" else "-5%"\n        # edge-tts 7.2+ requires an explicit sign even for zero pitch.\n        pitch = "+0Hz" if lang == "ar" else "+1Hz"\n'''
if old in text:
    text = text.replace(old, new, 1)
elif 'pitch = "+0Hz" if lang == "ar" else "+1Hz"' not in text:
    raise SystemExit('Live announcement pitch target not found')
path.write_text(text, encoding='utf-8')
print('Live announcement TTS pitch fixed for edge-tts 7.2+')
