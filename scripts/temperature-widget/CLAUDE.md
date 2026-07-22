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
bad range (critical urgency, stays on screen), and a quiet one when it
recovers to normal.

Targets GNOME Shell 42 (Ubuntu 22.04, mujina).

## How to test a change

**Always run this ON THE LAPTOP, not inside a container** - the container
cannot run GNOME Shell, so no UI change can be verified from inside it (see
[Dev loop caveat](#dev-loop-caveat)). After editing `extension.js`:

1. **Install the new copy:**

   ```bash
   ./scripts/temperature-widget/install.sh
   ```

   This copies `extension.js` + `metadata.json` into
   `~/.local/share/gnome-shell/extensions/temperature-bar@mujina/` and enables
   it via gsettings. The copy is what any shell (real or nested) loads.

2. **Load it into a shell.** Pick based on session type and how disruptive you
   want to be:

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
- **History is in-memory only** (2 h of one-sample-per-3-s, ~2,400 entries):
  trivial memory, no disk writes, and it resets on shell restart or logout -
  acceptable because the question it answers ("has it been getting hotter?")
  is about the current sitting, not yesterday. The graph's y-scale is FIXED
  at 40°C..crit rather than auto-fit, so two glances an hour apart are
  directly comparable; a sampling gap longer than 30 s (suspend, shell
  restart) breaks the line instead of drawing a fake straight segment
  across it.
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

## Dev loop caveat

The container cannot run GNOME Shell, so UI changes cannot be verified from
inside it. Logic (sensor discovery, severity state machine) is covered by a
Node harness with stubbed GNOME imports that was run against the real `/sys`
during development; visual changes need an install + shell load on the laptop
to check (see [How to test a change](#how-to-test-a-change)).
