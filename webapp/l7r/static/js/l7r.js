/* =========================================================================
   L7R Toolkit — Shared client JS
   - Seal-filter behavior on /relics (fortune AND clan, composed with AND)
   - Smooth scroll to fortune section on fortune-filter click
   ========================================================================= */

(function () {
  'use strict';

  function initRelicsFilter() {
    // Two kinds of fortune filters:
    //   data-fortune="<slug|all>"   — single-fortune buttons + the "all" reset
    //   data-fortune-category="..." — meta-button (e.g. "Minor Fortunes")
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
      // A fortune section hides if every card inside it is hidden — keeps the
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
        // Don't scroll on clan changes — the filter applies in place and a
        // jump back to top would feel disorienting when narrowing by clan.
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRelicsFilter);
  } else {
    initRelicsFilter();
  }
})();
