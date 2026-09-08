from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing marker: {label}")
    return text.replace(old, new, 1)

flask_path = Path('flask_app.py')
flask = flask_path.read_text(encoding='utf-8')

if 'GP_VOICE_BALANCE_PROSODY_V3' not in flask:
    start = flask.index('GP_STAFF_AR = [')
    end = flask.index('\n\n@app.route("/api/voice-audio/<token>.mp3")', start)
    block = r'''# GP_VOICE_BALANCE_PROSODY_V3
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
    if tone == "funny": return voice, "+2%", "+1Hz"
    return voice, "-2%", "+0Hz"


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
    final_rate = "-12%" if lang == "ar" else "-9%"
    final_pitch = "-8Hz" if lang == "ar" else "-5Hz"
    try:
        body_token, _ = gp_ensure_voice_file(track["body"], voice, body_rate, body_pitch)
        final_token, _ = gp_ensure_voice_file(track["final"], voice, final_rate, final_pitch)
    except Exception as exc:
        print("VOICE GENERATION ERROR:", repr(exc))
        return jsonify({"ok": False, "error": "voice_generation_failed"}), 503
    return jsonify({"ok": True, "text": track["text"], "lang": lang, "tone": track["tone"], "category": track["category"], "person": track["person"], "voice": voice, "audio_urls": [f"/api/voice-audio/{body_token}.mp3", f"/api/voice-audio/{final_token}.mp3"]})
'''
    flask = flask[:start] + block + flask[end:]
    flask_path.write_text(flask, encoding='utf-8')

tv_path = Path('templates/tv.html')
tv = tv_path.read_text(encoding='utf-8')
if 'GP_VOICE_BALANCE_PROSODY_V3' not in tv:
    marker = '    // GP_SERVER_VOICE_CLIENT_V2\n'
    insert = r'''    // GP_VOICE_BALANCE_PROSODY_V3
    const GP_BALANCED_STAFF={ar:['أبو عدنان','خبيطي','أبو نقطة','عمر','أبو آدم','حريري','أبو غسان','حازم'],en:['Abu Adnan','Khbeiti','Abu Nuqta','Omar','Abu Adam','Hariri','Abu Ghassan','Hazem']};
    const GP_STAFF_ROTATION_KEY='gpBalancedStaffRotationV3';
    function gpNextStaffPerson(){const lang=currentLanguage==='ar'?'ar':'en',names=GP_BALANCED_STAFF[lang];let i=0;try{i=parseInt(localStorage.getItem(GP_STAFF_ROTATION_KEY+lang)||'0',10)||0}catch(_){}return{lang,name:names[i%names.length],index:i%names.length,next:(i+1)%names.length}}
    function gpCommitStaffPerson(slot){try{localStorage.setItem(GP_STAFF_ROTATION_KEY+slot.lang,String(slot.next))}catch(_){}}
'''
    tv = replace_once(tv, marker, insert + marker, 'TV server marker')
    old_fetch = """    async function gpFetchServerVoiceTrack(){\n        const response = await fetch(apiUrl(`/api/voice-track?lang=${encodeURIComponent(currentLanguage)}&t=${Date.now()}`), {cache:'no-store'});\n        if(!response.ok) throw new Error(`voice ${response.status}`);\n        const track = await response.json();\n        if(!track || !track.ok || !track.audio_url) throw new Error('invalid voice track');\n        track.url = apiUrl(track.audio_url);\n        return track;\n    }\n"""
    new_fetch = """    async function gpFetchServerVoiceTrack(manual=false){\n        const slot=gpNextStaffPerson();\n        const response = await fetch(apiUrl(`/api/voice-track?lang=${encodeURIComponent(currentLanguage)}&person=${encodeURIComponent(slot.name)}&manual=${manual ? '1' : '0'}&t=${Date.now()}`), {cache:'no-store'});\n        if(!response.ok) throw new Error(`voice ${response.status}`);\n        const track = await response.json();\n        if(!track || !track.ok || !Array.isArray(track.audio_urls) || !track.audio_urls.length) throw new Error('invalid voice track');\n        track.urls=track.audio_urls.map(apiUrl); track._staffSlot=slot; return track;\n    }\n"""
    tv = replace_once(tv, old_fetch, new_fetch, 'voice fetch')
    tv = tv.replace("gpServerVoicePrefetch = gpFetchServerVoiceTrack().catch(() => null);", "gpServerVoicePrefetch = gpFetchServerVoiceTrack(false).catch(() => null);")
    old_play = """    async function playTeamVoice(_ignoredTrack=null, manual=false){\n        if(detailMode || teamVoicePlaying) return false;\n        if(!manual && (!teamVoiceEnabled || document.hidden)) return false;\n        stopTeamVoiceAudio();\n        let track = null;\n        try{ track = await (gpServerVoicePrefetch || gpFetchServerVoiceTrack()); }catch(_){ track = null; }\n        gpServerVoicePrefetch = null; gpPrefetchServerVoice();\n        if(!track){ updateVoiceButton('blocked'); return false; }\n        try{\n            const audio = new Audio(track.url); audio.preload='auto'; audio.volume=TEAM_VOICE_VOLUME; teamVoiceAudio=audio; teamVoicePlaying=true; setVoiceCaption(track.text,true);\n            const finish=()=>{ if(teamVoiceAudio===audio) teamVoiceAudio=null; teamVoicePlaying=false; setVoiceCaption('',false); };\n            audio.addEventListener('ended',finish,{once:true}); audio.addEventListener('error',finish,{once:true}); await audio.play(); updateVoiceButton(); return true;\n        }catch(_){ teamVoiceAudio=null; teamVoicePlaying=false; setVoiceCaption('',false); updateVoiceButton('blocked'); return false; }\n    }\n"""
    new_play = """    async function playVoiceSequence(track){for(let i=0;i<track.urls.length;i++){const audio=new Audio(track.urls[i]);audio.preload='auto';audio.volume=TEAM_VOICE_VOLUME;teamVoiceAudio=audio;await new Promise((resolve,reject)=>{audio.addEventListener('ended',resolve,{once:true});audio.addEventListener('error',reject,{once:true});audio.play().catch(reject)});if(i<track.urls.length-1)await new Promise(r=>setTimeout(r,180));}}\n    async function playTeamVoice(_ignoredTrack=null, manual=false){\n        if(detailMode || teamVoicePlaying) return false;\n        if(!manual && (!teamVoiceEnabled || document.hidden)) return false;\n        stopTeamVoiceAudio(); let track=null;\n        try{track=await(gpServerVoicePrefetch||gpFetchServerVoiceTrack(manual))}catch(_){track=null}\n        gpServerVoicePrefetch=null; if(!track){updateVoiceButton('blocked');return false}\n        try{teamVoicePlaying=true;setVoiceCaption(track.text,true);await playVoiceSequence(track);gpCommitStaffPerson(track._staffSlot);teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false);updateVoiceButton();gpPrefetchServerVoice();return true}catch(_){teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false);updateVoiceButton('blocked');gpPrefetchServerVoice();return false}\n    }\n"""
    tv = replace_once(tv, old_play, new_play, 'voice play sequence')
    tv_path.write_text(tv, encoding='utf-8')

print('Balanced staff rotation and ending prosody patch applied')
