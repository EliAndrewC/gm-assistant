"""
Obsidian Portal (op) module for uploading and downloading characters.

This module provides two approaches for interacting with Obsidian Portal:

1. BROWSER SESSION APPROACH (WORKING):
   Since the official API is broken, we simulate browser requests using
   session cookies extracted from a logged-in browser session. You'll need
   to periodically update the session_cookie and authenticity_token in
   development-secrets.ini when they expire.

2. OAUTH 1.0 API APPROACH (CURRENTLY BROKEN):
   The official OAuth 1.0 API documented at:
       https://help.obsidianportal.com/article/105-api-authentication-oauth
       https://help.obsidianportal.com/article/99-api-characters

   As of January 2025, the API endpoints return 403 Forbidden errors.
   According to the Obsidian Portal community forums, the API is
   "currently unusable". The OAuth code is preserved below in case the
   API is restored in the future.

To set up the browser session approach:
1. Log into Obsidian Portal in Chrome
2. Open DevTools (F12) -> Network tab
3. Navigate to your campaign's "New Character" page
4. Find any request to obsidianportal.com and copy:
   - Cookie header value -> session_cookie in development-secrets.ini
   - The authenticity_token from the page source (search for csrf-token)
"""

import re
from time import sleep
from threading import Thread

import cherrypy
import requests
from bs4 import BeautifulSoup

from chargen import config
from chargen import constants as c


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
    name, *, summary='', tags=None, description='', bio='', gm_info='', avatar_upload_id=''
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
        'game_character[gm_only]': '0',
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


def _scrape_characters_page(session, url):
    """
    Scrape a single characters listing page and return a list of dicts with
    name, slug, tags, and description for each character on the page.
    """
    response = session.get(url)
    if response.status_code != 200:
        cherrypy.log(f'Failed to fetch characters page: {response.status_code}')
        return [], False

    soup = BeautifulSoup(response.text, 'html.parser')
    characters = []

    for item in soup.find_all('div', class_='content-list-item'):
        card = item.find('div', class_='content-info')
        if not card:
            continue
        name_tag = card.find('h4', class_='character-name')
        if not name_tag:
            continue
        link = name_tag.find('a', href=re.compile(r'^/characters/[^/]+$'))
        if not link or link['href'].endswith('/new'):
            continue

        name = link.get_text(strip=True)
        if not name:
            continue

        slug = link['href'].split('/')[-1]
        tags = [a['data-tag'] for a in card.find_all('a', class_='tag-link') if a.get('data-tag')]
        desc_div = card.find('div', class_='description-text')
        description = desc_div.get('title', '') if desc_div else ''

        img = item.find('img', class_='game-content-image')
        avatar_url = img['src'] if img and img.get('src') else ''

        characters.append(
            {
                'name': name,
                'slug': slug,
                'tags': tags,
                'description': description,
                'avatar_url': avatar_url,
            }
        )

    has_next = soup.find('a', rel='next') is not None
    return characters, has_next


def existing_characters():
    """
    Returns a list of dicts for all characters in the campaign, each containing
    'name', 'slug', 'tags' (list of strings), and 'description'.

    Scrapes the campaign's /characters listing page which includes tags
    and tagline for each character. Handles pagination.
    """
    try:
        session = _get_browser_session()
        campaign_url = _get_campaign_base_url()
        all_characters = []
        page = 1

        while True:
            url = f'{campaign_url}/characters'
            if page > 1:
                url += f'?page={page}'

            characters, has_next = _scrape_characters_page(session, url)
            if not characters:
                break

            all_characters.extend(characters)

            if not has_next:
                break

            page += 1
            if page > 100:
                cherrypy.log('Reached pagination limit of 100 pages')
                break

        return all_characters

    except Exception as e:
        cherrypy.log(f'Failed to fetch existing characters: {e}')
        return []


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
