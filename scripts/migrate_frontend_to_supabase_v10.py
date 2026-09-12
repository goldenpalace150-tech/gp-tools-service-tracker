from pathlib import Path

API = "https://cqpmcqypwzlunskeeoml.supabase.co/functions/v1/gp-api"

# Patch TV frontend to call Supabase directly and preserve data/blob URLs for audio.
tv = Path("templates/tv.html")
text = tv.read_text(encoding="utf-8")
text = text.replace("const GP_BACKEND_ORIGIN = 'https://golden-palace-service-tracker.onrender.com';", f"const GP_BACKEND_ORIGIN = '{API}';")
text = text.replace("const apiUrl = path => `${API_BASE}${path}`;", "const apiUrl = path => /^(?:https?:|data:|blob:)/i.test(String(path || '')) ? String(path || '') : `${API_BASE}${path}`;")
text = text.replace('href="/manifest.webmanifest"', 'href="./manifest.webmanifest"')
tv.write_text(text, encoding="utf-8")

# Patch Streamlit/staff control backend to the same Supabase runtime.
tools = Path("tools_tracker.py")
text = tools.read_text(encoding="utf-8")
text = text.replace('GP_TV_BACKEND_URL = get_runtime_secret("GP_TV_BACKEND_URL") or "https://gp.18-232-7-146.sslip.io"', f'GP_TV_BACKEND_URL = get_runtime_secret("GP_TV_BACKEND_URL") or "{API}"')
text = text.replace('GP_TV_BACKEND_URL = "https://gp.18-232-7-146.sslip.io"', f'GP_TV_BACKEND_URL = "{API}"')
text = text.replace('"https://gp.18-232-7-146.sslip.io/control.html"', '"https://goldenpalace150-tech.github.io/gp-tools-service-tracker/control.html"')
tools.write_text(text, encoding="utf-8")

print("Migrated TV + staff control URLs to Supabase/GitHub Pages")
