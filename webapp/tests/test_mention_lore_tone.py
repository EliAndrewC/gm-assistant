"""The tone rules for the lore corpus - only the ones a test may legitimately hold.

WHY THIS FILE EXISTS. The GM read the first pass of feature 205 and said the
facts were right but the jokes were not there: *"just saying 'Ugh' doesn't
really do the trick"*, and *"the idea that there should be something funny in
every response is maybe not quite there."* An independent audit measured it -
6.1% of 1,030 lines cleared the bar - and named the recurring failures. The
corpus was rewritten; what is below keeps the named traps from returning.

**WHO JUDGES TONE: THE SUBAGENT AUDIT, NOT THIS FILE.** The GM answered that
question himself, twice, and it is the reason this file is as small as it is:

    *"You could dispatch the evaluation of whether your existing responses are
    good enough to a subagent check, which is probably a good way to go since
    that separates validation and verification from the actual implementation,
    which is a good general practice whether we're talking about coding or
    creative writing."*

    *"when you are done with your next editing pass, you should run the same
    subagent check on what you have written just to make sure that it actually
    does pass muster."*

So the project's standing rule that a guideline living only in prose is not a
rule does NOT license a test here. That rule exists because nobody remembers
prose; the GM specified who does the remembering, and it is not pytest.

WHAT A TEST MAY HOLD, and the line that decides it: **a BAN, never a
THRESHOLD.** The four checks below each forbid a SHAPE with no defensible use -
a mood-token opener, the `And this is` caption, the `Ask me about` signpost, a
reply reused verbatim. Nothing is lost by never writing them, so none of them
can fire on writing the GM would have liked, and no number had to be invented,
because the only value a ban takes is zero.

A THRESHOLD is the opposite, and one was tried and removed. A ceiling on the
trailing self-referential clause (`, and I ...`) was added here, capped at two
per category, on the strength of a second audit naming that construction as
"the new 'And this is...'". An independent adjudication rejected it and was
right on three counts, recorded so it is not rebuilt:

  - **The GM never asked for a number.** He asked for "a good mix". How much of
    one construction is too much is a density judgment, and density judgment is
    exactly what he assigned to the subagent. A threshold is a session's private
    answer to that question wearing a gate's clothing.
  - **It had no headroom.** 30 of 103 categories sat exactly at the cap. The
    next author writing one good line with a trailing clause into any of them
    would have hit a red gate on an aesthetic ruling the GM never made - and a
    guard that fires on correct work teaches a session to bypass every guard.
  - **It was orthogonal to the thing it claimed to protect.** An author could
    satisfy it by moving the clause to the front of the sentence and leaving ten
    identical woe-is-me lines behind, and could fail it while writing a genuine
    three-register mix.

The trailing clause is still a real defect. It lives in `lore/CLAUDE.md` with
the other named traps, where the audit will keep catching it.
"""

from __future__ import annotations

import re

from l7r.mention.lore import GM

#: HIM, specifically - first person singular, or the other bot. Deliberately
#: excludes `we|us|our`, which match Rokugan's own voice ("gave us the Yasuki
#: Taka system") rather than his.
SELF_REFERENCE = re.compile(r'\b(I|me|my|myself)\b|character sheet', re.IGNORECASE)

#: "Topic. Fine." - a mood bolted to the front of an encyclopedia entry. The GM
#: named this one directly; the line he was quoting had two of them and was
#: still flat. Widened to its obvious siblings on the audit's authority.
BARE_TOKEN_OPENER = re.compile(r'^(Ugh|Fine|Right|Wonderful|Yes|Sure|Okay)\.')

#: The formula that opened 97 of 103 second captions in the first pass.
CAPTION_FORMULA = 'And this is'

#: A signpost where the punchline goes. A line may still say "ask" - what it may
#: not do is OPEN by redirecting instead of landing.
SIGNPOST_OPENER = 'Ask me about'

#: The one number here, and it is a presence check rather than an apportionment.
#: THE GM SET NO NUMBER. What his words entail is only this: register 1 is
#: definitionally about him, so a category where he appears in NONE of its ten
#: replies contains no register 1 and therefore is not a mix. The audit measured
#: 35 of 103 categories at zero first-person words, so the defect is real. One
#: is the largest floor that follows from what he actually said - he was
#: explicit that a line "can just be humorous observations about the source
#: material itself", so any floor above one starts forbidding the register he
#: wrote that sentence to permit. Whether the mix is GOOD is the audit's call.
SELF_REFERENCE_FLOOR = 1


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


def test_no_category_leaves_him_out_entirely() -> None:
    """Not "enough" self-reference - ANY. See SELF_REFERENCE_FLOOR for why one.

    A category with ten replies and no first-person word in any of them has no
    register 1 in it at all, which cannot be a mix of three registers whatever
    else is true of it. That much follows from the GM's own words. How the three
    are balanced above that line is the subagent audit's judgment, not this
    file's.
    """
    absent = {
        topic: sum(1 for reply in pool if SELF_REFERENCE.search(reply))
        for topic, pool in GM.items()
        if sum(1 for reply in pool if SELF_REFERENCE.search(reply)) < SELF_REFERENCE_FLOOR
    }
    assert not absent, (
        f'ten straight lines of encyclopedia with nobody speaking them - no register 1 '
        f'is present at all: {absent}'
    )


#: Words too common to carry a joke. Dropped before shingling, which is the whole
#: reason this guard can exist - see below.
_STOPWORD_TEXT = (
    'a an the of to in and or is are was were be been it its that this those these for '
    'with on at by as i me my he she they them his her their you your not no but so '
    'which who whom what when where how all any from into over under than '
    'then there here have has had do does did will would can could '
    # NUMBERS. A pool legitimately repeats its own population figure - `akodo_toturi`
    # says "five hundred thousand samurai" in two lines on purpose. Without these the
    # guard fires on that, which is a guard firing on correct work.
    'one two three four five six seven eight nine ten eleven twelve fifteen twenty '
    'thirty forty fifty sixty seventy eighty ninety hundred thousand million percent'
)
_STOPWORDS = frozenset(_STOPWORD_TEXT.split())

#: Content words in a row that two replies IN THE SAME POOL may not share, compared
#: over the OPENING and CLOSING sentence of each - the two places a joke sits.
#:
#: It was closing-sentence-only at first, and a scoped audit caught that scoping
#: certifying an incomplete repair: two verbatim duplicates (`jikoju#3`/`#5` and
#: `hidden_way#5`/`#7`) shared a twenty-word OPENING sentence and sailed through
#: green. A guard that passes over the very defect its commit was written to fix is
#: worse than no guard, because it is trusted.
#:
#: Window measured rather than chosen: at four content words, five pairs, all five
#: genuine. At five, it misses `the_nameless_one#3`/`#8`, which is a real duplicate.
POOL_ECHO_WINDOW = 4


def _joke_positions(reply: str) -> list[str]:
    """The opening and closing sentence - where a punchline actually lands."""
    body = re.sub(r'https?://\S+', '', reply).strip()
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', body) if s]
    if not sentences:
        return []
    return [sentences[0]] if len(sentences) == 1 else [sentences[0], sentences[-1]]


def _content_words(sentence: str) -> list[str]:
    return [w for w in re.findall(r"[a-z']+", sentence.lower()) if w not in _STOPWORDS]


def test_no_pool_tells_the_same_joke_twice() -> None:
    """The defect that survived three passes and grew in every one of them.

    A near-duplicate guard over the WHOLE corpus was built, measured and dropped:
    it fired on facts two categories deliberately share, and no mechanism
    separates a repeated fact from a repeated joke. That reasoning is correct
    and it does not apply here, which is the insight this guard rests on:
    **inside a single ten-reply pool, a repeated punchline is never a
    legitimately shared fact.** The scope IS the discriminator.

    It is narrow on purpose. It catches the severe subclass - a punchline lifted
    onto a neighbor, which is how three of these were introduced, one of them
    verbatim - and it does not pretend to catch every echo. A guard that fires
    only on things with no defensible use is worth more than a broad one that
    argues with the author.
    """
    echoes: list[str] = []
    for topic, pool in GM.items():
        seen: dict[tuple[str, ...], int] = {}
        for i, reply in enumerate(pool):
            for sentence in _joke_positions(reply):
                words = _content_words(sentence)
                for j in range(len(words) - POOL_ECHO_WINDOW + 1):
                    gram = tuple(words[j : j + POOL_ECHO_WINDOW])
                    if seen.get(gram, i) != i:
                        echoes.append(f'{topic}#{seen[gram]} ~ #{i}: {" ".join(gram)!r}')
                    seen.setdefault(gram, i)
    assert not echoes, f'the same punchline twice in one ten-reply pool: {sorted(set(echoes))}'


#: A reply that says "that sentence" / "that word" IN ITS OPENING SENTENCE is
#: pointing at text it has not shown you. There is nothing earlier in the reply
#: for it to mean, and the sibling it does mean will not be delivered with it.
DANGLING_META_REFERENCE = re.compile(r'\bthat (sentence|word|phrase|clause|line)\b', re.IGNORECASE)


def test_no_reply_points_at_text_it_has_not_shown_you() -> None:
    """The one defect this session shipped TWICE, a commit apart.

    `benten#4` quoted "Probably right" after the same pass deleted that phrase
    from its sibling. `moto_language#5` said "Usually is doing the work in that
    sentence" after the same pass deleted the sentence. Both were caught by an
    audit, two commits and forty minutes later; both were committed by an author
    who had just written the rule against them into `lore/CLAUDE.md` in prose.

    A BROADER rule was proposed and measured first: every quoted span must occur
    elsewhere in its pool. It is not viable - 24 hits, and every one is correct
    writing, because a quoted span is normally a COINAGE rather than a
    back-reference. `castes#5` quotes "inhabitants" to name the right word,
    `ashigaru#8` quotes the record's euphemism "prepared", `vows_and_oaths#3`
    quotes the text of an oath. Nothing distinguishes those from a dangling
    quote by the quotation marks alone, and a guard firing on 24 good lines
    would be worse than none.

    What IS decidable is POSITION. Both real defects put the meta-reference in
    the opening sentence, where the reply cannot yet have shown you anything.
    The correct look-alikes put it in a later sentence, pointing back at their
    own first: `the_moto#7` ("...bringing back the old ways. THAT PHRASE ought
    to worry Rites") and `ministry_of_rites#6` ("...never formally tested. I
    have written THAT SENTENCE four times"). Both stay quiet, as they must.

    Verified against history rather than asserted: run over `gm_moto.py` at
    `add0dd24` and `gm_religion.py` at `9475cc11` - the exact commits that
    shipped them - this fires on each, once.
    """
    dangling: list[str] = []
    for topic, i, reply in _all_replies():
        opening = _joke_positions(reply)
        if opening and DANGLING_META_REFERENCE.search(opening[0]):
            dangling.append(f'{topic}#{i}: {opening[0]}')
    assert not dangling, (
        f'a reply pointing at text the player was never shown - the sibling it means '
        f'ships separately or not at all: {dangling}'
    )
