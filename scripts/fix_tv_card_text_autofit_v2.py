from pathlib import Path

path = Path('templates/tv.html')
text = path.read_text(encoding='utf-8')
marker = 'GP_TV_CARD_TEXT_AUTOFIT_V2'
if marker in text:
    print('TV card auto-fit v2 already applied')
    raise SystemExit(0)

style = r'''
    <!-- GP_TV_CARD_TEXT_AUTOFIT_V2 -->
    <style id="gp-tv-card-text-autofit-v2">
      /* Robust short-screen layout. Keep the number and Arabic/English title
         inside every card even on old Smart-TV browsers. */
      @media (max-height: 960px) and (min-width: 901px) {
        body.main-view-body .workflow-card,
        html.gp-legacy-tv body.main-view-body .workflow-card {
          position:relative !important;
          display:block !important;
          overflow:hidden !important;
          padding:0 !important;
          min-height:0 !important;
        }
        body.main-view-body .workflow-card p,
        html.gp-legacy-tv body.main-view-body .workflow-card p,
        body.main-view-body .workflow-card .open-hint,
        html.gp-legacy-tv body.main-view-body .workflow-card .open-hint {
          display:none !important;
        }
        body.main-view-body .workflow-card .icon,
        html.gp-legacy-tv body.main-view-body .workflow-card .icon {
          position:absolute !important;
          top:7px !important;
          right:11px !important;
          left:auto !important;
          margin:0 !important;
          color:#fff !important;
          font-size:29px !important;
          line-height:1 !important;
          z-index:3 !important;
        }
        body.main-view-body .workflow-card .count,
        html.gp-legacy-tv body.main-view-body .workflow-card .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.progress .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.collection .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.partner .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.zero .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.collected .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.partner_closed .count {
          position:absolute !important;
          top:29% !important;
          left:6px !important;
          right:6px !important;
          width:auto !important;
          margin:0 !important;
          color:#fff !important;
          font-size:54px !important;
          line-height:.92 !important;
          font-weight:950 !important;
          text-align:center !important;
          white-space:nowrap !important;
        }
        body.main-view-body .workflow-card h2,
        html.gp-legacy-tv body.main-view-body .workflow-card h2 {
          position:absolute !important;
          left:10px !important;
          right:10px !important;
          bottom:7px !important;
          width:auto !important;
          max-width:none !important;
          margin:0 !important;
          padding:0 !important;
          color:#fff !important;
          font-size:17px !important;
          line-height:1.05 !important;
          font-weight:900 !important;
          text-align:center !important;
          white-space:nowrap !important;
          overflow:hidden !important;
          text-overflow:ellipsis !important;
          direction:inherit !important;
        }
      }

      @media (max-height: 800px) and (min-width: 901px) {
        body.main-view-body .workflow-card .icon,
        html.gp-legacy-tv body.main-view-body .workflow-card .icon {
          top:5px !important;
          right:9px !important;
          font-size:25px !important;
        }
        body.main-view-body .workflow-card .count,
        html.gp-legacy-tv body.main-view-body .workflow-card .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.progress .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.collection .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.partner .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.zero .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.collected .count,
        html.gp-legacy-tv body.main-view-body .workflow-card.partner_closed .count {
          top:27% !important;
          font-size:44px !important;
        }
        body.main-view-body .workflow-card h2,
        html.gp-legacy-tv body.main-view-body .workflow-card h2 {
          bottom:5px !important;
          font-size:14px !important;
        }
      }

      /* Legacy TV color overrides had higher specificity than the main theme;
         keep all card text high-contrast on the colored tiles. */
      html.gp-legacy-tv body.main-view-body .workflow-card,
      html.gp-legacy-tv body.main-view-body .workflow-card h2,
      html.gp-legacy-tv body.main-view-body .workflow-card .count,
      html.gp-legacy-tv body.main-view-body .workflow-card .icon {
        color:#fff !important;
      }
    </style>
'''

if '</head>' not in text:
    raise SystemExit('Missing </head> in templates/tv.html')
text = text.replace('</head>', style + '\n</head>', 1)
path.write_text(text, encoding='utf-8')
print('Applied TV card auto-fit v2')
