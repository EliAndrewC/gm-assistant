"""Answer when a bot is mentioned in Discord.

A standalone process for an always-on box: one gateway connection listening, any
number of bot tokens speaking, so the bot a player addresses is the bot that
answers. See `CLAUDE.md` here for which file holds what.
"""

from __future__ import annotations

from l7r.mention.bots import Fleet, NotConfigured, load_fleet
from l7r.mention.memory import Memory
from l7r.mention.policy import Decider, is_bot, mentioned_bots
from l7r.mention.responder import handle, run_forever
from l7r.mention.rules import (
    CHARACTER_SHEET,
    DEFAULT_REPLY,
    GM_ASSISTANT,
    respond_to,
    strip_mentions,
)

__all__ = [
    'CHARACTER_SHEET',
    'DEFAULT_REPLY',
    'GM_ASSISTANT',
    'Memory',
    'Decider',
    'Fleet',
    'NotConfigured',
    'handle',
    'is_bot',
    'load_fleet',
    'mentioned_bots',
    'respond_to',
    'run_forever',
    'strip_mentions',
]
