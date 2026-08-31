"""What the bots say when they are addressed.

DATA, not code: adding a joke is an entry in a table, which is what FR-008 asks
for. Patterns are matched against the message with the mention itself stripped
out, so `@L7R GM Assistant what is your purpose?` matches on `what is your
purpose?`.

**Each bot answers in its own voice** (GM 2026-08-31). The Character Sheet is a
clerk that records dice; the GM Assistant is a scribe that remembers what you
did. A question hits that bot's own table first, falls through to `COMMON` for
things neither has an opinion about, and only then reaches a default. Whoever
was addressed is already the one replying - see `bots.py` - so this is the
second half of the same idea: the bot that answers should also sound like
itself.

**Replies are scripted rather than generated, and that was an implementer's
decision taken where the GM's request was silent** - see the Assumptions section
of `specs/203-mention-responder/spec.md`. It costs something real and the GM can
overrule it: a question nobody anticipated gets a default rather than an answer.
That is precisely why FR-002 requires a default at all - a page met with silence
reads as broken, while a page met with a shrug reads as a bot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Discord renders a mention as `<@id>` or `<@!id>`. Stripped before matching so a
#: pattern never has to know about the syntax.
MENTION = re.compile(r'<@!?\d+>')

#: Discord application ids. PUBLIC - they are in every invite URL - unlike the
#: tokens, which live in the gitignored secrets file. See `bots.py` for why that
#: distinction is load-bearing.
GM_ASSISTANT = '1509288141985415300'
CHARACTER_SHEET = '1490400739934212116'

#: A harbor porpoise, for the "what is your purpose?" joke.
#:
#: PUBLIC DOMAIN, and checked rather than assumed (GM 2026-08-31: *"We should only
#: use freely available images, never making use of something not legitimately free
#: for this kind of jokey use."*). This is fig. 1 from the "Porpoise" article in the
#: Encyclopaedia Britannica, 11th edition, vol. 22 (1911), p. 105, engraver credited
#: as "R.E.H." Published 1911, so it is out of copyright everywhere by age rather
#: than by permission someone granted - which is the sturdiest kind of free there
#: is, since it cannot be revoked or relicensed later. Wikimedia Commons records it
#: as `Public domain` with no attribution condition; the credit above is here
#: because saying where a thing came from is right, not because we are compelled.
#:
#: If this ever needs replacing, the bar is the same: public domain by age, or CC0.
#: Do NOT reach for a CC BY image and skip the attribution line - a joke is not a
#: reason to break someone's license.
PORPOISE_IMAGE = (
    'https://upload.wikimedia.org/wikipedia/commons/6/6a/EB1911_Porpoise_-_Phocaena_communis.jpg'
)


@dataclass(frozen=True)
class Rule:
    """One thing worth answering, and what to say."""

    pattern: re.Pattern[str]
    reply: str


def rule(expression: str, reply: str) -> Rule:
    return Rule(re.compile(expression, re.I), reply)


#: What a bot says when nothing matches and it has no default of its own.
DEFAULT_REPLY = 'I am listening, but that one has not been explained to me yet.'

#: Per-bot defaults, so even a shrug is in character.
DEFAULTS: dict[str, str] = {
    GM_ASSISTANT: 'I have written that down without understanding it. That is most of the job.',
    CHARACTER_SHEET: (
        'I keep the tally. Ask me something I have been taught, or roll and I will record it.'
    ),
}

#: The GM Assistant: keeper of the notes. It remembers; it does not roll.
GM_ASSISTANT_RULES: tuple[Rule, ...] = (
    # The joke the GM asked for: it hears "porpoise" and answers accordingly,
    # entirely straight, which is the whole gag. Discord embeds a bare image URL
    # on its own line.
    rule(
        r'\bwhat(\'s| is| are)? (your|ur) purpose\b',
        'Her name is Michiko. She is a harbor porpoise, she is nine years old, and she '
        'is not technically permitted in the Imperial canals. I would take it as a '
        'kindness if you did not raise the matter with the Emerald Magistrates.\n' + PORPOISE_IMAGE,
    ),
    rule(
        r'\bporpoise\b',
        'Michiko is well, thank you for asking. She is the only one of my responsibilities '
        'that has never once argued with a ruling.',
    ),
    rule(
        r'\bwho (are|r) you\b',
        "The GM's assistant. I remember what you said three sessions ago. All of it.",
    ),
    rule(r'\bcake\b', 'There was cake. You were not there. It has been recorded.'),
    rule(
        r'\b(hello|hi|hey|greetings)\b',
        'Welcome. Everything you do from here is going into the record.',
    ),
    rule(r'\b(thank you|thanks|arigato)\b', 'Noted, along with everything else.'),
    rule(
        r'\bare you (a )?(bot|robot|ai)\b',
        'I am a scribe with opinions. The opinions are not in the official record.',
    ),
    rule(
        r'\bhelp\b',
        'Ask the character sheet to roll. Ask me what happened, and to whom, and whether '
        'they deserved it.',
    ),
    rule(
        r'\broll\b',
        "That is the character sheet's department. I only write down what it says.",
    ),
)

#: The Character Sheet: the clerk with the dice. The GM likes this voice, so the
#: line it gives for "what is your purpose" is deliberately left alone.
CHARACTER_SHEET_RULES: tuple[Rule, ...] = (
    rule(
        r'\bwhat(\'s| is| are)? (your|ur) purpose\b',
        'I record what you roll. I do not judge it. Much.',
    ),
    rule(r'\bcake\b', 'The cake is a lie.'),
    rule(r'\bwho (are|r) you\b', 'A clerk. The Empire runs on clerks.'),
    rule(r'\b(hello|hi|hey|greetings)\b', 'Well met. Try not to roll badly in front of me.'),
    rule(r'\b(thank you|thanks|arigato)\b', 'It is my duty. Please do not make it a burden.'),
    rule(
        r'\bare you (a )?(bot|robot|ai)\b',
        'I am an instrument of record. Same thing, fewer feelings.',
    ),
    rule(r'\bhelp\b', 'I answer when addressed. I also answer /etiquette and friends.'),
    rule(r'\broll\b', 'Roll on the sheet and I will write it down. That is the arrangement.'),
)

#: Answered the same way whoever was asked. Keep this small - the point of the
#: split is that the bots do NOT sound alike - and reserve it for things that are
#: about the setting rather than about the bot.
COMMON: tuple[Rule, ...] = (
    rule(r'\bhonou?r\b', 'Honor is what you do when the roll has already failed.'),
    rule(r'\b(bushido|virtue)\b', 'Seven virtues. Most of you manage two on a good night.'),
    rule(
        r'\b(shadowlands|taint)\b',
        'We do not discuss it in open channels. Ask a Crab, and then buy them a drink.',
    ),
)

#: Which table belongs to which bot.
RULES_BY_BOT: dict[str, tuple[Rule, ...]] = {
    GM_ASSISTANT: GM_ASSISTANT_RULES,
    CHARACTER_SHEET: CHARACTER_SHEET_RULES,
}


def strip_mentions(text: str) -> str:
    """The message with mention markup removed and whitespace tidied."""
    return MENTION.sub(' ', text or '').strip()


def rules_for(application_id: str | None) -> tuple[Rule, ...]:
    """That bot's own table, then the shared one. Order is the precedence."""
    return RULES_BY_BOT.get(application_id or '', ()) + COMMON


def default_for(application_id: str | None) -> str:
    return DEFAULTS.get(application_id or '', DEFAULT_REPLY)


def respond_to(text: str, application_id: str | None = None) -> str:
    """What THIS bot says to this message. Never empty - see FR-002.

    An unknown application id still gets the shared table and the shared default,
    so a bot added to the fleet before it has been given a voice answers sensibly
    rather than falling over.
    """
    body = strip_mentions(text)
    for entry in rules_for(application_id):
        if entry.pattern.search(body):
            return entry.reply
    return default_for(application_id)
