from pathlib import Path

tp = Path('templates/tv.html')
tv = tp.read_text(encoding='utf-8')

if 'GP_CRISP_FEMALE_V6' in tv:
    print('Crisp female V6 already applied')
    raise SystemExit(0)

marker = '    async function confirmCollection(item, button) {'
if marker not in tv:
    raise SystemExit('confirmCollection marker missing')

override = r'''
    // GP_CRISP_FEMALE_V6
    // Approved female "Crisp" voice catalog. These are the exact generated MP3 previews
    // from the voice sample the user selected. No server TTS is used by the final override.
    const GP_CRISP_REFERENCE_URL='https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/ab12e999-2047-4cf8-bb9e-0539054d7a05.mp3';
    const GP_CRISP_STAFF = [
      {name:'أبو عدنان',tracks:[
        {text:'أبو عدنان، اليوم بدنا كل حالة عندك تكون واضحة ومحدّثة، والجاهز يطلع من الورشة بلا تأخير. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/c4c3269a-c508-42b3-8281-c2aea7862794.mp3'},
        {text:'أبو عدنان، إذا في حالة واقفة بلا سبب، خلّينا نعرف السبب اليوم ونحرّكها. خبرتك بتفرق، وشغلك المرتب بيبين.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/f1da361f-4313-4e28-b4d0-25d1dcac1a85.mp3'}]},
      {name:'خبيطي',tracks:[
        {text:'خبيطي، شدّ الهمة اليوم. خلّص الجاهز أول، وإذا جهاز عم يتدلّع ذكّره إنو وصل لعند أهل الخبرة. هيك الشغل الصح.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/a9609a8e-3fe7-41ae-9c7b-6dac1d9f3f81.mp3'},
        {text:'خبيطي، اليوم ممنوع الحالة تنام بالورشة من دون تحديث. يا منكمّلها، يا منكتب بوضوح شو ناطرين. تمام.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/43f41114-f7f1-43c7-b51c-f0b08436a395.mp3'}]},
      {name:'أبو نقطة',tracks:[
        {text:'أبو نقطة، بدنا كل نقطة بالحالة تكون واضحة، وآخر نقطة تكون: تم الإنجاز. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/ab4ca135-e5fa-44e4-aea8-c3d2dcb5719a.mp3'},
        {text:'أبو نقطة، كل حالة إلها قصة، بس ما بدنا القصة تطول. حدّثها بوقتها وخلي آخر سطر واضح: تم الإنجاز.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/195a5335-090c-4430-9753-646f7e4c4ed8.mp3'}]},
      {name:'عمر',tracks:[
        {text:'عمر، بلّش بالأقدم وخفّف قائمة الانتظار حالة ورا حالة، بس خليك دقيق بكل تحديث. ممتاز، هيك بدنا.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/a6c39513-90bf-4491-a8f8-0232692d1b65.mp3'},
        {text:'عمر، إذا الحالة جاهزة لا تخليها تستنى، وإذا مو جاهزة خلي السبب معروف. هيك منخفف التأخير ونمشي أسرع.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/b1fe02ab-3e50-46d6-b393-a58ddca9018b.mp3'}]},
      {name:'أبو آدم',tracks:[
        {text:'أبو آدم، أولوية العمليات اليوم للحالات المتأخرة. كل حالة لازم يكون إلها مسؤول واضح وخطوة جاية واضحة. تمام.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/68422110-6207-49f1-bd77-2b7a4981452e.mp3'},
        {text:'أبو آدم، إذا الداشبورد صار كله أخضر، لا تعمل ريفريش من الخوف. هاد اسمه إنجاز. خلّينا نكمّل بنفس النفس.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/eea810e3-1059-412a-8b5d-6b78dab5fad7.mp3'}]},
      {name:'حريري',tracks:[
        {text:'حريري، إذا خلصت الحالة حدّثها عالشاشة دغري، مشان الكل يعرف وين صار الشغل. شغل مرتب.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/27eea06a-f160-443e-999e-d1a63bd0fa51.mp3'},
        {text:'حريري، ورجينا لمسة الخبرة اليوم. خلّص الجاهز، وخلّي الحالة تنتقل للخطوة الجاية من دون ما تضيع بين المراحل.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/ee5ae571-9eec-4db3-9609-fef5995017cb.mp3'}]},
      {name:'أبو غسان',tracks:[
        {text:'أبو غسان، ركّز على الحالات اللي واقفة، وإذا في عائق ارفعه من بكير قبل ما يكبر. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/9543c73e-cee0-403c-bd9a-14657a4b2e31.mp3'},
        {text:'أبو غسان، اليوم بدنا المتابعة تمشي مع الشغل خطوة بخطوة. ما بدنا جهاز يخلص والحالة تضل واقفة عالشاشة.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/174d62a2-8392-4de1-9997-5f2d9fb763c2.mp3'}]},
      {name:'حازم',tracks:[
        {text:'حازم، اليوم بدنا شغل واضح من أول الفحص لآخر خطوة، وما نخلي حالة واقفة بلا سبب. تمام.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/8d57996b-0e16-413b-ba99-6db2094f1620.mp3'},
        {text:'حازم، إذا في شغلة معلّقة لا تتركها ساكتة. ارفعها من بكير وخلي الكل يعرف شو الخطوة الجاية. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/db8fbf86-7368-47ca-a8bd-686f5676cf2e.mp3'}]}
    ];
    const GP_CRISP_GENERAL = [
      {text:'يعطيكم العافية يا شباب القصر الذهبي. خلّونا اليوم نخلي قائمة المنجز أطول من قائمة الانتظار، وكل حالة تنتقل للخطوة الجاية بوضوح.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/26266cdd-e0ad-4459-a58f-4b46a59b7712.mp3'},
      {text:'شباب القصر الذهبي، الجهاز اللي مفكّر يقضي عطلة عنا خبرّوه إنو الحجز فل. خلّونا نخلّص الجاهز ونحدّث كل حالة بوقتها.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/4cb737d7-18f1-4a00-b846-02399e9332ac.mp3'}
    ];
    const GP_CRISP_STAFF_INDEX='gpCrispStaffIndexV6';
    const GP_CRISP_VARIANT_INDEX='gpCrispVariantIndexV6';
    const GP_CRISP_GENERAL_INDEX='gpCrispGeneralIndexV6';
    let gpCrispReferencePlayed=false;

    function gpReadIndex(key,mod){try{return Math.abs(parseInt(localStorage.getItem(key)||'0',10)||0)%mod}catch(_){return 0}}
    function gpWriteIndex(key,value){try{localStorage.setItem(key,String(value))}catch(_){}}
    function gpNextCrispStaffTrack(){
      const staffIdx=gpReadIndex(GP_CRISP_STAFF_INDEX,GP_CRISP_STAFF.length);
      const person=GP_CRISP_STAFF[staffIdx];
      const variantKey=`${GP_CRISP_VARIANT_INDEX}:${person.name}`;
      const variantIdx=gpReadIndex(variantKey,person.tracks.length);
      const track={...person.tracks[variantIdx],person:person.name};
      gpWriteIndex(variantKey,(variantIdx+1)%person.tracks.length);
      gpWriteIndex(GP_CRISP_STAFF_INDEX,(staffIdx+1)%GP_CRISP_STAFF.length);
      return track;
    }
    function gpNextCrispGeneral(){
      const idx=gpReadIndex(GP_CRISP_GENERAL_INDEX,GP_CRISP_GENERAL.length);
      gpWriteIndex(GP_CRISP_GENERAL_INDEX,(idx+1)%GP_CRISP_GENERAL.length);
      return {...GP_CRISP_GENERAL[idx],person:''};
    }
    function gpChooseCrispTrack(manual=false){
      if(manual && !gpCrispReferencePlayed){gpCrispReferencePlayed=true;return {text:'يعطيكم العافية يا شباب القصر الذهبي. اليوم بدنا نخلّص الحالات المتأخرة، ونخلي كل خطوة واضحة. حريري، أبو غسان، حازم، وأبو آدم، شدّوا الهمة وخلو الشغل مرتب. هيك بدنا الشغل.',url:GP_CRISP_REFERENCE_URL,person:''};}
      // One general line after each full 8-person staff cycle. Staff mentions remain exactly balanced.
      const staffIdx=gpReadIndex(GP_CRISP_STAFF_INDEX,GP_CRISP_STAFF.length);
      if(!manual && staffIdx===0 && gpReadIndex('gpCrispCycleSeenV6',2)===1){gpWriteIndex('gpCrispCycleSeenV6',0);return gpNextCrispGeneral();}
      if(!manual && staffIdx===0)gpWriteIndex('gpCrispCycleSeenV6',1);
      return gpNextCrispStaffTrack();
    }
    async function gpPlayCrispTrack(track){
      if(!track||!track.url)return false;
      try{
        stopTeamVoiceAudio();
        const audio=new Audio(track.url);audio.preload='auto';audio.volume=TEAM_VOICE_VOLUME;
        teamVoiceAudio=audio;teamVoicePlaying=true;setVoiceCaption(track.text,true);
        await new Promise((resolve,reject)=>{audio.addEventListener('ended',resolve,{once:true});audio.addEventListener('error',reject,{once:true});audio.play().catch(reject)});
        teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false);return true;
      }catch(_){teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false);return false;}
    }
    async function playTeamVoice(_ignoredTrack=null,manual=false){
      if(detailMode||teamVoicePlaying)return false;
      if(!manual&&(!teamVoiceEnabled||document.hidden))return false;
      const ok=await gpPlayCrispTrack(gpChooseCrispTrack(manual));
      updateVoiceButton(ok?undefined:'blocked');return ok;
    }
    async function testTeamVoice(){
      if(detailMode||teamVoicePlaying)return;
      const ok=await playTeamVoice(null,true);
      if(ok)showToast(tr('voicePlaying'));else showToast(tr('audioBlocked'),7000);
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
      try{localStorage.setItem('gpFemaleVoiceEnabled',teamVoiceEnabled?'1':'0')}catch(_){}
      if(!teamVoiceEnabled){clearTimeout(teamVoiceTimer);stopTeamVoiceAudio();updateVoiceButton();showToast(tr('voiceDisabled'));return;}
      updateVoiceButton();const ok=await playTeamVoice(null,true);
      if(ok)showToast(tr('voiceEnabled'));else showToast(tr('audioBlocked'),7000);
      scheduleNextTeamVoice();
    }
    function initialiseTeamVoice(){
      if(detailMode)return;
      try{teamVoiceEnabled=localStorage.getItem('gpFemaleVoiceEnabled')!=='0'}catch(_){teamVoiceEnabled=true}
      updateVoiceButton();if(teamVoiceEnabled)scheduleNextTeamVoice(7000);
    }

'''

tv = tv.replace(marker, override + marker, 1)
tp.write_text(tv, encoding='utf-8')
print('Approved Crisp female V6 applied')
