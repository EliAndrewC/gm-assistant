# `lore` - what the GM Assistant knows about THIS campaign

Feature 205. ~103 categories drawn from `/host-l7r-repo/setting/l7r.md`, each with ten replies that
are **annoyed first and factual second**. The Character Sheet has no lore of his own.

| file | holds |
|---|---|
| `topics.py` | every pattern, IN RESOLUTION ORDER. The order is the correctness story - read it first. |
| `gm_setting.py` | setting mechanics, the six Ministries, the calendar |
| `gm_religion.py` | vows, temples, Fortunes, the four Gods of Death |
| `gm_moto.py` | the Moto, the Unicorn, the gaijin west |
| `gm_world.py` | villains, metaplot, campaigns and their places |
| `gm_people.py` | significant individuals, relics, swords, geography |
| `gm_clans.py` | the seven clans, houses, the Imperials, the two jokes about him |
| `sheet.py` | the Character Sheet's Rokugan story pool and his Imperial pool |

## Resolution order is the whole design

Four routing rules the GM asked for claim overlapping strings. Without a precedence, each deletes
another:

- **`Moto` is a Unicorn family.** Family-to-clan routing would swallow all fourteen Moto categories.
- **`Kuni` is a Crab family.** It would swallow `kuni_yori` and `kuni_isamu`.
- **`Akodo no Damasu` is name-shaped**, so the named-person dismissal would claim the very house the
  GM asked for by name.
- **`Damasu` alone** is claimed by both the domain (a place) and the house.

Order: **individuals -> rich topics -> Imperial families -> houses -> a person with no category ->
clans.** The symptom of getting it wrong is a category that stops being reachable, which reading the
file will never show you. Tests pin it.

**A house is not a person.** `Akodo no Damasu` is family + house and routes to `damasu`.
`Akodo no Damasu Sei` has a given name and routes to the dismissal. The discriminator is whether a
given name follows. This is the GM's own correction and it is why two tiers exist rather than one.

**Two pattern hazards were closed during implementation**, both of which would have failed silently:

- `\w+ no \w+` for houses matched ordinary English ("there is no way"). The house pattern is now
  derived from the family list.
- A catch-all `[A-Z][a-z]{2,} [A-Z][a-z]{2,}` for the dismissal would have eaten "Good Bot" - and
  the capitals bought nothing, because every pattern is compiled case-insensitively. A person is now
  a family name followed by a given name, with a lookahead keeping "Matsu family" out.

## The two bots

The GM Assistant answers lore. The Character Sheet **never asserts a setting fact** - he praises the
GM Assistant, tells you to @-mention him, and tells a story in which the GM Assistant's knowledge of
*that subject* saved them both. Those stories are set in **Rokugan**; his ordinary unmatched stories
(in `pools.SHEET_GENERIC`) stay set in the **real world**. That contrast is the joke. Do not let the
two pools drift together.

**One exception, and it is the GM's**: `imperial_families` is answered by both, because the joke is
earnest praise against conspicuous discretion. `merely_an_assistant` is the reverse - the GM
Assistant's alone, because the insult only lands on the bot whose name contains his subordination.

## Facts

Lifted at authoring time. The deployed box has no copy of `l7r.md`, exactly as it has no copy of the
rules. A fact revised in the notes will NOT change here; the GM accepted that explicitly, since this
material rarely moves. A test can hold the shape but never the truth.
