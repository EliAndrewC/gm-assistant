/* What's a koku worth? (/money/koku, feature 221).
 *
 * `compute` is the browser twin of l7r/money/basket.py `reading`: tests/test_money_js.py runs it
 * under node against the Python on several states, so change the two together. The rest wires the
 * form: every change recomputes the readings and rewrites the link (l7r/money/web.py documents the
 * parameters), so the link always reopens what is on screen.
 */
(function (root) {
  'use strict';

  function compute(data, state) {
    var basket = data.baskets[state.basket];
    var snap = data.snapshots[state.snapshot];
    var qty = Object.assign({}, basket.goods, state.q || {});
    var lines = [];
    Object.keys(qty).forEach(function (good) {
      var opts = snap.goods[good] || [];
      var pick = opts.length ? opts[Math.min(Math.max((state.x || {})[good] || 0, 0), opts.length - 1)] : null;
      lines.push(line(good, data.goods[good].name, qty[good], pick ? pick.dollars : null, data.goods[good].silver));
    });
    (state.custom || []).forEach(function (c, i) {
      lines.push(line('custom-' + i, c.name, c.qty, c.dollars, c.silver));
    });
    var dollars = 0;
    var silver = 0;
    lines.forEach(function (ln) {
      dollars += ln.dollars;
      silver += ln.silver;
    });
    return {
      lines: lines,
      dollars: dollars,
      silver: silver,
      per_koku: silver ? dollars / silver * data.koku_kg * data.rice_ref : 0,
      left_out: lines.filter(function (ln) { return ln.quantity > 0 && !ln.counted; })
        .map(function (ln) { return ln.name; }),
    };
  }

  function line(good, name, quantity, dpu, spu) {
    var counted = quantity > 0 && !!dpu && !!spu;
    return {
      good: good,
      name: name,
      quantity: quantity,
      counted: counted,
      dollars: counted ? quantity * dpu : 0,
      silver: counted ? quantity * spu : 0,
    };
  }

  function pct(part, whole) {
    return part / whole < 0.005 ? '<1%' : Math.round(part / whole * 100) + '%';
  }

  // The twin of web.py `drivers`.
  function drivers(r) {
    var counted = r.lines.filter(function (ln) { return ln.counted; });
    if (!counted.length) return 'Nothing in the basket is priced on both sides.';
    function top(side, total) {
      var best = counted.reduce(function (a, b) { return b[side] > a[side] ? b : a; });
      var share = pct(best[side], total);
      var tied = counted.filter(function (ln) { return pct(ln[side], total) === share; })
        .map(function (ln) { return ln.name; });
      return tied.join(' and ') + ' (' + share + (tied.length > 1 ? ' each' : '') + ')';
    }
    return "Largest share of today's cost: " + top('dollars', r.dollars) + '. Largest share of the 1740s cost: ' + top('silver', r.silver) + '.';
  }

  root.kokuCompute = compute;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { compute: compute, drivers: drivers };
  }
  if (typeof document === 'undefined') return;

  function money(x, places) {
    return '$' + x.toLocaleString('en-US', { minimumFractionDigits: places, maximumFractionDigits: places });
  }

  function share(part, whole) {
    if (!whole || !part) return '-';
    var pct = part / whole * 100;
    return pct < 0.5 ? '<1%' : Math.round(pct) + '%';
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
    var snapSel = form.querySelector('[data-in="snapshot"]');
    var rows = Array.prototype.slice.call(form.querySelectorAll('tr[data-good]'));
    var customs = Array.prototype.slice.call(form.querySelectorAll('[data-custom]'));

    function qtyInput(row) { return row.querySelector('input[type="number"]'); }

    function state() {
      var basket = data.baskets[basketSel.value];
      var st = { basket: basketSel.value, snapshot: snapSel.value, q: {}, x: {}, custom: [], c: [] };
      rows.forEach(function (row) {
        var good = row.dataset.good;
        var q = number(qtyInput(row));
        var dflt = basket.goods[good] || 0;
        if (q !== null && q !== dflt) st.q[good] = q;
        var sub = row.querySelector('input[type="radio"]:checked');
        if (sub && sub.value !== '0') st.x[good] = parseInt(sub.value, 10);
      });
      customs.forEach(function (div, i) {
        var get = function (part) { return div.querySelector('[data-part="' + part + '"]'); };
        var name = get('name').value.trim();
        var raw = [name, get('unit').value.trim(), get('qty').value, get('silver').value, get('dollars').value];
        div.querySelector('input[type="hidden"]').value = name ? raw.join('|') : '';
        st.c[i] = name ? raw.join('|') : '';
        if (name) {
          st.custom.push({ name: name, qty: number(get('qty')) || 0, silver: number(get('silver')), dollars: number(get('dollars')) });
        }
      });
      return st;
    }

    function link(st) {
      var p = new URLSearchParams();
      if (st.basket !== data.standard) p.set('b', st.basket);
      if (st.snapshot !== data.newest) p.set('s', st.snapshot);
      Object.keys(st.q).forEach(function (g) { p.set('q_' + g, String(st.q[g])); });
      Object.keys(st.x).forEach(function (g) { p.set('x_' + g, String(st.x[g])); });
      st.c.forEach(function (c, i) { if (c) p.set('c' + (i + 1), c); });
      var qs = p.toString();
      return location.pathname + (qs ? '?' + qs : '');
    }

    function render() {
      var st = state();
      var r = compute(data, st);
      form.querySelector('[data-out="per-koku"]').textContent = money(r.per_koku, 0);
      form.querySelector('[data-out="per-koku-sticky"]').textContent = money(r.per_koku, 0);
      form.querySelector('[data-out="drivers"]').textContent = drivers(r);
      var customLines = r.lines.filter(function (ln) { return ln.good.indexOf('custom-') === 0; });
      var next = 0;
      customs.forEach(function (div, i) {
        var status = div.querySelector('[data-out="custom-status"]');
        if (!st.c[i]) { status.textContent = ''; return; }
        var ln = customLines[next++];
        status.textContent = ln.counted
          ? 'Counts for ' + pct(ln.dollars, r.dollars) + " of today's cost and " + pct(ln.silver, r.silver) + ' of the 1740s cost.'
          : 'Not counted until all five are filled in.';
      });
      form.querySelector('[data-out="description"]').textContent = data.baskets[st.basket].description;
      var left = form.querySelector('[data-out="left-out"]');
      var missing = r.lines.filter(function (ln) {
        return ln.quantity > 0 && !ln.counted && ln.good.indexOf('custom-') !== 0;
      }).map(function (ln) { return ln.name; });
      left.hidden = !missing.length;
      left.textContent = 'Not priced at this date, so left out: ' + missing.join(', ') + '.';
      var byGood = {};
      r.lines.forEach(function (ln) { byGood[ln.good] = ln; });
      rows.forEach(function (row) {
        var ln = byGood[row.dataset.good];
        var on = !!(ln && ln.counted);
        row.classList.toggle('koku-row--off', !on);
        row.querySelector('.koku-on').checked = (number(qtyInput(row)) || 0) > 0;
        var q = number(qtyInput(row)) || 0;
        row.querySelector('[data-out="share"]').textContent = on
          ? share(ln.dollars, r.dollars) + ' / ' + share(ln.silver, r.silver)
          : (q > 0 ? 'left out: no price' : 'not counted');
      });
      history.replaceState(null, '', link(st));
    }

    // The bar repeats the goods figure, so it shows only once the goods card is out of view.
    var bar = form.querySelector('.koku-sticky');
    var card = form.querySelector('.koku-reading--goods');
    if (bar && card && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        bar.classList.toggle('koku-sticky--shown', !entries[0].isIntersecting);
      }).observe(card);
    }

    function sourceLink(href) {
      var a = document.createElement('a');
      a.className = 'koku-link';
      a.textContent = 'source';
      a.href = href;
      return a;
    }

    function rebuildPrices() {
      var snap = data.snapshots[snapSel.value];
      rows.forEach(function (row) {
        var good = row.dataset.good;
        var opts = snap.goods[good] || [];
        var cell = row.querySelector('[data-out="now"]');
        var prev = row.querySelector('input[type="radio"]:checked');
        var keep = prev ? parseInt(prev.value, 10) : 0;
        var unit = data.goods[good].unit;
        cell.textContent = '';
        keep = Math.min(keep, opts.length - 1);
        if (opts.length > 1) {
          var set = document.createElement('fieldset');
          set.className = 'koku-subs';
          set.setAttribute('aria-label', "Where today's price of " + data.goods[good].name.toLowerCase() + ' comes from');
          opts.forEach(function (o, i) {
            var label = document.createElement('label');
            label.className = 'koku-sub';
            var radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'x_' + good;
            radio.value = String(i);
            radio.checked = i === keep;
            var text = document.createElement('span');
            var price = document.createElement('span');
            price.className = 'koku-price';
            price.textContent = money(o.dollars, 2) + ' a ' + unit;
            var as = document.createElement('span');
            as.className = 'koku-priced-as';
            as.textContent = o.priced_as + ' ';
            as.appendChild(sourceLink(o.link));
            text.appendChild(price);
            text.appendChild(document.createTextNode(' '));
            text.appendChild(as);
            label.appendChild(radio);
            label.appendChild(text);
            set.appendChild(label);
          });
          cell.appendChild(set);
        } else if (opts.length) {
          var price = document.createElement('span');
          price.className = 'koku-price';
          price.textContent = money(opts[0].dollars, 2) + ' a ' + unit;
          var as = document.createElement('span');
          as.className = 'koku-priced-as';
          as.textContent = opts[0].priced_as + ' ';
          as.appendChild(sourceLink(opts[0].link));
          cell.appendChild(price);
          cell.appendChild(document.createTextNode(' '));
          cell.appendChild(as);
        } else {
          var none = document.createElement('span');
          none.className = 'koku-missing';
          none.textContent = 'not priced at this date';
          cell.appendChild(none);
        }
      });
    }

    form.addEventListener('submit', function (e) { e.preventDefault(); render(); });
    form.addEventListener('input', function (e) {
      if (e.target.matches('input[type="number"], input[type="text"]')) render();
    });
    form.addEventListener('change', function (e) {
      var t = e.target;
      if (t === basketSel) {
        var goods = data.baskets[basketSel.value].goods;
        rows.forEach(function (row) {
          var q = goods[row.dataset.good] || 0;
          qtyInput(row).value = String(q);
          if (q) row.dataset.default = String(q);
        });
      } else if (t === snapSel) {
        rebuildPrices();
      } else if (t.classList.contains('koku-on')) {
        var row = t.closest('tr');
        qtyInput(row).value = t.checked ? row.dataset.default : '0';
      }
      render();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(typeof window !== 'undefined' ? window : globalThis);
