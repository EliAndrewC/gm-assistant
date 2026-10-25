"""The research record at /research/: the diagram repository's built site, served as it is.

The site is `research/site/` in the diagram repository's main checkout on the host, built there
by `make record` and never committed. `make prepare-deploy` bundles it into `webapp/research/`
(`python3 -m l7r.research bundle SRC DEST`), gzipping every text file, so the Docker build
context and the image carry about 20 MB instead of 106 MB. `ResearchSite` serves the gzipped
bytes as they are to any browser that accepts gzip (all of them) and decompresses for one that
does not, so a 33 MB `all.html` crosses the wire at a few MB without the 1-CPU machine
compressing it on every request. An uncompressed file is served as well, so a local
`L7R_RESEARCH_DIR` can point straight at the diagram checkout's site.

Every link inside the site is relative, which is why it works under the /research/ prefix
unchanged - and why /research must redirect to /research/ (CherryPy's trailing-slash tool does
that for `index`).
"""

from __future__ import annotations

import gzip
import mimetypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

import cherrypy
from cherrypy.lib import static

DEFAULT_SOURCE = Path('/host-l7r-repo/diagram/research/site')

# The image lays the bundle out at /app/research, beside /app/l7r.
RESEARCH_DIR = Path(os.environ.get('L7R_RESEARCH_DIR') or Path(__file__).parent.parent / 'research')

_COMPRESSIBLE = {'application/javascript', 'application/json', 'image/svg+xml'}


def _content_type(name: str) -> str:
    ctype = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    if ctype.startswith('text/') or ctype in _COMPRESSIBLE:
        return f'{ctype}; charset=utf-8'
    return ctype


def compressible(name: str) -> bool:
    """Whether a file of this name is text, which gzips well (images and fonts do not)."""
    ctype = mimetypes.guess_type(name)[0] or ''
    return ctype.startswith('text/') or ctype in _COMPRESSIBLE


def locate(root: Path, parts: tuple[str, ...]) -> tuple[Path, bool] | None:
    """The file a request path names under `root`, and whether it is the gzipped copy.

    A directory means its index.html. Anything resolving outside `root` (`..`, a symlink out)
    is not found, as is a dotfile such as the build's `.stamp`.
    """
    if any(part.startswith('.') for part in parts):
        return None
    base = root.resolve()
    target = base.joinpath(*parts).resolve()
    if not target.is_relative_to(base):
        return None
    if target.is_dir():
        target = target / 'index.html'
    packed = target.with_name(target.name + '.gz')
    if packed.is_file():
        return packed, True
    if target.is_file():
        return target, False
    return None


def accepts_gzip() -> bool:
    """Whether the current request's Accept-Encoding allows gzip."""
    return any(
        element.value in ('gzip', '*') and element.qvalue > 0
        for element in cherrypy.request.headers.elements('Accept-Encoding')
    )


class ResearchSite:
    """The static research record, mounted at /research."""

    def __init__(self, root: Path = RESEARCH_DIR) -> None:
        self.root = root

    @cherrypy.expose
    def index(self) -> object:
        return self._serve(())

    @cherrypy.expose
    def default(self, *parts: str, **_params: str) -> object:
        return self._serve(parts)

    def _serve(self, parts: tuple[str, ...]) -> object:
        found = locate(self.root, parts)
        if found is None:
            raise cherrypy.NotFound()
        path, packed = found
        ctype = _content_type(path.name.removesuffix('.gz') if packed else path.name)
        headers = cherrypy.response.headers
        headers['Cache-Control'] = 'public, max-age=300'
        if not packed:
            return static.serve_file(str(path), content_type=ctype)
        headers['Vary'] = 'Accept-Encoding'
        if accepts_gzip():
            headers['Content-Encoding'] = 'gzip'
            return static.serve_file(str(path), content_type=ctype)
        headers['Content-Type'] = ctype
        return gzip.decompress(path.read_bytes())


def last_research_commit(site: Path) -> int | None:
    """Unix time of the newest commit touching the site's source (`research/`), if a git repo."""
    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ['git', '-C', str(site.parent), 'log', '-1', '--format=%ct', '--', '.'],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    stamp = result.stdout.strip()
    return int(stamp) if result.returncode == 0 and stamp else None


def bundle(source: Path, dest: Path) -> int:
    """Copy the built site to `dest`, gzipping text files; return the number of files written.

    Gzip runs with mtime=0 and every file keeps its source mtime, so an unchanged site bundles
    to identical bytes and the image layer holding it stays cached between deploys.
    """
    if not (source / 'index.html').is_file():
        raise SystemExit(
            f'[deploy] no research site at {source} (no index.html). Build it in the diagram '
            'checkout with `make record`, or point L7R_RESEARCH_SITE at a built site.'
        )
    built = (source / 'index.html').stat().st_mtime
    committed = last_research_commit(source)
    if committed is not None and committed > built:
        sys.stderr.write(
            f'[deploy] WARNING: {source} is older than the last commit to research/ - '
            'the deploy ships the record as last built; `make record` in the diagram checkout '
            'refreshes it.\n'
        )
    staging = dest.with_name(dest.name + '.tmp')
    shutil.rmtree(staging, ignore_errors=True)
    count = 0
    for path in sorted(source.rglob('*')):
        rel = path.relative_to(source)
        if not path.is_file() or any(part.startswith('.') for part in rel.parts):
            continue
        out = staging / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if compressible(path.name):
            out = out.with_name(out.name + '.gz')
            out.write_bytes(gzip.compress(path.read_bytes(), compresslevel=9, mtime=0))
        else:
            shutil.copyfile(path, out)
        stat = path.stat()
        os.utime(out, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        count += 1
    shutil.rmtree(dest, ignore_errors=True)
    staging.rename(dest)
    return count


def main(argv: list[str]) -> int:
    """`bundle SRC DEST`: the deploy step."""
    if len(argv) != 3 or argv[0] != 'bundle':
        sys.stderr.write('usage: python3 -m l7r.research bundle SRC DEST\n')
        return 2
    count = bundle(Path(argv[1]), Path(argv[2]))
    sys.stdout.write(f'[deploy] research record ready: {count} files\n')
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
