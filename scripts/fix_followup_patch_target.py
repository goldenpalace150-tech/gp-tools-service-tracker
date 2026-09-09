from pathlib import Path

path = Path('scripts/apply_backend_ui_v2.py')
src = path.read_text(encoding='utf-8')

old_marker = 'flask_followup_marker = "# ==========================================================\\n# ENCOURAGING ARABIC ANNOUNCEMENT\\n# =========================================================="'
new_marker = 'flask_followup_marker = "# ==========================================================\\n# READ TV DATA\\n# =========================================================="'
if old_marker in src:
    src = src.replace(old_marker, new_marker, 1)

# Replace fragile punctuation-dependent translation patches with stable object anchors.
lines = src.splitlines()
rebuilt = []
for line in lines:
    if line.startswith('tv = replace_once(tv, "            connecting:\'Connecting to Google Sheets'):
        rebuilt.append("tv = replace_once(tv, \"            heading:'Service Workshop Tracker',\", \"            followupOverdue:'🔴 Overdue follow-ups', followupToday:'🟠 Due today', followupSpares:'🟡 Spare parts', followupInquiries:'🔵 Inquiries', owner:'Owner', waitingOn:'Waiting on', nextAction:'Next action', nextFollowup:'Next follow-up', priority:'Priority', related:'Related ID', daysOverdue:'Days overdue', heading:'Service Workshop Tracker',\", 'English follow-up translations')")
    elif line.startswith('tv = replace_once(tv, "            syncReady:\'اتصال Google Sheets'):
        rebuilt.append("tv = replace_once(tv, \"            heading:'متابعة خدمة الورشة',\", \"            followupOverdue:'🔴 متابعات متأخرة', followupToday:'🟠 متابعة اليوم', followupSpares:'🟡 قطع غيار', followupInquiries:'🔵 استفسارات', owner:'المسؤول', waitingOn:'بانتظار', nextAction:'الخطوة القادمة', nextFollowup:'المتابعة القادمة', priority:'الأولوية', related:'المرجع', daysOverdue:'أيام التأخير', heading:'متابعة خدمة الورشة',\", 'Arabic follow-up translations')")
    else:
        rebuilt.append(line)
src = '\n'.join(rebuilt) + ('\n' if src.endswith('\n') else '')

needle = "    if old not in text:\n        raise SystemExit(f'Missing patch target: {label}')"
replacement = "    if old not in text:\n        Path('PATCH_ERROR.txt').write_text(str(label), encoding='utf-8')\n        raise SystemExit(f'Missing patch target: {label}')"
if needle in src:
    src = src.replace(needle, replacement, 1)

path.write_text(src, encoding='utf-8')
print('Follow-up patch targets aligned with current source')
