---
name: diagram
description: Generate SVG diagrams of L5R/L7R locations using a consistent style library, then render to PNG. Two modes - compound/building plans (manors, magistracies, temples, keeps, battlefields; hand-authored SVG) and settlement maps (hamlets, villages, and towns - walled or unwalled; parametric generator plus an automated validator gate). Subjects are designed in conversation with the GM, drawn top-down in a labeled diagrammatic style, and saved in the pool.
---

# Diagrams

Generate top-down SVG plans of Rokugani locations - magistrate manors, village layouts, temple plans, military compounds, battle terrain, and the like. The skill covers the shared technical and aesthetic conventions (palette, patterns, building vocabulary, render pipeline, historical reference framework). The per-subject content - *what specifically goes in a given diagram* - is decided in conversation with the GM, not codified here.

The skill's first worked example is [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) (County Magistrate Kitsune Tatsuya's two-courtyard manor). All conventions below were extracted from that work, and `pool/ochiba-magistracy.svg` is the canonical template - copy it as the starting point for new diagrams and edit from there rather than rebuilding from scratch.

## Two modes

This skill covers two kinds of diagram that share the conventions below (palette, English-default labeling, kanji triangle, orientation, title block, label sizes, render pipeline, self-review) but differ in subject and method:

- **Mode A - Compound and building plans** (manor, magistracy, temple, keep, battlefield). Interior plan view: walls, courts, rooms, building footprints. Hand-authored SVG, copied from the canonical template [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) and edited. The "Building vocabulary" section is Mode A.
- **Mode B - Settlement maps** (hamlet, village, town - walled or unwalled). Landscape/terrain plan: a settlement in its fields, with realistic house density, irregular paddies, irrigation, and a shrine hill. Built by a **parametric generator** with an **automated validator** gate, because ~50 placed houses and clipped irregular fields are not practical to hand-place. Canonical example: [`pool/kikuta-village.svg`](pool/kikuta-village.svg). See "Mode B: Settlement maps" below.

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

## Mode B: Settlement maps (hamlets, villages, towns)

Settlement maps are landscape plans - a hamlet, village, or town sitting in its fields - not interior building plans. They reuse every shared convention above and add the vocabulary and workflow below.

### Architecture: a shared library + thin per-settlement specs

The common machinery lives in [`settlement.py`](settlement.py) (the `Settlement` class). A specific settlement is a **thin spec** that imports it, declares its fields/water/shrine/houses, and calls `finish()`. Worked examples, smallest to largest:

- [`pool/moritono.gen.py`](pool/moritono.gen.py) - a **hamlet** (no headman/shrine/tax-free), three small fields fed by a cascading stream, plus two features beyond the usual vocabulary: a **forest** (`s.forest(west_edge, ...)`) filling the east, and the county magistrate's **walled manor** (`s.manor(...)`, a hunting lodge - a Mode A compound shown as a feature, a samurai estate adjacent to but not part of the hamlet).
- [`pool/kikuta-village.gen.py`](pool/kikuta-village.gen.py) - an average **village**, **pond-fed**, TWO staggered common fields, hill-top Benten shrine with 7 torii, fallow fields ringed by abandoned houses.
- [`pool/hikari-no-sato.gen.py`](pool/hikari-no-sato.gen.py) - an average **village**, **stream-fed** (no pond), ONE great V-shaped common field with an internal fallow patch (no abandonment), a ring of small fields fed field-to-field, a modest 2-torii Benten shrine at the southern torii gateway (NOT on a hill), and a second Bishamon shrine in the southwest.
- [`pool/hoshizora.gen.py`](pool/hoshizora.gen.py) - an **unwalled town** (county seat, ~1,200 people). Imperial Road spine, a stream running parallel to the road between field pairs, a dense urban core (merchants/laborers/servants aligned to the road), a town **monastery** with a torii, the magistrate's walled manor + samurai houses, a segregated burakumin quarter, an amphitheater, **hayfield/grazing pastures** ringing barns, and a small forest - terrain features (forest, pasture, one field) run OFF the map edge.
- [`pool/hirameki.gen.py`](pool/hirameki.gen.py) - a **walled town**. The rampart is an irregular hill-anchored arc (`s.wall(...)`) whose two ends **climb partway up the hill flanks**; the **north flank is a steep hachured hill** (`s.hill(..., steep=True)`) carrying the magistrate's manor, so the slope defends that side instead of a wall; a front gate with guard station + guardtower; and a **chrysanthemum field** (`s.flower_field(...)`, the Imperial flower) kept INSIDE the walls, abutting the inner face (the wall bulges out around it).

**What is COMMON (lives in `settlement.py`, do not duplicate per village):** the palette and SVG defs; organic field outlines (bbox-based OR an arbitrary base polygon like a V) with non-uniform crop basins and per-plot angled rows; the south-facing pitched-roof house glyph; size-aware, corridor-aware, field-blocking house placement; hills + summit shrines + torii; ponds, off-map streams, and winding channels; tax-free plot picking (interior-validated); the manifest emission. When you need a NEW shared capability (a new field shape, a new building type), add it to the library, not to one village.

**What is SETTLEMENT-SPECIFIC (declared in the thin spec + echoed into `manifest["meta"]`):** field count/shape/placement; the irrigation **source** (pond vs stream vs field-to-field) - water *must exist*, but the kind varies by region (a pond/*tameike* suits a dry locale; a stream diversion suits a river valley - not every village had a pond); torii count; whether the main shrine sits on a hill or stands central on flat ground; whether blight left abandoned houses (Kikuta yes, Hikari no); additional shrines; the settlement scale and (for towns) the holding clan, walls, slope, and monastery dedications. The validator reads `meta` and each channel's `frm`/`to` anchors, so it adapts per settlement instead of assuming one layout - see the knob reference next.

### Settlement `meta()` and the per-settlement knobs

A settlement's identity and the rules the gate applies to it are declared with `s.meta(...)` (echoed into `manifest["meta"]`) plus two `Settlement` attributes. **This is also the persistence mechanism:** the knobs live in the `.gen.py` source, so every regeneration re-applies them and the gate fails loudly if a pass ever drops one - which is why these maps survive dozens of re-generation passes without losing their identity. Annotate non-obvious knobs with a comment explaining *why* (a changed-hands town, an intentional single monastery), so the reasoning travels with the data.

- `name=` - the place name (the title block).
- `scale=` - `"hamlet"` | `"village"` | `"town"`. Drives nearly everything downstream: headman/shrine presence, the house-count band, the religious tier, and which town rules switch on.
- `households=N` / `target_houses=N` - village sizing (occupied houses ≈ 0.7 per household, or an explicit count band).
- `walled=True` - a town has a rampart (turns on the wall / gate / main-street / amphitheater-inside checks).
- `torii_expected=N` - exact TOTAL torii count drawn: a village/hill shrine's gateway arches, OR the sum across a town's monastery avenues (a town monastery's avenue may be several arches - see `monastery_torii_scale_with_space`, so this is no longer "one per monastery").
- `shrine_on_hill=True` - the village shrine sits on the summit, reached by a torii ascent.
- `fallow_implies_abandoned=True` - fallow fields are ringed by abandoned houses (post-blight).
- `downhill=<cardinal name | [dx,dy]>` - the land's slope (so channels can be gated to run downhill); tag it when the gradient is clear (a hill on one side).
- `clan="<Great Clan>"` - the holding clan; sets the town's two default monastery dedications. **ASK the GM if not given.**
- `monastery_fortunes=[...]` - override the monastery dedications (a town that changed hands, or one with a single monastery).
- `amphitheater=False | "outside"` - omit the town amphitheater, or allow it outside a walled town.
- `gate_market=False` - suppress the extramural gate market a walled town has by default (a purely military fort, or a depopulated / suppressed gate). See `walled_town_has_gate_market`.
- `granary=True` - mark a rice-TRANSIT town and require a distinct granary (`s.granary(...)`, gated by `town_has_granary`). OFF by default - a standard county seat's grain sits inside the magistrate's yamen, not drawn separately.
- canvas is `Settlement(W, H, seed=...)` (echoed to `meta.W/H`); **`s.bscale`** (≈ 0.82 for a town) shrinks the urban glyphs so a larger settlement packs at a finer grain.

### Workflow (spec → validator → persona)

1. Pre-design conversation with the GM (scale, fields, water source, civic features, the residing NPC), grounded in the setting numbers below. **For a town, also settle:** the **holding clan** (sets the monastery dedications - ASK if not given), **walled or unwalled** (border/contested towns are walled), the **elevation slope** if there's a clear gradient (a hill), and any exceptions to the defaults (single monastery, no amphitheater, a town that changed hands).
2. Write a thin spec by copying the closest existing one: a **village** from `kikuta-village.gen.py` (pond, two fields) or `hikari-no-sato.gen.py` (stream, one V-field); a **hamlet** from `moritono.gen.py`; an **unwalled town** from `hoshizora.gen.py`; a **walled town** from `hirameki.gen.py`. Running it writes the `.svg`, the `.json`, **and the `.png`** next to itself - `s.finish()` rasterizes the PNG automatically (via `rsvg-convert` at 2600px), so the `.png` can never drift from the `.svg`. Only touch `settlement.py` if you need a genuinely new shared capability.
3. Run `python3 check_village.py <manifest>.json` - the machine gate. It must report ALL CHECKS PASSED before going further. (Running the test suite, `python3 -m pytest`, re-runs every gen and so refreshes every pool `.png` as a side effect - if you ever hand-edit an SVG, re-run the gen or the suite rather than calling `rsvg-convert` yourself.)
4. Read the PNG yourself - the persona pass the gate cannot do (coherent village? legible? balanced?). Per Constitution Principle I, get an independent review if you both built and reviewed.
5. Show the GM. Save the `.svg`, `.png`, `.gen.py`, and `.json` in `pool/`.

### Scale and density (ground in the setting numbers)

Pull from `/workspace/setting/median-domain.md`, `demographics.md`, `village-headsmen.md`:

- Average village: 200-500 people = 40-100 households (median household ~5 over 2-3 generations). Declare `meta(households=N)`; the gate's **`households_consistent`** check requires the OCCUPIED farmhouse count to be **~0.7 per household** (extended families share a roof - the GM's rule: "~70 households ... at least 50 houses"). So ~70 households → ~50 occupied houses, a few larger (the ~5% wealthy-landowner farmers) plus the headman's (largest). **Abandoned houses do not count toward households** (they're former homes).
- To seat ~50 houses you usually need them **two-deep** around the fields, not a single necklace - call `ring()` twice per field, an inner pass (small gap) and an outer pass (larger gap, e.g. ~55). A single ring saturates a field's perimeter around ~40 houses.
- Hamlet (`meta(scale="hamlet")`): 50-100 people = 10-20 households. A hamlet has **no headman of its own** (it falls under the village district's headman - so omit `s.headman(...)`), **no village shrine**, and **no tax-free plot**. The gate enforces this asymmetry: `hamlet_has_no_headman` for hamlets vs `village_has_headman` for villages; tax-free and the orientation checks simply don't apply at hamlet scale. A hamlet typically has just 1-3 small fields.
- Villages and hamlets are peasant-only - no resident samurai (samurai live in the county town).
- **Non-standard size:** for a larger-than-usual village (say 500 people / ~80 houses), declare `meta(target_houses=N)` and the gate's count band follows it (~N ±15%). House count is bounded by field perimeter (houses ring fields at ~56px spacing), so to actually *seat* that many: enlarge the canvas (`Settlement(W=..., H=...)`) and give bigger/more fields, then raise the `ring()` counts. A second concentric house ring is a small library addition if one ring around the fields can't hold them.
- **Town (`meta(scale="town")`):** a county seat, ~1,200 people / ~238 households (per [`budgets.md`](https://github.com/EliAndrewC/l7r/blob/main/setting/budgets.md)). A town is **not** peasant-only: it has ALL castes, and the map must place the **actual documented number of each non-farmer household** (the Town caste table's Families column - one building each), not a token sample. Per `budgets.md`: **~24 merchant houses, ~29 laborer dwellings, ~13 servant households, ~12 burakumin, ~4 samurai families**, plus ~156 farmer households. There is **no peasant headman** at town scale; the state is the magistrate, in a **walled manor** (`s.manor(...)`, walls only - its interior is a separate Mode A diagram). Three modelling conventions adjust what is actually DRAWN (and the gate's target bands): **servants** mostly live inside the samurai/merchant compounds they serve, so only the ~5 "miscellaneous" households stand alone (the rest aren't drawn); **shops** are additional business premises counted separately from the ~24 merchant dwellings (not household-gated); **samurai** show as 5-10 houses with the ~15-strong working platoon barracked inside the manor (not drawn). The gate enforces these counts per caste (`town_caste_count[...]`), farmer plurality (`town_farmers_plurality`), and the magistrate's manor (`town_has_magistrate_manor`).
- **Farmland is sampled, non-farmers are not.** We deliberately draw only some of a town's ~156 farmer households (the rest implied by the off-edge field, below), but we draw **all** the non-farmer households at their documented counts - so the map answers "where does each caste live?" faithfully. Farmers must still be the largest single group on the map (`town_farmers_plurality`), so ring the fields deep enough that farmhouses out-number the laborers (the largest non-farmer group, ~29).

### Fields

- Outlines are terrain-following: organic lobes (outgrowths) and bays (indentations) off a semi-rectangular core. Never clean rectangles.
- Interior paddies are a mosaic of bunded basins of **non-uniform size** (vary the cell widths - break the grid), with wavy bunds, not straight. Each cell reads as its crop: flooded rice basins show transplant rows, soybeans grow as rows on the raised bunds (nitrogen-fixing), and ~1 in 6 plots is a dry/hedge crop (furrowed) guarding against blight.
- Crop rows are **regular within a plot but angled differently between plots** - each basin has its own row orientation, never one global east-west direction.
- Field arrangement is village-specific - it might be two staggered fields of differing orientation (Kikuta) or one great V-shaped field ringed by small ones (Hikari). The universal rule: when there ARE two large common fields, do not make them similar size and orientation side by side (vary and stagger); and spread the smaller fields around the settlement.
- Every field is ringed by farmhouses, all field-adjacent. Whether blight leaves **abandoned houses** is village-specific: Kikuta's fallow fields are ringed by abandoned houses; Hikari's blight is an internal fallow patch of the main field with no abandonment. (Declared via `meta.fallow_implies_abandoned`.)
- No paddy on hills (upland rice exists but is not chosen when flat land is available). Hills carry grass, woods, and shrines only.
- Strip-allocation (usufruct, per `village-headsmen.md`): the headman doles non-contiguous strips across the common fields; show via subtle subdivision and the religious figure's tax-free allocation highlighted as non-contiguous **plots** (a vermillion tint + outline - high-contrast against the greens, and thematically the shrine's sacred color; a thin gold outline blends into the tan bunds and was hard to spot). That allocation is law-bounded to ~2 households worth (**2-3 plots**, scattered across the common fields) - gated by `check_village.py`.

### Houses

- Stylized pitched-roof glyphs: two shaded roof planes (darker north slope, lighter sunlit south slope) with a ridge highlight along the long axis, entry on the south face. NOT flat envelope/box icons.
- South-facing convention: ridge runs E-W, facade faces south (historical minka sun orientation).
- Many houses have an attached storehouse/shed (the L-wing on larger houses is the *kura* storehouse); roughly 1 in 3 smaller houses gets one. The headman's house is the largest.
- Houses never overlap and never sit on a road/lane or have water running through them.

### Water, religion, state markers

- Villages **must** have a water source, but its KIND is village-specific (regional). Historically not every paddy village had a pond: a reservoir **pond** (*tameike*, never "tank") suits a dry/rain-shadow locale (Kikuta); a **stream diversion** from off-map feeding the main field, which then feeds the smaller fields field-to-field, suits a river valley (Hikari). A pond, if used, must be larger than a house, on flat ground, set back from steep hills (erosion). Channels route AROUND buildings (never through the headman's house), take a near-direct path, **wind gently** (not dead straight), and must be **anchored at both ends** - each end starts/ends inside its source (pond / off-map edge / another field) and well inside its target field, so the field paints over the end (a visible connection, not a line stopping in the gap). Anchors are declared per channel as `frm`/`to` in the manifest. Channels are **no-build corridors**: the generator reserves ~33px around each, which is enough to keep a farmhouse's whole **footprint** off it (its half-diagonal is ~26px), not merely its centre - and `no_structure_on_channel` gates the rendered map with the *same rotated-rect footprint test the streams use* (a corner clipping a channel fails it, not just a centre on it). The earlier centre-only guard (`houses_off_corridors`, still kept for the lane) let corners slip through - that is how Hikari once shipped farmhouses sitting on its field-to-field channels.
- **Water flows downhill.** Streams and channels follow the land's slope. If a map declares its slope with **`meta(downhill=<dir>)`** (a cardinal name like `"south"`, or a `[dx,dy]` vector in map coords where `+y` is south), every channel must run *with* it - its source (the tap on the stream/pond, `poly[0]`) sits **uphill** of where it feeds the field (`poly[-1]`), gated by `channels_flow_downhill`. So when a north-flowing stream feeds a field to its east, tap the stream **upstream/north** of the field and angle the channel down to it; a channel run flat or angled back uphill would carry the water *away* from the field. Hirameki's hill is in the north, so it sets `downhill="south"`. Maps without the tag are exempt (slope unknown) - tag a map when its elevation gradient is clear (a hill, a falling valley).
- **The religious building scales with the settlement** (gated by `religious_matches_scale`): a **hamlet** has NONE; a **village** has a Shinto **shrine** ("Shrine to <Fortune>" / "village shrine"); a **town** has **monasteries** (each "Monastery of <Fortune>", with a torii in front); a **city** would have full **temples**. Never label a village site a "temple" - temples belong at town scale and up (see the `/temple` skill). If the GM says "temple" for a village, silently correct it to "shrine."
- **A town has TWO monasteries by default**, one for each of the **2 patron fortunes of the clan** whose holdings include it. Declare the clan with `meta(clan="Lion")`; the gate then expects exactly those two dedications (`town_monastery_count`, `town_monasteries_dedicated`). Patron pairs: **Crab** Bishamon+Ebisu, **Crane** Benten+Daikoku, **Dragon** Hotei+Ebisu, **Lion** Bishamon+Daikoku, **Phoenix** Fukurokujin+Hotei, **Scorpion** Benten+Jurojin, **Unicorn** Fukurokujin+Jurojin. **When generating a town, if the GM has not named the clan, ASK** - the dedications can't be chosen without it. Override the default with `meta(monastery_fortunes=[...])` (an explicit list, any length) for special cases: a town that **changed hands** (Hirameki is Lion-held but keeps a small older Benten monastery from Crane rule, so `monastery_fortunes=["Bishamon","Benten"]`), or a quiet town with just **one** monastery (Hoshizora, `monastery_fortunes=["Bishamon"]`). `town_declares_monasteries` requires every town to set `clan` or `monastery_fortunes` - this is also how the data persists across regenerations (it lives in the `.gen.py` source, re-run each pass). The same rule will extend to **city temples** at provincial-city / capital scale. Mark the principal monastery `primary=True`.
- **A town monastery fronts a torii AVENUE sized to its approach space** (`monastery_torii_scale_with_space`, walled towns only). Torii lead up to a hall along a processional way (*sando*); how many arches you draw is set by how much open approach there is in front of the monastery - the clear run from its front edge to the public street it faces, or to the field / wall / map-edge that cuts the approach short. A monastery with a long, open run to the market street shows **several** arches; one wedged hard into a corner shows a **single** arch. In Hirameki: Bishamon has a clear ~220px run south to the cross-street, so it fronts a 4-arch avenue; Benten is pinned between the west rampart and the Imperial chrysanthemum field (~50px), so it gets one arch. The check measures that span - deliberately **ignoring buildings**, since the avenue is a cleared way that displaces dwellings rather than being stopped by them - and wants roughly one arch per ~55px, within a +/-1 band. So you cannot under-build (1 arch where the approach has room for 5) or overflow (5 arches crammed into a corner). **This is a town-monastery rule ONLY; village shrines are exempt** - they carry 0-1 torii regardless of space. `meta(torii_expected=N)` is then the TOTAL arch count across all monasteries (Hirameki: 4 + 1 = 5), not the monastery count.
- The main shrine's placement is village-specific: it may sit on a **hill** (Kikuta's Benten, reached by a torii ascent) OR stand **on flat ground** reached by a torii gateway (Hikari's Benten sits at the southern entry path - a recent addition belongs at the village edge/gateway where there is room, not displacing an established structure). If on a hill it sits ON the summit, never overhanging the edge, with the torii ascent winding across the open face. Torii **count varies by village** (Kikuta 7, Hikari 2); whatever the count, they stay clear of the shrine hall and spread out. Each village district has one tax-free religious figure whose dwelling may double as the shrine.
- Fallow field: dry stipple, dashed organic outline (post-blight). Abandoned house: greyed and dashed with a collapse mark, clustered around the afflicted fields. Lanes and irrigation channels are no-build corridors.
- **No legend/key box, no descriptive subtitle, and do not label what is visually evident.** A settlement map should be self-evident: just the place name as a title (no "an average farming village..." subtitle/summary line), and inline labels only for the few non-obvious elements (fallow fields, the tax-free plots, named buildings). Do NOT state counts the reader can see (e.g. "2 torii" / "7 torii") - the torii are drawn. **No two body labels may overlap** (gated by `no_label_overlaps`).
- **A building's subtitle must add information, never restate the label or the obvious.** Drop subtitles that repeat the label - a "Monastery of Bishamon" needs no "(town monastery)" note (`religious_subtitle_not_redundant` gates this for religious halls: the subtitle may not contain "shrine"/"monastery"/"temple") - and drop subtitles for the visually evident, like "atop the hill" under a manor that is plainly drawn on a hill. KEEP subtitles that genuinely add context: "(still tended)" on a shrine, "county seat" on a manor (the settlement tier), "hunting lodge by the Shirin Forest" (what the compound actually is).

### Towns and walled towns

**The unifying principle for towns: Rokugan's geography is modeled on China, its administrative culture on Japanese samurai society.** That is the *why* behind almost every town decision below - the Chinese **walled county-seat** layout (the wall defines the town; the magistrate's *yamen* on the gate-to-citadel axis; the whole urban population inside; farmland outside), zoned and defended *jokamachi*-style (samurai by the castle, merchants on the streets, outcasts at the edge). When a town choice is unobvious, reach for "what would a Chinese county seat administered by samurai do?" A town spec adds urban vocabulary on top of the field/house machinery:

- **Urban core - businesses front the streets, housing sits back.** The `shop` and `merchant` glyphs are **businesses** (drawn with a striped awning + hanging sign so commerce reads as visually distinct); `laborer`/`servant` are **housing**. Three gated rules tie them to the street network: businesses must **front a street** (`businesses_front_streets`), every street-fronting building must **face the street it lines** (`buildings_face_street`), and **housing stays off the main street's frontage** (`housing_off_main_street`, set back behind the shops). Place businesses with **`s.frontage(street, items, rows=2)`** - it lines a street with shophouses, each rotated to face it (pass `skip=<full road poly>` when fronting a sub-stretch of a longer road). Fill block interiors with **`s.pack(bbox, items, face_streets=True)`** - each building turns to face its nearest street, and spots that wouldn't front any street are skipped. Place housing with plain `s.pack(...)` in set-back bboxes (>92px from the main street). The **burakumin quarter** is its own pack, segregated at an edge (exempt - not part of the commercial frontage).
- **Streets and town layout (history).** Chinese towns - Rokugan's geographic model - were *planned*, not organic: a main avenue ran from the principal (usually south) gate straight to the **government office (yamen)**, which sat on that axis facing south, with the grid divided into blocks by cross streets. Early (Tang) cities walled those blocks into curfew *wards*; by the Song the wards opened into **shop-lined streets** (merchant shophouses fronting the roadbed), and commerce spilled **outside the gates** along the approach road (the *guan-xiang* suburb). Japan copied the Tang grid for its imperial capitals (Nara/Kyoto) but laid out castle towns (*jokamachi*) as zoned districts - samurai by the castle, merchants in trade-blocks, temples at the edge - with deliberately kinked, defensive streets. **So a town should read as blocks fronting streets, not a scatter of houses.** An unwalled town gets this for free if a road runs through it (Hoshizora's Imperial Road is its spine). For a walled town, draw the streets explicitly (below).
- **Road** - `s.road(pts, label=...)`, an Imperial or trunk road as a spine; a no-build corridor (wide clearance). Like streams, **a road runs OFF both map edges** (`edge_features_run_off_map`).
- **We do not draw all the farmland.** A town's fields are a representative sample; the rest is implied off-map. So **at least one field must run OFF the map edge** (`town_has_field_off_edge`) - a partial field at the margin signals "more farmland beyond." Off-edge fields are exempt from the ringing and irrigation checks (their houses/water are off-map too).
- **Every town has an amphitheater** (`s.amphitheater(cx, cy, r, label=...)`; `town_has_amphitheater`) unless `meta(amphitheater=False)`. For a **walled** town it sits INSIDE the walls (`amphitheater_inside_wall`) unless `meta(amphitheater="outside")`.
- **The town granary is NOT a separate building by default - it lives inside the magistrate's compound (the yamen).** A county seat collects and forwards tax rice, so it has substantial grain storage, but at this scale that store sits within the administrative compound (both the Chinese ever-normal granary and the Japanese domain rice storehouse were kept at the seat of government), which on the map IS the magistrate's manor. So treat the granary as **implied by the manor** and do not draw a standalone one. The exception is a **rice-TRANSIT hub** - a town at a road/river junction where grain from many counties is gathered and forwarded up the kick-up chain - which historically grew a distinct fortified storehouse district. For that case only, set `meta(granary=True)` and draw a row of fireproof *kura* with `s.granary(cx, cy, n=...)` near the gate or transport route; `town_has_granary` then requires the granary to be present. The flag is **opt-in** (the inverse of the gate market / amphitheater / monastery defaults): absent it, no granary is expected or drawn.
- **Several merchant houses keep an attached storehouse (*kura*).** Because most Rokugani farmers are **tenants**, their (often absentee) landlords' rent-rice and bulk goods are stored in town - over and above the ordinary inventory storeroom a shop already has. So a noticeable **minority** of businesses run the classic narrow-front / deep-lot merchant compound with a fireproof *kura* behind the shopfront. Call `s.merchant_storehouses(count=6)` AFTER placing the businesses: it tucks a small kura behind several merchants (the **back**, opposite the street-facing awning), drawn as an annex like the farmhouse `shed`, so it needs no open ground in the maximally-packed quarter (there is none). `town_has_merchant_storehouses` requires **>= 3** - more than a token one or two, but still a minority.
- **Draft animals live in the farmhouse, not a barn; rural settlements have no hay barns.** East Asian wet-rice farming is not herd-based, so there are no European-style barns. The peasant farmhouse - specifically its *doma* (earthen-floored work bay) - stalls the draft ox or horse **under the same roof**, including for winter, so the farmhouse glyph (with its optional attached `shed` storeroom) already implies both the storeroom and the animal housing. Do **NOT** add barns to a village or hamlet. Barns + grazing pasture (`s.pasture(...)`, `s.building(..., "barn")`) appear ONLY for a specific reason: a **road / post town's horse-relay infrastructure** (Hoshizora, on the Imperial Road - remounts + hayfields to feed them) or a **horse-breeding domain** (Unicorn / Moto). Town **stables** are likewise not drawn separately - warhorses are inside the magistrate's manor, travellers' mounts at the (unlabelled) inns.
- **When the magistrate's manor sits on a large hill** (the manor center inside `M["hill"]`'s ellipse), two arrangement rules apply: the **amphitheater goes at the foot of the hill on the downhill/town side** (`amphitheater_at_hill_foot`: near the hill's base edge, aligned with the slope) so the townsfolk sit on the slope to watch; and the **manor's gate faces the town below** (`manor_gate_faces_town`) - pass `s.manor(..., gate_dir="south"|...)` so the gate opens toward the building centroid (defaults to `"west"` for flat-ground manors, which these checks don't touch). Hirameki puts its amphitheater at the hill's south foot, offset from the main-street axis, with the manor gate facing south.
- **Pastures and large terrain** - hayfields/grazing (`s.pasture(...)`), forests (`s.forest_patch(...)`): a large area feature near an edge must **cross** that edge rather than sitting wholly on the map (`edge_features_run_off_map`). Barns sit within the grazing.
- **Streams stay between fields, never through them** (`streams_avoid_fields`): run a stream parallel to the road between field pairs. **Every fully-on-map field must SHOW a water source** (`fields_show_water_source`) - a channel ending inside it, or the field directly abutting a stream/pond. Being merely *near* water with no visible connection does not count, so tap the stream with a channel (`s.channel(stream_pt, field_pt, {"kind":"stream"}, {"kind":"field","name":...})`). Fields that run off the map edge are exempt (their water may be off-map too).
- **Nothing overlaps the manor, road, stream, or irrigation channel** (`no_structure_on_manor` / `_road` / `_stream` / `_channel`): the manor blocks a rect expanded by 36; roads, streams, and channels are corridors tested by the full rotated-rect footprint. Fields stay clear of the road (`fields_clear_of_road`).

**Walled towns** (`meta(walled=True)`) add a rampart:

- `s.wall(pts, gate=(gx,gy))` draws an irregular thick polyline (a wide no-build corridor - clearance ~46, so even a large building's corner stays off the rampart) with a gate gap, flanking posts, a guard station, and a guardtower. The gate records to the manifest. The wall must be **irregular** - `wall_sections_irregular` requires **>= 5 sections and a section-length coefficient of variation >= 0.25** (a spread test, so a wall may hug a feature with several short segments while a lazy near-regular polygon still fails); `walled_town_has_wall` requires both a wall and a gate. No structure may overlap the rampart stroke (`no_structure_on_wall`).
- A wall need not enclose a full ring. It can be an **open arc anchored to a steep hill**: the hill's back/sides defend that flank, so the rampart ties into the slope. Draw the hill with `s.hill(..., steep=True)` (emphasized hachures on the steep north back/upper flanks), and **run the wall's two ends partway UP the hill flanks** so the slope, not a blunt wall-end, closes each side. The magistrate's manor sits on the summit.
- A **chrysanthemum field** (`s.flower_field(...)`, the Imperial flower - "Heaven with the defenders") is kept INSIDE the walls, abutting the rampart. A field may **abut** the wall but must never cross it (`fields_clear_of_wall`). To make it read as genuinely flush (not a thin tan sliver): flatten the abutting edge with `flower_field(..., flat_west=True)` and run a **straight wall segment** right along it - centre the wall ~5px outside the field's flat edge so the rampart's inner stroke (half-width ~5) lands flush on the field boundary. A wavy field edge against a straight wall always leaves a visible gap; flatten one, straighten the other, and they touch.
- **The whole urban core lives INSIDE the wall** (historical: a Chinese walled county seat / Japanese *jokamachi* enclosed its townspeople; the *graph* for "city," 城, means "wall"). Inside, zoned around the magistrate's hilltop citadel: samurai by the manor, then the merchant/shop streets, then the **laborers and servants in back-lane blocks** off the commercial avenue, plus the monastery - and open ground the surrounding farmers retreat into during a raid. **Outside the wall, only:** the farmland and farmhouses, the **segregated burakumin quarter** (outcasts on marginal land - historically correct), and a *small* **gate market** (*guan-xiang*) of a few shophouses along the road just outside the gate. The gate market is a **default, not an option**: a walled town is gated to have a few businesses (shops/merchants) outside the wall near the gate (`walled_town_has_gate_market`, >= 3 within ~420px), because the gate is a chokepoint where the rural population trades without entering the walls, travellers buy services, and vendors dodge the intramural tax and market regulation. Suppress it only for a real exception with `meta(gate_market=False)` (a purely military fort, a depopulated or suppressed gate). Do NOT push the laborers/servants outside to save room - that inverts the real pattern.
- **Town scale ≠ village scale.** A town is ~1,200 people vs a village's ~350, so it needs a genuinely larger drawing: a bigger canvas (Hirameki is `Settlement(2600, 1820, ...)`) AND a finer building grain - set `s.bscale ≈ 0.82` so the urban glyphs pack denser (town buildings are smaller dots than village houses; the `bscale` factor only applies where set, so an unwalled town like Hoshizora can keep `1.0`). Sizing the wall like a village's is what forces the population outside - give the rampart room for the whole core.
- **Streets carve the interior into blocks.** Draw `s.street(pts, width=26, main=True, label="main street")` for the **gate-to-yamen axis** (extend it *through* the gate so the gate market frontage outside is on the same avenue) and `s.street(pts, width=20)` for one or two market cross-streets - *before* the frontage/packs. `walled_town_has_main_street` requires a `main=True` street running inward from the gate; `no_structure_on_street` keeps buildings off the bed. Then line the streets with `s.frontage(...)` (businesses, two-deep, facing the street; `face_streets=True` packs skip deep spots so commerce only lines frontage) and fill the laborer/servant **back-lane blocks** with `s.pack(..., face_streets="fill")` - the `"fill"` mode faces buildings near a street but still fills the deep block cores (tenement housing, which is `>92px` from any street and therefore exempt from the facing check). Give the laborer quarters their own back-lanes off the avenue so their dwellings front a *non-main* street (`housing_off_main_street` only bars them from the main commercial frontage). Because `frontage()` sits *against* the street it fronts (it skips that street's corridor), several streets no longer starve each other the way plain `pack()`-into-blocks did - a main axis plus a couple of cross-streets and back-lanes is fine.
- **No "street to nowhere": every street earns its existence by the buildings along it** (`streets_have_buildings` - no inside-the-walls stretch longer than ~130px may be empty of buildings that **front this street**). The rigor that matters: a building counts toward a street only if that street is the one it actually **fronts** (its nearest street, the one it was rotated to face) - a building sitting beside a north-south lane but fronting the east-west cross-street it is nearer to does NOT keep the lane alive. (An earlier, looser version counted any building within proximity and so missed lanes that dead-ended past their last real frontage.) The *why* is historical: a street is **access infrastructure for the buildings it serves**, and it is paved or worn into the ground by the foot traffic to and from them - Beijing's *hutong* alleys "emerged as access routes lined by contiguous courtyard residences," and a desire path forms only between real destinations. A planned grid line that never gets built up simply **isn't drawn** (an undeveloped block). Note the asymmetry: **buildings with no street are fine** (the poor can't afford street frontage - they sit in the deep block cores), but **a street with no buildings is not**. When the check fails, fix it by **building demand**: (1) if there are buildings the lane could serve - dwellings sitting off in the cores, or documented households still owed - **route the lane to them or move them onto it** (lower-status dwellings readily line lesser back-lanes); (2) if the population is already fully housed (all the `town_caste_count` bands are met), the street has no reason to exist - **trim it back to its last building, or remove it** (this is what Hirameki's redundant lower cross-lane got: deleted, with no loss of laborer capacity since `face_streets="fill"` had already seated them in the cores). Don't add a street first and hope buildings find it; add streets where the buildings (or the demand for them) already are.

- **The wall must HUG the built town - don't wall in empty space** (`wall_hugs_the_town` - no contiguous stretch of rampart longer than ~280px may run more than ~140px from the nearest building, feature, or terrain). The *why* is pure economics: a rampart is the single most expensive thing a town builds (rammed earth or stone, maintained for centuries), and its cost scales with its **length**, so a town walls in exactly what it must defend and no more - the line is drawn to skirt the built-up area, not to inscribe a tidy circle around a lot of empty ground. Historically this is why town walls are *irregular*: they kink in to exclude a gully and bulge out around a quarter, following the settlement's actual footprint (and the terrain). Two kinds of slack are legitimate and the check allows for them: (1) **terrain** - a wall climbs or skirts a hill rather than levelling it, so the hill counts as filled "occupancy" (Hirameki's north rampart rides up the citadel hill and is exempt there); (2) a **modest gate forecourt** - the open *masugata* assembly/defensive square just inside the gate is real, so a short open dip at the gate is fine. What is NOT fine is a long empty margin along a whole face (Hirameki's first town-scale draft enclosed empty ground at three of its four quadrant edges - the east rampart ran ~260px from anything). When the check fails, the fix is almost always to **pull that face of the wall inward** to ride just outside the last buildings (this is what Hirameki's S/SE/E faces got - and the cross-street and east quarter were drawn in to match, since a tighter wall means a smaller interior); only rarely do you instead **fill the margin** with displaced buildings. Note this composes with `streets_have_buildings`: streets earn their length from buildings, and the wall earns *its* length from the whole built area - both reject infrastructure drawn around emptiness.

### The validator (`check_village.py`)

The generator emits a manifest the validator asserts against; it must pass before a settlement map is presented. It works for **any** village/hamlet, not just Kikuta: the UNIVERSAL invariants are always checked, while the VILLAGE-SPECIFIC expectations are read from `manifest["meta"]` and from each channel's `frm`/`to` anchors.

- **Universal (always):** no farmhouse overlaps (rotated-rect SAT); nothing on a lane / **irrigation channel** (`no_structure_on_channel`, same footprint test as streams) / **road** (`no_structure_on_road`) / **stream** (`no_structure_on_stream`) / manor / **wall** (`no_structure_on_wall`) / **town street** (`no_structure_on_street`) / **religious hall** (`no_structure_on_religious`) / **gate guard station + tower** (`no_structure_on_gate`) / **torii arch** (`no_structure_on_torii`) - the manor, hall, gate structures, and each torii block a rect plus a building-half margin, because an ellipse undershoots their corners; all houses field-adjacent; every (on-map) field ringed; no cultivation on a hill; houses face south; the headman's house is the largest; no two body labels overlap; each channel is anchored at both ends, winds gently, and is reasonably direct; any torii are clear of the shrine and spread out; fields stay clear of any road or town street, incl. the road running out the gate (`fields_clear_of_road`) and never cross a wall (`fields_clear_of_wall` - abut only); every fully-on-map field shows a water source - a channel feeding it or the field abutting a stream/pond (`fields_show_water_source`); streams never run through fields (`streams_avoid_fields`); roads/streams/large terrain run off the map edge (`edge_features_run_off_map`); the religious building matches the settlement scale (`religious_matches_scale`); roads/streets are a ground layer drawn UNDER anything that legitimately sits on them - a gatehouse or a label (`roads_drawn_under_overlays`); in a town, businesses front the streets (`businesses_front_streets`), street-fronting buildings face the street they line (`buildings_face_street`), and dwellings stay off the main commercial frontage (`housing_off_main_street`).
- **Meta-driven (per settlement):** a village must have a headman / a hamlet must not (`village_has_headman` / `hamlet_has_no_headman`, from `meta.scale`); occupied-house count consistent with `meta.households` (~0.7 houses/household), or a `meta.target_houses` band, else the `meta.scale` default (village 40-80 / hamlet 10-30); tax-free plots 2-3 (villages); fallow fields ring abandoned houses ONLY if `meta.fallow_implies_abandoned`; the two largest common fields differ in orientation ONLY when there are two; shrine-on-summit + torii-on-hill ONLY if `meta.shrine_on_hill`; torii count == `meta.torii_expected`; pond checks ONLY if a pond exists; channel source anchored to pond / off-map edge / stream / field per its declared `frm`; channels run downhill ONLY if `meta.downhill` is declared (`channels_flow_downhill` - source uphill of the field along the slope).
- **Town-scale (`meta.scale=="town"`):** each non-farmer caste's building count falls in its `budgets.md`-derived band (`town_caste_count[merchant|laborer|servant|burakumin|samurai]` - merchant ~24, laborer ~29, servant ~5 standalone, burakumin ~12, samurai 5-10; shops are additional and ungated); farmers are the plurality (`town_farmers_plurality`); a magistrate's walled manor exists (`town_has_magistrate_manor`); at least one field runs off the edge (`town_has_field_off_edge`); an amphitheater exists unless `meta(amphitheater=False)` (`town_has_amphitheater`); when the manor is on a large hill, the amphitheater sits at the hill's foot (`amphitheater_at_hill_foot`) and the manor gate faces the town (`manor_gate_faces_town`); the town declares its monasteries via `meta.clan` or `meta.monastery_fortunes` (`town_declares_monasteries`) and has the right count and dedications (`town_monastery_count`, `town_monasteries_dedicated`); a noticeable minority of merchant houses keep an attached storehouse (`town_has_merchant_storehouses`, >= 3 kura); a rice-transit town declaring `meta(granary=True)` draws a distinct granary (`town_has_granary`). **Walled (`meta.walled`):** a wall + gate exist (`walled_town_has_wall`) and the wall is irregular (`wall_sections_irregular`: >= 5 sections, length CoV >= 0.25); no structure overlaps the rampart (`no_structure_on_wall`); a main street runs inward from the gate (`walled_town_has_main_street`); every inside-the-walls street has buildings along it - no "street to nowhere" (`streets_have_buildings`); the rampart hugs the built area rather than enclosing empty corner space, terrain and a modest gate forecourt excepted (`wall_hugs_the_town`); each monastery's torii avenue fills its approach space - several arches for a long clear run to the street, a single arch for a cramped corner (`monastery_torii_scale_with_space`); a small extramural gate market of a few shophouses sits outside the gate unless `meta(gate_market=False)` (`walled_town_has_gate_market`); the amphitheater sits inside the walls unless `meta(amphitheater="outside")` (`amphitheater_inside_wall`).

**Three disciplines this gate has taught us:**

1. **Any rule that can be machine-checked belongs in `check_village.py`, not only in this prose.** When a new Mode B rule emerges, add it as an assertion.
2. **The manifest must record what is actually RENDERED, not the generator's pre-render inputs.** The fields render as a smoothed (Catmull-Rom) curve that bows inward of the raw outline vertices; recording the vertices let a channel "connect" in the manifest while visually stopping in the gap. The generator now records the *sampled smoothed boundary* (`smooth_points`). A check is only as honest as the geometry it asserts against - sample the drawn shape, and still eyeball a crop, because a green check on the wrong geometry is worse than no check.
3. **Test the checks themselves, with negative fixtures, and enforce 100% coverage.** `gate(M)` takes a manifest dict and returns the failed-check names (`main(path)` wraps it for the CLI). `test_villages.py` proves the real maps PASS (integration, running the gens in-process so they count toward coverage); **`test_checks.py`** proves each check FIRES on a deliberately-broken synthetic manifest (unit); **`test_settlement.py`** reaches the generator branches the five maps don't. The integration/unit pair is not redundant: if a refactor silently neuters a check, every real map still passes and `test_villages` stays green while the check sits dead - only a negative fixture catches that. **Coverage is gated at 100%** (`pyproject.toml`: `[tool.coverage.report] fail_under = 100`), so this isn't aspirational - the suite *fails* below 100%. Run the **whole** suite (`python3 -m pytest` from the skill dir; needs `pytest-cov`); a subset under-reports and trips the gate. The few genuinely-unreachable defensive fallbacks carry an explained `# pragma: no cover`. **When you add a check or a generator branch, add the test that exercises it** - the gate will fail until you do. Writing "here is a map that SHOULD fail this" also forces you to enumerate the ways the thing can be wrong, which is how *logic gaps* (not just regressions) surface - the streets-to-nowhere miss was such a gap.

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

- **Draw-order / layering.** The generator emits two layers: the base (`self.add`) and a deferred **top layer** (`self.add_top`), concatenated base-then-top at `finish()`. Roads, streets, terrain, and buildings live in the base; **all labels and the gate furniture (guard station + tower) live in the top layer**, so a road or street can never paint over a label or a gatehouse that sits on it (a street runs *through* the gate, under the gatehouse). Anything that records a footprint a road might overlap should carry its draw-order `z` into the manifest so `roads_drawn_under_overlays` can gate it.
- 2400 px wide gives readable labels at typical viewing sizes. Smaller widths may render the smallest labels (latrines, well annotations) illegibly.
- **This manual command is for Mode A only.** Mode B settlement maps render their PNG automatically: `s.finish()` calls `rsvg-convert` at 2600px after writing the SVG (pass `render=False` or a different `png_width` to override), so the `.png` stays paired with the `.svg` without a separate step. Re-run the gen (or the test suite, which re-runs every gen) to refresh it; don't call `rsvg-convert` by hand for a Mode B map.
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

This checklist is for **Mode A** (compound/building plans). **Mode B settlement maps** follow their own loop instead - the "Workflow (spec → validator → persona)" steps above: `check_village.py` must report ALL CHECKS PASSED, then a persona read of the PNG. (Note the Mode B differences: title is the place name only - no subtitle/summary line - and no legend/key box.)

Before declaring done (Mode A):

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
- [`settlement.py`](settlement.py) - the shared Mode B library (`Settlement` class); all common machinery lives here
- [`pool/kikuta-village.gen.py`](pool/kikuta-village.gen.py) - Mode B example A: pond-fed, two staggered fields, 7-torii hill shrine, fallow-with-abandonment
- [`pool/hikari-no-sato.gen.py`](pool/hikari-no-sato.gen.py) - Mode B example B: stream-fed, one V-shaped field, internal fallow patch, flat-ground Benten shrine at the southern torii gateway, standalone Bishamon shrine
- [`pool/moritono.gen.py`](pool/moritono.gen.py) - Mode B example C: a hamlet (no headman/shrine/tax-free) with a forest and the magistrate's walled manor (`forest()` / `manor()` features)
- [`pool/hoshizora.gen.py`](pool/hoshizora.gen.py) - Mode B example D: an **unwalled town** (county seat) - Imperial Road spine, road-fronting urban core, all castes, single-monastery exception
- [`pool/hirameki.gen.py`](pool/hirameki.gen.py) - Mode B example E: a **walled town** - hill-anchored rampart, urban core inside, gate-to-yamen streets, chrysanthemum field, two monasteries (changed-hands), downhill irrigation, amphitheater at the hill foot
- [`check_village.py`](check_village.py) - Mode B automated validator (the machine gate); meta-driven so it works for any hamlet/village/town; run before presenting a settlement map
- [`test_villages.py`](test_villages.py) - pytest (also runnable standalone) that regenerates every pool map and runs the full gate; pins the whole Mode B process against regressions. Run it after any change to `settlement.py` or a spec
- [`test_checks.py`](test_checks.py) - negative-fixture unit tests for the gate itself: each asserts a check FIRES on a deliberately-broken synthetic manifest (so a silently-neutered check is caught). Add a fixture when you add or tighten a check
- [`test_settlement.py`](test_settlement.py) - unit tests for the `settlement.py` branches the pool generators don't exercise (unused vocabulary methods, internal fallbacks)
- [`pyproject.toml`](pyproject.toml) - pytest + coverage config; `fail_under = 100` mechanically enforces full coverage of `check_village.py` + `settlement.py`. Run `python3 -m pytest` from the skill dir (needs `pytest` + `pytest-cov`); the full suite must run together or the coverage gate trips
- `/workspace/setting/village-headsmen.md` - village structure, strip-allocation/usufruct, headman role (Mode B grounding)
- `/workspace/setting/median-domain.md` - sizing data (samurai per town, etc.)
- `/workspace/setting/government.md` - role hierarchies (ministries, magistrates, etc.)
- `/workspace/setting/hierarchies.md` - administrative structure (province / county / village)
- `/workspace/setting/demographics.md` - populations
- [`/.claude/skills/temple/SKILL.md`](../temple/SKILL.md) - temple organization (for diagrams of religious sites)
- [`/.claude/skills/relic/SKILL.md`](../relic/SKILL.md) - Japanese authenticity triangle; relic conventions
- `/.specify/memory/constitution.md` - Principle I (visual verification before declaring done), Principle XI (Japanese authenticity)
