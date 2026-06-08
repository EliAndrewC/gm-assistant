---
name: diagram
description: Generate SVG diagrams of L5R/L7R locations (manor plans, village layouts, temple plans, battlefields, etc.) using a consistent style library, then render to PNG. Subjects are designed in conversation with the GM, drawn top-down in a labeled diagrammatic style, and saved as paired .svg + .png in the pool.
---

# Diagrams

Generate top-down SVG plans of Rokugani locations - magistrate manors, village layouts, temple plans, military compounds, battle terrain, and the like. The skill covers the shared technical and aesthetic conventions (palette, patterns, building vocabulary, render pipeline, historical reference framework). The per-subject content - *what specifically goes in a given diagram* - is decided in conversation with the GM, not codified here.

The skill's first worked example is [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) (County Magistrate Kitsune Tatsuya's two-courtyard manor). All conventions below were extracted from that work, and `pool/ochiba-magistracy.svg` is the canonical template - copy it as the starting point for new diagrams and edit from there rather than rebuilding from scratch.

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
- `pool/<subject>.png` - 2400 px rendered output

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

- [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) - canonical worked example; use as the template for new diagrams
- `/workspace/setting/median-domain.md` - sizing data (samurai per town, etc.)
- `/workspace/setting/government.md` - role hierarchies (ministries, magistrates, etc.)
- `/workspace/setting/hierarchies.md` - administrative structure (province / county / village)
- `/workspace/setting/demographics.md` - populations
- [`/.claude/skills/temple/SKILL.md`](../temple/SKILL.md) - temple organization (for diagrams of religious sites)
- [`/.claude/skills/relic/SKILL.md`](../relic/SKILL.md) - Japanese authenticity triangle; relic conventions
- `/.specify/memory/constitution.md` - Principle I (visual verification before declaring done), Principle XI (Japanese authenticity)
