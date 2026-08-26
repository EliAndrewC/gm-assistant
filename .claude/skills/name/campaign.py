#!/usr/bin/env python3
"""Used given names for the /name skill, from the campaign-character cache.

Feature 200: the cache (``webapp/opcache/characters.json``) is the same one the
/synthesize prompt reads; it is reconciled after every character creation and,
here, when older than MAX_AGE - via the OAuth API, never a browser cookie. The
cookie scraper (fetch_campaign_names.py / campaign-names.txt) is gone.
"""

import sys

import similarity  # noqa: F401  - puts webapp/ on sys.path

from chargen import opcache

CACHE_PATH = opcache._CACHE_PATH
#: used-names-extra.txt next to the pool: names in use that OP cannot report
#: (a PC with no OP record). The pool is never depleted by use (GM 2026-08-26).
EXTRA_PATH = opcache.EXTRA_USED_PATH
MAX_AGE = 3600.0  # mirrors the retired `/loop 1h update name cache` cadence


def used_names(refresh=None):
    """Sorted given names on the roster. ``refresh``: None = refresh if the
    cache is older than MAX_AGE; True = force; False = never (offline read).
    Never raises - a failed refresh is reported on stderr and the last cached
    roster is used (an empty one is reported too, since every name then looks
    free)."""
    if refresh is not False:
        try:
            opcache.refresh_if_stale(0.0 if refresh else MAX_AGE, CACHE_PATH)
        except Exception as e:  # OP boundary: report, do not block the pick
            print(f"WARNING: campaign cache refresh failed: {e}", file=sys.stderr)
    age = opcache.cache_age(CACHE_PATH)
    if age is None:
        print(
            "WARNING: no campaign cache - picking against an EMPTY roster "
            "(run with --refresh once Obsidian Portal is reachable)",
            file=sys.stderr,
        )
    elif age > MAX_AGE:
        print(
            f"WARNING: campaign cache is {age / 3600:.1f}h old and could not be refreshed",
            file=sys.stderr,
        )
    names = sorted(opcache.used_given_names(CACHE_PATH, EXTRA_PATH))
    if age is not None and not names:
        print("WARNING: campaign cache holds NO characters - every name looks free", file=sys.stderr)
    return names
