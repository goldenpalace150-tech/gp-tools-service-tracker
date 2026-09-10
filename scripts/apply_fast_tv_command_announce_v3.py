from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Missing patch target: {label}")
    return text.replace(old, new, 1)


tools_path = Path("tools_tracker.py")
flask_path = Path("flask_app.py")
tv_path = Path("templates/tv.html")
announce_path = Path("templates/announce.html")

tools = tools_path.read_text(encoding="utf-8")
flask = flask_path.read_text(encoding="utf-8")
tv = tv_path.read_text(encoding="utf-8")
announce = announce_path.read_text(encoding="utf-8")

# =============================================================================
# STREAMLIT: commands are lightweight by default. Only the explicit refresh
# button asks the TV to rebuild dashboard data.
# =============================================================================
if "GP_FAST_COMMAND_PATH_V3" not in tools:
    tools = replace_once(
        tools,
        "# GP_TV_CONTROL_RELIABLE_V2\n\ndef gp_apply_tv_control_and_wait(reason, **fields):\n    \"\"\"Send one TV command, force fresh data, and wait briefly for TV ACK.\"\"\"\n    payload = dict(fields)\n    payload[\"refresh_now\"] = True\n    payload[\"reason\"] = str(reason or \"backend_tv_control\")[:120]\n",
        "# GP_TV_CONTROL_RELIABLE_V2\n# GP_FAST_COMMAND_PATH_V3\n\ndef gp_apply_tv_control_and_wait(reason, refresh_data=False, **fields):\n    \"\"\"Send one lightweight TV command and wait briefly for the TV ACK.\n\n    Dashboard data is refreshed only when refresh_data=True. This keeps simple\n    voice/toggle commands independent from the heavier Ledger/remarks refresh.\n    \"\"\"\n    payload = dict(fields)\n    if refresh_data:\n        payload[\"refresh_now\"] = True\n    payload[\"reason\"] = str(reason or \"backend_tv_control\")[:120]\n",
        "lightweight TV control helper",
    )

    tools = tools.replace(
        "f\"✅ {status_word} لصوت الموظفين، وتم تحديث البيانات، والتلفزيون أكد تنفيذ الأمر.\"",
        "f\"✅ {status_word} لصوت الموظفين، والتلفزيون أكد تنفيذ الأمر.\"",
    )
    tools = tools.replace(
        "\"⚠️ تم حفظ أمر صوت الموظفين وتحديث البيانات على الخادم، لكن التلفزيون لم يؤكد التنفيذ خلال 6 ثوانٍ.\"",
        "\"⚠️ تم حفظ أمر صوت الموظفين على الخادم، لكن التلفزيون لم يؤكد التنفيذ خلال 6 ثوانٍ.\"",
    )
    tools = tools.replace(
        "f\"✅ {status_word} لتنبيه التأخير، وتم تحديث البيانات، والتلفزيون أكد تنفيذ الأمر.\"",
        "f\"✅ {status_word} لتنبيه التأخير، والتلفزيون أكد تنفيذ الأمر.\"",
    )
    tools = tools.replace(
        "\"⚠️ تم حفظ أمر تنبيه التأخير وتحديث البيانات على الخادم، لكن التلفزيون لم يؤكد التنفيذ خلال 6 ثوانٍ.\"",
        "\"⚠️ تم حفظ أمر تنبيه التأخير على الخادم، لكن التلفزيون لم يؤكد التنفيذ خلال 6 ثوانٍ.\"",
    )
    tools = tools.replace(
        'gp_apply_tv_control_and_wait("manual_backend_push")',
        'gp_apply_tv_control_and_wait("manual_backend_push", refresh_data=True)',
    )
    tools = tools.replace(
        "كل زر ينفذ العملية ويطلب تحديث البيانات في نفس اللحظة. الأخضر يظهر فقط بعد أن يؤكد التلفزيون تنفيذ الأمر.",
        "أوامر الصوت والتنبيه تُرسل بخفة من دون إعادة تحميل كل البيانات. زر تحديث البيانات وحده يعيد تحميل Ledger والملاحظات. الأخضر يظهر بعد تأكيد التلفزيون.",
    )

# =============================================================================
# FLASK: command_id changes for every control command, while data_revision is
# changed only for an explicit refresh. This is the server half of the fast path.
# =============================================================================
if "GP_FAST_COMMAND_PATH_V3" not in flask:
    flask = replace_once(
        flask,
        "@app.route(\"/api/tv-control\", methods=[\"GET\", \"POST\", \"OPTIONS\"])\ndef api_tv_control():\n",
        "# GP_FAST_COMMAND_PATH_V3\n@app.route(\"/api/tv-control\", methods=[\"GET\", \"POST\", \"OPTIONS\"])\ndef api_tv_control():\n",
        "flask fast command marker",
    )
    flask = replace_once(
        flask,
        "        refresh_now = bool(payload.get(\"refresh_now\"))\n        if changed or refresh_now:\n            command_id = str(time.time_ns())\n            state[\"command_id\"] = command_id\n            state[\"command_created_at\"] = time.time()\n            # Every control command also carries an immediate data refresh revision.\n            state[\"data_revision\"] = command_id\n\n",
        "        refresh_now = bool(payload.get(\"refresh_now\"))\n        if changed or refresh_now:\n            command_id = str(time.time_ns())\n            state[\"command_id\"] = command_id\n            state[\"command_created_at\"] = time.time()\n            # Fast path: ordinary commands never trigger the heavy dashboard refresh.\n            # Only an explicit refresh request advances the data revision.\n            if refresh_now:\n                state[\"data_revision\"] = command_id\n\n",
        "server command/data revision split",
    )

# =============================================================================
# TV: visible fullscreen control, stronger Arabic card spacing, and optional
# interaction-triggered Syrian humour using the same server Arabic voice.
# =============================================================================
if "GP_TV_LAYOUT_FULLSCREEN_MOVEMENT_V3" not in tv:
    tv_addition = r'''
    <!-- GP_TV_LAYOUT_FULLSCREEN_MOVEMENT_V3 -->
    <style id="gp-tv-layout-fullscreen-movement-v3">
      body.lang-ar.main-view-body .workflow-card{
        padding-top:clamp(46px,4.2vw,62px)!important;
      }
      body.lang-ar.main-view-body .workflow-card .icon{
        top:12px!important;right:16px!important;left:auto!important;
      }
      body.lang-ar.main-view-body .workflow-card h2{
        max-width:100%!important;width:100%!important;margin:0!important;
        text-align:center!important;line-height:1.18!important;
        overflow-wrap:anywhere!important;
      }
      body.lang-ar.main-view-body .workflow-card .count{
        text-align:center!important;
      }
      .gp-tv-floating-controls{
        position:fixed;right:14px;bottom:14px;z-index:95;display:flex;gap:8px;
        align-items:center;direction:ltr;
      }
      .gp-tv-float-btn{
        border:1px solid rgba(213,166,46,.72);background:#071a2d;color:#fff;
        min-height:42px;padding:9px 13px;border-radius:999px;font-weight:850;
        box-shadow:0 8px 24px rgba(7,26,45,.24);font-size:13px;
      }
      .gp-tv-float-btn.on{background:#14532d;border-color:#86efac}
      .gp-tv-float-btn:hover{filter:brightness(1.08)}
      @media(max-width:800px){.gp-tv-floating-controls{right:8px;bottom:8px}.gp-tv-float-btn{padding:8px 10px;font-size:12px}}
    </style>
    <div class="gp-tv-floating-controls" id="gpTvFloatingControls">
      <button type="button" class="gp-tv-float-btn" id="gpFullscreenToggle">⛶ Fullscreen</button>
      <button type="button" class="gp-tv-float-btn" id="gpMovementVoiceToggle">😄 حركة ON</button>
    </div>
    <script>
    (() => {
      const detail = new URLSearchParams(location.search).get('view') === 'details';
      const fsBtn = document.getElementById('gpFullscreenToggle');
      const moveBtn = document.getElementById('gpMovementVoiceToggle');
      const controls = document.getElementById('gpTvFloatingControls');
      if (detail && controls) controls.style.display = 'none';

      function updateFullscreenButton(){
        if(!fsBtn) return;
        fsBtn.textContent = document.fullscreenElement ? '⤢ Exit fullscreen' : '⛶ Fullscreen';
      }
      async function toggleFullscreen(event){
        if(event){event.preventDefault();event.stopPropagation();}
        try{
          if(document.fullscreenElement) await document.exitFullscreen();
          else await document.documentElement.requestFullscreen({navigationUI:'hide'});
        }catch(_){}
        updateFullscreenButton();
      }
      if(fsBtn) fsBtn.addEventListener('click', toggleFullscreen);
      document.addEventListener('fullscreenchange', updateFullscreenButton);
      updateFullscreenButton();

      const STORAGE_KEY='gpMovementFunnyVoiceV1';
      let enabled=true;
      try{enabled=localStorage.getItem(STORAGE_KEY)!=='0'}catch(_){}
      let lastPlayed=0;
      let playing=false;
      const COOLDOWN_MS=25000;
      const phrases=[
        'لا تِلْعَب بالنار، بتحرق أصابيعك.',
        'هَدّي اللعب يا بطل، وخَلّي الشغل يمشي.',
        'الشاشة للشغل مو للعب يا غالي.',
        'انتبه يا نجم، كل حركة محسوبة.',
        'يا زلمة، خلّي البركة بالشغل مو بالمشاوير عالشاشة.'
      ];
      function updateMoveButton(){
        if(!moveBtn) return;
        moveBtn.textContent=enabled?'😄 حركة ON':'😴 حركة OFF';
        moveBtn.classList.toggle('on',enabled);
      }
      if(moveBtn){
        moveBtn.addEventListener('click',(event)=>{
          event.preventDefault();event.stopPropagation();
          enabled=!enabled;
          try{localStorage.setItem(STORAGE_KEY,enabled?'1':'0')}catch(_){}
          updateMoveButton();
        });
      }
      updateMoveButton();

      async function speakFunnyInteraction(event){
        if(detail || !enabled || document.hidden || playing) return;
        if(event && event.target && event.target.closest && event.target.closest('#gpTvFloatingControls')) return;
        const now=Date.now();
        if(now-lastPlayed<COOLDOWN_MS) return;
        lastPlayed=now;
        playing=true;
        const phrase=phrases[Math.floor(Math.random()*phrases.length)];
        try{
          const response=await fetch(`/api/followup-voice?lang=ar&text=${encodeURIComponent(phrase)}&t=${Date.now()}`,{cache:'no-store'});
          if(!response.ok) throw new Error('voice');
          const data=await response.json();
          if(!data || !data.ok || !data.audio_url) throw new Error('voice');
          const audio=new Audio(data.audio_url);
          audio.volume=1.0;
          await audio.play();
          await new Promise(resolve=>{audio.onended=resolve;audio.onerror=resolve;setTimeout(resolve,9000)});
        }catch(_){}
        finally{playing=false;}
      }
      let pointerTimer=0;
      document.addEventListener('pointermove',(event)=>{
        clearTimeout(pointerTimer);
        pointerTimer=setTimeout(()=>speakFunnyInteraction(event),350);
      },{passive:true});
      ['pointerdown','touchstart','keydown'].forEach(name=>document.addEventListener(name,speakFunnyInteraction,{passive:true}));
    })();
    </script>
'''
    tv = replace_once(tv, "</body>\n</html>", tv_addition + "</body>\n</html>", "TV fullscreen/movement controls")

# =============================================================================
# ANNOUNCE: branded icon, submit loading overlay, faster receipt polling, and
# a short police-style alert when the TV technical-delivery ACK arrives.
# =============================================================================
if "GP_ANNOUNCE_BRAND_FAST_ACK_V3" not in announce:
    announce = replace_once(
        announce,
        "  <title>Golden Palace · Live TV Announcement</title>\n",
        "  <title>Golden Palace · Live TV Announcement</title>\n  <!-- GP_ANNOUNCE_BRAND_FAST_ACK_V3 -->\n",
        "announce marker",
    )
    announce = replace_once(
        announce,
        ".brand-line{display:flex;align-items:center;gap:14px}.mark{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:2px solid var(--gold2);color:var(--gold2);font-weight:950;letter-spacing:.05em;background:rgba(255,255,255,.04)}\n",
        ".brand-line{display:flex;align-items:center;gap:14px}.mark{width:58px;height:58px;border-radius:16px;display:flex;align-items:center;justify-content:center;border:1px solid rgba(241,209,108,.55);background:#071a2d;overflow:hidden;flex:0 0 58px}.mark svg{width:100%;height:100%;display:block}\n",
        "announce brand mark CSS",
    )
    announce = replace_once(
        announce,
        "    .privacy{margin-top:14px;text-align:center;color:var(--muted);font-size:12px;line-height:1.55}.last{margin-top:14px;border-top:1px solid var(--line);padding-top:14px}.last small{color:var(--muted);font-weight:700}.last div{margin-top:5px;font-weight:800;line-height:1.55;overflow-wrap:anywhere}\n",
        "    .privacy{margin-top:14px;text-align:center;color:var(--muted);font-size:12px;line-height:1.55}.last{margin-top:14px;border-top:1px solid var(--line);padding-top:14px}.last small{color:var(--muted);font-weight:700}.last div{margin-top:5px;font-weight:800;line-height:1.55;overflow-wrap:anywhere}\n    .gp-loading-overlay{position:fixed;inset:0;z-index:999;display:none;align-items:center;justify-content:center;background:rgba(7,26,45,.76);backdrop-filter:blur(5px)}.gp-loading-overlay.show{display:flex}.gp-loading-card{width:min(380px,calc(100% - 34px));background:#071a2d;color:#fff;border:1px solid rgba(213,166,46,.72);border-radius:24px;padding:28px;text-align:center;box-shadow:0 24px 70px rgba(0,0,0,.35)}.gp-loading-logo{width:74px;height:74px;margin:0 auto 14px}.gp-loading-logo svg{width:100%;height:100%}.gp-loading-ring{width:38px;height:38px;margin:13px auto;border:4px solid rgba(255,255,255,.18);border-top-color:var(--gold2);border-radius:50%;animation:gpSpin .8s linear infinite}@keyframes gpSpin{to{transform:rotate(360deg)}}.ack-flash{animation:gpAckFlash .55s ease 0s 3}@keyframes gpAckFlash{50%{box-shadow:0 0 0 7px rgba(22,163,74,.18),0 12px 36px rgba(15,23,42,.08)}}\n",
        "announce loading/ack CSS",
    )
    logo_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" aria-label="Golden Palace"><rect width="512" height="512" rx="96" fill="#071a2d"/><circle cx="256" cy="256" r="178" fill="none" stroke="#d5a62e" stroke-width="24"/><text x="256" y="290" font-family="Arial,sans-serif" font-size="142" font-weight="700" text-anchor="middle" fill="#f4bd2d">GP</text></svg>'
    announce = replace_once(
        announce,
        '<section class="brand"><div class="brand-line"><div class="mark">GP</div><div><h1>Live TV Announcement</h1><p>إعلان مباشر إلى شاشة الورشة · Management-only publishing page</p></div></div></section>',
        f'<section class="brand"><div class="brand-line"><div class="mark">{logo_svg}</div><div><h1>Golden Palace · Live TV Announcement</h1><p>إعلان مباشر إلى شاشة الورشة · Management-only publishing page</p></div></div></section>',
        "announce branded header",
    )
    announce = replace_once(
        announce,
        "<body>\n  <main class=\"shell\">",
        f'<body>\n  <div id="gpLoadingOverlay" class="gp-loading-overlay" aria-live="polite"><div class="gp-loading-card"><div class="gp-loading-logo">{logo_svg}</div><strong>Golden Palace</strong><div class="gp-loading-ring"></div><div>جارٍ إرسال الإعلان إلى شاشة الورشة…<br><small>Sending command to TV…</small></div></div></div>\n  <main class="shell">',
        "announce loading overlay",
    )
    announce = replace_once(
        announce,
        '<form method="post" action="/announce" autocomplete="off">',
        '<form id="announceForm" method="post" action="/announce" autocomplete="off">',
        "announce form id",
    )
    helper_script = r'''
  <script>
  (() => {
    const form=document.getElementById('announceForm');
    const loading=document.getElementById('gpLoadingOverlay');
    if(form) form.addEventListener('submit',()=>{ if(loading) loading.classList.add('show'); });

    window.playPoliceAlert = function playPoliceAlert(){
      try{
        const AudioCtx=window.AudioContext||window.webkitAudioContext;
        if(!AudioCtx) return;
        const ctx=new AudioCtx();
        const gain=ctx.createGain();
        gain.gain.setValueAtTime(0.0001,ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.16,ctx.currentTime+0.03);
        gain.gain.exponentialRampToValueAtTime(0.0001,ctx.currentTime+1.05);
        gain.connect(ctx.destination);
        const osc=ctx.createOscillator();
        osc.type='sine';
        osc.frequency.setValueAtTime(690,ctx.currentTime);
        osc.frequency.linearRampToValueAtTime(980,ctx.currentTime+0.24);
        osc.frequency.linearRampToValueAtTime(690,ctx.currentTime+0.5);
        osc.frequency.linearRampToValueAtTime(980,ctx.currentTime+0.76);
        osc.frequency.linearRampToValueAtTime(690,ctx.currentTime+1.0);
        osc.connect(gain);osc.start();osc.stop(ctx.currentTime+1.08);
        setTimeout(()=>{try{ctx.close()}catch(_){}},1400);
      }catch(_){}
    };
  })();
  </script>
'''
    announce = replace_once(
        announce,
        "\n  {% if success and published_id %}\n  <script>\n",
        "\n" + helper_script + "\n  {% if success and published_id %}\n  <script>\n",
        "announce helper script",
    )
    announce = replace_once(
        announce,
        "    let attempts = 0;\n    let finished = false;\n",
        "    let attempts = 0;\n    let finished = false;\n    let policePlayed = false;\n",
        "announce alert state",
    )
    announce = replace_once(
        announce,
        "            if (displayed) {\n              displayStep.classList.add('on');\n",
        "            if (displayed) {\n              displayStep.classList.add('on');\n              if (!policePlayed) {\n                policePlayed = true;\n                box.classList.add('ack-flash');\n                try { window.playPoliceAlert && window.playPoliceAlert(); } catch (_) {}\n                setTimeout(() => box.classList.remove('ack-flash'), 1900);\n              }\n",
        "announce technical ACK alert",
    )
    announce = announce.replace("if (!finished && attempts >= 45)", "if (!finished && attempts >= 180)")
    announce = announce.replace("if (!finished) setTimeout(check, 1000);", "if (!finished) setTimeout(check, 250);")
    announce = announce.replace("setTimeout(check, 500);", "setTimeout(check, 200);")

# Persist changes.
tools_path.write_text(tools, encoding="utf-8")
flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
announce_path.write_text(announce, encoding="utf-8")
print("Fast TV command path, announcement ACK alert, fullscreen, Arabic layout, and movement voice patched")
