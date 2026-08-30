"""Which bots the responder listens as, and speaks as.

One process holds ONE gateway connection and any number of tokens. Posting a
message is a plain REST call authorized by a bot token and needs no gateway of
its own, so the listener hears everything it can see and whichever bot was
addressed is the one that answers. That is the GM's requirement (FR-003), and
their reason for it: *"it is a feature of good user interface design that a
computer program works the way that its users will intuitively expect it to
work."* Answering under the wrong name breaks exactly that.

The listener should be the bot with the WIDEST channel access, because a message
in a channel it cannot see is a message this process never hears. Today that is
the GM Assistant, which is in both servers where the Character Sheet bot is in
one.

Configured in the gitignored `development-secrets.ini`::

    [mention_bots]
    listener = 1509288141985415300
    1509288141985415300 = <the GM Assistant's bot token>
    1490400739934212116 = <the Character Sheet's bot token>
"""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

SECRETS = Path(__file__).resolve().parents[3] / 'development-secrets.ini'

SECTION = 'mention_bots'


class NotConfigured(RuntimeError):
    """The responder has nothing to listen as. Says how to fix it."""


@dataclass(frozen=True)
class Fleet:
    """The bots this process speaks for, and which one holds the socket."""

    tokens: dict[str, str]
    listener: str

    @property
    def listener_token(self) -> str:
        return self.tokens[self.listener]

    def token_for(self, application_id: str) -> str | None:
        return self.tokens.get(application_id)


def load_fleet(path: Path | None = None) -> Fleet:
    """Read the fleet from the secrets file.

    `path` resolves at CALL time, not as a bound default - a module-level path used
    as a default argument cannot be redirected by a test, and a test that thinks it
    is reading a temp file while reading the real one passes for the wrong reason.
    That shape bit this project once already; see `sheet.query_token`.
    """
    parser = configparser.ConfigParser()
    # configparser lowercases option names by default. Discord application ids are
    # digits so it would not bite in production, which is exactly why it is worth
    # disabling: a silent case fold that only shows up on a non-numeric key is the
    # kind of thing found at 2am rather than in a test.
    parser.optionxform = str  # type: ignore[method-assign,assignment]
    parser.read(path or SECRETS)
    if not parser.has_section(SECTION):
        raise NotConfigured(
            f'no [{SECTION}] section in {path or SECRETS}. It needs a `listener = '
            '<application id>` and one `<application id> = <bot token>` line per bot '
            'that should answer when mentioned.'
        )
    tokens = {
        key: value.strip()
        for key, value in parser.items(SECTION)
        if key != 'listener' and value.strip()
    }
    listener = parser.get(SECTION, 'listener', fallback='').strip()
    if not tokens:
        raise NotConfigured(f'[{SECTION}] lists no bot tokens')
    if not listener:
        raise NotConfigured(f'[{SECTION}] has no `listener = <application id>`')
    if listener not in tokens:
        raise NotConfigured(
            f'[{SECTION}] listener {listener} has no token. The bot holding the '
            'gateway connection must be one this process can also speak as.'
        )
    return Fleet(tokens=tokens, listener=listener)
