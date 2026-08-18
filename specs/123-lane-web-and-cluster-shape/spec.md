# Feature 123: The lane web, and a cluster that matches its rolled shape

**Status**: specified
**Created**: 2026-08-18
**Origin**: GM rulings of 2026-08-18 on the three questions in
`.claude/skills/diagram/future-work.md`, plus the research pass those rulings required.

## Why this exists

A `settlement-review` escalated three questions as "rulings wanted". The GM ruled on the ASKING as
well as the questions (now constitution Principle XII, v1.9.0): research precedes a ruling, and
where research supports two answers the generator VARIES rather than picks. The research pass then
settled two of the three outright. This feature is what those answers oblige.

Question A needed no code. Questions B and C do, and they are one feature because both are the same
defect wearing different clothes: **the map does not deliver what the generator promised.**

## User scenarios

### US1 (P1) - Every farmhouse can be reached

A GM prints a scripted hamlet and traces the way from the road to any house on it. Today that fails
for roughly a third of the houses: Sawada seats 19 farmhouses and 9 of them stand more than 120 ft
from any drawn way, with a worst case of 290 ft and an entire SE block touched by nothing; Inashiro
is 6 of 15 with a worst of 362 ft. The research is decisive that this is wrong - a nucleated
cluster's compactness exists precisely so that "every house in the nucleated village is accessible
via the interconnected system of narrow lanes and alleys" (see
`.claude/skills/diagram/research/homesteads.md`). The back rank being reached "along unfigured
footpaths" was a defensible-sounding reading with nothing behind it.

**Independent test**: roll any scripted hamlet; no farmhouse is beyond a lane's reach, and the gate
enforces it.

### US2 (P1) - Two hamlets with the same water and the same skeleton still read as two places

The research supports two forms of that access, and per Principle XII both must be drawn, chosen per
settlement on a seeded knob:

- **alleys** - narrow laterals off the spine between plots, colonised as semi-private space by the
  houses they pass. The accretive Chinese gridiron form; it says the place grew.
- **back_lane** - a way parallel to the main lane behind the plots, which doubles as the edge
  between the village and its fields. The planned form; it says the place was laid out.

**Independent test**: across a 24-seed cohort both forms appear, and a map's `meta.lane_web` matches
the geometry actually drawn.

### US3 (P2) - A rolled knob is honored, or the map does not claim it

`cluster_shape` is rolled on every scripted hamlet (`round`/`elongated`/`crescent`), and on every
scripted hamlet it is then ignored: `stage_homesteads` seats houses by rows and frontage, and the
map records `meta.cluster_seeding` instead - a trace that says, in writing, that the rolled shape
went unhonored. The GM's ruling on question B: *"when we do not ask for something and the knob is
set randomly, then we still want what is drawn to match what was randomly selected for the knob
value."* A knob nothing reads is not variance; it is a number in a log.

**Independent test**: a hamlet rolled `elongated` measures visibly more elongated than the same seed
rolled `round`, and the twin detector's `cluster_shape` axis distinguishes them.

## Functional requirements

- **FR1** Every farmhouse in a scripted hamlet is within reach of a drawn way. "Reach" is a stated
  distance with a stated basis, not a number chosen to make the current maps pass.
- **FR2** A `lane_web` knob is rolled per settlement over `("alleys", "back_lane")` and recorded in
  `meta.lane_web`.
- **FR3** The web's geometry is DERIVED from the cluster's own frame and rank pitch - never pinned -
  and is laid in the same pre-house stage as the rest of the skeleton, because a lane is a no-build
  corridor the homesteads front.
- **FR4** Web lanes obey every existing way constraint: clear of crop, of the wet toe, of marsh, and
  they do not cross a watercourse (an internal lane stops at the bank; the spur and connector are
  the ways that leave).
- **FR5** A gate check enforces FR1 and fires on the pre-feature manifests, which are frozen as
  negative fixtures.
- **FR6** The rolled `cluster_shape` shapes the seated cluster, and `meta.cluster_shape` records
  what was drawn. `meta.cluster_seeding`'s "the rolled shape went unhonored" branch is retired.

## Success criteria

- **SC1** Across a 24-seed cohort, zero farmhouses beyond the reach threshold. Baseline: ~30%.
- **SC2** Both `lane_web` forms occur in a 24-seed cohort.
- **SC3** The cohort pass rate does not drop and no seed that passed before fails after
  (constitution Principle XIII). Baseline measured in a detached worktree at `ae1f94d`.
- **SC4** `make done` green, 100% coverage on the changed pure-logic packages.
- **SC5** `settlement-review` on each re-rolled pool hamlet reports no new ERROR.

## Assumptions

- The four live scripted hamlets re-roll; the 19 legacy maps are FROZEN and are neither regenerated
  nor re-gated.
- The village tier is not built here. It inherits this via `sitegen` when it lands.

## Out of scope

- Question A (byre beside a wellhead): research decisive, no change.
- The town and city tiers.
