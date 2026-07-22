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

test('serialize -> parse round-trips a history', () => {
    const samples = [[1, 40], [2, 41.5], [3, 99.9]];
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
