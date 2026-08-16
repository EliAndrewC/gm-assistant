# Data Model: scatter_audit (108)

## Entities

### BasePoint
The anchor of one drawn ground-cover glyph, parsed from the SVG (the manifest does not record scatter).

| field | type | source |
|---|---|---|
| `family` | one of `blade`, `dot`, `pine`, `crown`, `reed` | emission styling (research.md R2) |
| `x`, `y` | float, world px | element attributes (`x1/y1` for lines, `cx/cy` for circles) |

Notes: three blades share one tuft base - each blade line still yields its own BasePoint (matches the 2026-08-16 review's counting, so totals reconcile). Blade/branch TIPS are never parsed (disclosed lean departure).

### KeepOut family
A rule family the audit adjudicates against, derived from the engine + manifest, never re-implemented.

| family | geometry | owner |
|---|---|---|
| `water+cutbank` | `Settlement._watercourse_segs(shim, channel_margin=px(_BANK_MARGIN_FT))` - streams at drawn width + pad, irrigation channels additionally + cut-bank margin | engine method on shim |
| `crop` | manifest `fields[].poly` + `dry_plots[].poly`, padded `_CROP_MARGIN_FT` via `boxed_polys` | manifest geometry + engine constant/helpers |

Adjudication matrix: `blade`/`dot`/`pine`/`crown` are tested against both families. `reed` is REPORT-ONLY (counted, never adjudicated - reeds are the water fringe by doctrine; their own rules are the marsh's, out of scope).

### Violation
| field | type |
|---|---|
| `x`, `y` | float |
| `family` | BasePoint family |
| `keepout` | KeepOut family name |

### Report
| field | contents |
|---|---|
| `map` | map stem audited |
| `families_checked` | the adjudicated families and the keep-out families that ran (visible-omission contract, FR-003) |
| `counts` | per-BasePoint-family parse counts (zero TOTAL -> loud failure, exit 2) |
| `violations` | list of Violation (empty = clean) |
| `density_bands` | base counts in 0-15 / 15-30 / 30-45 px beyond the water keep-out edge (sterile-halo judgment input) |

## State transitions

None - single-pass read-only diagnostic. Exit codes are the state: 0 clean, 1 violations found, 2 usage error / parse failure (including zero bases).

## Validation rules

- SVG and JSON must both exist for the map stem; missing either -> exit 2.
- Zero bases parsed across all families -> exit 2 with ERROR text naming the styling-drift hypothesis (FR-004).
- Manifest missing `meta.ftpx` -> exit 2 (cannot convert real-feet margins).
