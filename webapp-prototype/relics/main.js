/* =========================================================================
   Relics - Client (v2)
   Renders the per-Fortune index or the detail page from window.RELICS_BUNDLE.
   ========================================================================= */

(function () {
  'use strict';

  const bundle = window.RELICS_BUNDLE;
  if (!bundle) {
    document.body.innerHTML = '<p style="padding:4rem;text-align:center;font-family:serif;">Failed to load relic data.</p>';
    return;
  }

  const FORTUNES = bundle.fortunes;
  const RELICS   = bundle.relics;

  const CLAN_LABEL = {
    any:       'Anywhere',
    crab:      'Crab',
    crane:     'Crane',
    dragon:    'Dragon',
    fox:       'Fox',
    lion:      'Lion',
    mantis:    'Mantis',
    phoenix:   'Phoenix',
    scorpion:  'Scorpion',
    sparrow:   'Sparrow',
    unicorn:   'Unicorn',
    wasp:      'Wasp',
    dragonfly: 'Dragonfly',
    hare:      'Hare',
  };

  /* ------------------------- helpers ------------------------- */

  function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]);
    });
  }

  function proseToHtml(text) {
    const paragraphs = text.split(/\n\s*\n/);
    return paragraphs.map(function (p) {
      const safe = escapeHtml(p.trim());
      const withEm = safe.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
      return '<p>' + withEm + '</p>';
    }).join('\n');
  }

  /* ------------------------- index page ------------------------- */

  function renderIndex() {
    renderSeals();
    renderSections();
    bindFilters();
  }

  function renderSeals() {
    const rail = document.getElementById('seals');
    if (!rail) return;

    const seals = [];

    seals.push(
      '<button class="seal" type="button" data-fortune="all" aria-pressed="true">' +
        '<span class="seal__circle">all</span>' +
        '<span class="seal__name">all</span>' +
      '</button>'
    );

    Object.keys(FORTUNES).forEach(function (slug) {
      const f = FORTUNES[slug];
      seals.push(
        '<button class="seal" type="button" data-fortune="' + slug + '" aria-pressed="false" title="' + escapeHtml(f.domain) + '">' +
          '<span class="seal__circle" lang="ja">' + escapeHtml(f.kanji) + '</span>' +
          '<span class="seal__name">' + escapeHtml(f.name) + '</span>' +
        '</button>'
      );
    });

    rail.innerHTML = seals.join('');
  }

  function renderSections() {
    const root = document.getElementById('sections-root');
    if (!root) return;

    const sections = Object.keys(FORTUNES).map(function (slug) {
      const f = FORTUNES[slug];
      const relics = RELICS.filter(function (r) { return r.fortune === slug; });
      return (
        '<section class="fortune-section" id="fortune-' + slug + '" data-fortune="' + slug + '">' +
          '<header class="fortune-section__header">' +
            '<div class="fortune-section__kanji" lang="ja">' + escapeHtml(f.kanji) + '</div>' +
            '<div class="fortune-section__title-group">' +
              '<p class="fortune-section__romaji">' + escapeHtml(slug) + '</p>' +
              '<h2 class="fortune-section__name">' + escapeHtml(f.name) + '</h2>' +
              '<p class="fortune-section__domain">' + escapeHtml(f.domain) + '</p>' +
            '</div>' +
          '</header>' +
          '<div class="cards">' +
            relics.map(renderCard).join('') +
          '</div>' +
        '</section>'
      );
    }).join('');

    root.innerHTML = sections;
  }

  function renderCard(relic) {
    const clanLabel = CLAN_LABEL[relic.clan] || relic.clan;
    // For card display, show only the main category (drop the parenthetical descriptor).
    // The full relic_type appears in the detail page meta band.
    const typeShort = (relic.relic_type || '').split(/\s*\(/)[0].trim();
    return (
      '<a class="card" href="relic.html?slug=' + encodeURIComponent(relic.slug) + '" data-fortune="' + escapeHtml(relic.fortune) + '" data-clan="' + escapeHtml(relic.clan) + '">' +
        '<div class="card__top">' +
          '<span class="card__type" title="' + escapeHtml(relic.relic_type) + '">' + escapeHtml(typeShort) + '</span>' +
          '<span class="card__clan" data-clan="' + escapeHtml(relic.clan) + '">' + escapeHtml(clanLabel) + '</span>' +
        '</div>' +
        '<div class="card__hero">' +
          '<span class="card__kanji" lang="ja">' + escapeHtml(relic.japanese_kanji) + '</span>' +
          '<p class="card__romaji">' + escapeHtml(relic.japanese_romaji) + '</p>' +
        '</div>' +
        '<div class="card__foot">' +
          '<h3 class="card__name">' + escapeHtml(relic.name) + '</h3>' +
          '<p class="card__entity">' + escapeHtml(relic.named_entity) + '</p>' +
        '</div>' +
      '</a>'
    );
  }

  function bindFilters() {
    const seals = document.querySelectorAll('.seal');
    const sections = document.querySelectorAll('.fortune-section');

    seals.forEach(function (seal) {
      seal.addEventListener('click', function () {
        const fortune = seal.dataset.fortune;
        seals.forEach(function (s) { s.setAttribute('aria-pressed', String(s === seal)); });

        if (fortune === 'all') {
          sections.forEach(function (s) { s.hidden = false; });
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          sections.forEach(function (s) {
            s.hidden = (s.dataset.fortune !== fortune);
          });
          // Smooth scroll to the now-visible section, accounting for sticky nav
          const target = document.getElementById('fortune-' + fortune);
          if (target) {
            const navHeight = document.querySelector('.nav').offsetHeight || 70;
            const targetTop = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
            window.scrollTo({ top: targetTop, behavior: 'smooth' });
          }
        }
      });
    });
  }

  /* ------------------------- detail page ------------------------- */

  function renderDetail() {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get('slug');
    const root = document.getElementById('detail-root');
    if (!slug) {
      root.innerHTML = notFound('No relic specified.');
      return;
    }

    const relic = RELICS.find(function (r) { return r.slug === slug; });
    if (!relic) {
      root.innerHTML = notFound('No such relic in the pool.');
      return;
    }

    const f = fortuneOf(relic.fortune);
    document.title = relic.name + ' - Relics';

    const sameFortune = RELICS.filter(function (r) { return r.fortune === relic.fortune; });
    const idx = sameFortune.findIndex(function (r) { return r.slug === slug; });
    const prev = sameFortune[idx - 1] || sameFortune[sameFortune.length - 1];
    const next = sameFortune[idx + 1] || sameFortune[0];

    const clanLabel = CLAN_LABEL[relic.clan] || relic.clan;

    root.innerHTML =
      '<header class="nav">' +
        '<div class="container nav__inner">' +
          '<a class="nav__brand" href="index.html">Relics <em>of the Seven Fortunes</em></a>' +
          '<a class="back-link" href="index.html">← back to the pool</a>' +
        '</div>' +
      '</header>' +

      '<main>' +
        '<section class="container">' +
          '<header class="detail-hero">' +
            '<p class="detail-hero__supertitle">Of ' + escapeHtml(f.name) + ' &middot; ' + escapeHtml(f.domain) + '</p>' +
            '<h1 class="detail-hero__kanji" lang="ja">' + escapeHtml(relic.japanese_kanji) + '</h1>' +
            '<p class="detail-hero__romaji">' + escapeHtml(relic.japanese_romaji) + '</p>' +
            '<h2 class="detail-hero__name">' + escapeHtml(relic.name) + '</h2>' +
          '</header>' +

          '<dl class="detail-meta">' +
            field('Fortune', '<span class="jp" lang="ja">' + escapeHtml(f.kanji) + '</span><strong>' + escapeHtml(f.name) + '</strong>') +
            field('Clan', escapeHtml(clanLabel)) +
            field('Type', escapeHtml(relic.relic_type)) +
            field('Resides at', escapeHtml(relic.temple)) +
            field('Tied to', escapeHtml(relic.named_entity)) +
          '</dl>' +
        '</section>' +

        '<article class="container">' +
          '<div class="detail-prose">' +
            proseToHtml(relic.description) +
          '</div>' +
        '</article>' +

        '<footer class="container">' +
          '<div class="detail-footer">' +
            '<div class="detail-footer__nav">' +
              (prev && prev.slug !== relic.slug
                ? '<a class="detail-footer__link detail-footer__link--prev" href="relic.html?slug=' + encodeURIComponent(prev.slug) + '">' +
                    '<strong>← previous of ' + escapeHtml(f.name) + '</strong>' +
                    escapeHtml(prev.name) +
                  '</a>'
                : '') +
              (next && next.slug !== relic.slug
                ? '<a class="detail-footer__link detail-footer__link--next" href="relic.html?slug=' + encodeURIComponent(next.slug) + '">' +
                    '<strong>next of ' + escapeHtml(f.name) + ' →</strong>' +
                    escapeHtml(next.name) +
                  '</a>'
                : '') +
            '</div>' +
          '</div>' +
        '</footer>' +
      '</main>';
  }

  function fortuneOf(slug) { return FORTUNES[slug]; }

  function field(label, valueHtml) {
    return (
      '<div class="detail-meta__field">' +
        '<dt class="detail-meta__label">' + escapeHtml(label) + '</dt>' +
        '<dd class="detail-meta__value">' + valueHtml + '</dd>' +
      '</div>'
    );
  }

  function notFound(msg) {
    return (
      '<header class="nav">' +
        '<div class="container nav__inner">' +
          '<a class="nav__brand" href="index.html">Relics <em>of the Seven Fortunes</em></a>' +
          '<a class="back-link" href="index.html">← back to the pool</a>' +
        '</div>' +
      '</header>' +
      '<section class="container">' +
        '<p style="padding: 6rem 0; text-align:center; font-family:serif; font-style:italic; color: var(--ink-faded); font-size: 1.2rem;">' +
          escapeHtml(msg) +
        '</p>' +
      '</section>'
    );
  }

  /* ------------------------- bootstrap ------------------------- */

  function init() {
    if (document.getElementById('sections-root')) {
      renderIndex();
    } else if (document.getElementById('detail-root')) {
      renderDetail();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
