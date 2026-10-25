/* What's a koku worth? (/money/koku, features 222, 223).
 *
 * `prices` and `compute` are the browser twins of l7r/money/basket.py `Model.prices` and `reading`;
 * tests/test_money_js.py runs them under node against the Python on several states, so change the
 * two together. The rest wires the form: every change recomputes both readings (the whole basket
 * and the average over goods) and rewrites the link (l7r/money/web.py documents the parameters), so
 * the link always reopens what is on screen.
 */
(function (root) {
  'use strict';

  // Every era's weight: the override, else the default; the reference alone if none prices rice.
  function weights(data, over) {
    var w = {};
    var any = false;
    Object.keys(data.eras).forEach(function (id) {
      var v = over && over[id] !== undefined ? over[id] : data.eras[id].weight;
      w[id] = Math.max(v, 0);
      if (w[id] && Object.keys(data.eras[id].goods).length) any = true;
    });
    if (!any) {
      Object.keys(data.eras).forEach(function (id) { w[id] = data.eras[id].reference ? 1 : 0; });
    }
    return w;
  }

  // The eras a good's price rests on: borrowed prices only when no weighted era observes it;
  // excluded ones (not pre-modern prices) never.
  function restsOn(data, w, good) {
    var eras = Object.keys(data.eras).filter(function (id) {
      var g = data.eras[id].goods[good];
      return w[id] && g && !g.excluded;
    });
    var observed = eras.filter(function (id) { return !data.eras[id].goods[good].borrowed; });
    return observed.length ? observed : eras;
  }

  function prices(data, over) {
    var w = weights(data, over);
    var out = {};
    Object.keys(data.goods).forEach(function (good) {
      var num = 0;
      var den = 0;
      restsOn(data, w, good).forEach(function (id) {
        num += w[id] * Math.log(data.eras[id].goods[good].ratio);
        den += w[id];
      });
      if (den) out[good] = data.rice_ref * Math.exp(num / den);
    });
    return out;
  }

  function compute(data, state) {
    var basket = data.baskets[state.basket];
    var snap = data.snapshots[state.snapshot];
    var rok = prices(data, state.w);
    var qty = Object.assign({}, basket.goods, state.q || {});
    var lines = [];
    Object.keys(qty).forEach(function (good) {
      var opts = snap.goods[good] || [];
      var pick = opts.length ? opts[Math.min(Math.max((state.x || {})[good] || 0, 0), opts.length - 1)] : null;
      lines.push(line(good, data.goods[good].name, qty[good], pick ? pick.dollars : null, rok[good] || null));
    });
    var dollars = 0;
    var silver = 0;
    lines.forEach(function (ln) {
      dollars += ln.dollars;
      silver += ln.silver;
    });
    var kokuSilver = data.koku_kg * data.rice_ref;
    var counted = lines.filter(function (ln) { return ln.counted; });
    var arithmetic = 0;
    var logs = 0;
    counted.forEach(function (ln) {
      ln.alone = ln.dpu / ln.spu * kokuSilver;
      ln.weight = state.equal ? 1 / counted.length : ln.silver / silver;
      arithmetic += ln.weight * ln.alone;
      logs += ln.weight * Math.log(ln.alone);
    });
    var geometric = counted.length ? Math.exp(logs) : 0;
    return {
      lines: lines,
      dollars: dollars,
      silver: silver,
      koku_cost: silver / kokuSilver,
      mean: state.mean || 'geometric',
      arithmetic: arithmetic,
      geometric: geometric,
      per_koku: (state.mean || 'geometric') === 'geometric' ? geometric : arithmetic,
      left_out: lines.filter(function (ln) { return ln.quantity > 0 && !ln.counted; })
        .map(function (ln) { return ln.name; }),
    };
  }

  // The whole basket: every good of the complete basket, only the substitutes and era weights.
  function computeWhole(data, state) {
    return compute(data, { basket: state.whole || data.standard, snapshot: state.snapshot, x: state.x, w: state.w, mean: 'arithmetic' });
  }

  function line(good, name, quantity, dpu, spu) {
    var counted = quantity > 0 && !!dpu && !!spu;
    return {
      good: good,
      name: name,
      quantity: quantity,
      counted: counted,
      dpu: dpu,
      spu: spu,
      dollars: counted ? quantity * dpu : 0,
      silver: counted ? quantity * spu : 0,
    };
  }

  // The twin of web.py `sig3`: three significant figures, whole numbers with commas from 100.
  function sig3(x) {
    var v = parseFloat(x.toPrecision(3));
    return v >= 100 ? v.toLocaleString('en-US', { maximumFractionDigits: 0 }) : String(v);
  }

  function pct(w) {
    return w < 0.005 ? '<1%' : Math.round(w * 100) + '%';
  }

  function money(x, places) {
    return '$' + x.toLocaleString('en-US', { minimumFractionDigits: places || 0, maximumFractionDigits: places || 0 });
  }

  // The twin of web.py `drivers`.
  function drivers(r) {
    var counted = r.lines.filter(function (ln) { return ln.counted; });
    if (!counted.length) return 'Nothing in the basket is priced on both sides.';
    var f = r.mean === 'geometric' ? Math.log : function (x) { return x; };
    var center = f(r.per_koku);
    var pulls = counted.map(function (ln) { return { p: ln.weight * (f(ln.alone) - center), ln: ln }; });
    var up = pulls.reduce(function (a, b) { return b.p > a.p ? b : a; });
    var down = pulls.reduce(function (a, b) { return b.p < a.p ? b : a; });
    function say(x) { return x.ln.name + ' (' + money(x.ln.alone) + ' alone, ' + pct(x.ln.weight) + ' of the weight)'; }
    if (up.p <= 0 || down.p >= 0) return 'Every good reads the same: ' + say(up) + '.';
    return 'Pulls the average up most: ' + say(up) + '. Pulls it down most: ' + say(down) + '.';
  }

  function axisPct(axis, dollars) {
    var lo = Math.log10(axis[0]);
    var x = (Math.log10(Math.max(dollars, axis[0])) - lo) / (Math.log10(axis[1]) - lo);
    return Math.round(Math.min(Math.max(x, 0), 1) * 10000) / 100;
  }

  root.kokuCompute = compute;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { sig3: sig3, compute: compute, computeWhole: computeWhole, drivers: drivers, prices: prices, restsOn: restsOn, weights: weights, axisPct: axisPct };
  }
  if (typeof document === 'undefined') return;

  // The twin of the template's `amount` macro: "2.6 liters", "3.31 m²".
  function amount(q, unit) {
    var u = unit.replace(' for a year', '');
    return q + ' ' + (u === 'liter' && q !== 1 ? 'liters' : u);
  }

  function number(input) {
    var v = parseFloat(input.value);
    return isFinite(v) && v >= 0 ? v : null;
  }

  function init() {
    var form = document.getElementById('koku-form');
    if (!form) return;
    var data = JSON.parse(document.getElementById('koku-data').textContent);
    var basketSel = form.querySelector('[data-in="basket"]');
    var rows = Array.prototype.slice.call(form.querySelectorAll('li[data-good]'));
    var eraInputs = Array.prototype.slice.call(form.querySelectorAll('[data-in="weight"]'));
    var out = function (name) { return form.querySelector('[data-out="' + name + '"]'); };

    function box(row) { return row.querySelector('.koku-on'); }

    // A ticked good counts at its checkbox's quantity; an unticked one at 0.
    function quantity(row) { return box(row).checked ? parseFloat(box(row).value) || 0 : 0; }

    function state() {
      var basket = data.baskets[basketSel.value];
      var mean = form.querySelector('[data-in="mean"]:checked');
      var st = {
        basket: basketSel.value, snapshot: data.newest, q: {}, x: {}, w: {},
        mean: mean ? mean.value : 'geometric', equal: form.querySelector('[data-in="equal"]').checked,
      };
      rows.forEach(function (row) {
        var good = row.dataset.good;
        var q = quantity(row);
        if (q !== (basket.goods[good] || 0)) st.q[good] = q;
        var sub = row.querySelector('input[type="radio"]:checked');
        if (sub && sub.value !== '0') st.x[good] = parseInt(sub.value, 10);
      });
      eraInputs.forEach(function (input) {
        var id = input.closest('[data-era]').dataset.era;
        var v = number(input);
        if (v !== null && v !== data.eras[id].weight) st.w[id] = v;
      });
      return st;
    }

    function link(st) {
      var p = new URLSearchParams();
      if (st.basket !== data.standard) p.set('b', st.basket);
      if (st.mean !== 'geometric') p.set('m', st.mean);
      if (st.equal) p.set('eq', '1');
      Object.keys(st.q).forEach(function (g) { p.set('q_' + g, String(st.q[g])); });
      Object.keys(st.x).forEach(function (g) { p.set('x_' + g, String(st.x[g])); });
      Object.keys(st.w).forEach(function (e) { p.set('w_' + e, String(st.w[e])); });
      var qs = p.toString();
      return location.pathname + (qs ? '?' + qs : '');
    }

    function place(el, dollars) { el.style.setProperty('--at', axisPct(data.axis, dollars) + '%'); }

    function render() {
      var st = state();
      var r = compute(data, st);
      var whole = computeWhole(data, st);
      out('per-koku').textContent = money(r.per_koku);
      out('per-koku-sticky').textContent = money(r.per_koku);
      out('whole').textContent = money(whole.arithmetic);
      out('whole-sticky').textContent = money(whole.arithmetic);
      out('legend-central').textContent = money(r.per_koku);
      out('legend-high').textContent = money(whole.arithmetic);
      out('mean-name').textContent = '(' + (st.equal ? 'equal weights, ' : '') + st.mean + ' mean)';
      out('whole-gloss').textContent = "A laborer's year of necessities cost " + whole.koku_cost.toFixed(2) +
        ' koku in Rokugan and costs ' + money(whole.dollars) + ' today, so a koku is ' + money(whole.arithmetic) +
        '. Averaging what a koku buys of each good instead, so that no one good can dominate, gives ' + money(r.per_koku) + '.';
      out('drivers').textContent = drivers(r);
      out('description').textContent = data.baskets[st.basket].description;
      var left = out('left-out');
      var missing = r.left_out;
      left.hidden = !missing.length;
      left.textContent = 'Not priced, so left out: ' + missing.join(', ') + '.';
      var byGood = {};
      r.lines.forEach(function (ln) { byGood[ln.good] = ln; });
      var w = weights(data, st.w);
      var rok = prices(data, st.w);
      rows.forEach(function (row) {
        var ln = byGood[row.dataset.good];
        var on = !!(ln && ln.counted);
        row.classList.toggle('koku-good--off', !on);
        row.querySelector('[data-out="qty"]').textContent = amount(parseFloat(box(row).value), data.goods[row.dataset.good].unit);
        row.querySelector('[data-out="weight"]').textContent = on ? pct(ln.weight) : '-';
        row.querySelector('[data-out="alone"]').textContent = on ? money(ln.alone) : (quantity(row) > 0 ? 'no price' : 'left out');
        place(row.querySelector('.koku-track__mark--central'), r.per_koku);
        place(row.querySelector('.koku-track__mark--high'), whole.arithmetic);
        // Rokugan's side: the price under these weights, and which periods it rests on.
        var good = row.dataset.good;
        var price = row.querySelector('[data-out="rok-price"]');
        if (price && rok[good]) {
          price.firstElementChild.textContent = sig3(rok[good] / (data.rice_ref * data.koku_kg) * 1000) + ' sen a ' + data.goods[good].unit;
          price.lastChild.textContent = ', the price of ' + (rok[good] / data.rice_ref).toFixed(2) + ' kg of rice.';
        }
        var on_ = restsOn(data, w, good);
        Array.prototype.forEach.call(row.querySelectorAll('.koku-cites [data-era]'), function (li) {
          li.hidden = on_.indexOf(li.dataset.era) < 0;
        });
        var dot = row.querySelector('.koku-track__dot');
        dot.hidden = !on;
        if (on) {
          place(dot, ln.alone);
          dot.style.setProperty('--size', (8 + 12 * Math.sqrt(ln.weight)).toFixed(1) + 'px');
          dot.title = ln.name + ': ' + money(ln.alone) + ' alone, ' + pct(ln.weight) + ' of the weight';
        }
      });
      history.replaceState(null, '', link(st));
    }

    // The goods table's axis header sticks just under the app nav, whose height varies by width.
    var nav = document.querySelector('.app-nav');
    function navHeight() {
      document.documentElement.style.setProperty('--koku-nav-h', (nav ? nav.offsetHeight : 0) + 'px');
    }
    navHeight();
    window.addEventListener('resize', navHeight);

    // The bar repeats the goods figures, so it shows only once the goods card is out of view.
    var bar = form.querySelector('.koku-sticky');
    var card = form.querySelector('.koku-reading--goods');
    if (bar && card && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        bar.classList.toggle('koku-sticky--shown', !entries[0].isIntersecting);
      }).observe(card);
    }

    form.addEventListener('submit', function (e) { e.preventDefault(); render(); });
    form.addEventListener('input', function (e) {
      if (e.target.matches('input[type="number"], input[type="text"]')) render();
    });
    form.addEventListener('change', function (e) {
      if (e.target === basketSel) {
        var goods = data.baskets[basketSel.value].goods;
        rows.forEach(function (row) {
          var q = goods[row.dataset.good] || 0;
          box(row).checked = q > 0;
          box(row).value = String(q || row.dataset.default);
        });
      }
      render();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(typeof window !== 'undefined' ? window : globalThis);
