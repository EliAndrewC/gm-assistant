#!/usr/bin/env python3
"""
Command-line script to authorize this application with Obsidian Portal.

NOTE: As of January 2025, the Obsidian Portal OAuth API is broken and returns
403 Forbidden errors. This script is preserved in case the API is restored.
For now, use the browser session approach documented in chargen/op.py.

This implements the OAuth 1.0a "out-of-band" (OOB) authorization flow:
1. Obtain a request token from Obsidian Portal
2. Direct the user to authorize the application
3. User enters the verifier PIN
4. Exchange for access tokens
5. Print the tokens to add to development-secrets.ini

Usage:
    ./env/bin/python authorize_op.py

Prerequisites:
    1. Register your application at Obsidian Portal to get consumer key/secret
    2. Add them to development-secrets.ini:
       [obsidian_portal]
       consumer_key = your_key_here
       consumer_secret = your_secret_here
"""

import sys
import os

# Add parent directory to path so we can import chargen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from requests_oauthlib import OAuth1Session
import requests

from chargen import config
from chargen.op import REQUEST_TOKEN_URL, AUTHORIZE_URL, ACCESS_TOKEN_URL


def get_consumer_credentials():
    """Get consumer key and secret from config."""
    op_config = config.get('obsidian_portal', {})
    consumer_key = op_config.get('consumer_key', '')
    consumer_secret = op_config.get('consumer_secret', '')

    if not consumer_key or not consumer_secret:
        print('Error: OAuth consumer credentials not configured.')
        print()
        print('To set up OAuth:')
        print('1. Go to http://www.obsidianportal.com/oauth/clients/new')
        print('   (You must be logged in to Obsidian Portal)')
        print('2. Register a new application')
        print('   - For "Callback URL", you can enter: oob')
        print('   - Or leave it blank if allowed')
        print('3. Create development-secrets.ini with:')
        print()
        print('   [obsidian_portal]')
        print('   consumer_key = your_consumer_key')
        print('   consumer_secret = your_consumer_secret')
        print()
        sys.exit(1)

    return consumer_key, consumer_secret


def main():
    print('Obsidian Portal OAuth 1.0a Authorization')
    print('=' * 45)
    print()
    print('WARNING: The Obsidian Portal OAuth API is currently broken (as of')
    print('January 2025). This script will likely fail with a 403 error.')
    print('Consider using the browser session approach instead - see')
    print('chargen/op.py and development-secrets.ini.example for details.')
    print()
    input('Press Enter to continue anyway, or Ctrl+C to abort...')
    print()

    # Step 1: Get consumer credentials
    consumer_key, consumer_secret = get_consumer_credentials()

    print(f'Using consumer key: {consumer_key[:8]}...')
    print()

    # Step 2: Obtain request token
    # Try without callback_uri first, then with 'oob' if that fails
    print('Step 1: Obtaining request token...')

    # First attempt: no callback_uri
    oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

    try:
        fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
    except Exception as e1:
        # Second attempt: with callback_uri='oob'
        print(f'  First attempt failed: {e1}')
        print('  Trying with callback_uri=oob...')
        oauth = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri='oob')
        try:
            fetch_response = oauth.fetch_request_token(REQUEST_TOKEN_URL)
        except Exception as e2:
            print(f'Error obtaining request token: {e2}')
            print()
            print('Troubleshooting tips:')
            print('1. Verify your consumer key and secret are correct (no extra spaces)')
            print('2. Check that your system clock is accurate (OAuth 1.0 is time-sensitive)')
            print('3. When registering your app, what did you enter for Callback URL?')
            print('   - Try registering a new app with callback URL set to: oob')
            print('4. The Obsidian Portal API may be temporarily unavailable')
            print()
            print('You can also try the manual test:')
            print(f'  curl -v "{REQUEST_TOKEN_URL}"')
            sys.exit(1)

    request_token = fetch_response.get('oauth_token')
    request_token_secret = fetch_response.get('oauth_token_secret')

    print('  Request token obtained successfully.')
    print()

    # Step 3: Direct user to authorization URL
    authorization_url = oauth.authorization_url(AUTHORIZE_URL)

    print('Step 2: Authorize the application')
    print()
    print('  Please visit this URL in your browser while logged into Obsidian Portal:')
    print()
    print(f'  {authorization_url}')
    print()
    print('  After authorizing, you will see a PIN/verifier code.')
    print()

    # Step 4: Get the verifier from user
    verifier = input('Step 3: Enter the verifier PIN: ').strip()

    if not verifier:
        print('Error: No verifier entered.')
        sys.exit(1)

    # Step 5: Exchange for access token
    print()
    print('Step 4: Exchanging for access token...')

    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=request_token,
        resource_owner_secret=request_token_secret,
        verifier=verifier,
    )

    try:
        oauth_tokens = oauth.fetch_access_token(ACCESS_TOKEN_URL)
    except Exception as e:
        print(f'Error obtaining access token: {e}')
        print()
        print('The verifier may be incorrect or expired. Please try again.')
        sys.exit(1)

    access_token = oauth_tokens.get('oauth_token')
    access_token_secret = oauth_tokens.get('oauth_token_secret')

    print('  Access token obtained successfully!')
    print()

    # Step 6: Display results
    print('=' * 45)
    print('Authorization Complete!')
    print('=' * 45)
    print()
    print('Add the following to your development-secrets.ini file:')
    print()
    print('[obsidian_portal]')
    print(f'consumer_key = {consumer_key}')
    print(f'consumer_secret = {consumer_secret}')
    print(f'access_token = {access_token}')
    print(f'access_token_secret = {access_token_secret}')
    print(f'campaign_id = YOUR_CAMPAIGN_ID_HERE')
    print()
    print('To find your campaign ID:')
    print('  - Go to your campaign on Obsidian Portal')
    print('  - Look at the URL or check the API response')
    print('  - The campaign ID is a UUID like: 12345678-1234-1234-1234-123456789abc')
    print()


if __name__ == '__main__':
    main()
