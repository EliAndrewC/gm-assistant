#!/usr/bin/env python3
"""Census of Legend of the Five Rings campaigns on Obsidian Portal whose owners allow bots.

Reads robots.txt and the pre-human-check exempt list, then visits the front page of every
opted-in campaign ONCE at one request per --delay (default 61 s; the floor is robots.txt's 20 s)
to learn its game system. Never a non-opted-in campaign, never the campaign directory (see
below). Writes the result under the gitignored webapp/opcache/opcrawl/. About five hours for
~290 opted-in campaigns; run it in the background.

  ./scripts/op_consent_census.py                 report L5R (game_system_id=62)
  ./scripts/op_consent_census.py --delay 121     slower still; --delay can never go below 20

Why not the campaign directory: `/campaigns?...&page=N` is answered with a Cloudflare challenge
on every paginated request, at any pace (measured 2026-08-27/28; the probes are recorded in
webapp/l7r/opcrawl/census.py). An undocumented block is still a block, and the GM ruled that if
the listing is not meant to be pulled automatically we do not pull it that way. The exempt list
is complete on its own, so nothing is lost.

Why the pace only ever goes UP, and why a challenge is never solved or routed around: this tool
exists to comply rigorously with Obsidian Portal's documented wishes (robots.txt) and its apparent
ones (a challenge is a "no"), and with the wishes of the humans who host their campaigns there
(only owners who turned on "allow bots" are ever read). We aim to be responsible internet
denizens and to be above board in appearance as well as conduct - this code is public, and
anyone at Obsidian Portal reading it should find nothing to object to. The full statement is in
webapp/l7r/opcrawl/__init__.py.
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
        default=61.0,
        help='seconds between requests; never below the robots.txt Crawl-delay (default 61)',
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
