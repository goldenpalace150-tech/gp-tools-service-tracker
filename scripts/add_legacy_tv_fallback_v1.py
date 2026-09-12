from pathlib import Path

path = Path('templates/tv.html')
text = path.read_text(encoding='utf-8')
marker = 'GP_LEGACY_TV_FALLBACK_V1'
if marker in text:
    print('legacy TV fallback already applied')
    raise SystemExit(0)

legacy_css = r'''
    <!-- GP_LEGACY_TV_FALLBACK_V1 -->
    <style id="gpLegacyTvCompatV1">
      html.gp-legacy-tv, html.gp-legacy-tv body { background:#f3f5f8 !important; color:#172033 !important; }
      html.gp-legacy-tv body { font-family:Arial,Tahoma,sans-serif !important; }
      html.gp-legacy-tv .topbar { background:#071a2d !important; color:#ffffff !important; border-color:#20364d !important; }
      html.gp-legacy-tv .brand h1, html.gp-legacy-tv .brand small { color:#ffffff !important; }
      html.gp-legacy-tv .brand h1 { font-size:28px !important; }
      html.gp-legacy-tv .brand small { font-size:13px !important; }
      html.gp-legacy-tv .status-chip, html.gp-legacy-tv .pill, html.gp-legacy-tv .action-btn, html.gp-legacy-tv .language-select, html.gp-legacy-tv .voice-btn { background:#102a45 !important; color:#ffffff !important; border-color:#42627f !important; }
      html.gp-legacy-tv .summary-item { background:#ffffff !important; color:#172033 !important; border-color:#d9e0e8 !important; }
      html.gp-legacy-tv .summary-item span { color:#475569 !important; }
      html.gp-legacy-tv .workflow-card { background:#ffffff !important; color:#172033 !important; border-color:#d9e0e8 !important; }
      html.gp-legacy-tv .workflow-card h2 { color:#172033 !important; font-size:28px !important; }
      html.gp-legacy-tv .workflow-card p, html.gp-legacy-tv .workflow-card .open-hint { color:#475569 !important; }
      html.gp-legacy-tv .workflow-card .count { font-size:72px !important; color:#172033 !important; }
      html.gp-legacy-tv .workflow-card.progress .count { color:#2563eb !important; }
      html.gp-legacy-tv .workflow-card.collection .count { color:#7c3aed !important; }
      html.gp-legacy-tv .workflow-card.partner .count { color:#0f766e !important; }
      html.gp-legacy-tv .workflow-card.zero .count { color:#16a34a !important; }
      html.gp-legacy-tv .workflow-card.collected .count { color:#15803d !important; }
      html.gp-legacy-tv .workflow-card.partner_closed .count { color:#475569 !important; }
      html.gp-legacy-tv .followup-station, html.gp-legacy-tv .followup-slide { background:#071a2d !important; color:#ffffff !important; border-color:#20364d !important; }
      html.gp-legacy-tv .followup-station *, html.gp-legacy-tv .followup-slide * { color:#ffffff !important; }
      html.gp-legacy-tv .detail-toolbar, html.gp-legacy-tv .ticket-panel, html.gp-legacy-tv .stat, html.gp-legacy-tv .remark-row { background:#ffffff !important; color:#172033 !important; }
      html.gp-legacy-tv .toast { background:#071a2d !important; color:#ffffff !important; }
    </style>
'''

legacy_js = r'''
    <script id="gpLegacyTvFallbackV1">
    (function () {
      var legacy = false;
      try {
        if (!window.CSS || !window.CSS.supports || !window.CSS.supports('color', 'var(--gp-test)')) legacy = true;
      } catch (e) { legacy = true; }
      try { new Function('var x={a:1}; return x?.a;'); }
      catch (e2) { legacy = true; }
      if (!legacy) return;

      document.documentElement.className += ' gp-legacy-tv';
      var API = 'https://cqpmcqypwzlunskeeoml.supabase.co/functions/v1/gp-api/api/data';
      var lastData = null;

      function el(id) { return document.getElementById(id); }
      function setText(id, value) { var node = el(id); if (node) node.innerHTML = String(value == null ? '' : value); }
      function count(value) { var n = parseInt(value, 10); return isNaN(n) ? 0 : n; }
      function currentLang() { var s = el('languageSelect'); return s && s.value === 'ar' ? 'ar' : 'en'; }

      function applyLanguage() {
        var ar = currentLang() === 'ar';
        document.documentElement.dir = ar ? 'rtl' : 'ltr';
        document.documentElement.lang = ar ? 'ar' : 'en';
        setText('pageHeading', ar ? 'متابعة خدمة الورشة' : 'Service Workshop Tracker');
        setText('lastSync', ar ? 'بيانات مباشرة من Golden Palace' : 'Golden Palace live data');
        setText('urgentLabel', ar ? '🔥 عاجل' : '🔥 Urgent');
        setText('delayedLabel', ar ? '⚠️ متأخر' : '⚠️ Delayed');
        setText('title-progress', ar ? 'قيد المعالجة' : 'In Repair');
        setText('desc-progress', ar ? 'الأجهزة الموجودة ضمن دورة صيانة فعالة.' : 'Tools currently in an active repair cycle.');
        setText('title-collection', ar ? 'بانتظار الاستلام' : 'Waiting Collection');
        setText('desc-collection', ar ? 'جاهزة ومفوترة ولم يتم تأكيد الاستلام بعد.' : 'Ready and invoiced, waiting for physical collection.');
        setText('title-partner', ar ? 'مطالبة شريك' : 'Partner Claim');
        setText('desc-partner', ar ? 'حالات الشركاء التي ما زالت بانتظار التسوية.' : 'Partner cycles waiting for settlement.');
        setText('title-zero', ar ? 'فاتورة صفر — مغلق' : 'Zero Invoice Closed');
        setText('desc-zero', ar ? 'فاتورة المبيع تساوي صفراً وأغلقت الدورة.' : 'Sales invoice is zero and the cycle is closed.');
        setText('title-collected', ar ? 'تم الاستلام' : 'Collected');
        setText('desc-collected', ar ? 'تم تأكيد استلام الزبون.' : 'Customer collection was confirmed.');
        setText('title-partner_closed', ar ? 'تسوية / صيانة' : 'Settled / Maintenance');
        setText('desc-partner_closed', ar ? 'تم تسجيل تسوية الشريك أو الإغلاق المالي.' : 'Partner settlement or maintenance closure recorded.');
      }

      function render(data) {
        if (!data) return;
        lastData = data;
        setText('count-progress', count(data.progress_count));
        setText('count-collection', count(data.collection_count));
        setText('count-partner', count(data.partner_count));
        setText('count-zero', count(data.zero_count));
        setText('count-collected', count(data.collected_count));
        setText('count-partner_closed', count(data.partner_closed_count));
        setText('urgentCount', count(data.urgent_count));
        setText('delayedCount', count(data.delayed_count));
        setText('remarksCount', data.remarks_list && data.remarks_list.length ? data.remarks_list.length : 0);
        setText('followup-count-overdue', count(data.followup_overdue_count));
        setText('followup-count-today', count(data.followup_due_today_count));
        setText('followup-count-spares', count(data.followup_spare_parts_count));
        setText('followup-count-inquiries', count(data.followup_inquiry_count));
        var sync = el('syncPill');
        if (sync) { sync.innerHTML = currentLang() === 'ar' ? '🟢 البيانات متصلة' : '🟢 Data Live'; sync.style.color = '#ffffff'; }
        applyLanguage();
      }

      function showError(message) {
        var sync = el('syncPill');
        if (sync) { sync.innerHTML = currentLang() === 'ar' ? '🔴 فشل جلب البيانات' : '🔴 Data failed'; sync.style.color = '#ffffff'; }
        var last = el('lastSync');
        if (last) last.innerHTML = message || 'Data request failed';
      }

      function load() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', API + '?force=1&t=' + new Date().getTime(), true);
        xhr.onreadystatechange = function () {
          if (xhr.readyState !== 4) return;
          if (xhr.status >= 200 && xhr.status < 300) {
            try { render(JSON.parse(xhr.responseText)); }
            catch (e) { showError('Invalid data response'); }
          } else { showError('HTTP ' + xhr.status); }
        };
        xhr.onerror = function () { showError('Network error'); };
        try { xhr.send(null); } catch (e) { showError(String(e)); }
      }

      var select = el('languageSelect');
      if (select && select.addEventListener) select.addEventListener('change', function () { applyLanguage(); if (lastData) render(lastData); });
      applyLanguage();
      load();
      window.setInterval(load, 30000);
    })();
    </script>
'''

if '</head>' not in text or '</body>' not in text:
    raise SystemExit('Expected HTML closing tags not found')
text = text.replace('</head>', legacy_css + '\n</head>', 1)
text = text.replace('</body>', legacy_js + '\n</body>', 1)
path.write_text(text, encoding='utf-8')
print('applied legacy Smart TV fallback')
