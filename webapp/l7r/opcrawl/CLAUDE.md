# `l7r.opcrawl` - consent census of other people's L5R campaigns on Obsidian Portal

`scripts/op_consent_census.py` (repo root) answers one question: which Legend of the Five Rings
campaigns on Obsidian Portal have owners who turned on "allow bots"? It reads the site's own
policy pages and then ONE front page of each opted-in campaign - never a campaign whose owner
did not opt in, and never the campaign directory - and writes the answer under the gitignored
`webapp/opcache/opcrawl/census-62.json`. The results are never committed; this tooling is
(GM 2026-08-27).

| file | holds |
|---|---|
| `robots.py` | `parse_robots` (the `*` group, longest-match with `*` wildcards) and `RECORDED`, what `www.obsidianportal.com/robots.txt` said on 2026-08-27: `Crawl-delay: 20`, GPTBot disallowed outright. |
| `pages.py` | `parse_exempt_slugs` - the `data-exempt-cses` list on the pre-human-check gate page, which IS the per-campaign "allow bots" setting (all six of the GM's campaigns are on it) - and `parse_front_page` for a campaign's name, game system (`system-logo-container` sidebar) and `Last Updated`. |
| `http.py` | one GET with a descriptive User-Agent that does NOT follow redirects, so every hop is throttled; sends the bare `human_check=` cookie only when asked to (exempt campaigns). |
| `summary.py` | `content_summary.json` - a campaign's OWN manifest of its content (GM found it 2026-08-28): every public wiki page, post, character and item with path, title and tags, plus a `gm_only` flag on the ones we must never request. `?cc=<n>` is required (no `cc` -> HTTP 400) but its value is ignored - a cache-buster, not a credential - so we send the current Unix time; the `human_check=` cookie is needed as for any campaign page. |
| `fetch.py` | STAGE 2 - `crawl_campaign(slug)`: the content summary FIRST - when served, it IS the crawl list (its public pages only, no link following, GM-only pages never asked for), and `summary_only=True` stops there. A campaign without the endpoint falls back to the front page + `/wikis` + `/characters` + `/adventure-log` and content links discovered by URL SHAPE (`classify`, `campaign_links`: same host only, query strings and fragments dropped so `?page=N` is never requested), one request per 61 s with the census's `_Site` stop rules, into a resumable `Manifest` (`opcache/opcrawl/<slug>/manifest.json` + `pages/NNNN.{html,txt}`). A rerun costs the site nothing for pages already cached; a challenge saves the manifest and raises. |
| `text.py` | `page_title` (minus the ` \| Campaign \| Obsidian Portal` suffixes), `strip_scripts`, and a generic `html_to_text` that keeps block structure - deliberately not a per-template parser, since the text is only read locally by a session. |
| `index.py` | STAGE 3 - a campaign is indexed once EITHER its summary or its manifest exists, so a summaries-only pass (one request each) already ranks campaigns by how much they publish and lists every page title and tag. `build_index` writes `opcache/opcrawl/index.json` and `index.md` (per campaign: counts by kind, prose volume, every page's title/url/length/snippet, sorted by volume) - the digest a session reads to act as summarizer and search engine; `search(regex)` greps every cached page and returns campaign/title/url/context. |
| `census.py` | `Throttle` (the larger of the recorded and live crawl delay between ANY two requests), `run_census` (robots -> gate -> every exempt slug's front page once), `write_census`, `summarize`, and `ConsentError` - raised, never worked around, when robots.txt changes, an own campaign leaves the exempt list, the gate is not served, or Cloudflare answers with a "Just a moment..." challenge. A 404 on one campaign is recorded on its row and the run continues. |

How the consent signal was established, the robots.txt judgment call (the gate page is under
`Disallow: /pre-human-check?*` and is reached only by following the server's redirect from the
GM's own campaign root), and the PRINCIPLES statement are in `census.py`'s module docstring and
`__init__.py`.

**The campaign directory is a recorded dead end** (2026-08-27/28). `/campaigns?game_system_id=62&page=N`
was challenged by Cloudflare (`403`, `cf-mitigated: challenge`) at 20, 61, 121 and 301 s between
requests across a day, while every other page served. Two 61 s probes isolated it: `/campaigns` and
`/campaigns?game_system_id=62` serve; `/campaigns?page=2` is challenged. The rule is on
PAGINATION. The GM ruled (2026-08-28): if the listing is not meant to be pulled automatically we
do not pull it that way - and sort-order or search tricks would only be the block worked around.
The exempt list is complete without it.

The CLI's default is `--delay 61`, three times the published floor and just past one minute,
because a site's Cloudflare rate rule is configured separately from its robots.txt and is often
stricter than it, or never reconciled with it (GM 2026-08-27); `--delay` can only raise the pace,
never take it under 20 s. The GM's back-off ladder if a run is ever challenged again is 61 -> 121
-> 301 -> 601 s; a challenge at 601 s means the site blocks effectively everything and the
endeavor is scrapped rather than slowed further.

Entry points: `scripts/op_consent_census.py` (stage 1) and `scripts/op_fetch_campaigns.py`
(stages 2/3: `--slug X` for one campaign, `--max-pages N` to trial, `--index-only`, `--search REGEX`).
Order of operations for the GM's questions: census -> GM sees the crawlable list -> fetch ->
index -> a session reads `index.md` and `search()`es, then hands the GM the Obsidian Portal URL.

## Testing

```
( cd webapp && pytest -n auto tests/test_opcrawl.py tests/test_opcrawl_fetch.py )
```

Every parsed page is a fixture under `tests/fixtures/opcrawl/`; the HTTP boundary is tested
against a local `http.server` thread. Hand-check: `./scripts/op_consent_census.py` in the
background (about `(exempt + 3) * 61` seconds, ~5 h; prints one progress line per campaign and
the crawlable list at the end).
