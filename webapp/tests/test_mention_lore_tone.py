"""The tone rules for the lore corpus, as far as tone can be counted.

WHY THIS FILE EXISTS. The GM read the first pass of feature 205 and said the
facts were right but the jokes were not there: *"just saying 'Ugh' doesn't
really do the trick"*, and *"the idea that there should be something funny in
every response is maybe not quite there."* An independent audit then measured
it - 6.1% of 1,030 lines cleared the bar - and named the recurring failures
precisely. The corpus was rewritten; these tests keep it rewritten.

WHAT IS ACTUALLY BEING TESTED. Not whether a line is funny. That is a judgment
call and `lore/CLAUDE.md` says so out loud. What IS countable is the audit's
list of failure SHAPES, each of which is a form the corpus fell into dozens of
times, and each of which the GM either named himself or would recognize:

  - the bare acknowledgment token ("Topic. Fine." then straight facts),
  - the "And this is..." caption, which opened 97 of 103 second captions,
  - the "Ask me about X" signpost, which closed a third of all categories,
  - a line reused verbatim in two places, which thins an already small stock.

And one positive floor: HE HAS TO BE IN THE POOL. The GM allows humor that is
purely judgment of the source material - his worked example is the Phoenix
line, which costs the assistant nothing - so this is deliberately a per-CATEGORY
floor rather than a per-line rule. Three of ten is the standard, not the
current number: with ten replies and three registers wanted in a mix, a
category where he appears fewer than three times has stopped being spoken by
anybody. Four categories were below it when the threshold was chosen and were
rewritten to clear it, rather than the threshold being lowered to admit them.
"""

from __future__ import annotations

import re

from l7r.mention.lore import GM

#: First person, or the one other bot - the two ways a line can put him in it.
SELF_REFERENCE = re.compile(r'\b(I|me|my|we|us|our|myself)\b|character sheet', re.IGNORECASE)

#: "Topic. Fine." - a mood bolted to the front of an encyclopedia entry. The GM
#: named this one directly; the line he was quoting had two of them and was
#: still flat.
BARE_TOKEN_OPENER = re.compile(r'^(Ugh|Fine|Right|Wonderful|Yes|Sure|Okay)\.')

#: The formula that opened almost every second caption in the first pass.
CAPTION_FORMULA = 'And this is'

#: A signpost where the punchline goes. A line may still say "ask" - what it may
#: not do is OPEN by redirecting instead of landing.
SIGNPOST_OPENER = 'Ask me about'

#: Per category, out of ten. See the module docstring for why three.
SELF_REFERENCE_FLOOR = 3


def _all_replies() -> list[tuple[str, int, str]]:
    return [(topic, i, reply) for topic, pool in GM.items() for i, reply in enumerate(pool)]


def test_no_reply_opens_with_a_bare_acknowledgment_token() -> None:
    offenders = [
        f'{topic}#{i}' for topic, i, reply in _all_replies() if BARE_TOKEN_OPENER.match(reply)
    ]
    assert not offenders, f'a mood is not a joke; rewrite the opener: {offenders}'


def test_no_caption_uses_the_and_this_is_formula() -> None:
    offenders = [
        f'{topic}#{i}' for topic, i, reply in _all_replies() if reply.startswith(CAPTION_FORMULA)
    ]
    assert not offenders, f'same caption joke {len(offenders)} times: {offenders}'


def test_no_reply_opens_by_signposting_another_question() -> None:
    offenders = [
        f'{topic}#{i}' for topic, i, reply in _all_replies() if reply.startswith(SIGNPOST_OPENER)
    ]
    assert not offenders, f'a redirect is not a punchline: {offenders}'


def test_no_reply_is_reused_anywhere_in_the_corpus() -> None:
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for topic, i, reply in _all_replies():
        where = f'{topic}#{i}'
        if reply in seen:
            duplicates.append(f'{seen[reply]} == {where}')
        seen[reply] = where
    assert not duplicates, f'a joke spent twice is a joke spent once: {duplicates}'


def test_every_category_puts_him_in_it() -> None:
    thin = {
        topic: sum(1 for reply in pool if SELF_REFERENCE.search(reply))
        for topic, pool in GM.items()
        if sum(1 for reply in pool if SELF_REFERENCE.search(reply)) < SELF_REFERENCE_FLOOR
    }
    assert not thin, (
        f'ten straight lines of encyclopedia with nobody speaking them '
        f'(floor is {SELF_REFERENCE_FLOOR} of ten): {thin}'
    )


# A NEAR-DUPLICATE GUARD WAS BUILT, MEASURED AND DELIBERATELY DROPPED.
#
# The re-audit found twelve JOKES still recurring near-verbatim across
# categories after the rewrite - one of them (abbots discovering that things
# portend success once the army is already moving) spent five times - and noted
# that the general rule had not taken because only the specific lines a previous
# audit named were fixed. That is exactly the shape this file exists to catch,
# so a guard was written for it. It does not work, and the two ways of building
# it were measured rather than guessed:
#
#   - Eight-word shingles over the whole reply: 70+ hits, and almost all of them
#     were deliberately shared FACTS, not shared jokes. "Ryoshun guards the
#     entrance to the celestial heavens" is asserted in three categories on
#     purpose; so is "every legionnaire is a samurai". A mechanism cannot tell a
#     fact repeated for a reader who lands in one category from a joke repeated
#     out of authorial habit.
#   - Shingling only the final sentence, where a punchline usually sits: far
#     fewer false positives, but it misses the motivating five-fold case,
#     because in three of those five the joke is mid-reply.
#
# So joke repetition stays with the audit subagent, which is where judgment
# lives. This is recorded rather than silently omitted so the next session does
# not spend the afternoon rebuilding it: the bar to reopen is a mechanism that
# separates a repeated fact from a repeated joke, and neither candidate does.

#: The other half of the floor. The GM asked for a MIX and said the ten replies
#: exist to carry one; a category where he is in nine of ten has replaced the
#: encyclopedia with a single reliable construction, which the re-audit called
#: "the new 'And this is...'". Seven of ten is the standard.
SELF_REFERENCE_CEILING = 7

#: The two categories that are ABOUT him, where saturation is the joke rather
#: than a tic. `merely_an_assistant` is the insult that only lands on the bot
#: whose name contains his subordination; `imperial_families` is sustained
#: ironic deference, which only works if it never breaks. Both were reviewed
#: and kept deliberately - this is a decision, not a backlog.
SATURATION_IS_THE_JOKE = frozenset({'merely_an_assistant', 'imperial_families'})


def test_no_category_is_monotone() -> None:
    saturated = {
        topic: sum(1 for reply in pool if SELF_REFERENCE.search(reply))
        for topic, pool in GM.items()
        if topic not in SATURATION_IS_THE_JOKE
        and sum(1 for reply in pool if SELF_REFERENCE.search(reply)) > SELF_REFERENCE_CEILING
    }
    assert not saturated, (
        f'one construction carrying the whole category - the GM asked for a mix of the '
        f'three registers and said the ten replies are why (ceiling is '
        f'{SELF_REFERENCE_CEILING} of ten): {saturated}'
    )
