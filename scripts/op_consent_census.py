#!/usr/bin/env python3
"""Census of Legend of the Five Rings campaigns on Obsidian Portal whose owners allow bots.

Reads robots.txt, the pre-human-check exempt list and the L5R browse listing at one request
per --delay (default 60 s; the floor is robots.txt's 20 s), never any other owner's campaign
pages, and writes the result under the gitignored webapp/opcache/opcrawl/. About 22 minutes.
See webapp/l7r/opcrawl/__init__.py.

  ./scripts/op_consent_census.py                 L5R (game_system_id=62), 60 s between requests
  ./scripts/op_consent_census.py --delay 120     slower still; --delay can never go below 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'webapp'))

from l7r.opcrawl.census import L5R_GAME_SYSTEM_ID, run_census, summarize, write_census  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    parser.add_argument('--game-system-id', type=int, default=L5R_GAME_SYSTEM_ID)
    parser.add_argument(
        '--delay',
        type=float,
        default=60.0,
        help='seconds between requests; never below the robots.txt Crawl-delay (default 60)',
    )
    args = parser.parse_args()
    census = run_census(
        game_system_id=args.game_system_id,
        delay=args.delay,
        progress=lambda s: print(s, flush=True),
    )
    print(summarize(census, write_census(census)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
