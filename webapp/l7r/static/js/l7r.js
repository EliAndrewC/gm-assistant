/* =========================================================================
   L7R Toolkit — Shared client JS
   - Seal-filter behavior on /relics
   - Smooth scroll to fortune section on filter click
   ========================================================================= */

(function () {
  'use strict';

  function initRelicsFilter() {
    const seals = document.querySelectorAll('.seal');
    const sections = document.querySelectorAll('.fortune-section');
    if (!seals.length || !sections.length) return;

    seals.forEach(function (seal) {
      seal.addEventListener('click', function () {
        const fortune = seal.dataset.fortune;
        seals.forEach(function (s) { s.setAttribute('aria-pressed', String(s === seal)); });

        if (fortune === 'all') {
          sections.forEach(function (s) { s.hidden = false; });
          window.scrollTo({ top: 0, behavior: 'smooth' });
          return;
        }

        sections.forEach(function (s) {
          s.hidden = (s.dataset.fortune !== fortune);
        });
        const target = document.getElementById('fortune-' + fortune);
        if (target) {
          const nav = document.querySelector('.app-nav');
          const navHeight = nav ? nav.offsetHeight : 70;
          const targetTop = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
          window.scrollTo({ top: targetTop, behavior: 'smooth' });
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRelicsFilter);
  } else {
    initRelicsFilter();
  }
})();
