/* extension.js - CPU Temperature Bar
 *
 * A colored horizontal gauge in the GNOME top panel showing the CPU
 * temperature, plus desktop notifications when the temperature crosses into
 * the warning or critical range. Clicking the gauge opens a popup with the
 * numeric details and a graph of the last two hours, for "is it my
 * imagination or is it getting hotter" questions.
 *
 * The gauge fills left-to-right and carries small tick marks at the warning
 * (orange) and bad (red) thresholds, so a rising temperature is visible as
 * the fill creeping toward the ticks long before the color changes.
 *
 * The thresholds deliberately mirror scripts/temperature-check.sh in this
 * repo (the script this widget grew out of):
 *
 *   warn at min(90C, crit - 12)     "CONCERNING"  -> orange
 *   bad  at min(100C, crit - 3)     "BAD"         -> red
 *
 * where crit is the chip's own reported critical temperature (110C on
 * mujina's coretemp; 100C assumed if the chip reports none). The gauge is
 * empty at 40C and full at crit, and is judged on the hotter of the package
 * temperature and the hottest individual core, same as the script.
 *
 * Written for GNOME Shell 42 (Ubuntu 22.04) - legacy `imports` style, not
 * the ESM style used by GNOME 45+.
 */
'use strict';

const { Gio, GLib, GObject, St } = imports.gi;
const ByteArray = imports.byteArray;
const Main = imports.ui.main;
const MessageTray = imports.ui.messageTray;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;

const Me = imports.misc.extensionUtils.getCurrentExtension();
const History = Me.imports.history; // pure parse/prune/election logic

const POLL_SECONDS = 3;

// Thresholds (degrees C) - keep in sync with scripts/temperature-check.sh.
const WARN_ABS = 90;
const BAD_ABS = 100;
const CRIT_WARN_MARGIN = 12;
const CRIT_BAD_MARGIN = 3;
const DEFAULT_CRIT = 100; // assumed only when the chip reports no crit temp

const EMPTY_AT = 40;  // gauge is empty at/below this temperature
const HYSTERESIS = 4; // degrees below a threshold before severity drops again

// De-noising the metric. The sensors occasionally return wildly-wrong reads -
// package AND hottest core both snapping to ~100C while the readings on either
// side sit at ~48C, a 50C swing in 3 s that is not physically possible. Four
// layered defenses:
//  - MAX_ABOVE_MEDIAN_C: a SPATIAL cross-core check (History.spatialMetric),
//    the primary defense and applied first, in _readTemps. A 616-poll per-core
//    capture (2026-07-22) found two specific cores (Core 8, Core 12) pinning to
//    ~100C while the machine was idle and every other core sat at ~55C - a bad
//    per-core sensor, since a die a few mm wide cannot hold a 45C gradient. The
//    metric therefore drops any core more than MAX_ABOVE_MEDIAN_C above the
//    core median and takes the hottest survivor. A GENUINE hot event heats the
//    whole die together (all cores within ~12C of the median), so nothing is
//    dropped and the gauge still rises. This is what the temporal defenses
//    below cannot do: the glitch runs last up to ~80 s, outlasting any median
//    or debounce window. See History.spatialMetric for the full rationale.
//  - SMOOTH_WINDOW: the metric that drives the bar/severity/archive is a MEDIAN
//    of the last few raw reads, so a LONE spike is discarded outright (median,
//    not mean, so it is not averaged in) and never colors the bar.
//  - MAX_JUMP_C / JUMP_CONFIRM_SAMPLES: a slew/jump gate (History.slewGate)
//    downstream of the median. The median kills a 1-poll spike but a run of 2+
//    consecutive bad reads outvotes a 3-wide median and slips through (observed
//    2026-07-22: the archive logged burst excursions to 98-101C while an
//    ice-packed, cool-to-touch laptop sat at ~50C). The gate refuses to move
//    the metric more than MAX_JUMP_C in one poll until the new level HOLDS for
//    JUMP_CONFIRM_SAMPLES polls, so a burst is ignored while a sustained real
//    excursion is accepted after a brief delay. See History.slewGate for the
//    full rationale. MAX_JUMP_C is set well above any real per-poll change
//    (genuine bursts ramp only a few degrees per 3 s poll) yet far below the
//    ~50C one-poll leap of a glitch; both numbers are provisional pending a
//    fine-grained raw capture and easy to retune here.
//  - CONFIRM_SAMPLES_BY_SEV: a severity must hold for this many consecutive
//    polls (indexed by severity) before it fires a notification, so brief
//    excursions do not interrupt. The two alert tiers deliberately differ
//    (GM decision 2026-07-23, after the RCA showed real bursty load
//    legitimately spikes the die to 95-100C for tens of seconds before the
//    fans catch up - normal turbo behavior, not an emergency):
//      - BAD (red, at/near the limit): 3 polls (~10 s). Near the limit, fast
//        notice is worth an occasional burst-triggered popup.
//      - WARN (orange, "keep an eye on it"): 20 polls (~60 s). A turbo burst
//        that clips the warning range for 10-30 s is routine and self-limiting
//        (throttling is the real safety net); only a genuinely SUSTAINED
//        warm state is worth an interruption.
//      - normal: 3 polls - not a notification (recovery is silent), just how
//        fast the confirmed-severity floor resets so a later re-escalation
//        can notify again.
const MAX_ABOVE_MEDIAN_C = 20;
const SMOOTH_WINDOW = 3;
const MAX_JUMP_C = 20;
const JUMP_CONFIRM_SAMPLES = 3;
const CONFIRM_SAMPLES_BY_SEV = [3, 20, 3];

// Sensors known to misreport on THIS machine, by their `sensors` label. They
// are HARD-excluded from the displayed/alarming metric (the gauge, severity,
// notifications, graph, and metric archive), but their raw readings are still
// recorded to the excluded-sensor archive (EXCLUDED_PATH) so a known-glitchy
// sensor can be inspected later without ever driving an alarm.
//
// This is a by-name complement to the statistical spatial reject
// (MAX_ABOVE_MEDIAN_C): the spatial check drops whatever is an outlier on a
// given poll, but a sensor we already KNOW is bad should never drive the gauge
// even on a poll where its glitch happens to land within the spatial band (e.g.
// under moderate load, when the rest of the die has risen toward it). Diagnosed
// 2026-07-22 from a 616-poll per-core capture: Core 8 and Core 12 intermittently
// pin to ~100C while the machine is idle. Edit this list if a new bad sensor
// turns up - find it with the per-core capture recipe in CLAUDE.md. Empty on a
// healthy machine (no exclusions, nothing written to the diagnostic archive).
const KNOWN_BAD_SENSORS = ['Core 8', 'Core 12'];

const BAR_WIDTH = 80; // px; wide so the fill's approach to the ticks is visible

// History graph shows the last 2 h. The in-memory buffer holds one sample per
// POLL_SECONDS (~2,400 entries) for a smooth live line; on startup it is
// SEEDED from the on-disk archive (below) so the graph is populated the
// instant a shell starts instead of drawing itself from empty.
const HISTORY_SECONDS = 7200;
const GRAPH_WIDTH = 340;
const GRAPH_HEIGHT = 120;
// A sampling gap longer than this breaks the graph line rather than drawing a
// misleading straight segment across it. It must sit comfortably above the
// archive's PERSIST_SECONDS cadence (else the coarser seeded portion of the
// line would fragment) yet still catch real gaps - suspend, a shell restart -
// which are minutes long.
const GAP_BREAK_SECONDS = 120;

// On-disk archive. Unlike the in-memory buffer, this survives shell restarts
// and logouts, so it answers "what were the trends over the last few weeks?"
// and can be handed to Claude to interpret. It lives under XDG_STATE_HOME
// (~/.local/state). A sample is persisted every PERSIST_SECONDS (coarser than
// the 3 s poll - 30 s resolution is plenty for trends and keeps the file
// ~10x smaller: ~2,880 lines/day, ~3 MB over the 30-day retention).
//
// Exactly one running instance writes at a time, chosen by a heartbeat lock
// file (History.canClaim). Every instance SEEDS its graph from the archive at
// startup and then tracks its own live samples; only the writer appends to and
// prunes the file. See CLAUDE.md "Persisted history" for the full rationale.
const PERSIST_SECONDS = 30;
const FILE_RETENTION_SECONDS = 30 * 24 * 3600;
const PRUNE_INTERVAL_SECONDS = 3600;
// The writer rewrites the lock every poll; a heartbeat older than this means
// the writer is gone and another instance may take over. Four missed polls.
const WRITER_STALE_SECONDS = 12;

const STATE_DIR = GLib.build_filenamev(
    [GLib.get_user_state_dir(), 'temperature-bar']);
const HISTORY_PATH = GLib.build_filenamev([STATE_DIR, 'history.jsonl']);
// Raw readings of the KNOWN_BAD_SENSORS - recorded but never displayed. Kept
// separate from the metric archive so the display path stays untouched.
const EXCLUDED_PATH = GLib.build_filenamev([STATE_DIR, 'excluded.jsonl']);
const LOCK_PATH = GLib.build_filenamev([STATE_DIR, 'writer.lock']);

// Severity -> fill color (RGB 0..1). 0 normal, 1 concerning, 2 bad.
const COLORS = [
    [0.30, 0.82, 0.40], // green
    [0.95, 0.62, 0.10], // orange
    [0.90, 0.17, 0.17], // red
];

function readFile(path) {
    try {
        const [ok, bytes] = GLib.file_get_contents(path);
        return ok ? ByteArray.toString(bytes).trim() : null;
    } catch (e) {
        return null;
    }
}

// Reads a sysfs millidegree value, returns degrees C (or null).
function readTemp(path) {
    const raw = readFile(path);
    if (raw === null)
        return null;
    const value = parseFloat(raw);
    return isNaN(value) ? null : value / 1000;
}

function listDir(path) {
    const names = [];
    try {
        const dir = Gio.File.new_for_path(path);
        const children = dir.enumerate_children(
            'standard::name', Gio.FileQueryInfoFlags.NONE, null);
        let info;
        while ((info = children.next_file(null)) !== null)
            names.push(info.get_name());
        children.close(null);
    } catch (e) {
        // directory missing or unreadable - return what we have
    }
    return names;
}

// Appends text to a file, creating parent dirs as needed. Returns true on
// success. Used for the one-line-per-sample archive.
function appendFile(path, text) {
    try {
        GLib.mkdir_with_parents(GLib.path_get_dirname(path), 0o755);
        const stream = Gio.File.new_for_path(path)
            .append_to(Gio.FileCreateFlags.NONE, null);
        stream.write_all(new TextEncoder().encode(text), null);
        stream.close(null);
        return true;
    } catch (e) {
        return false;
    }
}

// Atomically replaces a file's contents (temp-file + rename under the hood),
// creating parent dirs as needed. Used for the lock heartbeat and for
// rewriting the archive after a prune.
function writeFileAtomic(path, text) {
    try {
        GLib.mkdir_with_parents(GLib.path_get_dirname(path), 0o755);
        GLib.file_set_contents(path, text);
        return true;
    } catch (e) {
        return false;
    }
}

// This process's pid, read from /proc/self/stat (its first field, before the
// parenthesized comm, so process names with spaces are harmless).
function currentPid() {
    const stat = readFile('/proc/self/stat');
    return stat === null ? -1 : parseInt(stat.split(' ')[0], 10);
}

// A per-boot id, so a stale lock left by a previous boot (where the same pid
// may since have been reused by something else) is never mistaken for live.
function currentBootId() {
    return readFile('/proc/sys/kernel/random/boot_id') || '';
}

// Whether a pid is a live process on THIS boot (caller guards boot identity).
function pidAlive(pid) {
    return GLib.file_test(`/proc/${pid}`, GLib.FileTest.EXISTS);
}

/* Finds the CPU temperature sensors once, at enable time. Returns
 * { pkg, cores, crit, source } where pkg is a sysfs *_input path (or null),
 * cores is a list of such paths, and crit is degrees C (or null).
 *
 * Preferred source is a coretemp (Intel) or k10temp/zenpower (AMD) hwmon
 * chip - the same chips lm-sensors reads. Sensor numbering within a chip is
 * NOT contiguous (mujina has temp1, temp2..temp10, temp14, ...), so entries
 * are discovered by filename, never by counting.
 */
function discoverSensors() {
    const result = { pkg: null, cores: [], crit: null, source: null };

    const hwmonRoot = '/sys/class/hwmon';
    for (const hwmon of listDir(hwmonRoot)) {
        const base = `${hwmonRoot}/${hwmon}`;
        const chip = readFile(`${base}/name`);
        if (chip !== 'coretemp' && chip !== 'k10temp' && chip !== 'zenpower')
            continue;
        for (const entry of listDir(base)) {
            const m = entry.match(/^temp(\d+)_input$/);
            if (!m)
                continue;
            const n = m[1];
            const label = readFile(`${base}/temp${n}_label`) || '';
            const input = `${base}/temp${n}_input`;
            // Tctl/Tdie are the package-level readings on AMD chips.
            if (/^Package id/.test(label) || label === 'Tctl' || label === 'Tdie') {
                result.pkg = input;
                result.crit = readTemp(`${base}/temp${n}_crit`);
            } else {
                // Keep the label (e.g. "Core 8") alongside the path so a
                // known-bad sensor can be excluded by name (KNOWN_BAD_SENSORS).
                result.cores.push({ label, input });
            }
        }
        if (result.pkg || result.cores.length > 0) {
            result.source = `hwmon (${chip})`;
            return result;
        }
    }

    // Fallback: kernel thermal zones, same as the shell script.
    const tzRoot = '/sys/class/thermal';
    for (const zone of listDir(tzRoot)) {
        if (!zone.startsWith('thermal_zone'))
            continue;
        const base = `${tzRoot}/${zone}`;
        if (readTemp(`${base}/temp`) === null)
            continue;
        const ztype = readFile(`${base}/type`) || '';
        if (ztype === 'x86_pkg_temp')
            result.pkg = `${base}/temp`;
        else
            result.cores.push({ label: ztype, input: `${base}/temp` });
    }
    if (result.pkg || result.cores.length > 0)
        result.source = 'thermal zones';
    return result;
}

const TempBarButton = GObject.registerClass(
class TempBarButton extends PanelMenu.Button {
    _init() {
        super._init(0.0, 'CPU Temperature');

        this._sensors = discoverSensors();
        this._crit = this._sensors.crit ?? DEFAULT_CRIT;
        this._warnAt = Math.min(WARN_ABS, this._crit - CRIT_WARN_MARGIN);
        this._badAt = Math.min(BAD_ABS, this._crit - CRIT_BAD_MARGIN);

        this._sev = 0;
        this._metric = null;
        this._pkg = null;
        this._hottest = null;
        this._fraction = 0;

        // De-noising state.
        this._recent = [];      // last few raw metric reads, for the median despike
        this._accepted = null;  // last metric the slew/jump gate accepted
        this._jumpCandidate = null; // pending out-of-band level awaiting confirmation
        this._jumpCount = 0;    // consecutive polls that candidate has held
        this._lastUpdate = 0;   // ms of the previous poll, to detect a sampling gap
        this._debSev = null;    // severity currently accumulating a confirmation streak
        this._debCount = 0;     // length of that streak, in polls
        this._confirmedSev = 0; // last severity we actually notified about

        // Reused notification source/notification (see _notify).
        this._source = null;
        this._notification = null;

        // Writer election + persistence bookkeeping.
        this._pid = currentPid();
        this._bootId = currentBootId();
        this._isWriter = false;
        this._lastPersist = 0;
        this._lastPrune = 0;
        this._excluded = {};    // latest KNOWN_BAD_SENSORS reads, for the diagnostic archive
        // Previous /proc/stat snapshot, so each persisted sample can carry the
        // average CPU utilization since the one before it (History.parseProcStatCpu).
        this._cpuPrev = History.parseProcStatCpu(readFile('/proc/stat') || '');

        // Seed the in-memory graph from the on-disk archive's last 2 h, so a
        // freshly-started shell (including a nested test shell) shows real
        // history immediately rather than an empty graph that fills in from
        // scratch. Live samples then accumulate on top.
        this._history = History.pruneByAge(
            History.parseHistory(readFile(HISTORY_PATH) || ''),
            Date.now(), HISTORY_SECONDS * 1000); // [ms timestamp, degrees C]

        this._area = new St.DrawingArea({ width: BAR_WIDTH, y_expand: true });
        this._area.connect('repaint', area => this._onRepaint(area));
        this.add_child(this._area);

        this._buildMenu();
        this._update();

        this._timeoutId = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT, POLL_SECONDS, () => {
                this._update();
                return GLib.SOURCE_CONTINUE;
            });
    }

    destroy() {
        if (this._timeoutId) {
            GLib.source_remove(this._timeoutId);
            this._timeoutId = 0;
        }
        // Tear down our own notification source so disabling the extension
        // actually clears its notifications (they otherwise outlive the widget,
        // owned by the message tray). The 'destroy' handler nulls our refs.
        if (this._source !== null)
            this._source.destroy();
        // If we held the writer claim, release it so another running instance
        // takes over at once rather than waiting out the heartbeat staleness.
        // Guard on the lock still being ours - never delete a claim a
        // successor already took.
        if (this._isWriter) {
            const lock = History.parseLock(readFile(LOCK_PATH));
            if (lock !== null && lock.pid === this._pid && lock.bootId === this._bootId) {
                try {
                    Gio.File.new_for_path(LOCK_PATH).delete(null);
                } catch (e) {
                    // best effort - staleness will expire it otherwise
                }
            }
        }
        super.destroy();
    }

    // Gauge/graph x-position of a temperature, as a 0..1 fraction.
    _fractionOf(temp) {
        return Math.min(1, Math.max(0,
            (temp - EMPTY_AT) / (this._crit - EMPTY_AT)));
    }

    _buildMenu() {
        this._statusItem = new PopupMenu.PopupMenuItem('', { reactive: false });
        this._pkgItem = new PopupMenu.PopupMenuItem('', { reactive: false });
        this._coreItem = new PopupMenu.PopupMenuItem('', { reactive: false });
        this.menu.addMenuItem(this._statusItem);
        this.menu.addMenuItem(this._pkgItem);
        this.menu.addMenuItem(this._coreItem);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        this._graphArea = new St.DrawingArea(
            { width: GRAPH_WIDTH, height: GRAPH_HEIGHT });
        this._graphArea.connect('repaint', area => this._onGraphRepaint(area));
        const graphItem = new PopupMenu.PopupBaseMenuItem(
            { reactive: false, can_focus: false });
        graphItem.add_child(this._graphArea);
        this.menu.addMenuItem(graphItem);
        this._rangeItem = new PopupMenu.PopupMenuItem('', { reactive: false });
        this.menu.addMenuItem(this._rangeItem);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        const source = this._sensors.source ?? 'no sensor found';
        this.menu.addMenuItem(new PopupMenu.PopupMenuItem(
            `Warn ${this._warnAt}°C / bad ${this._badAt}°C / crit ${this._crit}°C - via ${source}`,
            { reactive: false }));
    }

    _readTemps() {
        const pkg = this._sensors.pkg ? readTemp(this._sensors.pkg) : null;
        const coreTemps = [];   // trusted per-core reads - feed the metric
        const excluded = {};    // KNOWN_BAD_SENSORS reads - recorded, never shown
        for (const core of this._sensors.cores) {
            const t = readTemp(core.input);
            if (t === null)
                continue;
            if (KNOWN_BAD_SENSORS.includes(core.label))
                excluded[core.label] = t;
            else
                coreTemps.push(t);
        }
        const hottest = coreTemps.length ? Math.max(...coreTemps) : null;
        // The metric drops spatial-outlier cores (a bad per-core sensor reading
        // far above the rest of the die) before taking the hottest survivor;
        // see History.spatialMetric. Known-bad sensors are already gone (never
        // entered coreTemps). Package temp is NOT a candidate - it mirrors the
        // die max, so it merely inherits a glitching core. Fall back to package
        // only when no trusted per-core sensors were found at all. `pkg` and
        // `hottest` are surfaced raw for the popup's diagnostic readout.
        const metric = coreTemps.length
            ? History.spatialMetric(coreTemps, { maxAboveMedianC: MAX_ABOVE_MEDIAN_C })
            : pkg;
        return { pkg, hottest, metric, excluded };
    }

    _update() {
        const now = Date.now();
        const { pkg, hottest, metric: raw, excluded } = this._readTemps();
        this._pkg = pkg;
        this._hottest = hottest;
        this._excluded = excluded;

        // A real sampling gap (suspend, shell restart) makes the de-noising
        // history stale: the pre-gap reads no longer predict the post-gap
        // temperature, and the slew gate would wrongly hold the old value (or
        // even flash a stale hot reading) for a few polls after resume. So
        // forget the smoothing/gate state across a gap and judge the resumed
        // stream fresh. Same GAP_BREAK_SECONDS the graph uses to break its line.
        if (this._lastUpdate !== 0 &&
            now - this._lastUpdate > GAP_BREAK_SECONDS * 1000) {
            this._recent = [];
            this._accepted = null;
            this._jumpCandidate = null;
            this._jumpCount = 0;
        }
        this._lastUpdate = now;

        // Despike, stage 1 (median): the metric that drives everything
        // downstream (bar, severity, graph, archive) starts as a median of the
        // last SMOOTH_WINDOW raw reads, so a single spurious sensor value is
        // discarded rather than shown. Until the window fills (first couple of
        // polls) the raw read is used as-is.
        let smoothed = raw;
        if (raw !== null) {
            this._recent.push(raw);
            if (this._recent.length > SMOOTH_WINDOW)
                this._recent.shift();
            if (this._recent.length === SMOOTH_WINDOW)
                smoothed = History.median(this._recent);
        }

        // Despike, stage 2 (slew/jump gate): the median kills lone spikes but a
        // run of 2+ consecutive bad reads outvotes it; the gate holds the last
        // good value through such a burst and only moves on a change that is
        // either physically plausible or sustained. See History.slewGate.
        const gate = History.slewGate(
            { accepted: this._accepted, candidate: this._jumpCandidate, count: this._jumpCount },
            raw === null ? null : smoothed,
            { maxJumpC: MAX_JUMP_C, confirmSamples: JUMP_CONFIRM_SAMPLES });
        this._accepted = gate.accepted;
        this._jumpCandidate = gate.candidate;
        this._jumpCount = gate.count;
        const metric = this._accepted;
        this._metric = metric;

        if (metric === null) {
            this._sev = 0;
            this._fraction = 0;
        } else {
            this._history.push([now, metric]);
            const cutoff = now - HISTORY_SECONDS * 1000;
            while (this._history.length > 0 && this._history[0][0] < cutoff)
                this._history.shift();

            // Bar severity: immediate, with downward hysteresis so hovering at
            // 89-91C does not flip-flop the color every few seconds.
            let sev = 0;
            if (metric >= this._warnAt)
                sev = 1;
            if (metric >= this._badAt)
                sev = 2;
            if (sev < this._sev) {
                const floor = (this._sev === 2 ? this._badAt : this._warnAt) - HYSTERESIS;
                if (metric > floor)
                    sev = this._sev;
            }
            this._sev = sev;

            this._maybeNotify(metric);
            this._fraction = Math.max(0.02, this._fractionOf(metric));
        }

        this._persistTick(now);

        this._area.queue_repaint();
        this._graphArea.queue_repaint();
        this._updateMenu();
    }

    // Runs every poll. Re-elects the writer (so a reader takes over within a
    // few seconds if the current writer logs out), and if THIS instance is the
    // writer, appends a sample every PERSIST_SECONDS and prunes the archive to
    // its retention window hourly.
    _persistTick(now) {
        this._electWriter(now);
        if (!this._isWriter)
            return;
        if (this._metric !== null && now - this._lastPersist >= PERSIST_SECONDS * 1000) {
            // The sample carries the average CPU utilization since the previous
            // persist (`u`) - the real-heat-vs-stuck-sensor discriminator; see
            // History.parseProcStatCpu for the 2026-07-23 rationale. Fail-soft:
            // an unreadable /proc/stat just writes the sample without `u`.
            const cpuCur = History.parseProcStatCpu(readFile('/proc/stat') || '');
            const cpuPct = History.cpuUtilizationPct(this._cpuPrev, cpuCur);
            if (cpuCur !== null)
                this._cpuPrev = cpuCur;
            appendFile(HISTORY_PATH,
                History.serializeSample(now, this._metric, cpuPct));
            // Known-bad sensors are excluded from the metric above, but their
            // raw reads are still recorded here so they can be inspected later
            // (KNOWN_BAD_SENSORS). Nothing is written on a healthy machine where
            // the exclusion list is empty.
            if (Object.keys(this._excluded).length > 0)
                appendFile(EXCLUDED_PATH,
                    History.serializeExcludedSample(now, this._excluded));
            this._lastPersist = now;
        }
        if (now - this._lastPrune >= PRUNE_INTERVAL_SECONDS * 1000) {
            this._pruneArchive(now);
            this._pruneExcluded(now);
            this._lastPrune = now;
        }
    }

    // Claims (or renews) writership via the heartbeat lock, or stands down to
    // reader. On claiming, the lock is re-read to confirm we won any simult
    // -aneous-startup race; the loser sees the winner's pid next poll and
    // stays a reader. A brief double-claim is harmless - the first persisted
    // sample is 30 s out, long after election settles at the 3 s poll.
    _electWriter(now) {
        const lock = History.parseLock(readFile(LOCK_PATH));
        const writerPidAlive = lock !== null && pidAlive(lock.pid);
        if (!History.canClaim(lock, now, {
            staleMs: WRITER_STALE_SECONDS * 1000,
            myPid: this._pid,
            currentBootId: this._bootId,
            writerPidAlive,
        })) {
            this._isWriter = false;
            return;
        }
        writeFileAtomic(LOCK_PATH,
            History.serializeLock(this._pid, this._bootId, now));
        const back = History.parseLock(readFile(LOCK_PATH));
        this._isWriter = back !== null &&
            back.pid === this._pid && back.bootId === this._bootId;
    }

    // Rewrites the archive dropping samples past the retention window. Only
    // touches the file when something actually ages out, so the common hourly
    // call on a within-retention file is a cheap read with no write.
    _pruneArchive(now) {
        const samples = History.parseHistory(readFile(HISTORY_PATH) || '');
        const kept = History.pruneByAge(samples, now, FILE_RETENTION_SECONDS * 1000);
        if (kept.length !== samples.length)
            writeFileAtomic(HISTORY_PATH, History.serializeHistory(kept));
    }

    // Same retention prune for the excluded-sensor diagnostic archive. It shares
    // the metric archive's 30-day window - long enough to look back at a
    // known-glitchy sensor's behavior, bounded so the file cannot grow forever.
    _pruneExcluded(now) {
        const samples = History.parseExcluded(readFile(EXCLUDED_PATH) || '');
        const kept = History.pruneByAge(samples, now, FILE_RETENTION_SECONDS * 1000);
        if (kept.length !== samples.length)
            writeFileAtomic(EXCLUDED_PATH, History.serializeExcludedHistory(kept));
    }

    _updateMenu() {
        if (this._metric === null) {
            this._statusItem.label.text = 'No CPU temperature sensor found';
            this._pkgItem.label.text = '-';
            this._coreItem.label.text = '-';
            this._rangeItem.label.text = '-';
            return;
        }
        const verdicts = ['NORMAL', 'CONCERNING', 'BAD'];
        const headroom = (this._crit - this._metric).toFixed(0);
        this._statusItem.label.text =
            `${verdicts[this._sev]} - ${Math.round(this._metric)}°C, headroom ${headroom}°C`;
        this._pkgItem.label.text = this._pkg !== null
            ? `Package: ${Math.round(this._pkg)}°C` : 'Package: n/a';
        this._coreItem.label.text = this._hottest !== null
            ? `Hottest core: ${Math.round(this._hottest)}°C` : 'Hottest core: n/a';

        let lo = Infinity, hi = -Infinity;
        for (const [, temp] of this._history) {
            if (temp < lo) lo = temp;
            if (temp > hi) hi = temp;
        }
        const spanMin = Math.round(
            (this._history[this._history.length - 1][0] - this._history[0][0]) / 60000);
        this._rangeItem.label.text =
            `Last ${spanMin} min - min ${Math.round(lo)}°C / max ${Math.round(hi)}°C`;
    }

    // Debounced notification. Fires only when a severity has held for its
    // CONFIRM_SAMPLES_BY_SEV count of consecutive polls AND is higher than the
    // last severity we notified about - so brief excursions never interrupt,
    // and a sustained rise notifies exactly once (not every poll while it
    // stays hot). Any change of severity restarts the streak, so "sustained"
    // means continuously in that state. Recovery is intentionally silent: the
    // gauge color already shows it.
    _maybeNotify(metric) {
        const sev = metric >= this._badAt ? 2 : (metric >= this._warnAt ? 1 : 0);
        if (sev === this._debSev) {
            this._debCount++;
        } else {
            this._debSev = sev;
            this._debCount = 1;
        }
        // Act exactly once, the poll the streak reaches this severity's count.
        if (this._debCount !== CONFIRM_SAMPLES_BY_SEV[sev])
            return;
        const prevConfirmed = this._confirmedSev;
        this._confirmedSev = sev;
        if (sev <= prevConfirmed)
            return;
        const t = Math.round(metric);
        if (sev === 2)
            this._notify(`CPU at ${t}°C`,
                'At or near the thermal limit - the CPU is throttling or about to.', true);
        else
            this._notify(`CPU running hot: ${t}°C`,
                'Concerning - keep an eye on it.', false);
    }

    // Presents a notification, reusing ONE source and ONE notification for the
    // widget's lifetime and updating it in place. The old code created a fresh
    // MessageTray.Source on every fire; during an oscillating hot spell that
    // stacked dozens of separate, individually-dismissable banners that felt
    // impossible to clear. With a single reused source there is at most one
    // banner, and it just updates.
    _notify(title, body, critical) {
        if (this._source === null) {
            this._source = new MessageTray.Source('CPU Temperature',
                'temperature-symbolic');
            this._source.connect('destroy', () => {
                this._source = null;
                this._notification = null;
            });
            Main.messageTray.add(this._source);
        }
        if (this._notification === null) {
            this._notification = new MessageTray.Notification(
                this._source, title, body);
            this._notification.connect('destroy', () => {
                this._notification = null;
            });
        } else {
            this._notification.update(title, body, { clear: true });
        }
        this._notification.setUrgency(critical
            ? MessageTray.Urgency.CRITICAL : MessageTray.Urgency.NORMAL);
        this._notification.setTransient(!critical);
        this._source.showNotification(this._notification);
    }

    // The panel gauge: horizontal trough filling left-to-right, with tick
    // marks at the warn/bad thresholds so "approaching orange" is visible.
    _onRepaint(area) {
        const cr = area.get_context();
        const [w, h] = area.get_surface_size();
        const inset = 6; // vertical margin inside the panel
        const barX = 1;
        const barW = w - 2;
        const barY = inset;
        const barH = h - 2 * inset;

        // Trough outline.
        cr.setSourceRGBA(1, 1, 1, 0.35);
        cr.setLineWidth(1);
        cr.rectangle(barX + 0.5, barY + 0.5, barW - 1, barH - 1);
        cr.stroke();

        const innerX = barX + 1;
        const innerY = barY + 1;
        const innerW = barW - 2;
        const innerH = barH - 2;

        if (this._metric !== null) {
            const fillW = Math.max(1, Math.round(this._fraction * innerW));
            const [r, g, b] = COLORS[this._sev];
            cr.setSourceRGBA(r, g, b, 1);
            cr.rectangle(innerX, innerY, fillW, innerH);
            cr.fill();
        } else {
            // Unknown state: dim gray block so the widget is visibly present
            // but clearly not reporting.
            cr.setSourceRGBA(0.6, 0.6, 0.6, 0.5);
            cr.rectangle(innerX + innerW / 4, innerY, innerW / 2, innerH);
            cr.fill();
        }

        // Threshold ticks, drawn over the fill so they stay visible.
        for (const [threshold, color] of
            [[this._warnAt, COLORS[1]], [this._badAt, COLORS[2]]]) {
            const x = innerX + Math.round(this._fractionOf(threshold) * innerW);
            const [r, g, b] = color;
            cr.setSourceRGBA(r, g, b, 0.9);
            cr.rectangle(x, innerY, 1, innerH);
            cr.fill();
        }
        cr.$dispose();
    }

    // The popup graph: last 2 h of samples on a fixed 40C..crit scale (fixed
    // so two glances an hour apart are directly comparable), with dashed
    // lines at the warn/bad thresholds.
    _onGraphRepaint(area) {
        const cr = area.get_context();
        const [w, h] = area.get_surface_size();
        const now = Date.now();
        const t0 = now - HISTORY_SECONDS * 1000;
        const xOf = t => ((t - t0) / (HISTORY_SECONDS * 1000)) * (w - 2) + 1;
        const yOf = temp => (h - 2) - this._fractionOf(temp) * (h - 4) + 1;

        // Opaque dark backdrop. The graph used to draw straight onto the popup
        // menu's themed background, whose color/opacity is theme-dependent - on
        // some themes that washed the low-alpha lines out to near-invisible
        // gray. Painting our own solid dark panel first means the lines below
        // always sit on a known dark surface, so full-alpha bright colors read
        // consistently regardless of the shell theme.
        cr.setSourceRGBA(0.10, 0.11, 0.14, 1);
        cr.rectangle(0, 0, w, h);
        cr.fill();

        // Frame.
        cr.setSourceRGBA(1, 1, 1, 0.4);
        cr.setLineWidth(1);
        cr.rectangle(0.5, 0.5, w - 1, h - 1);
        cr.stroke();

        // Threshold lines, dashed. Full alpha on the dark backdrop so orange
        // and red read as orange and red, not grayed-out.
        cr.setLineWidth(1.5);
        cr.setDash([4, 3], 0);
        for (const [threshold, color] of
            [[this._warnAt, COLORS[1]], [this._badAt, COLORS[2]]]) {
            const [r, g, b] = color;
            cr.setSourceRGBA(r, g, b, 1);
            const y = yOf(threshold);
            cr.moveTo(1, y);
            cr.lineTo(w - 1, y);
            cr.stroke();
        }
        cr.setDash([], 0);

        // Temperature line, broken across sampling gaps (suspend etc.).
        // Bright white at full alpha, 2 px, so it stands off the dark backdrop.
        cr.setSourceRGBA(1, 1, 1, 1);
        cr.setLineWidth(2);
        let prevT = null;
        for (const [t, temp] of this._history) {
            if (t < t0)
                continue;
            const x = xOf(t);
            const y = yOf(temp);
            if (prevT === null || t - prevT > GAP_BREAK_SECONDS * 1000)
                cr.moveTo(x, y);
            else
                cr.lineTo(x, y);
            prevT = t;
        }
        cr.stroke();
        cr.$dispose();
    }
});

class Extension {
    enable() {
        this._button = new TempBarButton();
        // Position 0 of the right box puts the gauge just left of the system
        // status area (wifi / sound / battery).
        Main.panel.addToStatusArea('temperature-bar', this._button, 0, 'right');
    }

    disable() {
        if (this._button) {
            this._button.destroy();
            this._button = null;
        }
    }
}

function init() {
    return new Extension();
}
