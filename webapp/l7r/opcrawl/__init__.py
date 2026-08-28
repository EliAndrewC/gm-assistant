"""Consent-first census of other people's Legend of the Five Rings campaigns on Obsidian Portal.

The GM wants to read how other tables run L5R, but ONLY where the campaign owner opted in, and
without ever making Obsidian Portal unhappy. This package does the consent census and nothing
else: it never fetches a single page of another owner's campaign. Its output is the list of L5R
campaigns whose owners turned on "allow bots" - the input a later, read-only fetcher would use.

PRINCIPLES (the GM's, 2026-08-27 - they govern every request this code makes):

* We comply with Obsidian Portal's DOCUMENTED wishes (robots.txt: the crawl delay, the disallowed
  paths, the agents it turns away) AND its APPARENT wishes (a Cloudflare challenge is the site
  saying "not right now" and is obeyed as such - we stop, we never solve or route around it, and
  we do not change IP addresses to get past it).
* We comply with the wishes of the humans who put their campaigns there. A campaign is read
  only if its owner turned on the setting that says bots may; every other campaign is not
  fetched at all, whatever is technically reachable. Nobody's writing is fed to a model without
  their permission.
* We are responsible internet denizens: a descriptive User-Agent that says who we are, a pace
  well below the published floor, back-off rather than retry when told no, and a hard stop when
  a site's behavior says it does not want automated visitors at all.
* We are above board in appearance as well as conduct. This code is public; anyone at Obsidian
  Portal reading it should find nothing they would object to, and the reasoning behind every
  judgment call is written down next to the call so it can be checked, not just trusted.

How the consent signal works (measured 2026-08-27, see `census.py`):

* Every anonymous request to `<slug>.obsidianportal.com` is 302'd to
  `www.obsidianportal.com/pre-human-check?ch=<slug>...`. That gate page embeds
  `data-exempt-cses`, the site-wide list of campaign slugs the owners exempted from the human
  check. The server enforces it: an exempt slug is served with the bare `human_check=` cookie the
  gate's own JavaScript sets; a non-exempt slug 302-loops forever without a real human check.
* `www.obsidianportal.com/robots.txt` says `Crawl-delay: 20` for everyone and disallows GPTBot
  outright. `robots.py` parses it and the census refuses to run if the recorded floor no longer
  holds or a URL it wants is now disallowed.
* Each opted-in campaign's front page names its game system (`pages.py`). The census visits
  each once. The campaign DIRECTORY is deliberately not walked - Cloudflare challenges any
  paginated listing request, an undocumented but unambiguous wish; the diagnosis is in
  `census.py`.

Entry point: `scripts/op_consent_census.py` at the repo root; the results land under the
gitignored `webapp/opcache/opcrawl/` and are never committed - only this tooling is.
"""

from l7r.opcrawl.census import OWN_CAMPAIGNS, Census, CensusRow, run_census, summarize
from l7r.opcrawl.pages import FrontPage, parse_exempt_slugs, parse_front_page
from l7r.opcrawl.robots import RobotsPolicy, parse_robots

__all__ = [
    'OWN_CAMPAIGNS',
    'Census',
    'CensusRow',
    'FrontPage',
    'RobotsPolicy',
    'parse_exempt_slugs',
    'parse_front_page',
    'parse_robots',
    'run_census',
    'summarize',
]
