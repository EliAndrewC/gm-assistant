# Implementation Plan: Shrine Builder

**Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md) | **Date**: 2026-10-17

## Summary

A `/shrines` page in the L7R Toolkit. The page is a GET form, so the design IS the link: each
category is a radio group named by its key, free text goes in text inputs, and submitting (or the
small script keeping the address bar in sync) leaves a URL that reproduces the design. The catalog
(categories, options, descriptions, and the GM-only costs) is a YAML file next to the code, outside
`static/`, so it is never served. The server renders cost information only when the request carries
a GM session; for everyone else the template never receives a cost.

## Technical context

- Python 3.14, CherryPy + Jinja2, PyYAML (all already in use).
- New package `webapp/l7r/shrines/`: `__init__.py` (pure logic: load catalog, parse design and GM
  settings from query params, price a design, negotiate), `catalog.yaml`, `CLAUDE.md` (index,
  historical grounding, test steps).
- Route: `Root.shrines(**params)` in `l7r/app.py`; template `templates/shrines.html`; styles in
  `static/css/shrines.css`, script in `static/js/shrines.js`, both loaded through the layout's
  `head_extra` block so the 2,977-line `l7r.css` does not grow.
- Nav: one `Section` row in `sections.py`.
- Tests: `tests/test_shrines.py` (logic) and `tests/test_shrines_routes.py` (rendering, the
  no-leak property), 100% coverage on the new package.

## Design decisions

1. **Pricing model.** Each option has zero or more *lines* `{contract, koku, heavy, per}`. `heavy`
   is porterage weight in units; `per: <category>` multiplies the line by the `units` of the option
   chosen in that category (size multiplies the sanctuary lines; gate form multiplies gate material
   lines). Fixed site-preparation lines are always added. Porterage = total heavy units x the
   remoteness rate, as its own contract. One generic mechanism, no per-category code.
2. **Moot categories** (FR-015): an option may list `voids: [category, ...]`. A voided category is
   rendered as not applying, its selection is dropped from the share link and from costs.
3. **GM params are prefixed `gm_`** and ignored entirely unless the viewer is a GM (FR-014). The
   share link is built from design params only, server-side and again in the script.
4. **No-leak property is tested by rendering**: the player view of the most expensive design is
   asserted to contain no catalog price, no `koku`, and no contract name.
5. **Player text has a word guard**: a test fails if any player-facing description contains a price
   word or a digit followed by `koku`/`bu`/`zeni`.
6. **Default budget** = reference design (flagged `reference: true` per category in the catalog)
   priced at the default remoteness, x 1.2, rounded up to 5.
7. **GM recompute** by resubmitting the form on change (server-side math, one implementation); the
   script restores scroll position so a reload does not jump to the top. Player changes only update
   the address bar and moot markers, no reload.

8. **One rule grammar, forward-only (refactor after amendment 4, GM invited it).** By amendment 4
   the builder had grown four applicability mechanisms (an option's `voids`, a category's
   `only_with`, an option's `only_with`, and `alt_when`), each implemented twice (Python and the
   browser script). Replaced by ONE `when` condition on categories and options (same grammar for
   `alt_when`), whose every clause must name an EARLIER category - validated. That makes
   resolution a single forward pass in wizard order (no fixpoint), and it rules out by
   construction two rules that flip each other forever, which a fixpoint over negated conditions
   can do. The browser no longer reads per-element data attributes: the server inlines the rules
   as JSON (conditions only; a test asserts no price word appears in it) and shrines.js runs the
   same pass. The catalog split into `data/catalog.yaml` plus one file per group, and the module
   into `catalog.py` / `design.py` / `pricing.py`, keeping files at human scale.

## Constitution Check

- **I. Viewports**: UI added; screenshot contact sheets at all four viewports and a zero-issue DOM
  audit before done; `frontend-review` subagent run. PASS (committed).
- **II. Design**: extends the existing editorial-archive system (Fraunces / EB Garamond / Shippori
  Mincho, paper and vermilion) rather than a new look; option cards as a field guide. PASS.
- **III. Pool conventions**: N/A - a fixed catalog, not a pool of generated content of a recurring
  kind.
- **IV/V. GM source**: N/A - no SOURCE blocks touched.
- **VI. Verify before done**: `make done`, screenshots, audit, review. PASS (committed).
- **VII-IX. Generation voice / setting**: option text uses setting terms (Fortunes, country monk,
  Ministry of Rites) and stays in-world; no campaign facts written. PASS.
- **X. Python discipline**: ruff, mypy --strict, 100% coverage on `l7r.shrines`. PASS (committed).
- **XI. Japanese authenticity**: every Japanese term in option text is a real term with its
  meaning given (nagare-zukuri, komainu, hassokuan, ...). PASS (committed).
- **XII. Historical grounding**: research.md R1-R6; prices carry their why in `CLAUDE.md` and the
  catalog header. Distinct historical forms are options, never one pick. PASS.
- **XIII/XIV. Regressions / defects**: baseline gate on unmodified code before push. PASS.
- **XV/XVI**: run unattended; spec reviewed FAITHFUL (round 2). PASS.
- **XVII/XVIII**: no README; the word guard ships with its own test proving it fires. PASS.
