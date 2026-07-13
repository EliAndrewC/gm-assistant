# Contract: Knob Interface (Mode B generator)

The diagram skill is an internal library/CLI, not a networked service; the "contracts" are the interfaces the generator and validator expose to a village-spec author (`pool/<name>.gen.py`) and to the test suite. Exact function signatures are an implementation detail (settled in `/speckit-tasks` + implementation, TDD-first); this file fixes the *behavioral* contract those signatures must honor.

## C1. Knob declaration (spec author surface)

- A village spec MAY pin any knob and MUST be able to leave any knob unset. Pinning uses the existing `s.meta(...)` declaration surface (extended with knob fields) or an equivalent explicit call - no knob requires hand-placed pixel coordinates.
- Unset knobs are resolved by an INDEPENDENT deterministic roll from the map seed (one draw per knob), filtered by the knob's historical-typing rule.
- A minimal spec (`seed` + `scale` + `down_deg` + water-source `kind` [+ optional `region`]) MUST produce a complete map with every other knob rolled.
- **Contract test**: a minimal spec generates a gate-passing map with zero hand-placed coordinates (SC-004); the same spec + seed regenerates byte-identically (SC-006 determinism).

## C2. Roll contract

- `roll(seed, knob_name, context)` is a pure function of (seed, knob_name, already-resolved context): deterministic, independent per knob, no wall-clock/nondeterministic entropy.
- The roll draws only from values whose `typing_rule` holds in `context`; if the filtered value space is empty, that is a spec error (loud failure), not a silent default.
- **Contract test**: two specs differing only in `seed` roll different knob combinations (US2); a given (spec, seed) always rolls the same combination.

## C3. Typing / validity contract

- A pinned knob value that violates its `typing_rule` (invalid for the stated geography or conflicting with another resolved knob) MUST be rejected or warned - never silently drawn (FR-004, FR-012).
- **Contract test**: pinning an incompatible value (e.g. a `mulberry_fishpond` overlay in a dry-upland region) fails/warns rather than producing a map.

## C4. Per-map gate contract (unchanged)

- Every generated map - rolled or pinned - MUST pass the existing `check_village` gate (all current invariants) plus any new per-knob/per-archetype validity rules.
- **Contract test**: `test_villages` regenerates the whole pool and the gate is green for all six existing maps after the knobs land.

## C5. Twin-detector contract (pool-level)

- Given a set of village manifests, the detector reports, for each same-`down_deg` pair, whether they differ on at least the threshold number of SC-001 structural axes.
- A pool with a twinned same-`down_deg` pair MUST be flagged; a pool where every same-`down_deg` pair differs on >= threshold axes passes.
- **Contract test** (negative fixture): a deliberately-twinned pair FIRES the detector; the re-varied Kikuta/Hoshigaoka pair PASSES.

## C6. Archetype plug-in contract (later phases)

- A new field/settlement/land-use archetype registers: its geometry generator, its settlement-placement logic, and its archetype-specific validator rules (so the per-map gate includes them), plus its grounding in `settlements.md`.
- An archetype value is region-typed; a roll excludes archetypes invalid for the stated geography.
- **Contract test**: a map built with a non-default archetype passes a gate that includes the archetype's rules; the archetype's grounding is recorded.

## Non-goals (explicit)

- No change to the map palette, glyph library, render pipeline, or scale ladder.
- No networked/API surface; no persisted store.
- No preset "village type" bundles (rolls are independent per knob, per D3).
- Byte-identical preservation of the four non-twinned maps is not required, but they MUST keep passing the gate.
