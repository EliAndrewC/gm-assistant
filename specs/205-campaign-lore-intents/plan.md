# Implementation Plan: Campaign Lore Intents

**Feature**: 205 | **Spec**: [spec.md](spec.md) | **List**: [candidate-list.md](candidate-list.md)

## Summary

~105 lore categories for the GM Assistant, each ten replies, each annoyed and then factual. The
Character Sheet gets no lore - he gets one pool of ~100 Rokugan-set stories about how the GM
Assistant's knowledge of that very subject saved them both. One exception, the GM's: the Imperial
families, which both bots answer.

## Structure

`webapp/l7r/mention/lore/`, a package because one file at this depth would run past 4,000 lines.

| file | holds |
|---|---|
| `topics.py` | every lore pattern, IN RESOLUTION ORDER (FR-019). Order is the whole correctness story. |
| `gm_setting.py` | clusters A, B, C - setting mechanics, the six Ministries, the calendar |
| `gm_religion.py` | clusters D, E - vows, temples, Fortunes, the four Gods of Death |
| `gm_moto.py` | cluster F - the Moto, the Unicorn, the gaijin |
| `gm_world.py` | clusters G, H, I, J, K - villains, campaigns, people, relics, geography |
| `gm_clans.py` | clusters L, M, N, O - the seven clans, houses, Imperials, being an assistant |
| `sheet.py` | the Rokugan story pool, the Imperial pool, the named-person dismissal |

## The one hard part: resolution order

Four rules claim overlapping strings, and the GM asked for all four. Without an order, each deletes
another:

- `Moto` is a Unicorn FAMILY. Family-to-clan routing would swallow all fourteen Moto categories.
- `Kuni` is a Crab family. It would swallow `kuni_yori` and `kuni_isamu`.
- `Akodo no Damasu` is name-shaped. The dismissal would claim the house the GM asked for by name.
- `Damasu` alone is claimed by both the domain (a place) and the house.

Order, most specific first: **named individuals -> rich specific topics -> Imperial families ->
houses -> clans -> dismissal.** The symptom of getting this wrong is a category that simply stops
being reachable, which no amount of reading the file reveals - so it is pinned by tests
(SC-009), not by care.

## Constitution Check

| Principle | How |
|---|---|
| I | `spec-fidelity` reviewed the spec three rounds against the GM's verbatim words before any code. |
| III | Every reply is data. Adding a fact is an entry. |
| VI | Gate green, then deployed and verified on the box. |
| X | Files split so none passes ~1,000 lines; 100% coverage; the ten-reply floor from 204 applies to every new pool. |
| XIII | No regression: the existing 1,311 tests keep passing. |

## Facts

Lifted from `l7r.md` at authoring time and staged under the session scratchpad by topic. The box has
no copy of the notes, exactly as it has no copy of the rules - so a fact that later changes in the
notes will not change here. The GM accepted this explicitly: *"Those setting notes do not change for
most of the things that we are talking about... if I ever want to make an update, then I can just do
that."*
