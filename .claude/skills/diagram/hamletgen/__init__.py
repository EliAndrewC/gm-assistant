"""SCRIPTED HAMLET GENERATION - the experiment (GM 2026-08-11).

WHAT THIS IS. A Mode B hamlet map is currently AUTHORED: a session writes a `.gen.py` by hand,
choosing the canvas, the sluice, the cluster center, the lane polylines, the pond rectangle, the
woodland patches and the windbreak belt as literal coordinates, then iterates against
`check_village.py` until the gate is green. That works, and it is slow. This module asks the GM's
question - "could a script do each of those steps instead?" - and answers it for the SIMPLEST tier,
the rice-farming hamlet, with `pool/hamlets/ikegami.gen.py` as the reference subject.

IT DOES NOT REPLACE ANYTHING. Nothing here is imported by `settlement.py`, `check_village.py`,
`waterfields.py` or any pool generator, and no existing map changes by a byte. It is additive: a
new module, its own tests, and its own demo maps in `pool/hamlets/` (marked `meta.generated_by` in
their manifests). Delete the module and those maps and the current method is exactly as it was.

WHAT IT IS NOT. It is not the knob engine - `Settlement.roll_village` (feature 005) already rolls a
gate-passing hamlet from a seed, and Honda and Shimizu in `pool/hamlets/` are the proof. This module
STANDS ON that work and closes the gap between what it produces and what a hand-authored map like
Ikegami contains, which is where the interesting engineering turned out to be:

  | Ikegami (authored)                 | roll_village          | here                            |
  |------------------------------------|-----------------------|---------------------------------|
  | drainage tameike at the low foot    | source pond only      | DERIVED from the drain outfall  |
  | a connector track running off-map   | none                  | DERIVED, steered clear of crops |
  | managed-woodland patches            | none                  | DERIVED by an open-ground scan  |
  | draft byres among the homesteads    | none                  | drawn                           |
  | field sized to the household count  | a hand-passed `fall`  | SOLVED for, to a real acreage   |
  | cluster with its back to the wind   | a lateral margin band | seated on the 背山面水 margin     |

THE ORDER IS THE DESIGN. `STAGES` below is the pipeline, and it is the same order a human follows
and the same order the engine's DRAW ORDER map (skill CLAUDE.md) requires - water, then the field
the water shapes, then the sink the field drains to, then the ways, then the homesteads that front
the ways, then their appurtenances, then ground cover, then the woods, then the frame. Each stage is
a module-level function of `(s, plan)`, so the sequence is readable in one place and every stage is
separately testable.

DERIVE, NEVER PIN. Every position in this module is computed from geometry that is already on the
map: the cluster from the field envelope's margins, the pond from the drain's last vertex, the
connector from the lane skeleton's gateway, the woodland from a scan of what ground is still open,
the windbreak from the houses that actually landed. That is the project's standing rule (a pinned
coordinate silently becomes false when the thing it referenced moves), and it is also what makes a
SCRIPT possible at all: a stage that reads the map can run at any size, seed or fall direction.

THE CHECKS ARE THE ORACLE, NOT A POST-HOC AUDIT. `generate()` runs `check_village.gate()` in-process
on the manifest it just built and returns the failures with the map. The GM asked whether the checks
should run per-placement or per-round: per-ROUND is right, and the reason is structural. The placer
(`Settlement._fits` and friends) already refuses an overlapping seat, so the overlap checks are a
formality that should never fire - running them after each house would cost a full gate per house to
re-prove something placement guarantees. What the gate actually catches is EMERGENT: acreage against
household count, a marsh that ended up uphill, a windbreak on the lee side, a connector that stopped
short of the edge. Those are properties of a FINISHED map, so they are checked once, on the finished
map. Where a stage can fail locally and recover (the cluster not seating every household) it retries
INSIDE the stage against the placer's own verdict, which is cheaper and more precise than a gate run.

Run it:
    python3 -m hamletgen --name Ikegami-scripted --seed 4 --households 15 --out wip/x
    python3 -m hamletgen --batch 12          # roll a whole cohort and gate every one
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
if SKILL not in sys.path:  # so the package works when run from anywhere
    sys.path.insert(0, SKILL)  # pragma: no cover - under pytest the skill dir is already on the path

# DERIVED SURFACE (feature 111, constitution clause 14): the star imports ARE the re-export
# mechanism - every submodule's public names resolve from the package root exactly as they did
# from the monolith, so `from hamletgen import HamletSpec, generate` and `hg.<anything>` keep
# working with zero consumer changes. The aliased block below carries the four underscore names
# with external consumers, which a bare star import silently DROPS. The bootstrap above must run
# BEFORE any of it (submodules import `settlement` and `waterfields` by absolute name), which is
# why the imports are not at the top of the file. Guard: tests/hamletgen/test_surface.py. No logic here.
from .cluster import *
from .cluster import _arm_crossing_accidental as _arm_crossing_accidental
from .cluster import _fork_spur as _fork_spur
from .consts import *
from .driver import *
from .frame import *
from .geom import *
from .hinterland import *
from .hinterland import _clear_gap as _clear_gap
from .hinterland import _near_line as _near_line
from .homesteads import *
from .plan import *
from .sink import *
from .water import *
from .ways import *
