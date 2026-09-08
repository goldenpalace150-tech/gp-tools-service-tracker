from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Missing marker: {label}")
    return text.replace(old, new, 1)


def upgrade_tv():
    p = Path("templates/tv.html")
    tv = p.read_text(encoding="utf-8")
    if "GP_UI_REFRESH_2026_09_08" in tv:
        return

    tv = tv.replace("</head>", """
    <!-- GP_UI_REFRESH_2026_09_08 -->
    <style id="gp-ui-refresh-2026-09-08">
      :root{--gp-navy:#071a2d;--gp-navy2:#0c2945;--gp-gold:#d5a62e}
      body{background:radial-gradient(circle at 12% 0%,#eef5ff 0,#f6f8fb 38%,#eef2f7 100%)}
      .topbar{background:linear-gradient(125deg,var(--gp-navy),var(--gp-navy2));border-color:rgba(213,166,46,.55);color:#fff;box-shadow:0 14px 34px rgba(7,26,45,.18)}
      .brand h1,.brand small{color:#fff!important}.pill,.action-btn{min-height:44px;border-radius:12px}
      .topbar .pill,.topbar .action-btn,.topbar select{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.22)}
      .workflow-card{border:1px solid rgba(148,163,184,.32);box-shadow:0 8px 26px rgba(15,23,42,.07);background:linear-gradient(160deg,#fff,#fbfdff)}
      .workflow-card::before{content:"";position:absolute;width:115px;height:115px;border-radius:50%;right:-36px;top:-42px;background:rgba(37,99,235,.055)}
      .workflow-card:hover{transform:translateY(-2px) scale(1.006)}
      .summary-item,.detail-toolbar,.ticket-panel,.stat,.remark-row{box-shadow:0 5px 18px rgba(15,23,42,.05)}
      button:focus-visible,input:focus-visible,select:focus-visible,.workflow-card:focus-visible{outline:3px solid #f0be3f!important;outline-offset:3px!important}
      .voice-caption{border:1px solid rgba(213,166,46,.65);box-shadow:0 12px 32px rgba(0,0,0,.24)}
      html[dir="ltr"] .voice-caption{direction:ltr}html[dir="rtl"] .voice-caption{direction:rtl}
      @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;transition-duration:.001ms!important;scroll-behavior:auto!important}}
    </style>
</head>""", 1)

    lang_marker = "    if (!['en','ar'].includes(currentLanguage)) currentLanguage = 'en';"
    tv = replace_once(tv, lang_marker, lang_marker + """

    const GP_BACKEND_ORIGIN = 'https://golden-palace-service-tracker.onrender.com';
    const API_BASE = window.location.hostname === 'golden-palace-service-tracker.onrender.com' ? '' : GP_BACKEND_ORIGIN;
    const apiUrl = path => `${API_BASE}${path}`;
""", "api base")

    for old, new in {
        "fetch('/api/close-ticket',": "fetch(apiUrl('/api/close-ticket'),",
        "fetch('/api/delete-remark',": "fetch(apiUrl('/api/delete-remark'),",
        "fetch('/api/health?reconnect=1',": "fetch(apiUrl('/api/health?reconnect=1'),",
        "fetch(`/api/remarks?t=${Date.now()}`,": "fetch(apiUrl(`/api/remarks?t=${Date.now()}`),",
        "fetch(`/api/data?t=${Date.now()}${forceArg}`,": "fetch(apiUrl(`/api/data?t=${Date.now()}${forceArg}`),",
    }.items():
        if old not in tv:
            raise RuntimeError(f"Missing fetch marker: {old}")
        tv = tv.replace(old, new)

    tv = tv.replace("window.location.href=`/tv?lang=${encodeURIComponent(currentLanguage)}`", "window.location.href=`/?lang=${encodeURIComponent(currentLanguage)}`")
    tv = tv.replace("const foreground = force || !latestData || foregroundRefreshPending;", "const foreground = force || foregroundRefreshPending;")
    tv = tv.replace("    } else {\n        setLoading(true, tr('loading'));\n    }\n    refreshDashboard(false);", "    } else {\n        setLoading(false);\n        const lastSync = document.getElementById('lastSync');\n        if (lastSync) lastSync.textContent = currentLanguage === 'ar' ? 'جارٍ جلب البيانات المباشرة…' : 'Connecting to live data…';\n    }\n    refreshDashboard(false);")
    tv = tv.replace("voiceOn:'🔊 Golden Palace female voice ON'", "voiceOn:'🔊 Golden Palace Syrian female voice ON'")
    tv = tv.replace("voiceOff:'🔇 Golden Palace female voice OFF'", "voiceOff:'🔇 Golden Palace Syrian female voice OFF'")
    tv = tv.replace("voiceOn:'🔊 صوت القصر الذهبي النسائي مفعّل'", "voiceOn:'🔊 الصوت النسائي السوري للقصر الذهبي مفعّل'")
    tv = tv.replace("voiceOff:'🔇 صوت القصر الذهبي النسائي متوقف'", "voiceOff:'🔇 الصوت النسائي السوري للقصر الذهبي متوقف'")

    override = r'''
    const GP_STAFF={ar:['أبو عدنان','خبيطي','أبو نقطة','عمر','أبو آدم','حريري','أبو غسان','حازم'],en:['Abu Adnan','Khbeiti','Abu Nuqta','Omar','Abu Adam','Hariri','Abu Ghassan','Hazem']};
    const GP_VOICE_BANK={
      ar:{starts:['يا أبطال القصر الذهبي','يعطيكم العافية يا شباب','يا جماعة الورشة','يا فريقنا الذهبي','أهل الهمة بالورشة','شباب القصر الذهبي'],motivation:['كل حالة منسكرها صح بتزيد ثقة الزبون فينا','الشغل المرتب اليوم بيريّحنا بكرا','كل جهاز عم يطلع مضبوط هو نقطة إلنا','السرعة حلوة بس الدقة أحلى','المتابعة الواضحة بتختصر نص الشغل','ما منترك حالة معلقة بلا سبب واضح','كل خطوة صغيرة اليوم بتعمل فرق كبير بنهاية الدوام','خبرتنا بتبين بالتفاصيل مو بالحكي'],action:['خلونا نركز على الحالات الأقدم أول','يلا منقفل المفتوح حالة ورا حالة','اللي جاهز ما نخليه يستنى','كل واحد يحدّث حالته أول بأول','خلونا نخلي القائمة أخف قبل نهاية الدوام','إذا في عائق نرفعه بسرعة وما نخليه ينام','الأولوية اليوم للحالة اللي مستنية قرار واضح','نرتب الشغل ونخلي كل جهاز بمكانه الصحيح'],funny:['اليوم الأجهزة داخلة الورشة متوترة، طمنوها إنو وصلت لعند أهل الخبرة','إذا جهاز عنّد معنا، ما في مشكلة… منعنّد عليه بالخبرة أكتر','قائمة الانتظار عم تعمل حالها كبيرة، بس نحنا منعرف كيف نصغّرها','الجهاز اللي مفكر يقضي عطلة عنا، خبرّوه إنو الحجز فل اليوم','إذا مفك البراغي اختفى مرة تانية، رح نعمله سند صيانة لحالو','الورشة اليوم بدها شغل مرتب وابتسامة، لأن الأجهزة كمان إلها نفسية','أي جهاز عم يمثل إنو ما فيه عطل، عنا فنيين بيعرفوا يخلّوه يعترف','خلونا نشتغل بهدوء… بس بسرعة تخلي القائمة نفسها تستغرب'],person:['{name}، اليوم عليك حركة حلوة بالقائمة، بدنا نشوف كم حالة رح تختفي','{name}، الأجهزة عاملة موعد معك اليوم، لا تخليها تنتظر كتير','{name}، ورجينا لمسة الخبرة وخلي آخر كلمة بالحالة: تم','{name}، عندك مهمة بسيطة… بس القائمة شايفتها مو بسيطة أبداً','{name}، شد الهمة، كل حالة بتخلصها عم تفتح مجال للي بعدها','{name}، إذا الجهاز ما حكى من أول فحص، اسأله بالطريقة الفنية تبعك'],ends:['والله يعطيكم العافية','وبالتوفيق يا شباب','يلا نكمّلها صح','والقهوة بعد الإنجاز أطيب','وخلي الزبون يحس بالفرق','ومنكمّل بنفس النفس الحلو']},
      en:{starts:['Golden Palace team','Workshop heroes','Great team','Golden Palace crew','Team, quick reminder','Service team'],motivation:['every properly closed case builds more customer trust','clean follow-up today saves time tomorrow','every finished tool is another win for the workshop','speed matters, but accuracy matters more','clear updates make the whole workshop faster','small improvements add up by the end of the day','our experience shows in the details','a tidy queue makes everyone’s work easier'],action:['let’s clear the oldest cases first','let’s close the ready cases one by one','keep every case updated as you work','raise blockers early instead of letting them sleep','give priority to anything waiting for a clear decision','keep the queue moving before the end of the shift','finish what is ready before opening extra work','keep the workshop organized and the status accurate'],funny:['the tools look nervous today, so remind them they came to the right workshop','if a tool refuses to cooperate, we have more experience than it has stubbornness','the waiting list is trying to look big again, let’s disappoint it','any tool planning a vacation in the workshop should know we are fully booked','if the screwdriver disappears again, we may open a service ticket for it','work fast, stay calm, and let the queue wonder what happened','some tools pretend nothing is wrong; luckily our technicians know better','the queue asked for an easy day; unfortunately it works for Golden Palace'],person:['{name}, the queue is watching you today; make a few cases disappear','{name}, the tools booked an appointment with you, so do not keep them waiting','{name}, give us the expert touch and make the final status Completed','{name}, one clean update can save the team several questions later','{name}, every case you finish makes room for the next one','{name}, if the tool stays quiet, ask it the technician way'],ends:['great work team','keep the good energy going','let’s finish strong','and keep the customer smiling','thank you team','one case at a time']}
    };
    function gpPick(a){return a[Math.floor(Math.random()*a.length)];}
    function gpRecentVoice(){try{return JSON.parse(localStorage.getItem('gpVoiceRecentV5')||'[]')}catch(_){return[]}}
    function gpRememberVoice(t){try{const a=gpRecentVoice().filter(x=>x!==t);a.push(t);localStorage.setItem('gpVoiceRecentV5',JSON.stringify(a.slice(-80)))}catch(_){}}
    function buildDynamicVoiceTrack(){const lang=currentLanguage==='ar'?'ar':'en',b=GP_VOICE_BANK[lang],name=gpPick(GP_STAFF[lang]),r=Math.random();let text='',category='motivation',tone='warm';if(r<.28){category='funny';tone='funny';text=`${gpPick(b.starts)}، ${gpPick(b.funny)}. ${gpPick(b.ends)}.`}else if(r<.52){category='person';tone=Math.random()<.55?'funny':'warm';text=`${gpPick(b.person).replace('{name}',name)}. ${gpPick(b.ends)}.`}else if(r<.82){text=`${gpPick(b.starts)}، ${gpPick(b.motivation)}، ${gpPick(b.action)}. ${gpPick(b.ends)}.`}else{category='workshop';text=`${gpPick(b.starts)}، ${gpPick(b.action)}. ${gpPick(b.motivation)}. ${gpPick(b.ends)}.`}return{id:`dyn-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,category,person:name,text:text.replace(/\s+/g,' ').trim(),url:'',lang,tone}}
    function chooseVoiceTrack(){const recent=gpRecentVoice();let track=buildDynamicVoiceTrack();for(let i=0;i<30&&recent.includes(track.text);i++)track=buildDynamicVoiceTrack();gpRememberVoice(track.text);return track}
    function speakFallback(track){if(!('speechSynthesis'in window)||!track)return false;try{const u=new SpeechSynthesisUtterance(track.text),isAr=track.lang==='ar';u.lang=isAr?'ar-SY':'en-US';u.rate=track.tone==='funny'?1.12:1.03;u.pitch=track.tone==='funny'?1.34:1.18;u.volume=1;const voices=window.speechSynthesis.getVoices(),h=['female','zira','samantha','sara','salma','hoda','laila','layla','maryam','mariam','nora','rana','jenny','aria','ava','emma'],female=v=>h.some(x=>String(v.name||'').toLowerCase().includes(x)),lang=v=>String(v.lang||'').toLowerCase();let preferred=isAr?(voices.find(v=>lang(v).startsWith('ar-sy')&&female(v))||voices.find(v=>lang(v).startsWith('ar-sy'))||voices.find(v=>lang(v).startsWith('ar')&&female(v))||voices.find(v=>lang(v).startsWith('ar'))):(voices.find(v=>lang(v).startsWith('en')&&female(v))||voices.find(v=>lang(v).startsWith('en-us'))||voices.find(v=>lang(v).startsWith('en')));if(preferred)u.voice=preferred;u.onend=()=>{teamVoicePlaying=false;setVoiceCaption('',false)};u.onerror=()=>{teamVoicePlaying=false;setVoiceCaption('',false)};teamVoicePlaying=true;setVoiceCaption(track.text,true);window.speechSynthesis.cancel();window.speechSynthesis.speak(u);return true}catch(_){return false}}
    function playTeamVoice(track,manual=false){if(!track||detailMode||teamVoicePlaying)return false;if(!manual&&(!teamVoiceEnabled||document.hidden))return false;stopTeamVoiceAudio();return speakFallback(track)}

'''
    tv = replace_once(tv, "    async function confirmCollection(item, button) {", override + "    async function confirmCollection(item, button) {", "voice override")
    p.write_text(tv, encoding="utf-8")


def upgrade_flask():
    p = Path("flask_app.py")
    s = p.read_text(encoding="utf-8")
    if "GP_RENDER_STATIC_CORS_2026_09_08" not in s:
        s = replace_once(s, "app = Flask(__name__)\n", "app = Flask(__name__)\n\n# GP_RENDER_STATIC_CORS_2026_09_08\n@app.after_request\ndef add_gp_tv_cors_headers(response):\n    origin=request.headers.get('Origin','').strip()\n    allowed=(origin=='https://golden-palace-service-tracker.onrender.com' or bool(re.fullmatch(r'https://gp-tv(?:-[a-z0-9-]+)?\\.onrender\\.com',origin)))\n    if allowed:\n        response.headers['Access-Control-Allow-Origin']=origin\n        response.headers['Vary']='Origin'\n        response.headers['Access-Control-Allow-Headers']='Content-Type'\n        response.headers['Access-Control-Allow-Methods']='GET, POST, OPTIONS'\n    return response\n", "cors")
        s = replace_once(s, "@app.route(\"/\")\ndef root_health():\n    # Intentionally no external I/O. Gives PythonAnywhere a fast startup probe.\n    return \"Golden Palace Service Tracker OK\", 200\n", "@app.route(\"/\")\n@app.route(\"/t\")\ndef root_health():\n    return tv_display()\n", "root")
        s = s.replace("PythonAnywhere", "Render")
        p.write_text(s, encoding="utf-8")


def upgrade_app():
    p = Path("tools_tracker.py")
    s = p.read_text(encoding="utf-8")
    if "GP_APP_UI_REFRESH_2026_09_08" in s:
        return
    marker = "# ==========================================\n# DATABASE ORM (DocType Engine)\n# =========================================="
    ui = '''# GP_APP_UI_REFRESH_2026_09_08\nif not is_tv_mode:\n    st.markdown("""\n    <style>\n      :root{--gp-navy:#071a2d;--gp-navy2:#0d2c49;--gp-gold:#d5a62e}\n      .stApp{background:radial-gradient(circle at 8% 0%,#edf4ff 0,#f6f8fb 34%,#eef2f7 100%)!important}\n      .block-container{max-width:1500px;padding-top:1.35rem;padding-bottom:3rem}\n      [data-testid="stSidebar"]{background:linear-gradient(180deg,var(--gp-navy),var(--gp-navy2))!important;border-inline-end:1px solid rgba(213,166,46,.35)}\n      [data-testid="stSidebar"] *{color:#f8fafc}[data-testid="stSidebar"] button{min-height:44px;border-radius:12px;border:1px solid rgba(255,255,255,.14);background:rgba(255,255,255,.07);color:#fff;font-weight:750}\n      .erp-card{border:1px solid rgba(148,163,184,.28)!important;border-radius:18px!important;box-shadow:0 10px 30px rgba(15,23,42,.07)!important;padding:22px!important;background:rgba(255,255,255,.96)!important}\n      div[data-testid="stMetric"]{background:#fff;border:1px solid rgba(148,163,184,.28);border-radius:16px;padding:16px;box-shadow:0 7px 22px rgba(15,23,42,.05)}\n      .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{min-height:44px;border-radius:12px;font-weight:750}\n      input,textarea,[data-baseweb="select"]>div{border-radius:12px!important}\n      .gp-app-hero{background:linear-gradient(120deg,var(--gp-navy),var(--gp-navy2));color:#fff;border:1px solid rgba(213,166,46,.55);border-radius:20px;padding:22px 24px;margin:.2rem 0 1.1rem;box-shadow:0 14px 38px rgba(7,26,45,.18)}\n      .gp-app-hero h1{color:#fff!important;margin:0 0 6px!important;font-size:clamp(28px,3vw,42px)}.gp-app-hero p{color:#dbe7f3!important;margin:0}.gp-app-chip{display:inline-flex;margin-top:12px;padding:6px 10px;border-radius:999px;background:rgba(213,166,46,.18);border:1px solid rgba(213,166,46,.55);color:#fff;font-size:12px;font-weight:800}\n      button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid #f0be3f!important;outline-offset:2px!important}\n    </style>\n    """,unsafe_allow_html=True)\n\n'''
    s = replace_once(s, marker, ui + marker, "app ui")
    s = replace_once(s, '    st.title(tr("workspace_title"))\n', '    hero_text = "لوحة تشغيل سريعة وواضحة لكل مهام القصر الذهبي" if st.session_state.get("ui_language") == "ar" else "A faster, clearer operating view for Golden Palace"\n    st.markdown(f"""<section class="gp-app-hero"><h1>🏢 {tr(\'workspace_title\')}</h1><p>{hero_text}</p><span class="gp-app-chip">{tr(\'user\')}: {current_user}</span></section>""", unsafe_allow_html=True)\n', "hero")
    p.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    upgrade_tv()
    upgrade_flask()
    upgrade_app()
