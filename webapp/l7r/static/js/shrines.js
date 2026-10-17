/* =========================================================================
   Shrine builder (/shrines, feature 216)
   - Player: every change rewrites the address bar and the share link from the
     form (disabled = moot categories are left out), and marks moot categories.
   - GM: every change resubmits the form so the server recomputes the ledger;
     the scroll position is restored after the reload.
   Nothing here knows a price - the GM ledger is rendered by the server.
   ========================================================================= */

(function () {
  'use strict';

  var SCROLL_KEY = 'l7r-shrines-scroll';

  function init() {
    var form = document.getElementById('shrine-form');
    if (!form) return;
    var isGm = form.dataset.gm === 'true';
    var share = document.getElementById('shrine-share-url');

    try {
      var saved = sessionStorage.getItem(SCROLL_KEY);
      if (saved !== null) {
        sessionStorage.removeItem(SCROLL_KEY);
        window.scrollTo(0, parseInt(saved, 10) || 0);
      }
    } catch (e) { /* storage unavailable: no scroll restore */ }

    function applyMoot() {
      var voided = {};
      form.querySelectorAll('input[type=radio][data-voids]:checked').forEach(function (input) {
        if (input.closest('fieldset.is-moot')) return;
        input.dataset.voids.split(' ').forEach(function (key) { voided[key] = true; });
      });
      form.querySelectorAll('fieldset.shrine-cat').forEach(function (fs) {
        var moot = !!voided[fs.dataset.cat];
        fs.classList.toggle('is-moot', moot);
        fs.disabled = moot;
        var note = fs.querySelector('[data-moot-note]');
        if (note) note.textContent = 'Does not apply with the choices above.';
      });
    }

    function designQuery() {
      var params = new URLSearchParams();
      new FormData(form).forEach(function (value, key) {
        if (key.indexOf('gm_') === 0) return;
        if (typeof value === 'string' && value.trim() === '') return;
        params.append(key, typeof value === 'string' ? value.trim() : value);
      });
      return params.toString();
    }

    function fitShare() {
      if (!share) return;
      share.style.height = 'auto';
      share.style.height = share.scrollHeight + 2 + 'px';
    }

    function syncSummary() {
      var list = document.querySelector('[data-summary]');
      if (!list) return;
      list.innerHTML = '';
      form.querySelectorAll('fieldset.shrine-cat:not(:disabled)').forEach(function (fs) {
        var checked = fs.querySelector('input[type=radio]:checked');
        if (!checked) return;
        var li = document.createElement('li');
        var label = document.createElement('span');
        label.textContent = fs.querySelector('.shrine-cat__label').textContent;
        li.appendChild(label);
        li.appendChild(document.createTextNode(' ' + checked.closest('.shrine-opt').querySelector('.shrine-opt__title').textContent));
        list.appendChild(li);
      });
    }

    function sync() {
      applyMoot();
      var query = designQuery();
      if (share) share.value = window.location.origin + share.dataset.base + '?' + query;
      if (!isGm) history.replaceState(null, '', share.dataset.base + '?' + query);
      syncSummary();
      fitShare();
    }

    form.addEventListener('change', function () {
      if (isGm) {
        try { sessionStorage.setItem(SCROLL_KEY, String(window.scrollY)); } catch (e) { /* ignore */ }
        form.submit();
        return;
      }
      sync();
    });
    form.addEventListener('input', function (event) {
      if (!isGm && event.target.matches('input[type=text], textarea')) sync();
    });
    form.addEventListener('submit', function () {
      try { sessionStorage.setItem(SCROLL_KEY, String(window.scrollY)); } catch (e) { /* ignore */ }
    });

    document.querySelectorAll('[data-copy]').forEach(function (button) {
      button.addEventListener('click', function () {
        var target = document.querySelector(button.dataset.copy);
        if (!target) return;
        var done = function () {
          var label = button.textContent;
          button.textContent = 'Copied';
          setTimeout(function () { button.textContent = label; }, 1600);
        };
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(target.value).then(done, function () { target.select(); });
        } else {
          target.select();
          try { document.execCommand('copy'); done(); } catch (e) { /* leave it selected */ }
        }
      });
    });

    if (share) share.value = window.location.origin + share.dataset.base + '?' + designQuery();
    fitShare();
    window.addEventListener('resize', fitShare);
    window.addEventListener('load', fitShare);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitShare);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
