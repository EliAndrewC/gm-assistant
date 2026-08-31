# Tasks: Campaign Lore Intents

**Feature**: 205 | **Plan**: [plan.md](plan.md)

## Phase 1 - routing

- [x] **T001** `lore/topics.py` - every pattern in resolution order (FR-019), with the family->clan
      and sword-name tables.
- [x] **T002** Wire `rules.py` to consult lore before small talk, and to give the Character Sheet the
      lore-story pool rather than lore facts.

## Phase 2 - the GM Assistant's lore

- [x] **T003** `gm_setting.py` - clusters A, B, C
- [x] **T004** `gm_religion.py` - clusters D, E
- [x] **T005** `gm_moto.py` - cluster F
- [x] **T006** `gm_world.py` - clusters G, H, I, J, K
- [x] **T007** `gm_clans.py` - clusters L, M, N, O

## Phase 3 - the Character Sheet

- [x] **T008** `sheet.py` - ~100 Rokugan stories (FR-010's required shape), the Imperial pool, the
      named-person dismissal.

## Phase 4 - proof

- [x] **T009** Tests: routing order, no unreachable category, sword names, house vs person, the
      Character Sheet asserting no lore, the ten-reply floor, the image ban.
- [x] **T010** `make done` green.
- [x] **T011** Deploy and verify on the box.

## Phase 5 - the tone pass (GM, 2026-08-31, after reading Phase 2)

The facts were right and the jokes were not there: *"just saying 'Ugh' doesn't really do the trick
... the idea that there should be something funny in every response is maybe not quite there."*

- [x] **T012** Independent subagent audit of all 1,030 lines. Verdict: **6.1% strict / 8.3%
      generous**, 35 of 103 categories with no first-person word at all, 3 of 206 image captions
      referencing him. The GM's read was correct and if anything generous.
- [x] **T013** Rewrite all six `gm_*.py` files to the restated bar - **three registers, mixed**
      (woe-is-me / judgment of the source / edged observation), the mix itself being the GM's
      instruction and the reason for having ten replies.
- [x] **T014** `tests/test_mention_lore_tone.py` - the countable half of the bar: the four traps
      (bare acknowledgment opener, `And this is` caption, `Ask me about` signpost, any reply reused
      anywhere) plus a floor of three self-referential replies in ten per category. Proven to fire:
      run against `c9a7fd45` in a detached worktree, all five checks go red, 89 of 103 categories
      under the floor.
- [x] **T015** Re-run the same audit against the rewrite. The GM asked for this explicitly, and for
      the reason: *"that separates validation and verification from the actual implementation, which
      is a good general practice whether we're talking about coding or creative writing."*
      **Verdict: 94.0% strict / 95.9% generous**, from 6.1% / 8.3%. No factual damage - it checked
      every load-bearing fact and found all six four-sword sites in step. It returned a punch list
      of ~90 line edits, worked in T017.
- [x] **T017** Work the round-2 punch list. Four defect classes, one of which was not a writing
      problem at all:
      - **15 captions written as the setup half of a diptych.** `rules.py` serves ONE line via
        `rng.choice`, so those shipped alone about half the time. Invisible while reading the file,
        obvious the moment you read the engine. Rule now recorded in `lore/CLAUDE.md`.
      - **21 pure-fact lines**, each the joke-free half of a fact split across a pair - same root
        cause. Facts kept, turns added; `moto_khuyag#3` and `gods_of_death#2` were on the fail list
        precisely BECAUSE they refused to trade the mechanism for a joke, which is the right trade.
      - **13 monotone categories**, almost all in `gm_setting`, leaning on one trailing
        self-referential clause. The audit called it *"the new 'And this is...'"*. Rebalanced, and a
        7-in-10 ceiling test added so it cannot silently return.
      - **12 jokes recurring across categories**, the worst used five times. Reduced to one use.
- [x] **T018** Fix the guard that let three British spellings through a green gate. CLAUDE.md states
      the doubled-`l` rule in prose and enumerates four of its members; `house-style-hooks.sh` only
      implemented the enumeration, so `cruellest` x2 and `duelling` shipped. Twenty doubled-`l` forms
      added, with cases in both directions. **The repair was itself blocked by the guard**: the
      exemption named the two-line wrapper `test-house-style-hooks.sh` and not `test_hooks_cases.py`
      where the cases live, so adding a case tripped the rule the case asserts. That is the project's
      own "check the ESCAPE first, or the guard cannot be repaired through the channel it guards"
      failure, and it is now fixed and pinned.
- [ ] **T019** Round-3 audit of the corrected corpus - full 1,030-line census, not scoped to the ~90
      changed lines, because the mix is a per-CATEGORY property, duplicate collision is corpus-global
      and fact consistency is cross-file. None of the three is visible from a scoped diff.
- [ ] **T020** Redeploy to the box, then push.

## What implementation found that the spec did not

- **Two pattern hazards that would have failed silently.** `\w+ no \w+` for houses matched ordinary
  English ("there is no way"); a catch-all `[A-Z][a-z]{2,} [A-Z][a-z]{2,}` for the dismissal would
  have eaten "Good Bot", and the capitals bought nothing because every pattern is compiled
  case-insensitively. Both are now derived from the family list.
- **PERSON has to outrank HOUSES**, not follow it. `Akodo no Damasu Sei` is a person and
  `Akodo no Damasu` is a house; since the person pattern requires a trailing given name, putting it
  first separates them cleanly. Discovered by a test, not by reading.
- **`Mirumoto` collided with feature 204.** It is a Dragon family AND the GM's designers-were-lazy
  joke. Resolved by giving each bot's SIGNATURE topics precedence over lore. Both remain reachable
  and both are asserted.
- **27 Character Sheet stories referred to him only as "he".** SC-006 requires every reply to NAME
  him, so the pool was regenerated programmatically rather than hand-patched.
