# Tasks: Campaign Lore Intents

**Feature**: 205 | **Plan**: [plan.md](plan.md)

## Phase 1 - routing

- [ ] **T001** `lore/topics.py` - every pattern in resolution order (FR-019), with the family->clan
      and sword-name tables.
- [ ] **T002** Wire `rules.py` to consult lore before small talk, and to give the Character Sheet the
      lore-story pool rather than lore facts.

## Phase 2 - the GM Assistant's lore

- [ ] **T003** `gm_setting.py` - clusters A, B, C
- [ ] **T004** `gm_religion.py` - clusters D, E
- [ ] **T005** `gm_moto.py` - cluster F
- [ ] **T006** `gm_world.py` - clusters G, H, I, J, K
- [ ] **T007** `gm_clans.py` - clusters L, M, N, O

## Phase 3 - the Character Sheet

- [ ] **T008** `sheet.py` - ~100 Rokugan stories (FR-010's required shape), the Imperial pool, the
      named-person dismissal.

## Phase 4 - proof

- [ ] **T009** Tests: routing order, no unreachable category, sword names, house vs person, the
      Character Sheet asserting no lore, the ten-reply floor, the image ban.
- [ ] **T010** `make done` green.
- [ ] **T011** Deploy and verify on the box.
