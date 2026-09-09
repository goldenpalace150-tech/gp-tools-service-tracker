from pathlib import Path
import re

TV = Path('templates/tv.html')
FLASK = Path('flask_app.py')
tv = TV.read_text(encoding='utf-8')
flask = FLASK.read_text(encoding='utf-8')

STYLE_MARK = 'GP_FOLLOWUP_AUTO_SLIDES_V3'
VOICE_MARK = 'GP_FOLLOWUP_VOICE_V2'

if STYLE_MARK not in tv:
    css = r'''
    <!-- GP_FOLLOWUP_AUTO_SLIDES_V3 -->
    <style id="gp-followup-auto-slides-v3">
    .followup-station{position:relative;flex:0 0 auto;margin:8px 0 10px;min-height:184px;overflow:hidden;border:1px solid #315472;border-radius:18px;background:linear-gradient(135deg,#071a2d,#0b2741 58%,#102f4b);box-shadow:0 10px 30px rgba(0,0,0,.20);color:#f8fafc;direction:ltr}
    body.lang-ar .followup-station{direction:rtl}.followup-station::before{content:"";position:absolute;inset:0 auto 0 0;width:5px;background:#d5a62e;z-index:2}body.lang-ar .followup-station::before{left:auto;right:0}
    .followup-station-head{height:44px;padding:7px 14px 6px 17px;display:flex;align-items:center;justify-content:space-between;gap:14px;border-bottom:1px solid rgba(148,163,184,.18)}body.lang-ar .followup-station-head{padding:7px 17px 6px 14px}
    .followup-station-title{display:flex;align-items:center;gap:8px;font-weight:950;font-size:clamp(14px,1.05vw,19px);white-space:nowrap}.followup-live-dot{width:9px;height:9px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 5px rgba(34,197,94,.10)}
    .followup-station-counts{display:flex;align-items:center;gap:6px;min-width:0;overflow:hidden}.followup-kpi{display:inline-flex;align-items:center;gap:5px;border:1px solid #315472;background:rgba(8,31,51,.76);border-radius:999px;padding:4px 8px;color:#dbe7f2;font-size:clamp(10px,.75vw,13px);font-weight:800;white-space:nowrap}.followup-kpi b{font-size:clamp(13px,.95vw,17px);color:#f4bd2d}.followup-kpi.overdue b{color:#ff7078}.followup-kpi.today b{color:#ffc553}
    .followup-slide{position:relative;width:100%;height:140px;border:0;background:transparent;color:inherit;padding:10px 17px 13px;display:grid;grid-template-columns:minmax(0,1.55fr) minmax(360px,.95fr);gap:18px;text-align:left;cursor:pointer}body.lang-ar .followup-slide{text-align:right}.followup-slide:hover{background:rgba(255,255,255,.025)}
    .followup-slide-main{min-width:0;display:flex;flex-direction:column;justify-content:center}.followup-slide-top{display:flex;align-items:center;gap:8px;min-width:0;margin-bottom:5px}.followup-category-badge{display:inline-flex;align-items:center;border-radius:999px;padding:4px 9px;border:1px solid #466581;background:#102d47;font-size:clamp(10px,.75vw,13px);font-weight:900;white-space:nowrap}.followup-slide-position{color:#9fb4c8;font-size:12px;font-weight:800;white-space:nowrap}
    .followup-slide-title{font-size:clamp(21px,1.75vw,31px);line-height:1.08;font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff}.followup-slide-brief{margin-top:6px;font-size:clamp(15px,1.18vw,21px);line-height:1.32;font-weight:750;color:#dbe7f2;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    .followup-slide-meta{display:grid;grid-template-columns:1fr 1fr;gap:7px 8px;align-content:center}.followup-slide-meta .meta-box{min-width:0;border:1px solid rgba(112,145,174,.28);border-radius:10px;background:rgba(5,24,41,.48);padding:7px 9px}.followup-slide-meta small{display:block;color:#91a9be;font-size:10px;font-weight:800;margin-bottom:2px;text-transform:uppercase;letter-spacing:.03em}.followup-slide-meta strong{display:block;color:#f8fafc;font-size:clamp(12px,.85vw,15px);font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .followup-slide-progress{position:absolute;left:0;right:0;bottom:0;height:4px;background:rgba(255,255,255,.07);overflow:hidden}.followup-slide-progress span{display:block;height:100%;width:100%;transform-origin:left center;background:linear-gradient(90deg,#d5a62e,#f1d16c);animation:gp-followup-slide-progress 18s linear forwards}body.lang-ar .followup-slide-progress span{transform-origin:right center}
    .followup-station.cat-overdue{border-color:#8f3239}.followup-station.cat-overdue .followup-category-badge{border-color:#9b4148;background:#351a22;color:#ffb2b7}.followup-station.cat-today{border-color:#8a6416}.followup-station.cat-today .followup-category-badge{border-color:#947024;background:#342711;color:#ffd784}.followup-station.cat-spares{border-color:#7b6826}.followup-station.cat-spares .followup-category-badge{border-color:#87732d;background:#312b14;color:#f3db7a}.followup-station.cat-inquiries{border-color:#316c96}.followup-station.cat-inquiries .followup-category-badge{border-color:#397ba9;background:#102c43;color:#9bd5ff}.followup-station.empty .followup-slide{grid-template-columns:1fr}.followup-station.empty .followup-slide-meta{display:none}
    @keyframes gp-followup-slide-progress{from{transform:scaleX(0)}to{transform:scaleX(1)}}
    @media(max-width:1100px){.followup-station{min-height:174px}.followup-slide{height:130px;grid-template-columns:minmax(0,1.4fr) minmax(300px,.8fr);gap:10px}.followup-kpi span{display:none}}
    </style>
'''
    # Put the new style before the final head close, independent of older UI markers.
    if '</head>' not in tv:
        raise SystemExit('tv.html has no </head>')
    tv = tv.replace('</head>', css + '\n</head>', 1)

    station = r'''
        <section id="followupStation" class="followup-station empty" aria-label="Follow-up station">
          <div class="followup-station-head">
            <div class="followup-station-title"><span class="followup-live-dot"></span><span id="followupStationTitle">📌 Follow-Up Station</span></div>
            <div class="followup-station-counts">
              <span class="followup-kpi overdue"><span id="label-followup-overdue">🔴 Overdue</span><b id="followup-count-overdue">0</b></span>
              <span class="followup-kpi today"><span id="label-followup-today">🟠 Today</span><b id="followup-count-today">0</b></span>
              <span class="followup-kpi spares"><span id="label-followup-spares">🟡 Spares</span><b id="followup-count-spares">0</b></span>
              <span class="followup-kpi inquiries"><span id="label-followup-inquiries">🔵 Inquiries</span><b id="followup-count-inquiries">0</b></span>
            </div>
          </div>
          <button id="followupSlide" class="followup-slide" type="button">
            <div class="followup-slide-main">
              <div class="followup-slide-top"><span id="followupSlideCategory" class="followup-category-badge">Follow-Up</span><span id="followupSlidePosition" class="followup-slide-position"></span></div>
              <div id="followupSlideTitle" class="followup-slide-title">No follow-up cases waiting</div>
              <div id="followupSlideBrief" class="followup-slide-brief">New follow-up cases will appear here automatically.</div>
            </div>
            <div class="followup-slide-meta">
              <div class="meta-box"><small id="followupOwnerLabel">Owner</small><strong id="followupSlideOwner">—</strong></div>
              <div class="meta-box"><small id="followupWaitingLabel">Waiting on</small><strong id="followupSlideWaiting">—</strong></div>
              <div class="meta-box"><small id="followupDueLabel">Next follow-up</small><strong id="followupSlideDue">—</strong></div>
              <div class="meta-box"><small id="followupRelatedLabel">Related ID</small><strong id="followupSlideRelated">—</strong></div>
            </div>
            <div class="followup-slide-progress"><span id="followupSlideProgress"></span></div>
          </button>
        </section>'''
    pat = re.compile(r'<section class="followup-strip" aria-label="Follow-up queue">.*?</section>', re.S)
    tv, n = pat.subn(station.strip(), tv, count=1)
    if n != 1:
        raise SystemExit(f'old follow-up strip not found ({n})')

    js = r'''

    // GP_FOLLOWUP_AUTO_SLIDES_V3
    const GP_FOLLOWUP_SLIDE_MS=18000;
    let gpFollowupSlides=[],gpFollowupSlideIndex=0,gpFollowupSlideTimer=null,gpFollowupLastAnnouncement='',gpFollowupLastAnnouncementAt=0;
    const gpFuVal=(v,f='—')=>{const s=String(v==null?'':v).trim();return s||f};
    function gpFuMeta(c){const ar=currentLanguage==='ar',m={followup_overdue:{css:'overdue',label:ar?'🔴 متابعة متأخرة':'🔴 Overdue Follow-Up',spoken:ar?'متابعة متأخرة':'overdue follow-up'},followup_today:{css:'today',label:ar?'🟠 متابعة اليوم':'🟠 Due Today',spoken:ar?'متابعة مطلوبة اليوم':'follow-up due today'},followup_spares:{css:'spares',label:ar?'🟡 قطع غيار':'🟡 Spare Parts',spoken:ar?'متابعة قطع غيار':'spare parts follow-up'},followup_inquiries:{css:'inquiries',label:ar?'🔵 استفسار':'🔵 Inquiry',spoken:ar?'متابعة استفسار':'inquiry follow-up'}};return m[c]||m.followup_inquiries}
    function gpBuildFuSlides(data){const defs=[['followup_overdue','followup_overdue_list'],['followup_today','followup_due_today_list'],['followup_spares','followup_spare_parts_list'],['followup_inquiries','followup_inquiry_list']],out=[],seen=new Set();for(const [cat,key] of defs){for(const item of (Array.isArray(data?.[key])?data[key]:[])){const id=String(item.followup_id||`${item.related_id||''}|${item.title||''}|${item.next_followup||''}`);if(!id||seen.has(id))continue;seen.add(id);out.push({...item,_gpCategory:cat,_gpKey:id})}}return out}
    function gpFuSpeech(item,meta){const ar=currentLanguage==='ar',p=[meta.spoken],title=gpFuVal(item.title,''),action=gpFuVal(item.next_action,''),owner=gpFuVal(item.owner,''),waiting=gpFuVal(item.waiting_on,''),due=gpFuVal(item.next_followup,''),related=gpFuVal(item.related_id,''),days=Number(item.days_overdue||0);if(title)p.push(title);if(ar){if(action)p.push(`الخطوة الجاية: ${action}`);if(owner)p.push(`المسؤول: ${owner}`);if(waiting)p.push(`بانتظار: ${waiting}`);if(days>0)p.push(`متأخرة ${days} يوم`);else if(due)p.push(`موعد المتابعة: ${due}`);if(related)p.push(`الحالة المرتبطة: ${related}`)}else{if(action)p.push(`Next action: ${action}`);if(owner)p.push(`Owner: ${owner}`);if(waiting)p.push(`Waiting on: ${waiting}`);if(days>0)p.push(`${days} days overdue`);else if(due)p.push(`Next follow-up: ${due}`);if(related)p.push(`Related case: ${related}`)}return p.join('. ').replace(/\s+/g,' ').slice(0,430)}
    async function gpAnnounceFu(item,meta){if(!item||detailMode||!teamVoiceEnabled||document.hidden||teamVoicePlaying)return;const text=gpFuSpeech(item,meta),key=`${currentLanguage}|${item._gpKey}|${item.next_action||''}|${item.waiting_on||''}`;if(key===gpFollowupLastAnnouncement&&Date.now()-gpFollowupLastAnnouncementAt<120000)return;try{const r=await fetch(apiUrl(`/api/followup-voice?lang=${encodeURIComponent(currentLanguage)}&text=${encodeURIComponent(text)}`),{cache:'no-store'});if(!r.ok||teamVoicePlaying||document.hidden)return;const t=await r.json();if(!t.ok||!t.audio_url)return;stopTeamVoiceAudio();const a=new Audio(apiUrl(t.audio_url));a.preload='auto';a.volume=TEAM_VOICE_VOLUME;teamVoiceAudio=a;teamVoicePlaying=true;gpFollowupLastAnnouncement=key;gpFollowupLastAnnouncementAt=Date.now();setVoiceCaption(text,true);await new Promise((ok,bad)=>{a.addEventListener('ended',ok,{once:true});a.addEventListener('error',bad,{once:true});a.play().catch(bad)});teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false)}catch(_){teamVoiceAudio=null;teamVoicePlaying=false;setVoiceCaption('',false)}}
    function gpFuProgress(){const b=document.getElementById('followupSlideProgress');if(!b)return;b.style.animation='none';void b.offsetWidth;b.style.animation=''}
    function renderFollowupSlide(announce=false){const s=document.getElementById('followupStation'),btn=document.getElementById('followupSlide');if(!s||!btn)return;const ar=currentLanguage==='ar';document.getElementById('followupStationTitle').textContent=ar?'📌 محطة المتابعة':'📌 Follow-Up Station';document.getElementById('followupOwnerLabel').textContent=ar?'المسؤول':'Owner';document.getElementById('followupWaitingLabel').textContent=ar?'بانتظار':'Waiting on';document.getElementById('followupDueLabel').textContent=ar?'المتابعة القادمة':'Next follow-up';document.getElementById('followupRelatedLabel').textContent=ar?'الحالة المرتبطة':'Related ID';if(!gpFollowupSlides.length){s.className='followup-station empty';btn.dataset.category='';document.getElementById('followupSlideCategory').textContent=ar?'✅ لا يوجد متابعات':'✅ Follow-Up Clear';document.getElementById('followupSlidePosition').textContent='';document.getElementById('followupSlideTitle').textContent=ar?'لا يوجد حالات متابعة معلّقة':'No follow-up cases waiting';document.getElementById('followupSlideBrief').textContent=ar?'أي حالة جديدة رح تظهر هون تلقائياً.':'New follow-up cases will appear here automatically.';['followupSlideOwner','followupSlideWaiting','followupSlideDue','followupSlideRelated'].forEach(id=>document.getElementById(id).textContent='—');gpFuProgress();return}if(gpFollowupSlideIndex>=gpFollowupSlides.length)gpFollowupSlideIndex=0;const x=gpFollowupSlides[gpFollowupSlideIndex],m=gpFuMeta(x._gpCategory);s.className=`followup-station cat-${m.css}`;btn.dataset.category=x._gpCategory;document.getElementById('followupSlideCategory').textContent=m.label;document.getElementById('followupSlidePosition').textContent=`${gpFollowupSlideIndex+1} / ${gpFollowupSlides.length}`;document.getElementById('followupSlideTitle').textContent=gpFuVal(x.title,gpFuVal(x.related_id,gpFuVal(x.followup_id,ar?'حالة متابعة':'Follow-Up Case')));document.getElementById('followupSlideBrief').textContent=gpFuVal(x.next_action,gpFuVal(x.waiting_on,ar?'لا توجد خطوة تالية مسجلة':'No next action recorded'));document.getElementById('followupSlideOwner').textContent=gpFuVal(x.owner);document.getElementById('followupSlideWaiting').textContent=gpFuVal(x.waiting_on);document.getElementById('followupSlideDue').textContent=x.timing==='overdue'&&Number(x.days_overdue||0)>0?(ar?`متأخرة ${Number(x.days_overdue)} يوم`:`${Number(x.days_overdue)} days overdue`):gpFuVal(x.next_followup);document.getElementById('followupSlideRelated').textContent=gpFuVal(x.related_id,gpFuVal(x.followup_id));gpFuProgress();if(announce)setTimeout(()=>gpAnnounceFu(x,m),350)}
    function updateFollowupSlideshow(data){const old=gpFollowupSlides[gpFollowupSlideIndex]?._gpKey;gpFollowupSlides=gpBuildFuSlides(data);if(old){const i=gpFollowupSlides.findIndex(x=>x._gpKey===old);gpFollowupSlideIndex=i>=0?i:0}else if(gpFollowupSlideIndex>=gpFollowupSlides.length)gpFollowupSlideIndex=0;renderFollowupSlide(false);if(!gpFollowupSlideTimer){setTimeout(()=>renderFollowupSlide(true),900);gpFollowupSlideTimer=setInterval(()=>{if(detailMode||document.hidden||!gpFollowupSlides.length)return;gpFollowupSlideIndex=(gpFollowupSlideIndex+1)%gpFollowupSlides.length;renderFollowupSlide(true)},GP_FOLLOWUP_SLIDE_MS)}}
'''
    marker = re.search(r'\n\s*function updateMain\s*\(data\)\s*\{', tv)
    if not marker:
        raise SystemExit('updateMain not found')
    tv = tv[:marker.start()] + js + tv[marker.start():]

    # Hook slideshow into updateMain after the existing follow-up counters are updated.
    hook_pat = re.compile(r'(if\s*\(fuSpares\)[^\n]*followup_inquiry_count\);?[^\n]*\n)')
    tv, n = hook_pat.subn(r'\1        updateFollowupSlideshow(data);\n', tv, count=1)
    if n != 1:
        raise SystemExit('follow-up counter update hook not found')

    # Replace old mini-button listener if present; otherwise insert beside workflow listener.
    tv = re.sub(r"\n\s*document\.querySelectorAll\('\.followup-mini'\)[^\n]*", '', tv, count=1)
    listener = "\n    document.getElementById('followupSlide')?.addEventListener('click',e=>{const c=e.currentTarget.dataset.category;if(c)openCategory(c)});"
    wf = re.search(r"\n\s*document\.querySelectorAll\('\.workflow-card'\)[^\n]*", tv)
    if not wf:
        raise SystemExit('workflow-card listener not found')
    tv = tv[:wf.end()] + listener + tv[wf.end():]

if VOICE_MARK not in flask:
    route = r'''

# GP_FOLLOWUP_VOICE_V2
@app.route("/api/followup-voice")
def api_followup_voice():
    lang = "en" if str(request.args.get("lang", "ar")).lower().startswith("en") else "ar"
    text = re.sub(r"\s+", " ", str(request.args.get("text", ""))).strip()
    if not text:
        return jsonify({"ok": False, "error": "missing_text"}), 400
    text = text[:500]
    voice = GP_AR_VOICE if lang == "ar" else GP_EN_VOICE
    try:
        token, _ = gp_ensure_voice_file(text, voice, "-3%" if lang == "ar" else "-5%", "+1Hz")
    except Exception as exc:
        print("FollowUp voice generation error:", repr(exc))
        return jsonify({"ok": False, "error": "voice_generation_failed"}), 503
    return jsonify({"ok": True, "text": text, "lang": lang, "voice": voice, "audio_url": f"/api/voice-audio/{token}.mp3"})
'''
    marker = re.search(r'\n\s*@app\.route\("/api/voice-audio/<token>\.mp3"\)', flask)
    if not marker:
        raise SystemExit('voice-audio route not found')
    flask = flask[:marker.start()] + route + flask[marker.start():]

TV.write_text(tv, encoding='utf-8')
FLASK.write_text(flask, encoding='utf-8')
print('Follow-up TV slideshow patch applied')
