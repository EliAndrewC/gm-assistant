"""CherryPy application root for the L7R Toolkit.

Routes:
- GET /                landing page
- GET /relics          all 42 relics grouped by Fortune
- GET /relics/<slug>   single relic detail
- GET /names           pre-generated Rokugani names with filters
- GET /places          pre-generated place names with filters
- GET /places/<slug>   single place detail
- /chargen/*           mounted chargen Root (legacy)
- /static/*            static assets
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import cherrypy
from jinja2 import Environment

from l7r.auth import AuthConfig, load_auth_config
from l7r.auth_routes import AuthRoot, current_user, install_auth_tool
from l7r.fortunes import FORTUNES
from l7r.jinja_env import build_environment
from l7r.names import (
    GeneratedName,
    find_name_by_slug,
    load_names,
    random_name,
)
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
from l7r.sections import SECTIONS
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


_DEFAULT_POOL_DIR = _resolve_default_pool_dir()
_DEFAULT_NAMES_DIR = _resolve_default_names_dir()
_DEFAULT_PLACES_DIR = _resolve_default_places_dir()


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


class Root:
    """Top-level CherryPy controller for the L7R Toolkit."""

    def __init__(
        self,
        relics: list[Relic],
        names: list[GeneratedName] | None = None,
        places: list[Place] | None = None,
        env: Environment | None = None,
    ) -> None:
        self._relics = relics
        self._names = names if names is not None else []
        self._places = places if places is not None else []
        self._env = env if env is not None else build_environment()
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

    # GET /terms - public (linked from Discord OAuth consent screen)
    @cherrypy.expose
    def terms(self) -> bytes:
        return self._render('terms.html', current_section='')

    # GET /privacy - public (linked from Discord OAuth consent screen)
    @cherrypy.expose
    def privacy(self) -> bytes:
        return self._render('privacy.html', current_section='')

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
            filtered = [n for n in filtered if not n.peasant]

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


def make_app(
    pool_dir: Path | None = None,
    names_dir: Path | None = None,
    places_dir: Path | None = None,
) -> Root:
    """Construct a wired Root with relics, names, and places loaded from disk."""
    pool_src = pool_dir if pool_dir is not None else _DEFAULT_POOL_DIR
    names_src = names_dir if names_dir is not None else _DEFAULT_NAMES_DIR
    places_src = places_dir if places_dir is not None else _DEFAULT_PLACES_DIR
    return Root(
        relics=load_relics(pool_src),
        names=load_names(names_src),
        places=load_places(places_src),
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

    Called when `cherryd --import l7r` boots the process.

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
