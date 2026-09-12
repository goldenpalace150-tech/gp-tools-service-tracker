from pathlib import Path

path = Path('templates/tv.html')
text = path.read_text(encoding='utf-8')
marker = 'GP_TV_CARD_TEXT_AUTOFIT_V1'
if marker in text:
    print('TV card auto-fit already applied')
    raise SystemExit(0)

style = r'''
    <!-- GP_TV_CARD_TEXT_AUTOFIT_V1 -->
    <style id="gp-tv-card-text-autofit-v1">
      /* Keep workflow labels readable at every kiosk height. On shorter
         screens the number + title switch to one horizontal row instead
         of letting the title fall below the card. */
      body.main-view-body .workflow-card h2 {
        min-width:0 !important;
        overflow-wrap:break-word !important;
        word-break:normal !important;
      }

      /* Toolbar labels also scale down before they can collide. */
      body.main-view-body .top-actions .pill,
      body.main-view-body .top-actions .action-btn,
      body.main-view-body .top-actions .language-select,
      body.main-view-body .top-actions .status-chip {
        font-size:12px !important;
        font-size:clamp(11px,.78vw,14px) !important;
        padding:6px 9px !important;
        min-width:0 !important;
        white-space:nowrap !important;
      }

      @media (max-height: 960px) and (min-width: 901px) {
        body.main-view-body .workflow-card {
          display:flex !important;
          flex-direction:row !important;
          align-items:center !important;
          justify-content:center !important;
          padding:30px 18px 9px !important;
          overflow:hidden !important;
        }
        body.main-view-body .workflow-card .count {
          flex:0 0 auto !important;
          width:auto !important;
          margin:0 8px !important;
          line-height:.9 !important;
          white-space:nowrap !important;
          text-align:center !important;
          font-size:58px !important;
          font-size:clamp(44px,4.1vw,68px) !important;
        }
        body.main-view-body .workflow-card h2 {
          flex:1 1 auto !important;
          width:auto !important;
          max-width:none !important;
          margin:0 8px !important;
          line-height:1.08 !important;
          text-align:center !important;
          font-size:22px !important;
          font-size:clamp(17px,1.45vw,25px) !important;
        }
        body.main-view-body .workflow-card p {
          display:none !important;
        }
        body.main-view-body .workflow-card .icon {
          top:8px !important;
          right:14px !important;
          left:auto !important;
          line-height:1 !important;
          font-size:32px !important;
          font-size:clamp(28px,2.15vw,36px) !important;
        }
        body.lang-ar.main-view-body .workflow-card .icon {
          top:8px !important;
          right:14px !important;
          left:auto !important;
        }
        body.main-view-body .workflow-card .open-hint,
        body.lang-ar.main-view-body .workflow-card .open-hint {
          top:9px !important;
          bottom:auto !important;
          left:14px !important;
          right:auto !important;
          font-size:10px !important;
          font-size:clamp(9px,.68vw,11px) !important;
          white-space:nowrap !important;
        }
      }

      @media (max-height: 800px) and (min-width: 901px) {
        body.main-view-body .workflow-card {
          padding:25px 12px 7px !important;
        }
        body.main-view-body .workflow-card .count {
          font-size:50px !important;
          font-size:clamp(38px,3.7vw,58px) !important;
          margin:0 6px !important;
        }
        body.main-view-body .workflow-card h2 {
          font-size:19px !important;
          font-size:clamp(15px,1.25vw,21px) !important;
          margin:0 6px !important;
        }
        body.main-view-body .workflow-card .icon {
          font-size:28px !important;
        }
      }
    </style>
'''

if '</head>' not in text:
    raise SystemExit('Missing </head> in templates/tv.html')
text = text.replace('</head>', style + '\n</head>', 1)
path.write_text(text, encoding='utf-8')
print('Applied responsive workflow-card text auto-fit CSS')
