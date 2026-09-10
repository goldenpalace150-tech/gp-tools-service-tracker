from pathlib import Path

path = Path('templates/announce.html')
text = path.read_text(encoding='utf-8')
if 'GP_ANNOUNCE_V4_COPY_FIX' not in text:
    text = text.replace('<!-- GP_ANNOUNCE_V4 -->', '<!-- GP_ANNOUNCE_V4 -->\n  <!-- GP_ANNOUNCE_V4_COPY_FIX -->', 1)
# Clean every malformed token left by earlier bilingual replacements.
text = text.replace('تم الاطلاعd', 'تم الاطلاع')
text = text.replace('Seen / Acknowledged', 'تم الاطلاع')
text = text.replace('“تم الاطلاع” appears only after a person presses the button on the workshop TV.', '“تم الاطلاع” يظهر فقط بعد أن يضغط شخص زر التأكيد على شاشة الورشة.')
path.write_text(text, encoding='utf-8')
print('Announcement V4 copy fixed exhaustively')
