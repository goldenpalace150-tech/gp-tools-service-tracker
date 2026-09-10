from pathlib import Path

path = Path('templates/tv.html')
text = path.read_text(encoding='utf-8')
marker = '    <!-- GP_TV_LAYOUT_FULLSCREEN_MOVEMENT_V3 -->'
removed = False
while marker in text:
    start = text.index(marker)
    end = text.index('</body>', start)
    text = text[:start] + text[end:]
    removed = True
text = text.replace('gpTvFloatingControls', 'gpTvFloatingControlsLegacyRemoved') if False else text
path.write_text(text, encoding='utf-8')
print('Legacy V3 floating TV controls removed' if removed else 'Legacy V3 floating TV controls already absent')
