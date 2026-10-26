"""Feature 228: the description, the picture and the shrine's wiki page - the pure parts, the
services with fake Gemini and Obsidian Portal calls, and the routes' sign-in gate."""

from __future__ import annotations

import base64
import io
import json
import re
import urllib.error
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from urllib.parse import parse_qs

import cherrypy
import pytest
from PIL import Image

from l7r.app import Root
from l7r.auth import CurrentUser
from l7r.lookup.gemini import GeminiError
from l7r.shrines import Catalog, art, describe, load_catalog, parse_design, wiki
from l7r.shrines.access import CostAccess
from l7r.shrines.web import PUBLIC_URL, Guard, ShrineServices
from tests.test_shrines import DEFAULT_FRAMING, price_words

SECRETS = {'gemini': {'api_key': 'k'}}
EM, EN = chr(0x2014), chr(0x2013)
QUERY = 'shrine_name=The+Fox+Rest&kind=kami&form=hokora&bell=suzu&other_bell=a+conch'


@pytest.fixture(scope='module')
def catalog() -> Catalog:
    return load_catalog()


def jpeg() -> bytes:
    out = io.BytesIO()
    Image.new('RGB', (4, 3), 'white').save(out, format='JPEG')  # the model often answers in JPEG
    return out.getvalue()


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


# --- the picture's prompt -------------------------------------------------------------------------


def test_styles_are_player_text() -> None:
    styles = art.load_styles()
    assert len(styles) >= 4
    assert len({s.key for s in styles}) == len(styles)
    for s in styles:
        assert price_words(f'{s.label} {s.note}') == []
        assert not DEFAULT_FRAMING.search(s.note)


def test_image_prompt_follows_the_choices(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {
            'kind': 'memorial',
            'sharing': ['headmound', 'temple'],
            'guardians': 'foxes',
            'bell': 'suzu',
            'other_bell': 'a conch shell on a cord',
            'lanterns': 'pair',
            'other_lanterns': 'paper lanterns strung through the trees',
            'instead_lanterns': '1',
            'rite': 'full',
        },
    )
    prompt = art.image_prompt(catalog, design)
    foxes = catalog.category('guardians').option('foxes')  # type: ignore[union-attr]
    pair = catalog.category('lanterns').option('pair')  # type: ignore[union-attr]
    assert foxes is not None
    assert pair is not None
    assert f'- {foxes.look}' in prompt
    assert '- a conch shell on a cord' in prompt
    assert '- paper lanterns strung through the trees' in prompt
    assert pair.look not in prompt  # "instead" replaces the step's own look
    assert '- \n' not in prompt  # options with nothing to see add no empty line
    assert (
        prompt.index('conch') < prompt.index('foxes') < prompt.index('paper lanterns')
    )  # wizard order
    assert 'No people' in prompt


def test_style_prompt_puts_the_style_first_and_caps_the_subject() -> None:
    style = art.load_styles()[0]
    text = art.style_prompt(style, '  ' + 'x' * (art.PROMPT_CAP + 50))
    assert text.startswith(style.preamble + '\n\n')
    assert len(text) == len(style.preamble) + 2 + art.PROMPT_CAP


def opener_for(payload: dict[str, Any], seen: list[Any] | None = None) -> Any:
    """A saved Gemini response body, standing in for the HTTP response."""

    def opener(request: Any, timeout: float) -> io.BytesIO:
        if seen is not None:
            seen.append(request)
        return io.BytesIO(json.dumps(payload).encode())

    return opener


def test_draw_returns_the_inline_image() -> None:
    image = jpeg()
    parts = [{'text': 'Here it is'}, {'inlineData': {'mimeType': 'image/jpeg', 'data': b64(image)}}]
    seen: list[Any] = []
    payload = {'candidates': [{'content': {'parts': parts}}]}
    data, mime = art.draw(key='k', model='m', prompt='p', opener=opener_for(payload, seen))
    assert (data, mime) == (image, 'image/jpeg')
    body = json.loads(seen[0].data)
    assert body['generationConfig'] == {
        'responseModalities': ['IMAGE'],
        'imageConfig': {'aspectRatio': '4:3'},
    }
    assert seen[0].get_header('X-goog-api-key') == 'k'


@pytest.mark.parametrize(
    ('payload', 'message'),
    [
        (
            {'candidates': [{'finishReason': 'SAFETY', 'content': {'parts': [{'text': 'no'}]}}]},
            'SAFETY',
        ),
        ({}, 'no candidates'),
    ],
)
def test_draw_without_an_image_fails(payload: dict[str, Any], message: str) -> None:
    with pytest.raises(GeminiError, match=message):
        art.draw(key='k', model='m', prompt='p', opener=opener_for(payload))


def test_draw_transport_failures_never_carry_the_key() -> None:
    def http_error(request: Any, timeout: float) -> io.BytesIO:
        raise urllib.error.HTTPError(request.full_url, 400, 'bad', {}, None)  # type: ignore[arg-type]

    def down(request: Any, timeout: float) -> io.BytesIO:
        raise urllib.error.URLError('down')

    with pytest.raises(GeminiError, match='HTTP 400') as exc:
        art.draw(key='secret', model='m', prompt='p', opener=http_error)
    assert 'secret' not in str(exc.value)
    with pytest.raises(GeminiError, match='URLError'):
        art.draw(key='secret', model='m', prompt='p', opener=down)


# --- the description ------------------------------------------------------------------------------


def test_design_text_uses_the_wording_and_the_players_words(catalog: Catalog) -> None:
    design = parse_design(
        catalog,
        {
            'shrine_name': 'The Fox Rest',
            'kind': 'memorial',
            'heart': 'bones',
            'sharing': ['headmound', 'temple'],
            'bell': 'suzu',
            'other_bell': 'a conch',
            'other_roof': 'turf',
            'instead_roof': '1',
        },
    )
    text = describe.design_text(catalog, design)
    assert text.startswith('Name of the shrine: The Fox Rest')
    assert "The player's own words, as well: a conch" in text
    assert "The player's own words, instead of the listed choices: turf" in text
    assert text.count('- The head under a mound of its own') == 1
    assert 'Timber' not in text  # not answered
    assert 'sacred' in design.inactive
    assert 'Sacred object' not in text


def test_brief_is_short_and_carries_the_house_style() -> None:
    assert len(describe.BRIEF.split()) < 400
    assert 'never em or en dashes' in describe.BRIEF
    assert 'No prices' in describe.BRIEF


# --- the wiki page --------------------------------------------------------------------------------


def test_body_round_trips() -> None:
    body = wiki.build_body(
        '[[File:7 | class=media-item-align-none | A.png]]',
        'One\ntwo.\n\n\nThree.',
        'https://x/shrines?kind=kami&bell=suzu',
    )
    assert body == (
        '[[File:7 | class=media-item-align-none | A.png]]\r\n\r\nOne two.\r\n\r\nThree.\r\n\r\n'
        '"Open this shrine in the Shrine Builder":https://x/shrines?kind=kami&bell=suzu'
    )
    saved = wiki.parse_page(
        {
            'id': 12,
            'wiki_page_url': 'https://op/wiki_pages/a',
            'body': body,
            'body_html': '<p><img class="x" src="https://cdn/a.png?1&amp;2" /></p>',
            'game_master_info': wiki.merge_gm_info('', 'ink', 'a\nb'),
        }
    )
    assert saved.page_id == '12'
    assert saved.description == 'One two.\n\nThree.'
    assert saved.image_line.startswith('[[File:7')
    assert saved.image_url == 'https://cdn/a.png?1&2'
    assert (saved.style, saved.prompt) == ('ink', 'a\nb')
    assert saved.params == {'kind': ['kami'], 'bell': ['suzu']}


def test_gm_notes_keep_what_the_gm_wrote() -> None:
    first = wiki.merge_gm_info('The GM wrote this.', 'ink', 'one')
    assert first.startswith('The GM wrote this.\r\n\r\n-- shrine builder')
    second = wiki.merge_gm_info(first + '\r\nAnd this.', 'woodblock', 'two')
    assert 'The GM wrote this.' in second
    assert 'And this.' in second
    assert 'style: woodblock' in second
    assert 'one' not in second


def test_a_page_the_gm_rewrote_still_parses() -> None:
    saved = wiki.parse_page({'body': 'Just prose.\r\n\r\nMore.', 'game_master_info': None})
    assert saved == wiki.Saved('', '', {}, 'Just prose.\n\nMore.', '', '', '', '')


def test_find_page_needs_the_name_and_the_tag() -> None:
    pages = [
        {'id': 1, 'name': 'The Fox Rest', 'tags': []},
        {'id': 2, 'name': 'the  fox rest', 'tags': ['shrine']},
    ]
    assert wiki.find_page(' The Fox  Rest ', pages) == pages[1]
    assert wiki.find_page('Elsewhere', pages) is None


# --- the services ---------------------------------------------------------------------------------


class FakePortal:
    """Obsidian Portal as the shrine builder sees it: a listing, pages, uploads."""

    def __init__(self) -> None:
        self.pages: dict[str, dict[str, Any]] = {}
        self.uploads: list[tuple[bytes, str]] = []
        self.listed = 0
        self.other_pages: list[dict[str, Any]] = [{'id': 'x', 'name': 'Ubame County', 'tags': []}]
        self.file_id: int | None = 901

    def calls(self) -> dict[str, Any]:
        return {
            'list': self.listing,
            'get': lambda pid: self.pages[pid],
            'create': self.create,
            'update': self.update,
            'upload': self.upload,
        }

    def listing(self) -> list[dict[str, Any]]:
        self.listed += 1
        mine = [{'id': p['id'], 'name': p['name'], 'tags': p['tags']} for p in self.pages.values()]
        return self.other_pages + mine if self.other_pages else []

    def create(
        self, name: str, *, body: str, game_master_info: str, tags: list[str]
    ) -> dict[str, Any]:
        pid = f'p{len(self.pages) + 1}'
        self.pages[pid] = {
            'id': pid,
            'name': name,
            'tags': tags,
            'body': body,
            'body_html': '<img src="https://cdn/pic.png">' if '[[File:' in body else '',
            'game_master_info': game_master_info,
            'wiki_page_url': f'https://op/wiki_pages/{pid}',
        }
        return self.pages[pid]

    def update(self, pid: str, **fields: Any) -> None:
        self.pages[pid].update(fields)

    def upload(self, data: bytes, filename: str) -> dict[str, Any]:
        self.uploads.append((data, filename))
        return {'id': self.file_id} if self.file_id else {}


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def portal() -> FakePortal:
    return FakePortal()


def services(
    catalog: Catalog,
    portal: FakePortal | None = None,
    secrets: dict[str, dict[str, str]] = SECRETS,
    **kw: Any,
) -> ShrineServices:
    return ShrineServices(
        catalog,
        lambda: secrets,
        portal=(portal or FakePortal()).calls(),
        text_call=kw.get('text_call'),
        image_call=kw.get('image_call'),
        clock=kw.get('clock', Clock()),
    )


def test_guard_stops_only_a_runaway_loop() -> None:
    clock = Clock()
    guard = Guard(3, clock)
    assert [guard.allow('a') for _ in range(4)] == [True, True, True, False]
    assert guard.allow('b')
    clock.now += 3601
    assert guard.allow('a')


def test_describe_sends_the_brief_and_the_design(catalog: Catalog) -> None:
    seen: dict[str, Any] = {}

    def text_call(**kw: Any) -> Any:
        seen.update(kw)
        return SimpleNamespace(text=f'A path{EM}then a shrine {EN} quiet.')

    svc = services(catalog, text_call=text_call)
    assert svc.describe('u', {'query': QUERY}) == (200, {'text': 'A path - then a shrine - quiet.'})
    assert seen['key'] == 'k'
    assert seen['model'] == 'gemini-3.1-flash-lite'
    assert seen['system'] == describe.BRIEF
    assert 'own words, as well: a conch' in seen['prompt']
    assert seen['temperature'] > 0.5  # pressing again writes a different description


def test_describe_failures(catalog: Catalog) -> None:
    def broken(**kw: Any) -> Any:
        raise GeminiError('m: HTTP 500')

    assert services(catalog, text_call=broken).describe('u', {})[0] == 502
    unset = services(catalog, secrets={}, text_call=broken)
    assert unset.describe('u', {}) == (
        503,
        {'error': 'Descriptions are not set up on this server.'},
    )
    svc = services(catalog, text_call=broken)
    svc.describe_guard = Guard(0)
    assert svc.describe('u', {})[0] == 429


def test_describe_calls_gemini_by_default(
    catalog: Catalog, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, Any] = {}

    def generate(**kw: Any) -> Any:
        seen.update(kw)
        return SimpleNamespace(text='ok')

    monkeypatch.setattr('l7r.lookup.gemini.generate', generate)
    assert services(catalog).describe('u', {'query': QUERY})[0] == 200
    assert seen['key'] == 'k'


def test_draw(catalog: Catalog, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def draw(**kw: Any) -> tuple[bytes, str]:
        seen.update(kw)
        return b'img', 'image/png'

    monkeypatch.setattr(art, 'draw', draw)
    svc = services(catalog)
    status, answer = svc.draw('u', {'prompt': 'the foxes by the gate', 'style': 'woodblock'})
    assert (status, answer) == (200, {'image': b64(b'img'), 'mime': 'image/png'})
    style = svc.style('woodblock')
    assert style is not None
    assert seen['prompt'].startswith(style.preamble)
    assert seen['prompt'].endswith('the foxes by the gate')
    assert seen['model'] == 'gemini-3.1-flash-image'


def test_draw_failures(catalog: Catalog) -> None:
    def broken(**kw: Any) -> tuple[bytes, str]:
        raise GeminiError('m: no image (SAFETY)')

    svc = services(catalog, image_call=broken)
    assert svc.draw('u', {'prompt': 'x', 'style': 'nope'})[0] == 400
    assert svc.draw('u', {'prompt': '  ', 'style': 'ink'})[0] == 400
    assert svc.draw('u', {'prompt': 'x', 'style': 'ink'})[0] == 502
    unset = services(catalog, secrets={}, image_call=broken)
    assert unset.draw('u', {'prompt': 'x', 'style': 'ink'})[0] == 503
    svc.draw_guard = Guard(0)
    assert svc.draw('u', {'prompt': 'x', 'style': 'ink'})[0] == 429


def test_prompt_needs_no_sign_in(catalog: Catalog) -> None:
    status, answer = services(catalog).prompt({'guardians': 'foxes'})
    assert status == 200
    assert 'stone foxes' in answer['prompt']


def test_save_then_find_then_update(catalog: Catalog, portal: FakePortal) -> None:
    svc = services(catalog, portal)
    assert svc.wiki_get(parse_qs(QUERY)) == (200, {'found': False})

    status, answer = svc.wiki_save(
        'u',
        {
            'query': QUERY,
            'description': 'Moss.\n\nFoxes.',
            'style': 'ink',
            'prompt': 'p1',
            'image': b64(jpeg()),
        },
    )
    assert (status, answer) == (200, {'url': 'https://op/wiki_pages/p1', 'created': True})
    page = portal.pages['p1']
    assert page['name'] == 'The Fox Rest'
    assert page['tags'] == ['shrine']
    assert page['body'].startswith('[[File:901 | class=media-item-align-none | TheFoxRest.png]]')
    assert f'"Open this shrine in the Shrine Builder":{PUBLIC_URL}/shrines?' in page['body']
    assert portal.uploads[0][0].startswith(b'\x89PNG')  # converted from the model's JPEG

    assert svc.wiki_get(parse_qs(QUERY)) == (
        200,
        {
            'found': True,
            'url': 'https://op/wiki_pages/p1',
            'matches': True,
            'description': 'Moss.\n\nFoxes.',
            'image_url': 'https://cdn/pic.png',
            'style': 'ink',
            'prompt': 'p1',
        },
    )
    # order and spelling do not matter; a different choice does
    reordered = 'other_bell=a+conch&bell=suzu&form=hokora&kind=kami&shrine_name=The+Fox+Rest'
    assert svc.wiki_get(parse_qs(reordered))[1]['matches']
    changed = QUERY.replace('hokora', 'nagare')
    assert svc.wiki_get(parse_qs(changed))[1]['matches'] is False

    # an update with no new picture keeps the page's picture and the GM's own notes
    page['game_master_info'] = 'GM: Shizu paid extra.\r\n\r\n' + page['game_master_info']
    status, answer = svc.wiki_save(
        'u', {'query': changed, 'description': 'New.', 'style': 'screen', 'prompt': 'p2'}
    )
    assert (status, answer) == (200, {'url': 'https://op/wiki_pages/p1', 'created': False})
    assert page['body'].startswith('[[File:901 |')
    assert '\r\n\r\nNew.\r\n\r\n' in page['body']
    assert 'GM: Shizu paid extra.' in page['game_master_info']
    assert 'p2' in page['game_master_info']
    assert len(portal.uploads) == 1
    assert svc.wiki_get(parse_qs(changed))[1]['matches'] is True


def test_wiki_listing_is_cached_briefly(catalog: Catalog, portal: FakePortal) -> None:
    clock = Clock()
    svc = services(catalog, portal, clock=clock)
    svc.wiki_get(parse_qs(QUERY))
    svc.wiki_get(parse_qs(QUERY))
    assert portal.listed == 1
    clock.now += 121
    svc.wiki_get(parse_qs(QUERY))
    assert portal.listed == 2


def test_save_refusals(catalog: Catalog, portal: FakePortal) -> None:
    svc = services(catalog, portal)
    good = {'query': QUERY, 'description': 'x', 'style': 'ink', 'prompt': 'p', 'image': b64(jpeg())}
    assert svc.wiki_save('u', {**good, 'description': ' '})[0] == 400
    assert svc.wiki_save('u', {**good, 'image': 'x' * 12_000_001})[0] == 400
    assert svc.wiki_save('u', {**good, 'image': ''}) == (
        400,
        {'error': 'Draw a picture first: the wiki page needs both a picture and a description.'},
    )
    assert svc.wiki_save('u', {**good, 'image': '!!'})[0] == 400  # not base64
    assert svc.wiki_save('u', {**good, 'image': b64(b'hello')})[0] == 400  # not a picture
    portal.file_id = None
    assert svc.wiki_save('u', good) == (
        502,
        {'error': 'Obsidian Portal did not accept the picture.'},
    )
    assert portal.pages == {}


def test_obsidian_portal_down(catalog: Catalog, portal: FakePortal) -> None:
    portal.other_pages = []
    svc = services(catalog, portal)
    assert svc.wiki_get(parse_qs(QUERY)) == (
        200,
        {'error': 'Could not check the wiki (ConnectionError).'},
    )
    good = {'query': QUERY, 'description': 'x', 'style': 'ink', 'image': b64(jpeg())}
    assert svc.wiki_save('u', good) == (
        502,
        {'error': 'Obsidian Portal refused the page (ConnectionError).'},
    )


def test_default_portal_is_chargen_op(catalog: Catalog) -> None:
    from chargen import op

    calls = ShrineServices(catalog, lambda: {})._calls()
    assert calls['create'] is op.create_wiki_page
    assert calls['upload'] is op.upload_image


def test_permalink_base_is_configurable(catalog: Catalog) -> None:
    svc = services(catalog, secrets={'shrines': {'public_url': 'http://localhost:8080/'}})
    link = svc.permalink(svc.design('kind=kami'))
    assert link.startswith('http://localhost:8080/shrines?kind=kami')


# --- the routes -----------------------------------------------------------------------------------


@pytest.fixture
def root(catalog: Catalog, portal: FakePortal) -> Iterator[Root]:
    svc = services(
        catalog,
        portal,
        text_call=lambda **kw: SimpleNamespace(text='A quiet shrine.'),
        image_call=lambda **kw: (b'img', 'image/png'),
    )
    yield Root(
        relics=[],
        shrine_catalog=catalog,
        cost_access=CostAccess(lambda: 't', lambda t: {'characters': []}),
        shrine_services=svc,
    )
    if hasattr(cherrypy.request, 'l7r_user'):
        del cherrypy.request.l7r_user
    cherrypy.request.method = 'GET'


def respond(root: Root, action: str, method: str, body: object = None, **params: Any) -> Any:
    """(status, JSON answer) of one call to /shrines/<action>."""
    cherrypy.request.method = method
    raw = body if isinstance(body, bytes) else json.dumps(body or {}).encode()
    cherrypy.request.body = SimpleNamespace(read=lambda: raw)
    cherrypy.response.status = 200
    answer = json.loads(root.shrines(action, **params))
    return cherrypy.response.status, answer


def sign_in(role: str = 'player') -> None:
    cherrypy.request.l7r_user = CurrentUser('42', 'Shizu', role)  # type: ignore[arg-type]


@pytest.mark.parametrize('action', ['describe', 'draw', 'wiki'])
def test_spending_and_writing_need_a_sign_in(root: Root, action: str) -> None:
    assert respond(root, action, 'POST', {'query': QUERY}) == (
        401,
        {'error': 'Sign in to do that.'},
    )


def test_signed_in_player_can_describe_draw_and_save(root: Root) -> None:
    sign_in()
    assert respond(root, 'describe', 'POST', {'query': QUERY}) == (200, {'text': 'A quiet shrine.'})
    status, answer = respond(root, 'draw', 'POST', {'prompt': 'x', 'style': 'ink'})
    assert status == 200
    assert answer['mime'] == 'image/png'
    body = {'query': QUERY, 'description': 'd', 'style': 'ink', 'image': b64(jpeg())}
    status, answer = respond(root, 'wiki', 'POST', body)
    assert (status, answer['created']) == (200, True)


def test_reading_needs_no_sign_in(root: Root) -> None:
    status, answer = respond(root, 'prompt', 'GET', guardians='foxes')
    assert status == 200
    assert 'stone foxes' in answer['prompt']
    assert respond(root, 'wiki', 'GET', shrine_name='Nowhere') == (200, {'found': False})


def test_bad_requests(root: Root) -> None:
    sign_in()
    assert respond(root, 'describe', 'POST', b'{nope')[0] == 400
    assert respond(root, 'describe', 'POST', b'[1]')[0] == 400
    assert respond(root, 'describe', 'GET')[0] == 404
    assert respond(root, 'paint', 'POST')[0] == 404


def test_old_spellings_redirect(catalog: Catalog, root: Root) -> None:
    root._shrine_catalog = SimpleNamespace(  # type: ignore[assignment]
        legacy_steps={'torii': 'gate_form'}, legacy_options={}
    )
    cherrypy.request.method = 'GET'
    with pytest.raises(cherrypy.HTTPRedirect) as redirect:
        root.shrines(torii='myojin', kind='kami')
    assert redirect.value.status == 303
    assert redirect.value.urls[0].endswith('/shrines?gate_form=myojin&kind=kami')


def test_page_carries_the_studio_only_for_signed_in_users(root: Root) -> None:
    cherrypy.request.method = 'GET'
    anon = root.shrines(**parse_qs(QUERY)).decode()
    assert 'data-studio data-signed-in="false"' in anon
    for control in ('data-describe', 'data-draw', 'data-save'):
        assert control not in anon
    assert 'data-signin>Sign in</a> to describe' in anon
    assert 'plus a conch' in anon  # the summary shows the player's own words
    sign_in()
    page = root.shrines(**parse_qs(QUERY)).decode()
    for control in ('data-describe', 'data-draw', 'data-save'):
        assert control in page
    # the studio's fields belong to their own form, so they never reach the design's link
    fields = re.findall(
        r'<(?:textarea|input)[^>]*(?:data-description|data-prompt|name="art_style")[^>]*>', page
    )
    assert len(fields) == 2 + len(art.load_styles())
    assert all('form="shrine-studio"' in f for f in fields)


def test_gm_ledger_prices_other_work(root: Root) -> None:
    sign_in('gm')
    cherrypy.request.method = 'GET'
    page = root.shrines(**parse_qs(QUERY)).decode()
    assert 'name="gm_other_bell"' in page
    assert 'placeholder="unpriced"' in page
    assert '+ 1 unpriced' in page
    assert 'less 1 unpriced' in page
    priced = root.shrines(**parse_qs(QUERY + '&gm_other_bell=2')).decode()
    assert '+ 1 unpriced' not in priced
    assert 'value="2"' in priced
