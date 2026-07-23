/* history.js - pure logic for the CPU Temperature Bar's on-disk history.
 *
 * Split out from extension.js so it can be unit-tested under plain Node
 * (see test-history.js): nothing in here touches GNOME, the filesystem, or
 * the clock. The extension supplies the IO and `now`; this module only
 * parses, serializes, prunes, and decides who gets to write.
 *
 * Loadable from BOTH environments: GJS exposes top-level `function`
 * declarations as properties of the imported module (so extension.js does
 * `Me.imports.history.parseHistory(...)`), and the `module.exports` tail
 * makes the same names available under Node. `typeof module` is a safe guard
 * (no ReferenceError on an undefined identifier), so the tail is simply
 * skipped inside GJS.
 */
'use strict';

// --- Sample history: one JSON object per line ------------------------------
// [ms-since-epoch, degrees C, optional avg CPU %].

// Parses one line to [t, c] or [t, c, u], or null if blank/malformed.
// Malformed lines are skipped rather than fatal - a half-written final line
// (writer killed mid-append) must not poison the whole history. The `u` field
// (average CPU utilization % since the previous sample) is OPTIONAL: lines
// written before 2026-07-23 lack it, and a failed /proc/stat read omits it,
// so a missing or invalid `u` never invalidates the temperature sample.
function parseHistoryLine(line) {
    const s = String(line).trim();
    if (!s)
        return null;
    let obj;
    try {
        obj = JSON.parse(s);
    } catch (e) {
        return null;
    }
    if (!obj || typeof obj.t !== 'number' || typeof obj.c !== 'number')
        return null;
    if (!isFinite(obj.t) || !isFinite(obj.c))
        return null;
    if (typeof obj.u === 'number' && isFinite(obj.u))
        return [obj.t, obj.c, obj.u];
    return [obj.t, obj.c];
}

function parseHistory(text) {
    const out = [];
    for (const line of String(text).split('\n')) {
        const parsed = parseHistoryLine(line);
        if (parsed !== null)
            out.push(parsed);
    }
    return out;
}

// Temperatures are stored to 0.1 C - finer precision than the sensors deliver
// and than any graph pixel can show, so it just wastes bytes. Utilization is
// stored as an integer percent for the same reason, and only when it is a
// usable number - absence, not a sentinel, marks "could not read".
function serializeSample(t, c, u) {
    const out = { t: Math.round(t), c: Math.round(c * 10) / 10 };
    if (typeof u === 'number' && isFinite(u))
        out.u = Math.round(u);
    return JSON.stringify(out) + '\n';
}

function serializeHistory(samples) {
    return samples.map(([t, c, u]) => serializeSample(t, c, u)).join('');
}

// --- CPU utilization: /proc/stat counters -> percent busy -------------------
//
// Each persisted sample carries the average CPU utilization since the previous
// one (the `u` field), because utilization is THE discriminator between a
// genuine hot event and a stuck sensor: real heat comes with real load, a
// glitch reads 100 C on an idle machine. Learned 2026-07-23, second RCA round:
// deciding whether that morning's 91-98 C warnings were real required an
// external temps+load capture precisely because the archive recorded no load
// data. With `u` on every line the archive answers "was the machine actually
// working?" by itself. Pure parsing/arithmetic here; the extension supplies
// the /proc/stat text and keeps the previous snapshot between persists.

// Parses the aggregate "cpu " line of /proc/stat into cumulative jiffy
// counters { busy, total }, or null if there is no parseable aggregate line.
// Fields: user nice system idle iowait irq softirq steal (guest time is
// already folded into user/nice by the kernel). Idle means idle + iowait;
// everything else is busy. Only the "cpu " line matters - the per-core
// "cpuN" lines never match (no whitespace after "cpu").
function parseProcStatCpu(text) {
    for (const line of String(text ?? '').split('\n')) {
        const m = line.match(/^cpu\s+(.*)$/);
        if (!m)
            continue;
        const nums = m[1].trim().split(/\s+/).map(Number);
        if (nums.length < 4 || nums.some(n => !isFinite(n)))
            return null;
        const [user, nice, system, idle, iowait = 0, irq = 0, softirq = 0, steal = 0] = nums;
        const total = user + nice + system + idle + iowait + irq + softirq + steal;
        return { busy: total - idle - iowait, total };
    }
    return null;
}

// Average utilization (integer percent, 0..100) between two /proc/stat
// snapshots, or null when either snapshot is missing, no time has elapsed,
// or the counters went backward (a reset - jiffies are cumulative, so a
// negative delta means the numbers cannot be trusted).
function cpuUtilizationPct(prev, cur) {
    if (!prev || !cur)
        return null;
    const busy = cur.busy - prev.busy;
    const total = cur.total - prev.total;
    if (!(total > 0) || busy < 0)
        return null;
    return Math.min(100, Math.round(100 * busy / total));
}

// --- Excluded-sensor diagnostic archive ------------------------------------
//
// Sensors named in KNOWN_BAD_SENSORS (extension.js) are dropped from the
// displayed/alarming metric, but their raw readings are still recorded here so
// a known-glitchy sensor can be inspected later WITHOUT ever driving the gauge
// (per the GM's ask 2026-07-22: quarantine the display, keep the data). This is
// a SEPARATE file from the metric archive (excluded.jsonl vs history.jsonl), so
// the metric archive's [t, c] shape and graph-seeding stay untouched. One line
// per persist: {"t": <ms>, "v": {"<label>": <°C>, ...}}. Kept in the same
// [t, rest] tuple shape as the sample history, so pruneByAge prunes it unchanged.

function serializeExcludedSample(t, values) {
    const v = {};
    for (const k of Object.keys(values)) {
        const n = values[k];
        if (typeof n === 'number' && isFinite(n))
            v[k] = Math.round(n * 10) / 10; // 0.1 C, same precision as the metric
    }
    return JSON.stringify({ t: Math.round(t), v }) + '\n';
}

// Parses one excluded line to [t, {label: °C, ...}], or null if blank/malformed.
// Same tolerance as parseHistoryLine: a half-written final line must not poison
// the whole file. Individual non-finite sensor values are dropped, not fatal.
function parseExcludedLine(line) {
    const s = String(line).trim();
    if (!s)
        return null;
    let obj;
    try {
        obj = JSON.parse(s);
    } catch (e) {
        return null;
    }
    if (!obj || typeof obj.t !== 'number' || !isFinite(obj.t))
        return null;
    if (!obj.v || typeof obj.v !== 'object')
        return null;
    const values = {};
    for (const k of Object.keys(obj.v)) {
        const n = obj.v[k];
        if (typeof n === 'number' && isFinite(n))
            values[k] = n;
    }
    return [obj.t, values];
}

function parseExcluded(text) {
    const out = [];
    for (const line of String(text).split('\n')) {
        const parsed = parseExcludedLine(line);
        if (parsed !== null)
            out.push(parsed);
    }
    return out;
}

function serializeExcludedHistory(samples) {
    return samples.map(([t, values]) => serializeExcludedSample(t, values)).join('');
}

// Median of a list of numbers. Used to despike the temperature metric: a
// median of the last few raw reads discards a lone spurious value outright
// (unlike a mean, which would average it in). Does not mutate the input.
function median(nums) {
    const sorted = [...nums].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

/* Slew/jump gate: the second despike stage, downstream of the median.
 *
 * Silicon has thermal mass, so the *true* CPU temperature cannot leap by tens
 * of degrees for a single 3 s poll and snap back - that shape is a bad sensor
 * read, not a temperature. A lone spike is already discarded by the median-of-3
 * upstream, but a run of 2+ CONSECUTIVE bad reads outvotes a 3-wide median and
 * slips through (observed 2026-07-22: the archive logged burst excursions to
 * 98-101 C while an ice-packed, cool-to-touch laptop sat at ~50 C). This gate
 * catches exactly that residual case.
 *
 * It refuses to MOVE the accepted metric to a level more than maxJumpC away
 * until that new level has HELD for confirmSamples consecutive polls. So a
 * brief burst is ignored - the metric holds its last good value - while a
 * genuine sustained excursion is accepted after confirmSamples polls. That
 * acceptance delay mirrors the notification debounce and is harmless: the
 * hardware's own thermal throttling, not this gauge, is the real safety net, so
 * a few seconds of lag on a real event costs nothing, and nothing is ever
 * permanently hidden. A normal gradual rise (a few degrees per poll, well
 * within maxJumpC) is in-band every poll and passes through with zero lag; only
 * a physically-impossible single-poll leap engages the gate.
 *
 * Pure and caller-driven: the extension owns the streak state and threads it
 * back in each poll.
 *
 *   state.accepted   last accepted metric (C), or null at startup / after a reset
 *   state.candidate  the pending out-of-band level being confirmed, or null
 *   state.count      consecutive polls that candidate has held
 *   reading          the newest (already median-smoothed) read, or null if the
 *                    sensor could not be read this poll
 *   opts.maxJumpC    largest per-poll change treated as physically plausible
 *   opts.confirmSamples  polls an out-of-band level must hold before it is believed
 *
 * Returns the next { accepted, candidate, count }; `accepted` is the value to
 * show and record this poll.
 */
function slewGate(state, reading, opts) {
    const { accepted, candidate, count } = state;
    const { maxJumpC, confirmSamples } = opts;
    // No reading this poll (sensor read failed): go blank and forget any pending
    // excursion, so the stream is judged fresh when reads resume. Matches the
    // caller's "null metric -> blank gauge" handling and the median's own reset.
    if (reading === null)
        return { accepted: null, candidate: null, count: 0 };
    // First real reading (startup, or the poll after a gap reset): nothing to
    // compare against, so trust it - refusing it would leave the gauge blank.
    if (accepted === null)
        return { accepted: reading, candidate: null, count: 0 };
    // Within a physically-plausible per-poll change: accept directly and clear
    // any half-built candidate. The common case - a real temperature drifts by
    // only a few degrees between 3 s polls.
    if (Math.abs(reading - accepted) <= maxJumpC)
        return { accepted: reading, candidate: null, count: 0 };
    // Out of band: too large a jump to be real for one poll. Hold the last good
    // value and require the new level to persist. A read that continues the
    // pending excursion (within maxJumpC of the candidate) extends the streak;
    // anything else restarts it at the new level.
    const continues =
        candidate !== null && Math.abs(reading - candidate) <= maxJumpC;
    const nextCount = continues ? count + 1 : 1;
    if (nextCount >= confirmSamples)
        return { accepted: reading, candidate: null, count: 0 };
    return { accepted, candidate: reading, count: nextCount };
}

/* Spatial despike: the metric for a poll, computed by dropping per-core
 * readings that sit implausibly far above the rest of the die, then taking the
 * hottest survivor.
 *
 * Silicon conducts heat well, so a single core physically cannot sit tens of
 * degrees hotter than its on-die neighbors - such a reading is a bad per-core
 * sensor, not a temperature. This was diagnosed on 2026-07-22 from a 616-poll
 * per-core capture: two specific cores (Core 8 and Core 12) intermittently
 * pinned to ~100-101°C while the machine was idle (5-10% CPU) and every other
 * core sat at ~55°C - a ~45°C gradient across a die a few mm wide, impossible
 * for a real temperature. A GENUINE hot event looks completely different: the
 * whole die heats together (all cores within ~12°C of the median) as load and
 * clock-throttling rise, so NO core is an outlier and nothing is dropped. The
 * `maxAboveMedianC` band cleanly separates the two - the observed glitch
 * gradient (~45°C) is far above it while the observed real-load spread (~12°C)
 * is well below - so a real all-core hot event still drives the gauge while a
 * lone stuck sensor no longer can.
 *
 * This is the PRIMARY defense against the stuck-sensor failure, upstream of the
 * median and slew gate (which the ~80 s glitch runs outlast). Package temp is
 * deliberately NOT a candidate here: it mirrors the die max, so it merely
 * inherits whichever core is glitching.
 *
 *   coreTemps   array of per-core temperatures (numbers); nulls are ignored
 *   opts.maxAboveMedianC  a core more than this above the core median is dropped
 *
 * Returns the metric (°C), or null if there are no usable core readings. The
 * kept set is never empty: the median value itself always satisfies the band
 * (median <= median + maxAboveMedianC), so at least one core always survives.
 */
function spatialMetric(coreTemps, opts) {
    const temps = coreTemps.filter(t => typeof t === 'number' && isFinite(t));
    if (temps.length === 0)
        return null;
    const cutoff = median(temps) + opts.maxAboveMedianC;
    const kept = temps.filter(t => t <= cutoff);
    return Math.max(...kept);
}

// Keeps only samples no older than maxAgeMs before `now`. Used both to bound
// the on-disk file (30-day retention) and to pick the recent window that
// seeds a freshly-started shell's graph. Boundary is inclusive (t == cutoff
// is kept).
function pruneByAge(samples, now, maxAgeMs) {
    const cutoff = now - maxAgeMs;
    return samples.filter(([t]) => t >= cutoff);
}

// --- Writer election: a single heartbeat lock file, { pid, bootId, ts }. ---
//
// Any instance can write history, but only one should at a time. Coordination
// is a lock file the current writer rewrites every poll (the heartbeat). An
// instance may claim writership when no one else holds a live claim. This
// needs no knowledge of whether a shell is nested - it only asks "is another
// writer alive right now?".

function serializeLock(pid, bootId, ts) {
    return JSON.stringify({ pid, bootId, ts: Math.round(ts) }) + '\n';
}

function parseLock(text) {
    const s = String(text ?? '').trim();
    if (!s)
        return null;
    let obj;
    try {
        obj = JSON.parse(s);
    } catch (e) {
        return null;
    }
    if (!obj || typeof obj.pid !== 'number' ||
        typeof obj.bootId !== 'string' || typeof obj.ts !== 'number')
        return null;
    return { pid: obj.pid, bootId: obj.bootId, ts: obj.ts };
}

/* Whether THIS instance may claim (or keep) writership, given the lock it
 * just read. Pure: the caller supplies liveness facts it gathered via IO.
 *
 *   lock            parsed lock file, or null if absent/unreadable
 *   now             current time (ms)
 *   opts.staleMs    a heartbeat older than this means the writer is gone
 *   opts.myPid      this process's pid
 *   opts.currentBootId  this boot's id (guards against pid reuse across boots)
 *   opts.writerPidAlive is the lock holder's pid a live process right now?
 *
 * Claimable when: no lock; the lock is already ours (same boot); the lock is
 * from a previous boot (its pid is meaningless now); the heartbeat is stale;
 * or the holder's process is simply gone. Otherwise another instance is alive
 * and fresh, so we stand down and read.
 */
function canClaim(lock, now, opts) {
    const { staleMs, myPid, currentBootId, writerPidAlive } = opts;
    if (!lock)
        return true;
    if (lock.pid === myPid && lock.bootId === currentBootId)
        return true;
    if (lock.bootId !== currentBootId)
        return true;
    if (now - lock.ts > staleMs)
        return true;
    if (!writerPidAlive)
        return true;
    return false;
}

var HISTORY_EXPORTS = {
    parseHistoryLine,
    parseHistory,
    serializeSample,
    serializeHistory,
    parseProcStatCpu,
    cpuUtilizationPct,
    serializeExcludedSample,
    parseExcludedLine,
    parseExcluded,
    serializeExcludedHistory,
    median,
    slewGate,
    spatialMetric,
    pruneByAge,
    serializeLock,
    parseLock,
    canClaim,
};
if (typeof module !== 'undefined' && module.exports)
    module.exports = HISTORY_EXPORTS;
