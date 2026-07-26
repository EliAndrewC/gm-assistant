# Feature Specification: The Overlap Matrix (systemic overlap rules for settlement maps)

**Feature Branch**: `main` (session-clone workflow, as for features 002-016)

**Created**: 2026-07-26

**Status**: Draft

**Input**: GM: "we probably need something like what cities have for our rural settlements like towns and villages where we have lists of things which can't overlap. Currently it's like playing whack-a-mole where every time we make a new map, I see a few more things which have never happened to overlap before but now they do. So I'd like to make sure our automated checks aren't just individually listing 'X cannot overlap with Y, N cannot overlap with M, etc' and are being more systemic about it. This will also help if we add new map features, so we can simply just add them to the 'cannot overlap with stuff' list. As opposed to e.g. grazing land, which can overlap with stuff because e.g. a well or a building can be built on grazing land, so overlap there is fine."

## Context

Two defects on the Ubame map prompted this: a magistrate's manor overlapping a road (fixed in
feature 016 by adding `manor_walls_clear_of_ways`) and **dry crop fields overlapping a
watercourse** (still present: 1 dry plot over the stream). The second is the interesting one,
because no check governs it and the reason is structural rather than an oversight.

**The existing registry is not the thing the GM thinks it is.** `_OVERLAP_STRUCTS` is not a
city feature - it runs at every tier. Its limit is a different axis: it models
**structure x hazard** (a building against a road, wall, stream, moat, torii...). It has no concept
of **ground x ground**, which is exactly where `dry_plots x water` lives. Adding the manor check
worked and the dry-plot defect stayed invisible because the two sit on opposite sides of a gap in
the *model*, not a gap in a list.

**The scale of the gap, measured.** A pool-wide survey of every pair of drawn features found
**101 distinct feature-type pairs that actually overlap somewhere in the pool**, and **none of them
is classified**. The legitimate ones - `commons x houses`, `field_ditches x fields`,
`threshing_yards x houses` - are legitimate only by accident of nobody having written a check.

**A finding that must shape the design.** That survey has substantial false positives, because it
compared *recorded envelopes*. Several features record an ENVELOPE that is much larger than what is
drawn inside it: a `commons` polygon is an outline containing a sparse grass scatter; a
`village_groves` record is a belt outline whose drawn objects are its clumps; a `fields` outline is
a smoothed curve that bows outside the plots actually tiled within it. A matrix that tests envelopes
would reproduce those false positives, block legitimate maps, and be switched off - so the matrix
must test **drawn extents**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adding a new map feature protects it against everything (Priority: P1)

An author adds a new feature to the engine. They classify it once. From that moment it is
protected against every other feature it should not overlap, and permitted to overlap the things it
legitimately may - with no per-pair rules to write and nothing to remember.

**Why this priority**: this is the GM's actual request. It ends the whack-a-mole.

**Independent Test**: add a feature key, give it a class, run the suite; it is refused overlap with
every incompatible class without any new check being written.

**Acceptance Scenarios**:

1. **Given** a new feature key with a declared class, **When** the gate runs, **Then** it is refused overlap with every class the matrix forbids, with no per-pair code.
2. **Given** a new feature key with NO declared class, **When** the suite runs, **Then** a test fails naming that key.
3. **Given** a pair the matrix forbids, **When** a map draws them overlapping, **Then** the gate fails naming both features and their position.

---

### User Story 2 - Permissive ground stays permissive (Priority: P1)

Grazing land, pasture and scrub can be built on. A well or a building standing on grazing is
correct and must never be reported.

**Why this priority**: the GM named this explicitly. A matrix that flags legitimate overlaps is
worse than no matrix - it trains everyone to ignore it.

**Independent Test**: a map with a well and a building inside a grazing commons passes.

**Acceptance Scenarios**:

1. **Given** a building inside a grazing commons, **When** the gate runs, **Then** nothing fires.
2. **Given** a feature whose record is an ENVELOPE around a sparse scatter, **When** the matrix tests it, **Then** it tests the drawn extents, not the envelope.

---

### User Story 3 - The dry-plot defect is caught by the system, not by a bespoke rule (Priority: P2)

The motivating bug - a dry crop field over a watercourse - is caught because GROUND and WATER are
incompatible classes, not because someone wrote `dry_plots_clear_of_water`.

**Independent Test**: the current Ubame manifest fails the matrix on that plot before the fix, and
passes after, with no pair-specific code anywhere.

**Acceptance Scenarios**:

1. **Given** the pre-fix Ubame manifest, **When** the gate runs, **Then** the matrix reports the dry plot over the stream.
2. **Given** a hypothetical paddy over a road, **When** the gate runs, **Then** the matrix reports it, though no such map exists.

---

### Edge Cases

- **Envelope vs drawn extent** (above) - the central correctness risk.
- **A feature legitimately ON another**: a bridge over water, a sluice on its channel, a ward gate on its fence, a water gate on the wall, in-field ditches on their own paddy. These are real and must be expressible.
- **An annex belongs to a parent**: a threshing yard, dooryard garden, farm shed or merchant kura abuts *its own* building and nothing else. The exemption must be scoped to the parent, not blanket.
- **Same-class pairs differ**: two watercourses may meet at a confluence and two ways at a junction; two buildings may not share ground.
- **Tolerances**: a hairline stroke floor means a drawn ditch is wider than its true width. The matrix must not fire on stroke-width slop where the true geometries are clear of each other.
- **A pair that is legitimate on one tier and not another** - if any exist, the matrix must be able to say so rather than forcing a global answer.

## Requirements *(mandatory)*

- **FR-001**: The system MUST classify every geometric feature key into exactly one overlap class.
- **FR-002**: The system MUST define a pairwise policy between classes, **forbidden by default**, with every permission carrying a recorded reason.
- **FR-003**: The system MUST enforce that policy in a single general check rather than per-pair checks.
- **FR-004**: The system MUST fail loudly, naming the key, when a drawn feature key has no class.
- **FR-005**: The system MUST test **drawn extents**, never envelopes, for any feature whose record is an envelope around sparse drawn objects.
- **FR-006**: The system MUST support per-pair exceptions for genuine cases (bridge over water, sluice on channel, ditch on its own field), each with a reason.
- **FR-007**: The system MUST scope annex exemptions to the annex's OWN parent, so an annex overlapping a *different* building is still a defect.
- **FR-008**: Permissive ground cover (grazing commons, pasture, scrub) MUST permit anything built on it.
- **FR-009**: The system MUST classify all 101 currently-co-occurring pairs, distinguishing real defects from measurement artifacts, and fix the real ones.
- **FR-010**: Existing per-pair overlap checks that the matrix subsumes SHOULD be retired, so there is one source of truth; any kept MUST have a reason.
- **FR-011**: The matrix MUST NOT fire on stroke-width slop where true geometries are clear.
- **FR-012**: The dry crop plot over the stream on the current map MUST be fixed.

### Key Entities

- **Overlap class**: a named category with a policy row. Draft set: `SOLID`, `GROUND`, `WATER`, `WAY`, `COVER`, `OVERLAY`, `VEGETATION`, `ANNEX`.
- **Policy matrix**: class x class -> FORBIDDEN | ALLOWED(reason).
- **Exception**: a per-key or per-key-pair override with a reason.
- **Drawn extent**: the geometry actually inked, as opposed to a recorded envelope.

## Success Criteria *(mandatory)*

- **SC-001**: Adding a new feature requires exactly one classification line to be fully protected; demonstrated by a test that adds a synthetic key.
- **SC-002**: An unclassified key fails the suite by name.
- **SC-003**: All 101 co-occurring pairs are resolved to FORBIDDEN-and-clean or ALLOWED-with-reason; none is left implicit.
- **SC-004**: The motivating dry-plot-over-water defect is caught by the general matrix with no pair-specific code, and then fixed.
- **SC-005**: Zero false positives on the existing pool: every map passes, and every permission is a recorded judgment rather than a silenced failure.
- **SC-006**: The number of hand-written per-pair overlap checks decreases.
- **SC-007**: 100% coverage maintained; every pool map still passes.

## Assumptions

- The class set above is a starting point and may change during classification; the spec fixes the *mechanism*, not the final class names.
- "Drawn extent" is available for every envelope-recording feature, or can be recorded; if a feature's drawn objects are not in the manifest, recording them is part of the work (the same conclusion the scrub-on-a-roof defect reached).
- Tier-specific policy is supported only if a real case appears; otherwise the matrix is global.
- Work happens in the session clone on `main`, as for features 002-016.
