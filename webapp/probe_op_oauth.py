#!/usr/bin/env python3
"""Probe the Obsidian Portal OAuth 1.0a API to see if it still 403s.

Months ago OP emailed claiming the API was fixed. Before refactoring
op.py to use the official API, this script verifies the claim end-to-end:

  Step 1 (non-interactive): POST /oauth/request_token. If this 403s,
  the API is still broken and we stop. No user interaction needed.

  Step 2 (interactive, --full only): print the authorize URL; user
  opens it in a browser logged into OP, authorizes the app, gets a
  verifier PIN, pastes it. Script exchanges for access tokens.

  Step 3 (--full only): hit GET /campaigns.json with the access tokens
  to confirm end-to-end works.

Usage from /gm-assistant/webapp/:
    python3 probe_op_oauth.py          # step 1 only
    python3 probe_op_oauth.py --full   # step 1 + 2 + 3 (interactive)

Reads consumer_key / consumer_secret from development-secrets.ini.
"""

from __future__ import annotations

import argparse
import configparser
import sys
from pathlib import Path
from urllib.parse import parse_qs

import requests
from requests_oauthlib import OAuth1, OAuth1Session

REQUEST_TOKEN_URL = 'https://www.obsidianportal.com/oauth/request_token'
AUTHORIZE_URL = 'https://www.obsidianportal.com/oauth/authorize'
ACCESS_TOKEN_URL = 'https://www.obsidianportal.com/oauth/access_token'
API_BASE_URL = 'https://api.obsidianportal.com/v1'


def load_consumer_creds() -> tuple[str, str]:
    ini = Path(__file__).resolve().parent / 'development-secrets.ini'
    if not ini.exists():
        sys.exit(f'ERROR: {ini} not found')
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(ini, encoding='utf-8')
    if not parser.has_section('obsidian_portal'):
        sys.exit('ERROR: [obsidian_portal] section missing')
    ck = parser.get('obsidian_portal', 'consumer_key', fallback='').strip()
    cs = parser.get('obsidian_portal', 'consumer_secret', fallback='').strip()
    if not ck or not cs:
        sys.exit('ERROR: consumer_key / consumer_secret not populated')
    return ck, cs


def step1_request_token(ck: str, cs: str) -> tuple[int, str | None, str | None]:
    """POST /oauth/request_token. Returns (status, oauth_token, oauth_token_secret)."""
    auth = OAuth1(ck, client_secret=cs, callback_uri='oob', signature_type='auth_header')
    print(f'[step 1] POST {REQUEST_TOKEN_URL}')
    try:
        r = requests.post(REQUEST_TOKEN_URL, auth=auth, timeout=20)
    except requests.RequestException as e:
        print(f'  -> network error: {e}')
        return 0, None, None
    print(f'  -> HTTP {r.status_code}')
    body_preview = (r.text or '')[:400]
    print(f'  -> body (first 400): {body_preview!r}')
    if r.status_code != 200:
        return r.status_code, None, None
    tokens = parse_qs(r.text)
    return 200, tokens.get('oauth_token', [None])[0], tokens.get('oauth_token_secret', [None])[0]


def step2_interactive_authorize(
    ck: str, cs: str, request_token: str, request_secret: str
) -> tuple[str, str]:
    print()
    print('[step 2a] Open this URL in a browser (signed in to Obsidian Portal):')
    print(f'  {AUTHORIZE_URL}?oauth_token={request_token}')
    verifier = input('After authorizing, paste the verifier PIN: ').strip()
    if not verifier:
        sys.exit('ERROR: no verifier entered')
    print(f'[step 2b] POST {ACCESS_TOKEN_URL}')
    sess = OAuth1Session(
        ck,
        client_secret=cs,
        resource_owner_key=request_token,
        resource_owner_secret=request_secret,
        verifier=verifier,
    )
    try:
        tokens = sess.fetch_access_token(ACCESS_TOKEN_URL)
    except Exception as e:
        sys.exit(f'ERROR exchanging verifier: {e}')
    at = tokens.get('oauth_token')
    ats = tokens.get('oauth_token_secret')
    print('  -> success')
    print(f'  -> access_token        = {at}')
    print(f'  -> access_token_secret = {ats}')
    print('  (paste these into [obsidian_portal] in development-secrets.ini)')
    return at, ats


def step3_probe_api(ck: str, cs: str, at: str, ats: str) -> int:
    sess = OAuth1Session(ck, client_secret=cs, resource_owner_key=at, resource_owner_secret=ats)
    url = f'{API_BASE_URL}/campaigns.json'
    print(f'[step 3] GET {url}')
    r = sess.get(url, timeout=20)
    print(f'  -> HTTP {r.status_code}')
    body_preview = (r.text or '')[:800]
    print(f'  -> body (first 800): {body_preview!r}')
    return r.status_code


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--full', action='store_true', help='Run step 2 (interactive) + step 3')
    args = ap.parse_args()

    ck, cs = load_consumer_creds()
    print(f'(consumer_key {len(ck)} chars, consumer_secret {len(cs)} chars)')
    print()

    status, rt, rs = step1_request_token(ck, cs)
    print()

    if status != 200 or not rt:
        print('VERDICT: request_token endpoint did not return a usable token.')
        print('         OAuth flow is blocked at the first step. API likely still broken.')
        return

    if not args.full:
        print('VERDICT: request_token endpoint is alive.')
        print('         Re-run with --full to walk the interactive auth flow + probe an API call.')
        return

    at, ats = step2_interactive_authorize(ck, cs, rt, rs or '')
    print()
    api_status = step3_probe_api(ck, cs, at, ats)
    print()
    if api_status == 200:
        print('VERDICT: API end-to-end works. Worth re-enabling op.py OAuth path.')
    else:
        print(f'VERDICT: API returned {api_status}. OAuth auth works, API still broken.')


if __name__ == '__main__':
    main()
