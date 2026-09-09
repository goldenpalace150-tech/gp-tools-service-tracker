from pathlib import Path

tp = Path('templates/tv.html')
tv = tp.read_text(encoding='utf-8')

if 'GP_LEVANTINE_VOICE_V4' not in tv:
    raise SystemExit('Levantine V4 is missing from tv.html')

if 'GP_LEVANTINE_TEST_V5' not in tv:
    marker = '    async function confirmCollection(item, button) {'
    if marker not in tv:
        raise SystemExit('confirmCollection marker missing')

    override = r'''
    // GP_LEVANTINE_TEST_V5
    // Test Voice now uses the same dynamic Levantine voice and the same balanced staff rotation.
    async function testTeamVoice(){
        if(detailMode || teamVoicePlaying) return;
        try{
            const ok = await playTeamVoice(null, true);
            if(ok) showToast(tr('voicePlaying'));
            else showToast(tr('audioBlocked'), 7000);
        }catch(_){
            showToast(tr('audioBlocked'), 7000);
        }
    }

'''
    tv = tv.replace(marker, override + marker, 1)
    tp.write_text(tv, encoding='utf-8')
    print('Levantine Test V5 applied')
else:
    print('Levantine Test V5 already applied')
