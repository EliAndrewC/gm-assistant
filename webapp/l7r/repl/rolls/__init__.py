"""Capture rolls posted in Discord into an NPC's Obsidian Portal record.

The GM opens a conversation with the NPC the players are talking to, plays, and
closes it; the rolls land in that NPC's public bio under the portrait, in the GM's
own shorthand. See `CLAUDE.md` in this directory for which file holds what.
"""

from __future__ import annotations

from l7r.repl.rolls.annotate import annotate
from l7r.repl.rolls.conversation import (
    abandon_conversation,
    begin_conversation,
    close_open_conversation,
    collect,
    conversation_status,
    end_conversation,
)
from l7r.repl.rolls.models import Contest, Conversation, RecordingRule, Roll
from l7r.repl.rolls.rules import contest, record, render_contest, render_open, round_down

__all__ = [
    'Contest',
    'Conversation',
    'RecordingRule',
    'Roll',
    'abandon_conversation',
    'annotate',
    'begin_conversation',
    'close_open_conversation',
    'collect',
    'contest',
    'conversation_status',
    'end_conversation',
    'record',
    'render_contest',
    'render_open',
    'round_down',
]
