"""CherryPy application root for the L7R Toolkit.

Routes:
- GET /                landing page
- GET /relics          all 42 relics grouped by Fortune
- GET /relics/<slug>   single relic detail
- GET /names           pre-generated Rokugani names with filters
- GET /places          pre-generated place names with filters
- GET /places/<slug>   single place detail
- GET /dreams          dream-divination framework + example gallery
- GET /dreams/<slug>   single worked dream-omen example
- GET /api/names       JSON name suggestions for the character-sheet app's generated NPCs
                       (feature 213; bearer-token auth, `[character_sheet] names_token`)
- POST /api/npc-numbers  a character-sheet NPC's built stats into its Obsidian Portal record's
                       `NPC numbers:` block (feature 226; the same bearer token)
- /chargen/*           mounted chargen Root (legacy)
- /static/*            static assets

Importing THIS module wires the CherryPy tree - `cherryd --import l7r.app` is how the app starts,
and anything that wants the tree mounted (conftest, the character tests, the opcache refresh)
imports `l7r.app` rather than `l7r`.

`l7r` itself is a PEP 420 namespace portion with no code in it (feature 119 made it one so the
diagram engine's `l7r.diagram.*` could share the parent package; that engine has been in its own
repository since feature 131). It must not gain an `__init__.py` casually - the mypy configuration
is built around the namespace shape. `tests/test_namespace_portion.py` guards this and says what
retiring it would take.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import cherrypy
from jinja2 import Environment

from l7r import sheetnames
from l7r.auth import AuthConfig, load_auth_config
from l7r.auth_routes import AuthRoot, current_user, install_auth_tool
from l7r.dreams import DreamScene, find_scene_by_slug, load_dream_scenes, render_markdown
from l7r.fortunes import FORTUNES
from l7r.jinja_env import build_environment
from l7r.money import basket as money_basket
from l7r.money import ledger as money_ledger
from l7r.money import prices as money_prices
from l7r.money import web as money_web
from l7r.money.readings import (
    DAY_RICE_KG,
    LABORER_DAY_SEN,
    LABORER_KOKU_YEAR,
    load_wages,
    resolve_koku_kg,
    wage_dollars_per_koku,
)
from l7r.names import (
    GeneratedName,
    find_name_by_slug,
    load_names,
    random_name,
)
from l7r.notes_markup import load_wiki_links, render_notes
from l7r.places import (
    COMMONALITIES,
    PLACE_TYPES,
    REGIONAL_CONTEXTS,
    Place,
    filter_places,
    find_place_by_slug,
    load_places,
    random_place,
)
from l7r.pool import Relic, load_relics
from l7r.research import ResearchSite
from l7r.sections import SECTIONS
from l7r.shrines import (
    TEXT_FIELDS,
    Catalog,
    default_budget,
    format_koku,
    format_number,
    gm_query,
    load_catalog,
    moot_note,
    negotiate,
    option_effects,
    option_offered,
    parse_design,
    parse_negotiation,
    rules_json,
    share_query,
)
from l7r.shrines.access import CostAccess
from l7r.slugs import find_relic_by_slug, neighbors_in_fortune, relics_for_fortune

logger = logging.getLogger(__name__)

_HERE = Path(__file__).parent


def _resolve_default_pool_dir() -> Path:
    """Resolve the relic pool directory.

    Production deploys override with `L7R_RELIC_POOL_DIR`. In development we
    walk up to `.claude/skills/relic/pool` relative to the package.
    """
    import os

    env_override = os.environ.get('L7R_RELIC_POOL_DIR')
    if env_override:
        return Path(env_override)
    return (_HERE.parent.parent / '.claude' / 'skills' / 'relic' / 'pool').resolve()


def _resolve_default_names_dir() -> Path:
    """Resolve the names pool directory."""
    import os

    env_override = os.environ.get('L7R_NAMES_DIR')
    if env_override:
        return Path(env_override)
    return (_HERE.parent.parent / '.claude' / 'skills' / 'name').resolve()


def _resolve_default_places_dir() -> Path:
    """Resolve the places pool directory."""
    import os

    env_override = os.environ.get('L7R_PLACES_DIR')
    if env_override:
        return Path(env_override)
    return (_HERE.parent.parent / '.claude' / 'skills' / 'place-names').resolve()


def _resolve_default_dream_pool_dir() -> Path:
    """Resolve the PUBLIC dream-scene pool directory.

    Production deploys override with `L7R_DREAM_POOL_DIR`. In development we
    walk up to `.claude/skills/dream/pool` relative to the package. Only the
    public `pool/` tier is ever pointed at; the gitignored `pool-local/` tier
    is never read (feature 011, FR-007).
    """
    import os

    env_override = os.environ.get('L7R_DREAM_POOL_DIR')
    if env_override:
        return Path(env_override)
    return (_HERE.parent.parent / '.claude' / 'skills' / 'dream' / 'pool').resolve()


_DEFAULT_POOL_DIR = _resolve_default_pool_dir()
_DEFAULT_NAMES_DIR = _resolve_default_names_dir()
_DEFAULT_PLACES_DIR = _resolve_default_places_dir()
_DEFAULT_DREAM_POOL_DIR = _resolve_default_dream_pool_dir()
_DREAM_FRAMEWORK_PATH = _HERE / 'content' / 'dreams_framework.md'


def _group_relics_by_fortune(relics: list[Relic]) -> dict[str, list[Relic]]:
    """Group relics into a fortune-keyed dict, with all FORTUNES keys present."""
    return {slug: relics_for_fortune(relics, slug) for slug in FORTUNES}


def _build_filter_qs(
    *,
    place_type: str | None,
    commonality: str | None,
    regional: str | None,
    suffix: str | None,
) -> str:
    """Build the canonical query string for active /places filters.

    Action params (random, via) are excluded - this is the filter context only,
    used by templates to build links that preserve filter state across
    navigation between the index and detail pages.
    """
    parts: list[str] = []
    if place_type:
        parts.append(f'place_type={place_type}')
    if commonality:
        parts.append(f'commonality={commonality}')
    if regional:
        parts.append(f'regional={regional}')
    if suffix:
        parts.append(f'suffix={suffix}')
    return '&'.join(parts)


def _build_names_filter_qs(
    *,
    gender: str | None,
    caste: str | None,
) -> str:
    """Build the canonical query string for active /names filters.

    Same role as _build_filter_qs but for the names axes (gender, caste).
    """
    parts: list[str] = []
    if gender:
        parts.append(f'gender={gender}')
    if caste:
        parts.append(f'caste={caste}')
    return '&'.join(parts)


def _clans_with_relics(relics: list[Relic]) -> list[str]:
    """Sorted unique clan slugs present in the relic pool.

    Used to render the clan filter rail - only show buttons for clans that
    actually have at least one relic, so the rail adapts as the pool grows.
    """
    return sorted({r.clan for r in relics})


class NamesApi:
    """`/api/*`: token-authenticated JSON for the character-sheet app (features 213 and 226).

    The session tool leaves `/api` open (mount config); THIS handler is the whole gate. The
    token is `[character_sheet] names_token`, INBOUND - the sheet app presents it to us - and is
    read at request time through `token`, so a test (or a secrets change) reaches it. Both
    routes take it: one caller, the sheet app, on one server (feature 226's spec declined a
    second secret, which the GM would have had to copy into both apps by hand).

    `portal` is the Obsidian Portal boundary `/api/npc-numbers` writes through - `characters`,
    `get_body`, `update`, as `npcbackport.backport` takes them - `chargen.op` when not given.
    """

    def __init__(
        self,
        token: Callable[[], str],
        portal: Mapping[str, Callable[..., Any]] | None = None,
    ) -> None:
        self._token = token
        self._portal = portal

    def _denied(self) -> bytes | None:
        """The gate, before any parsing and any Obsidian Portal call; None lets the caller in."""
        cherrypy.response.headers['Content-Type'] = 'application/json'
        configured = self._token().strip()
        if not configured:  # fail closed: no secret configured means nobody gets in
            return _json_error(503, 'names API is not configured on this server')
        header = cherrypy.request.headers.get('Authorization', '')
        # Header only: a `token=` query parameter lands in **_ignored and counts for nothing.
        if not sheetnames.token_matches(header, configured):
            cherrypy.response.headers['WWW-Authenticate'] = 'Bearer'
            return _json_error(401, 'missing or invalid bearer token')
        return None

    # GET /api/names?count=N&peasant=true|false&avoid=A,B
    @cherrypy.expose
    def names(
        self,
        count: str | None = None,
        peasant: str | None = None,
        avoid: str | list[str] | None = None,
        **_ignored: Any,
    ) -> bytes:
        denied = self._denied()
        if denied is not None:
            return denied
        # Auth before parsing and before the refresh: an unauthenticated caller can neither
        # probe the parameters nor make this app walk Obsidian Portal.
        try:
            n = sheetnames.parse_count(count)
            is_peasant = sheetnames.parse_peasant(peasant)
        except ValueError as e:
            return _json_error(400, str(e))
        from chargen import namepool, opcache

        sheetnames.refresh_used_names()
        picks = sheetnames.suggest_names(
            n,
            peasant=is_peasant,
            pool=namepool.load_pool(namepool.pool_dir()),
            used=opcache.used_given_names(),
            avoid=sheetnames.parse_avoid(avoid),
        )
        return json.dumps({'names': picks}).encode('utf-8')

    # POST /api/npc-numbers  {"name": str, "stats": {str: int}, "sheet_id": int?}
    # (CherryPy's default dispatcher maps the `-` in the path to this method's `_`.)
    @cherrypy.expose
    def npc_numbers(self, **_ignored: Any) -> bytes:
        denied = self._denied()
        if denied is not None:
            return denied
        if cherrypy.request.method != 'POST':
            cherrypy.response.headers['Allow'] = 'POST'
            return _json_error(405, 'POST the NPC as JSON')
        try:
            name, stats, sheet_id = _backport_request(cherrypy.request.body.read())
            from l7r import npcbackport

            answer = npcbackport.backport(name, stats, **self._portal_calls())
        except ValueError as e:
            return _json_error(400, str(e))
        # cherrypy.log, not `logger`: the deployed app prints only CherryPy's own log (feature 226).
        cherrypy.log(f'npc-numbers: sheet {sheet_id} {answer["status"]}: {answer["message"]}')
        return json.dumps(answer).encode('utf-8')

    def _portal_calls(self) -> dict[str, Callable[..., Any]]:
        if self._portal is not None:
            return dict(self._portal)
        from chargen import op

        return {
            'characters': op.existing_characters,
            'get_body': op.get_character_body,
            'update': op.update_character,
        }


_BACKPORT_FIELDS = frozenset({'name', 'stats', 'sheet_id'})


def _backport_request(raw: bytes) -> tuple[str, dict[str, object], object]:
    """``(name, stats, sheet_id)`` from an `/api/npc-numbers` body; ValueError says what's wrong."""
    try:
        body = json.loads(raw or b'null')
    except ValueError:
        raise ValueError('the body is not JSON') from None
    if not isinstance(body, dict):
        raise ValueError('the body must be a JSON object with "name" and "stats"')
    unknown = sorted(set(body) - _BACKPORT_FIELDS)
    if unknown:
        raise ValueError(f'unknown fields: {", ".join(unknown)}')
    name = body.get('name')
    stats = body.get('stats')
    if not isinstance(name, str) or not name.strip():
        raise ValueError('"name" must be the NPC\'s name')
    if not isinstance(stats, dict) or not stats:
        raise ValueError('"stats" must be an object of stat names to ranks')
    return name.strip(), stats, body.get('sheet_id')


def _json_error(status: int, message: str) -> bytes:
    cherrypy.response.status = status
    return json.dumps({'error': message}).encode('utf-8')


def _sheet_token() -> str:
    """`[character_sheet] roll_query_token`: the sheet app's read token (FR-048); '' when unset."""
    section = _load_secrets().get('character_sheet', {})
    return str(section.get('roll_query_token', '')).strip()


def _names_token() -> str:
    """`[character_sheet] names_token` from development-secrets.ini; '' when unset."""
    section = _load_secrets().get('character_sheet', {})
    return str(section.get('names_token', '')).strip()


class Root:
    """Top-level CherryPy controller for the L7R Toolkit."""

    def __init__(
        self,
        relics: list[Relic],
        names: list[GeneratedName] | None = None,
        places: list[Place] | None = None,
        dream_scenes: list[DreamScene] | None = None,
        dream_framework_html: str = '',
        env: Environment | None = None,
        wiki_links: dict[str, str] | None = None,
        names_token: Callable[[], str] | None = None,
        shrine_catalog: Catalog | None = None,
        cost_access: CostAccess | None = None,
    ) -> None:
        self._relics = relics
        self._shrine_catalog = shrine_catalog if shrine_catalog is not None else load_catalog()
        self._cost_access = cost_access or CostAccess(lambda: _sheet_token())
        # Resolved at REQUEST time (a lambda, not a bound default), so a test patching
        # `_names_token` reaches a Root built before the patch.
        self.api = NamesApi(names_token or (lambda: _names_token()))
        self._names = names if names is not None else []
        self._places = places if places is not None else []
        self._dream_scenes = dream_scenes if dream_scenes is not None else []
        self._dream_framework_html = dream_framework_html
        self._env = env if env is not None else build_environment()
        # /names notes: glossary tooltips + verified Wikipedia links on bearers
        # (GM 2026-08-26). Bound here so the filter sees this app's link table.
        links = wiki_links or {}
        self._env.filters['notes_markup'] = lambda text: render_notes(str(text), links)
        self._relics_by_fortune = _group_relics_by_fortune(relics)
        self._clans_with_relics = _clans_with_relics(relics)

    # GET /
    @cherrypy.expose
    def index(self) -> bytes:
        return self._render('landing.html', current_section='landing')

    # GET /relics, GET /relics/<slug>
    @cherrypy.expose
    def relics(self, slug: str | None = None) -> bytes:
        if slug is None:
            return self._render(
                'relics_index.html',
                current_section='relics',
                relics_by_fortune=self._relics_by_fortune,
                clans_with_relics=self._clans_with_relics,
            )

        relic = find_relic_by_slug(self._relics, slug)
        if relic is None:
            return self._render_404()

        fortune = FORTUNES.get(relic.fortune)
        if fortune is None:
            # Defensive: a relic file declared an unknown fortune.
            logger.warning('relic %s has unknown fortune %s', relic.slug, relic.fortune)
            return self._render_404()

        prev_relic, next_relic = neighbors_in_fortune(self._relics, slug)
        return self._render(
            'relic_detail.html',
            current_section='relics',
            relic=relic,
            fortune=fortune,
            prev_relic=prev_relic,
            next_relic=next_relic,
        )

    # GET /dreams, GET /dreams/<slug>
    @cherrypy.expose
    def dreams(self, slug: str | None = None) -> bytes:
        if slug is None:
            return self._render(
                'dreams_index.html',
                current_section='dreams',
                framework_html=self._dream_framework_html,
                scenes=self._dream_scenes,
            )

        scene = find_scene_by_slug(self._dream_scenes, slug)
        if scene is None:
            return self._render_404()

        return self._render(
            'dream_detail.html',
            current_section='dreams',
            scene=scene,
        )

    # GET /shrines - the shrine builder (feature 216). The design lives in the query string. Costs
    # reach the template ONLY for the GM and for a player whose grouped character has Commerce
    # (FR-048, read-only for them): for anyone else `ledger` is None and the `gm_*` params are
    # never read, so neither the page nor its source can carry a price. The sheet roster is
    # consulted only for a signed-in non-GM.
    @cherrypy.expose
    def shrines(self, **params: Any) -> bytes:
        catalog = self._shrine_catalog
        design = parse_design(catalog, params)
        user = current_user()
        is_gm = user is not None and user.role == 'gm'
        priced = is_gm or (user is not None and self._cost_access.allows(user.discord_id))
        context: dict[str, Any] = {}
        if priced:
            negotiation = parse_negotiation(catalog, params)
            context = {
                'ledger': negotiate(catalog, design, negotiation),
                'negotiation': negotiation,
                'gm_query': gm_query(catalog, design, negotiation),
                'suggested_budget': default_budget(catalog),
                'format_koku': format_koku,
                'format_number': format_number,
            }
        return self._render(
            'shrines.html',
            current_section='shrines',
            body_class='page-shrines',
            option_effects=option_effects,
            catalog=catalog,
            design=design,
            moot_note=moot_note,
            option_offered=option_offered,
            rules_json=rules_json(catalog),
            text_fields=TEXT_FIELDS,
            share_query=share_query(catalog, design),
            is_gm=is_gm,
            priced=priced,
            missing=sum(
                1
                for c in catalog.categories
                if c.key not in design.choices
                and c.key not in design.multi
                and c.key not in design.voided
            ),
            **context,
        )

    # GET /money - the Money section (feature 222): a landing page listing its tools, and
    # /money/koku, what a koku is worth: the whole basket and the average over goods (feature 223),
    # good by good. Public, like
    # Dreams: nothing on it is GM-only. The whole state is in the link (l7r/money/web.py).
    @cherrypy.expose
    def money(self, tool: str | None = None, **params: Any) -> bytes:
        if tool is None:
            return self._render('money_index.html', current_section='money')
        if tool == 'prices':
            model = money_basket.load()
            wage = load_wages()[-1]
            koku_kg, _ = resolve_koku_kg(None)
            state = money_web.parse_state(model, {})
            return self._render(
                'money_prices.html',
                current_section='money',
                body_class='page-money',
                sheets=money_prices.sheets(
                    money_ledger.load(),
                    money_ledger.load_swings(),
                    money_web.state_reading(model, state, koku_kg).per_koku,
                    wage_dollars_per_koku(wage),
                ),
                source_link=money_prices.source_link,
                plain=money_prices.plain,
                research_url=money_prices.research_url,
                day_sen=LABORER_DAY_SEN,
                laborer_koku_year=LABORER_KOKU_YEAR,
                day_rice_kg=DAY_RICE_KG,
                koku_kg=koku_kg,
            )
        if tool != 'koku':
            return self._render_404()
        model = money_basket.load()
        wage = load_wages()[-1]
        koku_kg, _ = resolve_koku_kg(None)
        state = money_web.parse_state(model, params)
        reading = money_web.state_reading(model, state, koku_kg)
        whole = money_web.whole_reading(model, state, koku_kg)
        return self._render(
            'money_koku.html',
            current_section='money',
            body_class='page-money',
            model=model,
            state=state,
            rows=money_web.rows(model, state, reading),
            reading=reading,
            whole=whole,
            weights=model.weights(state.weights),
            axis_pct=money_web.axis_pct,
            model_means=money_basket.MEANS,
            rice_alone=money_web.alone_of(whole, 'rice'),
            drivers=money_web.drivers(reading),
            left_out=money_web.left_out(reading),
            sen=lambda silver: money_web.sen(silver, model, koku_kg),
            sig3=money_web.sig3,
            source_label=money_web.source_label,
            research_url=money_prices.research_url,
            plain=money_prices.plain,
            data_json=money_web.page_json(model, koku_kg, wage),
            wage=wage,
            wage_per_koku=wage_dollars_per_koku(wage),
            laborer_koku_year=LABORER_KOKU_YEAR,
            day_rice_kg=DAY_RICE_KG,
            koku_kg=koku_kg,
        )

    # GET /terms - public (linked from Discord OAuth consent screen)
    @cherrypy.expose
    def terms(self) -> bytes:
        return self._render('terms.html', current_section='')

    # GET /privacy - public (linked from Discord OAuth consent screen)
    @cherrypy.expose
    def privacy(self) -> bytes:
        return self._render('privacy.html', current_section='')

    # GET /viewer - standalone full-screen image viewer with NO site chrome, for
    # showing character art on a shared screen without exposing a filename. Served
    # raw (not through the Jinja layout) and deliberately kept out of SECTIONS/nav.
    @cherrypy.expose
    def viewer(self) -> bytes:
        return (_HERE / 'static' / 'viewer.html').read_bytes()

    # POST /archive/save - GM-only stub. The gm gate is applied via the
    # mount config (tools.l7r_auth.min_role='gm' for the '/archive' prefix);
    # this handler can assume the caller is a GM.
    @cherrypy.expose
    def archive(self, action: str = '', **_kwargs: Any) -> bytes:
        if action != 'save':
            raise cherrypy.HTTPError(404)
        if cherrypy.request.method != 'POST':
            raise cherrypy.HTTPError(405)
        body = cherrypy.request.body.read()
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            raise cherrypy.HTTPError(400, 'invalid JSON body') from None
        user = current_user()
        logger.info(
            'archive stub save by %s: %s',
            user.discord_id if user else '<unknown>',
            json.dumps(payload)[:500],
        )
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps({'ok': True, 'note': 'archive stub - not yet persisted'}).encode('utf-8')

    # GET /names
    @cherrypy.expose
    def names(
        self,
        gender: str | None = None,
        caste: str | None = None,
        random: str | None = None,
        picked: str | None = None,
    ) -> bytes:
        active_gender = gender if gender in {'male', 'female'} else None
        active_caste = caste if caste in {'peasant', 'samurai'} else None

        filtered = self._names
        if active_gender:
            filtered = [n for n in filtered if n.gender == active_gender]
        if active_caste == 'peasant':
            filtered = [n for n in filtered if n.peasant]
        elif active_caste == 'samurai':
            # Court-style names plus register names attested on warrior-house
            # women (the same tier the chargen engine prefers for samurai).
            filtered = [n for n in filtered if not n.peasant or n.samurai]

        filter_qs = _build_names_filter_qs(gender=active_gender, caste=active_caste)

        # Random pick: pick from the currently-filtered list and redirect to
        # /names?picked=<slug>&<filters>#card-<slug> so the browser scrolls
        # to the picked card and the page can morph the masthead button into
        # "Another random pick" with the same filter context preserved.
        if random is not None:
            picked_name_for_random = random_name(filtered)
            if picked_name_for_random is not None:
                slug = picked_name_for_random.slug
                url = f'/names?picked={slug}'
                if filter_qs:
                    url += '&' + filter_qs
                url += f'#card-{slug}'
                raise cherrypy.HTTPRedirect(url)

        # The picked slug only counts if it resolves to a real name and
        # survives the current filters. If the GM lands on /names?picked=foo
        # but switches filters to one that excludes foo, we clear the pick
        # rather than leaving a phantom "Another random pick" label.
        picked_name = None
        if picked is not None:
            picked_name = find_name_by_slug(filtered, picked)
        picked_slug = picked_name.slug if picked_name else None

        return self._render(
            'names_index.html',
            current_section='names',
            names=filtered,
            total_count=len(self._names),
            filtered_count=len(filtered),
            active_gender=gender if gender in {'male', 'female'} else 'all',
            active_caste=caste if caste in {'peasant', 'samurai'} else 'all',
            filter_qs=filter_qs,
            picked_slug=picked_slug,
        )

    # GET /places, GET /places/<slug>
    @cherrypy.expose
    def places(
        self,
        slug: str | None = None,
        place_type: str | None = None,
        commonality: str | None = None,
        regional: str | None = None,
        suffix: str | None = None,
        random: str | None = None,
        via: str | None = None,
    ) -> bytes:
        active_place_type = place_type if place_type in PLACE_TYPES else None
        active_commonality = commonality if commonality in COMMONALITIES else None
        active_regional = regional if regional in REGIONAL_CONTEXTS else None
        active_suffix = suffix if suffix else None

        # filter_qs is the canonical query string carrying the active filter
        # axes only - no random/via action params. Both the index and detail
        # templates use it to build links that preserve the filter context
        # across navigation, so clicking a card and then "back to the pool"
        # returns the GM to the same filtered view they came from.
        filter_qs = _build_filter_qs(
            place_type=active_place_type,
            commonality=active_commonality,
            regional=active_regional,
            suffix=active_suffix,
        )

        if slug is not None:
            place = find_place_by_slug(self._places, slug)
            if place is None:
                return self._render_404()
            return self._render(
                'places_detail.html',
                current_section='places',
                place=place,
                filter_qs=filter_qs,
                from_random=(via == 'random'),
                preselected_scale=active_place_type,
            )

        filtered = filter_places(
            self._places,
            place_type=active_place_type,
            commonality=active_commonality,
            regional=active_regional,
            suffix=active_suffix,
        )

        # When the random query param is set, pick one entry from the filter
        # result and redirect to its detail page. The redirect carries
        # via=random so the detail page can render an "Another random pick"
        # button, plus filter_qs so further random picks stay within the same
        # filtered subset. If the filter result is empty we silently fall
        # through to render the empty index so the user can adjust filters.
        if random is not None:
            picked = random_place(filtered)
            if picked is not None:
                url = f'/places/{picked.slug}?via=random'
                if filter_qs:
                    url += '&' + filter_qs
                raise cherrypy.HTTPRedirect(url)

        suffixes_present = sorted(
            {p.suffix for p in self._places if p.suffix is not None},
        )

        return self._render(
            'places_index.html',
            current_section='places',
            places=filtered,
            total_count=len(self._places),
            filtered_count=len(filtered),
            place_types=PLACE_TYPES,
            commonalities=COMMONALITIES,
            regional_contexts=REGIONAL_CONTEXTS,
            suffixes=suffixes_present,
            active_place_type=active_place_type,
            active_commonality=active_commonality,
            active_regional=active_regional,
            active_suffix=active_suffix,
            filter_qs=filter_qs,
        )

    # ---- internals ----

    def _render(self, template_name: str, **context: Any) -> bytes:
        template = self._env.get_template(template_name)
        rendered = template.render(SECTIONS=SECTIONS, current_user=current_user(), **context)
        return rendered.encode('utf-8')

    def _render_404(self) -> bytes:
        cherrypy.response.status = 404
        return self._render('_404.html', current_section='')


def _load_dream_framework_html(path: Path = _DREAM_FRAMEWORK_PATH) -> str:
    """Render the player-facing framework markdown to HTML once at startup.

    Returns an empty string if the file is absent (the /dreams page still
    renders its examples gallery), so a missing framework degrades gracefully.
    """
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        logger.warning('dreams framework file %s not found; page will omit it', path)
        return ''
    return render_markdown(text)


def make_app(
    pool_dir: Path | None = None,
    names_dir: Path | None = None,
    places_dir: Path | None = None,
    dream_pool_dir: Path | None = None,
) -> Root:
    """Construct a wired Root with relics, names, places, and dream scenes."""
    pool_src = pool_dir if pool_dir is not None else _DEFAULT_POOL_DIR
    names_src = names_dir if names_dir is not None else _DEFAULT_NAMES_DIR
    places_src = places_dir if places_dir is not None else _DEFAULT_PLACES_DIR
    dream_src = dream_pool_dir if dream_pool_dir is not None else _DEFAULT_DREAM_POOL_DIR
    return Root(
        relics=load_relics(pool_src),
        names=load_names(names_src),
        places=load_places(places_src),
        dream_scenes=load_dream_scenes(dream_src),
        dream_framework_html=_load_dream_framework_html(),
        wiki_links=load_wiki_links(names_src),
    )


def _error_page_handler(status: int, message: str, traceback: str, version: str) -> bytes:
    """Render the 404 page for missing routes inside the shared shell."""
    env = build_environment()
    template = env.get_template('_404.html')
    return template.render(
        SECTIONS=SECTIONS, current_section='', current_user=current_user()
    ).encode('utf-8')


def _forbidden_handler(status: int, message: str, traceback: str, version: str) -> bytes:
    """Render the 403 page when the auth tool blocks a non-GM user."""
    env = build_environment()
    template = env.get_template('forbidden.html')
    return template.render(
        SECTIONS=SECTIONS, current_section='', current_user=current_user()
    ).encode('utf-8')


def _load_secrets() -> dict[str, Any]:
    """Load development-secrets.ini as a plain dict; returns empty dict if missing.

    Interpolation is disabled so values containing literal `%` (e.g. cookie
    values with percent-encoding) don't trip the parser.
    """
    import configparser

    path = _HERE.parent / 'development-secrets.ini'
    if not path.exists():
        return {}
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(path, encoding='utf-8')
    result: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        result[section] = dict(parser.items(section))
    return result


def _auth_config() -> AuthConfig:
    """Build the AuthConfig from development-secrets.ini."""
    return load_auth_config(_load_secrets())


def _apply_server_config() -> None:
    """Apply server bind config from the environment.

    Inside any container (podman, docker, Fly), bind to 0.0.0.0 so the host
    can reach the process. The default 127.0.0.1 only accepts traffic on the
    container's loopback, so a host port-forward (e.g. `podman --publish
    8080:8080`) lands on the container's external interface where nothing is
    listening, and the kernel sends RST. Detection is automatic via runtime
    marker files (/run/.containerenv for podman, /.dockerenv for docker) plus
    FLY_APP_NAME for Fly.

    Behind a TLS-terminating proxy (Fly), additionally trust X-Forwarded-Proto
    so cherrypy.url() and HTTPRedirect build https:// URLs. Podman has no such
    proxy in front, so that setting stays Fly-only.
    """
    import os

    in_container = bool(
        os.environ.get('FLY_APP_NAME')
        or os.path.exists('/run/.containerenv')
        or os.path.exists('/.dockerenv')
    )
    if in_container:
        cherrypy.config.update(
            {
                'server.socket_host': '0.0.0.0',  # noqa: S104 - required in containers
                'server.socket_port': int(os.environ.get('PORT', '8080')),
                'engine.autoreload.on': False,
            }
        )

    if os.environ.get('FLY_APP_NAME'):
        cherrypy.config.update({'tools.proxy.on': True})


def mount_application() -> None:
    """Wire the L7R toolkit and chargen into the CherryPy tree.

    Called when `cherryd --import l7r.app` boots the process.

    Chargen's website module self-mounts at '/' on import (legacy behavior). We
    import it first, swap its Jinja env for the shared one, re-mount it at
    /chargen, and finally mount our L7R Root at '/' (overwriting chargen's
    self-mount).
    """
    _apply_server_config()

    auth_config = _auth_config()
    install_auth_tool(auth_config)

    # Chargen is the character generator - logged-in players and GMs only.
    # The /cleanup listing and the /delete action let GMs prune characters
    # from Obsidian Portal via the OAuth API; restrict them to gm role.
    chargen_config = {
        '/': {
            'tools.l7r_auth.on': True,
            'tools.l7r_auth.min_role': 'player',
        },
        '/cleanup': {'tools.l7r_auth.min_role': 'gm'},
        '/delete': {'tools.l7r_auth.min_role': 'gm'},
    }

    try:
        from chargen import website as chargen_website

        chargen_website.jinja_env = build_environment()
        cherrypy.tree.mount(chargen_website.Root(), '/chargen', config=chargen_config)
    except ImportError:
        logger.warning('chargen not importable; /chargen section will be unavailable')

    root = make_app()
    shared_env = build_environment()
    auth_root = AuthRoot(config=auth_config, env=shared_env)
    # The research record: public static pages with no shared shell, so no auth tool.
    cherrypy.tree.mount(
        ResearchSite(),
        '/research',
        config={'/': {'error_page.404': _error_page_handler}},
    )
    cherrypy.tree.mount(
        auth_root,
        '/auth',
        config={'/': {}},  # explicitly no auth tool - auth routes must be reachable
    )
    cherrypy.tree.mount(
        root,
        '/',
        config={
            '/': {
                'error_page.404': _error_page_handler,
                'error_page.403': _forbidden_handler,
                'tools.l7r_auth.on': True,
                # Landing, relics catalog, names catalog: public. The tool
                # still attaches current_user on these routes if a valid
                # session is present, so the nav can render the user pill.
                'tools.l7r_auth.min_role': 'anonymous',
            },
            # /api/* is for other apps, not browsers: no Discord session exists there. The
            # session tool stays non-blocking (anonymous) and each handler checks its own
            # bearer token - see NamesApi.names.
            '/api': {
                'tools.l7r_auth.min_role': 'anonymous',
            },
            # GM-only archive endpoints (currently just /archive/save).
            '/archive': {
                'tools.l7r_auth.min_role': 'gm',
            },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': str(_HERE / 'static'),
                'tools.l7r_auth.on': False,
            },
        },
    )


mount_application()
