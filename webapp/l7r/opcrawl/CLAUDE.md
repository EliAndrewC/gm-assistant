# `l7r.opcrawl` - consent census of other people's L5R campaigns on Obsidian Portal

`scripts/op_consent_census.py` (repo root) answers one question: which Legend of the Five Rings
campaigns on Obsidian Portal have owners who turned on "allow bots"? It reads ONLY the site's
own policy pages and the public browse listing - never another owner's campaign - and writes the
answer under the gitignored `webapp/opcache/opcrawl/census-62.json`. The results are never
committed; this tooling is (GM 2026-08-27).

| file | holds |
|---|---|
| `robots.py` | `parse_robots` (the `*` group, longest-match with `*` wildcards) and `RECORDED`, what `www.obsidianportal.com/robots.txt` said on 2026-08-27: `Crawl-delay: 20`, GPTBot disallowed outright. |
| `pages.py` | `parse_exempt_slugs` - the `data-exempt-cses` list on the pre-human-check gate page, which IS the per-campaign "allow bots" setting (all six of the GM's campaigns are on it) - and `parse_browse` for the `/campaigns?game_system_id=62` tiles (12 per page) and page count. |
| `http.py` | one GET with a descriptive User-Agent that does NOT follow redirects, so every hop is throttled. |
| `census.py` | `Throttle` (the larger of the recorded and live crawl delay between ANY two requests), `run_census`, `write_census`, `summarize`, and `ConsentError` - raised, never worked around, when robots.txt changes, an own campaign leaves the exempt list, a non-200 comes back, or Cloudflare answers with a "Just a moment..." challenge. |

How the consent signal was established, and the one robots.txt judgment call (the gate page
is under `Disallow: /pre-human-check?*` and is reached only by following the server's redirect
from the GM's own campaign root), are in `census.py`'s module docstring and `__init__.py`.

Measured 2026-08-27: the site answers ~15 requests bunched inside a few minutes with a
Cloudflare challenge (`403`, `cf-mitigated: challenge`) on the browse listing for a while
afterwards. That is exactly the case the throttle exists for; if a run stops on a challenge,
wait and retry later rather than changing the delay downward. The CLI's default is `--delay 60`,
three times the published floor, because a site's Cloudflare rate rule is configured separately
from its robots.txt and is often stricter than it, or never reconciled with it (GM 2026-08-27);
`--delay` can only raise the pace, never take it under 20 s.

## Testing

```
( cd webapp && pytest -n auto tests/test_opcrawl.py )
```

Every parsed page is a fixture under `tests/fixtures/opcrawl/`; the HTTP boundary is tested
against a local `http.server` thread. Hand-check: `./scripts/op_consent_census.py` (about
`(pages + 3) * 20` seconds; prints progress per page and the crawlable list at the end).
