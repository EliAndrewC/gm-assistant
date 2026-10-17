# Shrine builder (`/shrines`, feature 216)

A player designs a small, remote, unstaffed shrine in a step-by-step wizard, one decision per page
(the name first, a summary and the share link last; steps that do not apply are skipped). The
design lives entirely in the link; the current step rides in the `#step-...` hash, which the share
link never carries. The GM opens the same link while signed in as GM and sees the fair price
of every choice, grouped into contracts, and a ledger where Tadashi's Commerce rolls bring each
contract down. What is left of the budget is what he keeps.

| file | what |
|---|---|
| `data/catalog.yaml` | contracts, remoteness, site lines, `alt_when`, the order of groups - and the format notes for everything below |
| `data/groups/<key>.yaml` | one wizard section each: its steps, options, player text, GM-only price `lines`, and `when` rules |
| `catalog.py` | the data model, the one `when` grammar (`Clause`), loading (`load_raw` merges the files) and validation |
| `design.py` | resolving a design in one forward pass, links, moot notes, `enables`, and `rules_json` for the browser |
| `pricing.py` | fair prices, porterage, Tadashi's per-contract haggling, number formatting (GM only) |
| `../templates/shrines.html`, `../static/css/shrines.css`, `../static/js/shrines.js` | the page; the script's `resolve()` mirrors `design._resolve` |
| `../../tests/test_shrines.py`, `../../tests/test_shrines_routes.py` | logic and rules; what each viewer can see |
| `specs/216-shrine-builder/` (repo root) | spec with every amendment, the GM's messages verbatim, research with sources, plan |

## The one rule: `when`

Every step and every option may carry `when: {<earlier step>: [options]}` or
`{<earlier step>: {not: [options]}}`; all keys must hold, and an unanswered step counts as "no
value" (a plain list fails, a `not` passes). Clauses may only look BACKWARD - validation rejects a
forward or self reference - so `design._resolve` and the browser's `resolve()` settle the whole
wizard in one pass. Don't reintroduce `voids`/`only_with`-style side channels: express it as a
`when` on the thing that appears or disappears. `alt_when` uses the same grammar to switch the
`alt:` wording (for a memorial the dead are honored ancestors, not kami).

## Rules that hold this together

- **The player never sees a price.** `catalog.yaml` is outside `static/`, and the route builds a
  ledger only for a GM session; the `gm_*` params are not even read otherwise. A test renders the
  costliest design with GM params forced into the link, as anonymous and as player, and asserts no
  `koku`, no contract name and no `gm_` survives.
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
- **No homework** (FR-017): the only free-text field is the shrine's name, pre-filled
  (`default_name` in the catalog: "The memorial hermitage of Shoda the Fox-forest Guardian", the
  GM's wording). Don't add notes or inscription boxes.
- **Nothing pre-selected, and no fixed order** (FR-023): every step starts empty, Next waits for a
  choice, and `shrines.js` shuffles the cards each time a step is shown. Catalog order means
  nothing to the player.
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
`docs/spec-kit-and-reviews.md`): use a `general-purpose` agent whose message starts with the
definition's body pasted VERBATIM and ends with the file to read, so the shared part still caches
as a prefix. Apply findings with judgment, re-run the tests, and re-review the changed sections
once. Recurring findings become tests (as "no hermit/disciples/he outside a `for Shoda` example"
did, in `test_shoda_only_appears_as_an_example`).

## Historical grounding (why the numbers are what they are)

- **Unstaffed shrines are the normal case.** Most Japanese shrines have no priest of their own
  (*kenmusha*, served from another shrine) and are kept by parishioners; *hokora* in groves and by
  roads are smaller still. So the catalog is built around a place nobody lives at.
- **Currency: 1 ryo = 1 koku.** Both are pinned to a koku of rice, and the Edo rice price hovered
  near one ryo per koku. Relative prices are the point, and this keeps them.
- **Anchors** (village ledgers from Tama district, 1749-1805, AIJ paper No. 420): copper re-roofing
  of a LARGE one-bay sanctuary ~43 ryo, mostly copper bought in Edo; carved front panels and
  painting on the same building ~62 ryo, mostly labor; a small sanctuary's repair and repainting
  ~10 ryo; a whole village temple hall ~250 ryo. So copper roofing a small (4.2-shaku bay)
  sanctuary is 22 koku and relief panels 20 (the ledger's large building had a 7.8-shaku bay). A
  craftsman earned about 1 ryo per 30-40 days.
- **Estimates, not ledger figures**: stone torii, guardians, lanterns, steles. They are mason labor
  plus **porterage**: every heavy line carries `heavy` loads, charged at the remoteness rate (cart
  road 0.25, foot trail 0.6, no trail 1.0 koku per load). Remoteness changes porterage and nothing
  else.
- **Rites**: a pacification festival is its own option because enshrining someone who died a hard,
  disputed death is the *goryo* pattern (Michizane as Tenjin): the shrine exists to calm the dead.
- **Negotiation**: Commerce has no pricing formula in the rules, so each contract borrows the
  Culture gift rule's shape: max(0, roll - baseline) percent off, baseline 25 by default. The GM can
  type a contractor's contested roll into the baseline instead.
- **Suggested budget**: the reference design (`reference:` in each category - a "fairly nice small
  memorial in the forest", ~135 koku at the default remoteness) x 1.2, rounded up to 5 =
  **165 koku**. The
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
