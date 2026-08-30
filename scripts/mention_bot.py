#!/usr/bin/env python3
"""Run the Discord mention responder.

    ./scripts/mention_bot.py

Listens on one bot's gateway connection and replies as whichever bot was
mentioned. Configure the fleet in `webapp/development-secrets.ini` under
`[mention_bots]` - see `webapp/l7r/mention/bots.py`.

Meant for an always-on box. It reconnects on its own and answers no bot, ever.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webapp"))

from l7r.mention import NotConfigured, run_forever  # noqa: E402


def main() -> int:
    try:
        asyncio.run(run_forever())
    except NotConfigured as exc:
        print(f"not configured: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
