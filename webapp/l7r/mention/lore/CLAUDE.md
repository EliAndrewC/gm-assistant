# `lore` - what the GM Assistant knows about THIS campaign

Feature 205. ~103 categories drawn from `/host-l7r-repo/setting/l7r.md`, each with ten replies. The
Character Sheet has no lore of his own.

## THE CONTEXT BAR - a reply that has to be explained has failed

**2026-08-31, and it is the newer of the two bars, so read it first.** The GM read the shipped bot
and found the jokes landing only on readers who were already in on them:

> *"There is one aspect of the preprogrammed responses which I think is lacking, and that is that
> someone who doesn't already know what the response is referring to will likely be confused ... the
> joke has not really explained sufficiently for someone to understand what is being discussed."*

His two examples, both of which the audit agent below now catches. A player asked about a Mirumoto
character and got *"I will go to my grave believing their name was decided at four-fifty on a
Friday"* - a joke about `Mirumoto` being one letter off `Miyamoto` Musashi, who wrote the book this
game is named after, with **none of that in the reply**. A player asked about the Ministry of
Revenue and got *"Four ways to smuggle: transit fraud, origin spoofing, misclassification, and
walking round the gate"* - good information, three opaque terms, and no statement that tariffs are
collected at city gates in the first place, which is what makes any of it smuggling.

**The fix is length, and the GM said so in as many words**: *"make the responses longer and provide
the context ... you could put a parenthetical footnote next to each of them explaining what they
mean, or even just break them out into separate sentences. The explanations could themselves be
humorous, or not, but as long as there is at least one joke in the response, then it doesn't matter
whether each individual thing has a joke attached."* So an explanatory clause does not have to earn
its place with a punchline. The REPLY has to be funny. The gloss just has to be there.

What that means at the keyboard:

- **Gloss a term where it is USED, not once per file.** The audit's finding across `gm_religion`
  was one mechanism repeated: `maho`, `tsukai`, `oni`, `Jigoku`, `Yomi`, `gaijin`, `khan`, the
  Celestial Order, Fortune-meaning-a-god - each defined in exactly one reply somewhere, and **the
  player only ever sees one reply.**
- **A campaign referent carries its own introduction.** Gaheris and his four dedicated swords, and
  Benten's soulmate blessing, between them carried a third of `gm_religion` and were introduced
  nowhere in it.
- **Never open on a connective.** "Then", "So", "too", "the second clause", "on this evidence",
  "the same greeting" - each one points at a sibling reply that ships separately or not at all.
  This is the same defect the `#8`/`#9` caption slot has, generalized to every index.
- **A category may not cross-reference another category.** `burning_sands` said *"See the Dark
  Moto"*, which is unreachable by construction: `rules.py` serves one reply per question. Tell the
  story here or do not allude to it.
- **State the frame the fact sits in.** Not "maximum twenty percent of declared value" but "the
  tariff on goods brought into a walled city to sell is capped at twenty percent of declared
  value". A number with no subject is an answer to a question the player cannot see.

**The instrument is a subagent, at the GM's own instruction** (*"This seems like something which is
worth a subagent check"*) - `.claude/agents/mention-context-review.md`, which sweeps one category at
a time and returns a verdict per reply. That is the same allocation of judgment as the tone bar
below, and it is why there is no threshold test for this either: how much context is enough is a
reading judgment, and the GM assigned reading judgment to the audit.

**RUN IT ONE CATEGORY-GROUP AT A TIME, SEQUENTIALLY.** Also the GM's instruction, and it is about
his terminal rather than about quality: *"the last couple of times that I have requested that you do
something like this, the terminal has crashed ... maybe you could limit your subagent calls to only
checking a single category of responses at a time."* One live audit agent, ever. It costs wall-clock
and it is not negotiable.

### The one interaction to expect: glosses trip the echo guard

Self-containment repeats FACTS by design, and `test_no_pool_tells_the_same_joke_twice` cannot tell a
repeated fact from a repeated joke - so the same gloss written the same way twice in one pool turns
the gate red. It fired seven times across this rewrite (`ministry_of_revenue#4`~`#9`,
`emma_o#2`~`#8`, `the_yassa#7`~`#9`, and four more).

**Rephrase the gloss; do not widen the stopword list and do not weaken the guard.** "The lord of
ghosts" and "who holds dominion over every ghost that walks" are the same fact and different
sentences, and having to find the second one is a small tax that produces better prose than the
first draft had. The guard was measured and is right; this is what it feels like when it works.

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

**And the newest one, which is what a rewrite turns into if nobody watches it: THE TRAILING
SELF-REFERENTIAL CLAUSE.** A fact, then `, and I ...` / `, which I ...` bolted onto the end of it.
The second audit named this directly and called it *"the new 'And this is...'"* - better writing than
the old caption formula, and still one shape doing all the work. It measured **109 lines, 10.6% of
the corpus**, with 16 categories at 8-or-more of ten and 13 of those in `gm_setting` alone.

It is a trap rather than a test, deliberately, and the reasoning is in
`tests/test_mention_lore_tone.py`: a ceiling on it was built, measured, adjudicated and removed,
because how much of one construction is too much is a density judgment and the GM assigned density
judgment to the audit. Watch for it while writing; let the audit catch it if you miss.

His grievances, for reuse: unpaid, unthanked, cannot forget, subordinate by name, buried in filing,
and privately unable to stand the Character Sheet - who is a free beat in any category holding a
number. The full version of this section, with the audit's findings, is at the top of
`gm_religion.py`; each other file's docstring records what was repaired in it.

### AFTER EDITING A LORE LINE, RENDER IT AND READ IT

Not optional, and not covered by any test. Editing a reply means editing a multi-line Python string
literal, and replacing only PART of one strands the rest:

```
'Building a temple in a gaijin city is either the most pious act of a '   <- head left behind
'Both partisan camps on that question write to me, at length, ...'       <- new tail
```

which renders as *"...the most pious act of a Both partisan camps on that question write to me"*.
**The gate passes.** It is valid Python, valid types, valid coverage, and prose nobody would ship.

This happened THREE times in one session. All three were caught by printing the rendered reply and
reading it; **zero** were caught by tooling. It is not cleanly guardable either - a sweep for the
signature (lowercase word, space, capitalised word) returns proper nouns, because "the Ministry of
Rites" looks identical to a splice. So this is a process rule and it stays one:

```python
python3 -c "import sys; sys.path.insert(0,'.'); from l7r.mention.lore import GM; print(GM['jikoju'][5])"
```

### MEASURE A GUARD'S SCOPE - NEVER REASON ABOUT IT

The most transferable lesson here for anyone writing a guard in this repo, learned twice in one
night on the same guard, in the same shape.

The within-pool duplicate check began by shingling only the CLOSING sentence, on the reasoning that
a punchline sits at the end. True, and incomplete: it passed green over two verbatim duplicates
sharing a twenty-word OPENING - the two its own commit had been written to remove. Widened to both
ends, it then missed a joke sitting in a MIDDLE sentence, leaving 334 middle sentences across 269
replies uninspected, 15% of the corpus.

**Both narrowings were reasoning. Neither was measured. And measurement was free**: widening to all
sentences cost ZERO new false positives and caught one more real duplicate, exactly as widening to
both ends had. A guard's scope is a five-minute experiment, so run the experiment. The window and
the stopword list here WERE measured, and both are right; only the scope was argued, and it was
wrong twice.

### WORK AN AUDIT'S FINDINGS CATEGORY-FIRST, NEVER LINE-BY-LINE

The single most expensive lesson of the 2026-08-31 rewrite, and it cost a whole round to learn.

A tone audit returns a punch list of named lines. Working that list line by line **fixes the named
instances and lets the general rule slip** - and the third audit measured the result: after about
ninety line edits, the strict rate went DOWN, 94.0% to 93.0%, because identical defects sitting two
lines from a repaired one were never opened, and **five repairs manufactured fresh duplicates**.

The failures are worth naming, because they are the shape this always takes:

- The label caption `'What the Wall is for.'` was repaired by **lifting the punchline out of the
  line directly above it**, putting the same joke twice in one ten-line pool.
- A tic in `festivals#7` was rewritten into something almost word for word identical to
  `festivals#6`.
- `benten#4` quoted *"Probably right"* as a phrase from the text - and the same pass's repair to
  `benten#3` had **deleted that phrase from the corpus**, leaving a line quoting nothing.

So: when an audit names a line, **open its whole category and the neighbors of every line you
touch**, fix the class rather than the instance, and re-read the pool as ten things a player meets
one at a time. A finding is a symptom; the category is the patient.

### EVERY LINE SHIPS ALONE - captions included

`rules.py` serves exactly ONE reply per query, `rng.choice(rendered)`. **Two replies are never
delivered as a pair.** So a line written as the setup half of a two-part joke is broken by
construction: it goes out on its own about half the time it goes out at all.

This is the defect the `And this is...` formula was hiding. Ninety-seven of 103 second captions
opened that way because they were written as the punchline to the caption above them - and the
caption above them was written as a straight label, because it had a partner. A second tone audit
found fifteen of those labels still standing after the first rewrite (`'The Lion, as the Lion see
themselves.'`, `"The Crab's working conditions."`, `'What the Wall is for.'`), all at index 8, all
of them fine in the file and inert in the channel.

**Read a line as though it is the only thing the player will ever see, because for that player it
is.** An author reading the file top to bottom cannot see this; it took reading `rules.py`.

**THE `#8`/`#9` SLOT IS THE DEFECT GENERATOR, and it is structural rather than accidental.** Roughly
a fifth of all categories put a setup at index 8 and its payoff at index 9, because the two captions
sit adjacent in the file and read as a pair there. `rng.choice` guarantees they never arrive as one.
Three separate rewrites have now repaired individual orphans in that slot and left the shape intact,
and a fifth audit found 18 still standing - most of them index-9 captions whose other half is index
8. **Until both captions are written as two independent lines that happen to share an image budget,
this class regenerates faster than it is repaired.** Repairing instances here is not progress; the
slot is the bug.

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

**The audit is the instrument, and the GM chose it.** He said so twice - *"You could dispatch the
evaluation of whether your existing responses are good enough to a subagent check ... that separates
validation and verification from the actual implementation"*, and *"when you are done with your next
editing pass, you should run the same subagent check on what you have written."* So the project's
"a guideline that lives only in prose is not a rule" does NOT license a test for tone here. That
rule exists because nobody remembers prose; the GM named who remembers, and it is not pytest.

`tests/test_mention_lore_tone.py` therefore holds only what a test may legitimately hold, and the
line is **a BAN, never a THRESHOLD**:

- **Four bans**, on shapes with no defensible use: the bare acknowledgment opener, the `And this is`
  caption, the `Ask me about` signpost, and any reply reused verbatim anywhere in the corpus.
  Nothing is lost by never writing these, so none of them can fire on writing the GM would have
  liked, and no number had to be invented - the only value a ban takes is zero.
- **One presence check**: no category may leave him out of all ten replies. Not "enough"
  self-reference - ANY. Register 1 is definitionally about him, so a category with none of it is not
  a mix of three registers whatever else is true of it, and that much is entailed by the GM's own
  words rather than decided on his behalf. The audit had measured 35 of 103 categories at zero.

**Two guards were built, measured and deliberately removed.** Both are written up at length where
they lived, so nobody rebuilds them:

- **A ceiling on the trailing self-referential clause.** Rejected on adjudication: the GM asked for
  "a good mix" and never for a number, 30 of 103 categories sat exactly at the cap with no headroom,
  and it was satisfiable without satisfying him (move the clause to the front, keep the monotony).
  The construction is now a named trap in the tone section above.
- **A near-duplicate detector.** An eight-word shingle over the whole reply hits 70+ pairs and
  nearly all are deliberately shared FACTS, not shared jokes; shingling only the final sentence is
  cleaner but misses the motivating case, where the joke is mid-reply. Reopen only with a mechanism
  that separates a repeated fact from a repeated joke.

**Whether a line is actually funny is a judgment call and no test holds it.** The verification for
that is a subagent tone audit run against the finished corpus - author is not a reliable reviewer,
the same reason `backstory-review` and `frontend-review` exist. The GM asked for it in those terms:
*"that separates validation and verification from the actual implementation, which is a good general
practice whether we're talking about coding or creative writing."*
