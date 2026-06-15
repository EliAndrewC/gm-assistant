---
name: diagram
description: Generate SVG diagrams of L5R/L7R locations using a consistent style library, then render to PNG. Two modes - compound/building plans (manors, magistracies, temples, keeps, battlefields; hand-authored SVG) and settlement maps (villages and hamlets; parametric generator plus an automated validator gate). Subjects are designed in conversation with the GM, drawn top-down in a labeled diagrammatic style, and saved in the pool.
---

# Diagrams

Generate top-down SVG plans of Rokugani locations - magistrate manors, village layouts, temple plans, military compounds, battle terrain, and the like. The skill covers the shared technical and aesthetic conventions (palette, patterns, building vocabulary, render pipeline, historical reference framework). The per-subject content - *what specifically goes in a given diagram* - is decided in conversation with the GM, not codified here.

The skill's first worked example is [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) (County Magistrate Kitsune Tatsuya's two-courtyard manor). All conventions below were extracted from that work, and `pool/ochiba-magistracy.svg` is the canonical template - copy it as the starting point for new diagrams and edit from there rather than rebuilding from scratch.

## Two modes

This skill covers two kinds of diagram that share the conventions below (palette, English-default labeling, kanji triangle, orientation, title block, label sizes, render pipeline, self-review) but differ in subject and method:

- **Mode A - Compound and building plans** (manor, magistracy, temple, keep, battlefield). Interior plan view: walls, courts, rooms, building footprints. Hand-authored SVG, copied from the canonical template [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) and edited. The "Building vocabulary" section is Mode A.
- **Mode B - Settlement maps** (village, hamlet). Landscape/terrain plan: a settlement in its fields, with realistic house density, irregular paddies, irrigation, and a shrine hill. Built by a **parametric generator** with an **automated validator** gate, because ~50 placed houses and clipped irregular fields are not practical to hand-place. Canonical example: [`pool/kikuta-village.svg`](pool/kikuta-village.svg). See "Mode B: Settlement maps" below.

## Workflow

1. **Pre-design conversation.** Talk to the GM about what's present. Ask about scale (manor vs. village vs. temple vs. battlefield), notable features (workshops, shrines, garrisons), the residing NPC(s), the surrounding context (walled? what's outside?). Pull sizing and role context from the relevant setting files (`/workspace/setting/median-domain.md`, `/workspace/setting/government.md`, `/workspace/setting/hierarchies.md`).

2. **Pitch and confirm.** Offer the GM 3-5 distinct ideas to react to before settling on a layout. Flag any deliberate L5R divergences from historical Japan (e.g., Inari shrine as a hall rather than a standalone, on-grounds barracks rather than off-site retainer housing).

3. **Write the SVG.** Top-down plan view. North at the top of the viewBox. Main gate of any walled compound facing south (bottom). Use the style conventions and building vocabulary below.

4. **Render to PNG.** See the render pipeline section.

5. **Self-review.** Read the rendered PNG yourself. Does every named feature appear? Are labels legible? Is the layout coherent? Iterate before showing the GM.

6. **Report to GM.** Describe what changed, what's deliberately absent, where the diagram diverges from history (Edo vs. Sengoku vs. L5R), and offer a historical-accuracy review pass.

## Labeling rule: English-default

Use **English** for commonplace nouns: `latrine`, `bath`, `rice granary`, `entry porch`, `cell`, `hearing court`, `kitchen`, `stables`, `well`.

Reserve **Japanese** for terms that function as names:

- **Roles / titles** that are L5R-specific: `karo`, `daimyo`, `yoriki`, `daikan`, `ashigaru`.
- **Theological / cosmological proper terms**: `Ta-no-Kami`, `Myobu`, Fortune names (`Inari`, `Bishamon`, etc.).
- **Named relics**: `Akami-fude`, `Chigiri-no-Chou`, etc. - coined per the relic skill.
- **Named places, clans, families, lineages**: as canonical.

When kanji appears in a label, it must pass the **kanji ↔ romaji ↔ meaning triangle** per Constitution Principle XI. Cross-reference: [`/.claude/skills/relic/SKILL.md`](../relic/SKILL.md) for the triangle worksheet pattern.

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
| Service buildings (kitchen, stables, barracks, gatehouse) | `#C9A57A` | `#6B4F2A` |
| Plain wood buildings (tithe-archive, etc.) | `#E8D2A8` | `#6B4F2A` |
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
- Compass rose: top-right, ~28 px circle, dark needle, `N` above, `S` below.

### Title block

Centered at top of viewBox:

- Title - font-size 30, bold
- Subtitle (one line, place + clan + seat-holder name) - font-size 14, italic
- Summary line (one phrase describing the plan type) - font-size 11

### Label sizes

- Building names: bold, ~13 px
- Sub-labels under building name: italic, ~10-11 px
- Annotations: italic, ~9 px
- Tiny labels (latrines, incidental features): ~7-8 px
- Court labels (`OUTER COURT`, `INNER COURT`, `HEARING COURT`): bold, ~13-14 px, with `letter-spacing="2"`

## Building vocabulary

Standard features with rough SVG conventions. New diagrams should reuse this vocabulary; new features should be added here as they're invented.

### Walls and gates

- **Compound wall** - 4-segment heavy stroke in `#2D2A24`. Draw each side as its own `<line>` so gate-openings are gaps. Don't use a single `<rect>`.
- **Main gate** - opening of ~80 px in the south wall, flanked by short heavy posts (~16×14 px).
- **Threshold stone** - small cinnabar rect (~28×14) centered in the gate threshold, annotated outside the wall (e.g., "(buried Pact-Bowl checkpoint)").
- **Internal divider wall** - lighter stroke (~6 px) in `#3F3A30`, separating courts, with its own gate opening.
- **Gatehouse** - small ~120×42 dark-wood rect just inside the gate.

### Outer court (administrative / public)

- **Audience pavilion (engawa + dais)** - long narrow building (~360×55) along the north edge of the outer court. Magistrate's tatami platform centered on the front; two clerk positions flanking.
- **Hearing court** - open sand-textured area (~360×145) immediately south of the audience pavilion. Witness/defendant kneeling marks (~30×14 rects) along the bottom.
- **Tithe archive** - modest plain-wood building (~160×140).
- **Stables** - modest building (~160×80) with vertical stall divisions.
- **Cell** - *small* (~70×80) holding structure with horizontal lattice-bar lines. Edo-style cells are small; large multi-cell blocks are anachronistic for civilian magistrates.
- **Barracks** - moderate building (~80-160 wide) with internal bunk divisions. On-grounds barracks are appropriate for L5R/L7R's Sengoku-flavored blend; pure Edo civilian would have retainer rooms in the residence instead.
- **Rice granary** - raised storehouse (~160×135) using `granary-slats` pattern, with small stilt-blocks visible at the base.

### Inner court (private / sacred)

- **Residence wing** - long building along the north range. Internal soft-divisions (dashed lines) separating named occupants (Tatsuya's quarters, karo & family, senior retainers, etc.).
- **Entry porch** - small projection (~40×14) from the residence's south face at the main entrance.
- **Kitchen + pantries** - modest building (~160×135) with hearth indicator (small dark rect with a small orange circle for fire).
- **Bath house** - small detached pavilion (~70-80 wide) in the inner garden. Optional steam-plume curve above.
- **Inner garden** - stipple-patterned rect occupying central inner-court space. Optional ornamental pond (ellipse) and stone lanterns.

### Wells

A compound housing ~50 people plus horses needs 2-4 wells, distributed by use:

- **Kitchen well** (busiest) - small stone-curb rect (~22×22) with dark well-mouth circle, inside or immediately adjacent to the kitchen building.
- **Garden well** - same form, in the inner garden for family / ornamental use.
- **Stables well** - same form, just outside the stables for horse-watering.
- **Bath-area well** (optional fourth) - only for very large compounds; usually the kitchen well serves the bath by carry.

### Latrines

Very small grey rects (~14-20 px square), labeled `latrine`. Place against walls in corners, away from food prep and water sources. Typically at least one for the inner court and one for the outer.

### Sacred features

- **Modest shrine (standalone)** - small wooden structure with torii silhouette nearby. For routine rural Inari shrines and the like.
- **Hall shrine (L5R-style, e.g., Fox lands)** - full building with vermillion edging (`#A03020` strips at top and bottom). Internal rail division for multiple altars; identifiers like torii silhouette (east) or straw-doll silhouette (west) for distinct altar aspects.
- **Workshop colonnade** - open hatched area (`colonnade-hatch` pattern) attached to a shrine's working side, for sacred craft production (e.g., cinnabar painting of threshold stones).

### Approaches and surroundings

- **Road to gate** - two stacked paths (solid translucent + dashed darker) for ~150 px into the gate from the appropriate cardinal direction. Label the destination/road name in italic alongside.
- **Town / surroundings outside walls** - by default, leave the surrounding parchment empty. Only add exterior buildings if the surrounding context is itself part of the diagram's subject.

## Mode B: Settlement maps (villages and hamlets)

Settlement maps are landscape plans - a village or hamlet sitting in its fields - not interior building plans. They reuse every shared convention above and add the vocabulary and workflow below. Canonical example: [`pool/kikuta-village.svg`](pool/kikuta-village.svg), built by [`pool/kikuta-village.gen.py`](pool/kikuta-village.gen.py) and gated by [`check_village.py`](check_village.py).

### Workflow (generator + validator)

Settlement maps are produced by a parametric Python generator, not hand-placed, because realistic density (~50 houses) plus irregular clipped fields are impractical by hand. The generator emits a paired `.svg` and a `.json` manifest that an automated validator checks. The loop:

1. Pre-design conversation with the GM (scale, fields, civic features, the residing NPC), grounded in the setting numbers below.
2. Write/adjust the generator (copy `pool/kikuta-village.gen.py` as the starting point). It writes the `.svg` and `.json` next to itself.
3. Run `python3 check_village.py <manifest>.json` - the machine gate. It must report ALL CHECKS PASSED before going further.
4. Render to PNG: `rsvg-convert -w 2600 pool/<subject>.svg -o pool/<subject>.png`. Settlement maps need 2600px+ for the small labels.
5. Read the PNG yourself - the persona pass the gate cannot do (coherent village? legible? balanced?). Per Constitution Principle I, get an independent review if you both built and reviewed.
6. Show the GM. Save the `.svg`, `.png`, `.gen.py`, and `.json` in `pool/`.

### Scale and density (ground in the setting numbers)

Pull from `/workspace/setting/median-domain.md`, `demographics.md`, `village-headsmen.md`:

- Average village: 200-500 people = 40-100 households (median household ~5 over 2-3 generations). Draw ~50 houses, a few larger (the ~5% wealthy-landowner farmers) plus the headman's house (largest in the village).
- Hamlet: 50-100 people = 10-20 households; no named civic buildings and no headman of its own (hamlets fall under the village district's headman).
- Villages and hamlets are peasant-only - no resident samurai (samurai live in the county town).

### Fields

- Outlines are terrain-following: organic lobes (outgrowths) and bays (indentations) off a semi-rectangular core. Never clean rectangles.
- Interior paddies are a mosaic of bunded basins of **non-uniform size** (vary the cell widths - break the grid), with wavy bunds, not straight. Each cell reads as its crop: flooded rice basins show transplant rows, soybeans grow as rows on the raised bunds (nitrogen-fixing), and ~1 in 6 plots is a dry/hedge crop (furrowed) guarding against blight.
- Crop rows are **regular within a plot but angled differently between plots** - each basin has its own row orientation, never one global east-west direction.
- Do not place two large fields of similar size and orientation side by side. Vary orientation (one long E-W, one long N-S) and stagger diagonally. Spread smaller fields around the settlement (e.g. SW, SE, middle-north).
- Every field is ringed by farmhouses; fallow fields ring abandoned farmhouses. All houses field-adjacent.
- No paddy on hills (upland rice exists but is not chosen when flat land is available). Hills carry grass, woods, and shrines only.
- Strip-allocation (usufruct, per `village-headsmen.md`): the headman doles non-contiguous strips across the common fields; show via subtle subdivision and the religious figure's tax-free allocation highlighted as non-contiguous **plots** (a vermillion tint + outline - high-contrast against the greens, and thematically the shrine's sacred color; a thin gold outline blends into the tan bunds and was hard to spot). That allocation is law-bounded to ~2 households worth (**2-3 plots**, scattered across the common fields) - gated by `check_village.py`.

### Houses

- Stylized pitched-roof glyphs: two shaded roof planes (darker north slope, lighter sunlit south slope) with a ridge highlight along the long axis, entry on the south face. NOT flat envelope/box icons.
- South-facing convention: ridge runs E-W, facade faces south (historical minka sun orientation).
- Many houses have an attached storehouse/shed (the L-wing on larger houses is the *kura* storehouse); roughly 1 in 3 smaller houses gets one. The headman's house is the largest.
- Houses never overlap and never sit on a road/lane or have water running through them.

### Water, religion, state markers

- Villages need a water source: an irrigation POND (Japanese tameike), never "tank." Size it larger than a house, on flat ground, set back from steep hills (erosion). Feed paddies via channels that route AROUND buildings (never through the headman's house) and take a near-direct path. Each channel must **start inside the pond and end well inside its field** (so the field paints over the end - a visible connection, not a line stopping in the gap before the field), and should **wind gently** rather than run dead straight.
- Each village district has one tax-free religious figure (country monk or priestess); their dwelling may double as the shrine. A shrine sits ON the hill summit, never overhanging the edge; torii ascents wind across the open hill face, gates spread out, none hidden under the shrine.
- Fallow field: dry stipple, dashed organic outline (post-blight). Abandoned house: greyed and dashed with a collapse mark, clustered around the afflicted fields. Lanes and irrigation channels are no-build corridors.
- **No legend/key box.** A settlement map should be self-evident; the few non-obvious elements (fallow fields, the religious figure's tax-free plots, named buildings) are labeled inline instead.

### The validator (`check_village.py`)

The generator emits a manifest the validator asserts against; it must pass before a settlement map is presented. Current checks: no farmhouse overlaps (rotated-rect SAT); nothing on a lane/channel; all houses field-adjacent; every field ringed; fallow fields ring abandoned houses; no cultivation on the hill; shrine seated on the summit; pond larger than the headman's house and clear of the hill; irrigation directness; house count in the average-village band; tax-free plots law-bounded (2-3); the headman's house is the largest; houses face south; the two common fields differ in orientation; 7 torii that are clear of the shrine, on the hill, and spread out; and each irrigation channel starts inside the pond, ends well inside its field, and winds gently.

**Two disciplines this gate has taught us:**

1. **Any rule that can be machine-checked belongs in `check_village.py`, not only in this prose.** When a new Mode B rule emerges, add it as an assertion.
2. **The manifest must record what is actually RENDERED, not the generator's pre-render inputs.** The fields render as a smoothed (Catmull-Rom) curve that bows inward of the raw outline vertices; recording the vertices let a channel "connect" in the manifest while visually stopping in the gap. The generator now records the *sampled smoothed boundary* (`smooth_points`). A check is only as honest as the geometry it asserts against - sample the drawn shape, and still eyeball a crop, because a green check on the wrong geometry is worse than no check.

## Rokugan historical reference framework

L5R/L7R blends historical periods. When uncertain about authenticity:

- **Default civilian administrative features to Edo norms**: hearing court with the magistrate's dais overlooking the sand, rice granary at any tithe-collecting magistracy, modest single-cell detention (Edo detention was a holding function, not imprisonment-as-punishment).
- **Default military/security features to Sengoku norms**: walled compounds with main gate and gatehouse, on-grounds retainer barracks, watchtowers if scale warrants.
- **L5R deliberate divergences from history** (do NOT "correct" these):
  - Major Inari shrines in Fox lands may be substantial halls rather than modest standalone shrines.
  - Temple organization follows the L5R hierarchy (Grand Abbot, Stewards, etc.); see [`/.claude/skills/temple/SKILL.md`](../temple/SKILL.md).
  - Caste assignments may differ from historical Japan. For night-soil specifically: in L7R, burakumin handle this for samurai and wealthy merchants (matching L5R canon); farmers and other tenant peasants handle their own, because they need the fertilizer and could not plausibly afford to outsource. (Note: L5R-era materials called this caste "eta" - L7R has dropped that term as a real-world slur and uses "burakumin" throughout. See [`/workspace/setting/castes.md`](../../../setting/castes.md).)

For sizing - samurai per town, building footprint conventions, role hierarchies - draw on `/workspace/setting/median-domain.md`, `/workspace/setting/demographics.md`, `/workspace/setting/government.md`, `/workspace/setting/hierarchies.md`.

## Render pipeline

```sh
rsvg-convert -w 2400 pool/<subject>.svg -o pool/<subject>.png
```

- 2400 px wide gives readable labels at typical viewing sizes. Smaller widths may render the smallest labels (latrines, well annotations) illegibly.
- One-time setup if not already present in the container: `sudo apt-get install -y librsvg2-bin libcairo2`.
- After rendering, **read the PNG back yourself with the Read tool** to verify legibility and correctness before declaring done. Per Constitution Principle I, the author is not a reliable reviewer of their own visual output - but at minimum, look at it once before reporting it as ready.

## Output convention

Finished diagrams live in this skill's `pool/` directory as paired files:

- `pool/<subject>.svg` - source
- `pool/<subject>.png` - 2400 px rendered output (Mode B settlement maps render at 2600 px+)

Mode B settlement maps additionally save their generator and manifest alongside:

- `pool/<subject>.gen.py` - the parametric generator
- `pool/<subject>.json` - the manifest consumed by `check_village.py`

Subject names: lowercase-kebab-case, descriptive (e.g., `ochiba-magistracy`, `wasp-keep-hachinaga`, `kitsune-mori-pilgrimage-trail`).

## Checklist for a new diagram

Before declaring done:

- [ ] Subject pre-designed in conversation with the GM; scope agreed
- [ ] Sizing grounded in setting files (samurai counts, role roster, building footprints)
- [ ] Labels in English with the Japanese-reserved-for-names rule applied
- [ ] Any kanji passes the kanji ↔ romaji ↔ meaning triangle
- [ ] Title block (title + subtitle + summary) clear
- [ ] Compass rose present
- [ ] Legend / key boxes if conventions need explaining
- [ ] All named features visible at 2400 px render
- [ ] Self-review pass after first render (read the PNG)
- [ ] Both `.svg` and `.png` saved in `pool/`
- [ ] Historical-accuracy review offered to the GM at completion

## References

- [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) - canonical Mode A worked example; template for compound/building plans
- [`pool/kikuta-village.svg`](pool/kikuta-village.svg) - canonical Mode B worked example (an average village); built by [`pool/kikuta-village.gen.py`](pool/kikuta-village.gen.py)
- [`check_village.py`](check_village.py) - Mode B automated validator (the machine gate); run before presenting a settlement map
- `/workspace/setting/village-headsmen.md` - village structure, strip-allocation/usufruct, headman role (Mode B grounding)
- `/workspace/setting/median-domain.md` - sizing data (samurai per town, etc.)
- `/workspace/setting/government.md` - role hierarchies (ministries, magistrates, etc.)
- `/workspace/setting/hierarchies.md` - administrative structure (province / county / village)
- `/workspace/setting/demographics.md` - populations
- [`/.claude/skills/temple/SKILL.md`](../temple/SKILL.md) - temple organization (for diagrams of religious sites)
- [`/.claude/skills/relic/SKILL.md`](../relic/SKILL.md) - Japanese authenticity triangle; relic conventions
- `/.specify/memory/constitution.md` - Principle I (visual verification before declaring done), Principle XI (Japanese authenticity)
