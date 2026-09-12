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

# A deployed Streamlit/PythonAnywhere environment may still contain an old
# GP_TV_BACKEND_URL secret. Map that one retired value to AppDeploy so the
# running app does not keep calling the suspended Render backend.
tools_path = Path("tools_tracker.py")
if tools_path.exists():
    tools = tools_path.read_text(encoding="utf-8")
    anchor = f'GP_TV_BACKEND_URL = get_runtime_secret("GP_TV_BACKEND_URL") or "{NEW}"\n'
    marker = "GP_APPDEPLOY_BACKEND_FALLBACK_V1"
    if marker not in tools and anchor in tools:
        replacement = (
            anchor
            + f'# {marker}\n'
            + f'if GP_TV_BACKEND_URL.rstrip("/") == "{OLD}":\n'
            + f'    GP_TV_BACKEND_URL = "{NEW}"\n'
        )
        tools = tools.replace(anchor, replacement, 1)
        tools_path.write_text(tools, encoding="utf-8")
        print("Added legacy Render secret fallback to tools_tracker.py")
