"""The daily spending ceiling, and the log of every question asked.

Both are safeguards the session added and raised with the GM (spec 218, Story 8):

- The CEILING protects the GM's Gemini bill from a runaway loop. When today's
  spend reaches it, the bot says so privately instead of calling Gemini. There
  is deliberately no per-person rate limit: with a ceiling in place it adds no
  cost protection, and refusing a player works against the point of the
  feature, that nobody should feel they are bothering anyone.
- The LOG records who asked what, the reply and its cost, so the GM can see
  what players struggle with and new evaluation questions can come from it.

Both files live beside the bot and are gitignored.
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def _today() -> str:
    return datetime.date.today().isoformat()


class Ledger:
    def __init__(
        self,
        spend_path: Path,
        log_path: Path,
        ceiling: float,
        *,
        today: Callable[[], str] = _today,
    ) -> None:
        self.spend_path = spend_path
        self.log_path = log_path
        self.ceiling = ceiling
        self._today = today

    def spent(self) -> float:
        """Dollars spent today. A missing, unreadable or yesterday's file is zero."""
        try:
            data = json.loads(self.spend_path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return 0.0
        if not isinstance(data, dict) or data.get('day') != self._today():
            return 0.0
        return float(data.get('usd', 0.0))

    def allows(self) -> bool:
        return self.spent() < self.ceiling

    def charge(self, usd: float) -> None:
        total = self.spent() + usd
        self.spend_path.write_text(
            json.dumps({'day': self._today(), 'usd': round(total, 6)}) + '\n', encoding='utf-8'
        )

    def log(self, record: Mapping[str, Any]) -> None:
        with self.log_path.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps({'day': self._today(), **record}, ensure_ascii=False) + '\n')
