from pathlib import Path

VOICE_API = "https://cqpmcqypwzlunskeeoml.supabase.co/functions/v1/gp-voice"

p = Path("templates/tv.html")
text = p.read_text(encoding="utf-8")
anchor = "const apiUrl = path => /^(?:https?:|data:|blob:)/i.test(String(path || '')) ? String(path || '') : `${API_BASE}${path}`;"
if "const GP_VOICE_API =" not in text:
    if anchor not in text:
        raise SystemExit("apiUrl anchor not found")
    text = text.replace(anchor, anchor + f"\n    const GP_VOICE_API = '{VOICE_API}';", 1)
text = text.replace("apiUrl(`/api/followup-voice?", "`${GP_VOICE_API}?")
if text.count(VOICE_API) < 1:
    raise SystemExit("voice API marker missing")
if "/api/followup-voice?" in text:
    raise SystemExit("legacy followup voice route still present")
p.write_text(text, encoding="utf-8")
print("TV voice route migrated to Supabase gp-voice")
