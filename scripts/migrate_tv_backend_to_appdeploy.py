from pathlib import Path

OLD = "https://golden-palace-service-tracker.onrender.com"
NEW = "https://gp.18-232-7-146.sslip.io"

files = [
    Path("tools_tracker.py"),
    Path("GP-TV-Fullscreen.cmd"),
]

for path in files:
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    if OLD in text:
        text = text.replace(OLD, NEW)
        path.write_text(text, encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"No retired Render URL found in {path}")
