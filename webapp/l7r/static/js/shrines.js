/* =========================================================================
   Shrine builder (/shrines, feature 216)
   - A wizard: one step (decision) on screen at a time, Back / Next, steps for
     categories that do not apply are skipped. The current step rides in the
     address bar's #hash; the share link never carries it, so a shared link
     opens on the first step (the GM's view opens on the summary).
   - Player: every change rewrites the address bar and the share link from the
     form (disabled = moot categories are left out) and the summary list.
   - Ledger viewers (the GM, or a player whose character has Commerce, FR-048):
     every change resubmits the form so the server recomputes the ledger,
     returning to the same step.
   Nothing here knows a price - the ledger is rendered by the server.
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
    // A ledger on the page: changes go to the server, which reprices the design.
    var priced = form.dataset.priced === 'true';
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

    // The applicability rules (data/catalog.yaml `when`), sent by the server as JSON - conditions
    // only. resolve() is design.py's _resolve() in JavaScript: ONE forward pass in wizard order;
    // a step is in play if its rule holds against the choices already resolved, and a picked option
    // is kept only if its own rule holds. Every clause names an earlier step, so one pass is final.
    var rules = JSON.parse(document.getElementById('shrine-rules').textContent);

    // [key, options, negate]: an unchosen or not-in-play step is "no value" - a plain clause fails,
    // a negated one passes.
    function holds(clause, choices) {
      var present = clause[1].indexOf(choices[clause[0]]) >= 0;
      return clause[2] ? !present : present;
    }

    function resolve() {
      var choices = {};
      form.querySelectorAll('fieldset.shrine-cat').forEach(function (fs) {
        var key = fs.dataset.cat;
        var failing = (rules.categories[key] || []).filter(function (c) { return !holds(c, choices); })[0];
        fs.classList.toggle('is-moot', !!failing);
        fs.disabled = !!failing;
        if (failing) return;
        var optionRules = rules.options[key] || {};
        fs.querySelectorAll('input[type=radio], input[type=checkbox]').forEach(function (input) {
          var ok = (optionRules[input.value] || []).every(function (c) { return holds(c, choices); });
          input.closest('.shrine-opt-cell').classList.toggle('is-unavailable', !ok);
          input.disabled = !ok;
          if (!ok) input.checked = false;
        });
        var checked = fs.querySelector('input:checked');
        if (checked) choices[key] = checked.value;
      });
      // FR-030/FR-032/FR-037: the first named wording whose rule holds replaces the plain wording.
      var wording = 'plain';
      for (var w = 0; w < rules.wordings.length; w++) {
        if (rules.wordings[w][1].every(function (c) { return holds(c, choices); })) { wording = rules.wordings[w][0]; break; }
      }
      Array.prototype.slice.call(form.classList).forEach(function (cls) {
        if (cls.indexOf('wording-') === 0) form.classList.remove(cls);
      });
      form.classList.add('wording-' + wording);
    }

    // The text of an element as the current wording shows it (a hidden step's innerText would
    // run every wording's variant together).
    function shownText(el) {
      var m = form.className.match(/wording-([\w-]+)/);
      var variant = m ? el.querySelector('.w-' + m[1]) : null;
      return (variant || el).textContent.replace(/\s+/g, ' ').trim();
    }

    // FR-040: the same simulation as design.option_effects(). For each option on a step, resolve
    // the wizard with it picked and with the step unanswered; steps that only then appear and
    // later options only then offered are what it "makes possible"; the tag counts them (FR-041).
    var model = Array.prototype.map.call(form.querySelectorAll('fieldset.shrine-cat'), function (fs) {
      return {
        key: fs.dataset.cat,
        options: Array.prototype.map.call(fs.querySelectorAll('input[type=radio]'), function (i) { return i.value; })
      };
    });

    function evaluate(raw) {
      var choices = {};
      var inactive = {};
      model.forEach(function (st) {
        var failing = (rules.categories[st.key] || []).some(function (c) { return !holds(c, choices); });
        if (failing) { inactive[st.key] = true; return; }
        var v = raw[st.key];
        var oc = v === undefined ? null : ((rules.options[st.key] || {})[v] || []);
        if (oc && oc.every(function (c) { return holds(c, choices); })) choices[st.key] = v;
      });
      return { choices: choices, inactive: inactive };
    }

    function offeredSet(ev) {
      var out = {};
      model.forEach(function (st) {
        if (ev.inactive[st.key]) return;
        var orules = rules.options[st.key] || {};
        st.options.forEach(function (o) {
          if (orules[o] && orules[o].every(function (c) { return holds(c, ev.choices); })) out[st.key + '.' + o] = true;
        });
      });
      return out;
    }

    function currentRaw() {
      var raw = {};
      form.querySelectorAll('fieldset.shrine-cat:not(:disabled) input[type=radio]:checked').forEach(function (i) {
        raw[i.name] = i.value;
      });
      return raw;
    }

    function updateEffects(step) {
      var fs = step && step.querySelector('fieldset.shrine-cat');
      if (!fs) return;
      var key = fs.dataset.cat;
      var raw = currentRaw();
      delete raw[key];
      var base = evaluate(raw);
      var baseOffered = offeredSet(base);
      var keys = model.map(function (st) { return st.key; });
      var cells = fs.querySelectorAll('.shrine-opt-cell');
      var any = false;
      cells.forEach(function (cell) {
        var opt = cell.dataset.option;
        var trial = Object.assign({}, raw);
        trial[key] = opt;
        var ev = evaluate(trial);
        var made = keys.filter(function (k) { return base.inactive[k] && !ev.inactive[k]; }).map(function (k) {
          return shownText(form.querySelector('fieldset[data-cat="' + k + '"] .shrine-cat__label'));
        });
        var offered = offeredSet(ev);
        Object.keys(offered).forEach(function (k) {
          var parts = k.split('.');
          if (baseOffered[k] || base.inactive[parts[0]]) return;
          var title = form.querySelector('fieldset[data-cat="' + parts[0] + '"] .shrine-opt-cell[data-option="' + parts[1] + '"] .shrine-opt__title');
          made.push(shownText(title));
        });
        // counted as the header counts: the final summary step included
        var effect = cell.querySelector('[data-effect]');
        var has = made.length > 0;
        any = any || has;
        effect.classList.toggle('is-empty', !has);
        effect.tabIndex = has ? 0 : -1;
        // FR-041: count the choices that exist because of this option
        var steps = keys.filter(function (k) { return base.inactive[k] && !ev.inactive[k]; }).length;
        var n = steps || made.length;
        effect.querySelector('[data-effect-tag]').textContent = has ? n + ' custom choice' + (n === 1 ? '' : 's') : '';
        var tip = effect.querySelector('[data-effect-tip]');
        tip.innerHTML = '';
        if (has) {
          var b = document.createElement('b');
          b.textContent = 'Makes possible later:';
          tip.appendChild(b);
          tip.appendChild(document.createTextNode(' ' + made.join(', ')));
        }
      });
      fs.querySelectorAll('[data-effect]').forEach(function (e) { e.classList.toggle('is-none', !any); });
      trimSpacers(fs);
    }

    // An empty tag only keeps a row's cards lined up; in a row with no tag at all it is just a gap.
    function trimSpacers(fs) {
      var cells = Array.prototype.slice.call(fs.querySelectorAll('.shrine-opt-cell:not(.is-unavailable)'));
      cells.forEach(function (c) { c.querySelector('[data-effect]').classList.remove('is-row-free'); });
      var rows = {};
      cells.forEach(function (c) {
        var top = Math.round(c.getBoundingClientRect().top);
        (rows[top] = rows[top] || []).push(c);
      });
      Object.keys(rows).forEach(function (top) {
        var tagged = rows[top].some(function (c) { return !c.querySelector('[data-effect]').classList.contains('is-empty'); });
        if (!tagged) rows[top].forEach(function (c) { c.querySelector('[data-effect]').classList.add('is-row-free'); });
      });
    }

    // Keep a tooltip on screen: one that would run off the right edge opens right-aligned.
    function placeTip(host) {
      var tip = host.querySelector('[role=tooltip]');
      host.classList.remove('tip-right', 'tip-left');
      if (!tip) return;
      var width = document.documentElement.clientWidth;
      var r = tip.getBoundingClientRect();
      if (r.right > width - 8) host.classList.add('tip-right');
      else if (r.left < 8) host.classList.add('tip-left');
    }
    function tipHost(event) {
      return event.target.closest && event.target.closest('[data-effect], [data-gloss]');
    }
    form.addEventListener('mouseover', function (event) { var h = tipHost(event); if (h) placeTip(h); });
    form.addEventListener('focusin', function (event) { var h = tipHost(event); if (h) placeTip(h); });

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
          var picked = fs.querySelectorAll('input:checked');
          var checked = picked[0];
          var li = document.createElement('li');
          var a = document.createElement('a');
          a.href = '#shrine-step-' + fs.dataset.cat;
          a.dataset.goto = fs.dataset.cat;
          var label = document.createElement('span');
          label.textContent = shownText(fs.querySelector('.shrine-cat__label'));
          a.appendChild(label);
          a.appendChild(document.createTextNode(' '));
          var answer = document.createElement('em');
          if (checked) {
            answer.textContent = Array.prototype.map.call(picked, function (i) {
              return shownText(i.closest('.shrine-opt').querySelector('.shrine-opt__title'));
            }).join('; ');
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
      if (priced) return window.location.pathname + window.location.search + hash;
      return share.dataset.base + '?' + designQuery() + hash;
    }

    function writeAddress() {
      if (share) share.value = window.location.origin + share.dataset.base + '?' + designQuery();
      history.replaceState({ step: current ? current.dataset.step : null, depth: depth }, '', urlFor(current));
    }

    // FR-023: a fresh random order every time a step is shown, so position biases no choice.
    function shuffle(step) {
      // only [data-shuffle] grids: a multi-select step's exclusive option stays put (FR-044)
      var grid = step.querySelector('.shrine-opts[data-shuffle]');
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
      // FR-042: a fixed number of phases, never a step count that moves with the choices.
      wizard.querySelector('[data-count]').textContent = 'Part ' + step.dataset.phase + ' of ' + wizard.dataset.phases;
      document.documentElement.classList.toggle('wizard-deep', step.dataset.step !== 'name');
      wizard.querySelector('[data-bar]').style.width = ((index + 1) / list.length * 100) + '%';
      backBtn.style.visibility = index > 0 ? 'visible' : 'hidden';
      var last = index === list.length - 1;
      nextBtn.hidden = last;
      gateNext();
      nextBtn.textContent = index === list.length - 2 ? 'See your shrine' : 'Next';
      if (step.dataset.step === 'review') { syncSummary(); fitShare(); }
      updateEffects(step);
      writeAddress();
      if (scroll) wizard.scrollIntoView({ block: 'start' });
    }

    // Next waits for a choice: nothing is pre-selected, and skipping past a step unchosen would
    // leave a hole in the design. (The summary's "change" links still jump anywhere.)
    function gateNext() {
      if (!current) return;
      var fs = current.querySelector('fieldset.shrine-cat');
      var open = fs && !fs.disabled && !fs.querySelector('input:checked');
      nextBtn.disabled = !!open;
      var hint = wizard.querySelector('[data-hint]');
      hint.hidden = !open;
      hint.textContent = fs && fs.querySelector('input[type=checkbox]') ? 'Choose at least one' : 'Choose one';
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

    form.addEventListener('change', function (event) {
      // FR-044: on a multi-select step an exclusive option and the others clear each other
      var box = event.target;
      if (box.type === 'checkbox' && box.checked) {
        box.closest('fieldset').querySelectorAll('input[type=checkbox]').forEach(function (other) {
          if (other !== box && (box.hasAttribute('data-exclusive') || other.hasAttribute('data-exclusive'))) other.checked = false;
        });
      }
      if (priced) {
        try { sessionStorage.setItem(SCROLL_KEY, String(window.scrollY)); } catch (e) { /* ignore */ }
        form.action = '/shrines' + (current ? '#step-' + current.dataset.step : '');
        form.submit();
        return;
      }
      resolve();
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
      if (!priced && event.target.matches('[name=shrine_name]')) { syncSummary(); writeAddress(); }
    });
    // The name box wraps but is one line: Enter moves on instead of breaking it.
    var nameBox = form.querySelector('[data-one-line]');
    if (nameBox) {
      nameBox.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
          event.preventDefault();
          if (priced) form.requestSubmit(); else advance(neighbor(current, 1));
        }
      });
    }

    form.addEventListener('submit', function (event) {
      if (!priced) {
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

    // The ledger's sticky pin sits just under the site header, whose height changes with the width.
    var header = document.querySelector('.app-nav');
    function trackHeader() {
      if (header) document.documentElement.style.setProperty('--shrine-nav-h', header.offsetHeight + 'px');
    }
    trackHeader();
    window.addEventListener('resize', trackHeader);

    resolve();
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
    window.addEventListener('resize', function () { if (current) updateEffects(current); });
    window.addEventListener('load', fitShare);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitShare);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
