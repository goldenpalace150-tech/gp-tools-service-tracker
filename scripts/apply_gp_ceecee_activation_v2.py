from pathlib import Path

# ---------------- backend: voice + prosody ----------------
fp = Path('flask_app.py')
flask = fp.read_text(encoding='utf-8')
if 'GP_LEVANTINE_VOICE_V4' not in flask:
    flask = flask.replace(
        'GP_AR_VOICE = os.environ.get("GP_AR_VOICE", "ar-SY-AmanyNeural").strip() or "ar-SY-AmanyNeural"',
        '# GP_LEVANTINE_VOICE_V4\nGP_AR_VOICE = os.environ.get("GP_AR_VOICE", "ar-LB-LaylaNeural").strip() or "ar-LB-LaylaNeural"',
        1,
    )
    flask = flask.replace(
        'if tone == "funny": return voice, "+2%", "+1Hz"\n    return voice, "-2%", "+0Hz"',
        'if tone == "funny": return voice, "+6%", "+3Hz"\n    return voice, "+1%", "+1Hz"',
        1,
    )
    flask = flask.replace(
        'final_rate = "-12%" if lang == "ar" else "-9%"\n    final_pitch = "-8Hz" if lang == "ar" else "-5Hz"',
        'final_rate = "-5%" if lang == "ar" else "-7%"\n    final_pitch = "-3Hz" if lang == "ar" else "-4Hz"',
        1,
    )
fp.write_text(flask, encoding='utf-8')

# ---------------- TV: dynamic activation override ----------------
tp = Path('templates/tv.html')
tv = tp.read_text(encoding='utf-8')
if 'GP_LEVANTINE_VOICE_V4' not in tv:
    # Keep button wording intentionally simple.
    tv = tv.replace("voiceOn:'🔊 Golden Palace Syrian female voice ON'", "voiceOn:'Enable / Disable'")
    tv = tv.replace("voiceOff:'🔇 Golden Palace Syrian female voice OFF'", "voiceOff:'Enable / Disable'")
    tv = tv.replace("voiceOn:'🔊 صوت القصر الذهبي النسائي السوري مفعّل'", "voiceOn:'تفعيل / إيقاف'")
    tv = tv.replace("voiceOff:'🔇 صوت القصر الذهبي النسائي السوري متوقف'", "voiceOff:'تفعيل / إيقاف'")

    marker = '    async function confirmCollection(item, button) {'
    if marker not in tv:
        raise SystemExit('confirmCollection marker missing')

    override = r'''
    // GP_LEVANTINE_VOICE_V4
    // Dynamic, browser-independent Levantine female voice.
    // This override intentionally comes after the old Ceecee catalog so Enable/Disable uses
    // the new dynamic content while the exact Ceecee test can remain available for comparison.
    let gpDynamicVoicePrefetchV4 = null;

    async function gpFetchServerVoiceTrackV4(manual=false){
        const slot=gpNextStaffPerson();
        const response=await fetch(apiUrl(`/api/voice-track?lang=${encodeURIComponent(currentLanguage)}&person=${encodeURIComponent(slot.name)}&manual=${manual?'1':'0'}&t=${Date.now()}`),{cache:'no-store'});
        if(!response.ok) throw new Error(`voice ${response.status}`);
        const track=await response.json();
        if(!track||!track.ok||!Array.isArray(track.audio_urls)||!track.audio_urls.length) throw new Error('invalid voice track');
        track.urls=track.audio_urls.map(apiUrl);track._staffSlot=slot;return track;
    }
    function gpPrefetchDynamicLevantine(){
        if(!gpDynamicVoicePrefetchV4) gpDynamicVoicePrefetchV4=gpFetchServerVoiceTrackV4(false).catch(()=>null);
        return gpDynamicVoicePrefetchV4;
    }
    async function gpPlayDynamicLevantine(track){
        if(!track)return false;
        try{
            teamVoicePlaying=true;setVoiceCaption(track.text,true);
            for(let i=0;i<track.urls.length;i++){
                const audio=new Audio(track.urls[i]);audio.preload='auto';audio.volume=TEAM_VOICE_VOLUME;teamVoiceAudio=audio;
                await new Promise((resolve,reject)=>{audio.addEventListener('ended',resolve,{once:true});audio.addEventListener('error',reject,{once:true});audio.play().catch(reject)});
                if(i<track.urls.length-1)await new Promise(r=>setTimeout(r,160));
            }
            gpCommitStaffPerson(track._staffSlot);teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false);return true;
        }catch(_){teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false);return false;}
    }
    async function playTeamVoice(_ignoredTrack=null,manual=false){
        if(detailMode||teamVoicePlaying)return false;
        if(!manual&&(!teamVoiceEnabled||document.hidden))return false;
        stopTeamVoiceAudio();let track=null;
        try{track=await(gpDynamicVoicePrefetchV4||gpFetchServerVoiceTrackV4(manual));}catch(_){track=null;}
        gpDynamicVoicePrefetchV4=null;
        if(!track){updateVoiceButton('blocked');return false;}
        const ok=await gpPlayDynamicLevantine(track);
        if(ok){updateVoiceButton();gpPrefetchDynamicLevantine();}else updateVoiceButton('blocked');
        return ok;
    }
    function scheduleNextTeamVoice(delay=TEAM_VOICE_INTERVAL_MS){
        clearTimeout(teamVoiceTimer);teamVoiceTimer=null;if(detailMode||!teamVoiceEnabled)return;
        teamVoiceTimer=setTimeout(async()=>{
            if(!teamVoiceEnabled||document.hidden||teamVoicePlaying){scheduleNextTeamVoice(TEAM_VOICE_RETRY_MS);return;}
            const ok=await playTeamVoice(null,false);scheduleNextTeamVoice(ok?TEAM_VOICE_INTERVAL_MS:TEAM_VOICE_RETRY_MS);
        },Math.max(1000,delay));
    }
    async function toggleTeamVoice(){
        if(detailMode)return;
        teamVoiceEnabled=!teamVoiceEnabled;
        try{localStorage.setItem('gpFemaleVoiceEnabled',teamVoiceEnabled?'1':'0');}catch(_){}
        if(!teamVoiceEnabled){clearTimeout(teamVoiceTimer);stopTeamVoiceAudio();updateVoiceButton();showToast(tr('voiceDisabled'));return;}
        updateVoiceButton();gpPrefetchDynamicLevantine();
        const ok=await playTeamVoice(null,true);
        if(ok)showToast(tr('voiceEnabled'));else showToast(tr('audioBlocked'),7000);
        scheduleNextTeamVoice();
    }
    function initialiseTeamVoice(){
        if(detailMode)return;
        try{teamVoiceEnabled=localStorage.getItem('gpFemaleVoiceEnabled')!=='0';}catch(_){teamVoiceEnabled=true;}
        updateVoiceButton();gpPrefetchDynamicLevantine();if(teamVoiceEnabled)scheduleNextTeamVoice(7000);
    }
'''
    tv = tv.replace(marker, override + marker, 1)

tp.write_text(tv, encoding='utf-8')
print('Levantine dynamic voice V4 applied')
