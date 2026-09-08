# Trigger marker: 2026-09-08 server voice validation
from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing marker: {label}")
    return text.replace(old, new, 1)

# ------------------------------------------------------------------
# requirements.txt: server-side neural speech, independent of browser
# ------------------------------------------------------------------
req_path = Path('requirements.txt')
req = req_path.read_text(encoding='utf-8')
if 'edge-tts' not in req.lower():
    req = req.rstrip() + '\nedge-tts>=7.2,<8\n'
    req_path.write_text(req, encoding='utf-8')

# ------------------------------------------------------------------
# Flask backend voice generator
# ------------------------------------------------------------------
flask_path = Path('flask_app.py')
flask = flask_path.read_text(encoding='utf-8')
if 'GP_SERVER_SYRIAN_VOICE_V2' not in flask:
    flask = replace_once(flask, 'import hashlib\n', 'import hashlib\nimport asyncio\nimport random\nimport tempfile\n', 'flask imports')
    flask = replace_once(flask, 'from flask import Flask, jsonify, render_template, request\n', 'from flask import Flask, jsonify, render_template, request, send_file\n', 'flask send_file import')

    marker = '# ==========================================================\n# WORKFLOW CONSTANTS\n# =========================================================='
    voice_backend = r'''
# ==========================================================
# GP_SERVER_SYRIAN_VOICE_V2
# Browser-independent server generated workshop voice
# ==========================================================

GP_AR_VOICE = os.environ.get("GP_AR_VOICE", "ar-SY-AmanyNeural").strip() or "ar-SY-AmanyNeural"
GP_EN_VOICE = os.environ.get("GP_EN_VOICE", "en-US-JennyNeural").strip() or "en-US-JennyNeural"
GP_VOICE_CACHE_DIR = os.path.join(tempfile.gettempdir(), "golden_palace_voice_v2")
os.makedirs(GP_VOICE_CACHE_DIR, exist_ok=True)
GP_VOICE_FILE_LOCKS = {}
GP_VOICE_FILE_LOCKS_GUARD = threading.Lock()

GP_STAFF_AR = ["أبو عدنان", "خبيطي", "أبو نقطة", "عمر", "حريري", "أبو غسان", "حازم"]
GP_STAFF_EN = ["Abu Adnan", "Khbeiti", "Abu Nuqta", "Omar", "Hariri", "Abu Ghassan", "Hazem"]

GP_AR_STARTS = ["يا أبطال القصر الذهبي", "يعطيكم العافية يا شباب", "يا جماعة الورشة", "يا فريقنا الذهبي", "أهل الهمة بالورشة", "شباب القصر الذهبي"]
GP_AR_MOTIVATION = ["كل حالة منسكرها صح بتزيد ثقة الزبون فينا", "الشغل المرتب اليوم بيريحنا بكرا", "كل جهاز عم يطلع مضبوط هو نقطة إلنا", "السرعة حلوة بس الدقة أحلى", "المتابعة الواضحة بتختصر نص الشغل", "ما منترك حالة معلقة بلا سبب واضح", "كل خطوة صغيرة اليوم بتعمل فرق كبير بنهاية الدوام", "خبرتنا بتبين بالتفاصيل مو بالحكي", "الزبون ما بيشوف كل التعب اللي ورا الكواليس، بس بيحس بالنتيجة المرتبة", "لما كل واحد يحدث حالته بوقتها، الفريق كله بيصير أسرع"]
GP_AR_ACTION = ["خلونا نركز على الحالات الأقدم أول", "يلا منقفل المفتوح حالة ورا حالة", "اللي جاهز ما نخليه يستنى", "كل واحد يحدث حالته أول بأول", "خلونا نخلي القائمة أخف قبل نهاية الدوام", "إذا في عائق نرفعه بسرعة وما نخليه ينام", "الأولوية اليوم للحالة اللي مستنية قرار واضح", "نرتب الشغل ونخلي كل جهاز بمكانه الصحيح", "الحالة اللي ما إلها خطوة جاية واضحة بدها قرار اليوم", "نخلي المعلومة تمشي أسرع من الجهاز بين الأقسام"]
GP_AR_FUNNY = ["اليوم الأجهزة داخلة الورشة متوترة، طمنوها إنو وصلت لعند أهل الخبرة", "إذا جهاز عند معنا، ما في مشكلة، منعنّد عليه بالخبرة أكتر", "قائمة الانتظار عم تعمل حالها كبيرة، بس نحنا منعرف كيف نصغرها", "الجهاز اللي مفكر يقضي عطلة عنا، خبرّوه إنو الحجز فل اليوم", "إذا مفك البراغي اختفى مرة تانية، رح نعمله سند صيانة لحالو", "الورشة اليوم بدها شغل مرتب وابتسامة، لأن الأجهزة كمان إلها نفسية", "أي جهاز عم يمثل إنو ما فيه عطل، عنا فنيين بيعرفوا يخلّوه يعترف", "خلونا نشتغل بهدوء، بس بسرعة تخلي القائمة نفسها تستغرب", "إذا الشاشة صارت كلها أخضر، لا حدا يعمل ريفريش من الخوف، هاد اسمه إنجاز", "الداشبورد ما بيصلح الأجهزة، بس بيحرج الحالة اللي قاعدة بلا تحديث"]
GP_AR_PERSON = ["{name}، اليوم عليك حركة حلوة بالقائمة، بدنا نشوف كم حالة رح تختفي", "{name}، الأجهزة عاملة موعد معك اليوم، لا تخليها تنتظر كتير", "{name}، ورجينا لمسة الخبرة وخلي آخر كلمة بالحالة تم", "{name}، شد الهمة، كل حالة بتخلصها عم تفتح مجال للي بعدها", "{name}، إذا الجهاز ما حكى من أول فحص، اسأله بالطريقة الفنية تبعك", "{name}، تحديث صغير منك هلق بيوفر ثلاث أسئلة بعد شوي"]
GP_AR_MANAGER = ["توجيه من أبو آدم: الأولوية للحالات المتأخرة والعالقة، وأي عائق واضح ارفعوه بسرعة مشان ما يوقف حركة الشغل", "أبو آدم متابع حركة العمليات اليوم، خلوا كل حالة محدثة والخطوة الجاية واضحة حتى كل فريق يعرف شو عليه", "رسالة أبو آدم للفريق: السرعة مهمة، بس التنظيم والدقة أهم، وإذا في تأخير سببه واضح منحلّه سوا", "أبو آدم يذكّر الفريق: ما بدنا بطولة فردية، بدنا شغل فريق يسلّم الحالة صح من أول مرة", "أبو آدم عم يتابع الأرقام، بس الأهم إنو كل حالة يكون إلها مسؤول وخطوة جاية واضحة", "من أبو آدم للفريق: إذا في عائق خبرونا بكير، التأخير المعلوم منقدر نحلّه، التأخير المخفي هو المشكلة", "أبو آدم بيقول: اليوم الناجح مو بس بعدد الحالات اللي تسكرت، كمان بقديش خففنا العوائق ووقت انتظار الزبون", "أبو آدم عم ينسق حركة الشغل بين الأقسام، خلوا الأولويات واضحة والمعلومة توصل بسرعة وما نخلي أي حالة تضيع بين فريق وفريق"]
GP_AR_MANAGER_JOKES = ["أبو آدم طلب تطوير بسيط، ومن خبرتنا بالتطوير البسيط، إذا خلصناه اليوم بكرا بيطلعله إصدار رقم اثنين", "أبو آدم بيقول إذا الداشبورد صار أخضر كله لا تخافوا، مو عطل بالنظام، هاد اسمه إنجاز حقيقي", "أبو آدم طلب نشيل البوتل نِك، بس رجاء لا حدا ينقله من قسم لقسم ويسميها إعادة توزيع", "رسالة تطوير من أبو آدم: أي اختصار بخطوات الشغل مرحب فيه، إلا إذا الاختصار رجعنا ثلاث خطوات لورا", "أبو آدم عم يطور العمليات لدرجة إذا العملية زبطت زيادة، غالباً رح نفتح مشروع تطوير جديد لنعرف ليش زبطت", "إذا لقينا عملية بدها خمس موافقات مشان تصير أسرع، خبروا أبو آدم قبل ما نضيف الموافقة السادسة"]
GP_AR_ENDS = ["والله يعطيكم العافية", "وبالتوفيق يا شباب", "يلا نكملها صح", "والقهوة بعد الإنجاز أطيب", "وخلي الزبون يحس بالفرق", "ومنكمّل بنفس النفس الحلو"]

GP_EN_STARTS = ["Golden Palace team", "Workshop heroes", "Great team", "Golden Palace crew", "Service team"]
GP_EN_MOTIVATION = ["every properly closed case builds more customer trust", "clean follow-up today saves time tomorrow", "speed matters, but accuracy matters more", "clear updates make the whole workshop faster", "our experience shows in the details"]
GP_EN_ACTION = ["let us clear the oldest cases first", "keep every case updated as you work", "raise blockers early instead of letting them sleep", "keep the queue moving", "make the next action clear on every case"]
GP_EN_FUNNY = ["the waiting list is trying to look big again, let us disappoint it", "if the screwdriver disappears again, we may open a service ticket for it", "if the dashboard turns completely green, do not panic, that is called progress"]
GP_EN_MANAGER = ["A note from Abu Adam: prioritize delayed and blocked cases, and raise obstacles early so operations keep moving", "Abu Adam is following today’s operations; keep every case updated and make the next action clear", "Abu Adam reminds the team that good operations means clear ownership, fewer blockers, and less customer waiting time"]
GP_EN_MANAGER_JOKES = ["Abu Adam asked for one small improvement; operations experience says version two is already waiting around the corner", "Abu Adam says if the dashboard turns completely green, do not restart it; that is called an achievement", "Abu Adam asked us to remove the bottleneck, not move it to another department and call it redistribution"]
GP_EN_ENDS = ["great work team", "keep the good energy going", "let us finish strong", "thank you team"]


def gp_build_voice_message(lang="ar"):
    lang = "en" if str(lang).lower().startswith("en") else "ar"
    r = random.random()
    tone = "warm"
    category = "motivation"
    person = ""
    if lang == "ar":
        if r < 0.12:
            category = "management_joke"; person = "أبو آدم"; text = f"{random.choice(GP_AR_MANAGER_JOKES)}. {random.choice(GP_AR_ENDS)}."; tone = "funny"
        elif r < 0.27:
            category = "management"; person = "أبو آدم"; text = f"{random.choice(GP_AR_MANAGER)}. {random.choice(GP_AR_ENDS)}."
        elif r < 0.48:
            category = "funny"; text = f"{random.choice(GP_AR_STARTS)}، {random.choice(GP_AR_FUNNY)}. {random.choice(GP_AR_ENDS)}."; tone = "funny"
        elif r < 0.66:
            category = "person"; person = random.choice(GP_STAFF_AR); text = f"{random.choice(GP_AR_PERSON).format(name=person)}. {random.choice(GP_AR_ENDS)}."
        elif r < 0.86:
            text = f"{random.choice(GP_AR_STARTS)}، {random.choice(GP_AR_MOTIVATION)}، {random.choice(GP_AR_ACTION)}. {random.choice(GP_AR_ENDS)}."
        else:
            category = "workshop"; text = f"{random.choice(GP_AR_STARTS)}، {random.choice(GP_AR_ACTION)}. {random.choice(GP_AR_MOTIVATION)}. {random.choice(GP_AR_ENDS)}."
    else:
        if r < 0.12:
            category = "management_joke"; person = "Abu Adam"; text = f"{random.choice(GP_EN_MANAGER_JOKES)}. {random.choice(GP_EN_ENDS)}."; tone = "funny"
        elif r < 0.27:
            category = "management"; person = "Abu Adam"; text = f"{random.choice(GP_EN_MANAGER)}. {random.choice(GP_EN_ENDS)}."
        elif r < 0.48:
            category = "funny"; text = f"{random.choice(GP_EN_STARTS)}, {random.choice(GP_EN_FUNNY)}. {random.choice(GP_EN_ENDS)}."; tone = "funny"
        elif r < 0.66:
            category = "person"; person = random.choice(GP_STAFF_EN); text = f"{person}, keep the case moving and make the next update clear. {random.choice(GP_EN_ENDS)}."
        else:
            text = f"{random.choice(GP_EN_STARTS)}, {random.choice(GP_EN_MOTIVATION)}, {random.choice(GP_EN_ACTION)}. {random.choice(GP_EN_ENDS)}."
    return {"lang": lang, "text": re.sub(r"\\s+", " ", text).strip(), "tone": tone, "category": category, "person": person}


def gp_voice_settings(lang, tone):
    voice = GP_AR_VOICE if lang == "ar" else GP_EN_VOICE
    if tone == "funny": return voice, "+5%", "+2Hz"
    return voice, "-3%", "+0Hz"


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
    track = gp_build_voice_message(lang)
    voice, rate, pitch = gp_voice_settings(lang, track["tone"])
    try:
        token, _path = gp_ensure_voice_file(track["text"], voice, rate, pitch)
    except Exception as exc:
        print("VOICE GENERATION ERROR:", repr(exc))
        return jsonify({"ok": False, "error": "voice_generation_failed"}), 503
    return jsonify({"ok": True, "text": track["text"], "lang": lang, "tone": track["tone"], "category": track["category"], "person": track["person"], "voice": voice, "audio_url": f"/api/voice-audio/{token}.mp3"})


@app.route("/api/voice-audio/<token>.mp3")
def api_voice_audio(token):
    token = str(token or "").lower().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", token): return "Not found", 404
    path = os.path.join(GP_VOICE_CACHE_DIR, f"{token}.mp3")
    if not os.path.exists(path): return "Not found", 404
    response = send_file(path, mimetype="audio/mpeg", conditional=True, max_age=86400)
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


'''
    flask = replace_once(flask, marker, voice_backend + marker, 'voice backend marker')
    flask_path.write_text(flask, encoding='utf-8')

# ------------------------------------------------------------------
# TV: always play the same server-generated voice on every browser.
# ------------------------------------------------------------------
tv_path = Path('templates/tv.html')
tv = tv_path.read_text(encoding='utf-8')
if 'GP_SERVER_VOICE_CLIENT_V2' not in tv:
    tv = tv.replace("voiceOn:'🔊 Amany · Syrian female natural voice ON'", "voiceOn:'🔊 Golden Palace Syrian female voice ON'")
    tv = tv.replace("voiceOff:'🔇 Amany · Syrian female natural voice OFF'", "voiceOff:'🔇 Golden Palace Syrian female voice OFF'")
    tv = tv.replace("voiceBlocked:'⚠️ Open in Microsoft Edge for Amany Syrian voice'", "voiceBlocked:'⚠️ Syrian voice service unavailable'")
    tv = tv.replace("audioBlocked:'Amany Syrian female neural voice is not available in this browser. Open the TV in Microsoft Edge.'", "audioBlocked:'The Syrian voice could not start. Use Test Voice once or allow audio for this site.'")
    tv = tv.replace("voiceOn:'🔊 أماني السورية · صوت نسائي طبيعي مفعّل'", "voiceOn:'🔊 صوت القصر الذهبي النسائي السوري مفعّل'")
    tv = tv.replace("voiceOff:'🔇 أماني السورية · صوت نسائي طبيعي متوقف'", "voiceOff:'🔇 صوت القصر الذهبي النسائي السوري متوقف'")
    tv = tv.replace("voiceBlocked:'⚠️ افتح الشاشة بMicrosoft Edge لتفعيل أماني السورية'", "voiceBlocked:'⚠️ خدمة الصوت السوري غير متاحة حالياً'")
    tv = tv.replace("audioBlocked:'صوت أماني السوري النسائي الطبيعي غير متاح بهالمتصفح. افتح شاشة TV بMicrosoft Edge.'", "audioBlocked:'تعذر تشغيل الصوت السوري. اضغط اختبار الصوت مرة أو اسمح بالصوت للموقع.'")
    marker = '    async function confirmCollection(item, button) {'
    server_client = r'''
    // GP_SERVER_VOICE_CLIENT_V2
    let gpServerVoicePrefetch = null;
    async function gpFetchServerVoiceTrack(){
        const response = await fetch(apiUrl(`/api/voice-track?lang=${encodeURIComponent(currentLanguage)}&t=${Date.now()}`), {cache:'no-store'});
        if(!response.ok) throw new Error(`voice ${response.status}`);
        const track = await response.json();
        if(!track || !track.ok || !track.audio_url) throw new Error('invalid voice track');
        track.url = apiUrl(track.audio_url);
        return track;
    }
    function gpPrefetchServerVoice(){ if(!gpServerVoicePrefetch){ gpServerVoicePrefetch = gpFetchServerVoiceTrack().catch(() => null); } return gpServerVoicePrefetch; }
    async function playTeamVoice(_ignoredTrack=null, manual=false){
        if(detailMode || teamVoicePlaying) return false;
        if(!manual && (!teamVoiceEnabled || document.hidden)) return false;
        stopTeamVoiceAudio();
        let track = null;
        try{ track = await (gpServerVoicePrefetch || gpFetchServerVoiceTrack()); }catch(_){ track = null; }
        gpServerVoicePrefetch = null; gpPrefetchServerVoice();
        if(!track){ updateVoiceButton('blocked'); return false; }
        try{
            const audio = new Audio(track.url); audio.preload='auto'; audio.volume=TEAM_VOICE_VOLUME; teamVoiceAudio=audio; teamVoicePlaying=true; setVoiceCaption(track.text,true);
            const finish=()=>{ if(teamVoiceAudio===audio) teamVoiceAudio=null; teamVoicePlaying=false; setVoiceCaption('',false); };
            audio.addEventListener('ended',finish,{once:true}); audio.addEventListener('error',finish,{once:true}); await audio.play(); updateVoiceButton(); return true;
        }catch(_){ teamVoiceAudio=null; teamVoicePlaying=false; setVoiceCaption('',false); updateVoiceButton('blocked'); return false; }
    }
    function scheduleNextTeamVoice(delay=TEAM_VOICE_INTERVAL_MS){
        clearTimeout(teamVoiceTimer); teamVoiceTimer=null; if(detailMode||!teamVoiceEnabled)return;
        teamVoiceTimer=setTimeout(async()=>{ try{ if(!teamVoiceEnabled||document.hidden||teamVoicePlaying){scheduleNextTeamVoice(TEAM_VOICE_RETRY_MS);return;} const ok=await playTeamVoice(null,false); scheduleNextTeamVoice(ok?TEAM_VOICE_INTERVAL_MS:TEAM_VOICE_RETRY_MS);}catch(_){scheduleNextTeamVoice(TEAM_VOICE_RETRY_MS);} },Math.max(1000,delay));
    }
    async function toggleTeamVoice(){
        if(detailMode)return; try{ teamVoiceEnabled=!teamVoiceEnabled; localStorage.setItem('gpFemaleVoiceEnabled',teamVoiceEnabled?'1':'0'); if(!teamVoiceEnabled){clearTimeout(teamVoiceTimer);stopTeamVoiceAudio();updateVoiceButton();showToast(tr('voiceDisabled'));return;} updateVoiceButton();gpPrefetchServerVoice();const ok=await playTeamVoice(null,true);if(ok)showToast(tr('voiceEnabled'));else showToast(tr('audioBlocked'),7000);scheduleNextTeamVoice();}catch(_){updateVoiceButton('blocked');}
    }
    async function testTeamVoice(){ if(detailMode)return; try{const ok=await playTeamVoice(null,true);if(ok)showToast(tr('voicePlaying'));else showToast(tr('audioBlocked'),7000);}catch(_){showToast(tr('audioBlocked'),7000);} }
    function initialiseTeamVoice(){ if(detailMode)return; try{teamVoiceEnabled=localStorage.getItem('gpFemaleVoiceEnabled')!=='0';}catch(_){teamVoiceEnabled=true;} updateVoiceButton();gpPrefetchServerVoice();if(teamVoiceEnabled)scheduleNextTeamVoice(7000); }

'''
    tv = replace_once(tv, marker, server_client + marker, 'server voice client marker')
    tv_path.write_text(tv, encoding='utf-8')

launcher = r'''@echo off
setlocal
set "TVURL=https://gp-tv.onrender.com/?lang=ar"
set "PROFILE=%LOCALAPPDATA%\GoldenPalace-TV-Kiosk"
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if exist "%CHROME%" (start "Golden Palace TV" "%CHROME%" --user-data-dir="%PROFILE%-Chrome" --kiosk "%TVURL%" --no-first-run --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required & exit /b 0)
if exist "%EDGE%" (start "Golden Palace TV" "%EDGE%" --user-data-dir="%PROFILE%-Edge" --kiosk "%TVURL%" --edge-kiosk-type=fullscreen --no-first-run --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required & exit /b 0)
echo Golden Palace TV requires Chrome or Microsoft Edge for automatic kiosk startup.
echo The voice itself is server-generated and is not tied to either browser.
pause
endlocal
'''
Path('GP-TV-Fullscreen.cmd').write_text(launcher, encoding='utf-8', newline='\r\n')
Path('templates/GP-TV-Fullscreen.cmd').write_text(launcher, encoding='utf-8', newline='\r\n')
print('GP server voice v2 patch applied')
