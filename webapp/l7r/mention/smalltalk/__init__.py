"""Common-bot small talk, split by whose voice it is.

`voices.py` (one level up) holds what is OURS - the porpoise, the feud, the
Mirumoto grievance. This package holds the long tail that every bot on every
server gets asked, drawn from the standard small-talk taxonomies.

See `CLAUDE.md` here for which file holds what.

**AT LEAST TEN REPLIES PER CATEGORY.** The GM's rule of thumb - *"a dozen
different responses for each call and response"* - and `tests/test_mention.py`
enforces it. It used to demand three, which is how a median of four shipped
through a green gate: the guideline lived in someone's memory, and memory is not
a mechanism. If a category cannot support ten, it is probably not a category.

**What the tests can and cannot hold.** They count replies, ban images from every
Character Sheet pool, reject any image URL that did not come from `images.py`,
and prove no pattern is dead and no pool unreachable. They cannot check that a
line is earnest or sarcastic - tone is a judgment call, so it is left to whoever
is writing, guided by the voice notes at the top of each file.
"""

from __future__ import annotations

from l7r.mention.smalltalk.gm import GM
from l7r.mention.smalltalk.sheet import SHEET
from l7r.mention.smalltalk.topics import TOPIC_ORDER

__all__ = ['GM', 'SHEET', 'TOPIC_ORDER']
