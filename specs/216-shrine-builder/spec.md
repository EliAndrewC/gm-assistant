# Feature Specification: Shrine Builder

**Feature Branch**: none (project works on `main`; `SPECIFY_FEATURE=216-shrine-builder`)

**Created**: 2026-10-17

**Status**: Draft

**Input**: GM request, 2026-10-17 (dictated; quoted with voice-to-text corrections applied - "Shota" = Shoda, "Rakugani" = Rokugani, "rules" = rolls):

> Shizu has commissioned a shrine to the hermit Shoda. In this group, the hermit Shoda died during the collection of the bounty. And there was much contention over this, and as a result, the current acting county magistrate of Ubame County has agreed to pay to fund a forest shrine to Shoda in the place in the forest where the hermit lived and where he taught his disciples.
>
> I have basically no idea what a forest shrine costs. And so I would like for you to help me figure that out. But more than that, I think it would be kind of fun to put together a little, like, shrine builder app. We could make this a section of the GM toolkit, and, you know, I could, like, link the player to it, and then there could be different options for [...] the different types of things that are decisions you might make about it. things like what kind of materials are used, or the shape of the shrine, or what kind of altar it has [...] I'm sure that there were kind of different styles that weren't simply a matter of, like, whether someone wanted the good one or the cheap one [...] And to the extent that some of them really were more expensive or considered better, then Shizu does not have commerce and really is not an expert in those things. And so part of what is happening here is that there is a budget, and the character Tadashi is managing it. And he's going to get to keep all of the money that's left over. And he's good at negotiating [...] I basically want Shizu to be able to design the shrine without knowledge of what the different things cost, and then I, as the GM, can have Tadashi make a series of rolls, which will then determine kind of how well he makes out. Which I think will be both a fun little mini-game, but also an interesting reflection of how Rokugani budgeting works.
>
> Now, Tadashi [...] has done a single commerce negotiation already for the overall budget of the shrine. And he won this negotiation handily by exceeding his opponent's contested commerce roll by more than 10. So I assume that given the circumstances, this will be a fairly nice forest shrine, though it is remote, so that does, you know, kind of cap the type of building it is. [...] I think the intention is that this is the kind of shrine that is, like, unstaffed. Like, nobody lives there. [...] this is a place where there would be a donation box that visitors could drop money into. But other than Shoda's disciples coming to occasionally sweep the shrine, clean it, collect the donations, etc., then [...] there wouldn't be anyone there most of the time.

Characters: Shizu = Tsuruchi Shizukanaken (the player designing); Tadashi = Asako Tadashi (has Commerce, manages the budget, keeps the remainder).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The player designs the shrine without seeing prices (Priority: P1)

Shizu's player opens a link the GM sent and walks through the decisions that go into a small, remote, unstaffed shrine: the form of the sanctuary, its roof, its timber and finish, the gate, the guardians, the lanterns, the water basin, the offering box, the sacred object housed inside, the consecration, and so on. Each choice explains what it is, what it looks like, and what it says about the person enshrined, so a player with no knowledge of Shinto architecture can choose meaningfully. Nothing on the page reveals what anything costs. When finished, the player has a link that reproduces exactly this design, and sends it to the GM.

**Why this priority**: It is the half of the mini-game the player touches, and the half that needs the most content. Without it there is nothing to price.

**Independent Test**: Open the builder logged out (or as a player), make a choice in every category, copy the share link, open it in a fresh browser: the same design appears. Search the page source for any cost figure, price word or contract total: none present.

**Acceptance Scenarios**:

1. **Given** a visitor who is not the GM, **When** they open the builder, **Then** they see every decision category with its options, descriptions and a sensible default selected, and no cost information anywhere in the page (visible or in the source).
2. **Given** a design in progress, **When** the player changes a choice, **Then** the share link updates to encode that choice, and opening the link elsewhere restores the full design including the shrine name (FR-017).
3. **Given** a choice whose option makes another category moot (for example, no sanctuary building at all makes the roof choice meaningless), **When** the player selects it, **Then** the moot category is visibly marked as not applying and contributes nothing to the design.

---

### User Story 2 - The GM sees what the design costs against the budget (Priority: P1)

The GM opens the same link while logged in as GM. Alongside the player's design they see a cost breakdown: each chosen element's fair price, grouped into the contracts a builder would actually let (carpentry, roofing, stonework, metal fittings, finishing and carving, rites, porterage), the total fair price, and the magistrate's budget, with the difference.

**Why this priority**: It answers the GM's first question ("what does a forest shrine cost?") and is what the negotiation acts on.

**Independent Test**: Open a shared design as GM: the breakdown sums correctly, every chosen option with a cost appears in exactly one contract, and changing the remoteness setting changes the heavy-material lines and nothing else.

**Acceptance Scenarios**:

1. **Given** a shared design, **When** the GM opens it, **Then** they see per-contract subtotals, a fair-price total, the budget, and the budget minus the fair-price total.
2. **Given** the GM changes the budget or the remoteness setting, **When** the page updates, **Then** totals recompute and the GM's settings survive a reload of the GM's own link.

---

### User Story 3 - Tadashi negotiates each contract and the GM sees what he keeps (Priority: P2)

For each contract the GM enters Tadashi's Commerce roll (and, when a contractor contests it, that contractor's roll). The panel shows what each contract actually costs after the negotiation, the total actually paid, and what Tadashi keeps: the budget minus what was paid. If the design costs more than the budget even after negotiation, the panel says so and by how much.

**Why this priority**: It is the mini-game itself, but it only means anything once Stories 1 and 2 exist.

**Independent Test**: Enter rolls for every contract; check each negotiated price against the formula, and check that "Tadashi keeps" equals budget minus the sum of negotiated prices.

**Acceptance Scenarios**:

1. **Given** a contract with no roll entered, **When** the GM views the panel, **Then** that contract is shown at its fair price and marked as not yet negotiated.
2. **Given** Tadashi's roll beats the contract's baseline by X, **When** it is entered, **Then** that contract's price drops by X percent of its fair price (the existing gift-buying rule's shape: X = roll minus 25 by default, minimum 0).
3. **Given** the negotiated total exceeds the budget, **When** the panel renders, **Then** it shows the shortfall instead of a remainder.

### Edge Cases

- A share link from an older version of the option catalog names an option that no longer exists: that category falls back to its default and the page says one choice could not be restored.
- A malformed or hand-edited link (unknown keys, absurd roll values, text too long): ignored or clamped, never an error page.
- A non-GM tries to reach GM figures by adding parameters to the URL: they see the player view, with no costs.
- A roll entered without a contract applying (the category is moot): it has no effect.
- Every cost category set to its most expensive option: totals still render; the shortfall is shown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The toolkit MUST have a "Shrines" section reachable from its navigation, containing the shrine builder.
- **FR-002**: The builder MUST present decision categories covering at least: the form of the sanctuary (including forms with no conventional building), its size, a worship hall, roof covering, timber, surface finish, carving, gate (form and material), guardian statues, lanterns, water basin, offering box and bell, the altar or offering stand where offerings are set before the sanctuary (its own category, separate from the sacred object), the sacred object housed in the sanctuary, enclosure, approach path, name plaque, and the consecration rite.
- **FR-002a**: The option catalog MUST be limited to a small, remote, unstaffed shrine: no option may add living quarters, lodging, a priest's office, or other features that assume resident or overnight staff, and the sizes and structures offered MUST be ones a remote forest site could plausibly hold. Remoteness limits which options are offered, not only what they cost (FR-010).
- **FR-003**: Where the historical record shows a thing was done in genuinely different FORMS (not merely better and worse versions), the builder MUST offer those forms as options, each described by what it is, how it looks and what it signals; it MUST NOT reduce such a category to a cheap/expensive pair.
- **FR-004**: Every option MUST carry a player-facing description that a player unfamiliar with Shinto architecture can choose from. Player-facing text MUST NOT state or imply price (no figures, no "cheap", "costly", "luxurious", "budget").
- **FR-005**: The builder MUST offer free-text fields for the shrine's name, the person enshrined, and notes on the sacred object and any inscription.
- **FR-006**: The complete design MUST be encoded in the page's link, so the link alone reproduces it; the page MUST offer a way to copy that link.
- **FR-007**: For any viewer who is not logged in as GM, the page (including its source and any data it loads) MUST contain no cost, price, contract or budget information.
- **FR-008**: For the GM, the page MUST show each chosen option's fair price, grouped into contracts, with per-contract subtotals, the total, the budget, and the difference.
- **FR-009**: Every option's fair price MUST be grounded in the historical research and the reasoning recorded where the prices live (the project's "record the why" rule), including the conversion from historical currency to koku.
- **FR-010**: Heavy materials carried to a remote site MUST bear a porterage cost governed by a GM-adjustable remoteness setting; changing it MUST change only porterage.
- **FR-011**: The GM MUST be able to set the budget; the page MUST suggest a default budget consistent with Tadashi's already-won negotiation (a fairly nice forest shrine) and state how it was derived.
- **FR-012**: For each contract the GM MUST be able to enter Tadashi's Commerce roll and a baseline (default 25; the GM may instead enter a contractor's contested roll as the baseline). Savings on that contract MUST be max(0, roll minus baseline) percent of its fair price.
- **FR-013**: The GM view MUST show the negotiated price per contract, the total paid, and what Tadashi keeps (budget minus total paid), or the shortfall if the total paid exceeds the budget.
- **FR-014**: The GM's settings (budget, remoteness, rolls, baselines) MUST be reproducible from the GM's own link, separate from the player's design so that sharing the player link never carries GM figures.
- **FR-015**: Choices that make another category moot MUST mark it as not applying and exclude it from the design and the costs.
- **FR-016**: The research behind the options and prices MUST be written down in the section's own documentation, including the answer to whether unstaffed shrines were historically real.

### Key Entities

- **Category**: one decision (e.g. roof covering); has a label, a player-facing explanation, a default option, and optionally a rule for when it does not apply.
- **Option**: one choice within a category; has a label, a player-facing description, and (GM-only) a fair price, the contract it belongs to, and whether it is heavy (bears porterage).
- **Contract**: a trade a builder would let (carpentry, roofing, stonework, metal fittings, finishing and carving, rites, porterage); the unit Tadashi negotiates.
- **Design**: the player's selections plus free text; lives entirely in the share link.
- **Negotiation**: the GM's budget, remoteness setting, and per-contract rolls and baselines; lives in the GM's link.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A player can make a choice in every category and copy the share link in under ten minutes without outside help.
- **SC-002**: Zero cost figures or price words appear in the player view's source for any design (verified automatically).
- **SC-003**: Opening a share link reproduces 100% of the selections and the shrine name (FR-017).
- **SC-004**: At least two thirds of the categories offer options that differ in form or meaning, not only in quality.
- **SC-005**: For any design and any rolls, the GM view's totals match a hand calculation from the documented prices and formula.
- **SC-006**: The page passes the project's layout audit with zero issues at GM, tablet and mobile widths.

## Assumptions

- The page is reachable without logging in, like the rest of the toolkit's catalog pages, so the GM can simply send the player a link; the GM's figures depend on the GM being logged in.
- There is no server-side storage: designs live in links. The fly.io app scales to zero and the toolkit has no database.
- The catalog serves any small unstaffed shrine, not only Shoda's; the shrine's name is the only free-text field, pre-filled for Shoda's shrine (FR-017), and option text may refer to "the hermit" since Shoda's is the first use.
- Historical currency converts to koku at roughly 1 ryo = 1 koku, since both are anchored to a koku of rice and the Edo rice price hovered near one ryo per koku; this is recorded with the prices.
- The negotiation formula borrows the shape of the existing rule for buying gifts (Culture skill: spend X percent less, X = roll minus 25), since Commerce itself has no pricing formula. The GM can override any baseline.
- Recording the campaign facts (Shoda's death, the Ubame County magistrate funding the shrine) in `l7r.md` or Obsidian Portal is NOT part of this feature.

## Out of Scope

- Saving designs on the server, listing past designs, or multiple shrines per page.
- Pictures or diagrams of the shrine.
- Writing anything to Obsidian Portal or `l7r.md`.

## Amendment 1 (GM message 2, 2026-10-17)

The GM reviewed the deployed page. These requirements supersede the ones they name.

- **FR-017** (supersedes FR-005): there is exactly ONE free-text field, the shrine's name, which
  merges the old "enshrined" and "name" fields. It is pre-filled with a name made for Shoda's
  shrine and stays editable. There is no field for notes on the sacred object and none for an
  inscription or story: the page never prompts the player to write something.
- **FR-018**: the builder is a step-by-step wizard, one decision per page, with a way back and
  forward and a final page holding the summary and the share link. Steps for categories that do
  not apply are skipped. The share link still reproduces the whole design.
- **FR-019** (amends FR-003): no option may be another option plus more (no "X" beside "X with
  Y"), and no category may be a choice between a lesser and a greater version of the same thing.
  The sanctuary-size category is removed for this reason (the sanctuary is one small bay, the size
  a remote site holds), and FR-002's "its size" is struck.
- **FR-020**: no option is presented as an absence ("None", "No gate", "Nothing", "No basin").
  Each such option is a positive form a real forest shrine has, described as what it is: the
  forest itself guards the shrine; a clearing lets sun and moon light the path; visitors purify
  themselves in the stream as the hermit did. Categories are named for what is chosen ("Ornament"
  / the working of beams and transoms, not "Carving"), and prompts ask "what" or "how" ("What
  guards the shrine?", "How is the path lit?"), never "is there a ...?".
- **FR-021**: no option text frames itself as the default or the norm ("the usual", "the
  standard", "ordinary"). Where an option's text says it is the usual or standard choice, it MUST
  be reworded to "one of the most common ..." (or the same idea in the same form), not deleted:
  the commonness is kept, only the default framing goes.

## Amendment 2 (GM message 3, 2026-10-17)

- **FR-022** (amends FR-017): the pre-filled shrine name is "The memorial hermitage of Shoda the
  Fox-forest Guardian".
- **FR-023**: on every step the options appear in a random order, drawn afresh each time a step is
  shown, including when the player returns to a step with Back, so placement biases no choice.
- **FR-024**: the browser's Back button steps back through the wizard exactly as the wizard's own
  Back button does.
- **FR-025**: the open-to-the-sky form (sacred tree or rock) has at least one decision of its own
  that no other form shows. Two are provided: what the kami dwells in (a great tree, a rock seat,
  a standing stone, the whole grove) and how the ground before it is laid (white gravel, moss,
  four green bamboo with a rope, a ring of river stones). They apply only to that form.
- **FR-026**: every option ends with one sentence saying what makes it good to choose - what it
  suits, the feeling it evokes, how it moves visitors - EXCEPT an option described as "one of the
  most common", which gets no such sentence.

## Review history

- **Round 1 - CHANGES REQUIRED** (2026-10-17, `spec-fidelity`, Mode 2, against `gm-request.md`).
  (1) The GM named "what kind of altar it has" and FR-002 had no altar category: added, separate
  from the sacred object. (2) "It is remote, so that does... cap the type of building" and "that is
  the type of shrine that we are talking about" lived only in prose: added FR-002a, which scopes the
  catalog (no living quarters or lodging, sizes a remote site can hold) so remoteness limits options
  and not only price.
- **Round 2 - FAITHFUL** (2026-10-17). Both changes confirmed; FR-002a's "lodging"/"overnight
  staff" judged to follow from "nobody lives there", and the worship hall judged consistent with it.
- **Round 3 (amendment 1, message 2) - CHANGES REQUIRED** (2026-10-17). (1) FR-021 made the
  "one of the most common" rewording optional where the GM required it: now MUST. (2) User Story 1
  scenario 2, SC-003 and an Assumption still described the removed free-text fields: amended to the
  single shrine name.
- **Round 4 (amendment 1) - FAITHFUL** (2026-10-17). Both changes confirmed; "option text may refer
  to the hermit" judged to follow from the GM's own stream example.
- **Round 5 (amendment 2, message 3) - CHANGES REQUIRED** (2026-10-17). (1) FR-023 "each time the
  page is loaded" could mean a full reload only: now each time a step is shown. (2) FR-024's
  parenthetical made the browser the reference too, licensing a change to the wizard's Back: struck.
- **Round 6 (amendment 2) - FAITHFUL** (2026-10-17). Both changes confirmed.
