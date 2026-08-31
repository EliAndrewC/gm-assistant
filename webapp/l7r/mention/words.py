"""Pull the significant words out of a message, ELIZA-style.

The point is FR-009: a reply that uses the words the player actually typed reads
as though someone was listening, and that effect is most of what made ELIZA work
in 1966 with no model at all.

WHY THIS IS HAND-ROLLED, AND WHAT WAS DECLINED (FR-012, and the GM delegated the
choice: *"either just doing the literal thing that ELIZA did back in the day, or
having some Python module, which doesn't take up much RAM or CPU"*).

  - **spaCy** `en_core_web_sm`: a real tagger, ~12 MB on disk but ~80 MB resident
    once the pipeline loads. The bot is ~18 MB today on a 512 MB Lightsail nano
    that also runs the GM's other services, so this is the whole box's slack
    spent on choosing which noun to put in a joke.
  - **NLTK** averaged perceptron: smaller, but adds a dependency plus a runtime
    data download - a deploy step that can fail on a box nobody is watching.
  - **This**: a stopword list plus suffix and position heuristics. Zero
    dependencies, zero marginal memory, and wrong sometimes - which costs a
    slightly odd joke, the cheapest possible failure.

Swapping in a tagger later means reimplementing `extract` and nothing else; the
rest of the package only ever sees an `Extraction`.

ACCURACY IS NOT THE GOAL. Calling a noun a verb produces a strange sentence in a
joke bot. The things that would actually matter - leaking markup, injecting a
mention, crashing on an emoji - are handled by `clean` and are tested.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Everything Discord might put in a message that must never come back out. A
#: reply is built from these words, so a surviving `<@id>` would be a PING - the
#: exact hazard `allowed_mentions` guards at the other end, closed here too.
_MARKUP = (
    re.compile(r'```.*?```', re.S),  # fenced code
    re.compile(r'`[^`]*`'),  # inline code
    re.compile(r'<a?:\w+:\d+>'),  # custom emoji
    re.compile(r'<[@#&!]?[&!]?\d+>'),  # mentions, channels, roles
    re.compile(r'@(everyone|here)\b', re.I),
    re.compile(r'https?://\S+'),  # links
    re.compile(r'\|\|.*?\|\|', re.S),  # spoilers
)

#: Words that carry no content. Deliberately generous - a false stop costs one
#: candidate, while a false keep puts "the" in a punchline.
STOPWORDS = frozenset(
    [
        'a',
        'about',
        'above',
        'after',
        'again',
        'against',
        'all',
        'am',
        'an',
        'and',
        'any',
        'are',
        'aren',
        'as',
        'at',
        'be',
        'because',
        'been',
        'before',
        'being',
        'below',
        'between',
        'both',
        'but',
        'by',
        'can',
        'cannot',
        'could',
        'couldn',
        'did',
        'didn',
        'do',
        'does',
        'doesn',
        'doing',
        'don',
        'down',
        'during',
        'each',
        'few',
        'for',
        'from',
        'further',
        'had',
        'hadn',
        'has',
        'hasn',
        'have',
        'haven',
        'having',
        'he',
        'her',
        'here',
        'hers',
        'herself',
        'him',
        'himself',
        'his',
        'how',
        'i',
        'if',
        'in',
        'into',
        'is',
        'isn',
        'it',
        'its',
        'itself',
        'just',
        'll',
        'me',
        'might',
        'more',
        'most',
        'must',
        'my',
        'myself',
        'no',
        'nor',
        'not',
        'now',
        'of',
        'off',
        'on',
        'once',
        'only',
        'or',
        'other',
        'ought',
        'our',
        'ours',
        'ourselves',
        'out',
        'over',
        'own',
        're',
        's',
        'same',
        'shan',
        'she',
        'should',
        'shouldn',
        'so',
        'some',
        'such',
        't',
        'than',
        'that',
        'the',
        'their',
        'theirs',
        'them',
        'themselves',
        'then',
        'there',
        'these',
        'they',
        'this',
        'those',
        'through',
        'to',
        'too',
        'under',
        'until',
        'up',
        've',
        'very',
        'was',
        'wasn',
        'we',
        'were',
        'weren',
        'what',
        'when',
        'where',
        'which',
        'while',
        'who',
        'whom',
        'why',
        'will',
        'with',
        'won',
        'would',
        'wouldn',
        'you',
        'your',
        'yours',
        'yourself',
        'yourselves',
        'im',
        'ive',
        'dont',
        'doesnt',
        'cant',
        'wont',
        'isnt',
        'thats',
        'whats',
        'gonna',
        'gotta',
        'kinda',
        'sorta',
        'please',
        'thanks',
        'thank',
        'hey',
        'hi',
        'hello',
        'yeah',
        'yep',
        'nope',
        'ok',
        'okay',
        'lol',
        'lmao',
        'haha',
        'hmm',
        'um',
        'uh',
        'oh',
        'get',
        'got',
        'go',
        'going',
        'went',
        'make',
        'made',
        'made',
        'take',
        'took',
        'come',
        'came',
        'want',
        'wanted',
        'like',
        'liked',
        'know',
        'knew',
        'think',
        'thought',
        'say',
        'said',
        'tell',
        'told',
        'give',
        'gave',
        'one',
        'two',
        'three',
        'really',
        'very',
        'just',
        'guy',
        'guys',
        'thing',
        'things',
        'stuff',
        'someone',
        'something',
        'anyone',
        'anything',
        'everyone',
        'everything',
    ]
)

#: Suffixes that usually mean a verb. `-ing` and `-ed` do most of the work; the
#: rest catch coined words, which players produce constantly.
_VERB_SUFFIXES = ('ing', 'ed', 'ate', 'ify', 'ise', 'ize')

#: Small closed set of very common verbs that no suffix rule would catch. Not a
#: lexicon - just the ones that show up in questions to a bot.
_KNOWN_VERBS = frozenset(
    [
        'run',
        'walk',
        'eat',
        'drink',
        'fight',
        'kill',
        'die',
        'roll',
        'write',
        'read',
        'speak',
        'talk',
        'ask',
        'answer',
        'help',
        'fix',
        'break',
        'build',
        'buy',
        'sell',
        'steal',
        'find',
        'lose',
        'win',
        'draw',
        'cast',
        'pray',
        'bow',
        'kneel',
        'ride',
        'sail',
        'swim',
        'sing',
        'dance',
        'sleep',
        'wake',
        'burn',
        'cut',
        'stab',
        'shoot',
        'hide',
        'seek',
        'guard',
        'serve',
        'rule',
        'judge',
        'punish',
        'forgive',
        'remember',
        'forget',
        'explain',
        'teach',
        'learn',
        'practice',
        'train',
        'hunt',
        'cook',
        'fish',
        'farm',
    ]
)

#: A determiner in front of a word is decent evidence it is a noun.
_DETERMINERS = frozenset(
    [
        'the',
        'a',
        'an',
        'my',
        'your',
        'his',
        'her',
        'their',
        'our',
        'this',
        'that',
        'these',
        'those',
        'some',
        'any',
    ]
)

_TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]*")

#: Nothing longer than this goes into a reply. A 200-character "word" is either an
#: attack or a keyboard sitting under a book.
MAX_WORD = 24


@dataclass(frozen=True)
class Extraction:
    """The content words worth echoing back."""

    nouns: tuple[str, ...]
    verbs: tuple[str, ...]

    @property
    def topic(self) -> str | None:
        """The single best word to build a sentence around."""
        if self.nouns:
            return self.nouns[0]
        if self.verbs:
            return self.verbs[0]
        return None

    def __bool__(self) -> bool:
        return bool(self.nouns or self.verbs)


def clean(text: str) -> str:
    """Strip every piece of Discord markup before anything else looks at it."""
    out = text or ''
    for pattern in _MARKUP:
        out = pattern.sub(' ', out)
    return out


def _looks_like_verb(word: str, previous: str | None) -> bool:
    if word in _KNOWN_VERBS:
        return True
    if previous == 'to':
        return True
    # `-ed`/`-ing` on a short stem is usually a real inflection; on a 3-letter
    # word ("bed", "red") it is usually not.
    return len(word) > 5 and word.endswith(_VERB_SUFFIXES)


def _salience(word: str, position: int, after_determiner: bool) -> tuple[int, int]:
    """Rank candidates. Longer and determiner-led first, earlier as a tiebreak."""
    score = len(word) + (3 if after_determiner else 0)
    return (-score, position)


def extract(text: str, limit: int = 3) -> Extraction:
    """The nouns and verbs worth putting in a reply, best first.

    Returns empty tuples for a message with nothing in it - an emoji, "ok", pure
    punctuation - which is why FR-013 requires templates that need no slots.
    """
    words = [w.lower().strip("'-") for w in _TOKEN.findall(clean(text))]
    nouns: list[tuple[tuple[int, int], str]] = []
    verbs: list[tuple[tuple[int, int], str]] = []
    seen: set[str] = set()

    for index, word in enumerate(words):
        if len(word) < 3 or len(word) > MAX_WORD or word in STOPWORDS or word in seen:
            continue
        seen.add(word)
        previous = words[index - 1] if index else None
        rank = _salience(word, index, previous in _DETERMINERS)
        if _looks_like_verb(word, previous):
            verbs.append((rank, word))
        else:
            nouns.append((rank, word))

    nouns.sort()
    verbs.sort()
    return Extraction(
        nouns=tuple(word for _, word in nouns[:limit]),
        verbs=tuple(word for _, word in verbs[:limit]),
    )
