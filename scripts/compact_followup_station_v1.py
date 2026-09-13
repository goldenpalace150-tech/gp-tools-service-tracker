from pathlib import Path

path = Path('templates/tv.html')
text = path.read_text(encoding='utf-8')
marker = 'GP_COMPACT_FOLLOWUP_STATION_V1'
if marker in text:
    print('compact follow-up station already applied')
    raise SystemExit(0)

style = r'''
    <!-- GP_COMPACT_FOLLOWUP_STATION_V1 -->
    <style id="gp-compact-followup-station-v1">
      /* The follow-up station is a status strip on the main TV, not the
         primary content. Compact it on kiosk-height screens so the six
         workflow cards get the vertical space and their labels never fight
         the large counts. */
      @media (min-width:901px) and (max-height:1000px) {
        body.main-view-body .followup-station {
          min-height:132px !important;
          height:132px !important;
          margin:5px 0 7px !important;
          border-radius:15px !important;
        }
        body.main-view-body .followup-station-head {
          height:35px !important;
          padding:5px 12px !important;
          gap:9px !important;
        }
        body.main-view-body .followup-station-title {
          gap:6px !important;
          font-size:13px !important;
          font-size:clamp(12px,.85vw,15px) !important;
        }
        body.main-view-body .followup-live-dot {
          width:7px !important;
          height:7px !important;
          box-shadow:0 0 0 3px rgba(34,197,94,.10) !important;
        }
        body.main-view-body .followup-station-counts { gap:4px !important; }
        body.main-view-body .followup-kpi {
          gap:4px !important;
          padding:3px 7px !important;
          font-size:10px !important;
          font-size:clamp(9px,.66vw,11px) !important;
        }
        body.main-view-body .followup-kpi b {
          font-size:12px !important;
          font-size:clamp(11px,.78vw,14px) !important;
        }
        body.main-view-body .followup-slide {
          height:95px !important;
          padding:6px 14px 9px !important;
          grid-template-columns:minmax(0,1.65fr) minmax(270px,.75fr) !important;
          gap:10px !important;
        }
        body.main-view-body .followup-slide-top {
          gap:6px !important;
          margin-bottom:2px !important;
        }
        body.main-view-body .followup-category-badge {
          padding:2px 7px !important;
          font-size:10px !important;
          font-size:clamp(9px,.66vw,11px) !important;
        }
        body.main-view-body .followup-slide-position { font-size:10px !important; }
        body.main-view-body .followup-slide-title {
          font-size:21px !important;
          font-size:clamp(17px,1.28vw,23px) !important;
          line-height:1.04 !important;
        }
        body.main-view-body .followup-slide-brief {
          margin-top:3px !important;
          font-size:14px !important;
          font-size:clamp(12px,.88vw,16px) !important;
          line-height:1.18 !important;
          -webkit-line-clamp:1 !important;
        }
        body.main-view-body .followup-slide-meta {
          gap:4px !important;
        }
        body.main-view-body .followup-slide-meta .meta-box {
          border-radius:8px !important;
          padding:4px 6px !important;
        }
        body.main-view-body .followup-slide-meta small {
          font-size:8px !important;
          margin-bottom:1px !important;
        }
        body.main-view-body .followup-slide-meta strong {
          font-size:11px !important;
          font-size:clamp(10px,.7vw,12px) !important;
        }
        body.main-view-body .followup-slide-progress { height:3px !important; }
      }

      @media (min-width:901px) and (max-height:800px) {
        body.main-view-body .followup-station {
          min-height:108px !important;
          height:108px !important;
          margin:4px 0 6px !important;
        }
        body.main-view-body .followup-station-head {
          height:30px !important;
          padding:3px 10px !important;
        }
        body.main-view-body .followup-station-title {
          font-size:12px !important;
        }
        body.main-view-body .followup-kpi {
          padding:2px 6px !important;
          font-size:9px !important;
        }
        body.main-view-body .followup-kpi b { font-size:11px !important; }
        body.main-view-body .followup-slide {
          height:76px !important;
          padding:4px 12px 7px !important;
          grid-template-columns:minmax(0,1.8fr) minmax(235px,.65fr) !important;
          gap:8px !important;
        }
        body.main-view-body .followup-slide-title {
          font-size:18px !important;
        }
        body.main-view-body .followup-slide-brief {
          font-size:12px !important;
          margin-top:2px !important;
        }
        body.main-view-body .followup-slide-meta .meta-box { padding:3px 5px !important; }
        body.main-view-body .followup-slide-meta small { display:none !important; }
        body.main-view-body .followup-slide-meta strong { font-size:10px !important; }
      }
    </style>
'''

if '</head>' not in text:
    raise SystemExit('Missing </head> in templates/tv.html')
text = text.replace('</head>', style + '\n</head>', 1)
path.write_text(text, encoding='utf-8')
print('Applied compact follow-up station CSS')
