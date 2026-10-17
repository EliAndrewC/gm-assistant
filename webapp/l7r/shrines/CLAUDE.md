# Shrine builder (`/shrines`, feature 216)

A player designs a small, remote, unstaffed shrine by choosing one option per category. The design
lives entirely in the link. The GM opens the same link while signed in as GM and sees the fair price
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
- **Unstaffed and remote** (FR-002a): no option adds living quarters, lodging or an office, and the
  sanctuary stays one bay. Tests check both.

## Historical grounding (why the numbers are what they are)

- **Unstaffed shrines are the normal case.** Most Japanese shrines have no priest of their own
  (*kenmusha*, served from another shrine) and are kept by parishioners; *hokora* in groves and by
  roads are smaller still. So the catalog is built around a place nobody lives at.
- **Currency: 1 ryo = 1 koku.** Both are pinned to a koku of rice, and the Edo rice price hovered
  near one ryo per koku. Relative prices are the point, and this keeps them.
- **Anchors** (village ledgers from Tama district, 1749-1805, AIJ paper No. 420): copper re-roofing
  of a LARGE one-bay sanctuary ~43 ryo, mostly copper bought in Edo; carved front panels and
  painting on the same building ~62 ryo, mostly labor; a small sanctuary's repair and repainting
  ~10 ryo; a whole village temple hall ~250 ryo. So copper roofing a small sanctuary is 22 koku and
  full carving 20; "generous" size multiplies sanctuary lines by 1.8 (a 7.8-shaku bay against
  4.2). A craftsman earned about 1 ryo per 30-40 days.
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

- Signed out: pick options; the address bar and the "Your design" link follow every change. Choose
  "Sacred tree or rock" and the roof, timber, finish, carving, size and sacred-object sections grey
  out. View source: no `koku` anywhere.
- Signed in as GM, open the same link: the GM ledger appears on the right (below on narrow screens).
  Type a roll into a contract; the page recalculates and the "Tadashi keeps" line moves.
