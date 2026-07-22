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
getting hotter" questions. The extension also sends desktop notifications the
moment the temperature crosses INTO the warning range (normal urgency) or the
bad range (critical urgency, stays on screen). It does NOT notify on recovery -
the gauge color already shows that, and a "back to normal" popup is just noise.

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
  script - a single core can spike above the package reading.
- **Hysteresis (4°C) on the way down**: severity drops only once the reading
  is clearly below the threshold. Without it, a CPU hovering at 89-91°C would
  flip between green and orange every poll and re-send the "running hot"
  notification each time it crossed upward again.
- **Sensors are discovered by filename, never by counting**: coretemp's
  `tempN` numbering is sparse on this chip (temp1, temp2..temp10, temp14,
  ...), so a `for i in 1..N` loop that stops at the first gap would silently
  miss most cores.
- **Polling is a 3-second sysfs read** - a handful of small in-kernel file
  reads, negligible cost, and fast enough to catch a thermal runaway before
  it reaches throttling.

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
