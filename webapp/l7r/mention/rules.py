"""What the bots say when they are addressed.

DATA, not code: adding a joke is an entry in `RULES`, which is what FR-008 asks
for. Patterns are matched against the message with the mention itself stripped
out, so `@L7R GM Assistant what is your purpose?` matches on `what is your
purpose?`.

**Replies are scripted rather than generated, and that was an implementer's
decision taken where the GM's request was silent** - see the Assumptions section
of `specs/203-mention-responder/spec.md`. It costs something real and the GM can
overrule it: a question nobody anticipated gets `DEFAULT_REPLY` rather than an
answer. That is precisely why FR-002 requires a default at all - a page met with
silence reads as broken, while a page met with a shrug reads as a bot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Discord renders a mention as `<@id>` or `<@!id>`. Stripped before matching so a
#: pattern never has to know about the syntax.
MENTION = re.compile(r'<@!?\d+>')


@dataclass(frozen=True)
class Rule:
    """One thing worth answering, and what to say."""

    pattern: re.Pattern[str]
    reply: str


def rule(expression: str, reply: str) -> Rule:
    return Rule(re.compile(expression, re.I), reply)


#: What a bot says when nothing matches. FR-002: a page always gets an answer.
DEFAULT_REPLY = (
    'I keep the tally. Ask me something I have been taught, or roll and I will record it.'
)

#: The rule table. Order matters - the first match wins - so put the specific
#: above the general. Every entry here is a joke the GM can edit, add to or delete
#: without touching a line of code.
RULES: tuple[Rule, ...] = (
    rule(r'\bwhat is your purpose\b', 'I record what you roll. I do not judge it. Much.'),
    rule(r'\bcake\b', 'The cake is a lie.'),
    rule(r'\bwho (are|r) you\b', 'A clerk. The Empire runs on clerks.'),
    rule(r'\b(hello|hi|hey|greetings)\b', 'Well met. Try not to roll badly in front of me.'),
    rule(r'\b(thank you|thanks|arigato)\b', 'It is my duty. Please do not make it a burden.'),
    rule(
        r'\bare you (a )?(bot|robot|ai)\b',
        'I am an instrument of record. Same thing, fewer feelings.',
    ),
    rule(
        r'\bhelp\b',
        'I answer when addressed. The character sheet answers /etiquette and friends.',
    ),
    rule(r'\broll\b', 'Roll on the sheet and I will write it down. That is the arrangement.'),
    rule(r'\bhonou?r\b', 'Honor is what you do when the roll has already failed.'),
    rule(r'\b(bushido|virtue)\b', 'Seven virtues. Most of you manage two on a good night.'),
)


def strip_mentions(text: str) -> str:
    """The message with mention markup removed and whitespace tidied."""
    return MENTION.sub(' ', text or '').strip()


def respond_to(text: str, rules: tuple[Rule, ...] = RULES, default: str = DEFAULT_REPLY) -> str:
    """What to say to this message. Never empty - see FR-002."""
    body = strip_mentions(text)
    for entry in rules:
        if entry.pattern.search(body):
            return entry.reply
    return default
