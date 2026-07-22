# CPU Temperature Bar (GNOME extension)

A colored horizontal gauge in the GNOME top panel, sitting just left of the
system status area (wifi / sound / battery), showing the CPU temperature at a
glance:

- **green** - normal, comfortable headroom
- **orange** - concerning (the `WARN` range of `scripts/temperature-check.sh`)
- **red** - bad, at or near the thermal limit

The gauge fills left-to-right as the temperature rises, with small orange and
red tick marks at the two thresholds - so a rising temperature is visible as
the fill creeping toward the ticks, well before the color changes. Clicking
it opens a popup with the numeric details (verdict, package temp, hottest
core, headroom, thresholds) plus a graph of the last 2 hours with dashed
threshold lines and a min/max summary, for "is it my imagination or is it
getting hotter" questions. The extension also sends a desktop notification once
the temperature has *stayed* in the warning range (normal urgency) or the bad
range (critical urgency) for a few polls - see [Notification debounce +
metric smoothing](#notification-debounce--metric-smoothing) for why it waits
rather than firing on the first reading. It does NOT notify on recovery - the
gauge color already shows that, and a "back to normal" popup is just noise.

Targets GNOME Shell 42 (Ubuntu 22.04, mujina).

## How to test a change

**Pure logic runs in the container; UI/IO needs the laptop.** The history
parse/prune and writer-election logic in `history.js` is unit-tested and
runnable anywhere:

```bash
node --test scripts/temperature-widget/test-history.js
```

Everything else - GNOME Shell rendering, the gauge, notifications, and the
actual file IO - can only be verified on the laptop, because the container
cannot run GNOME Shell (see [Dev loop caveat](#dev-loop-caveat)). After
editing `extension.js` or `history.js`:

1. **Install the new copy:**

   ```bash
   ./scripts/temperature-widget/install.sh
   ```

   This copies `extension.js` + `history.js` + `metadata.json` into
   `~/.local/share/gnome-shell/extensions/temperature-bar@mujina/` and enables
   it via gsettings. The copy is what any shell (real or nested) loads.

2. **Load it into a shell.** Pick based on session type and how disruptive you
   want to be. Note the graph is now **seeded from the on-disk archive** (see
   [Persisted history](#persisted-history)), so a nested test shell shows your
   real recent history right away instead of an empty graph - as long as your
   main session has been running to populate
   `~/.local/state/temperature-bar/history.jsonl`. To eyeball or reset the
   archive: `cat ~/.local/state/temperature-bar/history.jsonl` to view it,
   `rm` it to start fresh.

   - **Wayland, without disturbing your real session (preferred for iterating).**
     Run a **nested** GNOME Shell in its own window. It is a separate shell
     instance that loads the same installed extension, so your real panel -
     and any running Claude Code session, terminals, etc. - are left alone:

     ```bash
     dbus-run-session -- gnome-shell --nested --wayland
     ```

     The widget appears in the nested window's top panel; click it to check the
     popup graph. **Close the window to end the test.** Re-run `install.sh` and
     relaunch the nested shell for each iteration.

   - **Wayland, make it live for real.** Log out and back in. Only do this once
     the nested-shell check looks right - a real logout kills your session.

   - **X11.** Press Alt+F2, type `r`, Enter (in-place shell restart, no logout).

## Install / update (make it live)

Same first step as testing:

```bash
./scripts/temperature-widget/install.sh
```

Then reload GNOME Shell for your real session: on X11 press Alt+F2, type `r`,
Enter; on Wayland log out and back in.

To remove: `gnome-extensions disable temperature-bar@mujina`, then delete
`~/.local/share/gnome-shell/extensions/temperature-bar@mujina/`.

## Design notes (the "why")

- **Thresholds mirror `scripts/temperature-check.sh`** rather than inventing
  new ones: warn at min(90°C, crit - 12), bad at min(100°C, crit - 3), where
  crit is the chip's own reported critical temperature. Mujina's coretemp
  reports crit = 110°C, so the effective thresholds are warn 90°C / bad
  100°C, and the bar is full at 110°C. Empty is pinned at 40°C - idle temps
  live in the 40s-50s, so anchoring lower would waste most of the gauge's
  travel on readings that never occur.
- **The popup graph shows the last 2 h from an in-memory buffer** (one sample
  per 3 s, ~2,400 entries) for a smooth live line, but that buffer is SEEDED
  at startup from the on-disk archive (see "Persisted history" below), so a
  freshly-started shell shows real history immediately instead of an empty
  graph. The graph's y-scale is FIXED at 40°C..crit rather than auto-fit, so
  two glances an hour apart are directly comparable; a sampling gap longer
  than 120 s (suspend, shell restart) breaks the line instead of drawing a
  fake straight segment across it. (120 s, not 30 s: it must sit above the
  archive's 30 s persist cadence so the coarser seeded portion of the line
  does not fragment, while still catching real gaps, which are minutes long.)
- **The popup graph paints its own opaque dark backdrop** before drawing any
  lines, rather than drawing straight onto the popup menu's themed background.
  The menu background's color and opacity are theme-dependent, and on some
  themes they washed the low-alpha lines out to near-invisible gray (the temp
  line and both dashed threshold lines all looked grayed-out). A known dark
  panel underneath lets the lines use full-alpha bright colors that read
  consistently regardless of shell theme - white 2 px for the temperature
  trace, full-saturation orange/red for the dashed thresholds.
- **Judged on the hotter of package temp and hottest core**, same as the
  script - a single core can spike above the package reading. (This raw metric
  is then median-smoothed before use; see [Notification debounce + metric
  smoothing](#notification-debounce--metric-smoothing).)
- **Bar-color hysteresis (4°C) on the way down**: the gauge *color* severity
  drops only once the reading is clearly below the threshold, so a CPU hovering
  at 89-91°C does not flip the bar between green and orange every poll. (This
  governs the bar color only; notification spam is handled separately by the
  debounce below.)
- **Sensors are discovered by filename, never by counting**: coretemp's
  `tempN` numbering is sparse on this chip (temp1, temp2..temp10, temp14,
  ...), so a `for i in 1..N` loop that stops at the first gap would silently
  miss most cores.
- **Polling is a 3-second sysfs read** - a handful of small in-kernel file
  reads, negligible cost, and fast enough to catch a thermal runaway before
  it reaches throttling.

## Notification debounce + metric smoothing

The bare thresholds fire far too eagerly, because the sensors are noisy. A
10-minute sample of this machine at idle (196 reads, 3 s apart; the recording
lived at `scratchpad/temps.csv` during development) showed:

- an idle baseline of ~53°C, but a **max of 102°C**, and **10% of all 3 s
  intervals jumping ≥10°C**, one of them by 55°C;
- **provably-spurious single-read glitches**: twice, package *and* hottest core
  both snapped to *exactly 100°C* for one poll while the readings on either
  side were 45-52°C (`49 → 100 → 52`, `45 → 100 → 46`). A 50°C rise-and-fall in
  3 s is not physically possible - the silicon has thermal mass - so these are
  bad reads, not real temperatures (and they land on a suspiciously round 100);
- exactly one **genuine** hot burst (~50 s sustained 90-102°C, multiple cores,
  package tracking).

Under the naive "notify the instant severity rises" logic that fired **6
notifications (5 critical) in 10 idle minutes**. Four defenses fix it, the
spatial check first and then the temporal stack:

1. **Spatial cross-core reject (`MAX_ABOVE_MEDIAN_C = 20`; `History.spatialMetric`).**
   The primary defense, applied first (in `_readTemps`, upstream of the temporal
   stack below). A 616-poll per-core capture on 2026-07-22 - laptop on an ice
   pack, case cool to the touch throughout - pinned the root cause down: **two
   specific cores, Core 8 and Core 12, intermittently report a spurious
   ~100-101°C** while every other core sits at ~55°C. Over that sample the two
   pinned to ≥100°C in 80 and 96 of 616 polls; no other core did so more than 4
   times. It is provably not real heat - the machine was idle (5-10% CPU) with
   most cores parked at the 400 MHz floor, and a die a few mm across cannot hold
   a ~45°C gradient between neighboring cores. The package temp then *inherits*
   it (package = die max), and the old metric `max(package, hottest core)`
   amplified that one bad sensor straight onto the gauge.

   A **genuine** hot event is spatially different: real load heats the whole die
   together. The same capture's true-load stretches ran 94-100% CPU with the
   whole core set at ~88-92°C (and the clock throttling *down* from 4.6 GHz to
   ~2.6 GHz - the hardware's own response to real heat). So the discriminator is
   spatial spread, not magnitude: drop any core more than `MAX_ABOVE_MEDIAN_C`
   above the *median of all cores*, then take the hottest survivor. A lone stuck
   core is an outlier and is dropped; an all-cores-hot event has no outlier and
   passes untouched. `MAX_ABOVE_MEDIAN_C = 20` sits between the two observed
   clusters - real load spreads only ~12°C above the median, the glitch ~45°C.
   Package temp is deliberately not a candidate, since it just mirrors the
   glitching core. (CPU utilization is the clean *offline* discriminator; the
   hardware throttle counters are not, because a sensor falsely reading 100°C
   makes the CPU throttle that core on phantom heat, so they tick in both
   regimes - a minor real cost of the defect, separate from this cosmetic fix.)

   Replaying the fix over a 754-poll capture: polls that would color the bar RED
   (metric ≥100°C) fall from 188 to 51, orange-or-worse (≥90°C) from 287 to 115,
   and **all 70 genuine whole-die-hot polls are preserved** - zero real events
   lost. This is the defense the temporal ones below cannot provide: the glitch
   runs last up to ~80 s (26 consecutive polls), outlasting any median or
   debounce window. Pure logic in `history.js`, unit-tested in `test-history.js`.
   `MAX_ABOVE_MEDIAN_C` is tunable and lives beside the other de-noise constants.

2. **Median-of-3 smoothing (`SMOOTH_WINDOW`).** The metric that drives the bar,
   the severity, the graph, and the archive is the median of the last 3 raw
   reads, not the raw read. A median (not a mean) *discards* a lone outlier
   rather than averaging it in, so a single glitch read never colors the bar or
   enters the record. In the sample, both isolated 100°C glitches smoothed to
   55°C and 45°C - gone. The user opted into smoothing the **bar** too (not just
   notifications), because a glitch that is provably not a real temperature has
   no business flashing the gauge red.
3. **Slew/jump gate (`MAX_JUMP_C = 20`, `JUMP_CONFIRM_SAMPLES = 3`;
   `History.slewGate`).** Median-of-3 kills a *lone* spike, but a **run of 2+
   consecutive bad reads outvotes a 3-wide median** and slips through. This was
   found in the wild on 2026-07-22: with an ice pack under the laptop and the
   case cool to the touch, the archive still logged burst excursions to
   98-101°C that snapped back to ~50°C - physically impossible for the real die
   temperature, and pinning to a suspiciously round 100 just like the
   development glitches, but 2 polls long instead of 1, so the median passed
   them. The gate sits downstream of the median and refuses to *move* the
   accepted metric by more than `MAX_JUMP_C` in a single poll until the new
   level has *held* for `JUMP_CONFIRM_SAMPLES` polls. So a brief burst is
   ignored (the metric holds its last good value) while a genuinely sustained
   excursion is accepted after ~9 s - the same confirmation philosophy as the
   notification debounce, and harmless for the same reason (hardware throttling,
   not this gauge, is the safety net), with nothing ever permanently hidden. A
   normal gradual rise stays within `MAX_JUMP_C` every poll and passes through
   with **zero** lag; only a physically-impossible single-poll leap engages the
   gate. `MAX_JUMP_C = 20` sits well above any real per-poll change (genuine
   bursts ramp only a few degrees per 3 s poll) yet far below the ~50°C
   one-poll leap of a glitch. These numbers were set from the coarse 30 s
   archive; the fine-grained per-core capture (2026-07-22, see defense 1) later
   confirmed the burst shape and, more importantly, localized the root cause to
   two stuck core sensors - now handled upstream by the spatial reject. That
   makes this gate a **secondary** backstop for short all-core bursts rather
   than the main line against the Core 8/12 glitch. The gate's de-noising state
   is reset across a sampling gap
   longer than `GAP_BREAK_SECONDS` (suspend, shell restart), so a stale pre-gap
   value cannot be held after resume. The gate logic is pure and lives in
   `history.js`, unit-tested in `test-history.js`.
4. **Notification debounce (`CONFIRM_SAMPLES = 3`).** A severity must hold for 3
   consecutive polls (~9 s) before it fires, and fires **once** on the way up
   (not every poll while it stays hot). This catches the residual 1-2 poll
   excursions that survive smoothing. The number is sized from the data:
   smoothing + N=3 fired **2** notifications over the 10 min, both inside the
   genuine burst; the two glitches fired nothing. ~9 s of confirmation delay is
   harmless because the hardware's own thermal throttling - not this widget - is
   the actual safety mechanism; the popup is purely informational.

Recovery is **not** notified (the gauge color shows it). And notifications
reuse **one** `MessageTray.Source` + one `Notification`, updated in place,
rather than creating a fresh source per fire: the old per-fire-source behavior
stacked dozens of separately-dismissable banners during an oscillating hot
spell, which is what made them feel impossible to clear. The widget also
destroys its own source on `disable()`, so disabling the extension now clears
its notifications (they used to outlive it, owned by the message tray).

## Persisted history

The temperature history is written to an on-disk archive at
`~/.local/state/temperature-bar/history.jsonl` (XDG_STATE_HOME), one JSON
object per line: `{"t": <unix_ms>, "c": <°C>}`. Three reasons it exists rather
than the history living purely in memory:

1. **Testable graph.** A nested test shell (see [How to test a
   change](#how-to-test-a-change)) seeds its graph from the archive, so the
   graph and its rendering can be checked against real data immediately instead
   of waiting for a fresh buffer to fill.
2. **Long-term trends.** The in-memory graph only spans 2 h; the archive keeps
   30 days, so "is it running hotter this month than last week?" is answerable.
3. **Interpretable by Claude.** The file is plain JSONL at a known path, so it
   can be handed to Claude to read and interpret (`cat` it, or point Claude at
   the path).

Design choices, with the "why":

- **A sample is persisted every 30 s, not every 3 s.** The gauge still polls
  every 3 s (responsiveness, notifications), but 30 s resolution is plenty for
  trends and keeps the file ~10x smaller: ~2,880 lines/day, ~3 MB across the
  30-day retention. The file is pruned to retention on startup and hourly, and
  the prune only rewrites the file when something actually ages out.
- **Exactly one instance writes at a time, chosen by a heartbeat lock file**
  (`~/.local/state/temperature-bar/writer.lock`, `{pid, bootId, ts}`). This is
  the answer to "if both my real session and a `--nested` test shell are
  running, who saves the data?" - **without** the widget needing to know
  whether it is nested (which an extension cannot reliably detect anyway).
  Every instance re-reads the lock each poll; whoever finds no *live* writer
  claims it and rewrites the lock every poll as a heartbeat, while everyone
  else just reads the archive to seed their graph. A claim counts as live only
  if its heartbeat is fresh (< 12 s), it is from the current boot (`bootId`
  guards pid reuse across reboots), and the holder's pid still exists in
  `/proc`. So: your main session is normally the sole writer; a nested test
  shell launched alongside it sees a live writer and stays a read-only
  reader (getting the seeded graph you wanted); and if the main session logs
  out, any still-running instance takes over writing within a few seconds, so
  the single archive keeps growing across logouts and reboots. A writer that
  is disabled cleanly deletes its own lock so takeover is instant rather than
  waiting out the staleness window. The election logic is pure and lives in
  `history.js` (`canClaim`), unit-tested in `test-history.js`.
- **Why a heartbeat lock rather than an OS file lock or D-Bus name?** GJS has
  no `flock`, and a `--nested` shell launched via `dbus-run-session` sits on a
  *separate* session bus, so D-Bus name ownership cannot coordinate across the
  two. A heartbeat file is the portable primitive that works regardless.

## Dev loop caveat

The container cannot run GNOME Shell, so UI and IO changes cannot be verified
from inside it. The **pure logic** (history parse/serialize/prune and the
writer-election decision) lives in `history.js` and IS runnable in the
container:

```bash
node --test scripts/temperature-widget/test-history.js
```

Sensor discovery, the severity state machine, the actual file IO, and all
rendering still need an install + shell load on the laptop to check (see [How
to test a change](#how-to-test-a-change)).
