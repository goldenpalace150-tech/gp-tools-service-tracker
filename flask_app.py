import os
import re
import json
import time
import hashlib
import asyncio
import random
import tempfile
import threading
from io import StringIO
from datetime import datetime

import pandas as pd
import requests
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

# GP_RENDER_STATIC_CORS_2026_09_08
@app.after_request
def add_gp_tv_cors_headers(response):
    origin=request.headers.get('Origin','').strip()
    allowed=(origin=='https://golden-palace-service-tracker.onrender.com' or bool(re.fullmatch(r'https://gp-tv(?:-[a-z0-9-]+)?\.onrender\.com',origin)))
    if allowed:
        response.headers['Access-Control-Allow-Origin']=origin
        response.headers['Vary']='Origin'
        response.headers['Access-Control-Allow-Headers']='Content-Type'
        response.headers['Access-Control-Allow-Methods']='GET, POST, OPTIONS'
    return response


# Reuse HTTPS connections to Google instead of opening a new TLS session
# on every dashboard refresh.
HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update({"User-Agent": "GoldenPalace-TV/1.0"})


# ==========================================================
# SETTINGS
# ==========================================================

# IMPORTANT:
# GOOGLE_SHEET_ID must be the editable Google Sheet ID from:
# https://docs.google.com/spreadsheets/d/<GOOGLE_SHEET_ID>/edit
# It is NOT the published 2PACX id.
SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1qLBFUoVDB7XMhxiR4UINyWqRwhOWwirW9ak1HOiiqHA").strip()

MAIN_GID = 0
REMARKS_GID = 798418979

# Published copy used only for fast/read-only TV reads.
PUBLISHED_SHEET_KEY = (
    "2PACX-1vSq8gkP3TooLk8fE64bgMoGlEjEtpq1Ty7b60fqJfipFiRdh3udiZN06dJ8H1zNLMWuOAsAxovkT7Eu"
)

SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    f"{PUBLISHED_SHEET_KEY}/pub?gid={MAIN_GID}&single=true&output=csv"
)

REMARKS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    f"{PUBLISHED_SHEET_KEY}/pub?gid={REMARKS_GID}&single=true&output=csv"
)


# ==========================================================
# FILE PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(BASE_DIR, "credentials.json")
AUDIO_DIR = os.path.join(BASE_DIR, "static", "generated_audio")
os.makedirs(AUDIO_DIR, exist_ok=True)


# Dashboard cache is memory-only.  The previous implementation repeatedly
# replaced a ~2.6 MB tv_data_cache.json file; on Render/NFS that can
# create many .nfs* temporary files when another worker still has the old file
# open.  Browser localStorage provides the fast warm-start snapshot instead.
TV_CACHE_TTL_SECONDS = max(5, int(os.environ.get("TV_CACHE_TTL_SECONDS", "15")))
REMARKS_CACHE_TTL_SECONDS = max(15, int(os.environ.get("REMARKS_CACHE_TTL_SECONDS", "60")))

_TV_CACHE_DATA = None
_TV_CACHE_SAVED_AT = 0.0
_TV_CACHE_LOCK = threading.RLock()
_TV_REFRESH_LOCK = threading.Lock()
_TV_REFRESHING = False
_TV_LAST_REFRESH_ERROR = ""

_REMARKS_CACHE = []
_REMARKS_CACHE_SAVED_AT = 0.0


# ==========================================================
# OPTIONAL GOOGLE APPS SCRIPT WRITE ENDPOINT
# ==========================================================

GOOGLE_APPS_SCRIPT_URL = os.environ.get("GOOGLE_APPS_SCRIPT_URL", "").strip()
GOOGLE_APPS_SCRIPT_SECRET = os.environ.get("GOOGLE_APPS_SCRIPT_SECRET", "").strip()


# ==========================================================
# ELEVENLABS SETTINGS
# ==========================================================

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()



# ==========================================================
# GP_SERVER_SYRIAN_VOICE_V2
# Browser-independent server generated workshop voice
# ==========================================================

# GP_LEVANTINE_VOICE_V4
GP_AR_VOICE = os.environ.get("GP_AR_VOICE", "ar-LB-LaylaNeural").strip() or "ar-LB-LaylaNeural"
GP_EN_VOICE = os.environ.get("GP_EN_VOICE", "en-US-JennyNeural").strip() or "en-US-JennyNeural"
GP_VOICE_CACHE_DIR = os.path.join(tempfile.gettempdir(), "golden_palace_voice_v2")
os.makedirs(GP_VOICE_CACHE_DIR, exist_ok=True)
GP_VOICE_FILE_LOCKS = {}
GP_VOICE_FILE_LOCKS_GUARD = threading.Lock()

# GP_VOICE_BALANCE_PROSODY_V3
GP_STAFF_AR = ["أبو عدنان", "خبيطي", "أبو نقطة", "عمر", "أبو آدم", "حريري", "أبو غسان", "حازم"]
GP_STAFF_EN = ["Abu Adnan", "Khbeiti", "Abu Nuqta", "Omar", "Abu Adam", "Hariri", "Abu Ghassan", "Hazem"]

GP_AR_PERSON = [
    "{name}، يعطيك العافية. اليوم بدنا نخلي كل حالة عندك محدثة، والخطوة الجاية واضحة.",
    "{name}، شغلك المرتب بيفرق. خلّينا نخلص الجاهز، وما نخلي أي حالة واقفة بلا سبب.",
    "{name}، كل تحديث صغير بوقته بيوفّر علينا أسئلة وتأخير بعدين.",
    "{name}، ركّز اليوم على الأقدم، وخلي الحالة تنتقل للخطوة الجاية من دون تأخير.",
    "{name}، إذا في عائق بالحالة، ارفعه بكير. هيك منحلّه قبل ما يكبر.",
    "{name}، ورجينا لمسة الخبرة. بدنا الحالة واضحة من أولها لآخرها.",
    "{name}، خفّف القائمة حالة ورا حالة، بس خليك دقيق بالتحديث.",
    "{name}، إذا الجهاز عم يتدلّع، ذكّره إنو وصل لعند أهل الخبرة.",
]
GP_AR_MANAGER = [
    "أبو آدم، متابعة العمليات اليوم واضحة: الأولوية للحالات المتأخرة، وأي عائق لازم يطلع بسرعة قبل ما يوقف الشغل.",
    "أبو آدم، التنسيق بين الأقسام هو الأساس اليوم. كل حالة بدها مسؤول واضح وخطوة جاية واضحة.",
    "أبو آدم، الأرقام مهمة، بس الأهم إنو ما تضل أي حالة معلّقة بلا قرار.",
    "أبو آدم، اليوم الناجح مو بس بعدد الحالات اللي تسكرت، كمان بقديش خفّ وقت انتظار الزبون.",
    "أبو آدم، ترتيب الأولويات اليوم أهم من فتح شغل جديد. خلّينا نخلّص الجاهز أول.",
    "أبو آدم، إذا في تأخير معروف منقدر نديره. التأخير المخفي هو اللي بيعمل المشكلة.",
]
GP_AR_MANAGER_JOKES = [
    "أبو آدم، طلبت تطوير بسيط. ومن خبرتنا بالتطوير البسيط، الإصدار رقم اثنين غالباً واقف عالباب.",
    "أبو آدم، إذا الداشبورد صار كله أخضر، لا تعمل ريفريش من الخوف. هاد اسمه إنجاز.",
    "أبو آدم، طلبت نشيل الاختناق من العملية. بس ممنوع ننقله لقسم تاني ونسميها إعادة توزيع.",
    "أبو آدم، أي اختصار بخطوات الشغل مرحّب فيه، إلا إذا الاختصار رجّعنا ثلاث خطوات لورا.",
    "أبو آدم، واضح إنو تطوير العمليات ما بيخلص. كل ما نزبط شغلة، بتطلع شغلة أذكى بدها تطوير.",
]
GP_AR_FUNNY = [
    "اليوم الأجهزة داخلة الورشة متوترة. طمنوها إنو وصلت لعند أهل الخبرة.",
    "إذا جهاز عَنَّد معنا، ما في مشكلة. منعنّد عليه بالخبرة أكتر.",
    "قائمة الانتظار عم تعمل حالها كبيرة اليوم. خلّونا نصغّرها شوي.",
    "الجهاز اللي مفكّر يقضي عطلة عنا، خبرّوه إنو الحجز فل.",
    "إذا مفك البراغي اختفى مرة تانية، رح نفتحله سند صيانة لحاله.",
    "الداشبورد ما بيصلّح الأجهزة، بس بصراحة بيحرج الحالة اللي قاعدة بلا تحديث.",
]
GP_AR_FINALS = [
    "يعطيكم العافية يا شباب.",
    "نكملها صح اليوم.",
    "خلي الزبون يحس بالفرق.",
    "مشكورين، وكملوا بنفس النفس الحلو.",
    "الله يقويكم، ومنكمّل.",
    "تمام يا شباب، هيك بدنا الشغل.",
]
GP_EN_PERSON = [
    "{name}, keep every case updated and make the next action clear.",
    "{name}, clear the ready work first and raise any blocker early.",
    "{name}, one accurate update now saves several questions later.",
]
GP_EN_MANAGER = [
    "Abu Adam, today’s operations priority is delayed work, visible blockers, and clear ownership.",
    "Abu Adam, keep the flow between teams clear and make sure every case has a next action.",
]
GP_EN_MANAGER_JOKES = [
    "Abu Adam, you asked for one small improvement. Version two is probably already waiting.",
    "Abu Adam, if the dashboard turns completely green, do not restart it. That is called progress.",
]
GP_EN_FINALS = ["Great work, team.", "Let us finish strong.", "Thank you, team.", "Keep it moving."]


def gp_build_voice_message(lang="ar", force_named=""):
    lang = "en" if str(lang).lower().startswith("en") else "ar"
    requested_person = str(force_named or "").strip()
    tone = "warm"
    category = "person"
    person = requested_person
    if lang == "ar":
        if person not in set(GP_STAFF_AR):
            person = random.choice(GP_STAFF_AR)
        if person == "أبو آدم":
            if random.random() < 0.35:
                body = random.choice(GP_AR_MANAGER_JOKES); category = "management_joke"; tone = "funny"
            else:
                body = random.choice(GP_AR_MANAGER); category = "management"
        else:
            if random.random() < 0.22:
                body = f"{person}، {random.choice(GP_AR_FUNNY)}"; category = "person_funny"; tone = "funny"
            else:
                body = random.choice(GP_AR_PERSON).format(name=person)
        final = random.choice(GP_AR_FINALS)
    else:
        if person not in set(GP_STAFF_EN):
            person = random.choice(GP_STAFF_EN)
        if person == "Abu Adam":
            if random.random() < 0.35:
                body = random.choice(GP_EN_MANAGER_JOKES); category = "management_joke"; tone = "funny"
            else:
                body = random.choice(GP_EN_MANAGER); category = "management"
        else:
            body = random.choice(GP_EN_PERSON).format(name=person)
        final = random.choice(GP_EN_FINALS)
    body = re.sub(r"\s+", " ", body).strip()
    final = re.sub(r"\s+", " ", final).strip()
    text = f"{body} {final}".strip()
    return {"lang": lang, "text": text, "body": body, "final": final, "tone": tone, "category": category, "person": person}


def gp_voice_settings(lang, tone):
    voice = GP_AR_VOICE if lang == "ar" else GP_EN_VOICE
    if tone == "funny": return voice, "+6%", "+3Hz"
    return voice, "+1%", "+1Hz"


def gp_voice_cache_path(text, voice, rate, pitch):
    token = hashlib.sha256(f"{voice}|{rate}|{pitch}|{text}".encode("utf-8")).hexdigest()
    return token, os.path.join(GP_VOICE_CACHE_DIR, f"{token}.mp3")


async def gp_generate_edge_tts(text, voice, rate, pitch, path):
    import edge_tts
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch, volume="+0%")
    await communicator.save(path)


def gp_ensure_voice_file(text, voice, rate, pitch):
    token, path = gp_voice_cache_path(text, voice, rate, pitch)
    if os.path.exists(path) and os.path.getsize(path) > 1000: return token, path
    with GP_VOICE_FILE_LOCKS_GUARD: lock = GP_VOICE_FILE_LOCKS.setdefault(token, threading.Lock())
    with lock:
        if os.path.exists(path) and os.path.getsize(path) > 1000: return token, path
        tmp_path = path + ".tmp"
        try:
            if os.path.exists(tmp_path): os.remove(tmp_path)
            asyncio.run(gp_generate_edge_tts(text, voice, rate, pitch, tmp_path))
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) <= 1000: raise RuntimeError("voice generation returned an empty audio file")
            os.replace(tmp_path, path)
        finally:
            try:
                if os.path.exists(tmp_path): os.remove(tmp_path)
            except Exception: pass
    return token, path


@app.route("/api/voice-track")
def api_voice_track():
    lang = "en" if str(request.args.get("lang", "ar")).lower().startswith("en") else "ar"
    requested_person = str(request.args.get("person", "")).strip()
    track = gp_build_voice_message(lang, requested_person)
    voice, body_rate, body_pitch = gp_voice_settings(lang, track["tone"])
    final_rate = "-5%" if lang == "ar" else "-7%"
    final_pitch = "-3Hz" if lang == "ar" else "-4Hz"
    try:
        body_token, _ = gp_ensure_voice_file(track["body"], voice, body_rate, body_pitch)
        final_token, _ = gp_ensure_voice_file(track["final"], voice, final_rate, final_pitch)
    except Exception as exc:
        print("VOICE GENERATION ERROR:", repr(exc))
        return jsonify({"ok": False, "error": "voice_generation_failed"}), 503
    return jsonify({"ok": True, "text": track["text"], "lang": lang, "tone": track["tone"], "category": track["category"], "person": track["person"], "voice": voice, "audio_urls": [f"/api/voice-audio/{body_token}.mp3", f"/api/voice-audio/{final_token}.mp3"]})

# GP_FOLLOWUP_VOICE_V2
@app.route("/api/followup-voice")
def api_followup_voice():
    lang = "en" if str(request.args.get("lang", "ar")).lower().startswith("en") else "ar"
    text = re.sub(r"\s+", " ", str(request.args.get("text", ""))).strip()
    if not text:
        return jsonify({"ok": False, "error": "missing_text"}), 400
    text = text[:500]
    voice = GP_AR_VOICE if lang == "ar" else GP_EN_VOICE
    try:
        token, _ = gp_ensure_voice_file(text, voice, "-3%" if lang == "ar" else "-5%", "+1Hz")
    except Exception as exc:
        print("FollowUp voice generation error:", repr(exc))
        return jsonify({"ok": False, "error": "voice_generation_failed"}), 503
    return jsonify({"ok": True, "text": text, "lang": lang, "voice": voice, "audio_url": f"/api/voice-audio/{token}.mp3"})




# GP_MANUAL_TV_ANNOUNCEMENT_API_V1
GP_MANUAL_ANNOUNCEMENT_FILE = os.path.join(tempfile.gettempdir(), "gp_manual_tv_announcement_v1.json")
GP_MANUAL_ANNOUNCEMENT_LOCK = threading.RLock()
GP_TV_ANNOUNCEMENT_KEY = os.environ.get("GP_TV_ANNOUNCEMENT_KEY", "").strip()


def gp_detect_announcement_language(text, requested="auto"):
    requested = str(requested or "auto").lower().strip()
    if requested in {"ar", "en"}:
        return requested
    return "ar" if re.search(r"[\u0600-\u06ff]", str(text or "")) else "en"


def gp_read_manual_announcement():
    try:
        with GP_MANUAL_ANNOUNCEMENT_LOCK:
            if not os.path.exists(GP_MANUAL_ANNOUNCEMENT_FILE):
                return None
            with open(GP_MANUAL_ANNOUNCEMENT_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        if float(data.get("expires_at", 0) or 0) < time.time():
            return None
        return data
    except Exception as exc:
        print("Manual announcement read error:", repr(exc))
        return None


def gp_write_manual_announcement(data):
    temp_path = f"{GP_MANUAL_ANNOUNCEMENT_FILE}.{os.getpid()}.tmp"
    with GP_MANUAL_ANNOUNCEMENT_LOCK:
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False)
            os.replace(temp_path, GP_MANUAL_ANNOUNCEMENT_FILE)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass


def gp_manual_announcement_authorized():
    if not GP_TV_ANNOUNCEMENT_KEY:
        return True
    return request.headers.get("X-GP-Announcement-Key", "").strip() == GP_TV_ANNOUNCEMENT_KEY



# GP_TV_CONTROL_AND_PUSH_V1
GP_TV_CONTROL_FILE = os.path.join(tempfile.gettempdir(), "gp_tv_control_v1.json")
GP_TV_CONTROL_LOCK = threading.RLock()


def gp_default_tv_control():
    return {
        "staff_voice_enabled": True,
        "data_revision": "",
        "updated_at": 0,
        "reason": "",
    }


def gp_read_tv_control():
    state = gp_default_tv_control()
    try:
        with GP_TV_CONTROL_LOCK:
            if os.path.exists(GP_TV_CONTROL_FILE):
                with open(GP_TV_CONTROL_FILE, "r", encoding="utf-8") as handle:
                    saved = json.load(handle)
                if isinstance(saved, dict):
                    state.update(saved)
    except Exception as exc:
        print("TV control read error:", repr(exc))
    state["staff_voice_enabled"] = bool(state.get("staff_voice_enabled", True))
    state["data_revision"] = str(state.get("data_revision", "") or "")
    return state


def gp_write_tv_control(state):
    temp_path = f"{GP_TV_CONTROL_FILE}.{os.getpid()}.tmp"
    with GP_TV_CONTROL_LOCK:
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False)
            os.replace(temp_path, GP_TV_CONTROL_FILE)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass


@app.route("/api/tv-control", methods=["GET", "POST", "OPTIONS"])
def api_tv_control():
    if request.method == "OPTIONS":
        return ("", 204)
    state = gp_read_tv_control()
    if request.method == "POST":
        if not gp_manual_announcement_authorized():
            return jsonify({"ok": False, "error": "unauthorized"}), 403
        payload = request.get_json(silent=True) or {}
        if "staff_voice_enabled" in payload:
            state["staff_voice_enabled"] = bool(payload.get("staff_voice_enabled"))
        if payload.get("refresh_now"):
            # String form preserves nanosecond uniqueness in JavaScript.
            state["data_revision"] = str(time.time_ns())
        state["updated_at"] = time.time()
        state["reason"] = re.sub(r"\s+", " ", str(payload.get("reason", ""))).strip()[:120]
        gp_write_tv_control(state)
    response = jsonify({"ok": True, **state})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@app.route("/api/manual-announcement", methods=["POST", "OPTIONS"])
def api_manual_announcement():
    if request.method == "OPTIONS":
        return ("", 204)
    if not gp_manual_announcement_authorized():
        return jsonify({"ok": False, "error": "unauthorized"}), 403
    payload = request.get_json(silent=True) or {}
    text = re.sub(r"\s+", " ", str(payload.get("text", ""))).strip()
    if not text:
        return jsonify({"ok": False, "error": "missing_text"}), 400
    text = text[:700]
    lang = gp_detect_announcement_language(text, payload.get("lang", "auto"))
    now = time.time()
    announcement_id = f"{int(now * 1000)}-{hashlib.sha1(text.encode('utf-8')).hexdigest()[:8]}"
    announcement = {
        "id": announcement_id,
        "text": text,
        "lang": lang,
        "published_by": re.sub(r"\s+", " ", str(payload.get("published_by", ""))).strip()[:80],
        # GP_MANUAL_TV_VOICE_TOGGLE_V1
        "voice_enabled": payload.get("voice_enabled", True) is not False,
        "created_at": now,
        "expires_at": now + 600,
    }
    gp_write_manual_announcement(announcement)
    response = jsonify({"ok": True, **announcement})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.route("/api/manual-announcement/latest")
def api_manual_announcement_latest():
    announcement = gp_read_manual_announcement()
    after = str(request.args.get("after", "")).strip()
    if not announcement or (after and after == str(announcement.get("id", ""))):
        response = jsonify({"ok": True, "announcement": None})
    else:
        response = jsonify({"ok": True, "announcement": announcement})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.route("/api/voice-audio/<token>.mp3")
def api_voice_audio(token):
    token = str(token or "").lower().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", token): return "Not found", 404
    path = os.path.join(GP_VOICE_CACHE_DIR, f"{token}.mp3")
    if not os.path.exists(path): return "Not found", 404
    response = send_file(path, mimetype="audio/mpeg", conditional=True, max_age=86400)
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


# ==========================================================
# WORKFLOW CONSTANTS
# ==========================================================

CASE_STATUS_OPEN = "مفتوح"
CASE_STATUS_CLOSED = "مغلق"

COLLECTION_NOT_READY = "لم يجهز للتسليم بعد"
COLLECTION_AWAITING = "بانتظار تأكيد الاستلام"
COLLECTION_SPECIAL_AWAITING = "حالة خاصة - بانتظار الاستلام"
COLLECTION_PAID_AWAITING_CLOSE = "تم تسجيل القبض - بانتظار إغلاق الحالة"  # legacy
COLLECTION_CLOSED = "تم الاستلام وإغلاق الحالة"
COLLECTION_ZERO_NOT_REQUIRED = "لا يحتاج تأكيد الاستلام - فاتورة صفر"
COLLECTION_PARTNER_NOT_APPLICABLE = "غير منطبق - حالة شريك"

WF_WAITING = "WAITING"
WF_IN_REPAIR = "IN_REPAIR"
WF_WAIT_COLLECTION = "WAIT_COLLECTION"
WF_WAIT_PARTNER = "WAIT_PARTNER"
WF_CLOSED_ZERO = "CLOSED_ZERO_INVOICE"
WF_CLOSED_COLLECTED = "CLOSED_COLLECTED"
WF_CLOSED_PARTNER = "CLOSED_PARTNER_SETTLED"
WF_CLOSED_TV = "CLOSED_TV_CONFIRMED"

CLOSED_WORKFLOW_STATES = {
    WF_CLOSED_ZERO,
    WF_CLOSED_COLLECTED,
    WF_CLOSED_PARTNER,
    WF_CLOSED_TV,
}

NO_PAYMENT_SPECIAL_CASES = {
    "يعمل من المصدر",
    "الزبون رفض الإصلاح",
    "مكلف",
    "كفالة",
    "غير قابل للإصلاح",
    "لا يوجد عطل",
}


# ==========================================================
# GOOGLE SHEETS WRITE CONNECTION
# ==========================================================

remarks_sheet = None
main_sheet = None
followup_sheet = None
spreadsheet_obj = None

LAST_WRITE_ERROR = ""
LAST_CONNECT_ATTEMPT = 0.0
LAST_READ_SOURCE = "published_csv"
RECONNECT_INTERVAL_SECONDS = 30


def initialize_google_sheets():
    """Connect to the editable Google Sheet for live read/write operations."""
    global remarks_sheet, main_sheet, followup_sheet, spreadsheet_obj
    global LAST_WRITE_ERROR, LAST_CONNECT_ATTEMPT

    LAST_CONNECT_ATTEMPT = time.monotonic()
    LAST_WRITE_ERROR = ""

    remarks_sheet = None
    main_sheet = None
    followup_sheet = None
    spreadsheet_obj = None

    try:
        import gspread

        if not SHEET_ID:
            LAST_WRITE_ERROR = (
                "GOOGLE_SHEET_ID is not configured. "
                "Use the editable spreadsheet ID, not the published 2PACX ID."
            )
            print("ERROR:", LAST_WRITE_ERROR)
            return False

        # Preferred: credentials.json beside flask_app.py (or the path in
        # GOOGLE_APPLICATION_CREDENTIALS). Alternative: GOOGLE_SERVICE_ACCOUNT_JSON
        # containing the service-account JSON object.
        configured_creds_path = os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS",
            CREDS_PATH,
        ).strip() or CREDS_PATH

        service_account_json = os.environ.get(
            "GOOGLE_SERVICE_ACCOUNT_JSON",
            "",
        ).strip()

        if os.path.exists(configured_creds_path):
            gc = gspread.service_account(filename=configured_creds_path)

        elif service_account_json:
            from google.oauth2.service_account import Credentials

            info = json.loads(service_account_json)
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            credentials = Credentials.from_service_account_info(
                info,
                scopes=scopes,
            )
            gc = gspread.authorize(credentials)

        else:
            LAST_WRITE_ERROR = (
                "Google credentials are missing on Render. "
                "Upload credentials.json beside flask_app.py or configure "
                "GOOGLE_SERVICE_ACCOUNT_JSON."
            )
            print("ERROR:", LAST_WRITE_ERROR)
            return False

        spreadsheet_obj = gc.open_by_key(SHEET_ID)

        # IMPORTANT: tools_tracker.py reads the named worksheet "Ledger".
        # Use the same named worksheet first so the TV can never drift to a
        # different first tab if Google Sheet tab order changes.
        try:
            main_sheet = spreadsheet_obj.worksheet("Ledger")
        except Exception:
            try:
                main_sheet = spreadsheet_obj.get_worksheet_by_id(MAIN_GID)
            except Exception:
                main_sheet = spreadsheet_obj.get_worksheet(0)

        # Prefer the named Remarks worksheet, then keep the historical GID fallback.
        try:
            remarks_sheet = spreadsheet_obj.worksheet("Remarks")
        except Exception:
            try:
                remarks_sheet = spreadsheet_obj.get_worksheet_by_id(REMARKS_GID)
            except Exception:
                remarks_sheet = None
                for worksheet in spreadsheet_obj.worksheets():
                    try:
                        if int(getattr(worksheet, "id", -1)) == int(REMARKS_GID):
                            remarks_sheet = worksheet
                            break
                    except Exception:
                        pass

        # FollowUp is optional so TV/collection writes remain available before the new sheet exists.
        try:
            followup_sheet = spreadsheet_obj.worksheet("FollowUp")
        except Exception:
            followup_sheet = None

        if main_sheet is None:
            LAST_WRITE_ERROR = "Ledger/Main worksheet was not found."
            print("ERROR:", LAST_WRITE_ERROR)
            return False

        if remarks_sheet is None:
            LAST_WRITE_ERROR = "Remarks worksheet was not found."
            print("ERROR:", LAST_WRITE_ERROR)
            return False

        # Lightweight permission/read test. The actual write is only done when
        # the user explicitly closes a remark or confirms collection.
        main_sheet.row_values(1)
        remarks_sheet.row_values(1)

        LAST_WRITE_ERROR = ""
        print("SUCCESS: Google Sheets live connection ready.")
        return True

    except Exception as exc:
        LAST_WRITE_ERROR = f"{type(exc).__name__}: {exc}"
        print("GOOGLE SHEETS ERROR:", LAST_WRITE_ERROR)
        remarks_sheet = None
        main_sheet = None
        spreadsheet_obj = None
        return False


def write_ready():
    return main_sheet is not None and remarks_sheet is not None


def maybe_reconnect_google_sheets(force=False):
    if write_ready():
        return True

    elapsed = time.monotonic() - LAST_CONNECT_ATTEMPT

    if force or elapsed >= RECONNECT_INTERVAL_SECONDS:
        return initialize_google_sheets()

    return False


# IMPORTANT: do not connect to Google Sheets during module import.
# Render waits for the WSGI app to load; a network call here can
# exceed its reload/startup timeout. The editable Sheet connection is opened
# lazily only when a write action explicitly needs it.


# ==========================================================
# STATUS / WORKFLOW HELPERS
# ==========================================================


def normalize_doc_string(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_number(value, default=0.0):
    try:
        number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        return float(number) if pd.notna(number) else float(default)
    except Exception:
        return float(default)


def is_zero_amount(value, tolerance=0.000001):
    try:
        number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        return pd.notna(number) and abs(float(number)) <= tolerance
    except Exception:
        return False


def special_case_from_remarks(text):
    t = normalize_doc_string(text)
    if any(key in t for key in [
        "رفض الإصلاح", "رفض الاصلاح", "الزبون رفض", "رفض الصيانة",
        "رفض التصليح", "لم يوافق على الإصلاح", "لم يوافق على الاصلاح",
    ]):
        return "الزبون رفض الإصلاح"
    if any(key in t for key in ["يعمل من المصدر", "يعمل على المصدر"]):
        return "يعمل من المصدر"
    if "مكلف" in t:
        return "مكلف"
    if any(key in t for key in ["كفالة", "ضمان"]) and not any(
        key in t for key in ["خارج الكفالة", "خارج كفالة", "خارج الضمان"]
    ):
        return "كفالة"
    if any(key in t for key in [
        "غير قابل للإصلاح", "غير قابل للاصلاح", "غير قابل للصيانة",
        "لاتصلح", "لا تصلح", "لا يمكن إصلاح", "لا يمكن اصلاح",
    ]):
        return "غير قابل للإصلاح"
    if "لايوجد عطل" in t or "لا يوجد عطل" in t:
        return "لا يوجد عطل"
    return ""


def combined_document_text(document_origin="", document_history="", cycle_history=""):
    # Cycle history is preferred because full document_history can contain older repairs.
    cycle = normalize_doc_string(cycle_history)
    if cycle:
        return cycle
    return normalize_doc_string(f"{document_origin} {document_history}")


def status_from_workflow(workflow_state, special_case=""):
    wf = normalize_doc_string(workflow_state)
    special = normalize_doc_string(special_case)
    if wf == WF_CLOSED_ZERO:
        return "مغلق - فاتورة صفر"
    if wf in {WF_CLOSED_COLLECTED, WF_CLOSED_TV}:
        return "مغلق - تم الاستلام"
    if wf == WF_CLOSED_PARTNER:
        return "مغلق - تمت تسوية الشريك"
    if wf == WF_WAIT_COLLECTION:
        return f"حالة خاصة - بانتظار الاستلام ({special})" if special else "جاهز للتسليم - بانتظار الاستلام"
    if wf == WF_WAIT_PARTNER:
        return "جاهز - بانتظار مطالبة الشريك"
    if wf == WF_IN_REPAIR:
        return "قيد المعالجة"
    return "قيد الانتظار"


def derive_workflow_state(row):
    """Use persisted cycle-aware state first, then migrate legacy rows safely."""
    sid = normalize_doc_string(row.get("service_id", "")).upper()
    wf = normalize_doc_string(row.get("workflow_state", ""))
    valid = {
        WF_WAITING, WF_IN_REPAIR, WF_WAIT_COLLECTION, WF_WAIT_PARTNER,
        WF_CLOSED_ZERO, WF_CLOSED_COLLECTED, WF_CLOSED_PARTNER, WF_CLOSED_TV,
    }
    if wf in valid:
        return wf

    case_status = normalize_doc_string(row.get("case_status", ""))
    closed_by = normalize_doc_string(row.get("closed_by", ""))
    close_note = normalize_doc_string(row.get("close_note", ""))
    docs = combined_document_text(
        row.get("document_origin", ""),
        row.get("document_history", ""),
        row.get("cycle_history", ""),
    )
    is_partner = sid.startswith("V")
    has_collect = "قبض" in docs
    has_sale = "مبيع خ ص" in docs
    has_entry = "اد خ ص" in docs
    has_partner_settlement = "خ صيانة" in docs

    if case_status == CASE_STATUS_CLOSED and closed_by and closed_by != "Ameen Import":
        return WF_CLOSED_TV
    if "فاتورة" in close_note and "صفر" in close_note:
        return WF_CLOSED_ZERO
    if has_collect:
        return WF_CLOSED_COLLECTED

    # Zero-invoice rule applies only when this is an Ameen-derived sale row.
    technician = normalize_doc_string(row.get("technician", ""))
    zero_confirmed = int(clean_number(row.get("cycle_zero_sales_confirmed", 0), 0)) == 1
    if technician == "Ameen Import" and has_sale and zero_confirmed:
        return WF_CLOSED_ZERO

    if is_partner and has_partner_settlement:
        return WF_CLOSED_PARTNER
    if is_partner and has_sale:
        return WF_WAIT_PARTNER
    if (sid.startswith("S") or sid.startswith("D")) and has_sale:
        return WF_WAIT_COLLECTION
    if has_entry:
        return WF_IN_REPAIR
    if case_status == CASE_STATUS_CLOSED:
        return WF_CLOSED_COLLECTED
    return WF_WAITING


def category_for_workflow(workflow_state):
    wf = normalize_doc_string(workflow_state)
    if wf in {WF_IN_REPAIR, WF_WAITING}:
        return "progress"
    if wf == WF_WAIT_COLLECTION:
        return "collection"
    if wf == WF_WAIT_PARTNER:
        return "partner"
    if wf == WF_CLOSED_ZERO:
        return "zero"
    if wf in {WF_CLOSED_COLLECTED, WF_CLOSED_TV}:
        return "collected"
    if wf == WF_CLOSED_PARTNER:
        return "partner_closed"
    return "progress"


def parse_days(date_value):
    try:
        parsed = pd.to_datetime(normalize_doc_string(date_value), errors="coerce")
        if pd.isna(parsed):
            return 0
        return max((datetime.now() - parsed).days, 0)
    except Exception:
        return 0



# GP_FOLLOWUP_TV_API_V1
FOLLOWUP_CLOSED_STATUSES = {"Done", "Closed", "مغلق", "منجز"}


def get_tv_followups():
    """Read structured FollowUp items from the same editable spreadsheet when available."""
    global followup_sheet
    try:
        if followup_sheet is None:
            maybe_reconnect_google_sheets(force=True)
            if spreadsheet_obj is not None and followup_sheet is None:
                try:
                    followup_sheet = spreadsheet_obj.worksheet("FollowUp")
                except Exception:
                    return []
        if followup_sheet is None:
            return []
        df = dataframe_from_worksheet(followup_sheet).dropna(how="all")
        if df.empty or "followup_id" not in df.columns:
            return []
        defaults = {
            "type":"", "related_id":"", "title":"", "owner":"", "waiting_on":"", "priority":"Normal",
            "status":"Open", "created_at":"", "next_followup":"", "last_update":"", "next_action":"",
            "history":"", "source":"", "closed_at":"", "closed_by":"",
        }
        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default
        records = []
        today = pd.Timestamp(datetime.now().date())
        for _, row in df.iterrows():
            status = normalize_doc_string(row.get("status", "")) or "Open"
            if status in FOLLOWUP_CLOSED_STATUSES:
                continue
            due_raw = normalize_doc_string(row.get("next_followup", ""))
            due = pd.to_datetime(due_raw, errors="coerce")
            timing = "unscheduled"
            days_overdue = 0
            if pd.notna(due):
                due_day = pd.Timestamp(due.date())
                if due_day < today:
                    timing = "overdue"
                    days_overdue = int((today - due_day).days)
                elif due_day == today:
                    timing = "today"
                else:
                    timing = "future"
            records.append({
                "followup_id": normalize_doc_string(row.get("followup_id", "")),
                "type": normalize_doc_string(row.get("type", "")),
                "related_id": normalize_doc_string(row.get("related_id", "")),
                "title": normalize_doc_string(row.get("title", "")),
                "owner": normalize_doc_string(row.get("owner", "")),
                "waiting_on": normalize_doc_string(row.get("waiting_on", "")),
                "priority": normalize_doc_string(row.get("priority", "")) or "Normal",
                "status": status,
                "created_at": normalize_doc_string(row.get("created_at", "")),
                "next_followup": due_raw,
                "last_update": normalize_doc_string(row.get("last_update", "")),
                "next_action": normalize_doc_string(row.get("next_action", "")),
                "history": normalize_doc_string(row.get("history", "")),
                "source": normalize_doc_string(row.get("source", "")),
                "timing": timing,
                "days_overdue": days_overdue,
            })
        priority_rank = {"Urgent":0, "Important":1, "Normal":2}
        timing_rank = {"overdue":0, "today":1, "unscheduled":2, "future":3}
        records.sort(key=lambda x: (timing_rank.get(x["timing"], 9), priority_rank.get(x["priority"], 9), x["next_followup"], x["followup_id"]))
        return records
    except Exception as exc:
        print("FollowUp TV read error:", repr(exc))
        return []


# ==========================================================
# READ TV DATA
# ==========================================================


def read_published_csv(url, **kwargs):
    """Read published Google CSV with a hard timeout so TV requests cannot hang."""
    response = HTTP_SESSION.get(url, timeout=(2.5, 5.0))
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text), **kwargs)


def dataframe_from_worksheet(worksheet):
    values = worksheet.get_all_values()

    if not values:
        return pd.DataFrame()

    headers = [normalize_doc_string(value) for value in values[0]]

    # Make duplicate/blank headers safe for pandas.
    seen = {}
    safe_headers = []
    for index, header in enumerate(headers):
        base = header or f"column_{index + 1}"
        count = seen.get(base, 0)
        seen[base] = count + 1
        safe_headers.append(base if count == 0 else f"{base}_{count + 1}")

    width = len(safe_headers)
    rows = []
    for raw_row in values[1:]:
        row = list(raw_row[:width])
        if len(row) < width:
            row.extend([""] * (width - len(row)))
        rows.append(row)

    return pd.DataFrame(rows, columns=safe_headers)


def read_live_or_published_main():
    """Read the exact Tools Tracker Ledger, with published CSV only as fallback.

    This function is called from the background cache worker, never from the
    initial /tv page render, so a live Google read cannot block Render
    startup or make the TV page itself slow.
    """
    global LAST_READ_SOURCE

    # First choice: the same editable spreadsheet + named Ledger worksheet used
    # by tools_tracker.py. This keeps TV counts/details synchronized with the app.
    try:
        if main_sheet is None:
            maybe_reconnect_google_sheets(force=True)
        if main_sheet is not None:
            df = dataframe_from_worksheet(main_sheet)
            if "service_id" in df.columns:
                LAST_READ_SOURCE = "tools_tracker_ledger_live"
                return df
    except Exception as exc:
        print("Tools Tracker Ledger live read error:", repr(exc))

    # Fallback keeps the TV useful if the Google API/service account is briefly
    # unavailable. It is not considered the authoritative source.
    LAST_READ_SOURCE = "published_csv_fallback"
    return read_published_csv(SHEET_CSV_URL)


def read_live_or_published_remarks():
    """Fast TV remarks read path; it must not overwrite the main Ledger source label."""
    result = []
    try:
        df_rem = read_published_csv(REMARKS_CSV_URL, header=None)
        for idx, row in df_rem.iterrows():
            if len(row) == 0:
                continue
            text = str(row.iloc[0]).strip()
            if text and text.lower() not in {"nan", "unnamed: 0", ""}:
                result.append({"row": int(idx + 1), "text": text})
    except Exception as exc:
        print("Remarks published read error:", repr(exc))

    return result


def load_tv_cache():
    """Return the current in-memory dashboard snapshot without disk I/O."""
    with _TV_CACHE_LOCK:
        if isinstance(_TV_CACHE_DATA, dict):
            return _TV_CACHE_DATA, _TV_CACHE_SAVED_AT
    return None, 0.0


def save_tv_cache(data):
    """Store a successful dashboard snapshot in memory only."""
    global _TV_CACHE_DATA, _TV_CACHE_SAVED_AT
    if not isinstance(data, dict):
        return
    with _TV_CACHE_LOCK:
        _TV_CACHE_DATA = data
        _TV_CACHE_SAVED_AT = time.time()


def invalidate_tv_cache():
    """Mark the current snapshot stale without discarding it from the screen."""
    global _TV_CACHE_SAVED_AT
    with _TV_CACHE_LOCK:
        _TV_CACHE_SAVED_AT = 0.0


def _empty_tv_payload():
    """Small immediate response while the first background refresh is warming."""
    data = {
        "progress_count": 0,
        "collection_count": 0,
        "partner_count": 0,
        "zero_count": 0,
        "collected_count": 0,
        "partner_closed_count": 0,
        "urgent_count": 0,
        "delayed_count": 0,
        "special_count": 0,
        "followup_open_count": 0,
        "followup_overdue_count": 0,
        "followup_due_today_count": 0,
        "followup_spare_parts_count": 0,
        "followup_inquiry_count": 0,
        "followup_list": [],
        "followup_overdue_list": [],
        "followup_due_today_list": [],
        "followup_spare_parts_list": [],
        "followup_inquiry_list": [],
        "progress_list": [],
        "collection_list": [],
        "partner_list": [],
        "zero_list": [],
        "collected_list": [],
        "partner_closed_list": [],
        "urgent_list": [],
        "delayed_list": [],
        "special_list": [],
        "remarks_list": list(_REMARKS_CACHE),
        "write_ready": write_ready(),
        "read_source": "warming_cache",
        "write_error": LAST_WRITE_ERROR if not write_ready() else "",
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "loading": True,
        "refreshing": True,
    }
    data["in_progress"] = 0
    data["partner_claim_count"] = 0
    data["partner_claim_list"] = []
    data["ready"] = 0
    data["ready_list"] = []
    data["delayed"] = 0
    data["announcement_text"] = ""
    data["announcement_audio"] = ""
    return data


def _refresh_tv_cache_worker():
    global _TV_REFRESHING, _TV_LAST_REFRESH_ERROR
    try:
        fresh = build_tv_api_payload()
        has_any_queue_data = any(fresh.get(key) for key in (
            "progress_list", "collection_list", "partner_list",
            "zero_list", "collected_list", "partner_closed_list"
        ))
        cached, _ = load_tv_cache()
        # Keep the last known good snapshot if Google/published CSV briefly
        # returns an accidental empty result.  On the first ever load, allow an
        # empty but valid result so the UI still completes its warm-up state.
        if has_any_queue_data or not cached:
            fresh["loading"] = False
            fresh["refreshing"] = False
            save_tv_cache(fresh)
            _TV_LAST_REFRESH_ERROR = ""
        else:
            _TV_LAST_REFRESH_ERROR = "Tools Tracker Ledger returned no queue rows; previous snapshot kept."
    except Exception as exc:
        _TV_LAST_REFRESH_ERROR = f"{type(exc).__name__}: {exc}"
        print("TV background refresh error:", repr(exc))
    finally:
        with _TV_REFRESH_LOCK:
            _TV_REFRESHING = False


def start_tv_refresh(force=False):
    """Start one background Google refresh without ever breaking /api/data."""
    global _TV_REFRESHING, _TV_LAST_REFRESH_ERROR
    cached, saved_at = load_tv_cache()
    if not force and cached and (time.time() - saved_at) < TV_CACHE_TTL_SECONDS:
        return False

    with _TV_REFRESH_LOCK:
        if _TV_REFRESHING:
            return False
        _TV_REFRESHING = True

    try:
        thread = threading.Thread(
            target=_refresh_tv_cache_worker,
            name="golden-palace-tv-refresh",
            daemon=True,
        )
        thread.start()
        return True
    except Exception as exc:
        with _TV_REFRESH_LOCK:
            _TV_REFRESHING = False
        _TV_LAST_REFRESH_ERROR = f"Refresh thread start failed: {type(exc).__name__}: {exc}"
        print("TV refresh thread start error:", repr(exc))
        return False


def get_cached_remarks(force=False):
    """Remarks use their own slower refresh so they never delay the six main counters."""
    global _REMARKS_CACHE, _REMARKS_CACHE_SAVED_AT
    now = time.time()
    if not force and _REMARKS_CACHE and (now - _REMARKS_CACHE_SAVED_AT) < REMARKS_CACHE_TTL_SECONDS:
        return list(_REMARKS_CACHE)
    try:
        fresh = read_live_or_published_remarks()
        _REMARKS_CACHE = fresh
        _REMARKS_CACHE_SAVED_AT = now
    except Exception as exc:
        print("Remarks cache refresh error:", repr(exc))
    return list(_REMARKS_CACHE)


def get_tv_queue(include_remarks=False):
    """Return one current record per service ID, including open and closed states."""
    try:
        df = read_live_or_published_main().dropna(how="all")
        if "service_id" not in df.columns:
            return [], []

        df["service_id"] = df["service_id"].apply(normalize_doc_string)
        df = df[df["service_id"].str.strip() != ""].copy()

        defaults = {
            "cycle_no": 0,
            "cycle_key": "",
            "cycle_started_at": "",
            "cycle_last_event_date": "",
            "cycle_last_event": "",
            "cycle_document_count": 0,
            "cycle_sales_total": 0.0,
            "cycle_zero_sales_confirmed": 0,
            "cycle_payment_total": 0.0,
            "cycle_partner_settlement_total": 0.0,
            "cycle_history": "",
            "workflow_state": "",
            "financial_status": "",
            "collection_status": "",
            "special_case": "",
            "partner_claim_status": "غير منطبق",
            "repair_stage": "",
            "document_history": "",
            "source_document_count": 1,
            "case_status": CASE_STATUS_OPEN,
            "closed_at": "",
            "closed_by": "",
            "close_note": "",
            "warranty_status": "",
            "document_origin": "",
            "remarks": "",
            "status": "",
            "priority": "",
            "date_logged": "",
            "date_resolved": "",
            "tool_name": "",
            "customer_name": "",
            "phone_number": "",
            "reported_issue": "",
            "technician": "",
        }
        for col, default in defaults.items():
            if col not in df.columns:
                df[col] = default

        # If duplicate legacy rows exist, newest cycle wins even when an older row is closed.
        df["_cycle_sort"] = pd.to_numeric(df["cycle_no"], errors="coerce").fillna(0)
        df["_date_sort"] = pd.to_datetime(
            df["cycle_last_event_date"].replace("", pd.NA).fillna(df["date_resolved"].replace("", pd.NA)).fillna(df["date_logged"]),
            errors="coerce",
        )
        df = df.sort_values(["service_id", "_cycle_sort", "_date_sort"], kind="stable")
        df = df.groupby("service_id", as_index=False).tail(1).reset_index(drop=True)

        remarks_list = get_cached_remarks() if include_remarks else list(_REMARKS_CACHE)
        records = []
        for _, row in df.iterrows():
            sid = normalize_doc_string(row.get("service_id", "")).upper()
            wf = derive_workflow_state(row)
            category = category_for_workflow(wf)
            special = normalize_doc_string(row.get("special_case", "")) or special_case_from_remarks(row.get("remarks", ""))
            status = status_from_workflow(wf, special)
            case_status = CASE_STATUS_CLOSED if wf in CLOSED_WORKFLOW_STATES else CASE_STATUS_OPEN

            cycle_started_at = normalize_doc_string(row.get("cycle_started_at", "")) or normalize_doc_string(row.get("date_logged", ""))
            cycle_last_event_date = normalize_doc_string(row.get("cycle_last_event_date", "")) or normalize_doc_string(row.get("date_resolved", "")) or cycle_started_at
            days = parse_days(cycle_started_at)
            days_since_last_event = parse_days(cycle_last_event_date)

            priority_raw = normalize_doc_string(row.get("priority", ""))
            is_urgent = "عاجل" in priority_raw or "urgent" in priority_raw.lower()
            is_delayed = wf not in CLOSED_WORKFLOW_STATES and days >= 3
            can_close = (sid.startswith("S") or sid.startswith("D")) and wf == WF_WAIT_COLLECTION

            collection_status = normalize_doc_string(row.get("collection_status", ""))
            if not collection_status:
                if wf in {WF_CLOSED_COLLECTED, WF_CLOSED_TV}:
                    collection_status = COLLECTION_CLOSED
                elif wf == WF_CLOSED_ZERO:
                    collection_status = COLLECTION_ZERO_NOT_REQUIRED
                elif wf in {WF_WAIT_PARTNER, WF_CLOSED_PARTNER}:
                    collection_status = COLLECTION_PARTNER_NOT_APPLICABLE
                elif wf == WF_WAIT_COLLECTION:
                    collection_status = COLLECTION_SPECIAL_AWAITING if special else COLLECTION_AWAITING
                else:
                    collection_status = COLLECTION_NOT_READY

            financial_status = normalize_doc_string(row.get("financial_status", ""))
            if not financial_status:
                docs = combined_document_text(row.get("document_origin", ""), row.get("document_history", ""), row.get("cycle_history", ""))
                if "قبض" in docs:
                    financial_status = "قبض مسجل"
                elif "خ صيانة" in docs:
                    financial_status = "خ صيانة مسجلة"
                elif "مبيع خ ص" in docs and int(clean_number(row.get("cycle_zero_sales_confirmed", 0), 0)) == 1:
                    financial_status = "فاتورة مبيع صفر"
                elif "مبيع خ ص" in docs:
                    financial_status = "فاتورة مبيع قائمة"
                else:
                    financial_status = "لا توجد فاتورة مبيع"

            records.append({
                "service_id": sid,
                "cycle_no": int(clean_number(row.get("cycle_no", 0), 0)),
                "cycle_key": normalize_doc_string(row.get("cycle_key", "")),
                "cycle_started_at": cycle_started_at,
                "cycle_last_event_date": cycle_last_event_date,
                "cycle_last_event": normalize_doc_string(row.get("cycle_last_event", "")) or normalize_doc_string(row.get("document_origin", "")),
                "cycle_document_count": int(clean_number(row.get("cycle_document_count", 0), 0)),
                "cycle_sales_total": clean_number(row.get("cycle_sales_total", row.get("cost_debit", 0)), 0),
                "cycle_zero_sales_confirmed": int(clean_number(row.get("cycle_zero_sales_confirmed", 0), 0)),
                "cycle_payment_total": clean_number(row.get("cycle_payment_total", row.get("payment_credit", 0)), 0),
                "cycle_partner_settlement_total": clean_number(row.get("cycle_partner_settlement_total", row.get("partner_claim_amount", 0)), 0),
                "cycle_history": normalize_doc_string(row.get("cycle_history", "")),
                "workflow_state": wf,
                "category": category,
                "status": status,
                "financial_status": financial_status,
                "case_status": case_status,
                "collection_status": collection_status,
                "partner_claim_status": normalize_doc_string(row.get("partner_claim_status", "")),
                "special_case": special,
                "service_age_days": days,
                "days_since_last_event": days_since_last_event,
                "priority": "عاجل" if is_urgent else "عادي",
                "is_urgent": bool(is_urgent),
                "is_delayed": bool(is_delayed),
                "can_close_from_tv": bool(can_close),
                "tool_name": normalize_doc_string(row.get("tool_name", "")),
                "customer_name": normalize_doc_string(row.get("customer_name", "")),
                "phone_number": normalize_doc_string(row.get("phone_number", "")),
                "reported_issue": normalize_doc_string(row.get("reported_issue", "")),
                "remarks": normalize_doc_string(row.get("remarks", "")),
                "warranty_status": normalize_doc_string(row.get("warranty_status", "")),
                "document_origin": normalize_doc_string(row.get("document_origin", "")),
                "document_history": normalize_doc_string(row.get("document_history", "")),
                "date_logged": normalize_doc_string(row.get("date_logged", "")),
                "date_resolved": normalize_doc_string(row.get("date_resolved", "")),
                "closed_at": normalize_doc_string(row.get("closed_at", "")),
                "closed_by": normalize_doc_string(row.get("closed_by", "")),
                "close_note": normalize_doc_string(row.get("close_note", "")),
            })

        records.sort(key=lambda item: (
            item["workflow_state"] in CLOSED_WORKFLOW_STATES,
            not item["is_urgent"],
            -item["service_age_days"],
            item["service_id"],
        ))
        return records, remarks_list

    except Exception as exc:
        print("Main sheet error:", repr(exc))
        return [], []


def separate_jobs(records):
    """Six primary, mutually-exclusive dashboard tabs plus urgency metadata."""
    result = {
        "progress": [],
        "collection": [],
        "partner": [],
        "zero": [],
        "collected": [],
        "partner_closed": [],
        "urgent": [],
        "delayed": [],
        "special": [],
    }
    for record in records:
        category = record.get("category", "progress")
        if category in result:
            result[category].append(record)
        if record.get("is_urgent") and record.get("workflow_state") not in CLOSED_WORKFLOW_STATES:
            result["urgent"].append(record)
        if record.get("is_delayed"):
            result["delayed"].append(record)
        if record.get("special_case"):
            result["special"].append(record)
    return result


# ==========================================================
# ENCOURAGING ARABIC ANNOUNCEMENT
# ==========================================================


def build_encouragement(data):
    urgent_list = data.get("urgent_list", [])
    delayed_list = data.get("delayed_list", [])
    ready_list = data.get("ready_list", [])
    progress_list = data.get("progress_list", [])
    collection_list = data.get("collection_list", [])
    partner_claim_list = data.get("partner_list", data.get("partner_claim_list", []))
    remarks_list = data.get("remarks_list", [])

    messages = []

    if urgent_list:
        item = urgent_list[0]
        messages.append(
            f"تنبيه عاجل لفريق القصر الذهبي. المهمة رقم {item.get('service_id', '')} "
            "تحتاج متابعة فورية وعدم التأخير."
        )

    if delayed_list:
        item = delayed_list[0]
        messages.append(
            f"تنبيه متابعة. المهمة رقم {item.get('service_id', '')} متأخرة "
            f"منذ {item.get('days', 0)} أيام وتحتاج إجراء واضح اليوم."
        )

    if collection_list:
        item = collection_list[0]
        messages.append(
            f"تنبيه الاستلام. الجهاز {item.get('service_id', '')} بانتظار تأكيد الاستلام. "
            "عند استلام الزبون يرجى إغلاقه مباشرة من شاشة التلفزيون."
        )

    if partner_claim_list:
        item = partner_claim_list[0]
        messages.append(
            f"تنبيه مالي. حالة الشريك {item.get('service_id', '')} تحتاج متابعة مطالبة الشريك."
        )

    if remarks_list:
        remark = remarks_list[0]
        messages.append(
            f"تنبيه ملاحظة لفريق القصر الذهبي. {remark.get('text', '')}. "
            "يرجى المتابعة ثم إغلاق الملاحظة عند الانتهاء."
        )

    if ready_list:
        item = ready_list[0]
        messages.append(
            f"المعدة رقم {item.get('service_id', '')} جاهزة للتسليم. يرجى متابعة تسليمها للزبون."
        )

    if progress_list:
        item = progress_list[0]
        messages.append(
            f"العمل مستمر على المهمة رقم {item.get('service_id', '')}. "
            "يرجى المحافظة على تحديث الحالة وعدم تركها بدون متابعة."
        )

    if not messages:
        messages.append(
            "يعطيكم العافية يا فريق القصر الذهبي. لا توجد حالياً تنبيهات معلقة، "
            "ونستمر بالدقة والمتابعة."
        )

    index = datetime.now().second % len(messages)
    return messages[index]


# ==========================================================
# ELEVENLABS AUDIO
# ==========================================================


def generate_human_audio(text):
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        return None

    audio_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    filename = f"announcement_{audio_hash}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    if os.path.exists(filepath):
        return "/static/generated_audio/" + filename

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
        params = {"output_format": "mp3_44100_128"}
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {"text": text, "model_id": "eleven_multilingual_v2"}

        response = requests.post(
            url,
            params=params,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            print("ElevenLabs error:", response.status_code, response.text)
            return None

        with open(filepath, "wb") as audio_file:
            audio_file.write(response.content)

        return "/static/generated_audio/" + filename

    except Exception as exc:
        print("ElevenLabs generation error:", repr(exc))
        return None


# ==========================================================
# TV PAGE
# ==========================================================


@app.route("/")
@app.route("/t")
def root_health():
    return tv_display()


@app.route("/tv")
def tv_display():
    """Serve the TV page as plain HTML, bypassing Jinja completely.

    The TV page is intentionally self-contained and loads its live data from
    /api/data. Serving the file directly prevents a missing template variable
    or Jinja parsing issue from turning /tv into a generic HTTP 500.
    """
    tv_path = os.path.join(BASE_DIR, "templates", "tv.html")

    if not os.path.isfile(tv_path):
        # Return a useful message instead of Render's generic 500 page.
        templates_dir = os.path.join(BASE_DIR, "templates")
        try:
            found = sorted(os.listdir(templates_dir)) if os.path.isdir(templates_dir) else []
        except Exception:
            found = []
        return (
            "TV file not found. Expected: " + tv_path +
            "\nFiles currently in templates/: " + ", ".join(found),
            500,
            {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"},
        )

    try:
        with open(tv_path, "r", encoding="utf-8") as tv_file:
            html = tv_file.read()
        return (
            html,
            200,
            {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store, no-cache, must-revalidate"},
        )
    except Exception as exc:
        return (
            f"TV file read error: {type(exc).__name__}: {exc}",
            500,
            {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"},
        )


# ==========================================================
# API DATA
# ==========================================================


def build_tv_api_payload():
    records, _ = get_tv_queue(include_remarks=False)
    groups = separate_jobs(records)
    followups = get_tv_followups()
    followup_overdue = [x for x in followups if x.get("timing") == "overdue"]
    followup_today = [x for x in followups if x.get("timing") == "today"]
    followup_spares = [x for x in followups if x.get("type") == "Spare Part"]
    followup_inquiries = [x for x in followups if x.get("type") in {"Customer Inquiry", "Supplier Inquiry"}]

    data = {
        "progress_count": len(groups["progress"]),
        "collection_count": len(groups["collection"]),
        "partner_count": len(groups["partner"]),
        "zero_count": len(groups["zero"]),
        "collected_count": len(groups["collected"]),
        "partner_closed_count": len(groups["partner_closed"]),
        "urgent_count": len(groups["urgent"]),
        "delayed_count": len(groups["delayed"]),
        "special_count": len(groups["special"]),
        "followup_open_count": len(followups),
        "followup_overdue_count": len(followup_overdue),
        "followup_due_today_count": len(followup_today),
        "followup_spare_parts_count": len(followup_spares),
        "followup_inquiry_count": len(followup_inquiries),
        "followup_list": followups,
        "followup_overdue_list": followup_overdue,
        "followup_due_today_list": followup_today,
        "followup_spare_parts_list": followup_spares,
        "followup_inquiry_list": followup_inquiries,
        "progress_list": groups["progress"],
        "collection_list": groups["collection"],
        "partner_list": groups["partner"],
        "zero_list": groups["zero"],
        "collected_list": groups["collected"],
        "partner_closed_list": groups["partner_closed"],
        "urgent_list": groups["urgent"],
        "delayed_list": groups["delayed"],
        "special_list": groups["special"],
        "remarks_list": list(_REMARKS_CACHE),
        "write_ready": write_ready(),
        "read_source": LAST_READ_SOURCE,
        "write_error": LAST_WRITE_ERROR if not write_ready() else "",
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Backward-compatible aliases.
    data["in_progress"] = data["progress_count"]
    data["partner_claim_count"] = data["partner_count"]
    data["partner_claim_list"] = data["partner_list"]
    data["ready"] = data["collection_count"]
    data["ready_list"] = data["collection_list"]
    data["delayed"] = data["delayed_count"]
    data["announcement_text"] = ""
    data["announcement_audio"] = ""
    return data


@app.route("/api/data")
def api_data():
    """Never return HTTP 500 to the TV for cache/refresh errors.

    The live Google Ledger refresh still runs in the background.  If a local
    cache-management error happens, return a small diagnostic payload with HTTP
    200 so the browser can keep retrying instead of freezing at `API 500`.
    """
    try:
        force = str(request.args.get("force", "")).lower() in {"1", "true", "yes"}
        cached, saved_at = load_tv_cache()
        now = time.time()

        age = max(now - saved_at, 0) if saved_at else None
        stale = (not cached) or force or (age is not None and age >= TV_CACHE_TTL_SECONDS)
        if stale:
            start_tv_refresh(force=force)

        if cached:
            response = dict(cached)
            response["cache_age_seconds"] = round(age or 0, 1)
            response["refreshing"] = bool(_TV_REFRESHING)
            response["loading"] = False
            if _TV_LAST_REFRESH_ERROR:
                response["refresh_error"] = _TV_LAST_REFRESH_ERROR
            return jsonify(response)

        # First request after a WSGI restart: return immediately while the
        # background worker loads the exact Tools Tracker Ledger worksheet.
        response = _empty_tv_payload()
        if _TV_LAST_REFRESH_ERROR:
            response["refresh_error"] = _TV_LAST_REFRESH_ERROR
        return jsonify(response)

    except Exception as exc:
        # The TV must remain reachable even if an unexpected cache error occurs.
        # Surface the exact backend error in JSON for diagnosis, but keep HTTP 200
        # so the frontend continues its retry cycle.
        print("/api/data safety error:", repr(exc))
        response = _empty_tv_payload()
        response["loading"] = True
        response["refreshing"] = False
        response["refresh_error"] = f"{type(exc).__name__}: {exc}"
        response["read_source"] = "api_safety_fallback"
        return jsonify(response)


@app.route("/api/remarks")
def api_remarks():
    force = str(request.args.get("force", "")).lower() in {"1", "true", "yes"}
    remarks = get_cached_remarks(force=force)
    return jsonify({"remarks_list": remarks, "count": len(remarks)})


@app.route("/api/health")
def api_health():
    force = str(request.args.get("reconnect", "")).lower() in {"1", "true", "yes"}

    if force:
        initialize_google_sheets()

    configured_creds_path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        CREDS_PATH,
    ).strip() or CREDS_PATH

    return jsonify(
        {
            "status": "ok",
            "read_source": LAST_READ_SOURCE,
            "write_ready": write_ready(),
            "google_sheet_id_configured": bool(SHEET_ID),
            "credentials_found": (
                os.path.exists(configured_creds_path)
                or bool(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip())
            ),
            "write_error": LAST_WRITE_ERROR if not write_ready() else "",
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


# ==========================================================
# SHEET WRITE HELPERS
# ==========================================================


def ensure_write_connection():
    if write_ready():
        return True
    return maybe_reconnect_google_sheets(force=True)


def worksheet_values_and_headers(worksheet):
    values = worksheet.get_all_values()
    if not values:
        return [], []
    headers = [normalize_doc_string(value) for value in values[0]]
    return values, headers


def ensure_columns(worksheet, headers, required_columns):
    headers = list(headers)

    for column_name in required_columns:
        if column_name not in headers:
            headers.append(column_name)
            worksheet.update_cell(1, len(headers), column_name)

    return headers


def find_service_row(values, headers, service_id, cycle_key=""):
    if "service_id" not in headers:
        return None

    service_col = headers.index("service_id")
    cycle_col = headers.index("cycle_key") if "cycle_key" in headers else None
    requested_cycle = normalize_doc_string(cycle_key)

    candidates = []
    for row_number, row_values in enumerate(values[1:], start=2):
        current_sid = normalize_doc_string(row_values[service_col]) if service_col < len(row_values) else ""
        if current_sid.upper() != service_id.upper():
            continue
        if requested_cycle and cycle_col is not None:
            current_cycle = normalize_doc_string(row_values[cycle_col]) if cycle_col < len(row_values) else ""
            if current_cycle != requested_cycle:
                continue
        candidates.append(row_number)

    return candidates[-1] if candidates else None

    service_col = headers.index("service_id")

    for row_number, row_values in enumerate(values[1:], start=2):
        current_sid = (
            normalize_doc_string(row_values[service_col])
            if service_col < len(row_values)
            else ""
        )
        if current_sid.upper() == service_id.upper():
            return row_number

    return None


# ==========================================================
# CLOSE REMARK
# ==========================================================


@app.route("/api/delete-remark", methods=["POST"])
def delete_remark():
    global remarks_sheet

    try:
        data = request.get_json(silent=True) or {}
        row_num = data.get("row")

        if not row_num:
            return jsonify({"status": "error", "message": "رقم الملاحظة غير موجود."}), 400

        row_num = int(row_num)

        # Optional Apps Script write path.
        if GOOGLE_APPS_SCRIPT_URL:
            try:
                response = requests.post(
                    GOOGLE_APPS_SCRIPT_URL,
                    json={
                        "action": "delete_remark",
                        "row": row_num,
                        "secret": GOOGLE_APPS_SCRIPT_SECRET,
                    },
                    timeout=20,
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "success":
                        global _REMARKS_CACHE_SAVED_AT
                        _REMARKS_CACHE_SAVED_AT = 0.0
                        invalidate_tv_cache()
                        return jsonify(
                            {
                                "status": "success",
                                "row": row_num,
                                "method": "apps_script",
                            }
                        )

                print("Apps Script response:", response.text)

            except Exception as exc:
                print("Apps Script write error:", repr(exc))

        if not ensure_write_connection() or remarks_sheet is None:
            return jsonify(
                {
                    "status": "error",
                    "message": (
                        "تعذر الاتصال بـ Google Sheets للكتابة. "
                        "تأكد من GOOGLE_SHEET_ID وأن credentials.json موجود، "
                        "وأن Service Account لديه صلاحية Editor على الملف الأصلي."
                    ),
                }
            ), 500

        remarks_sheet.update_cell(row_num, 1, "")
        _REMARKS_CACHE_SAVED_AT = 0.0
        invalidate_tv_cache()

        return jsonify(
            {
                "status": "success",
                "row": row_num,
                "method": "gspread",
            }
        )

    except Exception as exc:
        print("Delete remark exception:", repr(exc))
        return jsonify({"status": "error", "message": str(exc)}), 500


# ==========================================================
# CONFIRM CUSTOMER COLLECTION / CLOSE TICKET
# ==========================================================


@app.route("/api/close-ticket", methods=["POST"])
def close_ticket():
    global main_sheet

    try:
        data = request.get_json(silent=True) or {}
        service_id = normalize_doc_string(data.get("service_id", "")).upper()
        requested_cycle_key = normalize_doc_string(data.get("cycle_key", ""))

        if not service_id:
            return jsonify(
                {"status": "error", "message": "رقم سند الصيانة غير موجود."}
            ), 400

        # Only customer S/D cases can be manually confirmed from TV.
        if not (service_id.startswith("S") or service_id.startswith("D")):
            return jsonify(
                {
                    "status": "error",
                    "message": "حالات الشريك V لا تغلق يدوياً من شاشة استلام الزبون.",
                }
            ), 400

        # Validate against current TV queue so an in-progress job cannot be closed
        # by manually calling the endpoint.
        jobs, _ = get_tv_queue()
        current_job = next(
            (
                job
                for job in jobs
                if normalize_doc_string(job.get("service_id", "")).upper()
                == service_id
            ),
            None,
        )

        if current_job is None:
            return jsonify(
                {
                    "status": "error",
                    "message": "الحالة غير موجودة ضمن الحالات المفتوحة الحالية.",
                }
            ), 404

        if requested_cycle_key and normalize_doc_string(current_job.get("cycle_key", "")) != requested_cycle_key:
            return jsonify({
                "status": "error",
                "message": "This detail window is stale. The ticket has moved to a different repair cycle. Refresh before closing.",
            }), 409

        if not current_job.get("can_close_from_tv"):
            return jsonify(
                {
                    "status": "error",
                    "message": (
                        "هذه الحالة ليست جاهزة أو بانتظار الاستلام، "
                        "لذلك لا يمكن إغلاقها من شاشة TV."
                    ),
                }
            ), 400

        if not ensure_write_connection() or main_sheet is None:
            return jsonify(
                {
                    "status": "error",
                    "message": (
                        "تعذر الاتصال بجدول Ledger للكتابة. "
                        "تأكد من GOOGLE_SHEET_ID و credentials.json وصلاحية Editor."
                    ),
                }
            ), 500

        values, headers = worksheet_values_and_headers(main_sheet)

        if not values:
            return jsonify({"status": "error", "message": "جدول Ledger فارغ."}), 404

        if "service_id" not in headers:
            return jsonify(
                {"status": "error", "message": "عمود service_id غير موجود في Ledger."}
            ), 500

        target_row = find_service_row(values, headers, service_id, requested_cycle_key)
        if target_row is None:
            return jsonify(
                {
                    "status": "error",
                    "message": f"لم يتم العثور على السند {service_id} في Ledger.",
                }
            ), 404

        required_columns = [
            "workflow_state",
            "case_status",
            "collection_status",
            "repair_stage",
            "status",
            "date_resolved",
            "closed_at",
            "closed_by",
            "close_note",
        ]
        headers = ensure_columns(main_sheet, headers, required_columns)

        closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        close_note = normalize_doc_string(data.get("note", ""))
        if not close_note:
            close_note = "تأكيد استلام يدوي من شاشة TV"

        updates = {
            "workflow_state": WF_CLOSED_TV,
            "case_status": CASE_STATUS_CLOSED,
            "collection_status": COLLECTION_CLOSED,
            "repair_stage": CASE_STATUS_CLOSED,
            "status": "مغلق - تم الاستلام (Closed)",
            "date_resolved": closed_at.split(" ")[0],
            "closed_at": closed_at,
            "closed_by": "TV",
            "close_note": close_note,
        }

        for column_name, value in updates.items():
            column_number = headers.index(column_name) + 1
            main_sheet.update_cell(target_row, column_number, value)

        invalidate_tv_cache()
        start_tv_refresh(force=True)

        return jsonify(
            {
                "status": "success",
                "service_id": service_id,
                "closed_at": closed_at,
                "cycle_key": requested_cycle_key or normalize_doc_string(current_job.get("cycle_key", "")),
                "message": "تم تأكيد الاستلام وإغلاق دورة الصيانة الحالية.",
            }
        )

    except Exception as exc:
        print("Close ticket exception:", repr(exc))
        return jsonify({"status": "error", "message": str(exc)}), 500


# ==========================================================
# START
# ==========================================================


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
