# Tasks: Bot Personalities

**Feature**: 204-bot-personalities | **Spec**: [spec.md](spec.md)

A task is checked when its artifact exists and was verified. T010 and T011 are the ones that found
real defects.

## Phase 1 - Mechanism

- [x] **T001** `words.py` - the ELIZA-style extractor. Stopwords plus suffix and position
      heuristics; `clean` strips every kind of Discord markup FIRST, because a reply is built out of
      these words and a surviving `<@id>` would be a ping. The two rejected alternatives (spaCy at
      ~80 MB resident, NLTK's tagger plus a runtime data download) are priced in the docstring, per
      the record-the-why rule - the GM delegated this choice and the reasoning should outlive the
      decision. (FR-009, FR-012)
- [x] **T002** `memory.py` - per bot, per channel: the last reply (FR-003) and the relay count
      (FR-007). Bounded `OrderedDict`, in-process, forgetful on redeploy. A database would be a
      bigger commitment than the feature.
- [x] **T003** `vocab.py` - the words that mean "this is about the game". Literal by necessity: the
      deploy payload has neither the rules repository nor the rest of `l7r`, so importing the
      canonical skills would make the bot un-deployable. The derive-don't-maintain rule is kept one
      step removed, by a test that cross-checks against `skills.load_skills()` in the repository.
      (FR-010)
- [x] **T004** `images.py` - every postable URL, what it SHOWS, and the proof it is free. The
      subject matters as much as the license: you cannot write a setup for a picture you have not
      identified. (FR-005, FR-015 through FR-018)
- [x] **T005** `rules.py` - the engine. Four resolution layers, slot rendering that simply does not
      offer a template it cannot fill (which is how FR-013 needs no special case), and a random pick
      that avoids the previous line.

## Phase 2 - Content

- [x] **T006** `voices.py` - purpose, porpoise facts, ignore-instructions, the feud tiers, the
      same-program beat, the Mirumoto grievance, small talk. ~200 lines of material.
- [x] **T007** `pools.py` - the unmatched pools: 103 lines for the GM Assistant, 102 for the
      Character Sheet, split across generic and game-flavored tiers. (SC-002)
- [x] **T008** Images placed on lines WRITTEN to set them up, at ~17% of the GM Assistant's lines
      and 0% of the Character Sheet's. (FR-015, FR-016, FR-017)
- [x] **T009** `responder.py` and `__init__.py` rewired: the reply is computed per bot inside the
      loop, with the channel and the shared `Memory` threaded through.

## Phase 3 - Verification, and what it caught

- [x] **T010** **A smoke test found the feud firing on the wrong input.** *"What do you THINK of the
      character sheet?"* escalated the feud instead of answering the question, because `think` is
      both an opinion word and a reporting word, and the relay check ran first. A player who had
      relayed nothing could reach the deepest insult by asking a neutral question - which is exactly
      the failure the spec review had already rejected once, arriving a second time through a
      different door. Fixed by checking the direct-question pattern first; the reason sits at the
      branch, and `test_a_relay_escalates_and_a_plain_question_does_not` pins both halves.
- [x] **T011** Three test failures on first run: two assertions left stale by the rewrite, and the
      pools genuinely short of the hundred-per-bot bar (80 and 87). The bar was met by writing more
      lines, not by lowering it.
- [x] **T012** `tests/test_mention.py` - 107 tests, no network. Sweeping assertions run over EVERY
      pool by introspection rather than a hand-kept list, so a new pool is covered the moment it
      exists: no empty replies, no unfilled slots, no unvetted image URLs, and no image anywhere in
      a Character Sheet pool.
- [x] **T013** `make done` green: ruff, format, mypy --strict, hook guards, pytest, 100% coverage.
- [x] **T014** Deployed to Lightsail and redeployed after each change.

## Notes for whoever comes next

- **Adding a joke is a data edit.** Pick the pool in `voices.py` or `pools.py`, add a line. The
  sweeping tests will hold it to the rules automatically.
- **Adding an image is not.** It goes through `images.py`, needs its license verified at the source,
  and needs a line written around it. A test rejects any URL that did not come from there.
- **Do not add a probability to the engine.** The one-in-five image rate is a property of the
  writing, deliberately - see `images.py` for why.
