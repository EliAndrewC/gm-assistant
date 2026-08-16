# Research: Review-Loop Efficiency (108)

## R1. Does the pre-gate pool-regen sweep produce anything the stop-work ritual needs? NO - verified

- **Decision**: The FR-009 rule can be unconditional: regenerate only the MOTIVATING map in the foreground (a session needs its render for its own crop inspection); never run a foreground whole-pool regen sweep before the gate. The gate verifies the pool; main's renders never come from the clone.
- **Rationale**: `scripts/sync-with-main.sh` (RENDER MODEL, GM 2026-07-22): "renders no longer flow clone -> main by copy. render-sync REGENERATES main's diagram renders in place from main's own committed tip (via render_cache.py), so a render in main is a pure function of main's code and can never be a stale copy." Clone-side renders of non-motivating maps are therefore write-only work. The 2026-08-16 cut-bank fix ran a 38s foreground `regen.py pool/*/*.gen.py` sweep whose only durable effect was warming the clone's gencache with rendered entries - the gate would have regenerated on miss anyway (in its coverage subprocess, `DIAGRAM_SKIP_RENDER=1` - `test_villages.py:141`), and render-sync then re-derived main's renders from main's tip regardless.
- **Alternatives considered**: Making the rule conditional on the gate's cache path restoring renders (`gencache.OUTPUT_SUFFIXES` includes .svg/.png, so entries built by a rendering run do carry them; entries built by the gate's own miss subprocess do not). Rejected: irrelevant once R1's finding stands - no ritual step reads clone renders of non-motivating maps, so the conditional would encode a dependency that does not exist.
- **Interaction preserved**: the existing "run the WHOLE affected test file before the gate" rule is untouched; this narrows only what ELSE runs.

## R2. SVG scatter parse anchors - verified against `settlement/land.py` (lines 362-397, 473-489)

- **Decision**: Parse four commons families plus one report-only family, keyed on the engine's stable emission styling:
  - grass blades: `<g stroke="#A7A860" stroke-width="0.8">` bucket; each `<line>` inside it is one blade whose BASE is `(x1, y1)` (three blades share one tuft base). Tips (`x2, y2`) are exempt by the disclosed blade-tip-lean departure - bases only.
  - brush dots: `<circle ... fill="#94A063" ...>` - base is the center.
  - pine trunks: `<line ... stroke="#7A6A48" ...>` - base is `(x1, y1)` (y2 is the tip). Branch strokes (`#6E8452`) are canopy ink, not bases - ignored.
  - woodland crowns: `<circle ... fill="#6E8B4A|#7C9856|#87A45C" ...>` - base is the center (crown shadow ellipses `#59703E` and sun-highlight circles are companion ink - the highlight shares the crown's fill palette? No: highlight is `#A6BA79` - distinct, ignored).
  - marsh reeds: `<g stroke="#6E9377">` bucket - REPORT-ONLY family (counted, never adjudicated against the cut-bank margin: reeds are the water fringe by doctrine).
- **Rationale**: These are the exact strings the engine emits; the 2026-08-16 review's independent parse used the same anchors and reconciled to the engine totals (231,392 bases on Inashiro).
- **Loud-failure guard (FR-004)**: zero bases parsed for every family = ERROR exit, because a styling drift would otherwise read as a clean map ("a check that never runs looks exactly like a check that passes").

## R3. Keep-out derivation without re-stating rules

- **Decision**: A minimal shim object carries the manifest (`M`), `ftpx`-derived `px()`, and `bscale`, and the audit calls the ENGINE'S OWN unbound methods on it: `Settlement._watercourse_segs(shim, channel_margin=shim.px(Settlement._BANK_MARGIN_FT))` for the water + cut-bank family, and the crop keep-out is built from the manifest's `fields[].poly` + `dry_plots[].poly` padded by `Settlement._CROP_MARGIN_FT` via the engine's `boxed_polys`/`boxed_grid`/`boxed_hit` helpers - the same helpers the scatter uses.
- **Rationale**: observe-don't-restate ("a diagnostic that restates what it observes will lie to you, or die", diagram CLAUDE.md). The executed geometry code is the engine's; a future margin change moves the audit's verdicts with no script change. Geometry comes from the MANIFEST (the "same manifest source" discipline) - the engine's in-memory registries (`field_polys`, `dry_polys`) do not exist post-hoc.
- **Alternatives considered**: re-running the generator to rebuild a live `Settlement` (rejected: "read derived data from the recorded artifact, not by re-running the generator" - and it would take ~20s per map instead of seconds); re-implementing `_watercourse_segs` arithmetic in the script (rejected: the exact drift class the doctrine forbids).
- **Known scope note**: the audit adjudicates the two families FR-003 requires (water+cut-bank, crop margins). Urban halos, corridors, pond, clearings are NOT adjudicated in v1 - the report's `families checked` line names what ran, so the omission is visible, and violations of unchecked families simply do not appear (no false PASS claim is made about them).

## R4. Performance envelope

- **Decision**: Pure-Python parse (regex over the SVG's element stream) + the engine's pre-boxed grid for adjudication.
- **Rationale**: Inashiro's SVG is 16.7 MB / 231k bases; the same grid prefilter keeps the engine's own scatter fast (per-point cost ~O(cell)). Budget: well under the SC-001 30s bound; expected low single-digit seconds.

## R5. Coverage / typing / test wiring - follow the `site_justice.py` pattern (verified)

- **Decision**: `scatter_audit` joins `[tool.coverage.run] source` and mypy `files` in the skill's `pyproject.toml`; `test_scatter_audit.py` covers it to 100% (module logic + `main(argv) -> int`; the `if __name__` guard carries the same `# pragma: no cover - CLI entry` as `site_justice.py:233`). Fixtures: a purpose-built miniature settlement rendered in-test (real engine, tiny canvas) for positive/negative adjudication, plus a doctored SVG fragment for the loud-failure path; the shipped Inashiro artifacts serve as the integration ground truth in quickstart, not as a unit fixture (committed pool bytes stay clean).
- **Rationale**: `site_justice` is the exemplar diagnostic already under the 100% gate with a CLI main tested by invocation (`test_site_justice.py` calls `sj.main([...])` and asserts exit codes).

## R6. DELTA-review value evidence (FR-006, the GM's keep/drop question)

- On record, DELTA passes have caught: 2026-08-16 Inashiro - `_fill_wedges` nesting 12 fillers wholly inside carved paddies (pre-existing, verified against the frozen manifest, fixed same day); 2026-08-15 Sawada - the bund-edge second pass (carve drop-test and gate walked bund EDGES, not just vertices, after review caught an acute junction wedge); 2026-08-16 cut-bank DELTA - confirmed the fix and put the collector-drain intent on record. The evidence supports KEEP + make cheap. The agent doc will require each notes entry's review line to keep recording what the pass caught (including "nothing"), so the question stays answerable with data.

## R7. Agent-doc edit classification

- Editing `.claude/agents/settlement-review.md` here adds a TOOL to the reviewer's kit, not a detection rule. The Subagent-check TDD procedure (docs/spec-kit-and-reviews.md: general rule first, red against the unfixed artifact) governs detection rules and does not apply; there is no motivating defect artifact to hold red. The independence constraint DOES apply: the doc must direct the reviewer to run the script themselves and interpret its output - the author's own audit run is a claim to re-verify, not evidence.
