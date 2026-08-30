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

Configuration is split by SENSITIVITY, not by convenience. The bot tokens are
credentials and live in the gitignored `development-secrets.ini`::

    [mention_bots]
    1509288141985415300 = <the GM Assistant's bot token>
    1490400739934212116 = <the Character Sheet's bot token>

while which of them listens is a public Discord application id, and lives in the
checked-in `development-defaults.ini`::

    [mention_bots]
    listener = 1509288141985415300
"""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

from configobj import ConfigObj

#: `parents[2]` is `webapp/`, where the secrets live. NOT [3]: the sibling
#: `l7r/repl/rolls/` package sits one directory deeper and uses [3] for the same
#: file, and copying that index landed this on the repo root - a wrong path that
#: every unit test missed, because they all pass an explicit path or monkeypatch
#: this constant. The test below walks the real one.
SECRETS = Path(__file__).resolve().parents[2] / 'development-secrets.ini'

#: The listener's application id lives HERE, not among the secrets. A Discord
#: application id is PUBLIC - it is in every invite URL and is rendered into this
#: app's own OAuth login link - so storing it as a secret value made
#: `test_chargen_security` report, correctly, that a value from the secrets file had
#: appeared in served HTML. The guard was right and the classification was wrong:
#: public ids public, tokens secret. Do not "fix" a future firing of that test by
#: relaxing it; move the non-secret out instead.
DEFAULTS = Path(__file__).resolve().parents[2] / 'development-defaults.ini'

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


def load_fleet(path: Path | None = None, defaults: Path | None = None) -> Fleet:
    """Read the tokens from the secrets file and the listener id from the defaults.

    Both paths resolve at CALL time, not as bound defaults - a module-level path used
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
            f'no [{SECTION}] section in {path or SECRETS}. It needs one '
            '`<application id> = <bot token>` line per bot that should answer when '
            'mentioned. The `listener = <application id>` line is public and goes in '
            'development-defaults.ini instead.'
        )
    tokens = {
        key: value.strip()
        for key, value in parser.items(SECTION)
        if key != 'listener' and value.strip()
    }
    # ConfigObj rather than configparser for this one, because the defaults file
    # opens with top-level keys before its first section and configparser rejects
    # that outright. ConfigObj is also what the rest of the webapp reads config
    # with, so this is the house tool rather than a workaround.
    public = ConfigObj(str(defaults or DEFAULTS))
    section = public.get(SECTION) or {}
    listener = str(section.get('listener', '')).strip()
    if not tokens:
        raise NotConfigured(f'[{SECTION}] lists no bot tokens')
    if not listener:
        raise NotConfigured(
            f'no `listener = <application id>` in [{SECTION}] of '
            f'{defaults or DEFAULTS}. The id is public, so it lives in the defaults '
            'file; only the tokens are secret.'
        )
    if listener not in tokens:
        raise NotConfigured(
            f'[{SECTION}] listener {listener} has no token. The bot holding the '
            'gateway connection must be one this process can also speak as.'
        )
    return Fleet(tokens=tokens, listener=listener)
