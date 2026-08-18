# Research: what makes a fan of lane ends a defect

## R1. The finding, and why the battery could not see it

A `settlement-review` read Mizuguchi's east node at 3x zoom as **a broom**. Three ways leave one point
at bearings 19.7 / 8.7 / 356.8 degrees - a 22.9 degree total spread, adjacent gaps of 11.0 and 11.9 -
and two of them end blunt in open ground.

Two rules should have caught it and neither did, for reasons worth keeping:

- **`lanes_reach_something`** asks each lane end to reach a way within 40 ft OR a farmhouse within 90.
  All three blunt ends claimed the **same** house, at 66.9, 55.1 and 40.0 ft. Nothing said a house
  could only discharge one end's obligation, so one farmhouse was answering for three ends standing
  within 40 ft of each other.
- **the lane web's shadow rule** refuses a new web run that parallels an existing way. Both offending
  arms are SKELETON lanes, laid by `stage_ways` **before the houses exist**, so they are never tested
  against each other. Measured: lane 2 lies within 30 ft of lane 0 for **100%** of its 127 ft (median
  12.3) and within 30 ft of lane 4 for 100% of it - three treads in one 25 ft corridor.

## R2. Why the bearing clause is not optional

The naive rule - "two ends may not front the same house" - is wrong, and the cohort says so loudly. A
house reached by two lanes from **opposite quarters** is a house on a corner: a real arrangement that
reads as one thing, not as a fan. Without a bearing test the rule flags most of a nucleated cluster's
middle, which is the opposite of what it is for. The fan is specifically ends arriving **alongside**
each other, where the eye merges them into one frayed way.

Measured on the four pool hamlets with no bearing clause: every map fired, including two pairs that
are plainly ordinary crossroads.

## R3. Why "blunt" has to mean what `_FRAY_DEG` already means

The first draft exempted any end within 40 ft of another way, on the reasoning that such an end is a
junction rather than a tine. That silently un-fired the motivating fixture - because the reviewer's
blunt ends stood **21.6 and 24.3 ft** from another way, i.e. inside that reach, and near-parallel to
it. They had not MET that way; they were running alongside it.

The engine already knows this. `trim_lane_stubs` carries `_FRAY_DEG = 20.0` with the note *"a lane
that meets another CROSSES it; one that FRAYS runs alongside it. Proximity alone is not arrival"* -
added after an earlier round found a lane satisfying the test written for it by being near the very
lane it had already met. The check restates the same 20 degrees (the gate does not import the
generator it gates), and the fixture fires again.

**The transferable rule:** when a new check needs to know whether two ways have met, it needs the
fray clause too. Distance alone has now been wrong twice, in two different checks, for the same
reason.

## R4. The fix, and why it belongs in the trim rather than in the placer

The reviewer's own minimum change was *"trim lane 2 back to the node - it is 100% shadowed by lane 0
over its whole length and costs nothing"*: the only house it serves is 23.7 ft from another lane.

`trim_lane_stubs` is the right home and needed only one clause. It already runs after placement, only
ever SHORTENS (so it cannot invalidate a seated house), and rewrites ink in the stream slots a lane
already owns. What it lacked was exclusivity: its house test asked *is there a farmhouse within 90
ft*, when the question is *is there a farmhouse within 90 ft that no better-placed end is already
fronting*. The end NEAREST the house keeps it; any end alongside it, pointing the same way, must find
its own reason to exist or be trimmed until it does - and if that leaves it under one homestead's
frontage, the existing floor drops it, which is exactly the reviewer's suggested outcome.

Fixing it in the PLACER was considered and rejected: `stage_ways` lays the skeleton before the houses
exist, so at that moment there is no house to be fronted twice and nothing to test against. The
information the rule needs does not exist until placement is done.
