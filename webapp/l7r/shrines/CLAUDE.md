# Shrine builder (`/shrines`, feature 216)

A player designs a small, remote, unstaffed shrine in a step-by-step wizard, one decision per page
(the name first, a summary and the share link last; steps that do not apply are skipped). The
design lives entirely in the link; the current step rides in the `#step-...` hash, which the share
link never carries. The GM opens the same link while signed in as GM and sees the fair price
of every choice, grouped into contracts, and a ledger where Tadashi's Commerce rolls bring each
contract down. What is left of the budget is what he keeps.

| file | what |
|---|---|
| `catalog.yaml` | categories, options, player text, and the GM-only price `lines`. Edit prices and options here |
| `__init__.py` | load/validate the catalog, read a design and the GM's `gm_*` settings from query params, price, negotiate |
| `../templates/shrines.html`, `../static/css/shrines.css`, `../static/js/shrines.js` | the page |
| `../../tests/test_shrines.py`, `../../tests/test_shrines_routes.py` | logic; what each viewer can see |
| `specs/216-shrine-builder/` (repo root) | spec, research trail with sources, plan |

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
- **Every option says why it is worth choosing** (FR-026): `appeal:` in the catalog, one sentence,
  required on every option except one described as "one of the most common". Tested.
- **Form-specific decisions** (FR-025): a category with `only_with: {form: [himorogi]}` applies
  only to that form (the kami's dwelling; the ground before it). `_voided` handles it server-side,
  `data-only-with` client-side.
- **Memorial or kami shrine** (FR-028 to FR-031): the step after the name picks the kind. A
  memorial adds the remains steps (`only_with: {kind: [memorial]}`): the heart of the shrine, how
  the remains are prepared, the salted head, sharing them (the Temple of Ebisu), storing them, and
  showing them. Remains at the heart means no kami: `catalog.alt_when` switches every `alt:` text
  (the "kami's dwelling" wording becomes the place where he rests) and voids the sacred object and
  the open-sky dwelling step. No boiling of bones - no East Asian record (research.md R7).
- **Browser Back = wizard Back** (FR-024): Next and summary jumps push a history entry; on
  popstate going back, the wizard shows the previous APPLICABLE step (what its own Back does), not
  merely the last page visited. The wizard's Back calls `history.back()` when there is a wizard
  entry behind it, so the two never drift apart.

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
  forest shrine", ~121 koku at the default remoteness) x 1.2, rounded up to 5 = **145 koku**. The
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
