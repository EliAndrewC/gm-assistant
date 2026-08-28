"""Read messages from the GM's Discord channels. Read-only, by design and by grant.

The bot ("L7R GM Assistant", application 1509288141985415300) holds permissions
66560 - View Channel and Read Message History, nothing else. It cannot post, and
this module has no code that would. That is deliberate: the feature needs to
observe a game, not participate in one, and a bot that structurally cannot speak
is one that cannot misbehave in the GM's players' channel.

No gateway connection and no always-on process. Plain REST reads, driven by the
REPL when the GM opens a conversation.

TWO API FACTS THAT SHAPE THIS MODULE (research.md R9, both measured live):

1. `before` and `after` are MUTUALLY EXCLUSIVE. A request carrying both silently
   honors one - a window bounded at both ends came back with 100 messages running
   hours past the `before` value. So the far end is bounded here, in Python, not
   by the API.

2. A snowflake can be SYNTHESIZED from a timestamp: `(unix_ms - 1420070400000) <<
   22`. That matters because a conversation starts when the GM says it does, not
   at some message we happen to know the id of, so there is no id to page from
   until the first poll returns one.
"""

from __future__ import annotations

import configparser
import json
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

API = 'https://discord.com/api/v10'

#: Discord's epoch, 2015-01-01T00:00:00Z in milliseconds.
EPOCH_MS = 1420070400000

#: Discord asks bots to identify themselves. Ours names the project it belongs to.
USER_AGENT = 'L7RGMAssistant (https://l7r-gm-assistant.fly.dev, 0.1)'

SECRETS = Path(__file__).resolve().parents[3] / 'development-secrets.ini'

#: The GM's two game channels. Named here rather than configured because they are
#: campaign facts that change roughly never, and a session that has to look them up
#: cannot start a conversation.
#: `test` is the GM's "Robot Role Call" server (guild 1543009570157236274), which
#: exists so nothing half-finished lands in the players' channels. The reader bot
#: holds the same read-only 66560 there as it does in the live server.
CHANNELS: Mapping[str, str] = {
    'monday': '832075590726844436',
    'tuesday': '832075722516201492',
    'test': '1543009572359241840',
}


class DiscordUnavailable(RuntimeError):
    """Discord could not be read. Never raised past the conversation layer."""


def snowflake(when: datetime) -> str:
    """The smallest message id that could have been created at `when`.

    Discord ids encode their creation time in the high bits, so this gives a
    lower bound to page from without knowing any real message id.
    """
    if when.tzinfo is None:
        raise ValueError('snowflake() needs a timezone-aware datetime')
    return str((int(when.timestamp() * 1000) - EPOCH_MS) << 22)


def bot_token(path: Path = SECRETS) -> str:
    """The bot token from `[discord] bot_token`, gitignored."""
    parser = configparser.ConfigParser()
    parser.read(path)
    token = parser.get('discord', 'bot_token', fallback='').strip()
    if not token:
        raise DiscordUnavailable(
            f'no [discord] bot_token in {path}. The bot reads with a BOT token, which '
            'is a different credential from the OAuth client_id/client_secret used '
            'for website login.'
        )
    return token


def _fetch(url: str, token: str, timeout: float) -> Any:
    request = urllib.request.Request(
        url, headers={'Authorization': f'Bot {token}', 'User-Agent': USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', 'replace')[:200]
        if exc.code == 403:
            raise DiscordUnavailable(
                f'403 from Discord for {url}. The bot is in the server but cannot see '
                'this channel: a private channel needs the bot added to its own '
                'permission overrides, which a server-level grant does not reach.'
            ) from exc
        raise DiscordUnavailable(f'{exc.code} from Discord: {detail}') from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DiscordUnavailable(f'could not reach Discord: {exc}') from exc


def messages_since(
    channel_id: str,
    after: datetime | str,
    *,
    until: datetime | None = None,
    token: str | None = None,
    limit: int = 100,
    max_pages: int = 20,
    fetch: Callable[[str, str, float], Any] = _fetch,
    timeout: float = 25.0,
) -> list[dict[str, Any]]:
    """Every message in `channel_id` after `after`, oldest first.

    `after` is either a datetime (converted to a synthesized snowflake) or a message
    id to resume from. `until` bounds the far end in Python, because the API will
    not do it. `max_pages` is a runaway guard, not a feature: 20 pages is 2,000
    messages, far more than a session produces, and hitting it is reported.
    """
    cursor = after if isinstance(after, str) else snowflake(after)
    resolved = token if token is not None else bot_token()
    collected: list[dict[str, Any]] = []
    for _ in range(max_pages):
        url = f'{API}/channels/{channel_id}/messages?after={cursor}&limit={limit}'
        page = fetch(url, resolved, timeout)
        if not page:
            break
        # Discord returns newest first even when paging forward with `after`.
        page = sorted(page, key=lambda m: int(m['id']))
        collected.extend(page)
        cursor = str(page[-1]['id'])
        if len(page) < limit:
            break
    if until is not None:
        collected = [m for m in collected if parse_timestamp(m['timestamp']) <= until]
    return collected


def parse_timestamp(raw: str) -> datetime:
    """Discord's ISO-8601 timestamp as a timezone-aware UTC datetime."""
    return datetime.fromisoformat(raw.replace('Z', '+00:00')).astimezone(UTC)


def has_image(message: Mapping[str, Any]) -> bool:
    """True when the message carries an image attachment.

    This says the message MIGHT be a pasted dice card. It never says it IS one -
    clipboard pastes and memes are both `image.png` (research.md R1), so only the
    join against recorded rolls can tell them apart.
    """
    attachments: Sequence[Mapping[str, Any]] = message.get('attachments') or ()
    return any(str(a.get('content_type') or '').startswith('image') for a in attachments)


def author_id(message: Mapping[str, Any]) -> str:
    author: Mapping[str, Any] = message.get('author') or {}
    return str(author.get('id') or '')


def author_name(message: Mapping[str, Any]) -> str:
    author: Mapping[str, Any] = message.get('author') or {}
    return str(author.get('global_name') or author.get('username') or '')
