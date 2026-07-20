---
name: diagram
description: Generate SVG diagrams of L5R/L7R locations using a consistent style library, then render to PNG. Two modes - compound/building plans (manors, magistracies, temples, keeps, battlefields; hand-authored SVG) and settlement maps (hamlets, villages, towns, and provincial cities - walled or unwalled; parametric generator plus an automated validator gate). Subjects are designed in conversation with the GM, drawn top-down in a labeled diagrammatic style, and saved in the pool.
---

# Diagrams

Generate top-down SVG plans of Rokugani locations - magistrate manors, village layouts, temple plans, military compounds, battle terrain, and the like. The skill covers the shared technical and aesthetic conventions (palette, patterns, render pipeline, historical reference framework); the mode-specific vocabulary lives in [`buildings.md`](buildings.md) and [`settlements.md`](settlements.md). The per-subject content - *what specifically goes in a given diagram* - is decided in conversation with the GM, not codified here.

The skill's first worked example is [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) (County Magistrate Kitsune Tatsuya's two-courtyard manor). All conventions below were extracted from that work, and `pool/ochiba-magistracy.svg` is the canonical template - copy it as the starting point for new diagrams and edit from there rather than rebuilding from scratch.

## Core principle: roughly to scale

Every diagram now carries a **declared scale** - the GM's scale ladder (2026-07, extended to Mode A):

| Tier | Scale | Why |
|------|-------|-----|
| Compound plan (Mode A) | **3 px = 1 ft** | interior plans need room-level legibility; a county magistracy's ~250×200 ft is authored on a 1200×900 working canvas, then the viewBox is cropped tight to the content (rectangular, minimal border - see "Framing" below; anchors in buildings.md's grounding) |
| Hamlet, town | **1 px = 1 ft** | towns crop to their core and skip most surrounding farmland, so they earn the zoom |
| Village | **1 px = 2 ft** | must show ~60-90 acres of working farmland around ~50-70 homesteads |
| Provincial city | **1 px = 3 ft** | the walled seat spans ~0.9 mi; 3 makes the wall a plausible ~2.9 mi perimeter |

The round numbers are deliberate (a human should be able to read distances off the map). Mode A compound plans are hand-authored, so they declare their scale with a **scale bar drawn on the sheet** (see the "Scale" section of [`buildings.md`](buildings.md)). Mode B declares via `s.meta(ftpx=N)`: the building grain follows automatically (`bscale = 1/ftpx` - the urban glyph library is calibrated at town scale, with the 44x29px farmhouse ~ the 46x28 ft *minka* anchor; this is what keeps a "merchant house" the same real ~57 ft on every map). Real-feet constants convert through `s.px(ft)`; linear features through `s.lw(ft)`, which applies the **4px linework floor**: standard cartographic practice - a 5 ft roji at 3 ft/px would be an invisible 1.7px, so thin linework draws at the minimum visible width, true-width-or-floored, never inflated past the floor. Villages declare `ftpx=2` for the record but keep `bscale = 1.0` (their placement constants were hand-pre-scaled to 2 ft/px before ftpx existed). Checks read `meta.ftpx` wherever a threshold means real feet (`on_a_street`'s 85 ft, the city theater's 185 ft).

Within the declared scale, maps stay **schematic, not survey-accurate** - small point glyphs (wells, torii, gate furniture) are drawn somewhat **oversized for legibility**. But that is a license to *round*, NOT a license to ignore scale: **relative sizes and distances are meant to be roughly proportional to reality.** A thing that is twice as large (or twice as far) in the world should read as roughly twice as large (or far) on the map. Hold proportions honest:

- A cemetery serving a thousand people should clearly **dwarf** one serving a hundred; a provincial city's wall should dwarf a village shrine; a manor should outsize a peasant house by about the ratio it really is.
- When you **size or place a new element**, ask "how big / how far is this relative to its neighbors in reality?" and match that proportion - don't just pick numbers that fit the gap.
- This is why glyphs already scale with the settlement grain (`s.bscale`), why a wellhead/grave/manor is sized against the dwellings around it, and why distances (set-backs, approaches, spacing) are tuned to read at the right *relative* magnitude.
- "Not literally 1px = 1 *shaku*" settles ties and rounds awkward numbers; it never excuses a feature that reads two or three times too big or too small for what it represents. When a check or a reviewer says something "looks too small/large/close," that is a real scale error to fix, not a quirk of a non-literal map.
- The *relative-size* facts that anchor specific glyphs (e.g. a threshing yard is ~1-3% of the paddy it serves in reality, but drawn near house-size for legibility) and any other research-grounded rule are recorded under **"Historical grounding: the why behind the realism checks"** in [`settlements.md`](settlements.md) (Mode A grounding lives in [`buildings.md`](buildings.md)) - per project policy, every research-driven check carries its reasoning there.

## Core principle: China first (then Japan)

Rokugan's **land** - its geography, terrain, agriculture, demographics, settlement patterns, and transport - is inspired **more by CHINA (especially Song/Ming, the rice-growing south our population density anchors to) than by Japan**. So when a map or geography question could go either way, **the Chinese answer is the guiding star**; the Japanese answer is the secondary / tiebreaker, used when the Chinese reality is ambiguous or strongly region-dependent.

- **Keep researching and documenting BOTH.** Japanese rural life is often the better-documented and the detail is genuinely useful (and much transfers - both are wet-rice monsoon-Asian societies). Record the Japanese findings as before. But when the two **differ**, resolve to the Chinese reality and say so.
- **The division of labor:** the **physical/economic** layer follows **China** - valley-bottom paddy + terraced/dry margins, nucleated villages, pond-and-canal irrigation (the *beitang*/comb doctrine), wheelbarrow-and-porter-and-boat transport, road/settlement scale. The **cultural surface** stays **Japanese** - clan and personal names, samurai caste, *kami*/Shinto shrines (torii, Inari, Benten), *minka* architecture vocabulary, the title block's Japanese terms. Draw a Japanese-flavored society **on a Chinese-shaped land**.
- **Already applied this way:** nucleated village form (Knapp: China rice-south villages of ~30-60 households); the COMB irrigation default (Chinese canal doctrine + *beitang* pond systems, the dominant village mode in rice China); demographics/budgets anchored to Song/Ming. When in doubt on a land question, ask "what was this like in the Chinese rice south?" first.
- **GM setting canon OVERRIDES the historical default.** China-first governs the UNDECIDED questions; where the GM has established world canon that diverges, the canon wins. The worked example: **artificial transport canals** are ubiquitous in Ming China but in Rokugan are a **LION-lands feature only** (other clans use natural water - coast, rivers - or land), so they are a tunable exception, NOT the Empire-wide rule (see "Village lanes and connecting paths" in [`settlements.md`](settlements.md)).

## Two modes

This skill covers two kinds of diagram that share the conventions below (palette, English-default labeling, kanji triangle, orientation, title block, label sizes, render pipeline, self-review) but differ in subject and method:

- **Mode A - Compound and building plans** (manor, magistracy, temple, keep, battlefield). Interior plan view: walls, courts, rooms, building footprints. Hand-authored SVG, copied from the canonical template [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) and edited. The Mode A vocabulary, checklist, and grounding live in [`buildings.md`](buildings.md) - read it before starting a Mode A diagram.
- **Mode B - Settlement maps** (hamlet, village, town, provincial city - walled or unwalled). Landscape/terrain plan: a settlement in its fields, with realistic house density, irregular paddies, irrigation, and a shrine. Built by a **parametric generator** with an **automated validator** gate, because ~50 placed houses and clipped irregular fields are not practical to hand-place. Canonical example: [`pool/kikuta-village.svg`](pool/kikuta-village.svg). See [`settlements.md`](settlements.md) - read it before starting a Mode B map.

## Workflow

1. **Pre-design conversation.** Talk to the GM about what's present. Ask about scale (manor vs. village vs. temple vs. battlefield), notable features (workshops, shrines, garrisons), the residing NPC(s), the surrounding context (walled? what's outside?). Pull sizing and role context from the relevant setting files (`/gm-assistant/setting/median-domain.md`, `/gm-assistant/setting/government.md`, `/gm-assistant/setting/hierarchies.md`).

2. **Pitch and confirm.** Offer the GM 3-5 distinct ideas to react to before settling on a layout. Flag any deliberate L5R divergences from historical Japan (e.g., Inari shrine as a hall rather than a standalone, on-grounds barracks rather than off-site retainer housing).

3. **Write the SVG.** Top-down plan view. North at the top of the viewBox. Main gate of any walled compound facing south (bottom). Use the style conventions below and the building vocabulary in [`buildings.md`](buildings.md).

4. **Render to PNG.** See the render pipeline section.

5. **Self-review.** Read the rendered PNG yourself. Does every named feature appear? Are labels legible? Is the layout coherent? Iterate before showing the GM.

6. **Report to GM.** Describe what changed, what's deliberately absent, where the diagram diverges from history (Edo vs. Sengoku vs. L5R), and offer a historical-accuracy review pass.

## Labeling rule: English-default

Use **English** for commonplace nouns: `latrine`, `bath`, `granary`, `entry porch`, `cell`, `hearing court`, `kitchen`, `stables`, `well`.

Reserve **Japanese** for terms that function as names:

- **Roles / titles** that are L5R-specific: `karo`, `daimyo`, `yoriki`, `daikan`, `ashigaru`.
- **Theological / cosmological proper terms**: `Ta-no-Kami`, `Myobu`, Fortune names (`Inari`, `Bishamon`, etc.).
- **Named relics**: `Akami-fude`, `Chigiri-no-Chou`, etc. - coined per the relic skill.
- **Named places, clans, families, lineages**: as canonical.

When kanji appears in a label, it must pass the **kanji ↔ romaji ↔ meaning triangle** per Constitution Principle XI. Cross-reference: [`/.claude/skills/relic/SKILL.md`](../relic/SKILL.md) for the triangle worksheet pattern.

Three further labeling rules (GM, 2026-07):

- **Label Imperial roads; leave other roads unlabeled.** An Imperial road is a named institution - part of the maintained Imperial highway network - and flagging it tells the reader something real about the settlement (traffic, waystations, who maintains it). An ordinary road needs no label: the drawing already shows where it runs and which edge it leaves by, so a label like "north road" restates what the map makes obvious (same defect as labeling a gate "gate"). Validated instance: Nagahara's through-road was labeled "north road" - removed; Tango's and Hoshizora's "Imperial Road" labels stay.
- **Annotations explain the unusual, not the universal.** A feature label states the function (`clerks' duty room`); italic sub-notes are reserved for what is particular to THIS subject (`staging store - tax grain barges down to Nagahara`). A note that would be equally true on any instance of the feature ("3-4 town clerks by day") is clutter - facts like that live in the skill docs, not on the sheet. This applies to ALL prose on the sheet, legend/notes boxes included: a box line stating a program fact ("~15 samurai per county town") is the same defect relocated.
- **Terms mean what they say.** A label that quietly asserts a quantity, rate, or relationship must match the setting's actual arrangements: "tithe" implies a tenth, and Rokugan's land tax is 1/3, so it is *tax grain* and a *tax archive* - never "tithe".

## Style conventions

### Canvas

- `viewBox="0 0 1200 900"` is the default landscape canvas for compound plans. Larger subjects (whole villages, battlefields) may need 1600×1200 or larger.
- Root font: `font-family="Georgia, 'Times New Roman', serif"`.

### Palette

| Element | Fill | Stroke |
|---|---|---|
| Land / parchment background | `#EFE3C2` | - |
| Compound wall | (stroke only) | `#2D2A24`, width 9 |
| Internal divider wall | (stroke only) | `#3F3A30`, width 6 |
| Court interior (earth pattern) | `url(#court-earth)` | - |
| Lord's buildings (residence, audience pavilion) | `#DDB87A` | `#5A3F1E` |
| Service buildings (kitchen, stables, barracks) | `#C9A57A` | `#6B4F2A` |
| Gatehouse / dais (dark wood) | `#8C6F3E` | `#4A3318` |
| Plain wood buildings (clerks' duty room, tally office, etc.) | `#E8D2A8` | `#6B4F2A` |
| Sealed kura (document storehouse, e.g. tax archive) | `#F2EFE4` | `#4A3318`, width 2.5 |
| Cells / restraint | `#B89868` | `#5C4318` |
| Sacred / shrine (vermillion-edged) | `#C9876C` | `#6B2A18`, with `#A03020` edging strips |
| Cinnabar markers (threshold stones, sacred boundaries) | `#A03020` | `#5C0A04` |
| Garden (stipple) | `url(#garden-stipple)` | `#7A8C5C` dashed |
| Water (ornamental pond) | `#9CB4C8` | `#5C7488` |
| Well stone curb | `#9C8C70` | `#5C4830` |
| Well-mouth (dark) | `#2D2A24` | - |
| Sand court (hearing-court pattern) | `url(#oshirasu-sand)` | `#9C7A40` dashed |
| Granary (vented slats) | `url(#granary-slats)` | `#5A3F1E` |
| Latrines / utility | `#7E726A` | `#3A2E1C` |

### Pattern library

Patterns are defined in `<defs>` and referenced by `url(#name)`. Current standard set, all present in `pool/ochiba-magistracy.svg`:

- `court-earth` - compacted earth in courtyards
- `garden-stipple` - green-on-green stipple for ornamental gardens
- `colonnade-hatch` - diagonal red hatching for covered open-air work spaces
- `oshirasu-sand` - pale sand-stipple for hearing courts
- `granary-slats` - horizontal vented slats for raised storehouses

Add new patterns as needed, kebab-case and descriptive. New patterns should be promoted into this list and back-ported into the canonical template if they're broadly reusable.

### Orientation

- North at top.
- Walled compounds: main gate faces south (bottom).
- No compass rose: north-at-top is invariant on every sheet, so the compass is retired furniture (GM 2026-07).

### Title block

Centered at the top, placed JUST ABOVE the compound (not floated high with a wide gap):

- Title - font-size 30, bold
- Subtitle (one line, place + clan + seat-holder name) - font-size 14, italic
- NO summary line by default. A one-phrase summary is allowed only if it states something NOT visually evident; never restate what the plan already shows (that it is walled, two-courtyard, or where the main gate faces - all readable from the drawing). "Walled two-courtyard compound - main gate south" is the canonical redundant summary; drop it.

### Framing: crop tight to content

Mode A diagrams are cropped tight - set the `viewBox` to hug the drawn content with only a small (~15-25 px) cosmetic border. **Diagrams are rectangular, not forced square.** No wide empty margins on any side (a river or road may legitimately run off an edge; empty parchment may not). **A road or path meant to leave the map must actually run to and off the viewBox edge** - draw it long enough to cross the frame and crop where it exits; a stub that stops short of the edge reads as a dead end. (The postern/gate LABELS go just inside, but any road THROUGH a gate runs out through the frame.) Keep furniture from forcing slack: the **scale bar** sits in a top corner beside the title (not in a dedicated empty band); **approach-road destination labels** sit close to the compound edge with a short road stub, not far out in a margin; and an **edge feature label** (a gate or postern name) goes just INSIDE the opening it names, never outside where it pushes the crop wider. Set the viewBox last, after placing everything, to the true content bounds.

### Label sizes

- Building names: bold, ~13 px
- Sub-labels under building name: italic, ~10-11 px
- Annotations: italic, ~9 px
- Tiny labels (latrines, incidental features): ~7-8 px
- Court labels (`OUTER COURT`, `INNER COURT`, `HEARING COURT`): bold, ~13-14 px, with `letter-spacing="2"`

## Rokugan historical reference framework

L5R/L7R blends historical periods. When uncertain about authenticity:

- **Default civilian administrative features to Edo norms**: hearing court with the magistrate's dais overlooking the sand, granary at any tax-collecting magistracy, modest single-cell detention (Edo detention was a holding function, not imprisonment-as-punishment).
- **Default military/security features to Sengoku norms**: walled compounds with main gate and gatehouse, on-grounds retainer barracks, watchtowers if scale warrants.
- **L5R deliberate divergences from history** (do NOT "correct" these):
  - Major Inari shrines in Fox lands may be substantial halls rather than modest standalone shrines.
  - Temple organization follows the L5R hierarchy (Grand Abbot, Stewards, etc.); see [`/.claude/skills/temple/SKILL.md`](../temple/SKILL.md).
  - Caste assignments may differ from historical Japan. For night-soil specifically: in L7R, burakumin handle this for samurai and wealthy merchants (matching L5R canon); farmers and other tenant peasants handle their own, because they need the fertilizer and could not plausibly afford to outsource. (Note: L5R-era materials called this caste "eta" - L7R has dropped that term as a real-world slur and uses "burakumin" throughout. See [`/gm-assistant/setting/castes.md`](../../../setting/castes.md).)

For sizing - samurai per town, building footprint conventions, role hierarchies - draw on `/gm-assistant/setting/median-domain.md`, `/gm-assistant/setting/demographics.md`, `/gm-assistant/setting/government.md`, `/gm-assistant/setting/hierarchies.md`.

## Render pipeline

**Setup - run this check once when the skill loads** (passwordless sudo is always available wherever this skill runs):

```sh
which resvg >/dev/null || sudo apt-get install -y resvg
[ -f /usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf ] || sudo apt-get install -y fonts-dejavu-extra
```

The renderer is **resvg** - required, deliberately no rsvg-convert fallback. Why (profiled on Tango, 2026-07): rsvg-convert took ~16s at 2600px, ~2/3 of it processing foliage circles lying entirely outside the cropped city viewBox; resvg culls off-view geometry properly and renders the same SVG in ~0.6s, visually identical. Both installs matter for that "identical": resvg's generic-family defaults name MS fonts, so `serif` must map to DejaVu Serif via `--serif-family`; and resvg does not synthesize oblique, so without the real italic faces (`fonts-dejavu-extra`) every italic label silently renders upright.

```sh
resvg --width 2400 --serif-family 'DejaVu Serif' pool/<subject>.svg pool/<subject>.png
```

- **Draw-order / layering.** The generator emits two layers: the base (`self.add`) and a deferred **top layer** (`self.add_top`), concatenated base-then-top at `finish()`. Roads, streets, terrain, and buildings live in the base; **all labels and the gate furniture (guard station + tower) live in the top layer**, so a road or street can never paint over a label or a gatehouse that sits on it (a street runs *through* the gate, under the gatehouse). Anything that records a footprint a road might overlap should carry its draw-order `z` into the manifest so `roads_drawn_under_overlays` can gate it.
- 2400 px wide gives readable labels at typical viewing sizes. Smaller widths may render the smallest labels (latrines, well annotations) illegibly.
- **This manual command is for Mode A only.** Mode B settlement maps render their PNG automatically: `s.finish()` calls `resvg` at 2600px after writing the SVG (pass `render=False` or a different `png_width` to override), so the `.png` stays paired with the `.svg` without a separate step. Re-run the gen (or the test suite, which re-runs every gen) to refresh it; don't call `resvg` by hand for a Mode B map.
- **Since the resvg switch the raster is cheap** (~0.6s even for the biggest map; the Python generation is now the long pole - for Tango, ~2.4s dominated by farmstead/appurtenance geometry). Two env knobs still make iteration cheaper **without changing committed output**:
  - `DIAGRAM_SKIP_RENDER=1` - skip the raster entirely. The gate (`check_village.py`) reads the JSON manifest, never the PNG, so **`test_villages` sets this** and the suite never pays to render PNGs nothing looks at. Use it yourself for a gate-only iteration: `DIAGRAM_SKIP_RENDER=1 python3 pool/<map>.gen.py && python3 check_village.py pool/<map>.json`.
  - `DIAGRAM_PNG_WIDTH=1300` - render at 1300px instead of 2600 for a quick visual eyeball; leave it unset for the full-res committed PNG.
- After rendering, **read the PNG back yourself with the Read tool** to verify legibility and correctness before declaring done. Per Constitution Principle I, the author is not a reliable reviewer of their own visual output - but at minimum, look at it once before reporting it as ready.

## Output convention

Finished diagrams live in this skill's `pool/` directory as paired files:

- `pool/<subject>.svg` - source
- `pool/<subject>.png` - 2400 px rendered output (Mode B settlement maps render at 2600 px+)

Mode A compound plans additionally save their design notes alongside:

- `pool/<subject>.notes.md` - intent, knob settings, deliberate choices, review log; the second source for the `building-review` subagent gate (see [`buildings.md`](buildings.md) "Design notes and the review gate")

Mode B settlement maps additionally save their generator and manifest alongside:

- `pool/<subject>.gen.py` - the parametric generator
- `pool/<subject>.json` - the manifest consumed by `check_village.py`

Subject names: lowercase-kebab-case, descriptive (e.g., `ochiba-magistracy`, `wasp-keep-hachinaga`, `kitsune-mori-pilgrimage-trail`).

## References

- [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) - canonical Mode A worked example; template for compound/building plans
- [`pool/hayakawa-magistracy.svg`](pool/hayakawa-magistracy.svg) - Mode A example B: the generic magistrate's-manor program (buildings.md) instantiated fresh - river-landing county, guest-wing annex, staff-housing option (c), two modest shrines
- [`settlement.py`](settlement.py) - the shared Mode B library (`Settlement` class); all common machinery lives here
- [`pool/kikuta-village.gen.py`](pool/kikuta-village.gen.py) - Mode B example A: **pond-fed single comb-field**, re-varied (feature 005) into a **LINEAR ribbon village** (`s.line_seeds`, `settlement_form="linear"`) strung along the field's high W margin fronting a spine street, with drifted field grain (`grain_drift`) and a Shrine to Benten reached by a **7-torii approach avenue on flat ground** (the burial ground shares its precinct). The structural contrast with Hoshigaoka's nucleated blob is what makes the two same-water villages read as different places (twin-detector).
- [`pool/hikari-no-sato.gen.py`](pool/hikari-no-sato.gen.py) - Mode B example B: the water-first SPLIT (multi-block) village - two separate `build_comb` fans (a TALL west block + a WIDE east block, own sluice/seed each) divided by a central N->S spur the nucleated cluster + shrines sit on; N->S flow (each block stream-fed from the northern hills, draining S to a reed marsh); central Benten shrine at the torii gateway + SW Bishamon shrine. Shows two side-by-side S-fans kept apart with SYMMETRIC short canals (so the drain lands on the S edge and the brook exits cleanly) and made to differ in aspect for `common_fields_vary_orientation`
- [`pool/moritono.gen.py`](pool/moritono.gen.py) - Mode B example C: a to-scale (1 ft/px) HAMLET beside a forest (no headman/shrine/tax-free), water flowing E->W - a source *tameike* fed by a brook out of the `forest()`, the comb paddy draining W to a marsh, plus the magistrate's walled `manor()` at the forest's edge. Shows the water-first + `hinterland()` rules on an EAST-downhill map (the scrub matrix fills around the manor + up to the forest, skipping those blocks) with `forest`-aware crop framing
- [`pool/akagahara.gen.py`](pool/akagahara.gen.py) - Mode B example C2: a **DISPERSED hamlet** (feature 005 `settlement_form="dispersed"`, `s._nucleated=False` so each farm draws its OWN yashikirin grove, no communal wood) - 15 farmsteads STREWN around the field's dry margins, RINGING the paddy (candidates hug the smoothed field outline, offset outward ~64px so every farm is field-adjacent; `try_place` drops any landing on the wet S toe, so they fill the N + W + E margins), on **red-clay ground** (a warm iron-red wash under the crops + scrub, the tell that names 赤ヶ原 "red plain"). A dispersed farm needs ~2x the margin room of a nucleated one, so the field is sized to the full ~20 acres and the farms ring it rather than clumping. The strewn-vs-clumped contrast is the dispersed archetype the twin-detector reads as `settlement_form`. (The simpler `s.scatter_seeds` helper strews farms over a margin BAND; Akagahara rings the whole outline for the fullest pattern.)
- [`pool/hoshizora.gen.py`](pool/hoshizora.gen.py) - Mode B example D: an **unwalled town** (county seat) - Imperial Road spine, road-fronting urban core, all castes, single-monastery exception
- [`pool/hirameki.gen.py`](pool/hirameki.gen.py) - Mode B example E: a **walled town** - hill-anchored rampart, urban core inside, gate-to-yamen streets, chrysanthemum field, two monasteries (changed-hands), downhill irrigation, a theater stage in the Benten monastery's precinct
- [`pool/tango.gen.py`](pool/tango.gen.py) - Mode B example F: a **walled provincial city** - closed moated ring, N-S Imperial road with gate inspection stations, governor's mansion + 6 ministries, a crossing-grid street network with ~600 densely-packed buildings, quartered districts, 5-15 varying-size outside samurai estates. Walled cities are sized **budget-first** (feature 009): `citybudget.plan_city(CityProgram(...))` computes the itemized space budget BEFORE anything is drawn, the wall comes from `budget.wall`, the promise is recorded via `s.meta(budget=budget_to_manifest(budget))`, and the `city_wall_matches_budget` gate holds the map to it - see "Budget-first wall sizing" in [`settlements.md`](settlements.md). Program knobs: `river`, `agricultural_district` (Tango-style in-wall farms, +15% interior - not typical but not a one-off), `extras` for city-specific itemized lines.
- [`check_village.py`](check_village.py) - Mode B automated validator (the machine gate); meta-driven so it works for any hamlet/village/town; run before presenting a settlement map
- [`test_villages.py`](test_villages.py) - pytest (also runnable standalone) that regenerates every pool map and runs the full gate; pins the whole Mode B process against regressions. Run it after any change to `settlement.py` or a spec
- [`test_checks.py`](test_checks.py) - negative-fixture unit tests for the gate itself: each asserts a check FIRES on a deliberately-broken synthetic manifest (so a silently-neutered check is caught). Add a fixture when you add or tighten a check
- [`test_settlement.py`](test_settlement.py) - unit tests for the `settlement.py` branches the pool generators don't exercise (unused vocabulary methods, internal fallbacks)
- [`pyproject.toml`](pyproject.toml) - pytest + coverage config; `fail_under = 100` mechanically enforces full coverage of `check_village.py` + `settlement.py`. Run `python3 -m pytest` from the skill dir (needs `pytest` + `pytest-cov`); the full suite must run together or the coverage gate trips
- `/gm-assistant/setting/village-headsmen.md` - village structure, strip-allocation/usufruct, headman role (Mode B grounding)
- `/gm-assistant/setting/median-domain.md` - sizing data (samurai per town, etc.)
- `/gm-assistant/setting/government.md` - role hierarchies (ministries, magistrates, etc.)
- `/gm-assistant/setting/hierarchies.md` - administrative structure (province / county / village)
- `/gm-assistant/setting/demographics.md` - populations
- [`/.claude/skills/temple/SKILL.md`](../temple/SKILL.md) - temple organization (for diagrams of religious sites)
- [`/.claude/skills/relic/SKILL.md`](../relic/SKILL.md) - Japanese authenticity triangle; relic conventions
- `/.specify/memory/constitution.md` - Principle I (visual verification before declaring done), Principle XI (Japanese authenticity)
