from pathlib import Path
import re

TV = Path('templates/tv.html')
text = TV.read_text(encoding='utf-8')

if 'GP_AMANY_KIOSK_2026_09_08' not in text:
    # PWA/fullscreen metadata.
    text = text.replace(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n'
        '    <meta name="theme-color" content="#071a2d">\n'
        '    <meta name="mobile-web-app-capable" content="yes">\n'
        '    <meta name="apple-mobile-web-app-capable" content="yes">\n'
        '    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
        '    <link rel="manifest" href="/manifest.webmanifest">\n'
        '    <!-- GP_AMANY_KIOSK_2026_09_08 -->',
        1,
    )

    # Make voice UI explicit about the exact voice requirement.
    text = text.replace("voiceOn:'🔊 Golden Palace Syrian female voice ON'", "voiceOn:'🔊 Amany · Syrian female natural voice ON'")
    text = text.replace("voiceOff:'🔇 Golden Palace Syrian female voice OFF'", "voiceOff:'🔇 Amany · Syrian female natural voice OFF'")
    text = text.replace("voiceBlocked:'⚠️ Click to enable voice'", "voiceBlocked:'⚠️ Open in Microsoft Edge for Amany Syrian voice'")
    text = text.replace("audioBlocked:'The browser blocked audio. Click Golden Palace voice once and allow sound for this site.'", "audioBlocked:'Amany Syrian female neural voice is not available in this browser. Open the TV in Microsoft Edge.'")
    text = text.replace("voiceOn:'🔊 الصوت النسائي السوري للقصر الذهبي مفعّل'", "voiceOn:'🔊 أماني السورية · صوت نسائي طبيعي مفعّل'")
    text = text.replace("voiceOff:'🔇 الصوت النسائي السوري للقصر الذهبي متوقف'", "voiceOff:'🔇 أماني السورية · صوت نسائي طبيعي متوقف'")
    text = text.replace("voiceBlocked:'⚠️ اضغط لتفعيل الصوت'", "voiceBlocked:'⚠️ افتح الشاشة بMicrosoft Edge لتفعيل أماني السورية'")
    text = text.replace("audioBlocked:'المتصفح منع تشغيل الصوت. اضغط على زر صوت القصر الذهبي مرة واسمح بالصوت لهذا الموقع.'", "audioBlocked:'صوت أماني السوري النسائي الطبيعي غير متاح بهالمتصفح. افتح شاشة TV بMicrosoft Edge.'")

    start = text.index('    const GP_STAFF=')
    end = text.index('    async function confirmCollection(item, button) {', start)
    replacement = r'''    // Exact Arabic voice policy: Microsoft Amany Online (Natural) - Arabic (Syria).
    // Never fall back to a generic Arabic/robotic voice.
    const GP_STAFF={ar:['أبو عدنان','خبيطي','أبو نقطة','عمر','حريري','أبو غسان','حازم'],en:['Abu Adnan','Khbeiti','Abu Nuqta','Omar','Hariri','Abu Ghassan','Hazem']};
    const GP_MANAGER={ar:'أبو آدم',en:'Abu Adam'};
    const GP_VOICE_BANK={
      ar:{
        starts:['يا أبطال القصر الذهبي','يعطيكم العافية يا شباب','يا جماعة الورشة','يا فريقنا الذهبي','أهل الهمة بالورشة','شباب القصر الذهبي'],
        motivation:['كل حالة منسكرها صح بتزيد ثقة الزبون فينا','الشغل المرتب اليوم بيريّحنا بكرا','كل جهاز عم يطلع مضبوط هو نقطة إلنا','السرعة حلوة بس الدقة أحلى','المتابعة الواضحة بتختصر نص الشغل','ما منترك حالة معلقة بلا سبب واضح','كل خطوة صغيرة اليوم بتعمل فرق كبير بنهاية الدوام','خبرتنا بتبين بالتفاصيل مو بالحكي'],
        action:['خلونا نركز على الحالات الأقدم أول','يلا منقفل المفتوح حالة ورا حالة','اللي جاهز ما نخليه يستنى','كل واحد يحدّث حالته أول بأول','خلونا نخلي القائمة أخف قبل نهاية الدوام','إذا في عائق نرفعه بسرعة وما نخليه ينام','الأولوية اليوم للحالة اللي مستنية قرار واضح','نرتب الشغل ونخلي كل جهاز بمكانه الصحيح'],
        funny:['اليوم الأجهزة داخلة الورشة متوترة، طمنوها إنو وصلت لعند أهل الخبرة','إذا جهاز عنّد معنا، ما في مشكلة… منعنّد عليه بالخبرة أكتر','قائمة الانتظار عم تعمل حالها كبيرة، بس نحنا منعرف كيف نصغّرها','الجهاز اللي مفكر يقضي عطلة عنا، خبرّوه إنو الحجز فل اليوم','إذا مفك البراغي اختفى مرة تانية، رح نعمله سند صيانة لحالو','الورشة اليوم بدها شغل مرتب وابتسامة، لأن الأجهزة كمان إلها نفسية','أي جهاز عم يمثل إنو ما فيه عطل، عنا فنيين بيعرفوا يخلّوه يعترف','خلونا نشتغل بهدوء… بس بسرعة تخلي القائمة نفسها تستغرب'],
        person:['{name}، اليوم عليك حركة حلوة بالقائمة، بدنا نشوف كم حالة رح تختفي','{name}، الأجهزة عاملة موعد معك اليوم، لا تخليها تنتظر كتير','{name}، ورجينا لمسة الخبرة وخلي آخر كلمة بالحالة: تم','{name}، عندك مهمة بسيطة… بس القائمة شايفتها مو بسيطة أبداً','{name}، شد الهمة، كل حالة بتخلصها عم تفتح مجال للي بعدها','{name}، إذا الجهاز ما حكى من أول فحص، اسأله بالطريقة الفنية تبعك'],
        manager:[
          'توجيه من أبو آدم: الأولوية للحالات المتأخرة والعالقة، وأي عائق واضح ارفعوه بسرعة مشان ما يوقف حركة الشغل',
          'أبو آدم متابع حركة العمليات اليوم؛ خلّوا كل حالة محدثة والخطوة الجاية واضحة حتى كل فريق يعرف شو عليه',
          'رسالة أبو آدم للفريق: السرعة مهمة، بس التنظيم والدقة أهم، وإذا في تأخير سببه واضح منحلّه سوا',
          'أبو آدم يذكّر الفريق: ما بدنا بطولة فردية، بدنا شغل فريق يسلّم الحالة صح من أول مرة',
          'أبو آدم عم يتابع الأرقام، بس الأهم إنو كل حالة يكون إلها مسؤول وخطوة جاية واضحة',
          'من أبو آدم للفريق: إذا في عائق خبرونا بكير؛ التأخير المعلوم منقدر نحلّه، التأخير المخفي هو المشكلة',
          'أبو آدم بيقول: اليوم الناجح مو بس بعدد الحالات اللي تسكرت، كمان بقديش خففنا العوائق ووقت انتظار الزبون',
          'أبو آدم عم ينسّق حركة الشغل بين الأقسام؛ خلّوا الأولويات واضحة، والمعلومة توصل بسرعة، وما نخلي أي حالة تضيع بين فريق وفريق'
        ],
        ends:['والله يعطيكم العافية','وبالتوفيق يا شباب','يلا نكمّلها صح','والقهوة بعد الإنجاز أطيب','وخلي الزبون يحس بالفرق','ومنكمّل بنفس النفس الحلو']
      },
      en:{
        starts:['Golden Palace team','Workshop heroes','Great team','Golden Palace crew','Team, quick reminder','Service team'],
        motivation:['every properly closed case builds more customer trust','clean follow-up today saves time tomorrow','every finished tool is another win for the workshop','speed matters, but accuracy matters more','clear updates make the whole workshop faster','small improvements add up by the end of the day','our experience shows in the details','a tidy queue makes everyone’s work easier'],
        action:['let’s clear the oldest cases first','let’s close the ready cases one by one','keep every case updated as you work','raise blockers early instead of letting them sleep','give priority to anything waiting for a clear decision','keep the queue moving before the end of the shift','finish what is ready before opening extra work','keep the workshop organized and the status accurate'],
        funny:['the tools look nervous today, so remind them they came to the right workshop','if a tool refuses to cooperate, we have more experience than it has stubbornness','the waiting list is trying to look big again, let’s disappoint it','any tool planning a vacation in the workshop should know we are fully booked','if the screwdriver disappears again, we may open a service ticket for it','work fast, stay calm, and let the queue wonder what happened','some tools pretend nothing is wrong; luckily our technicians know better','the queue asked for an easy day; unfortunately it works for Golden Palace'],
        person:['{name}, the queue is watching you today; make a few cases disappear','{name}, the tools booked an appointment with you, so do not keep them waiting','{name}, give us the expert touch and make the final status Completed','{name}, one clean update can save the team several questions later','{name}, every case you finish makes room for the next one','{name}, if the tool stays quiet, ask it the technician way'],
        manager:[
          'A note from Abu Adam: prioritize delayed and blocked cases, and raise obstacles early so operations keep moving',
          'Abu Adam is following today’s operations; keep every case updated and make the next action clear for the whole team',
          'Abu Adam’s message to the team: speed matters, but organization and accuracy matter more; visible blockers can be solved together',
          'Abu Adam reminds the team: we do not need individual heroes; we need coordinated teamwork that closes each case correctly',
          'Abu Adam is watching the numbers, but the key is that every case has a clear owner and a clear next step',
          'From Abu Adam: raise blockers early; a known delay can be managed, a hidden delay is the real problem',
          'Abu Adam says a successful day is not only the number of closed cases, but also fewer blockers and less customer waiting time',
          'Abu Adam is coordinating the flow between teams; keep priorities visible, information moving, and do not let a case fall between departments'
        ],
        ends:['great work team','keep the good energy going','let’s finish strong','and keep the customer smiling','thank you team','one case at a time']
      }
    };
    function gpPick(a){return a[Math.floor(Math.random()*a.length)];}
    function gpRecentVoice(){try{return JSON.parse(localStorage.getItem('gpVoiceRecentV6')||'[]')}catch(_){return[]}}
    function gpRememberVoice(t){try{const a=gpRecentVoice().filter(x=>x!==t);a.push(t);localStorage.setItem('gpVoiceRecentV6',JSON.stringify(a.slice(-120)))}catch(_){}}
    function buildDynamicVoiceTrack(){
      const lang=currentLanguage==='ar'?'ar':'en',b=GP_VOICE_BANK[lang],r=Math.random();let text='',category='motivation',tone='warm',person='';
      if(r<.16){category='management';person=GP_MANAGER[lang];text=`${gpPick(b.manager)}. ${gpPick(b.ends)}.`}
      else if(r<.38){category='funny';tone='funny';text=`${gpPick(b.starts)}، ${gpPick(b.funny)}. ${gpPick(b.ends)}.`}
      else if(r<.58){category='person';person=gpPick(GP_STAFF[lang]);tone=Math.random()<.45?'funny':'warm';text=`${gpPick(b.person).replace('{name}',person)}. ${gpPick(b.ends)}.`}
      else if(r<.84){text=`${gpPick(b.starts)}، ${gpPick(b.motivation)}، ${gpPick(b.action)}. ${gpPick(b.ends)}.`}
      else{category='workshop';text=`${gpPick(b.starts)}، ${gpPick(b.action)}. ${gpPick(b.motivation)}. ${gpPick(b.ends)}.`}
      return{id:`dyn-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,category,person,text:text.replace(/\s+/g,' ').trim(),url:'',lang,tone}
    }
    function chooseVoiceTrack(){const recent=gpRecentVoice();let track=buildDynamicVoiceTrack();for(let i=0;i<50&&recent.includes(track.text);i++)track=buildDynamicVoiceTrack();gpRememberVoice(track.text);return track}

    function gpVoiceName(v){return String((v&&v.name)||'').toLowerCase()}
    function gpVoiceLang(v){return String((v&&v.lang)||'').toLowerCase().replace('_','-')}
    function findAmanySyrianVoice(){
      if(!('speechSynthesis' in window)) return null;
      const voices=window.speechSynthesis.getVoices()||[];
      return voices.find(v=>gpVoiceLang(v)==='ar-sy' && gpVoiceName(v).includes('amany'))
          || voices.find(v=>gpVoiceName(v).includes('amany') && (gpVoiceName(v).includes('syria')||gpVoiceLang(v)==='ar-sy'))
          || voices.find(v=>gpVoiceName(v).includes('ar-sy-amanyneural'))
          || null;
    }
    function findEnglishFemaleVoice(){
      if(!('speechSynthesis' in window)) return null;
      const voices=window.speechSynthesis.getVoices()||[], hints=['female','zira','samantha','sara','jenny','aria','ava','emma','sonia','libby'];
      return voices.find(v=>gpVoiceLang(v).startsWith('en')&&hints.some(h=>gpVoiceName(v).includes(h))) || voices.find(v=>gpVoiceLang(v).startsWith('en')) || null;
    }
    function refreshExactVoiceStatus(){
      if(currentLanguage!=='ar') { updateVoiceButton(); return; }
      if(teamVoiceEnabled && !findAmanySyrianVoice()) updateVoiceButton('blocked'); else updateVoiceButton();
    }
    if('speechSynthesis' in window){
      window.speechSynthesis.addEventListener?.('voiceschanged',refreshExactVoiceStatus);
      window.speechSynthesis.onvoiceschanged=refreshExactVoiceStatus;
    }
    function speakFallback(track){
      if(!('speechSynthesis'in window)||!track)return false;
      try{
        const isAr=track.lang==='ar';
        const preferred=isAr?findAmanySyrianVoice():findEnglishFemaleVoice();
        if(isAr && !preferred){
          teamVoicePlaying=false;setVoiceCaption('',false);updateVoiceButton('blocked');
          showToast(currentLanguage==='ar'?'صوت أماني السوري النسائي الطبيعي غير موجود بهالمتصفح. افتح الشاشة بMicrosoft Edge.':'Amany Syrian female natural voice is unavailable. Open the TV in Microsoft Edge.',9000);
          return false;
        }
        const u=new SpeechSynthesisUtterance(track.text);
        u.lang=isAr?'ar-SY':'en-US';
        u.voice=preferred||null;
        u.rate=track.tone==='funny'?1.08:1.00;
        u.pitch=track.tone==='funny'?1.08:1.02;
        u.volume=1;
        u.onend=()=>{teamVoicePlaying=false;setVoiceCaption('',false)};
        u.onerror=()=>{teamVoicePlaying=false;setVoiceCaption('',false)};
        teamVoicePlaying=true;setVoiceCaption(track.text,true);window.speechSynthesis.cancel();window.speechSynthesis.speak(u);return true
      }catch(_){return false}
    }
    function playTeamVoice(track,manual=false){if(!track||detailMode||teamVoicePlaying)return false;if(!manual&&(!teamVoiceEnabled||document.hidden))return false;stopTeamVoiceAudio();return speakFallback(track)}

    // Best-effort browser fullscreen; true bar-free startup is provided by the Edge kiosk launcher/PWA.
    async function gpRequestFullscreen(){
      if(detailMode||document.fullscreenElement||window.matchMedia('(display-mode: fullscreen)').matches) return;
      try{await document.documentElement.requestFullscreen({navigationUI:'hide'})}catch(_){}
    }
    ['pointerdown','keydown','touchstart'].forEach(evt=>document.addEventListener(evt,gpRequestFullscreen,{once:true,passive:true}));
    setTimeout(gpRequestFullscreen,250);

    let gpWakeLock=null;
    async function gpKeepScreenAwake(){try{if('wakeLock'in navigator&&document.visibilityState==='visible')gpWakeLock=await navigator.wakeLock.request('screen')}catch(_){}}
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')gpKeepScreenAwake()});
    setTimeout(gpKeepScreenAwake,600);

    if('serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));}

'''
    text = text[:start] + replacement + text[end:]

TV.write_text(text, encoding='utf-8')

# Fullscreen installable app assets.
Path('templates/manifest.webmanifest').write_text('''{
  "name": "Golden Palace Workshop TV",
  "short_name": "GP TV",
  "start_url": "/?lang=ar",
  "scope": "/",
  "display": "fullscreen",
  "display_override": ["fullscreen", "standalone", "minimal-ui"],
  "orientation": "landscape",
  "background_color": "#071a2d",
  "theme_color": "#071a2d",
  "icons": [{"src":"/gp-icon.svg","sizes":"any","type":"image/svg+xml","purpose":"any maskable"}]
}''', encoding='utf-8')

Path('templates/gp-icon.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="96" fill="#071a2d"/><circle cx="256" cy="256" r="178" fill="none" stroke="#d5a62e" stroke-width="24"/><text x="256" y="290" font-family="Arial,sans-serif" font-size="142" font-weight="700" text-anchor="middle" fill="#f4bd2d">GP</text></svg>''', encoding='utf-8')

Path('templates/sw.js').write_text("self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));", encoding='utf-8')

Path('GP-TV-Fullscreen.cmd').write_text(r'''@echo off
setlocal
set "TVURL=https://gp-tv.onrender.com/?lang=ar"
set "PROFILE=%LOCALAPPDATA%\GoldenPalace-TV-Kiosk"
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" (
  echo Microsoft Edge was not found.
  pause
  exit /b 1
)
start "Golden Palace TV" "%EDGE%" --user-data-dir="%PROFILE%" --kiosk "%TVURL%" --edge-kiosk-type=fullscreen --no-first-run --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required
endlocal
''', encoding='utf-8', newline='\r\n')

print('Amany/kiosk patch applied')
