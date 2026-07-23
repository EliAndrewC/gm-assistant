/* test-history.js - Node unit tests for history.js (the pure persistence
 * logic). Run inside the container - no GNOME required:
 *
 *   node --test scripts/temperature-widget/test-history.js
 *
 * The extension's IO and rendering can only be checked on the laptop (see
 * CLAUDE.md), but everything in history.js is pure and covered here.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const H = require('./history.js');

test('parseHistoryLine accepts a well-formed sample', () => {
    assert.deepStrictEqual(H.parseHistoryLine('{"t":1000,"c":71.2}'), [1000, 71.2]);
    assert.deepStrictEqual(H.parseHistoryLine('  {"t":1000,"c":71.2}  '), [1000, 71.2]);
});

test('parseHistoryLine rejects blank, malformed, and incomplete lines', () => {
    for (const bad of [
        '', '   ', '\n',
        'not json', '{',                       // unparseable
        '{"t":1000}', '{"c":71.2}',            // missing a field
        '{"t":"x","c":71.2}', '{"t":1000,"c":"x"}', // wrong types
        '{"t":1000,"c":null}', 'null', '[]',   // no usable object
        '{"t":1000,"c":' + JSON.stringify(Infinity) + '}', // -> null (JSON has no Infinity)
    ]) {
        assert.strictEqual(H.parseHistoryLine(bad), null, `should reject: ${bad}`);
    }
    // Non-finite numbers that DO parse as JSON must still be rejected.
    assert.strictEqual(H.parseHistoryLine('{"t":1e999,"c":50}'), null); // 1e999 -> Infinity
});

test('parseHistory skips junk lines and keeps good ones in order', () => {
    const text = [
        '{"t":1,"c":40}',
        'garbage',
        '',
        '{"t":2,"c":41}',
        '{"t":3}',            // dropped
        '{"t":4,"c":42.5}',
    ].join('\n');
    assert.deepStrictEqual(H.parseHistory(text), [[1, 40], [2, 41], [4, 42.5]]);
});

test('serializeSample rounds time to int and temp to 0.1 C, ends in newline', () => {
    assert.strictEqual(H.serializeSample(1000.7, 71.249), '{"t":1001,"c":71.2}\n');
    assert.strictEqual(H.serializeSample(1000, 71.25), '{"t":1000,"c":71.3}\n'); // .25 -> .3
});

test('serializeSample records utilization as an integer percent when usable', () => {
    assert.strictEqual(H.serializeSample(1000, 71.2, 42.6), '{"t":1000,"c":71.2,"u":43}\n');
    assert.strictEqual(H.serializeSample(1000, 71.2, 0), '{"t":1000,"c":71.2,"u":0}\n');
    // No usable utilization -> the field is simply absent, never a sentinel.
    for (const missing of [undefined, null, NaN, Infinity, '42']) {
        assert.strictEqual(H.serializeSample(1000, 71.2, missing),
            '{"t":1000,"c":71.2}\n', `should omit u for: ${missing}`);
    }
});

test('parseHistoryLine carries a valid u and drops an invalid one', () => {
    assert.deepStrictEqual(
        H.parseHistoryLine('{"t":1000,"c":71.2,"u":43}'), [1000, 71.2, 43]);
    // A bad u never invalidates the temperature sample (old lines have no u
    // at all; a corrupt one degrades to the same shape).
    assert.deepStrictEqual(
        H.parseHistoryLine('{"t":1000,"c":71.2,"u":"x"}'), [1000, 71.2]);
    assert.deepStrictEqual(
        H.parseHistoryLine('{"t":1000,"c":71.2,"u":1e999}'), [1000, 71.2]);
});

test('serialize -> parse round-trips a history, with and without u', () => {
    const samples = [[1, 40], [2, 41.5, 55], [3, 99.9, 0]];
    assert.deepStrictEqual(H.parseHistory(H.serializeHistory(samples)), samples);
});

test('serializeHistory of an empty list is the empty string', () => {
    assert.strictEqual(H.serializeHistory([]), '');
});

test('pruneByAge keeps the cutoff sample (inclusive) and drops older ones', () => {
    const now = 10_000;
    const maxAge = 5_000; // cutoff = 5000
    const samples = [[4_999, 1], [5_000, 2], [5_001, 3], [10_000, 4]];
    assert.deepStrictEqual(
        H.pruneByAge(samples, now, maxAge),
        [[5_000, 2], [5_001, 3], [10_000, 4]]);
});

test('median discards a lone outlier and does not mutate its input', () => {
    assert.strictEqual(H.median([48, 100, 46]), 48);   // glitch high spike rejected
    assert.strictEqual(H.median([100, 48, 100]), 100);  // glitch low dip rejected
    assert.strictEqual(H.median([50]), 50);
    assert.strictEqual(H.median([50, 60]), 55);          // even length -> mean of middle two
    const input = [3, 1, 2];
    assert.strictEqual(H.median(input), 2);
    assert.deepStrictEqual(input, [3, 1, 2], 'input must be untouched');
});

// --- CPU utilization from /proc/stat ----------------------------------------

// A realistic /proc/stat head: aggregate line, then per-core lines that must
// be ignored (no whitespace after "cpu" in "cpu0").
const PROC_STAT =
    'cpu  100 20 30 800 50 0 10 5 0 0\n' +
    'cpu0 50 10 15 400 25 0 5 2 0 0\n' +
    'intr 12345\n';

test('parseProcStatCpu reads the aggregate line only', () => {
    // total = 100+20+30+800+50+0+10+5 = 1015; idle+iowait = 850; busy = 165.
    assert.deepStrictEqual(H.parseProcStatCpu(PROC_STAT), { busy: 165, total: 1015 });
});

test('parseProcStatCpu tolerates a short line (bare minimum 4 fields)', () => {
    assert.deepStrictEqual(
        H.parseProcStatCpu('cpu 10 0 10 80'), { busy: 20, total: 100 });
});

test('parseProcStatCpu rejects missing or malformed aggregate lines', () => {
    for (const bad of ['', 'cpu0 1 2 3 4', 'cpu  a b c d', 'cpu 1 2 3', null, undefined]) {
        assert.strictEqual(H.parseProcStatCpu(bad), null, `should reject: ${bad}`);
    }
});

test('cpuUtilizationPct averages the delta between two snapshots', () => {
    const prev = { busy: 100, total: 1000 };
    assert.strictEqual(H.cpuUtilizationPct(prev, { busy: 150, total: 1100 }), 50);
    assert.strictEqual(H.cpuUtilizationPct(prev, { busy: 100, total: 1100 }), 0);
    assert.strictEqual(H.cpuUtilizationPct(prev, { busy: 200, total: 1100 }), 100);
    // Rounding overshoot is clamped to 100.
    assert.strictEqual(H.cpuUtilizationPct(prev, { busy: 201, total: 1100 }), 100);
});

test('cpuUtilizationPct returns null on missing, stale, or reset counters', () => {
    const snap = { busy: 100, total: 1000 };
    assert.strictEqual(H.cpuUtilizationPct(null, snap), null);
    assert.strictEqual(H.cpuUtilizationPct(snap, null), null);
    assert.strictEqual(H.cpuUtilizationPct(snap, snap), null);           // no elapsed time
    assert.strictEqual(H.cpuUtilizationPct(snap, { busy: 50, total: 1100 }), null); // reset
});

// --- excluded-sensor diagnostic archive ------------------------------------

test('serializeExcludedSample rounds t to int and values to 0.1 C', () => {
    assert.strictEqual(
        H.serializeExcludedSample(1000.7, { 'Core 8': 100.24, 'Core 12': 58.06 }),
        '{"t":1001,"v":{"Core 8":100.2,"Core 12":58.1}}\n');
});

test('serializeExcludedSample drops non-finite sensor values', () => {
    assert.strictEqual(
        H.serializeExcludedSample(5, { 'Core 8': Infinity, 'Core 12': 60 }),
        '{"t":5,"v":{"Core 12":60}}\n');
});

test('parseExcludedLine round-trips and rejects malformed lines', () => {
    assert.deepStrictEqual(
        H.parseExcludedLine('{"t":1001,"v":{"Core 8":100.2}}'),
        [1001, { 'Core 8': 100.2 }]);
    for (const bad of [
        '', '  ', 'not json', '{',
        '{"t":1001}',                       // no v
        '{"v":{"Core 8":100}}',             // no t
        '{"t":"x","v":{}}',                 // t wrong type
        '{"t":1e999,"v":{}}',               // t -> Infinity
        '{"t":1,"v":42}',                   // v not an object
    ]) {
        assert.strictEqual(H.parseExcludedLine(bad), null, `should reject: ${bad}`);
    }
    // Individual non-finite sensor values are dropped, not fatal.
    assert.deepStrictEqual(
        H.parseExcludedLine('{"t":1,"v":{"Core 8":1e999,"Core 12":55}}'),
        [1, { 'Core 12': 55 }]);
});

test('parseExcluded skips junk and serialize -> parse round-trips', () => {
    const samples = [[1, { 'Core 8': 100 }], [2, { 'Core 8': 55, 'Core 12': 56 }]];
    assert.deepStrictEqual(H.parseExcluded(H.serializeExcludedHistory(samples)), samples);
    // pruneByAge works unchanged on the [t, values] shape.
    assert.deepStrictEqual(H.pruneByAge(samples, 2, 0), [[2, { 'Core 8': 55, 'Core 12': 56 }]]);
});

// --- slewGate: the burst-glitch defense the median cannot provide ----------

const GATE = { maxJumpC: 20, confirmSamples: 3 };

// Drives a sequence of readings through slewGate, threading state, and returns
// the accepted value after each reading - the metric the gauge would show.
function runGate(readings, opts = GATE, start = { accepted: null, candidate: null, count: 0 }) {
    let state = start;
    const out = [];
    for (const r of readings) {
        state = H.slewGate(state, r, opts);
        out.push(state.accepted);
    }
    return out;
}

test('slewGate trusts the first real reading', () => {
    assert.deepStrictEqual(
        H.slewGate({ accepted: null, candidate: null, count: 0 }, 52, GATE),
        { accepted: 52, candidate: null, count: 0 });
});

test('slewGate passes an in-band reading through with no lag', () => {
    // Gradual real drift - every step within maxJumpC - is accepted each poll.
    assert.deepStrictEqual(runGate([50, 58, 66, 72, 68]), [50, 58, 66, 72, 68]);
});

test('slewGate holds through a 2-poll burst the median lets slip', () => {
    // The exact failure observed 2026-07-22: the median of a 2-poll raw burst
    // still emits two high samples (50,100,100,50); the gate must ignore them.
    assert.deepStrictEqual(
        runGate([50, 50, 100, 100, 50, 50]),
        [50, 50, 50, 50, 50, 50]);
});

test('slewGate ignores an isolated downward glitch too', () => {
    // Low glitches were seen as well (stray 24/30 among ~50s).
    assert.deepStrictEqual(runGate([50, 50, 24, 50, 50]), [50, 50, 50, 50, 50]);
});

test('slewGate accepts a genuinely sustained excursion after confirmSamples', () => {
    // A real jump that HOLDS is believed on the 3rd consecutive out-of-band poll.
    assert.deepStrictEqual(
        runGate([50, 95, 95, 95, 95]),
        [50, 50, 50, 95, 95]);
});

test('slewGate restarts the streak when an excursion is not sustained', () => {
    // Two highs, then back to baseline, then two highs again: never 3 in a row,
    // so the metric never leaves baseline.
    assert.deepStrictEqual(
        runGate([50, 100, 100, 50, 100, 100, 50]),
        [50, 50, 50, 50, 50, 50, 50]);
});

test('slewGate follows a rising ramp toward a new plateau', () => {
    // A fast ramp whose per-poll steps exceed maxJumpC is gated until it settles,
    // then accepted - never permanently hidden.
    assert.deepStrictEqual(
        runGate([50, 75, 95, 100, 100]),
        [50, 50, 50, 100, 100]);
});

test('slewGate blanks on a failed read and re-trusts the next one', () => {
    assert.deepStrictEqual(
        H.slewGate({ accepted: 88, candidate: null, count: 0 }, null, GATE),
        { accepted: null, candidate: null, count: 0 });
    // After the blank, the next reading is treated as a fresh first read.
    assert.deepStrictEqual(runGate([50, null, 90]), [50, null, 90]);
});

// --- spatialMetric: reject a per-core sensor stuck far above the die --------

const SPAT = { maxAboveMedianC: 20 };

test('spatialMetric returns the hottest core when the die is uniform', () => {
    // Normal spread - nothing is an outlier, so the real hottest wins.
    assert.strictEqual(H.spatialMetric([54, 55, 56, 58, 60], SPAT), 60);
});

test('spatialMetric drops a lone stuck-high core (the Core 8/12 glitch)', () => {
    // Idle die at ~55C with one sensor pinned to 100 - the exact 2026-07-22
    // signature. The 100 is a ~44C outlier above the median; it is discarded and
    // the metric reflects the real die temperature.
    assert.strictEqual(H.spatialMetric([53, 55, 100, 58, 56, 100], SPAT), 58);
});

test('spatialMetric keeps a genuine all-core hot event', () => {
    // Real load heats the whole die together (all within the band of the median),
    // so nothing is dropped and the gauge still sees the true 101.
    assert.strictEqual(H.spatialMetric([88, 90, 92, 100, 101, 97], SPAT), 101);
});

test('spatialMetric ignores null/non-finite readings', () => {
    assert.strictEqual(H.spatialMetric([null, 55, 56, undefined, 57], SPAT), 57);
});

test('spatialMetric returns null when there are no usable readings', () => {
    assert.strictEqual(H.spatialMetric([], SPAT), null);
    assert.strictEqual(H.spatialMetric([null, undefined], SPAT), null);
});

test('spatialMetric handles a single core and keeps the median itself', () => {
    assert.strictEqual(H.spatialMetric([72], SPAT), 72);
    // Even-length: median is the mean of the two middle values; the lower-middle
    // core always satisfies the band, so the kept set is never empty.
    assert.strictEqual(H.spatialMetric([50, 100], SPAT), 50);
});

// --- barSeverity: gauge color with downward hysteresis ----------------------

// Mujina's effective thresholds: warn 90, bad 100, hysteresis 4.
const SEV = { warnAt: 90, badAt: 100, hysteresis: 4 };

// Threads a metric sequence through barSeverity and returns the severity the
// bar would show after each poll.
function runSeverity(metrics, start = 0) {
    let sev = start;
    return metrics.map(m => (sev = H.barSeverity(sev, m, SEV)));
}

test('barSeverity maps the plain thresholds on the way up', () => {
    assert.deepStrictEqual(runSeverity([50, 89.9, 90, 99.9, 100]), [0, 0, 1, 1, 2]);
});

test('barSeverity holds the color while hovering just under a threshold', () => {
    // The motivating flip-flop case: oscillating 89-91 stays orange - the
    // color only drops once no longer above the floor (warnAt - hysteresis,
    // here 86: 86.1 still holds, exactly 86 releases).
    assert.deepStrictEqual(
        runSeverity([91, 89, 91, 89, 86.1, 86]),
        [1, 1, 1, 1, 1, 0]);
});

test('barSeverity red releases below badAt - hysteresis', () => {
    assert.deepStrictEqual(runSeverity([101, 97, 96.1], 0), [2, 2, 2]);
    // 96 is exactly the floor (badAt - 4): not ABOVE it, so red releases; 95
    // is in the plain orange band.
    assert.deepStrictEqual(runSeverity([101, 96], 0), [2, 1]);
});

test('barSeverity drops straight from red to green when unambiguously cool', () => {
    // Hysteresis holds a color near ITS threshold; it never staircases a big
    // fall through orange.
    assert.deepStrictEqual(runSeverity([101, 55]), [2, 0]);
});

test('barSeverity treats no reading as normal', () => {
    assert.strictEqual(H.barSeverity(2, null, SEV), 0);
});

// --- notifyGate: per-severity debounce + recovery dismissal -----------------

// The shipped tiers: normal resets in 3 polls, warn must hold 20 polls
// (~60 s), bad fires after 3 (~10 s). See CONFIRM_SAMPLES_BY_SEV.
const NOTIFY = { confirmSamplesBySev: [3, 20, 3] };

// Threads a severity sequence through notifyGate and returns the non-null
// actions as [pollIndex, action] pairs - the IO the extension would perform.
function runNotify(sevs, state = { debSev: null, debCount: 0, confirmedSev: 0 }) {
    const actions = [];
    sevs.forEach((sev, i) => {
        state = H.notifyGate(state, sev, NOTIFY);
        if (state.action !== null)
            actions.push([i, state.action]);
    });
    return { actions, state };
}

test('notifyGate fires bad on the 3rd consecutive poll, exactly once', () => {
    assert.deepStrictEqual(
        runNotify([0, 0, 2, 2, 2, 2, 2]).actions,
        [[4, 'notify']]);
});

test('notifyGate stays silent through a routine turbo burst into orange', () => {
    // The 2026-07-23 RCA finding encoded as behavior: real bursty load spikes
    // the die into the warning range for 10-30 s (3-10 polls) and self-limits
    // via throttling. That must produce NO notification - only a full 60 s
    // (20 polls) continuously in warn earns the popup.
    const burst = [0, 0, ...Array(10).fill(1), 0, 0, 0];
    assert.deepStrictEqual(runNotify(burst).actions, []);
});

test('notifyGate fires warn after 20 consecutive polls (~60 s)', () => {
    const sustained = [0, ...Array(20).fill(1)];
    assert.deepStrictEqual(runNotify(sustained).actions, [[20, 'notify']]);
});

test('notifyGate restarts the warn streak on any severity change', () => {
    // 19 polls of warn, one green poll, 19 more: never 20 in a row -> silent.
    const flap = [...Array(19).fill(1), 0, ...Array(19).fill(1)];
    assert.deepStrictEqual(runNotify(flap).actions, []);
});

test('notifyGate escalates from confirmed warn to bad on the fast tier', () => {
    // A sustained warm spell that then hits the red band: the red popup still
    // arrives ~10 s after crossing, not 60.
    const seq = [...Array(20).fill(1), 2, 2, 2];
    assert.deepStrictEqual(
        runNotify(seq).actions,
        [[19, 'notify'], [22, 'notify']]);
});

test('notifyGate dismisses once recovery from a notified state is confirmed', () => {
    // Warning shown, then back to green: 3 consecutive normal polls withdraw
    // the banner (the state it reported is gone), exactly once - continued
    // green stays silent.
    const seq = [...Array(20).fill(1), 0, 0, 0, 0, 0];
    assert.deepStrictEqual(
        runNotify(seq).actions,
        [[19, 'notify'], [22, 'dismiss']]);
});

test('notifyGate never dismisses when nothing was notified', () => {
    // A burst too short to notify, then green: there is no banner to clean up.
    assert.deepStrictEqual(runNotify([1, 1, 0, 0, 0, 0]).actions, []);
});

test('notifyGate re-notifies a fresh episode after a dismissal', () => {
    const episode = [...Array(20).fill(1), 0, 0, 0];
    const first = runNotify(episode);
    assert.deepStrictEqual(first.actions, [[19, 'notify'], [22, 'dismiss']]);
    const second = runNotify(episode, first.state);
    assert.deepStrictEqual(second.actions, [[19, 'notify'], [22, 'dismiss']]);
});

test('notifyGate downgrade bad -> sustained warn keeps the banner but re-arms', () => {
    // Red confirmed, then a sustained warn plateau: no new action (the banner
    // stays - its "look at this" is still live), but the confirmed level
    // drops to warn, so a later return to red notifies again.
    const seq = [2, 2, 2, ...Array(20).fill(1), 2, 2, 2];
    assert.deepStrictEqual(
        runNotify(seq).actions,
        [[2, 'notify'], [25, 'notify']]);
});

test('lock serialize -> parse round-trips', () => {
    assert.deepStrictEqual(
        H.parseLock(H.serializeLock(4242, 'boot-abc', 1234.9)),
        { pid: 4242, bootId: 'boot-abc', ts: 1235 });
});

test('parseLock rejects blank and malformed content', () => {
    for (const bad of [
        '', '   ', null, undefined,
        'nope', '{',
        '{"pid":1,"bootId":"b"}',              // missing ts
        '{"pid":"1","bootId":"b","ts":1}',     // pid wrong type
        '{"pid":1,"bootId":2,"ts":1}',         // bootId wrong type
        '{"pid":1,"bootId":"b","ts":"1"}',     // ts wrong type
    ]) {
        assert.strictEqual(H.parseLock(bad), null, `should reject: ${bad}`);
    }
});

test('canClaim: no lock -> claimable', () => {
    assert.strictEqual(
        H.canClaim(null, 100, { staleMs: 12_000, myPid: 5, currentBootId: 'b', writerPidAlive: true }),
        true);
});

test('canClaim: the lock is already mine (same boot) -> claimable', () => {
    const lock = { pid: 5, bootId: 'b', ts: 100 };
    assert.strictEqual(
        H.canClaim(lock, 200, { staleMs: 12_000, myPid: 5, currentBootId: 'b', writerPidAlive: true }),
        true);
});

test('canClaim: same pid but a different boot -> claimable (pid reuse)', () => {
    const lock = { pid: 5, bootId: 'old-boot', ts: 100 };
    assert.strictEqual(
        H.canClaim(lock, 200, { staleMs: 12_000, myPid: 5, currentBootId: 'new-boot', writerPidAlive: true }),
        true);
});

test('canClaim: a stale heartbeat -> claimable even if the pid still exists', () => {
    const lock = { pid: 9, bootId: 'b', ts: 100 };
    assert.strictEqual(
        H.canClaim(lock, 100 + 12_001, { staleMs: 12_000, myPid: 5, currentBootId: 'b', writerPidAlive: true }),
        true);
});

test('canClaim: holder process gone -> claimable', () => {
    const lock = { pid: 9, bootId: 'b', ts: 100 };
    assert.strictEqual(
        H.canClaim(lock, 200, { staleMs: 12_000, myPid: 5, currentBootId: 'b', writerPidAlive: false }),
        true);
});

test('canClaim: another writer alive and fresh -> NOT claimable', () => {
    const lock = { pid: 9, bootId: 'b', ts: 100 };
    assert.strictEqual(
        H.canClaim(lock, 200, { staleMs: 12_000, myPid: 5, currentBootId: 'b', writerPidAlive: true }),
        false);
});
