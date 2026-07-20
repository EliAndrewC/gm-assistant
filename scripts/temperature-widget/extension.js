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

const POLL_SECONDS = 3;

// Thresholds (degrees C) - keep in sync with scripts/temperature-check.sh.
const WARN_ABS = 90;
const BAD_ABS = 100;
const CRIT_WARN_MARGIN = 12;
const CRIT_BAD_MARGIN = 3;
const DEFAULT_CRIT = 100; // assumed only when the chip reports no crit temp

const EMPTY_AT = 40;  // gauge is empty at/below this temperature
const HYSTERESIS = 4; // degrees below a threshold before severity drops again

const BAR_WIDTH = 80; // px; wide so the fill's approach to the ticks is visible

// History graph. Samples arrive every POLL_SECONDS, so 2 h is 2,400 samples
// of [ms timestamp, degrees C] - trivial memory. History lives only as long
// as the extension does (shell restart / logout clears it).
const HISTORY_SECONDS = 7200;
const GRAPH_WIDTH = 340;
const GRAPH_HEIGHT = 120;
// A sampling gap longer than this (suspend, shell restart) breaks the graph
// line rather than drawing a misleading straight segment across it.
const GAP_BREAK_SECONDS = 30;

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
                result.cores.push(input);
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
        if (readFile(`${base}/type`) === 'x86_pkg_temp')
            result.pkg = `${base}/temp`;
        else
            result.cores.push(`${base}/temp`);
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
        this._history = []; // [ms timestamp, degrees C], pruned to 2 h

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
        let pkg = this._sensors.pkg ? readTemp(this._sensors.pkg) : null;
        let hottest = null;
        for (const path of this._sensors.cores) {
            const t = readTemp(path);
            if (t !== null && (hottest === null || t > hottest))
                hottest = t;
        }
        let metric = pkg;
        if (hottest !== null && (metric === null || hottest > metric))
            metric = hottest;
        return { pkg, hottest, metric };
    }

    _update() {
        const { pkg, hottest, metric } = this._readTemps();
        this._pkg = pkg;
        this._hottest = hottest;
        this._metric = metric;

        if (metric === null) {
            this._sev = 0;
            this._fraction = 0;
        } else {
            const now = Date.now();
            this._history.push([now, metric]);
            const cutoff = now - HISTORY_SECONDS * 1000;
            while (this._history.length > 0 && this._history[0][0] < cutoff)
                this._history.shift();

            let sev = 0;
            if (metric >= this._warnAt)
                sev = 1;
            if (metric >= this._badAt)
                sev = 2;
            // On the way down, hold the current severity until the reading is
            // clearly below the threshold, so hovering at 89-91C does not
            // flip-flop (and re-notify) every few seconds.
            if (sev < this._sev) {
                const floor = (this._sev === 2 ? this._badAt : this._warnAt) - HYSTERESIS;
                if (metric > floor)
                    sev = this._sev;
            }

            const prev = this._sev;
            this._sev = sev;
            const t = Math.round(metric);
            if (sev > prev) {
                if (sev === 2)
                    this._notify(`CPU at ${t}°C`,
                        'At or near the thermal limit - the CPU is throttling or about to.', true);
                else
                    this._notify(`CPU running hot: ${t}°C`,
                        'Concerning - keep an eye on it.', false);
            } else if (sev === 0 && prev > 0) {
                this._notify(`CPU back to normal: ${t}°C`,
                    'Comfortable headroom again.', false);
            }

            this._fraction = Math.max(0.02, this._fractionOf(metric));
        }

        this._area.queue_repaint();
        this._graphArea.queue_repaint();
        this._updateMenu();
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

    _notify(title, body, critical) {
        const source = new MessageTray.Source('CPU Temperature',
            'temperature-symbolic');
        Main.messageTray.add(source);
        const notification = new MessageTray.Notification(source, title, body);
        notification.setUrgency(critical
            ? MessageTray.Urgency.CRITICAL : MessageTray.Urgency.NORMAL);
        notification.setTransient(!critical);
        source.showNotification(notification);
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

        // Frame.
        cr.setSourceRGBA(1, 1, 1, 0.25);
        cr.setLineWidth(1);
        cr.rectangle(0.5, 0.5, w - 1, h - 1);
        cr.stroke();

        // Threshold lines, dashed.
        cr.setDash([3, 3], 0);
        for (const [threshold, color] of
            [[this._warnAt, COLORS[1]], [this._badAt, COLORS[2]]]) {
            const [r, g, b] = color;
            cr.setSourceRGBA(r, g, b, 0.7);
            const y = yOf(threshold);
            cr.moveTo(1, y);
            cr.lineTo(w - 1, y);
            cr.stroke();
        }
        cr.setDash([], 0);

        // Temperature line, broken across sampling gaps (suspend etc.).
        cr.setSourceRGBA(1, 1, 1, 0.9);
        cr.setLineWidth(1.5);
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
