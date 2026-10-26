# Feature 228: Shrine builder - Other, description, art, wiki page, old links

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-26

**Status**: Draft

**Input**: `request.md` (the GM's two messages, verbatim). Builds on feature 216 (`specs/216-shrine-builder/`).

## Why

Players liked the shrine builder (`/shrines`). They want to see the shrine they designed: a written description and a
picture. They also want room for ideas the cards do not offer. A finished shrine should live on the campaign's
Obsidian Portal wiki rather than only in a link, and every link a player has already made, Shizu's above all, must keep
working.

## User Scenarios & Testing

### User Story 1 - Old links keep working, now and in every future change (Priority: P1)

Shizu's link (in `request.md`) and any other link a player has made open the same design they always did.

**Acceptance**:
1. Shizu's exact link resolves to the same choices it does today (every step, both `sharing` picks, the name), with no
   "could not be restored" notice.
2. A frozen list of real links (`webapp/tests/shrine_links.txt`, Shizu's first) is checked by a test: each resolves
   with nothing dropped and to the recorded choices. Adding a link to that list is how any future player link gets
   protected.
3. If a future change renames a step or an option, a compatibility table (`data/legacy.yaml`) maps the old key to the
   new one; a link that used an old key is rewritten and the browser is redirected to the current form. Removing an
   option or a step that a frozen link uses fails the test unless the table says where it went.
4. This is a standing rule of the shrine builder, written into `l7r/shrines/CLAUDE.md` for every future feature.

### User Story 2 - "Other" on every step (Priority: P1)

On every choice step a player can pick "Something else", type their own idea, and say whether it replaces the cards
("Instead") or adds to their pick ("As well").

**Acceptance**:
1. Every option step (not the name step) shows a "Something else" choice below its cards. Checking it reveals a text
   box and two choices: **Instead of these** and **As well as my choice**.
2. "Instead": the cards on that step are cleared and set aside; Next is allowed once the text box has text. The step
   then counts as having no listed option, so later steps that need a particular option there do not appear (the one
   `when` grammar: an unanswered step fails a plain clause and passes a `not`).
3. "As well": the player still picks a card (or cards, on a multi-select step) as usual; the text is an addition.
4. The text, the mode and the step ride in the link (`other_<step>=...`, `instead_<step>=1`), are capped in length,
   and come back when the link is opened. Links without them are unaffected.
5. The summary on the last step shows the other text on its step's line ("instead" or "as well").
6. Free text is the player's own and is exempt from the catalog's player-text tests (price words etc.).

### User Story 3 - The GM prices an "Other" (Priority: P1)

**Acceptance**:
1. In the ledger, every "Other" in the design appears under its own contract, **Other work**, as a line with an
   optional koku field (GM only; read-only for Commerce players, like every ledger figure). Empty = unpriced.
2. A priced Other adds to the fair price, is haggled with the Other work contract, and counts like any line.
3. An "Instead" Other removes the price of the listed option it replaces (there is no listed option).
4. If any Other is unpriced, the totals say so: the fair price, the paid price and what Tadashi keeps read as the
   figure "plus N unpriced" / "before N unpriced", never as a complete number.
5. A player without ledger access still never sees a price or a `gm_` field (feature 216's secrecy tests extend to
   designs with Others and GM Other prices in the link).

### User Story 4 - A written description (Priority: P1)

**Acceptance**:
1. On the last step, a signed-in player or the GM can press **Describe the shrine**. A cheap Gemini text model writes
   two or three short paragraphs describing the shrine as a visitor would find it, built from every chosen option
   (its label and player text, in the wording in force, memorial or kami) and every Other (instead/as well).
2. The prompt is short: a fixed brief (setting, tone, house style: hyphens not dashes, American spelling, no prices,
   no people living there, never contradict a choice) plus the design. No setting corpus.
3. The description appears in an editable box; pressing the button again writes a new one (replacing the box after
   confirmation if it was edited).
4. A signed-out visitor sees no button, only a note to sign in. A per-user guard stops only runaway or abusive
   request loops (well above any player's retrying); it never blocks ordinary retries.
5. Cost per description is recorded in the plan (measured), and is a fraction of a cent.

### User Story 5 - A picture, in the player's chosen style (Priority: P1)

**Acceptance**:
1. A signed-in player or the GM chooses an art style (several, e.g. ink wash, woodblock print, watercolor, realistic)
   and presses **Draw the shrine**. A Gemini image model draws it.
2. The image prompt is built **deterministically** from the design: each option carries a short visual phrase
   (`look:` in the catalog), each Other's text is included as written, plus the style's own preamble and fixed
   constraints (no people unless the player asks, no lettering, no modern objects). No LLM in between.
3. The prompt is shown in an editable box before drawing. The player may edit it (e.g. where the stone guardians
   stand) and draw again; a "rebuild from my choices" control restores the generated prompt.
4. Every press draws a new picture; the player can try again as often as they like, or change the style.
5. Signed-out visitors cannot draw. The same runaway-loop guard as US4.4, never a cap on ordinary retries.

### User Story 6 - Save the shrine as an Obsidian Portal wiki page (Priority: P1)

**Acceptance**:
1. With a description and a picture (both required, as the GM said upload "will save off both the description and
   the image"), a signed-in player or the GM presses **Create wiki page**. The app
   creates a public wiki page named after the shrine, tagged `shrine`, holding the picture, the description and a link
   back to this design in the shrine builder. The GM-only notes of the page hold the image style and prompt, so they
   can be reloaded.
2. Nothing is stored on fly.io: the wiki page is the only save.
3. Whenever anyone opens a shrine link, the page looks for a wiki page for that shrine (same name, tagged `shrine`).
   If there is one, it shows a link to it, and loads its description and picture into the boxes, and its prompt and
   style.
4. If the design in the wiki page's link equals the current design (compared after resolving both, so order and old
   key spellings do not matter), the page just says the wiki page matches. If not, it says the choices here differ
   from the wiki page and offers **Update wiki page**.
5. Update replaces the page's description, link, and (if a new picture was drawn) the picture; otherwise the picture
   on the page is kept.
6. The wiki lookup never slows or breaks the builder: it is a separate request, and if Obsidian Portal is down the page
   says it could not check.

## Requirements

- **FR-001** (US1) Shizu's link and every link in `tests/shrine_links.txt` resolve to their recorded choices with
  nothing dropped; this is a standing, tested rule for all future shrine-builder work.
- **FR-002** (US1) `data/legacy.yaml` maps renamed steps and options; links using an old key are rewritten and
  redirected (303) to the current query. Validation: every legacy target exists.
- **FR-003** (US2) Every option step offers "Something else" with free text (cap 300 characters) and a required mode
  (Instead / As well). Link keys `other_<step>`, `instead_<step>`; catalog keys may not collide with these prefixes.
- **FR-004** (US2) Instead = no listed option on that step (resolution treats it as unanswered); As well = a pick is
  still required. An Other on a step not in play is dropped like a pick.
- **FR-005** (US3) Ledger: contract **Other work**; each Other is a line with optional GM price `gm_other_<step>`;
  totals name unpriced Others.
- **FR-006** (US4) `POST /shrines/describe`: signed-in only, a per-user runaway-loop guard (never a cap on retries), cheap model from config
  (`[shrines] text_model`), short fixed brief, returns text.
- **FR-007** (US5) Every option carries `look:` (validated non-empty); `GET`/inline image prompt built from design +
  style; `POST /shrines/draw` (signed-in, same guard) takes the (possibly edited) prompt and a style and returns a
  PNG.
- **FR-008** (US6) `POST /shrines/wiki` (signed-in) creates or updates the OP wiki page; `GET /shrines/wiki?...`
  (anyone) returns the page's link, whether it matches, its description, picture URL, prompt and style.
- **FR-009** The player-text rules of feature 216 (no price words, no absences, etc.) cover the new player-facing text,
  including `look:` phrases (which the player can read in the prompt box). Player-typed text is exempt.
- **FR-010** Feature 216's FR-017 ("no homework": the name is the only free-text field) is amended by the GM's request:
  the Other text box is the second, and it is optional.

## Decisions made (cheap to change)

- A shrine's wiki page is found by its **name** (old links carry it; it does not change when options change). Two
  shrines with one name share a page - the wiki would not allow two anyway.
- Any signed-in player can create or update a shrine's page; updating replaces the body the app wrote.
- The description model is the cheapest Gemini Flash-Lite the project already uses (`gemini-3.1-flash-lite`);
  the image model is the one portraits use (`[gemini] image_model`), at 4:3.
- Art styles are a short fixed list in `data/art.yaml`.
- **"Instead" on a step others depend on** follows the one `when` grammar: e.g. "Something else / Instead" on the
  Kind step means no listed kind, so the remains steps and the memorial wording do not apply. The player's own text
  still reaches the description and the picture.
- **"Matches"** compares the two designs after resolving both: every pick, the name, and every Other (`other_`,
  `instead_`); `gm_` fields are ignored.
- **Other text is capped at 300 characters**, because the whole design lives in the link.
- **"Manually editing the prompt"** (message 2) is read as editing the description text and the image prompt; the
  description's fixed brief is not player-editable.
- **The picture on update**: Update keeps the page's current picture unless a new one was drawn this visit.

## Out of scope

- Storing anything on fly.io; a gallery of shrines; deleting wiki pages from the builder.
