# Mode A: Compound and building plans

This file is the Mode A half of the /diagram skill: interior plan views of manors, magistracies, temples, keeps, and battlefields, hand-authored in SVG.  Read [`SKILL.md`](SKILL.md) first for everything shared (principles, workflow, labeling, style conventions, render pipeline, output convention); this file adds the Mode A building vocabulary, checklist, and historical grounding.  The canonical template is [`pool/ochiba-magistracy.svg`](pool/ochiba-magistracy.svg) - copy it as the starting point for a new compound plan and edit from there rather than rebuilding from scratch.

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

Very small gray rects (~14-20 px square), labeled `latrine`. Place against walls in corners, away from food prep and water sources. Typically at least one for the inner court and one for the outer.

### Sacred features

- **Modest shrine (standalone)** - small wooden structure with torii silhouette nearby. For routine rural Inari shrines and the like.
- **Hall shrine (L5R-style, e.g., Fox lands)** - full building with vermillion edging (`#A03020` strips at top and bottom). Internal rail division for multiple altars; identifiers like torii silhouette (east) or straw-doll silhouette (west) for distinct altar aspects.
- **Workshop colonnade** - open hatched area (`colonnade-hatch` pattern) attached to a shrine's working side, for sacred craft production (e.g., cinnabar painting of threshold stones).

### Approaches and surroundings

- **Road to gate** - two stacked paths (solid translucent + dashed darker) for ~150 px into the gate from the appropriate cardinal direction. Label the destination/road name in italic alongside.
- **Town / surroundings outside walls** - by default, leave the surrounding parchment empty. Only add exterior buildings if the surrounding context is itself part of the diagram's subject.

## Checklist for a new diagram

This checklist is for **Mode A** (compound/building plans). **Mode B settlement maps** follow their own loop instead - the "Workflow (spec → validator → persona)" steps in [`settlements.md`](settlements.md): `check_village.py` must report ALL CHECKS PASSED, then a persona read of the PNG. (Note the Mode B differences: title is the place name only - no subtitle/summary line - and no legend/key box.)

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

## Historical grounding: the "why" behind the realism checks (Mode A)

Same project rule as the Mode B grounding section in [`settlements.md`](settlements.md): whenever historical research drives a Mode A generation rule, convention, or magic number, record the reasoning here next to the rule - what the research found, the decision it drove, and any deliberate departure from literal reality.  (The Edo-vs-Sengoku defaults and the deliberate L5R divergences live in SKILL.md's "Rokugan historical reference framework"; per-feature research findings for buildings go here.)
