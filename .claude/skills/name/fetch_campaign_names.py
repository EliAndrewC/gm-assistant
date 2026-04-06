#!/usr/bin/env python3
"""Fetch NPC names from Obsidian Portal using browser session cookies.
Based on the approach from https://github.com/EliAndrewC/chargen"""

import os
import sys
import requests
from bs4 import BeautifulSoup

CAMPAIGN_URL = "https://waspbountyhunters.obsidianportal.com"
CHARACTERS_URL = f"{CAMPAIGN_URL}/characters"

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SKILL_DIR, ".env")

def load_session_cookie():
    """Load session cookie from .env file or environment variable."""
    # Check environment variable first
    cookie = os.environ.get("OBSIDIAN_SESSION_COOKIE")
    if cookie:
        return cookie
    # Fall back to .env file
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("OBSIDIAN_SESSION_COOKIE="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("ERROR: No session cookie found.", file=sys.stderr)
    print(f"Set OBSIDIAN_SESSION_COOKIE in {ENV_PATH} or as an environment variable.", file=sys.stderr)
    print(f"Example: echo 'OBSIDIAN_SESSION_COOKIE=your_cookie_here' > {ENV_PATH}", file=sys.stderr)
    sys.exit(1)

SESSION_COOKIE = load_session_cookie()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": SESSION_COOKIE,
    "Referer": CAMPAIGN_URL,
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
}


def scrape_characters_page(session, url):
    """Scrape a single page of characters. Returns (names, next_url)."""
    resp = session.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"ERROR: Got status {resp.status_code} for {url}", file=sys.stderr)
        with open("/tmp/obsidian-debug.html", "w") as f:
            f.write(resp.text)
        print("Debug page saved to /tmp/obsidian-debug.html", file=sys.stderr)
        return [], None

    if "Pre Human Check" in resp.text:
        print("ERROR: Bot protection triggered. Session cookie may be expired.", file=sys.stderr)
        print("Re-extract cookies from Chrome DevTools and update the script.", file=sys.stderr)
        with open("/tmp/obsidian-debug.html", "w") as f:
            f.write(resp.text)
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")
    names = []

    # Match chargen's approach: look for character name links
    for item in soup.select("div.content-list-item"):
        name_el = item.select_one("h4.character-name a")
        if name_el:
            name = name_el.get_text(strip=True)
            if name:
                names.append(name)

    # Fallback: try broader selectors if the above didn't work
    if not names:
        for link in soup.select("a[href*='/characters/']"):
            name = link.get_text(strip=True)
            if name and len(name) > 1 and "/characters" not in name.lower():
                names.append(name)

    # Check for next page
    next_url = None
    next_link = soup.select_one("a.next_page") or soup.select_one("a[rel='next']")
    if next_link and next_link.get("href"):
        href = next_link["href"]
        if href.startswith("http"):
            next_url = href
        else:
            next_url = CAMPAIGN_URL + href

    return names, next_url


def fetch_all_names():
    """Fetch all character names, handling pagination."""
    session = requests.Session()
    all_names = []
    url = CHARACTERS_URL
    page = 0
    max_pages = 100

    while url and page < max_pages:
        page += 1
        names, next_url = scrape_characters_page(session, url)
        all_names.extend(names)
        url = next_url

    return all_names


def extract_personal_names(full_names):
    """Extract just the personal (given) name from full character names.
    E.g., 'Akodo no Damasu Chiho' -> 'Chiho'
    """
    personal = []
    for full in full_names:
        parts = full.strip().split()
        if parts:
            personal.append(parts[-1])
    return personal


if __name__ == "__main__":
    full_names = fetch_all_names()

    if not full_names:
        print("No characters found. The session cookie may be expired.", file=sys.stderr)
        sys.exit(1)

    personal_names = extract_personal_names(full_names)
    unique_personal = sorted(set(personal_names))

    output_path = "/workspace/.claude/skills/name/campaign-names.txt"
    with open(output_path, "w") as f:
        for name in unique_personal:
            f.write(name + "\n")

    print(f"Found {len(full_names)} characters, extracted {len(unique_personal)} unique personal names.")
    print(f"Saved to {output_path}")

    # Also print them for verification
    print("\nNames found:")
    for name in unique_personal:
        print(f"  {name}")
