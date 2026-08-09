# Implementation Plan: The capital's ground-reserving layer

**Branch**: none - `main`; active feature via `export SPECIFY_FEATURE=020-capital-ground-layer` | **Date**: 2026-08-09 | **Spec**: [spec.md](spec.md)

## Summary

Draw everything that reserves ground onto the Shiro Daika skeleton, so feature 021's housing can flow around it rather than be re-packed.

**The central planning finding: this layer is mostly REUSE, not new vocabulary.** The engine already draws walled samurai estates, state offices, granaries, docks, jetties and temple halls. Mapping each new institution onto the glyph it actually is keeps the new surface to two features and avoids inventing a second way to draw a thing the pool already draws:

| Institution | Drawn as | Why that glyph |
|---|---|---|
| the eight lineage compounds | `manor` | they ARE walled samurai estates; the manor glyph is walls + gate + implied interior, which is exactly the convention a lineage seat wants |
| six domain ministries, House Chancellery, domain school | `ministry` | state offices in state violet - the colour already carries "government", and the chancellery and school are government |
| Imperial Magistrate's compound | `manor`, with its own ink | foreign sovereign ground: a walled compound, but it must NOT read as another domain office, so it takes the manor form and a distinct colour rather than the ministries' violet |
| the Emperor's granaries, the domain granary | `granary` | already a raised slat-sided store |
| the two sovereign temples + teramachi rim | `shrine_hall` | already the temple precinct glyph |
| wharf, dock, jetties, quay | `dock` / `jetty` | built for Nagahara's river frontage; a capital's is bigger, not different |
| brokers' row | `frontage` of shops | it is a merchant street, per the GM's ruling that the row is merchant and not a ministry annex |

**Genuinely new**: `towpath` and `aqueduct`. Both are linear water-adjacent features with no existing analog.

## Technical Context

**Language**: Python 3.14 | **Dependencies**: none new | **Testing**: pytest (`test_settlement.py`, `test_checks.py`, `test_villages.py`)

**Constraints**: the pool must stay byte-identical; every new key must be a LIST of dicts (feature 019's lesson); everything drawn here must reserve ground in the registry the packer honors.

## Constitution Check

- **I / II**: N/A - no UI. **IV / V**: N/A / PASS - no SOURCE blocks.
- **III. Pool Data Conventions**: PASS - the map remains a draft in `wip/`; no pool member changes.
- **VI. Verify Before Reporting Done**: PASS - linters, whole affected test files, `make done` once backgrounded, pool byte-identity, plus the two artifact gates.
- **VII / IX. De-localized generation / Setting Integration**: PASS - the engine stays generic; only the gen is Daika-specific. Lineage names and weights come from the chargen config, the temples from `CLAN_FORTUNES`, the institutions from `budgets.md`.
- **X. Python Discipline**: PASS - ruff, `mypy --strict`, red-green TDD, 100% coverage.
- **XI. Japanese Authenticity**: PASS - *ote-suji*, *hanko*, *kuramae*, *qiandao*/towpath, *josui*, *kakehi* all used in their attested senses (018's research.md carries the sources).
- **XII. Historical Grounding Bookends (NON-NEGOTIABLE)**: **Opening inherited** from 018's research.md - this layer adds no world-assertion those findings do not already settle. **Closing applies again**: re-examine the render against them before done.

## Design decisions

### 1. Reuse the glyph, vary the ink and the label

Stated above. The one place a NEW look is required is the **Imperial Magistrate's compound**, which must read as not-of-the-domain; that is a colour parameter on the manor form, not a new glyph.

### 2. The two new linear features

- **`towpath(pts)`** - a narrow beaten path on one bank. Drawn deliberately UNLIKE a road: no roadbed fill, no dashed centre line, a hairline at the linework floor. It exists because of upstream haulage, so it runs to the wharf and stops.
- **`aqueduct(pts, intake=...)`** - an open channel outside the wall, its intake works on the river, terminating at a gate. **No arcade** - the form does not exist in either anchor tradition. Inside the wall it is not drawn at all; its draw-basins are 021's, with the wells.

### 3. The bridging fix, and what it is really about

`bridges()` carries `M["road"]` but not `M["roads"]`, and its water list omits `M["river"]` and the castle moat. `roads_bridge_water` mirrors those omissions exactly - so the two agree perfectly and are both wrong.

**Fix BOTH sides from one shared source.** The existing rule says placement and its check must read the same manifest source; this is the case that shows the rule guarantees *agreement*, not *correctness*. So the fix is not "add the missing keys twice" but "derive the carried-ways and the crossed-waters ONCE and have both sides consume it", with a comment saying why - otherwise the next omission reproduces the same silent symmetry.

### 4. Re-zone the quarters

`quarters[0]` marks NE "civic" and calls it the castle's ground, but the castle straddles all four wedges and the ministries belong SOUTH of the ote-mon. Re-zone so the civic quarter is the ground the government actually occupies.

## Verification strategy

1. `ruff format` + `ruff check` + `mypy --strict`
2. whole affected test files, `-n auto`, never `-k`
3. **render and LOOK** - `settlement-review` scoped as a DELTA, launched the moment the map is final; then Principle XII's closing gate against 018's research.md
4. `make done` once, backgrounded, log tail read before believing green
5. `git status --porcelain -- pool/` empty

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| The feature ends with the map still not green | Population cannot pass until housing lands in 021, and draw order forbids housing first. | Drawing housing here would mean re-packing it around this layer - the exact rework the split exists to avoid. The map stays a draft in `wip/`, which is where a non-green map must live. |
