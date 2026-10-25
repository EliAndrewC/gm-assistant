"""Tests for /research/ - bundling the diagram repository's built site and serving it.

Requests go through a real CherryPy Application over WSGI against a site built in tmp_path, so
the trailing-slash redirect, the 404 and the Content-Encoding headers are CherryPy's own.
"""

from __future__ import annotations

import gzip
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path
from wsgiref.util import setup_testing_defaults

import cherrypy
import pytest

from l7r import research
from l7r.app import _error_page_handler
from l7r.research import ResearchSite, bundle, compressible, locate, main
from l7r.sections import find_section_by_slug

INDEX = '<html><a href="q/salt.html">salt</a></html>'


@pytest.fixture
def site(tmp_path: Path) -> Path:
    """A miniature built site: pages, assets, a binary, and the build's dotfile."""
    root = tmp_path / 'site'
    (root / 'q').mkdir(parents=True)
    (root / 'assets').mkdir()
    (root / 'index.html').write_text(INDEX)
    (root / 'q' / 'salt.html').write_text('<p>What did salt cost?</p>' * 200)
    (root / 'q' / 'index.html').write_text('<p>questions</p>')
    (root / 'assets' / 'site.css').write_text('body { color: black; }')
    (root / 'nav.js').write_text('var nav = 1;')
    (root / 'assets' / 'mark.png').write_bytes(b'\x89PNG fake')
    (root / '.stamp').write_text('hash')
    return root


@pytest.fixture
def bundled(site: Path, tmp_path: Path) -> Path:
    dest = tmp_path / 'research'
    bundle(site, dest)
    return dest


Response = tuple[str, dict[str, str], bytes]


def request(root: Path, path: str, accept: str | None = 'gzip, deflate, br') -> Response:
    app = cherrypy.Application(
        ResearchSite(root), '/research', config={'/': {'error_page.404': _error_page_handler}}
    )
    environ: dict[str, object] = {'PATH_INFO': path, 'SCRIPT_NAME': '/research'}
    setup_testing_defaults(environ)
    environ['PATH_INFO'] = path.removeprefix('/research')
    if accept is not None:
        environ['HTTP_ACCEPT_ENCODING'] = accept
    captured: dict[str, object] = {}

    def start_response(
        status: str, headers: list[tuple[str, str]], exc_info: object = None
    ) -> None:
        captured['status'] = status
        captured['headers'] = dict(headers)

    body: Iterable[bytes] = app(environ, start_response)
    data = b''.join(body)
    getattr(body, 'close', lambda: None)()
    return str(captured['status']), dict(captured['headers']), data  # type: ignore[call-overload]


def test_research_is_a_public_section() -> None:
    section = find_section_by_slug('research')
    assert section is not None
    assert section.enabled
    assert section.path == '/research/'


def test_bundle_gzips_text_copies_binaries_and_skips_dotfiles(site: Path, bundled: Path) -> None:
    names = sorted(str(p.relative_to(bundled)) for p in bundled.rglob('*') if p.is_file())
    assert names == [
        'assets/mark.png',
        'assets/site.css.gz',
        'index.html.gz',
        'nav.js.gz',
        'q/index.html.gz',
        'q/salt.html.gz',
    ]
    assert gzip.decompress((bundled / 'index.html.gz').read_bytes()).decode() == INDEX
    assert (bundled / 'assets' / 'mark.png').read_bytes() == b'\x89PNG fake'
    assert (bundled / 'q' / 'salt.html.gz').stat().st_mtime_ns == (
        site / 'q' / 'salt.html'
    ).stat().st_mtime_ns


def test_bundle_is_byte_identical_across_runs(site: Path, tmp_path: Path) -> None:
    """mtime=0 in the gzip header: an unchanged site must not invalidate the image layer."""
    first, second = tmp_path / 'a', tmp_path / 'b'
    bundle(site, first)
    bundle(site, second)
    assert (first / 'q' / 'salt.html.gz').read_bytes() == (
        second / 'q' / 'salt.html.gz'
    ).read_bytes()


def test_bundle_replaces_a_previous_bundle(site: Path, tmp_path: Path) -> None:
    dest = tmp_path / 'research'
    (dest / 'gone').mkdir(parents=True)
    (dest / 'gone' / 'old.html.gz').write_bytes(b'x')
    assert bundle(site, dest) == 6
    assert not (dest / 'gone').exists()
    assert not (tmp_path / 'research.tmp').exists()


def test_bundle_refuses_an_unbuilt_site(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match='make record'):
        bundle(tmp_path / 'nowhere', tmp_path / 'out')


def test_bundle_warns_when_the_site_predates_the_last_research_commit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / 'repo'
    built = repo / 'research' / 'site'
    built.mkdir(parents=True)
    (built / 'index.html').write_text(INDEX)
    os.utime(built / 'index.html', (1_000_000_000, 1_000_000_000))
    (repo / 'research' / 'q.md').write_text('# q')
    git = ['git', '-C', str(repo), '-c', 'user.name=t', '-c', 'user.email=t@t']
    subprocess.run([*git[:3], 'init', '-q'], check=True)
    subprocess.run([*git, 'add', '.'], check=True)
    subprocess.run([*git, 'commit', '-qm', 'q'], check=True)
    bundle(built, tmp_path / 'out')
    assert 'older than the last commit' in capsys.readouterr().err


def test_bundle_outside_a_git_repo_does_not_warn(
    site: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bundle(site, tmp_path / 'out')
    assert capsys.readouterr().err == ''


def test_compressible() -> None:
    assert compressible('a.html')
    assert compressible('a.js')
    assert compressible('a.json')
    assert compressible('a.svg')
    assert not compressible('a.png')
    assert not compressible('a.woff2')


def test_locate_refuses_escapes_and_dotfiles(bundled: Path, tmp_path: Path) -> None:
    (tmp_path / 'secret.html').write_text('no')
    (bundled / 'link.html').symlink_to(tmp_path / 'secret.html')
    assert locate(bundled, ('..', 'secret.html')) is None
    assert locate(bundled, ('link.html',)) is None
    assert locate(bundled, ('.stamp',)) is None
    assert locate(bundled, ('q', 'missing.html')) is None
    assert locate(bundled, ('q',)) == ((bundled / 'q' / 'index.html.gz').resolve(), True)


def test_root_redirects_to_trailing_slash_so_relative_links_resolve(bundled: Path) -> None:
    status, headers, _ = request(bundled, '/research')
    assert status.startswith('301')
    assert headers['Location'].endswith('/research/')


def test_index_is_served_gzipped_as_html(bundled: Path) -> None:
    status, headers, body = request(bundled, '/research/')
    assert status.startswith('200')
    assert headers['Content-Encoding'] == 'gzip'
    assert headers['Content-Type'] == 'text/html;charset=utf-8'
    assert headers['Vary'] == 'Accept-Encoding'
    assert gzip.decompress(body).decode() == INDEX


def test_nested_page_and_assets(bundled: Path) -> None:
    _, headers, body = request(bundled, '/research/q/salt.html')
    assert gzip.decompress(body).decode().startswith('<p>What did salt cost?</p>')
    assert len(body) < 200  # 5,400 bytes of repetition compress to almost nothing
    _, headers, _ = request(bundled, '/research/assets/site.css')
    assert headers['Content-Type'] == 'text/css;charset=utf-8'
    _, headers, _ = request(bundled, '/research/nav.js')
    assert headers['Content-Type'].endswith('javascript;charset=utf-8')


def test_a_client_without_gzip_gets_plain_bytes(bundled: Path) -> None:
    for accept in (None, 'identity', 'gzip;q=0'):
        status, headers, body = request(bundled, '/research/', accept=accept)
        assert status.startswith('200')
        assert 'Content-Encoding' not in headers
        assert headers['Content-Type'] == 'text/html;charset=utf-8'
        assert body.decode() == INDEX


def test_binary_and_uncompressed_files_are_served_as_they_are(bundled: Path, site: Path) -> None:
    _, headers, body = request(bundled, '/research/assets/mark.png')
    assert headers['Content-Type'] == 'image/png'
    assert 'Content-Encoding' not in headers
    assert body == b'\x89PNG fake'
    _, headers, body = request(site, '/research/q/index.html')  # the raw diagram site, locally
    assert 'Content-Encoding' not in headers
    assert body == b'<p>questions</p>'


def test_missing_page_is_the_toolkit_404(bundled: Path) -> None:
    status, _, body = request(bundled, '/research/q/nope.html')
    assert status.startswith('404')
    assert b'error-404__code' in body


def test_default_dir_sits_beside_the_package() -> None:
    assert research.RESEARCH_DIR.name == 'research'


def test_main(site: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(['bundle', str(site), str(tmp_path / 'out')]) == 0
    assert 'research record ready: 6 files' in capsys.readouterr().out
    assert main([]) == 2
    assert main(['pack', 'a', 'b']) == 2
