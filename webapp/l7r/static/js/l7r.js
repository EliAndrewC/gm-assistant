/* =========================================================================
   L7R Toolkit — Shared client JS
   - Seal-filter behavior on /relics (fortune AND clan, composed with AND)
   - Smooth scroll to fortune section on fortune-filter click
   ========================================================================= */

(function () {
  'use strict';

  function initRelicsFilter() {
    const fortuneSeals = document.querySelectorAll('.seal[data-fortune]');
    const clanSeals = document.querySelectorAll('.seal[data-clan]');
    const cards = document.querySelectorAll('.cards .card');
    const sections = document.querySelectorAll('.fortune-section');
    if (!fortuneSeals.length || !cards.length) return;

    let currentFortune = 'all';
    let currentClan = 'all';

    function applyFilters() {
      // Per-card visibility = (fortune matches OR all) AND (clan matches OR all).
      cards.forEach(function (card) {
        const fortuneMatch = currentFortune === 'all' || card.dataset.fortune === currentFortune;
        const clanMatch = currentClan === 'all' || card.dataset.clan === currentClan;
        card.hidden = !(fortuneMatch && clanMatch);
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
      const target = document.getElementById('fortune-' + slug);
      if (!target) return;
      const nav = document.querySelector('.app-nav');
      const navHeight = nav ? nav.offsetHeight : 70;
      const targetTop = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
      window.scrollTo({ top: targetTop, behavior: 'smooth' });
    }

    fortuneSeals.forEach(function (seal) {
      seal.addEventListener('click', function () {
        currentFortune = seal.dataset.fortune;
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
