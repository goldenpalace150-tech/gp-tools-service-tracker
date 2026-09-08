from pathlib import Path

p = Path('templates/tv.html')
text = p.read_text(encoding='utf-8')

old = "    async function testTeamVoice(){ if(detailMode)return; try{const ok=await playTeamVoice(null,true);if(ok)showToast(tr('voicePlaying'));else showToast(tr('audioBlocked'),7000);}catch(_){showToast(tr('audioBlocked'),7000);} }"
new = r'''    // GP_CEECEE_EXACT_TEST_V1
    // Exact original HeyGen voice from the user's original tv(2).html:
    // Ceecee - Excited / voice id 1cd326303dc3411eaa9fcda84ee7b921.
    const GP_CEECEE_EXACT_TEST = {
        ar: {
            text: 'يعطيكم العافية يا شباب القصر الذهبي، خلونا اليوم نخلي قائمة المنجز أطول من قائمة الانتظار.',
            url: 'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=16fd171b-f07e-4e8f-a40e-1985ddd28c0a.wav'
        },
        en: {
            text: 'Golden Palace team, great work. Every completed job builds stronger customer trust.',
            url: 'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=ef21e428-1a4a-41f9-a5ed-9ec502640125.wav'
        }
    };
    async function testTeamVoice(){
        if(detailMode || teamVoicePlaying) return;
        const track = GP_CEECEE_EXACT_TEST[currentLanguage === 'ar' ? 'ar' : 'en'];
        try {
            stopTeamVoiceAudio();
            const audio = new Audio(track.url);
            audio.preload = 'auto';
            audio.volume = TEAM_VOICE_VOLUME;
            teamVoiceAudio = audio;
            teamVoicePlaying = true;
            setVoiceCaption(track.text, true);
            const finish = () => {
                if(teamVoiceAudio === audio) teamVoiceAudio = null;
                teamVoicePlaying = false;
                setVoiceCaption('', false);
            };
            audio.addEventListener('ended', finish, {once:true});
            audio.addEventListener('error', finish, {once:true});
            await audio.play();
            showToast(currentLanguage === 'ar' ? 'يتم الآن اختبار صوت Ceecee الأصلي.' : 'Testing the original Ceecee voice.');
        } catch (_) {
            teamVoiceAudio = null;
            teamVoicePlaying = false;
            setVoiceCaption('', false);
            showToast(tr('audioBlocked'), 7000);
        }
    }'''

if 'GP_CEECEE_EXACT_TEST_V1' in text:
    print('Exact Ceecee test already applied')
elif old not in text:
    raise SystemExit('Current testTeamVoice marker not found')
else:
    text = text.replace(old, new, 1)
    p.write_text(text, encoding='utf-8')
    print('Exact Ceecee test applied')
