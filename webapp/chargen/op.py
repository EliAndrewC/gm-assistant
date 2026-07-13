"""
Obsidian Portal (op) module for uploading and downloading characters.

This module uses a hybrid OAuth + browser-session approach:

1. OAUTH 1.0 API - used for reads and deletes (the bulk of operations).
   Verified working 2026-05-30 via probe_op_oauth.py.
   Endpoints:
     GET    /v1/users/me.json
     GET    /v1/campaigns/{id}.json
     GET    /v1/campaigns/{id}/characters.json
     POST   /v1/campaigns/{id}/characters.json
     PATCH  /v1/campaigns/{id}/characters/{cid}.json
     DELETE /v1/campaigns/{id}/characters/{cid}.json
   Requires consumer_key, consumer_secret, access_token, access_token_secret,
   campaign_id under [obsidian_portal] in development-secrets.ini. Tokens
   are obtained once via probe_op_oauth.py --full and don't expire on the
   normal "sessions rotate" cadence the browser cookie does.

2. BROWSER SESSION - still needed for character creation when an avatar
   is attached, and for image uploads (/files and /uploads endpoints).
   The OAuth API has NO file-upload mechanism: every variant of inline
   base64 avatar, avatar_upload_id, or avatar_url field is silently
   accepted but never applied (probed exhaustively, all return 200 with
   avatar_url=null). So create_character + upload_image + upload_avatar
   keep using the session_cookie path. These break when the cookie or
   authenticity_token rotates; update them per the steps below.

To refresh the browser-session credentials:
1. Log into Obsidian Portal in Chrome
2. Open DevTools (F12) -> Network tab
3. Navigate to your campaign's "New Character" page
4. Find any request to obsidianportal.com and copy:
   - Cookie header value -> session_cookie in development-secrets.ini
   - The authenticity_token from the page source (search for csrf-token)
"""

from threading import Thread
from time import sleep

import cherrypy
import requests
from requests_oauthlib import OAuth1Session

from chargen import config
from chargen import constants as c

API_BASE_URL = 'https://api.obsidianportal.com/v1'


# =============================================================================
# BROWSER SESSION APPROACH (WORKING)
# =============================================================================


def _get_campaign_base_url():
    """Get the campaign base URL from config."""
    campaign_url = config.get('campaign_url', '')
    if not campaign_url:
        raise ValueError('campaign_url not configured in development-defaults.ini')
    # Ensure https and no trailing slash
    if not campaign_url.startswith('http'):
        campaign_url = 'https://' + campaign_url
    return campaign_url.rstrip('/')


def _get_browser_session():
    """
    Create a requests session that mimics a browser with the configured
    session cookie.
    """
    op_config = config.get('obsidian_portal', {})
    session_cookie = op_config.get('session_cookie', '')

    if not session_cookie:
        raise ValueError(
            'Browser session not configured. Add session_cookie to '
            '[obsidian_portal] in development-secrets.ini. '
            'See the module docstring for instructions.'
        )

    campaign_url = _get_campaign_base_url()

    session = requests.Session()
    session.headers.update(
        {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': campaign_url,
            'Referer': f'{campaign_url}/characters/new',
            'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108";',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Cookie': session_cookie,
        }
    )

    return session


def _get_authenticity_token():
    """Get the CSRF authenticity token from config."""
    op_config = config.get('obsidian_portal', {})
    token = op_config.get('authenticity_token', '')

    if not token:
        raise ValueError(
            'authenticity_token not configured. Add it to [obsidian_portal] '
            'in development-secrets.ini. Find it in the page source by '
            'searching for "csrf-token" or "authenticity_token".'
        )

    return token


def create_character(
    name,
    *,
    summary='',
    tags=None,
    description='',
    bio='',
    gm_info='',
    avatar_upload_id='',
    gm_only=False,
):
    """
    Create a character in Obsidian Portal by simulating browser form submission.

    Args:
        name: The character's full name
        summary: A short tagline/summary for the character
        tags: List of tags to apply to the character
        description: The public description
        bio: The character's biography
        gm_info: GM-only information
        avatar_upload_id: The upload ID from upload_avatar() for the character thumbnail
        gm_only: When True, create the character as GM-only (hidden from players)

    Returns:
        requests.Response: The response from the server
    """
    session = _get_browser_session()
    campaign_url = _get_campaign_base_url()
    authenticity_token = _get_authenticity_token()

    payload = {
        'utf8': '✓',
        'authenticity_token': authenticity_token,
        'game_character[name]': name,
        'game_character[slug]': '',
        'game_character[tagline]': summary,
        'game_character[tag_list]': ','.join(tags) if tags else '',
        'tag-dummy-input-clone': '',
        'game_character[description]': description,
        'game_character[bio]': bio,
        'game_character[gm_info]': gm_info,
        'game_character[is_pc]': '0',
        'game_character[wish_list]': '',
        'game_character[gm_only]': '1' if gm_only else '0',
        'game_character[hide_stats]': '0',
        'commit': 'Create',
        'new_avatar_upload_id': avatar_upload_id,
    }

    response = session.post(f'{campaign_url}/characters', data=payload)

    if response.status_code == 200 and '/characters/' in response.url:
        # Success - we were redirected to the new character page
        cherrypy.log(f'Created character: {name} at {response.url}')
        # Add the personal name to USED_NAMES immediately so we don't reuse it
        personal_name = name.split()[-1]
        c.USED_NAMES.add(personal_name)
    elif response.status_code == 422:
        raise ValueError(
            'Failed to create character (422). The authenticity_token may '
            'have expired. Update it in development-secrets.ini.'
        )
    elif response.status_code == 403:
        raise ValueError(
            'Failed to create character (403). The session_cookie may have '
            'expired. Update it in development-secrets.ini.'
        )
    else:
        response.raise_for_status()

    return response


def upload_image(image_data: bytes, filename: str) -> dict:
    """
    Upload an image to Obsidian Portal and return the file info.
    This uploads to /files for embedding in character bio sections.

    Args:
        image_data: The raw PNG image bytes
        filename: The filename to use (e.g., "CharacterName.png")

    Returns:
        dict: The response from the server containing 'id', 'filename', etc.
    """
    op_config = config.get('obsidian_portal', {})
    asset_folder_id = op_config.get('asset_folder_id', '')

    if not asset_folder_id:
        raise ValueError(
            'asset_folder_id not configured. Add it to [obsidian_portal] '
            'in development-secrets.ini. Find it in the Network tab when '
            'uploading an image manually.'
        )

    session = _get_browser_session()
    campaign_url = _get_campaign_base_url()

    url = f'{campaign_url}/files?asset_folder_id={asset_folder_id}'

    # Update headers for JSON response and AJAX request
    session.headers.update(
        {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        }
    )
    # Remove Content-Type so requests can set it properly for multipart
    if 'Content-Type' in session.headers:
        del session.headers['Content-Type']

    files = {'file': (filename, image_data, 'image/png')}

    response = session.post(url, files=files)

    if response.status_code == 200:
        result = response.json()
        cherrypy.log(f'Uploaded image: {filename} with id {result.get("id")}')
        return result
    elif response.status_code == 422:
        raise ValueError(
            'Failed to upload image (422). The authenticity_token may '
            'have expired. Update it in development-secrets.ini.'
        )
    elif response.status_code == 403:
        raise ValueError(
            'Failed to upload image (403). The session_cookie may have '
            'expired. Update it in development-secrets.ini.'
        )
    else:
        response.raise_for_status()


def upload_avatar(image_data: bytes, filename: str) -> dict:
    """
    Upload an avatar/thumbnail image to Obsidian Portal.
    This uploads to /uploads with upload_type=character_avatar.

    Args:
        image_data: The raw PNG image bytes
        filename: The filename to use (e.g., "CharacterName.png")

    Returns:
        dict: The response from the server containing 'id', 'filename', etc.
    """
    session = _get_browser_session()
    campaign_url = _get_campaign_base_url()

    url = f'{campaign_url}/uploads'

    # Update headers for JSON response and AJAX request
    session.headers.update(
        {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        }
    )
    # Remove Content-Type so requests can set it properly for multipart
    if 'Content-Type' in session.headers:
        del session.headers['Content-Type']

    # Multipart form data with upload_type field
    files = {'file[0]': (filename, image_data, 'image/png')}
    data = {'upload_type': 'character_avatar'}

    response = session.post(url, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        cherrypy.log(f'Uploaded avatar: {filename} with id {result.get("id")}')
        return result
    elif response.status_code == 422:
        raise ValueError(
            'Failed to upload avatar (422). The authenticity_token may '
            'have expired. Update it in development-secrets.ini.'
        )
    elif response.status_code == 403:
        raise ValueError(
            'Failed to upload avatar (403). The session_cookie may have '
            'expired. Update it in development-secrets.ini.'
        )
    else:
        response.raise_for_status()


def _get_oauth_session():
    """Build a requests_oauthlib session signed with the configured tokens.

    Tokens come from [obsidian_portal] in development-secrets.ini. The
    consumer pair is registered at https://www.obsidianportal.com/oauth/clients
    once and rarely rotates; the access pair is obtained by running
    probe_op_oauth.py --full and pasting the printed values into the ini.
    """
    op_config = config.get('obsidian_portal', {})
    ck = op_config.get('consumer_key', '')
    cs = op_config.get('consumer_secret', '')
    at = op_config.get('access_token', '')
    ats = op_config.get('access_token_secret', '')
    missing = [
        name
        for name, val in [
            ('consumer_key', ck),
            ('consumer_secret', cs),
            ('access_token', at),
            ('access_token_secret', ats),
        ]
        if not val
    ]
    if missing:
        raise ValueError(
            f'OAuth credentials not configured: {", ".join(missing)} '
            f'missing from [obsidian_portal] in development-secrets.ini. '
            f'Run probe_op_oauth.py --full to obtain access tokens.'
        )
    return OAuth1Session(ck, client_secret=cs, resource_owner_key=at, resource_owner_secret=ats)


def _get_campaign_id():
    """Read campaign_id from [obsidian_portal] or raise with guidance."""
    op_config = config.get('obsidian_portal', {})
    cid = op_config.get('campaign_id', '')
    if not cid:
        raise ValueError(
            'campaign_id not configured in [obsidian_portal]. Discover it '
            'via GET /v1/users/me.json (the "campaigns" array on the response).'
        )
    return cid


def existing_characters():
    """Return a list of dicts for all characters in the campaign.

    Each dict has: id, slug, name, character_url, avatar_url, tags
    (list of strings), description, is_player_character, is_game_master_only.

    Uses the OAuth API - the campaign-wide listing endpoint returns all
    characters in one request (no pagination needed at our campaign size).
    """
    try:
        api = _get_oauth_session()
        campaign_id = _get_campaign_id()
        url = f'{API_BASE_URL}/campaigns/{campaign_id}/characters.json'
        response = api.get(url, timeout=20)
        response.raise_for_status()
    except Exception as e:
        cherrypy.log(f'Failed to fetch existing characters: {e}')
        return []

    return [
        {
            'id': c.get('id', ''),
            'slug': c.get('slug', ''),
            'name': c.get('name', ''),
            'character_url': c.get('character_url', ''),
            'avatar_url': c.get('avatar_url') or '',
            'tags': list(c.get('tags') or []),
            'description': c.get('description') or '',
            'updated_at': c.get('updated_at') or '',
            'is_player_character': bool(c.get('is_player_character')),
            'is_game_master_only': bool(c.get('is_game_master_only')),
        }
        for c in (response.json() or [])
    ]


def get_character_body(character_id: str) -> dict[str, object] | None:
    """Fetch one character's full body via the OAuth API.

    Returns {'name', 'tags', 'bio', 'game_master_info', 'updated_at'} or None on
    any failure (logged). Never raises - callers (the campaign-context cache)
    degrade gracefully when OP is unreachable.
    """
    try:
        api = _get_oauth_session()
        campaign_id = _get_campaign_id()
        url = f'{API_BASE_URL}/campaigns/{campaign_id}/characters/{character_id}.json'
        response = api.get(url, timeout=20)
        response.raise_for_status()
        c = response.json() or {}
    except Exception as e:
        cherrypy.log(f'Failed to fetch character body {character_id}: {e}')
        return None
    return {
        'name': c.get('name') or '',
        'tags': list(c.get('tags') or []),
        'bio': c.get('bio') or '',
        'description': c.get('description') or '',
        'game_master_info': c.get('game_master_info') or '',
        'updated_at': c.get('updated_at') or '',
    }


def fetch_character_page(character_url: str) -> str | None:
    """Fetch a character's OP page HTML via the authenticated browser session.

    Returns the page HTML on success, or None on any failure (logged). Never
    raises. Used to read the character's tagline (the one-line summary), which
    the OAuth JSON API does not expose; parse the HTML with
    ``opsynth.parse_tagline``.
    """
    try:
        session = _get_browser_session()
        response = session.get(character_url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        cherrypy.log(f'Failed to fetch character page {character_url}: {e}')
        return None


def delete_character(character_id):
    """Delete a character via the OAuth API.

    Returns True on success (204), False if the character was already gone
    (404). Any other status raises.
    """
    api = _get_oauth_session()
    campaign_id = _get_campaign_id()
    url = f'{API_BASE_URL}/campaigns/{campaign_id}/characters/{character_id}.json'
    response = api.delete(url, timeout=20)
    if response.status_code == 204:
        cherrypy.log(f'Deleted character via API: {character_id}')
        return True
    if response.status_code == 404:
        cherrypy.log(f'Character already gone: {character_id}')
        return False
    response.raise_for_status()
    return False


def update_character(character_id, **fields):
    """PATCH a character via the OAuth API. Returns the updated character dict.

    Pass any subset of: name, tagline, description, bio, game_master_info,
    tags (list[str]), is_player_character, is_game_master_only. The API
    silently drops unknown fields (we probed avatar variants exhaustively -
    every one returns 200 without taking effect), so only pass real ones.
    """
    if not fields:
        raise ValueError('update_character: no fields supplied')
    api = _get_oauth_session()
    campaign_id = _get_campaign_id()
    url = f'{API_BASE_URL}/campaigns/{campaign_id}/characters/{character_id}.json'
    response = api.patch(url, json={'character': fields}, timeout=30)
    response.raise_for_status()
    cherrypy.log(f'Updated character {character_id}: {list(fields)}')
    return response.json()


# ---------------------------------------------------------------------------
# Wiki page CRUD (OAuth API). Verified working 2026-05-30 - same endpoint
# shape as characters, nested under /campaigns/{id}/wikis/.
# Schema fields the API exposes:
#   name, slug, body (Textile), body_html, game_master_info,
#   game_master_info_html, is_game_master_only, tags, post_title,
#   post_tagline, post_time, wiki_page_url.
# ---------------------------------------------------------------------------


def existing_wiki_pages():
    """Return a list of dicts for all wiki pages in the campaign.

    Each dict has: id, slug, name, wiki_page_url, tags, is_game_master_only.
    Doesn't include body - fetch individual pages via get_wiki_page() for
    that. The listing endpoint gives enough metadata to route an intake
    to the right page without paying for every page's body.
    """
    try:
        api = _get_oauth_session()
        campaign_id = _get_campaign_id()
        url = f'{API_BASE_URL}/campaigns/{campaign_id}/wikis.json'
        response = api.get(url, timeout=20)
        response.raise_for_status()
    except Exception as e:
        cherrypy.log(f'Failed to fetch wiki pages: {e}')
        return []
    return [
        {
            'id': p.get('id', ''),
            'slug': p.get('slug', ''),
            'name': p.get('name', ''),
            'wiki_page_url': p.get('wiki_page_url', ''),
            'tags': list(p.get('tags') or []),
            'is_game_master_only': bool(p.get('is_game_master_only')),
        }
        for p in (response.json() or [])
    ]


def get_wiki_page(page_id):
    """Fetch a single wiki page with its full body + game_master_info.

    page_id is the API id (NOT the slug). Use existing_wiki_pages() to
    look up an id by slug if needed.
    """
    api = _get_oauth_session()
    campaign_id = _get_campaign_id()
    url = f'{API_BASE_URL}/campaigns/{campaign_id}/wikis/{page_id}.json'
    response = api.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def create_wiki_page(name, *, body='', game_master_info='', tags=None, is_game_master_only=False):
    """Create a wiki page via OAuth API. Returns the new page dict (incl. id, slug).

    `body` is Textile markup (OP's wiki dialect). \\r\\n line endings match
    existing pages; \\n alone also works.
    """
    api = _get_oauth_session()
    campaign_id = _get_campaign_id()
    url = f'{API_BASE_URL}/campaigns/{campaign_id}/wikis.json'
    payload = {
        'wiki_page': {
            'name': name,
            'body': body,
            'game_master_info': game_master_info,
            'is_game_master_only': bool(is_game_master_only),
        }
    }
    if tags:
        payload['wiki_page']['tags'] = list(tags)
    response = api.post(url, json=payload, timeout=30)
    response.raise_for_status()
    page = response.json()
    cherrypy.log(f'Created wiki page: {name} (id={page.get("id")}, slug={page.get("slug")})')
    return page


def update_wiki_page(page_id, **fields):
    """PATCH a wiki page via OAuth API. Returns the updated page dict.

    Pass any subset of: name, body, game_master_info, is_game_master_only,
    tags, post_title, post_tagline, post_time. Unknown fields are silently
    dropped (same behavior as character PATCH).

    The API returns 200 with an empty body on successful update; we re-GET
    the page so callers always get back the new state.
    """
    if not fields:
        raise ValueError('update_wiki_page: no fields supplied')
    api = _get_oauth_session()
    campaign_id = _get_campaign_id()
    url = f'{API_BASE_URL}/campaigns/{campaign_id}/wikis/{page_id}.json'
    response = api.patch(url, json={'wiki_page': fields}, timeout=30)
    response.raise_for_status()
    cherrypy.log(f'Updated wiki page {page_id}: {list(fields)}')
    if not response.text.strip():
        return get_wiki_page(page_id)
    return response.json()


def delete_wiki_page(page_id):
    """Delete a wiki page via OAuth API. Returns True on 204, False on 404."""
    api = _get_oauth_session()
    campaign_id = _get_campaign_id()
    url = f'{API_BASE_URL}/campaigns/{campaign_id}/wikis/{page_id}.json'
    response = api.delete(url, timeout=20)
    if response.status_code == 204:
        cherrypy.log(f'Deleted wiki page via API: {page_id}')
        return True
    if response.status_code == 404:
        cherrypy.log(f'Wiki page already gone: {page_id}')
        return False
    response.raise_for_status()
    return False


def existing_names():
    """
    Returns a list of all character names for the campaign.
    Wrapper around existing_characters() for backward compatibility.
    """
    return [char['name'] for char in existing_characters()]


def characters_by_tag(tag):
    """
    Returns a list of character dicts that have the given tag.
    Tag matching is case-insensitive.
    """
    tag_lower = tag.lower()
    return [
        char for char in existing_characters() if any(t.lower() == tag_lower for t in char['tags'])
    ]


def update_used_names():
    """
    We keep track of what names already exist in our campaign to avoid using the
    same name multiple times. Every time we create a character, we add its name
    to our global name set, but here we also periodically download everything in
    the background to update the list, in case we missed anything (e.g. if a new
    character was added through the Obsidian Portal UI instead of here).
    """
    while True:
        try:
            for name in existing_names():
                # we only track the personal name (e.g. "Gohei" instead of "Matsu Gohei")
                c.USED_NAMES.add(name.split()[-1])
        except Exception as e:
            cherrypy.log(f'Failed to update used names: {e}')
        sleep(3600)


existing_name_updater = Thread(target=update_used_names, daemon=True)
cherrypy.engine.subscribe('start', existing_name_updater.start)


# =============================================================================
# OAUTH 1.0 API APPROACH (CURRENTLY BROKEN - PRESERVED FOR FUTURE USE)
# =============================================================================
#
# As of January 2025, the Obsidian Portal OAuth API returns 403 Forbidden
# errors for all endpoints, including the request_token endpoint. This appears
# to be a server-side issue - even unauthenticated curl requests fail:
#
#   $ curl -v "https://www.obsidianportal.com/oauth/request_token"
#   < HTTP/2 403
#
# According to the Obsidian Portal community forums, the API is "currently
# unusable" and there have been discussions about potentially restoring it.
#
# The code below is preserved in case the API is restored. To use it:
# 1. Uncomment the code
# 2. Run authorize_op.py to obtain access tokens
# 3. Add tokens to development-secrets.ini
#
# OAuth 1.0 endpoints:
# REQUEST_TOKEN_URL = 'https://www.obsidianportal.com/oauth/request_token'
# AUTHORIZE_URL = 'https://www.obsidianportal.com/oauth/authorize'
# ACCESS_TOKEN_URL = 'https://www.obsidianportal.com/oauth/access_token'
# API_BASE_URL = 'https://api.obsidianportal.com/v1'
#
# def get_oauth_session(resource_owner_key=None, resource_owner_secret=None):
#     """
#     Create an OAuth1Session with the configured consumer credentials.
#     Optionally include resource owner (access token) credentials.
#     """
#     from requests_oauthlib import OAuth1Session
#
#     op_config = config.get('obsidian_portal', {})
#     consumer_key = op_config.get('consumer_key', '')
#     consumer_secret = op_config.get('consumer_secret', '')
#
#     if not consumer_key or not consumer_secret:
#         raise ValueError(
#             'OAuth consumer credentials not configured. '
#             'Add consumer_key and consumer_secret to [obsidian_portal] in development-secrets.ini'
#         )
#
#     return OAuth1Session(
#         consumer_key,
#         client_secret=consumer_secret,
#         resource_owner_key=resource_owner_key,
#         resource_owner_secret=resource_owner_secret
#     )
#
#
# def get_authenticated_session():
#     """
#     Get an OAuth1Session with full access token credentials for making API calls.
#     """
#     op_config = config.get('obsidian_portal', {})
#     access_token = op_config.get('access_token', '')
#     access_token_secret = op_config.get('access_token_secret', '')
#
#     if not access_token or not access_token_secret:
#         raise ValueError(
#             'OAuth access token not configured. '
#             'Run the authorize_op.py script to obtain access tokens.'
#         )
#
#     return get_oauth_session(
#         resource_owner_key=access_token,
#         resource_owner_secret=access_token_secret
#     )
#
#
# def get_campaign_id():
#     """Get the configured campaign ID for API calls."""
#     op_config = config.get('obsidian_portal', {})
#     campaign_id = op_config.get('campaign_id', '')
#
#     if not campaign_id:
#         raise ValueError(
#             'Campaign ID not configured. '
#             'Add campaign_id to [obsidian_portal] in development-secrets.ini'
#         )
#
#     return campaign_id
#
#
# def create_character_oauth(name, *, summary, description, gm_info, tags=None):
#     """Create a character using the OAuth API."""
#     session = get_authenticated_session()
#     campaign_id = get_campaign_id()
#     url = f'{API_BASE_URL}/campaigns/{campaign_id}/characters.json'
#
#     payload = {
#         'character': {
#             'name': name,
#             'tagline': summary,
#             'description': description,
#             'bio': description,
#             'game_master_info': gm_info,
#         }
#     }
#     if tags:
#         payload['character']['tags'] = tags
#
#     response = session.post(url, json=payload)
#     response.raise_for_status()
#     return response.json()
#
#
# def list_characters_oauth():
#     """Retrieve all characters from the campaign using OAuth API."""
#     session = get_authenticated_session()
#     campaign_id = get_campaign_id()
#     url = f'{API_BASE_URL}/campaigns/{campaign_id}/characters.json'
#
#     response = session.get(url)
#     response.raise_for_status()
#     return response.json()
