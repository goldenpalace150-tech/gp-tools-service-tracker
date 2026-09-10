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

# -----------------------------------------------------------------------------
# 1) Backend TV acknowledgments: hard maximum target is 5 seconds, not 6.
# -----------------------------------------------------------------------------
if "GP_ACK_MAX_5S_V4" not in tools:
    tools = tools.replace("deadline = time.time() + 6.0", "# GP_ACK_MAX_5S_V4\n    deadline = time.time() + 5.0")
    tools = tools.replace("خلال 6 ثوانٍ", "خلال 5 ثوانٍ")

# -----------------------------------------------------------------------------
# 2) TV: remove the previous floating-control / pointer-movement experiment.
#    Add fullscreen + REAL camera motion controls into the top toolbar.
#    Fix Arabic dashboard card order/alignment and make announcement pickup fast.
# -----------------------------------------------------------------------------
if "GP_TV_REAL_MOTION_V4" not in tv:
    old_marker = "    <!-- GP_TV_LAYOUT_FULLSCREEN_MOVEMENT_V3 -->"
    if old_marker in tv:
        start = tv.index(old_marker)
        end = tv.index("</body>", start)
        tv = tv[:start] + tv[end:]

    tv = tv.replace(
        '<button id="voiceTestButton" class="action-btn" type="button">▶ Test voice</button>',
        '<button id="voiceTestButton" class="action-btn" type="button">▶ Test voice</button>\n'
        '            <button id="motionVoiceButton" class="action-btn" type="button" title="Real camera movement detection">🎥 حركة</button>\n'
        '            <button id="fullscreenButton" class="action-btn" type="button" title="Fullscreen">⛶ ملء الشاشة</button>',
        1,
    )

    head_css = r'''
    <!-- GP_TV_REAL_MOTION_V4 -->
    <style id="gp-tv-real-motion-v4">
      /* Arabic means right-to-left card placement too: first workflow starts at the right. */
      body.lang-ar.main-view-body .dashboard-grid{direction:rtl!important}
      body.lang-ar.main-view-body .workflow-card{direction:rtl!important;text-align:right!important;padding-top:54px!important}
      body.lang-ar.main-view-body .workflow-card .icon{top:13px!important;right:18px!important;left:auto!important}
      body.lang-ar.main-view-body .workflow-card .open-hint{top:15px!important;left:18px!important;right:auto!important;text-align:left!important}
      body.lang-ar.main-view-body .workflow-card .count{width:100%!important;text-align:center!important;margin:3px 0 5px!important}
      body.lang-ar.main-view-body .workflow-card h2{width:100%!important;max-width:100%!important;text-align:center!important;margin:0!important;line-height:1.15!important}
      body.lang-ar.main-view-body .workflow-card p{width:100%!important;text-align:center!important;margin-left:auto!important;margin-right:auto!important}
      #fullscreenButton,#motionVoiceButton{flex:0 0 auto!important;white-space:nowrap!important}
      #motionVoiceButton.on{background:#0a2d29!important;border-color:#1f755a!important;color:#baf7cf!important}
      #motionVoiceButton.error{background:#381720!important;border-color:#7f1d2d!important;color:#fecaca!important}
      #gpMotionVideo,#gpMotionCanvas{position:fixed!important;width:1px!important;height:1px!important;opacity:.001!important;pointer-events:none!important;left:-20px!important;bottom:-20px!important}
    </style>
'''
    tv = replace_once(tv, "</head>\n", head_css + "</head>\n", "TV v4 head CSS")

    runtime = r'''
    <!-- GP_TV_REAL_MOTION_RUNTIME_V4 -->
    <video id="gpMotionVideo" playsinline muted></video><canvas id="gpMotionCanvas" width="96" height="54"></canvas>
    <script>
    (() => {
      const detail = new URLSearchParams(location.search).get('view') === 'details';
      const fsButton = document.getElementById('fullscreenButton');
      const motionButton = document.getElementById('motionVoiceButton');
      const motionVideo = document.getElementById('gpMotionVideo');
      const motionCanvas = document.getElementById('gpMotionCanvas');
      const MOTION_KEY = 'gpRealCameraMotionVoiceV4';
      let motionEnabled = false;
      let motionStream = null;
      let motionTimer = null;
      let priorFrame = null;
      let lastMotionVoice = 0;
      let motionVoiceBusy = false;
      const motionPhrases = [
        'شو هالحركة يا شباب؟ الشاشة عم تراقب أكتر من المدير اليوم!',
        'مين مرق من هون؟ يعطيك العافية، بس لا تنسى تحدّث الحالة.',
        'أهلا بالحركة! طالما عم نتحرك، خلّونا نحرك الحالات المتأخرة معنا.',
        'شايفينكم يا أبطال. حركة حلوة، بدنا معها تحديث أحلى.',
        'يا سلام عالنشاط! الجهاز اللي ناطر صيانة صار متحمس أكتر منّا.'
      ];

      function setFullscreenLabel(){
        if(!fsButton) return;
        const ar = document.body.classList.contains('lang-ar');
        fsButton.textContent = document.fullscreenElement ? (ar ? '⤢ خروج' : '⤢ Exit') : (ar ? '⛶ ملء الشاشة' : '⛶ Fullscreen');
      }
      async function toggleFullscreen(e){
        e?.preventDefault(); e?.stopPropagation();
        try{
          if(document.fullscreenElement) await document.exitFullscreen();
          else await document.documentElement.requestFullscreen({navigationUI:'hide'});
        }catch(_){}
        setFullscreenLabel();
      }
      fsButton?.addEventListener('click', toggleFullscreen);
      document.addEventListener('fullscreenchange', setFullscreenLabel);
      setFullscreenLabel();

      function setMotionButton(state, error=false){
        if(!motionButton) return;
        motionButton.classList.toggle('on', !!state && !error);
        motionButton.classList.toggle('error', !!error);
        const ar = document.body.classList.contains('lang-ar');
        motionButton.textContent = error ? (ar ? '🎥 الكاميرا غير متاحة' : '🎥 Camera unavailable') :
          state ? (ar ? '🎥 الحركة ON' : '🎥 Motion ON') : (ar ? '🎥 الحركة OFF' : '🎥 Motion OFF');
      }

      async function speakMotionPhrase(){
        const now = Date.now();
        if(motionVoiceBusy || now-lastMotionVoice < 30000 || detail || document.hidden) return;
        motionVoiceBusy = true; lastMotionVoice = now;
        const phrase = motionPhrases[Math.floor(Math.random()*motionPhrases.length)];
        try{
          const r = await fetch(apiUrl(`/api/followup-voice?lang=ar&text=${encodeURIComponent(phrase)}&t=${Date.now()}`), {cache:'no-store'});
          if(!r.ok) throw new Error('voice');
          const data = await r.json();
          if(!data?.ok || !data.audio_url) throw new Error('voice');
          const audio = new Audio(apiUrl(data.audio_url));
          audio.volume = 1;
          await audio.play();
          await new Promise(resolve => { audio.onended=resolve; audio.onerror=resolve; setTimeout(resolve,10000); });
        }catch(_){}
        finally{motionVoiceBusy=false;}
      }

      function inspectMotionFrame(){
        if(!motionEnabled || !motionVideo || motionVideo.readyState < 2) return;
        const ctx = motionCanvas.getContext('2d', {willReadFrequently:true});
        ctx.drawImage(motionVideo,0,0,96,54);
        const frame = ctx.getImageData(0,0,96,54).data;
        if(priorFrame){
          let changed=0, samples=0;
          for(let i=0;i<frame.length;i+=16){
            const d=Math.abs(frame[i]-priorFrame[i])+Math.abs(frame[i+1]-priorFrame[i+1])+Math.abs(frame[i+2]-priorFrame[i+2]);
            if(d>70) changed++;
            samples++;
          }
          if(samples && changed/samples > 0.045) speakMotionPhrase();
        }
        priorFrame = new Uint8ClampedArray(frame);
      }

      function stopMotion(){
        motionEnabled=false; priorFrame=null;
        if(motionTimer){clearInterval(motionTimer);motionTimer=null;}
        if(motionStream){motionStream.getTracks().forEach(t=>t.stop());motionStream=null;}
        try{localStorage.setItem(MOTION_KEY,'0')}catch(_){}
        setMotionButton(false);
      }
      async function startMotion(){
        if(detail) return;
        if(!navigator.mediaDevices?.getUserMedia){setMotionButton(false,true);return;}
        try{
          motionStream = await navigator.mediaDevices.getUserMedia({video:{width:{ideal:320},height:{ideal:180},frameRate:{ideal:8,max:12}},audio:false});
          motionVideo.srcObject=motionStream;
          await motionVideo.play();
          motionEnabled=true; priorFrame=null;
          try{localStorage.setItem(MOTION_KEY,'1')}catch(_){}
          setMotionButton(true);
          motionTimer=setInterval(inspectMotionFrame,700);
        }catch(_){motionEnabled=false;setMotionButton(false,true);}
      }
      motionButton?.addEventListener('click', async e => {
        e.preventDefault();e.stopPropagation();
        if(motionEnabled) stopMotion(); else await startMotion();
      });
      setMotionButton(false);
      try{if(localStorage.getItem(MOTION_KEY)==='1') setTimeout(startMotion,1200)}catch(_){}

      // Keep toolbar labels correct after language changes.
      document.getElementById('languageSelect')?.addEventListener('change',()=>setTimeout(()=>{setFullscreenLabel();setMotionButton(motionEnabled,false)},0));

      // Police-style attention sound belongs on the TV when a new management announcement appears.
      window.gpPlayTvPoliceAlert = function(){
        try{
          const AudioCtx=window.AudioContext||window.webkitAudioContext;
          if(!AudioCtx) return;
          const ctx=new AudioCtx();
          ctx.resume?.();
          const gain=ctx.createGain(); gain.connect(ctx.destination);
          gain.gain.setValueAtTime(.0001,ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(.22,ctx.currentTime+.03);
          gain.gain.exponentialRampToValueAtTime(.0001,ctx.currentTime+1.55);
          const osc=ctx.createOscillator(); osc.type='square'; osc.connect(gain);
          osc.frequency.setValueAtTime(650,ctx.currentTime);
          osc.frequency.linearRampToValueAtTime(1050,ctx.currentTime+.28);
          osc.frequency.linearRampToValueAtTime(650,ctx.currentTime+.56);
          osc.frequency.linearRampToValueAtTime(1050,ctx.currentTime+.84);
          osc.frequency.linearRampToValueAtTime(650,ctx.currentTime+1.12);
          osc.frequency.linearRampToValueAtTime(1050,ctx.currentTime+1.4);
          osc.start();osc.stop(ctx.currentTime+1.58);
          setTimeout(()=>ctx.close?.(),1900);
        }catch(_){}
      };
    })();
    </script>
'''
    tv = replace_once(tv, "</body>\n</html>", runtime + "</body>\n</html>", "TV v4 runtime")

    # Faster announcement pickup: 500 ms polling gives multiple chances inside five seconds.
    tv = tv.replace("const GP_MANUAL_ANNOUNCEMENT_POLL_MS = 1000;", "const GP_MANUAL_ANNOUNCEMENT_POLL_MS = 500;")
    # Play the police sound immediately after the announcement becomes visibly displayed.
    tv = tv.replace(
        "        if (overlay) overlay.classList.add('show');\n        // This is the first trustworthy delivery point: the TV page is visible and the overlay is on screen.\n",
        "        if (overlay) overlay.classList.add('show');\n        try { window.gpPlayTvPoliceAlert?.(); } catch (_) {}\n        // This is the first trustworthy delivery point: the TV page is visible and the overlay is on screen.\n",
        1,
    )

# -----------------------------------------------------------------------------
# 3) /announce: Arabic-first management page, explicit live-TV delivery target,
#    max-five-second technical receipt message, and fast polling. Police alert is
#    generated on the TV itself (not only on the sender's browser).
# -----------------------------------------------------------------------------
if "GP_ANNOUNCE_V4" not in announce:
    announce = announce.replace("<!-- GP_ANNOUNCE_BRAND_FAST_ACK_V3 -->", "<!-- GP_ANNOUNCE_BRAND_FAST_ACK_V3 -->\n  <!-- GP_ANNOUNCE_V4 -->")
    announce = announce.replace("Management-only publishing page", "صفحة الإدارة لإرسال إعلان مباشر ومؤكد إلى شاشة الورشة")
    announce = announce.replace("📣 Publish to TV Now", "📣 إرسال الآن إلى شاشة الورشة")
    announce = announce.replace("Accepted by server", "تم الاستلام من الخادم")
    announce = announce.replace("بانتظار تأكيد شاشة التلفزيون... قد تكون الشاشة مطفأة أو غير متصلة.", "بانتظار وصول الإعلان إلى شاشة الورشة — التأكيد التقني مستهدف خلال 5 ثوانٍ كحد أقصى.")
    announce = announce.replace("TV received", "وصل للتلفزيون")
    announce = announce.replace("Voice alert", "التنبيه الصوتي")
    announce = announce.replace("Seen / Acknowledge", "تم الاطلاع")
    announce = announce.replace("setTimeout(check, 500);", "setTimeout(check, 150);")
    announce = announce.replace("setTimeout(check, 350);", "setTimeout(check, 250);")
    announce = announce.replace("attempts >= 45", "attempts >= 20")
    announce = announce.replace("خلال 45 ثانية", "خلال 5 ثوانٍ")
    announce = announce.replace("within 45 seconds", "within 5 seconds")

# Flask marker: no API schema change required, but keep deployment traceable.
if "GP_ANNOUNCE_AND_MOTION_V4" not in flask:
    flask = flask.replace("app = Flask(__name__)\n", "app = Flask(__name__)\n\n# GP_ANNOUNCE_AND_MOTION_V4\n", 1)

tools_path.write_text(tools, encoding="utf-8")
flask_path.write_text(flask, encoding="utf-8")
tv_path.write_text(tv, encoding="utf-8")
announce_path.write_text(announce, encoding="utf-8")
print("Applied V4: 5s ACK, TV police alert, RTL order, toolbar fullscreen, real camera motion voice, announce page")
