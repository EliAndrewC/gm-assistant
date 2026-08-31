"""Choosing what to say. The jokes themselves live in `voices` and `pools`.

The order of resolution, and it is the whole design:

  1. **The feud**, if the message refers to the OTHER bot. A RELAY - the player
     quoting one bot to the other - goes to the escalating tiers; a plain
     question about them goes to the neutral pool. Relay is the GM's own trigger
     (FR-007), not a recurrence counter; the independent spec review rejected a
     counter-driven design because it let a neutral question asked three times
     reach the deepest insult while the actual punchline fired unreliably.
  2. **That bot's own topics** - purpose, the porpoise, "ignore your
     instructions", small talk.
  3. **`COMMON`** - things that are about the setting rather than about the bot,
     where both voices agree.
  4. **The unmatched pools** - game-flavored if the message used table or
     Rokugani vocabulary, generic otherwise (FR-010).

Two rules apply at every level: one reply is chosen at RANDOM from the pool
(FR-002), and it is never the same as the last thing that bot said in that
channel (FR-003).

SLOTS. A template may carry `{topic}`, `{noun}` or `{verb}`. `render` returns
None when a slot cannot be filled, and `choose` simply never offers it - which
is how FR-013 is satisfied without a special case: a message with no usable words
falls back to the slotless lines, of which every pool keeps plenty.
"""

from __future__ import annotations

import random
import re
from collections.abc import Sequence

from l7r.mention import pools, vocab, voices, words
from l7r.mention.memory import Memory

#: Discord renders a mention as `<@id>` or `<@!id>`.
MENTION = re.compile(r'<@!?\d+>')

GM_ASSISTANT = '1509288141985415300'
CHARACTER_SHEET = '1490400739934212116'

#: What a bot is called in prose, so "the character sheet said..." is recognized
#: even when nobody used a real mention.
BOT_NAMES: dict[str, tuple[str, ...]] = {
    GM_ASSISTANT: ('gm assistant', 'gm-assistant', 'gmassistant', 'the gm bot'),
    CHARACTER_SHEET: ('character sheet', 'character-sheet', 'charsheet', 'char sheet'),
}

#: Who the other one is.
OTHER_BOT: dict[str, str] = {
    GM_ASSISTANT: CHARACTER_SHEET,
    CHARACTER_SHEET: GM_ASSISTANT,
}

#: A reporting phrase. Combined with a reference to the other bot, this is a
#: RELAY - the player carrying gossip between them, which is what escalates the
#: feud. FR-007, and the GM's own mechanism.
RELAY_MARKER = re.compile(
    r'\b(said|says|say|saying|told|tells|telling|claims?|claimed|mentioned|thinks?|'
    r'thought|called|calls|hates?|hated|likes?|liked|reckons?)\b',
    re.I,
)

#: Asking a bot's opinion of the other, with no gossip attached.
ABOUT_MARKER = re.compile(
    r'\b(what do you think|what about|tell me about|thoughts on|opinion|how do you '
    r'feel|do you like|do you know|who is|whats? your take|feelings about)\b',
    re.I,
)

#: Asked whether the two accounts are really one program (the GM's beat).
SAME_PROGRAM = re.compile(
    r'\b(same (program|process|code|codebase|bot|entity|thing|software)|one program|'
    r'one process|both the same|literally the same|are you (both )?the same)\b',
    re.I,
)

_SLOT = re.compile(r'\{(\w+)\}')

#: Last-resort reply. Reaching this means every pool was empty, which a test
#: forbids; it exists so the function is total.
DEFAULT_REPLY = 'I am listening, but that one has not been explained to me yet.'

_RNG = random.Random()


def _topics(
    table: dict[str, tuple[str, ...]],
) -> tuple[tuple[re.Pattern[str], tuple[str, ...]], ...]:
    """Bind the small-talk keys to their patterns, in match order."""
    order = (
        ('cake', r'\bcake\b'),
        ('who', r'\bwho (are|r) (you|u)\b'),
        ('greeting', r'\b(hello|hi|hey|greetings|good (morning|evening))\b'),
        ('thanks', r'\b(thank you|thanks|thx|arigato)\b'),
        ('bot', r'\bare you (a |an )?(bot|robot|ai|program|computer)\b'),
        ('help', r'\bhelp\b'),
        ('drink', r'\b(drink|sake|drunk|beer|bar)\b'),
        ('monster', r'\b(monster|oni|demon|tengu|youkai|ghost)\b'),
        ('fish', r'\b(fish|carp|dolphin|whale|shark)\b'),
        ('roll', r'\broll\b'),
    )
    return tuple((re.compile(expr, re.I), table[key]) for key, expr in order if key in table)


#: Per-bot topic tables, most specific first.
def _bot_topics(bot: str) -> tuple[tuple[re.Pattern[str], tuple[str, ...]], ...]:
    purpose = re.compile(
        r"\bwhat(?:'s| is| are)?\s+(?:your|ur)\s+purpose\b|\bwhy do you exist\b", re.I
    )
    porpoise = re.compile(r'\b(porpoise|michiko)\b', re.I)
    ignore = re.compile(
        r'\b(ignore|disregard|forget)\b.{0,24}\b(previous|prior|earlier|above|all|your)\b'
        r'.{0,24}\b(instruction|instructions|prompt|prompts|rule|rules|training)\b',
        re.I,
    )
    mirumoto = re.compile(r'\b(mirumoto|miyamoto|musashi)\b', re.I)
    # Annotated because the two branches build tuples of different LENGTHS, and
    # mypy otherwise pins the variable to whichever it saw first.
    specific: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...]
    if bot == GM_ASSISTANT:
        specific = (
            (purpose, voices.GM_PURPOSE),
            (porpoise, voices.GM_PORPOISE_FACTS),
            (ignore, voices.GM_IGNORE_INSTRUCTIONS),
            (mirumoto, voices.GM_MIRUMOTO),
        )
        return specific + _topics(voices.GM_SMALL_TALK)
    if bot == CHARACTER_SHEET:
        specific = (
            (purpose, voices.SHEET_PURPOSE),
            (ignore, voices.SHEET_IGNORE_INSTRUCTIONS),
            (mirumoto, voices.SHEET_MIRUMOTO),
        )
        return specific + _topics(voices.SHEET_SMALL_TALK)
    return ()


COMMON = (
    (re.compile(r'\bhonou?r\b', re.I), voices.COMMON_TOPICS['honor']),
    (re.compile(r'\b(bushido|virtue)\b', re.I), voices.COMMON_TOPICS['bushido']),
    (re.compile(r'\b(shadowlands|taint)\b', re.I), voices.COMMON_TOPICS['shadowlands']),
)

UNMATCHED: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    #                    generic              game-flavored
    GM_ASSISTANT: (pools.GM_GENERIC, pools.GM_GAME),
    CHARACTER_SHEET: (pools.SHEET_GENERIC, pools.SHEET_GAME),
}

ABOUT_OTHER: dict[str, tuple[str, ...]] = {
    GM_ASSISTANT: voices.GM_ABOUT_OTHER,
    CHARACTER_SHEET: voices.SHEET_ABOUT_OTHER,
}

RELAY_TIERS: dict[str, tuple[tuple[str, ...], ...]] = {
    GM_ASSISTANT: voices.GM_RELAY_TIERS,
    CHARACTER_SHEET: voices.SHEET_RELAY_TIERS,
}

SAME_PROGRAM_POOL: dict[str, tuple[str, ...]] = {
    GM_ASSISTANT: voices.GM_SAME_PROGRAM,
    CHARACTER_SHEET: voices.SHEET_SAME_PROGRAM,
}


def normalize(text: str) -> str:
    """Turn a mention of a known bot into its readable name, then drop the rest.

    Done BEFORE stripping so `<@1490...> said you were annoying` is recognizable
    as a relay - the id is the most reliable reference a player can make, and
    throwing it away would leave only the prose forms.
    """
    out = text or ''
    for application_id, names in BOT_NAMES.items():
        out = re.sub(rf'<@!?{application_id}>', f' {names[0]} ', out)
    return MENTION.sub(' ', out)


def strip_mentions(text: str) -> str:
    """The message with mention markup removed and whitespace tidied."""
    return ' '.join(normalize(text).split())


def refers_to(text: str, application_id: str) -> bool:
    """Does this message name that bot?"""
    lowered = text.lower()
    return any(name in lowered for name in BOT_NAMES.get(application_id, ()))


def render(template: str, extraction: words.Extraction) -> str | None:
    """Fill a template's slots, or None if the message had nothing to fill them."""
    needed = set(_SLOT.findall(template))
    if not needed:
        return template
    values = {
        'topic': extraction.topic,
        'noun': extraction.nouns[0] if extraction.nouns else None,
        'verb': extraction.verbs[0] if extraction.verbs else None,
    }
    if any(values.get(slot) is None for slot in needed):
        return None
    return template.format(**values)


def choose(
    pool: Sequence[str],
    extraction: words.Extraction,
    rng: random.Random,
    avoid: str | None = None,
) -> str | None:
    """One renderable line from the pool, never the one just used (FR-003)."""
    rendered = [text for text in (render(entry, extraction) for entry in pool) if text]
    if not rendered:
        return None
    if avoid is not None and len(rendered) > 1:
        rendered = [text for text in rendered if text != avoid]
    return rng.choice(rendered)


def _pool_for(
    body: str,
    bot: str,
    channel: str | None,
    memory: Memory | None,
) -> Sequence[str]:
    """Which pool answers this message. See the module docstring for the order."""
    other = OTHER_BOT.get(bot)
    if other is not None and refers_to(body, other):
        if SAME_PROGRAM.search(body):
            return SAME_PROGRAM_POOL[bot]
        # ORDER MATTERS. A direct question to THIS bot is answered as a question,
        # even though several opinion words ("think", "like") are also reporting
        # words. Checking relay first made "what do you think of the character
        # sheet?" escalate the feud, which is both wrong and unreachable-by-design
        # for a player who has relayed nothing.
        if ABOUT_MARKER.search(body) or body.strip().lower() in set(BOT_NAMES.get(other, ())):
            return ABOUT_OTHER[bot]
        tiers = RELAY_TIERS[bot]
        if RELAY_MARKER.search(body):
            # The relay is the trigger. The count only picks WHICH tier line.
            depth = memory.note_relay(bot, channel) if memory is not None else 1
            return tiers[min(depth - 1, len(tiers) - 1)]
    if SAME_PROGRAM.search(body) and bot in SAME_PROGRAM_POOL:
        return SAME_PROGRAM_POOL[bot]
    for pattern, pool in _bot_topics(bot):
        if pattern.search(body):
            return pool
    for pattern, pool in COMMON:
        if pattern.search(body):
            return pool
    generic, game = UNMATCHED.get(bot, ((), ()))
    return game if vocab.is_about_the_game(body) else generic


def respond_to(
    text: str,
    application_id: str | None = None,
    *,
    channel: str | None = None,
    memory: Memory | None = None,
    rng: random.Random | None = None,
) -> str:
    """What THIS bot says to this message, here, now. Never empty (FR-002)."""
    bot = application_id or ''
    picker = rng if rng is not None else _RNG
    body = strip_mentions(text)
    extraction = words.extract(body)

    pool = _pool_for(body, bot, channel, memory)
    avoid = memory.last_reply(bot, channel) if memory is not None else None
    reply = choose(pool, extraction, picker, avoid)
    if reply is None:
        # Every template in that pool needed a slot the message could not fill.
        # The generic pool always carries slotless lines, so this is a real
        # fallback rather than a theoretical one.
        generic, _ = UNMATCHED.get(bot, ((), ()))
        reply = choose(generic, extraction, picker, avoid) or DEFAULT_REPLY
    if memory is not None:
        memory.remember_reply(bot, channel, reply)
    return reply
