from pathlib import Path

path = Path('scripts/apply_backend_ui_v2.py')
src = path.read_text(encoding='utf-8')
old = 'flask_followup_marker = "# ==========================================================\\n# ENCOURAGING ARABIC ANNOUNCEMENT\\n# =========================================================="'
new = 'flask_followup_marker = "# ==========================================================\\n# READ TV DATA\\n# =========================================================="'
if old in src:
    src = src.replace(old, new, 1)

needle = "    if old not in text:\n        raise SystemExit(f'Missing patch target: {label}')"
replacement = "    if old not in text:\n        Path('PATCH_ERROR.txt').write_text(str(label), encoding='utf-8')\n        raise SystemExit(f'Missing patch target: {label}')"
if needle in src:
    src = src.replace(needle, replacement, 1)

path.write_text(src, encoding='utf-8')
print('Follow-up patch insertion target and diagnostics aligned')
