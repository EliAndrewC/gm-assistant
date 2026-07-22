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

// --- Sample history: one JSON object per line, [ms-since-epoch, degrees C]. ---

// Parses one line to [t, c], or null if blank/malformed. Malformed lines are
// skipped rather than fatal - a half-written final line (writer killed
// mid-append) must not poison the whole history.
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
// and than any graph pixel can show, so it just wastes bytes.
function serializeSample(t, c) {
    return JSON.stringify({ t: Math.round(t), c: Math.round(c * 10) / 10 }) + '\n';
}

function serializeHistory(samples) {
    return samples.map(([t, c]) => serializeSample(t, c)).join('');
}

// Median of a list of numbers. Used to despike the temperature metric: a
// median of the last few raw reads discards a lone spurious value outright
// (unlike a mean, which would average it in). Does not mutate the input.
function median(nums) {
    const sorted = [...nums].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
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
    median,
    pruneByAge,
    serializeLock,
    parseLock,
    canClaim,
};
if (typeof module !== 'undefined' && module.exports)
    module.exports = HISTORY_EXPORTS;
