from pathlib import Path

p = Path('templates/tv.html')
text = p.read_text(encoding='utf-8')

if 'GP_CEECEE_ACTIVATION_V2' in text:
    print('Ceecee activation already applied')
    raise SystemExit(0)

# Simplify the activation button wording and keep it language-aware.
text = text.replace("voiceOn:'🔊 Golden Palace Syrian female voice ON', voiceOff:'🔇 Golden Palace Syrian female voice OFF'", "voiceOn:'Enable / Disable', voiceOff:'Enable / Disable'")
text = text.replace("voiceOn:'🔊 صوت القصر الذهبي النسائي السوري مفعّل', voiceOff:'🔇 صوت القصر الذهبي النسائي السوري متوقف'", "voiceOn:'تفعيل / إيقاف', voiceOff:'تفعيل / إيقاف'")
text = text.replace('>🔊 Golden Palace female voice ON</button>', '>Enable / Disable</button>')

marker = "    function initialiseTeamVoice(){ if(detailMode)return; try{teamVoiceEnabled=localStorage.getItem('gpFemaleVoiceEnabled')!=='0';}catch(_){teamVoiceEnabled=true;} updateVoiceButton();gpPrefetchServerVoice();if(teamVoiceEnabled)scheduleNextTeamVoice(7000); }"
if marker not in text:
    raise SystemExit('Current initialiseTeamVoice marker not found')

override = r'''
    // GP_CEECEE_ACTIVATION_V2
    // Activation uses ONLY the original pre-generated HeyGen Ceecee - Excited recordings.
    // No Amany, browser speechSynthesis, or server-generated voice is used here.
    const GP_CEECEE_ACTIVATION_CATALOG = {
        en: [
            {id:'c-en01',text:'Welcome to Golden Palace, where professional service, careful follow-up, and customer trust come first.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=c04953ea-1214-43fd-b946-498e539ffbe9.wav'},
            {id:'c-en02',text:'Golden Palace service follows every repair from reception to completion, with clear tracking at every step.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=565c0e0b-7997-4518-aaeb-ea52ee81ebe7.wav'},
            {id:'c-en03',text:'At Golden Palace, your equipment is handled with care, experience, and professional follow-up.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=668d6524-0187-43eb-8350-094fbe16a081.wav'},
            {id:'c-en04',text:'Golden Palace team, great work. Every completed job builds stronger customer trust.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=ef21e428-1a4a-41f9-a5ed-9ec502640125.wav'}
        ],
        ar: [
            {id:'c-ar01',text:'أهلاً وسهلاً بكم في القصر الذهبي، حيث الخدمة الاحترافية، المتابعة الدقيقة، وثقة العميل تأتي أولاً.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=804dcd6f-088b-47fa-b83a-8aa7cdce7b73.wav'},
            {id:'c-ar02',text:'في القصر الذهبي نتابع كل حالة صيانة من لحظة الاستلام حتى الإنجاز، بخطوات واضحة وسريعة ومنظمة.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=982b3124-fe53-4cf9-95fa-1907d526cfa2.wav'},
            {id:'c-ar03',text:'القصر الذهبي، خبرة في الصيانة، عناية حقيقية بالمعدات، ومتابعة تليق بثقة عملائنا.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=7ebe7d75-72df-48e3-8ab0-a45f32243a65.wav'},
            {id:'c-ar04',text:'يعطيكم العافية يا فريق القصر الذهبي. حافظوا على سرعة المتابعة، جودة الإصلاح، ووضوح التواصل مع كل عميل.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=3a82ac1c-ead4-4f2c-976c-75e806feb8be.wav'},
            {id:'c-ar05',text:'ورشة القصر الذهبي للصيانة - دقة واحترافية عالية في إنجاز كافة المهام.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=72a41ccc-8048-4e54-b9fd-4b0270d74b62.wav'},
            {id:'c-ar06',text:'فريق فني متميز ومحترف لخدمة وصيانة جميع معداتكم بأعلى معايير الجودة.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=d3b4e00a-ee7c-4480-af7f-8adf3457c7a6.wav'},
            {id:'c-ar07',text:'ثقتكم هي سر نجاحنا - نسعى دائماً لتقديم الأفضل لعملائنا الكرام.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=4208e766-a0b0-49d9-8d4c-0e8c9313a063.wav'},
            {id:'c-ar08',text:'بالقصر الذهبي، الصيانة مو بس إصلاح جهاز، هي متابعة واهتمام من أول لحظة لحد ما يرجع الجهاز لصاحبه.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=e985d6ce-f7b3-4547-ad1f-d464e426c1fa.wav'},
            {id:'c-ar09',text:'أهلاً بكم في القصر الذهبي، هون كل حالة صيانة إلها متابعة واضحة، وكل تفصيل محسوب لخدمة أفضل.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=a8aa88ab-27fa-49a8-bbaf-fcf9869ba0bf.wav'},
            {id:'c-ar10',text:'القصر الذهبي يطوّر أدواته باستمرار، لأن سرعة المتابعة وجودة الخدمة جزء أساسي من ثقة عملائنا.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=e968806d-7f9d-4451-be65-7b205e13a266.wav'},
            {id:'c-ar11',text:'في القصر الذهبي، هدفنا مو بس نصلّح العطل، هدفنا نخلي تجربة الخدمة كاملة وأوضح وأسرع.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=f2619f05-7c10-419f-a7d6-c4c7e9d6523d.wav'},
            {id:'c-ar12',text:'عميل القصر الذهبي يستحق متابعة دقيقة، ولهيك كل حالة عم تمر بخطوات واضحة من الاستلام حتى الإنجاز.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=fa696937-0ac6-4b7e-adff-fa8f038d1dec.wav'},
            {id:'c-ar13',text:'القصر الذهبي، خدمة صيانة تجمع الخبرة، التنظيم، وسرعة المتابعة تحت سقف واحد.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=a2c48994-e472-48ef-a4ed-448f178b7f10.wav'},
            {id:'c-ar14',text:'كل جهاز بيدخل ورشة القصر الذهبي بياخد حقه من الفحص والمتابعة، لأن ثقة العميل مسؤولية.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=528b12f9-6e7e-4b12-862c-ee07c27c2f37.wav'},
            {id:'c-ar15',text:'بالقصر الذهبي عم نطوّر الخدمة كل يوم، حتى تكون الصيانة أسرع، المتابعة أوضح، والنتيجة أفضل.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=0af19232-b086-4845-a9ca-8cd3d814b2b4.wav'},
            {id:'c-ar16',text:'يعطيكم العافية يا شباب القصر الذهبي، خلونا اليوم نخلي قائمة المنجز أطول من قائمة الانتظار.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=16fd171b-f07e-4e8f-a40e-1985ddd28c0a.wav'},
            {id:'c-ar17',text:'يا فريق القصر الذهبي، جهاز ورا جهاز، حالة ورا حالة، والشغل المرتب آخر النهار بيحكي عن حاله.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=91e848a1-6e0a-4957-a669-6214f7d37ff9.wav'},
            {id:'c-ar18',text:'شباب القصر الذهبي، اليوم ممنوع الجهاز يزعل بالورشة، يا بيتصلّح يا منعرف بالضبط ليش ما بدو يتصلّح!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=000348a4-2100-460f-a123-fdda585821dd.wav'},
            {id:'c-ar19',text:'شدّوا الهمة يا فريق القصر الذهبي، كل حالة عم تنسكر صح معناها زبون مرتاح أكتر.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=f0fd4a6b-168c-47ad-994c-710c909dbf46.wav'},
            {id:'c-ar20',text:'الورشة المرتبة بتريح الفني والزبون، يلا يا فريق القصر الذهبي خلونا نخلي الشغل ماشي متل الساعة.',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=0a79ba81-6ef5-4319-a363-8d46da758373.wav'},
            {id:'c-ar21',text:'صباح أو مسا النشاط يا فريق القصر الذهبي، الأجهزة كتيرة بس الخبرة أكتر!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=7557e240-364a-4685-a6bc-1c0b0da0ae37.wav'},
            {id:'c-ar22',text:'أبو عدنان، اليوم الأجهزة عم تسأل عنك، شكلها عرفت إنو دورها وصلت للصيانة الصح!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=89b675bf-e45c-459a-a1ed-dd4593785bd2.wav'},
            {id:'c-ar23',text:'يا أبو عدنان، إذا الجهاز ما رضي يحكي من أول فحص، عطيو نظرة الخبرة تبعك يمكن يعترف لحالو!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=9820404d-3767-476f-9631-b3183d794f35.wav'},
            {id:'c-ar24',text:'أبو عدنان، شد الهمة، بدنا الأجهزة تطلع من عندك مبسوطة أكتر من أصحابها!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=e4b9e1b6-2c2f-4bf2-a52a-c4665e3f4606.wav'},
            {id:'c-ar25',text:'خبيطي، شوي شوي عالأجهزة، مو سباق رالي... بس إذا خلصتن بسرعة ما حدا رح يزعل!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=6e40f831-0fb7-4bdf-b7f3-b87a1866c652.wav'},
            {id:'c-ar26',text:'يا خبيطي، الورشة اليوم بدها همتك، بس دير بالك الجهاز مو لازم يعرف قديش مستعجلين عليه!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=1cda7dfe-3251-4422-9bdc-4e506bbbb66b.wav'},
            {id:'c-ar27',text:'خبيطي، إذا كل جهاز خلصته اليوم أخد نقطة، شكلك آخر الدوام بدك آلة حاسبة!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=f3b2e9e4-e660-41de-8aae-733b206349fd.wav'},
            {id:'c-ar28',text:'أبو نقطة، اليوم بدنا كل النقاط واضحة، وآخر نقطة بكل حالة تكون: تم الإنجاز!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=38b428eb-3943-4dc7-b109-b18463de35bf.wav'},
            {id:'c-ar29',text:'يا أبو نقطة، اسمك لحالو بيقول إنك ما بتترك الموضوع بلا نقطة أخيرة!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=bf787b4a-920a-41c9-8c9c-23cc0dc08794.wav'},
            {id:'c-ar30',text:'أبو نقطة، الجهاز إذا وصل لعندك بيعرف إنو رح نعرف وين النقطة اللي عاملة المشكلة!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=b32885c0-6d8f-43d7-858a-973beb1273b9.wav'},
            {id:'c-ar31',text:'عمر، شد الهمة، قائمة الانتظار شايفتك وبلشت تخاف تصغر!',url:'https://resource2.heygen.ai/text_to_speech/628ccd7ec31243c99f2f4becb76ad697/1cd326303dc3411eaa9fcda84ee7b921/id=a26c3b1d-9984-423e-87b3-0c082fc29a81.wav'}
        ]
    };
    const GP_CEECEE_ROTATION_KEY='gpCeeceeActivationRotationV2';
    function gpShuffleCopy(items){const a=items.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
    function gpLoadCeeceeBag(lang){
        const catalog=GP_CEECEE_ACTIVATION_CATALOG[lang]||[];
        try{
            const stored=JSON.parse(localStorage.getItem(`${GP_CEECEE_ROTATION_KEY}:${lang}`)||'[]');
            const valid=Array.isArray(stored)?stored.filter(id=>catalog.some(x=>x.id===id)):[];
            if(valid.length)return valid;
        }catch(_){}
        const bag=gpShuffleCopy(catalog.map(x=>x.id));
        try{localStorage.setItem(`${GP_CEECEE_ROTATION_KEY}:${lang}`,JSON.stringify(bag));}catch(_){}
        return bag;
    }
    function chooseCeeceeActivationTrack(){
        const lang=currentLanguage==='ar'?'ar':'en', catalog=GP_CEECEE_ACTIVATION_CATALOG[lang]||[];
        let bag=gpLoadCeeceeBag(lang); if(!bag.length)return null;
        const id=bag.shift(); try{localStorage.setItem(`${GP_CEECEE_ROTATION_KEY}:${lang}`,JSON.stringify(bag));}catch(_){}
        return catalog.find(x=>x.id===id)||catalog[0]||null;
    }
    async function playCeeceeActivationTrack(track){
        if(!track)return false;
        try{
            stopTeamVoiceAudio();
            const audio=new Audio(track.url); audio.preload='auto'; audio.volume=TEAM_VOICE_VOLUME;
            teamVoiceAudio=audio; teamVoicePlaying=true; setVoiceCaption(track.text,true);
            await new Promise((resolve,reject)=>{audio.addEventListener('ended',resolve,{once:true});audio.addEventListener('error',reject,{once:true});audio.play().catch(reject)});
            teamVoiceAudio=null; teamVoicePlaying=false; setVoiceCaption('',false); return true;
        }catch(_){teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false);return false;}
    }
    async function playTeamVoice(_ignoredTrack=null,manual=false){
        if(detailMode||teamVoicePlaying)return false;
        if(!manual&&(!teamVoiceEnabled||document.hidden))return false;
        return await playCeeceeActivationTrack(chooseCeeceeActivationTrack());
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
        updateVoiceButton();
        const ok=await playTeamVoice(null,true);
        if(ok)showToast(tr('voiceEnabled'));else showToast(tr('audioBlocked'),7000);
        scheduleNextTeamVoice();
    }
    function initialiseTeamVoice(){
        if(detailMode)return;
        try{teamVoiceEnabled=localStorage.getItem('gpFemaleVoiceEnabled')!=='0';}catch(_){teamVoiceEnabled=true;}
        updateVoiceButton();
        if(teamVoiceEnabled)scheduleNextTeamVoice(7000);
    }
'''

text = text.replace(marker, override, 1)
p.write_text(text, encoding='utf-8')
print('Exact Ceecee activation rotation applied')
