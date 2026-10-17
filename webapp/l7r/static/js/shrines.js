/* =========================================================================
   Shrine builder (/shrines, feature 216)
   - A wizard: one step (decision) on screen at a time, Back / Next, steps for
     categories that do not apply are skipped. The current step rides in the
     address bar's #hash; the share link never carries it, so a shared link
     opens on the first step (the GM's view opens on the summary).
   - Player: every change rewrites the address bar and the share link from the
     form (disabled = moot categories are left out) and the summary list.
   - GM: every change resubmits the form so the server recomputes the ledger,
     returning to the same step.
   Nothing here knows a price - the GM ledger is rendered by the server.
   Without this script every step shows at once and the form still works.
   ========================================================================= */

(function () {
  'use strict';

  var SCROLL_KEY = 'l7r-shrines-scroll';

  function init() {
    var form = document.getElementById('shrine-form');
    var wizard = document.querySelector('[data-wizard]');
    if (!form || !wizard) return;
    var isGm = form.dataset.gm === 'true';
    var share = document.getElementById('shrine-share-url');
    var steps = Array.prototype.slice.call(wizard.querySelectorAll('.wizard-step'));
    var backBtn = wizard.querySelector('[data-back]');
    var nextBtn = wizard.querySelector('[data-next]');
    var current = null;
    // History depth of the current entry: every Next or summary jump pushes one entry, so the
    // browser's Back has somewhere to go inside the wizard (FR-024).
    var depth = 0;

    document.documentElement.classList.add('js-wizard');

    function stepByKey(key) {
      for (var i = 0; i < steps.length; i++) if (steps[i].dataset.step === key) return steps[i];
      return null;
    }

    function applies(step) {
      var fs = step.querySelector('fieldset.shrine-cat');
      return !fs || !fs.disabled;
    }

    function live() { return steps.filter(applies); }

    function applyMoot() {
      var voided = {};
      form.querySelectorAll('input[type=radio][data-voids]:checked').forEach(function (input) {
        if (input.closest('fieldset.is-moot')) return;
        input.dataset.voids.split(' ').forEach(function (key) { voided[key] = true; });
      });
      // `only_with`: a category that applies only when another has one of the listed options.
      form.querySelectorAll('fieldset[data-only-with]').forEach(function (fs) {
        var parts = fs.dataset.onlyWith.split(':');
        var picked = form.querySelector('fieldset[data-cat="' + parts[0] + '"]:not(:disabled) input:checked');
        if (!picked || parts[1].split('|').indexOf(picked.value) < 0) voided[fs.dataset.cat] = true;
      });
      form.querySelectorAll('fieldset.shrine-cat').forEach(function (fs) {
        var moot = !!voided[fs.dataset.cat];
        fs.classList.toggle('is-moot', moot);
        fs.disabled = moot;
      });
      // FR-036: an option that needs an earlier choice is hidden (and unpicked) without it.
      form.querySelectorAll('.shrine-opt[data-needs]').forEach(function (card) {
        var need = card.dataset.needs.split(':');
        var have = form.querySelector('fieldset[data-cat="' + need[0] + '"]:not(:disabled) input:checked');
        var ok = !!have && need[1].split('|').indexOf(have.value) >= 0;
        var input = card.querySelector('input');
        card.classList.toggle('is-unavailable', !ok);
        input.disabled = !ok;
        if (!ok) input.checked = false;
      });
      // FR-030: switch to the no-kami wording when the remains are the heart of the shrine.
      if (form.dataset.altWhen) {
        var cond = form.dataset.altWhen.split(':');
        var pick = form.querySelector('fieldset[data-cat="' + cond[0] + '"]:not(:disabled) input:checked');
        form.classList.toggle('is-alt', !!pick && cond[1].split('|').indexOf(pick.value) >= 0);
      }
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

    function fitBox(box) {
      if (!box) return;
      box.style.height = 'auto';
      box.style.height = box.scrollHeight + 2 + 'px';
    }

    function fitShare() {
      fitBox(share);
      fitBox(form.querySelector('[data-one-line]'));
    }

    function syncSummary() {
      var list = wizard.querySelector('[data-summary]');
      if (list) {
        list.innerHTML = '';
        form.querySelectorAll('fieldset.shrine-cat:not(:disabled)').forEach(function (fs) {
          var checked = fs.querySelector('input[type=radio]:checked');
          var li = document.createElement('li');
          var a = document.createElement('a');
          a.href = '#shrine-step-' + fs.dataset.cat;
          a.dataset.goto = fs.dataset.cat;
          var label = document.createElement('span');
          label.textContent = fs.querySelector('.shrine-cat__label').textContent;
          a.appendChild(label);
          a.appendChild(document.createTextNode(' '));
          var answer = document.createElement('em');
          if (checked) {
            answer.textContent = checked.closest('.shrine-opt').querySelector('.shrine-opt__title').textContent;
          } else {
            answer.textContent = 'not chosen yet';
            answer.className = 'is-open';
          }
          a.appendChild(answer);
          li.appendChild(a);
          list.appendChild(li);
        });
      }
      var open = list ? list.querySelectorAll('.is-open').length : 0;
      var note = wizard.querySelector('[data-open-note]');
      if (note) {
        note.hidden = open === 0;
        note.querySelector('[data-open-count]').textContent =
          open + ' choice' + (open === 1 ? '' : 's') + ' still open.';
      }
      var echo = wizard.querySelector('[data-name-echo]');
      var name = form.querySelector('[name=shrine_name]');
      if (echo && name) echo.textContent = name.value.trim() || 'Your shrine';
    }

    function urlFor(step) {
      var hash = step ? '#step-' + step.dataset.step : '';
      if (isGm) return window.location.pathname + window.location.search + hash;
      return share.dataset.base + '?' + designQuery() + hash;
    }

    function writeAddress() {
      if (share) share.value = window.location.origin + share.dataset.base + '?' + designQuery();
      history.replaceState({ step: current ? current.dataset.step : null, depth: depth }, '', urlFor(current));
    }

    // FR-023: a fresh random order every time a step is shown, so position biases no choice.
    function shuffle(step) {
      var grid = step.querySelector('.shrine-opts');
      if (!grid) return;
      var cards = Array.prototype.slice.call(grid.children);
      for (var i = cards.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var t = cards[i]; cards[i] = cards[j]; cards[j] = t;
      }
      cards.forEach(function (card) { grid.appendChild(card); });
    }

    function show(step, scroll) {
      if (!step || !applies(step)) return;
      if (step !== current) shuffle(step);
      current = step;
      steps.forEach(function (s) { s.classList.toggle('is-current', s === step); });
      var list = live();
      var index = list.indexOf(step);
      wizard.querySelector('[data-chapter-label]').textContent = step.dataset.chapter;
      // Count only steps an actual choice removed; form-specific steps (data-only-with) that are not
      // in play are simply absent, so step 1 never claims something was already skipped.
      var skipped = steps.filter(function (s) {
        var fs = s.querySelector('fieldset.shrine-cat');
        return fs && fs.disabled && !fs.dataset.onlyWith;
      }).length;
      var total = list.length;
      wizard.querySelector('[data-count]').textContent = 'Step ' + (index + 1) + ' of ' + total +
        (skipped ? ' \u00b7 ' + skipped + ' skipped' : '');
      document.documentElement.classList.toggle('wizard-deep', step.dataset.step !== 'name');
      wizard.querySelector('[data-bar]').style.width = ((index + 1) / list.length * 100) + '%';
      backBtn.style.visibility = index > 0 ? 'visible' : 'hidden';
      var last = index === list.length - 1;
      nextBtn.hidden = last;
      gateNext();
      nextBtn.textContent = index === list.length - 2 ? 'See your shrine' : 'Next';
      if (step.dataset.step === 'review') { syncSummary(); fitShare(); }
      writeAddress();
      if (scroll) wizard.scrollIntoView({ block: 'start' });
    }

    // Next waits for a choice: nothing is pre-selected, and skipping past a step unchosen would
    // leave a hole in the design. (The summary's "change" links still jump anywhere.)
    function gateNext() {
      if (!current) return;
      var fs = current.querySelector('fieldset.shrine-cat');
      var open = fs && !fs.disabled && !fs.querySelector('input[type=radio]:checked');
      nextBtn.disabled = !!open;
      wizard.querySelector('[data-hint]').hidden = !open;
    }

    function neighbor(step, delta) {
      var list = live();
      var index = list.indexOf(step) + delta;
      return index >= 0 && index < list.length ? list[index] : null;
    }

    // Forward moves (Next, a summary jump) push a history entry.
    function advance(step) {
      if (!step || !applies(step)) return;
      depth += 1;
      history.pushState({ step: step.dataset.step, depth: depth }, '', urlFor(step));
      show(step, true);
    }

    // The wizard's Back goes to the previous step that applies. When there is a wizard entry behind
    // this one it does so THROUGH the browser history, so the two Backs stay one and the same; the
    // popstate handler below does the actual move.
    function back() {
      var prev = neighbor(current, -1);
      if (!prev) return;
      if (depth > 0) {
        history.back();
      } else {
        show(prev, true);
      }
    }

    // FR-024: the browser's Back does exactly what the wizard's Back does - the previous step that
    // applies (not merely the last page visited, which after a summary jump would differ). Forward
    // restores the step that entry recorded.
    window.addEventListener('popstate', function (event) {
      var state = event.state;
      if (!state || typeof state.depth !== 'number') return;
      var target;
      if (state.depth < depth) {
        target = neighbor(current, -1) || stepByKey(state.step);
      } else {
        target = stepByKey(state.step);
        if (!target || !applies(target)) target = neighbor(current, 1) || current;
      }
      depth = state.depth;
      show(target, true);
    });

    backBtn.addEventListener('click', back);
    nextBtn.addEventListener('click', function () { advance(neighbor(current, 1)); });

    wizard.addEventListener('click', function (event) {
      var link = event.target.closest('[data-goto]');
      if (!link) return;
      event.preventDefault();
      advance(stepByKey(link.dataset.goto));
    });

    form.addEventListener('change', function () {
      if (isGm) {
        try { sessionStorage.setItem(SCROLL_KEY, String(window.scrollY)); } catch (e) { /* ignore */ }
        form.action = '/shrines' + (current ? '#step-' + current.dataset.step : '');
        form.submit();
        return;
      }
      applyMoot();
      syncSummary();
      writeAddress();
      gateNext();
      if (current) {
        // Re-count: choosing a form can change how many steps apply.
        show(current, false);
      }
    });
    form.addEventListener('input', function (event) {
      if (event.target.matches('[data-one-line]')) fitBox(event.target);
      if (!isGm && event.target.matches('[name=shrine_name]')) { syncSummary(); writeAddress(); }
    });
    // The name box wraps but is one line: Enter moves on instead of breaking it.
    var nameBox = form.querySelector('[data-one-line]');
    if (nameBox) {
      nameBox.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (isGm) form.requestSubmit(); else advance(neighbor(current, 1));
        }
      });
    }

    form.addEventListener('submit', function (event) {
      if (!isGm) {
        // Enter in the name field means "next", not "reload".
        event.preventDefault();
        advance(neighbor(current, 1));
        return;
      }
      try { sessionStorage.setItem(SCROLL_KEY, String(window.scrollY)); } catch (e) { /* ignore */ }
      form.action = '/shrines' + (current ? '#step-' + current.dataset.step : '');
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

    var fromHash = window.location.hash.indexOf('#step-') === 0
      ? stepByKey(window.location.hash.slice('#step-'.length)) : null;
    var first = (fromHash && applies(fromHash)) ? fromHash : stepByKey(isGm ? 'review' : 'name');
    // A #step-... link would make the browser scroll to that section and tuck its question under
    // the sticky nav (seen on mobile); land on the wizard's top instead.
    show(first, !!fromHash);

    // The one-line "Tadashi keeps" pin shows only once the full totals box has scrolled away.
    var totals = document.querySelector('.shrine-totals');
    var ledger = document.querySelector('.shrine-ledger');
    if (totals && ledger && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        ledger.classList.toggle('totals-hidden', !entries[0].isIntersecting);
      }, { rootMargin: '-60px 0px 0px 0px' }).observe(totals);
    }

    try {
      var saved = sessionStorage.getItem(SCROLL_KEY);
      if (saved !== null) {
        sessionStorage.removeItem(SCROLL_KEY);
        window.scrollTo(0, parseInt(saved, 10) || 0);
      }
    } catch (e) { /* storage unavailable: no scroll restore */ }

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
