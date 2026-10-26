# Shrine builder (`/shrines`, features 216 and 228)

## OLD LINKS MUST KEEP WORKING (GM 2026-10-26, standing rule for every change here)

Players have made shrines, and a link IS the save (Shizu's is the first line of
`tests/shrine_links.txt`). Every future change must keep every such link opening the design it was
made with. The format may change, but only behind a compatibility layer: a renamed step or option
goes into `data/legacy.yaml` (old key -> current key), `parse_design` reads old links through it,
and `GET /shrines` 303-redirects an old link to the current spelling. Never delete or rename an
option a saved link may use without an entry there, and never edit a frozen link to make a test
pass. Add any link a player shares to `tests/shrine_links.txt`; `tests/test_shrines_other.py`
checks that each one still resolves with nothing dropped.

A player designs a small, remote, unstaffed shrine in a step-by-step wizard, one decision per page
(the name first, a summary and the share link last; steps that do not apply are skipped). The
design lives entirely in the link; the current step rides in the `#step-...` hash, which the share
link never carries. The GM opens the same link while signed in as GM and sees the fair price
of every choice, grouped into contracts, and a ledger where Tadashi's Commerce rolls bring each
contract down. What is left of the budget is what he keeps. A signed-in player who owns a
character on the character-sheet app that is in a gaming group and has Commerce sees the same
ledger read-only (FR-048); its inputs stay the GM's.

| file | what |
|---|---|
| `data/catalog.yaml` | contracts, remoteness, site lines, `alt_when`, the order of groups - and the format notes for everything below |
| `data/groups/<key>.yaml` | one wizard section each: its steps, options, player text, GM-only price `lines`, and `when` rules |
| `catalog.py` | the data model, the one `when` grammar (`Clause`), loading (`load_raw` merges the files) and validation |
| `design.py` | resolving a design in one forward pass, links, moot notes, `enables`, and `rules_json` for the browser |
| `pricing.py` | fair prices, porterage, Tadashi's per-contract haggling, number formatting (ledger viewers only) |
| `data/looks.yaml` | feature 228: what each option LOOKS like, one phrase each, for the image prompt (missing or stray = CatalogError) |
| `data/art.yaml`, `art.py` | the art styles; the deterministic image prompt; the Gemini image call (REST) |
| `describe.py` | the description's short brief and the design as the model reads it |
| `wiki.py` | the shrine's Obsidian Portal wiki page: body, GM-notes block, parsing it back, finding it by name |
| `web.py` | `ShrineServices`: `/shrines/prompt`, `/shrines/describe`, `/shrines/draw`, `/shrines/wiki`, the runaway guard |
| `data/legacy.yaml` | renamed link keys (see the rule above) |
| `access.py` | `CostAccess`: who besides the GM sees the ledger - owners of a grouped Commerce character on the sheet app (`GET /api/characters`, `[character_sheet] roll_query_token`), cached 10 minutes, failing closed |
| `../templates/shrines.html`, `../static/css/shrines.css`, `../static/js/shrines.js` | the page; the script's `resolve()` mirrors `design._resolve` |
| `../../tests/test_shrines.py`, `../../tests/test_shrines_routes.py` | logic and rules; what each viewer can see |
| `../../tests/test_shrines_other.py`, `../../tests/test_shrines_studio.py`, `../../tests/shrine_links.txt` | feature 228: frozen links, Something else, its pricing; description, picture, wiki, routes |
| `specs/216-shrine-builder/`, `specs/228-shrine-wiki-art/` (repo root) | specs with every amendment, the GM's messages verbatim, research with sources, plans |

## The one rule: `when`

Every step and every option may carry `when: {<earlier step>: [options]}` or
`{<earlier step>: {not: [options]}}`; all keys must hold, and an unanswered step counts as "no
value" (a plain list fails, a `not` passes). Clauses may only look BACKWARD - validation rejects a
forward or self reference - so `design._resolve` and the browser's `resolve()` settle the whole
wizard in one pass. Don't reintroduce `voids`/`only_with`-style side channels: express it as a
`when` on the thing that appears or disappears. `alt_when` uses the same grammar to switch the
`alt:` wording (for a memorial the dead are honored ancestors, not kami).

## Rules that hold this together

- **The player never sees a price** - unless their character has Commerce (FR-048). `catalog.yaml`
  is outside `static/`, and the route builds a ledger only for the GM (`is_gm`, with inputs) and a
  Commerce player (`priced`, read-only: the link's GM figures ride in hidden inputs so a resubmit
  keeps them); the `gm_*` params are not even read otherwise. A test renders the costliest design
  with GM params forced into the link, as anonymous, as player and as each kind of non-qualifying
  sheet owner (ungrouped, no Commerce, editor only, NPC), and asserts no `koku` and no `gm_`
  survives. If the sheet app is down or the token unset, nobody but the GM sees costs.
- **Player text never implies price.** `test_player_text_never_mentions_price` runs a word list
  (cheap, costly, luxury, budget, any number followed by koku/bu...) over every label, prompt and
  option text. Describe what a thing IS and what it SIGNALS, never what it is worth.
- **Distinct forms, not a quality ladder** (spec FR-003, constitution XII). Where history did a
  thing several ways, each way is an option with its own meaning. Don't collapse a category into
  good/better/best.
- **Unstaffed and remote** (FR-002a): no option adds living quarters, lodging or an office.
- **No upgrades, no absences, no defaults** (GM 2026-10-17, FR-019 to FR-021). No option is
  another plus more (the old "vermilion" beside "black lacquer with vermilion"), so there is no
  size category - the sanctuary is one small bay. No option is a "None": the forest guards the
  shrine, a clearing lights the path, visitors wash in the stream as the hermit did. Prompts ask
  "what"/"how", never "is there a...?". Nothing is "the usual"; say "one of the most common".
  Tests enforce each of these.
- **No homework** (FR-017): the only free-text field a player must fill is the shrine's name,
  pre-filled (`default_name` in the catalog: "The memorial hermitage of Shoda the Fox-forest
  Guardian", the GM's wording). Don't add notes or inscription boxes. Feature 228 (the GM's request)
  adds ONE optional box per step, "Something else", off until the player turns it on.
- **Something else** (feature 228): `other_<step>=<text>` (300 characters), plus `instead_<step>=1`
  when it replaces the cards. "Instead" means the step has no listed option, so the `when` rules see
  it unanswered (Instead on Kind removes the remains steps). "As well" still needs a pick. The GM
  prices each one in the ledger's Other work contract (`gm_other_<step>`); unpriced ones are named
  in the totals ("+ 1 unpriced"), never silently counted as nothing. Option inputs carry `data-opt`
  in the page: nothing else in a fieldset is a pick, so script selectors must use it.
- **The studio** (feature 228, last step): a description (Gemini Flash-Lite, a ~250-word brief,
  ~$0.001 each), a picture (the portrait image model, 4:3, ~$0.07, the prompt built from `look`
  phrases with no LLM; the player can edit it, and the style preamble is added only at draw time),
  and the shrine's wiki page on Obsidian Portal, which is the ONLY save (nothing is stored on
  fly.io; a drawn picture stays in the browser until saved). Describe, draw and save need a sign-in;
  anyone can see the wiki status and a saved page's text and picture. The page is found by the
  shrine's NAME and tag `shrine`, and "matches" compares the two designs after resolving both. The
  key is the webapp's `[gemini] api_key` (written in quotes in the secrets file: `_load_secrets`
  strips them, as ConfigObj does - a quoted key once reached Google with its quotes). The
  per-user guard (120 descriptions, 60 pictures an hour) only stops runaway loops: the GM wants
  players to retry as often as they like.
- **Nothing pre-selected, and no fixed order** (FR-023): every step starts empty, Next waits for a
  choice, and `shrines.js` shuffles the cards each time a step is shown. Catalog order means
  nothing to the player.
- **Effect tags** (FR-040/FR-041): an option that makes something possible later has a tag
  above its card counting the choices that exist because of it - "5 custom choices" (the steps it
  brings, or, if none, the later options it opens) - with a tooltip naming them. Derived by
  simulation, never written by hand: `design.option_effects` server-side, `updateEffects()` in
  shrines.js live. Options that only remove steps get no tag. Not "N extra/more steps": the GM
  ruled the word out (a step is specific to a choice, not extra).
- **Progress counts phases** (FR-042): "Part 2 of 5" from `phases:` in `data/catalog.yaml`, a
  fixed list, so the denominator never moves and nothing is ever called "skipped". Steps that only
  some choices bring sit inside an existing phase (the remains steps are in phase 1).
- **Multi-select steps** (FR-044): `multi: true` on a step makes its cards checkboxes; an
  option with `exclusive: true` stands alone ("Kept together"), the rest combine ("Choose any that
  apply"). Picks live in `Design.multi`, repeat their key in the link, and are priced each. A
  multi-select step may not be named in any `when` rule (validated), so it is settled after the
  single-choice steps and never changes what else applies.
- **Every step keeps two options** (FR-045): at least two options on every step carry no `when`
  of their own (tested), so no earlier choice can leave a step with one card.
- **Japanese terms explain themselves** (FR-043): any option with `ja`/`romaji` must have a
  `gloss` (validated); it shows as a tooltip on the term.
- **Commonness is the closing line** (FR-046): a common option's "one of / among / perhaps the
  most common ..." sentence is its `appeal`, styled like every other closing line, and the
  wording varies (tested).
- **Cards** (FR-035): every card in a row has the same height and its italic appeal line sits at
  the bottom.
- **Every option says why it is worth choosing** (FR-026): `appeal:` in the catalog, one sentence,
  required on every option except one described as "one of the most common". Tested.
- **Form-specific decisions** (FR-025): `when: {form: [himorogi]}` puts the kami's dwelling and
  the ground before it in play only for the open-to-the-sky form.
- **Memorial or kami shrine** (FR-028 to FR-036): the step after the name picks the kind. A
  memorial adds the remains steps: the heart of the shrine (his spirit honored as an ancestor and
  registered with the domain's Ministry of Rites, honored by those who knew him, or the remains
  themselves), preparing them, dividing them (the head is part of this, not its own step), storing
  them, and showing them. Options stay generic; Shoda and the Temple of Ebisu appear only as
  examples. For any memorial `alt_when` switches the kami wording to honored-ancestor wording;
  remains at the heart also switch off the sacred object and the open-sky dwelling step. Only
  washed bones can be shown in a reliquary, and the preparation step says so (`decides`). No
  boiling of bones - no East Asian record (research.md R7).
- **Browser Back = wizard Back** (FR-024): Next and summary jumps push a history entry; on
  popstate going back, the wizard shows the previous APPLICABLE step (what its own Back does), not
  merely the last page visited. The wizard's Back calls `history.back()` when there is a wizard
  entry behind it, so the two never drift apart.

## Reviewing the player text (FR-039)

The author of option text is not a reliable judge of it. After any substantial text change:

```bash
( cd webapp && python3 -m l7r.shrines.review /tmp/shrine-review )   # one file per section
```

then run the `shrine-text-review` agent (`.claude/agents/shrine-text-review.md`) once per file,
two or three at a time (memory). **Caching:** the agent definition IS the shared system prompt -
keep it identical across calls and put nothing in the message but "review <file>". In the session
that creates or edits the definition it is not yet registered (harness gotcha in
`docs/spec-kit-and-reviews.md`): use a `general-purpose` agent whose message is the definition's
body pasted VERBATIM followed by the file to read. That fallback does NOT cache across calls - it
was measured on 2026-10-17 writing ~41.7k tokens fresh per launch despite the shared body coming
first (`docs/subagent-caching.md`) - so use it only in that one session, and put `CACHE_OK` in the
prompt to pass `scripts/subagent-cache-hooks.sh`. Apply findings with judgment, re-run the tests, and re-review the changed sections
once. Recurring findings become tests (as "no hermit/disciples/he outside a `for Shoda` example"
did, in `test_shoda_only_appears_as_an_example`).

## Historical grounding (why the numbers are what they are)

- **Unstaffed shrines are the normal case.** Most Japanese shrines have no priest of their own
  (*kenmusha*, served from another shrine) and are kept by parishioners; *hokora* in groves and by
  roads are smaller still. So the catalog is built around a place nobody lives at.
- **Prices come from the money skill** (GM 2026-10-18, replacing the first hand-set figures). Every
  line is the midpoint of a synthesis row in `l7r/money/data/ledger.jsonl` (id `shrine/<category>/
  <option>/<contract>`). Each row began as a pre-research estimate in `l7r/money/data/
  estimates.jsonl` (its source names it), built from craftsman-days at 30-50 sen, laborer-days at
  13-20 sen and materials - the money skill's wage rows, with carpenters at 2.6-4.7x the unskilled
  day (diagram 0250). The method and the check-every-line-in-labor-days rule are in `.claude/skills/
  money/questions.md` "Construction". Research (diagram#6 for Shizu's lines, #7 for the rest)
  grades the estimate with a finding and moves the ROW; never log a post-research "estimate" to
  re-price, because calibration would grade the model against its own answer.
- **The anchors** behind the days (village ledgers from Tama district, 1749-1805, AIJ paper No. 420):
  copper re-roofing of a LARGE one-bay sanctuary ~43 ryo, more than half of it copper bought in Edo; a
  small sanctuary's repair and repainting ~10 ryo, two-thirds labor (~190-250 craftsman-days). Roof
  work scales with roof AREA (the square of the bay), so copper on a small sanctuary is ~9 koku, not 22.
- **Porterage**: a LOAD is ~400 kg, about ten porter trips or a cartload. Cart road: loading plus half to
  one cart-hire day (0.08 koku); a foot trail half a day in: ten porter round trips of a day (0.17);
  deep forest: two days a trip (0.33). Remoteness changes porterage and nothing else.
- **Rites**: a pacification festival is its own option because enshrining someone who died a hard,
  disputed death is the *goryo* pattern (Michizane as Tenjin): the shrine exists to calm the dead.
- **Negotiation**: Commerce has no pricing formula in the rules, so each contract borrows the
  Culture gift rule's shape: max(0, roll - baseline) percent off, baseline 25 by default. The GM can
  type a contractor's contested roll into the baseline instead.
- **Suggested budget**: the reference design (`reference:` in each category - a "fairly nice small
  memorial in the forest", ~62.7 koku at the default remoteness) x 1.2, rounded up to 5 =
  **80 koku** (165 before the money-skill re-price, 65 before diagram 0255 re-priced the sanctuary, 75 before 0268/0269 re-priced the pavilion, the lanterns and the site). The
  1.2 is Tadashi's budget negotiation won by more than 10. Computed, so it moves with the prices.

## Testing it

```bash
( cd webapp && python3 -m pytest -n auto -q tests/test_shrines.py tests/test_shrines_routes.py )
( cd webapp && cherryd --import l7r.app )    # then open http://localhost:8080/shrines
```

- Signed out: step through with Next; the address bar follows every change. Choose "Sacred tree or
  rock" on the Form step and the step count drops from 22 to 17 (timber, roof, finish, ornament and
  sacred object are skipped). The last step lists every pick (each line jumps back to its step) and
  holds the link. View source: no `koku` anywhere.
- Signed in as GM, open the same link: the GM ledger appears on the right (below on narrow screens).
  Type a roll into a contract; the page recalculates and the "Tadashi keeps" line moves.
- Old links: `python3 -m pytest -q tests/test_shrines_other.py -k frozen` (Shizu's link first).
- Something else: on any step, check "Something else", type, pick "Instead of these": the cards dim,
  Next unlocks, the link gains `other_<step>` and `instead_<step>=1`, and the summary shows it. As
  GM the ledger shows an Other work line with an "unpriced" box and "+ 1 unpriced" totals.
- Studio (signed in): on the last step press Describe the shrine (~2 s), pick a style, Draw the
  shrine (~15 s), then Create wiki page; reopen the link and the page's text, picture and prompt
  load back with "matches these choices"; change a choice and it says the choices differ.
- Signed in as a player whose grouped character has Commerce (Marshall as Asako Tadashi, Chris as
  Tsuruchi Jimen): the "Ledger" panel shows the same figures with no inputs; changing a choice
  reprices it. Any other player sees no ledger. A new Commerce rank shows within 10 minutes.
