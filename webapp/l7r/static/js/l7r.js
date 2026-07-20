/* =========================================================================
   L7R Toolkit - Shared client JS
   - Seal-filter behavior on /relics (fortune AND clan, composed with AND)
   - Smooth scroll to fortune section on fortune-filter click
   ========================================================================= */

(function () {
  'use strict';

  function initRelicsFilter() {
    // Two kinds of fortune filters:
    //   data-fortune="<slug|all>"   - single-fortune buttons + the "all" reset
    //   data-fortune-category="..." - meta-button (e.g. "Minor Fortunes")
    //                                 matching every card with that category
    const fortuneSeals = document.querySelectorAll('.seal[data-fortune], .seal[data-fortune-category]');
    const clanSeals = document.querySelectorAll('.seal[data-clan]');
    const cards = document.querySelectorAll('.cards .card');
    const sections = document.querySelectorAll('.fortune-section');
    if (!fortuneSeals.length || !cards.length) return;

    // currentFortune is one of: 'all', a fortune slug, or 'category:<name>'.
    let currentFortune = 'all';
    let currentClan = 'all';

    function fortuneMatches(card) {
      if (currentFortune === 'all') return true;
      if (currentFortune.startsWith('category:')) {
        return card.dataset.fortuneCategory === currentFortune.slice('category:'.length);
      }
      return card.dataset.fortune === currentFortune;
    }

    function applyFilters() {
      cards.forEach(function (card) {
        const clanMatch = currentClan === 'all' || card.dataset.clan === currentClan;
        card.hidden = !(fortuneMatches(card) && clanMatch);
      });
      // A fortune section hides if every card inside it is hidden - keeps the
      // page from showing empty-named headers like "Daikoku" with no relics.
      sections.forEach(function (s) {
        const visible = s.querySelectorAll('.card:not([hidden])');
        s.hidden = visible.length === 0;
      });
    }

    function scrollToFortune(slug) {
      if (slug === 'all') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
      }
      if (slug.startsWith('category:')) {
        // Category meta-filter: scroll to the first visible section in that
        // category. There may be several; pick the first that survives the
        // filter pass and is still in the DOM.
        const cat = slug.slice('category:'.length);
        const target = document.querySelector(
          '.fortune-section[data-fortune-category="' + cat + '"]:not([hidden])'
        );
        if (!target) return;
        const nav = document.querySelector('.app-nav');
        const navHeight = nav ? nav.offsetHeight : 70;
        const targetTop = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
        window.scrollTo({ top: targetTop, behavior: 'smooth' });
        return;
      }
      const target = document.getElementById('fortune-' + slug);
      if (!target) return;
      const nav = document.querySelector('.app-nav');
      const navHeight = nav ? nav.offsetHeight : 70;
      const targetTop = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
      window.scrollTo({ top: targetTop, behavior: 'smooth' });
    }

    fortuneSeals.forEach(function (seal) {
      seal.addEventListener('click', function () {
        if (seal.dataset.fortuneCategory) {
          currentFortune = 'category:' + seal.dataset.fortuneCategory;
        } else {
          currentFortune = seal.dataset.fortune;
        }
        fortuneSeals.forEach(function (s) {
          s.setAttribute('aria-pressed', String(s === seal));
        });
        applyFilters();
        scrollToFortune(currentFortune);
      });
    });

    clanSeals.forEach(function (seal) {
      seal.addEventListener('click', function () {
        currentClan = seal.dataset.clan;
        clanSeals.forEach(function (s) {
          s.setAttribute('aria-pressed', String(s === seal));
        });
        applyFilters();
        // Don't scroll on clan changes - the filter applies in place and a
        // jump back to top would feel disorienting when narrowing by clan.
      });
    });
  }

  // ---------------------------------------------------------------------
  // /places detail: scale toggle + copy-paste description
  // ---------------------------------------------------------------------

  function scalePhrase(scale) {
    if (scale === 'province') return 'a province';
    if (scale === 'town') return 'a county town';
    if (scale === 'village') return 'a village';
    if (scale === 'hamlet') return 'a hamlet';
    return 'a ' + scale;
  }

  function renderDescription(box, scale) {
    const name = box.dataset.name || '';
    const kanji = box.dataset.kanji || '';
    const meaning = box.dataset.meaning || '';
    const suffixNote = box.dataset.suffixNote || '';
    const entryNotes = box.dataset.entryNotes || '';
    let line = name + ' (' + kanji + ", '" + meaning + "') is " + scalePhrase(scale) + '.';
    if (suffixNote) line += ' ' + suffixNote;
    if (entryNotes) line += ' ' + entryNotes;
    return line;
  }

  function initPlacesDetail() {
    const box = document.querySelector('.places-copy');
    if (!box) return;
    const textarea = box.querySelector('.places-copy__text');
    const toggleBtns = box.querySelectorAll('.places-copy__scale-btn');
    const copyBtn = box.querySelector('.places-copy__copy-btn');
    const labelEl = box.querySelector('.places-copy__scale-label');

    function activeScale() {
      const active = box.querySelector('.places-copy__scale-btn--active');
      if (active) return active.dataset.scale;
      if (labelEl) return labelEl.textContent.trim();
      return 'village';
    }

    function refresh() {
      textarea.value = renderDescription(box, activeScale());
    }

    toggleBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        toggleBtns.forEach(function (b) {
          const isActive = b === btn;
          b.classList.toggle('places-copy__scale-btn--active', isActive);
          b.setAttribute('aria-checked', String(isActive));
        });
        refresh();
      });
    });

    if (copyBtn) {
      copyBtn.addEventListener('click', function () {
        textarea.select();
        // navigator.clipboard is async and may be unavailable in older browsers
        // or when not served over HTTPS. document.execCommand is the fallback.
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(textarea.value).catch(function () {
            try { document.execCommand('copy'); } catch (e) { /* swallow */ }
          });
        } else {
          try { document.execCommand('copy'); } catch (e) { /* swallow */ }
        }
        const label = copyBtn.querySelector('span:last-child');
        if (label) {
          const original = label.textContent;
          label.textContent = 'Copied!';
          setTimeout(function () { label.textContent = original; }, 1200);
        }
      });
    }

    refresh();
  }

  // ---------------------------------------------------------------------
  // Responsive nav: hamburger toggle for the collapsed header menu
  // ---------------------------------------------------------------------

  function initNavToggle() {
    const header = document.querySelector('.app-nav');
    const toggle = header ? header.querySelector('.app-nav__toggle') : null;
    if (!toggle) return;

    function setOpen(open) {
      header.classList.toggle('app-nav--open', open);
      toggle.setAttribute('aria-expanded', String(open));
    }

    toggle.addEventListener('click', function () {
      setOpen(!header.classList.contains('app-nav--open'));
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });

    // Clicking anywhere outside the header closes the menu. Link clicks
    // inside it navigate away, so they need no special handling.
    document.addEventListener('click', function (e) {
      if (!header.contains(e.target)) setOpen(false);
    });
  }

  function init() {
    initRelicsFilter();
    initPlacesDetail();
    initNavToggle();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
