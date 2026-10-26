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
   - Feature 228: "Something else" on every step (the player's own words, instead of the cards or
     as well), and the studio on the last step: a description, a picture, and the shrine's wiki
     page. Option inputs carry data-opt; nothing else in a fieldset is a pick.
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

    // Feature 228: a step's "Something else" - null when off, else its text and mode
    // ('instead', 'also', or null before the player says which).
    function otherState(fs) {
      var box = fs.querySelector('[data-other]');
      if (!box || !box.querySelector('[data-other-toggle]').checked) return null;
      var mode = box.querySelector('[data-other-mode]:checked');
      return { text: box.querySelector('textarea').value.trim(), mode: mode ? mode.dataset.otherMode : null };
    }

    // Off = its text and mode are disabled, so they never reach the link (FormData skips them).
    function syncOther(fs) {
      var box = fs.querySelector('[data-other]');
      if (!box) return;
      var on = box.querySelector('[data-other-toggle]').checked;
      box.classList.toggle('is-on', on);
      box.querySelector('[data-other-body]').hidden = !on;
      box.querySelectorAll('textarea, [data-other-mode]').forEach(function (el) { el.disabled = !on; });
      var st = otherState(fs);
      fs.classList.toggle('is-instead', !!(st && st.mode === 'instead'));
    }

    function resolve() {
      var choices = {};
      form.querySelectorAll('fieldset.shrine-cat').forEach(function (fs) {
        var key = fs.dataset.cat;
        var failing = (rules.categories[key] || []).filter(function (c) { return !holds(c, choices); })[0];
        fs.classList.toggle('is-moot', !!failing);
        fs.disabled = !!failing;
        if (failing) return;
        syncOther(fs);
        // FR-004: "instead" sets the cards aside - the step has no listed option.
        var st = otherState(fs);
        var instead = !!(st && st.mode === 'instead');
        var optionRules = rules.options[key] || {};
        fs.querySelectorAll('input[data-opt]').forEach(function (input) {
          var ok = (optionRules[input.value] || []).every(function (c) { return holds(c, choices); });
          input.closest('.shrine-opt-cell').classList.toggle('is-unavailable', !ok);
          input.disabled = !ok || instead;
          if (!ok || instead) input.checked = false;
        });
        var checked = fs.querySelector('input[data-opt]:checked');
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
        options: Array.prototype.map.call(fs.querySelectorAll('input[data-opt][type=radio]'), function (i) { return i.value; })
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
      form.querySelectorAll('fieldset.shrine-cat:not(:disabled) input[data-opt][type=radio]:checked').forEach(function (i) {
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
          var picked = fs.querySelectorAll('input[data-opt]:checked');
          var checked = picked[0];
          var other = otherState(fs);
          if (other && (!other.text || !other.mode)) other = null;
          var li = document.createElement('li');
          var a = document.createElement('a');
          a.href = '#shrine-step-' + fs.dataset.cat;
          a.dataset.goto = fs.dataset.cat;
          var label = document.createElement('span');
          label.textContent = shownText(fs.querySelector('.shrine-cat__label'));
          a.appendChild(label);
          a.appendChild(document.createTextNode(' '));
          var answer = document.createElement('em');
          if (checked || other) {
            var parts = Array.prototype.map.call(picked, function (i) {
              return shownText(i.closest('.shrine-opt').querySelector('.shrine-opt__title'));
            });
            var text = parts.join('; ');
            if (other) {
              text = other.mode === 'instead' ? 'Instead, ' + other.text
                : (text ? text + ', plus ' : 'Plus ') + other.text;
            }
            answer.textContent = text;
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
      if (step.dataset.step === 'review') {
        syncSummary();
        fitShare();
        document.dispatchEvent(new CustomEvent('shrine:review'));
      }
      updateEffects(step);
      writeAddress();
      if (scroll) wizard.scrollIntoView({ block: 'start' });
    }

    // Next waits for a choice: nothing is pre-selected, and skipping past a step unchosen would
    // leave a hole in the design. (The summary's "change" links still jump anywhere.)
    function gateNext() {
      if (!current) return;
      var fs = current.querySelector('fieldset.shrine-cat');
      var hint = wizard.querySelector('[data-hint]');
      var message = '';
      if (fs && !fs.disabled) {
        var st = otherState(fs);
        var picked = fs.querySelector('input[data-opt]:checked');
        var many = fs.querySelector('input[data-opt][type=checkbox]');
        if (st && !st.text) message = 'Describe it in your own words';
        else if (st && !st.mode) message = 'Instead, or as well?';
        else if (!(st && st.mode === 'instead') && !picked) message = many ? 'Choose at least one' : 'Choose one';
      }
      nextBtn.disabled = !!message;
      hint.hidden = !message;
      hint.textContent = message;
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
      if (box.form !== form) return;  // the studio's fields belong to #shrine-studio
      if (box.hasAttribute('data-opt') && box.type === 'checkbox' && box.checked) {
        box.closest('fieldset').querySelectorAll('input[data-opt][type=checkbox]').forEach(function (other) {
          if (other !== box && (box.hasAttribute('data-exclusive') || other.hasAttribute('data-exclusive'))) other.checked = false;
        });
      }
      var otherBox = box.closest('[data-other]');
      if (otherBox) {
        var ofs = otherBox.closest('fieldset');
        syncOther(ofs);
        if (box.matches('[data-other-toggle]') && box.checked) otherBox.querySelector('textarea').focus();
        // An unfinished "something else" changes nothing yet: no reload for the ledger.
        var ost = otherState(ofs);
        if (priced && ost && (!ost.text || !ost.mode)) { gateNext(); return; }
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
      if (event.target.form !== form) return;
      if (event.target.matches('[data-one-line]')) fitBox(event.target);
      if (event.target.closest('[data-other]')) {
        gateNext();
        if (!priced) { syncSummary(); writeAddress(); }
      }
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

    // The one-line total pin shows only once the full totals box has scrolled away.
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

    initStudio(designQuery);

    window.addEventListener('resize', fitShare);
    window.addEventListener('resize', function () { if (current) updateEffects(current); });
    window.addEventListener('load', fitShare);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitShare);
  }

  /* -----------------------------------------------------------------------
     Feature 228: the studio on the last step. It looks up the shrine's wiki
     page (anyone), and for a signed-in viewer writes a description, draws a
     picture and saves both to the wiki. Nothing is stored on this server:
     a drawn picture stays in the page until it is saved.
     ----------------------------------------------------------------------- */
  function initStudio(designQuery) {
    var studio = document.querySelector('[data-studio]');
    if (!studio) return;
    var signedIn = studio.dataset.signedIn === 'true';
    var status = studio.querySelector('[data-wiki-status]');
    var desc = studio.querySelector('[data-description]');
    var promptBox = studio.querySelector('[data-prompt]');
    var picture = studio.querySelector('[data-picture]');
    var img = studio.querySelector('[data-picture-img]');
    var saveBtn = studio.querySelector('[data-save]');
    var note = studio.querySelector('[data-studio-status]');
    var drawn = null;          // {image, mime} of a picture drawn this visit, not yet saved
    var hasSavedPicture = false;
    var loadedFor = null;      // the wiki page whose contents fill the boxes
    var lastQuery = null;
    var descDirty = false;
    var promptDirty = false;
    if (desc) desc.addEventListener('input', function () { descDirty = true; });
    if (promptBox) promptBox.addEventListener('input', function () { promptDirty = true; });

    function say(el, text) { if (el) el.textContent = text; }

    function json(url, body) {
      var opts = body === undefined ? {} : {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
      };
      return fetch(url, opts).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (data) {
          if (!r.ok) throw new Error(data.error || ('The server said ' + r.status + '.'));
          return data;
        });
      });
    }

    function showPicture(src) {
      img.src = src;
      picture.hidden = false;
    }

    function setStyle(key) {
      var radio = key && studio.querySelector('input[name=art_style][value="' + key + '"]');
      if (radio) radio.checked = true;
    }

    function wikiStatus(data) {
      status.innerHTML = '';
      if (data.error) { say(status, data.error); return; }
      if (!data.found) {
        say(status, signedIn
          ? 'This shrine has no wiki page yet. Describe it and draw it, then create one.'
          : 'This shrine has no wiki page yet.');
        if (saveBtn) saveBtn.textContent = 'Create wiki page';
        return;
      }
      var a = document.createElement('a');
      a.href = data.url;
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = 'its wiki page';
      status.appendChild(document.createTextNode('This shrine has '));
      status.appendChild(a);
      status.appendChild(document.createTextNode(data.matches
        ? ', and it matches these choices.'
        : '. The choices here differ from the wiki page' + (signedIn ? ': update it to save them.' : '.')));
      status.classList.toggle('is-stale', !data.matches);
      if (saveBtn) saveBtn.textContent = 'Update wiki page';
    }

    function refreshPrompt(force) {
      if (!promptBox || (promptDirty && !force)) return Promise.resolve();
      return json('/shrines/prompt?' + designQuery()).then(function (data) {
        promptBox.value = data.prompt;
        promptDirty = false;
      });
    }

    function lookUp() {
      var q = designQuery();
      if (q === lastQuery) return;
      lastQuery = q;
      json('/shrines/wiki?' + q).then(function (data) {
        wikiStatus(data);
        // a signed-out visitor sees the boxes only when there is a saved page to show
        studio.querySelector('[data-studio-grid]').hidden = !signedIn && !data.found;
        if (data.found && loadedFor !== data.url) {
          loadedFor = data.url;
          if (!descDirty) desc.value = data.description || '';
          if (data.image_url && !drawn) { showPicture(data.image_url); hasSavedPicture = true; }
          setStyle(data.style);
          if (promptBox && data.prompt && !promptDirty) { promptBox.value = data.prompt; promptDirty = true; }
        }
      }).catch(function () { say(status, 'Could not check the wiki just now.'); });
      refreshPrompt(false);
    }

    document.addEventListener('shrine:review', lookUp);
    if (document.querySelector('.wizard-step.is-current[data-step=review]')) lookUp();
    if (!signedIn) return;

    function busy(button, text, work) {
      var label = button.textContent;
      button.disabled = true;
      button.textContent = text;
      say(note, '');
      return work().catch(function (err) { say(note, err.message); }).then(function () {
        button.disabled = false;
        button.textContent = label;
      });
    }

    studio.querySelector('[data-describe]').addEventListener('click', function (event) {
      if (descDirty && desc.value.trim() && !window.confirm('Replace the description you edited?')) return;
      busy(event.currentTarget, 'Writing...', function () {
        return json('/shrines/describe', { query: designQuery() }).then(function (data) {
          desc.value = data.text;
          descDirty = false;
        });
      });
    });

    studio.querySelector('[data-rebuild]').addEventListener('click', function () { refreshPrompt(true); });

    studio.querySelector('[data-draw]').addEventListener('click', function (event) {
      var style = studio.querySelector('input[name=art_style]:checked');
      busy(event.currentTarget, 'Drawing... (about 15 seconds)', function () {
        return refreshPrompt(false).then(function () {
          return json('/shrines/draw', { prompt: promptBox.value, style: style ? style.value : '' });
        }).then(function (data) {
          drawn = data;
          showPicture('data:' + data.mime + ';base64,' + data.image);
        });
      });
    });

    saveBtn.addEventListener('click', function (event) {
      if (!desc.value.trim()) { say(note, 'Write a description, or press Describe the shrine, first.'); return; }
      if (!drawn && !hasSavedPicture) { say(note, 'Draw a picture first: the wiki page needs both a picture and a description.'); return; }
      var style = studio.querySelector('input[name=art_style]:checked');
      busy(event.currentTarget, 'Saving to the wiki...', function () {
        return json('/shrines/wiki', {
          query: designQuery(),
          description: desc.value,
          style: style ? style.value : '',
          prompt: promptBox.value,
          image: drawn ? drawn.image : ''
        }).then(function (data) {
          drawn = null;
          hasSavedPicture = true;
          loadedFor = data.url;
          descDirty = true;  // what is in the box is what the page now says
          lastQuery = null;
          lookUp();
          say(note, data.created ? 'Wiki page created.' : 'Wiki page updated.');
        });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
