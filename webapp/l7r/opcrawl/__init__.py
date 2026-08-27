"""Consent-first census of other people's Legend of the Five Rings campaigns on Obsidian Portal.

The GM wants to read how other tables run L5R, but ONLY where the campaign owner opted in, and
without ever making Obsidian Portal unhappy. This package does the consent census and nothing
else: it never fetches a single page of another owner's campaign. Its output is the list of L5R
campaigns whose owners turned on "allow bots" - the input a later, read-only fetcher would use.

How the consent signal works (measured 2026-08-27, see `census.py`):

* Every anonymous request to `<slug>.obsidianportal.com` is 302'd to
  `www.obsidianportal.com/pre-human-check?ch=<slug>...`. That gate page embeds
  `data-exempt-cses`, the site-wide list of campaign slugs the owners exempted from the human
  check. The server enforces it: an exempt slug is served with the bare `human_check=` cookie the
  gate's own JavaScript sets; a non-exempt slug 302-loops forever without a real human check.
* `www.obsidianportal.com/robots.txt` says `Crawl-delay: 20` for everyone and disallows GPTBot
  outright. `robots.py` parses it and the census refuses to run if the recorded floor no longer
  holds or a URL it wants is now disallowed.
* The browse page `/campaigns?game_system_id=62` lists every L5R campaign (834 on 2026-08-27,
  19 pages). `pages.py` parses it from saved-fixture markup.

Entry point: `scripts/op_consent_census.py` at the repo root; the results land under the
gitignored `webapp/opcache/opcrawl/` and are never committed - only this tooling is.
"""

from l7r.opcrawl.census import OWN_CAMPAIGNS, Census, CensusRow, run_census, summarize
from l7r.opcrawl.pages import Campaign, parse_browse, parse_exempt_slugs
from l7r.opcrawl.robots import RobotsPolicy, parse_robots

__all__ = [
    'OWN_CAMPAIGNS',
    'Campaign',
    'Census',
    'CensusRow',
    'RobotsPolicy',
    'parse_browse',
    'parse_exempt_slugs',
    'parse_robots',
    'run_census',
    'summarize',
]
