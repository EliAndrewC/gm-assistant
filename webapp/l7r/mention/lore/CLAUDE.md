# `lore` - what the GM Assistant knows about THIS campaign

Feature 205. ~103 categories drawn from `/host-l7r-repo/setting/l7r.md`, each with ten replies. The
Character Sheet has no lore of his own.

## The tone bar - read this before writing a line

The first pass was **annoyed first, factual second**, and the GM read it and said the facts were
right and the jokes were not there: *"just saying 'Ugh' doesn't really do the trick"*, and *"the
idea that there should be something funny in every response is maybe not quite there."* An
independent audit measured it at **6.1% of 1,030 lines** clearing the bar, and 35 of 103 categories
containing no first-person word at all. The whole corpus was rewritten on 2026-08-31.

The bar now: **something funny in every reply**, in one of three registers, MIXED deliberately
across the ten - the mix is itself the GM's instruction, *"part of the reason of having ten
different possible responses per category"*:

1. **Performative woe-is-me.** The fact is not DECORATED with a complaint, it is RE-EXPLAINED
   THROUGH HIS POSITION - he is the second half of the sentence. The GM's worked example: follow
   *"unless he dies or embarrasses somebody"* with *"... like how I'm embarrassed for the both of us
   by this whole conversation."*
2. **Judgment of the source material**, from a point of view, costing him nothing. The GM's own
   exemplar is `gm_religion/shugenja#1` - *"The Phoenix are known for them, which is awkward, given
   that the founder of the Isawa practiced maho."*
3. **Sardonic observation about Rokugan, WITH AN EDGE.** A merely elegant epigram is the near miss
   that feels finished.

The traps, each of which the corpus fell into dozens of times: a bare `Ugh.`/`Fine.` opener (a mood
is not a joke - the line the GM quoted at us already had both); `Ask me about X` as a signpost where
a punchline belongs; the `And this is...` caption formula (97 of 103 second captions); scolding the
player (his comedy runs the other way - he is at the bottom of the ladder and it is one rung); a
flat inventory assertion, which is a receipt rather than a grievance; withholding used instead of a
punchline; and a line reused across categories, which thins an already small stock.

His grievances, for reuse: unpaid, unthanked, cannot forget, subordinate by name, buried in filing,
and privately unable to stand the Character Sheet - who is a free beat in any category holding a
number. The full version of this section, with the audit's findings, is at the top of
`gm_religion.py`; each other file's docstring records what was repaired in it.

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

Several facts are **load-bearing in more than one place** and a turn may go AROUND them but must
never soften them: the Enma / Emma-O distinction (four categories depend on it); the four-sword
mapping - Bloodstorm to Emma-O, Lamentation to Enma, Lightning to King Yan, Retirement to Wei Tin -
asserted in four places that must stay in step; 284 actual domains against 400 as a unit of
accounting; the FIXED third of the tax; the Ministry of Revenue's point-of-sale-not-point-of-transit
rule, on which a Drowned Merchant River plot lever is built; `Akodo no Damasu` being a family and a
house rather than a person; fifteen ranks rather than the published ten; the Candle of Tears being
the candle-HOLDER; and Moto Khuyag's region-locked detector.

## What the tests hold, and what they cannot

`tests/test_mention_lore_tone.py` holds the four traps that can be counted exactly - the bare
acknowledgment opener, the `And this is` caption, the `Ask me about` signpost, and any reply reused
anywhere in the corpus - plus a floor of **three replies in ten** per category carrying a
first-person marker or the other bot. That floor is a proxy, chosen at the standard rather than at
wherever the corpus sat: humor of register 2 needs no self-reference at all, so the rule is
per-CATEGORY, and a category he appears in fewer than three times has stopped being spoken by
anybody. Four categories were below it when it was set and were rewritten to clear it.

**Whether a line is actually funny is a judgment call and no test holds it.** The verification for
that is a subagent tone audit run against the finished corpus - author is not a reliable reviewer,
the same reason `backstory-review` and `frontend-review` exist. The GM asked for it in those terms:
*"that separates validation and verification from the actual implementation, which is a good general
practice whether we're talking about coding or creative writing."*
