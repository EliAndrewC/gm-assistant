"""The shrine builder's generation and wiki endpoints (feature 228), behind `Root.shrines`.

Each method takes plain inputs and returns `(status, json-able dict)`, so tests drive it with fake
Gemini and Obsidian Portal calls and no CherryPy request. The three that spend money or write to
the wiki (describe, draw, save) require a signed-in user; reading the prompt or the wiki page does
not. Nothing is stored on fly.io: a drawn picture lives in the browser until it is saved to the
wiki page (GM 2026-10-26).
"""

from __future__ import annotations

import base64
import binascii
import re
import time
from collections import deque
from collections.abc import Callable, Mapping
from io import BytesIO
from typing import Any

from l7r.lookup import gemini
from l7r.lookup.gemini import GeminiError
from l7r.shrines import art, describe, wiki
from l7r.shrines.catalog import Catalog
from l7r.shrines.design import Design, parse_design, share_query

__all__ = ['DESCRIPTION_CAP', 'Guard', 'PUBLIC_URL', 'ShrineServices', 'TEXT_MODEL']

TEXT_MODEL = 'gemini-3.1-flash-lite'
PUBLIC_URL = 'https://l7r-gm-assistant.fly.dev'
DESCRIPTION_CAP = 6000
IMAGE_CAP = 12_000_000  # bytes of base64: a 4:3 PNG from the image model is ~2 MB
LISTING_TTL = 120.0
# The two dashes the house style forbids, built from code points so this file never holds them.
_DASHES = re.compile(r'\s*[' + chr(0x2013) + chr(0x2014) + r']\s*')


class Guard:
    """Stops runaway or abusive request loops: at most `limit` calls per user per hour. Set far
    above anyone retrying by hand (spec US4.4: never a cap on ordinary retries)."""

    def __init__(self, limit: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._limit = limit
        self._clock = clock
        self._calls: dict[str, deque[float]] = {}

    def allow(self, user: str) -> bool:
        now = self._clock()
        calls = self._calls.setdefault(user, deque())
        while calls and now - calls[0] > 3600:
            calls.popleft()
        if len(calls) >= self._limit:
            return False
        calls.append(now)
        return True


def _query_params(query: object) -> dict[str, list[str]]:
    from urllib.parse import parse_qs

    return parse_qs(query if isinstance(query, str) else '', keep_blank_values=False)


def _png(data: bytes) -> bytes:
    """The picture as PNG (OP's upload is sent as image/png); ValueError if it is not an image."""
    from PIL import Image, UnidentifiedImageError

    try:
        image = Image.open(BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError('that is not a picture') from exc
    out = BytesIO()
    image.convert('RGB').save(out, format='PNG', optimize=True)
    return out.getvalue()


class ShrineServices:
    def __init__(
        self,
        catalog: Catalog,
        secrets: Callable[[], Mapping[str, Mapping[str, str]]],
        portal: Mapping[str, Callable[..., Any]] | None = None,
        text_call: Callable[..., Any] | None = None,
        image_call: Callable[..., tuple[bytes, str]] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._catalog = catalog
        self._secrets = secrets
        self._portal = portal
        self._text_call = text_call
        self._image_call = image_call
        self._clock = clock
        self.styles = art.load_styles()
        self.describe_guard = Guard(120, clock)
        self.draw_guard = Guard(60, clock)
        self._listing: tuple[float, list[Mapping[str, Any]]] | None = None

    # --- configuration ---------------------------------------------------------------------------

    def _setting(self, section: str, name: str, default: str = '') -> str:
        return str(self._secrets().get(section, {}).get(name, '') or default).strip()

    def _key(self) -> str:
        """The webapp's `[gemini] api_key`, the one chargen's portraits use."""
        return self._setting('gemini', 'api_key')

    def _calls(self) -> Mapping[str, Callable[..., Any]]:
        if self._portal is not None:
            return self._portal
        from chargen import op

        return {
            'list': op.existing_wiki_pages,
            'get': op.get_wiki_page,
            'create': op.create_wiki_page,
            'update': op.update_wiki_page,
            'upload': op.upload_image,
        }

    def style(self, key: object) -> art.Style | None:
        return next((s for s in self.styles if s.key == key), None)

    def design(self, query: object) -> Design:
        return parse_design(self._catalog, _query_params(query))

    def permalink(self, design: Design) -> str:
        base = self._setting('shrines', 'public_url', PUBLIC_URL).rstrip('/')
        return f'{base}/shrines?{share_query(self._catalog, design)}'

    # --- the picture's prompt (anyone) -----------------------------------------------------------

    def prompt(self, params: Mapping[str, object]) -> tuple[int, dict[str, Any]]:
        design = parse_design(self._catalog, params)
        return 200, {'prompt': art.image_prompt(self._catalog, design)}

    # --- signed-in, money-spending ---------------------------------------------------------------

    def describe(self, user: str, body: Mapping[str, Any]) -> tuple[int, dict[str, Any]]:
        if not self.describe_guard.allow(user):
            return 429, {'error': 'Too many descriptions this hour; try again later.'}
        key = self._key()
        if not key:
            return 503, {'error': 'Descriptions are not set up on this server.'}
        design = self.design(body.get('query'))
        call = self._text_call or gemini.generate
        model = self._setting('shrines', 'text_model', TEXT_MODEL)
        try:
            reply = call(
                key=key,
                model=model,
                system=describe.BRIEF,
                prompt=describe.design_text(self._catalog, design),
                thinking=self._setting('shrines', 'text_thinking', 'none'),
                temperature=0.9,
                timeout=60.0,
            )
        except GeminiError as exc:
            return 502, {'error': f'The description could not be written ({exc}).'}
        # house style: hyphens only (CLAUDE.md), whatever the model slips in
        text = _DASHES.sub(' - ', reply.text).strip()
        return 200, {'text': text}

    def draw(self, user: str, body: Mapping[str, Any]) -> tuple[int, dict[str, Any]]:
        style = self.style(body.get('style'))
        subject = body.get('prompt')
        if style is None or not isinstance(subject, str) or not subject.strip():
            return 400, {'error': 'Choose a style, and keep something in the prompt.'}
        if not self.draw_guard.allow(user):
            return 429, {'error': 'Too many pictures this hour; try again later.'}
        key = self._key()
        if not key:
            return 503, {'error': 'Pictures are not set up on this server.'}
        call = self._image_call or art.draw
        default_model = self._setting('gemini', 'image_model', 'gemini-3.1-flash-image')
        try:
            data, mime = call(
                key=key,
                model=self._setting('shrines', 'image_model', default_model),
                prompt=art.style_prompt(style, subject),
            )
        except GeminiError as exc:
            return 502, {'error': f'The picture could not be drawn ({exc}).'}
        return 200, {'image': base64.b64encode(data).decode('ascii'), 'mime': mime}

    # --- the wiki page ---------------------------------------------------------------------------

    def _pages(self, fresh: bool = False) -> list[Mapping[str, Any]]:
        now = self._clock()
        if fresh or self._listing is None or now - self._listing[0] > LISTING_TTL:
            pages = list(self._calls()['list']())
            if not pages:  # the campaign has many pages; none at all means OP did not answer
                raise ConnectionError('Obsidian Portal returned no wiki pages')
            self._listing = (now, pages)
        return self._listing[1]

    def _saved(self, name: str, fresh: bool = False) -> wiki.Saved | None:
        entry = wiki.find_page(name, self._pages(fresh))
        if entry is None:
            return None
        return wiki.parse_page(self._calls()['get'](entry['id']))

    def wiki_get(self, params: Mapping[str, object]) -> tuple[int, dict[str, Any]]:
        design = parse_design(self._catalog, params)
        try:
            saved = self._saved(design.text.get('shrine_name', ''))
        except Exception as exc:  # noqa: BLE001 - any OP failure: say so, never break the page
            return 200, {'error': f'Could not check the wiki ({type(exc).__name__}).'}
        if saved is None:
            return 200, {'found': False}
        theirs = parse_design(self._catalog, saved.params)
        return 200, {
            'found': True,
            'url': saved.url,
            'matches': share_query(self._catalog, theirs) == share_query(self._catalog, design),
            'description': saved.description,
            'image_url': saved.image_url,
            'style': saved.style,
            'prompt': saved.prompt,
        }

    def wiki_save(self, user: str, body: Mapping[str, Any]) -> tuple[int, dict[str, Any]]:
        design = self.design(body.get('query'))
        name = design.text.get('shrine_name', '').strip()
        description = str(body.get('description') or '').strip()[:DESCRIPTION_CAP]
        style = self.style(body.get('style'))
        prompt = str(body.get('prompt') or '').strip()[: art.PROMPT_CAP]
        image = body.get('image') or ''
        if not name or not description:
            return 400, {'error': 'The shrine needs a name and a description.'}
        if not isinstance(image, str) or len(image) > IMAGE_CAP:
            return 400, {'error': 'That picture is too large.'}
        try:
            saved = self._saved(name, fresh=True)
            if saved is None and not image:
                needs = (
                    'Draw a picture first: the wiki page needs both a picture and a description.'
                )
                return 400, {'error': needs}
            calls = self._calls()
            image_line = saved.image_line if saved is not None else ''
            if image:
                png = _png(base64.b64decode(image, validate=True))
                filename = re.sub(r'[^A-Za-z0-9]', '', name.title())[:60] + '.png'
                file_id = calls['upload'](png, filename).get('id')
                if not file_id:
                    return 502, {'error': 'Obsidian Portal did not accept the picture.'}
                image_line = f'[[File:{file_id} | class=media-item-align-none | {filename}]]'
            page_body = wiki.build_body(image_line, description, self.permalink(design))
            style_key = style.key if style is not None else ''
            if saved is None:
                page = calls['create'](
                    name,
                    body=page_body,
                    game_master_info=wiki.build_gm_info(style_key, prompt),
                    tags=[wiki.TAG],
                )
                url = str(page.get('wiki_page_url') or '')
            else:
                existing = calls['get'](saved.page_id)
                calls['update'](
                    saved.page_id,
                    body=page_body,
                    game_master_info=wiki.merge_gm_info(
                        str(existing.get('game_master_info') or ''), style_key, prompt
                    ),
                )
                url = saved.url
        except (ValueError, binascii.Error) as exc:
            return 400, {'error': f'That picture could not be read ({exc}).'}
        except Exception as exc:  # noqa: BLE001 - report OP failures to the player, not a 500 page
            return 502, {'error': f'Obsidian Portal refused the page ({type(exc).__name__}).'}
        self._listing = None
        return 200, {'url': url, 'created': saved is None}
