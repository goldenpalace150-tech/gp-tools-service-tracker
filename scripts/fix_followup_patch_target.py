from pathlib import Path

path = Path('scripts/apply_backend_ui_v2.py')
src = path.read_text(encoding='utf-8')
old = 'flask_followup_marker = "# ==========================================================\\n# ENCOURAGING ARABIC ANNOUNCEMENT\\n# =========================================================="'
new = 'flask_followup_marker = "# ==========================================================\\n# READ TV DATA\\n# =========================================================="'
if old not in src:
    raise SystemExit('Expected old follow-up insertion marker not found')
path.write_text(src.replace(old, new, 1), encoding='utf-8')
print('Follow-up patch insertion target corrected')
