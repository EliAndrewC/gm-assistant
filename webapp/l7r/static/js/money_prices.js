// The price sheets' filter (feature 225): hide items whose text lacks any word typed, and a sheet
// with none left. Without this script every sheet shows in full.
(function () {
  'use strict';

  function init() {
    var box = document.querySelector('[data-filter]');
    if (!box) return;
    // Each sheet's heading sticks just under the app nav, whose height varies by width.
    var nav = document.querySelector('.app-nav');
    function navHeight() {
      document.documentElement.style.setProperty('--prices-nav-h', (nav ? nav.offsetHeight : 0) + 'px');
    }
    navHeight();
    window.addEventListener('resize', navHeight);
    var sheets = Array.prototype.slice.call(document.querySelectorAll('[data-sheet]'));
    var none = document.querySelector('[data-none]');
    box.addEventListener('input', function () {
      var words = box.value.toLowerCase().split(/\s+/).filter(Boolean);
      var shown = 0;
      sheets.forEach(function (sheet) {
        var any = false;
        sheet.querySelectorAll('[data-item]').forEach(function (item) {
          var hit = words.every(function (w) { return item.dataset.text.indexOf(w) >= 0; });
          item.hidden = !hit;
          if (hit) any = true;
        });
        sheet.hidden = !any;
        if (any) shown++;
      });
      none.hidden = shown > 0;
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
