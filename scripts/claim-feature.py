#!/usr/bin/env python3
"""Claim the next spec-kit feature number under a host-wide lock - `scripts/claim-feature.py <slug>`.

PORTED from the diagram repository (its feature 197, `scripts/claim-feature.py`) on 2026-10-26 at the
GM's word: *"the diagram repo has a better approach for this ... see whether they have a robust
solution that we can just steal and implement here as well"*. The code is theirs unchanged but for
two things: there is no `make claim` target (this repository has no root Makefile; run the script
from your clone), and their feature-377 approval notice is gone (that guard does not exist here).
The history below is theirs, and the measurements in it are of their repository.

WHY (GM 2026-09-07): *"I believe that I have noticed there being times when two different sessions
each end up claiming the same spec kit feature number, and then this causes problems later when one
clone needs to go back and update their feature to use a different number ... we could have a makefile
target that selects the next feature number ... using some file locking or other kind of multiprocess
locking just to make sure that we always grab the next available feature number."*

Measured before this existed (specs/197/research.md R2): fourteen numbers were claimed by two features
at some point, eight renumber commits landed between 2026-08-29 and 2026-09-06, one feature renumbered
twice, and main still carries two features numbered 195. The old protocol read main's `specs/` after
`sync-in` and let the PUSH surface a collision - hours or days after both sessions had built on the
same number. Its blind spot was structural: a sibling session's claim lives in
`<mirror>/.clones/<other>/specs/` until that session pushes, and nothing read that directory.

WHAT "NEXT AVAILABLE" MEANS. A number is taken when any of these holds it, all read UNDER THE LOCK:
  1. the mirror's working tree `specs/`               (main as this container last saw it)
  2. the mirror's `origin/main` tree (`git ls-tree`)  (fetched but not yet fast-forwarded; no network)
  3. every clone's `specs/` under `<mirror>/.clones/` (the other sessions' UNPUSHED claims)
  4. the ledger of every claim this tool has made
Next = 1 + the maximum. THE CLAIM IS THE DIRECTORY: `specs/NNN-slug/` is created in the caller's clone
before the lock is released, so the next caller's scan (source 3) sees it.

WHERE THE STATE LIVES, AND WHY IT NEEDS NO REGENERATING. The lock and the ledger sit under the
mirror's `.specify/` - the mirror root is the host volume, so both survive a container rebuild, and
both are gitignored (`*.lock` already was; the ledger has its own line). The ledger is a RECORD and a
safety net, never the only source: sources 1-3 alone give the right next number in every case but one -
a number claimed and then abandoned (its directory deleted before any push) is held only by the
ledger, and with the ledger gone it is reused. That is harmless (a number that never reached main
identifies nothing) and is stated here so nobody "fixes" it with a counter file, which WOULD need
regenerating (spec D1/D2).

The lock is `fcntl.flock` on a file - the same lock `flock(1)` takes, so a shell that ever holds
`flock` on the same path serializes with this too. No fetch happens under it: `sync-in` fetches GitHub
main at every prompt, so source 2 is at most one turn old; a spec pushed from the GM's laptop inside
that turn is the one residual window, and the old "renumber the unpushed spec" rule is kept for exactly
that case (spec D4).

    claim-feature.py <slug> [--dry-run] [--root DIR] [--main DIR] [--lock-timeout S]
    claim-feature.py --renumber specs/NNN-slug [--dry-run ...]     (move an existing directory to the next number)

Refusals (exit 2, nothing created, nothing appended): run from the mirror itself (main is never a
workspace); a slug that is not lower-case kebab; a slug already in use anywhere the scan reads; the
lock not acquired within the timeout (a held lock is a hung process, not a queue - the refusal names
the file). A number held by two directories in main is REPORTED on every claim and never renumbered
by a claim - renumbering a landed feature is the GM's call (spec D3). When the GM makes it, `--renumber`
performs the move under the same lock: that is how the 195
duplicate was resolved on 2026-09-07 (`195-target-descriptions-and-two-removals` -> 198, the one with
fewer references to its number).
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NUMBERED = re.compile(r"^(\d{3,})-(.+)$")
LEDGER_NAME = "feature-numbers.jsonl"
LOCK_NAME = "feature-numbers.lock"


class Refusal(Exception):
    """A refusal: exit 2, nothing written."""


def repo_root(cwd: Path | None = None) -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
        cwd=cwd,
    )
    return Path(out.stdout.strip()).resolve()


def mirror_of(root: Path) -> Path:
    """The mirror: a clone's grandparent when its parent is `.clones`, else the root itself - the
    derivation `sync-with-main.sh` and `main-tree-hooks.sh` use."""
    return root.parent.parent if root.parent.name == ".clones" else root


def numbered_dirs(specs: Path) -> list[tuple[int, str]]:
    """(number, name) for every `NNN-*` directory under specs/, or nothing when it does not exist."""
    if not specs.is_dir():
        return []
    out = []
    for p in sorted(specs.iterdir()):
        m = NUMBERED.match(p.name)
        if p.is_dir() and m:
            out.append((int(m.group(1)), p.name))
    return out


def origin_main_dirs(mirror: Path) -> list[tuple[int, str]]:
    """`specs/NNN-*` in the mirror's fetched `origin/main` - a packfile read, best effort (a fixture
    or a mirror without the ref contributes nothing)."""
    r = subprocess.run(
        ["git", "-C", str(mirror), "ls-tree", "--name-only", "origin/main", "specs/"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return []
    out = []
    for line in r.stdout.splitlines():
        name = line.strip().split("/", 1)[-1]
        m = NUMBERED.match(name)
        if m:
            out.append((int(m.group(1)), name))
    return out


def ledger_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a torn line is not a reason to refuse every future claim
    return rows


def duplicates_in(dirs: list[tuple[int, str]]) -> list[tuple[int, list[str]]]:
    """Numbers held by more than one distinct name - main's 195 today."""
    by: dict[int, set[str]] = {}
    for n, name in dirs:
        by.setdefault(n, set()).add(name)
    return sorted((n, sorted(names)) for n, names in by.items() if len(names) > 1)


def collect(root: Path, mirror: Path) -> dict[str, list[tuple[int, str]]]:
    """Every source, keyed by its name - read under the lock."""
    sources: dict[str, list[tuple[int, str]]] = {
        "main": numbered_dirs(mirror / "specs"),
        "origin/main": origin_main_dirs(mirror),
        "clones": [],
        "ledger": [(int(r["number"]), f"{int(r['number']):03d}-{r.get('slug', '')}") for r in ledger_rows(mirror / ".specify" / LEDGER_NAME) if "number" in r],
    }
    clones_dir = mirror / ".clones"
    seen = set()
    if clones_dir.is_dir():
        for clone in sorted(clones_dir.iterdir()):
            if clone.is_dir():
                seen.add(clone.resolve())
                sources["clones"] += numbered_dirs(clone / "specs")
    if root.resolve() not in seen and root.resolve() != mirror.resolve():
        sources["clones"] += numbered_dirs(root / "specs")  # a root outside .clones/ (tests) still counts itself
    return sources


class Lock:
    """`flock` on the mirror's lock file, polled so a hung holder yields a refusal rather than a hang."""

    def __init__(self, path: Path, timeout: float):
        self.path, self.timeout, self.fd = path, timeout, -1

    def __enter__(self) -> Lock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    os.close(self.fd)
                    raise Refusal(
                        f"could not take the feature-number lock within {self.timeout:g}s: {self.path} is held by another process - a hung claim, not a queue; look at who holds it (fuser {self.path})"
                    ) from None
                time.sleep(0.02)

    def __exit__(self, *_: object) -> None:
        fcntl.flock(self.fd, fcntl.LOCK_UN)
        os.close(self.fd)


def claim(
    slug: str,
    root: Path,
    mirror: Path,
    dry_run: bool = False,
    lock_timeout: float = 30.0,
    err=sys.stderr,
    move_from: Path | None = None,
) -> str:
    """Claim (or, dry-run, name) the next feature directory. Returns its name; raises Refusal.

    `move_from` is the RENUMBER form (GM 2026-09-07, on the standing 195 duplicate: *"Yes please fix
    195 by deduplicating it"*): an existing `specs/NNN-slug/` in the clone is moved to the next number
    under the same lock and the same derivation, so a deduplication is a claim like any other rather
    than a hand-typed `git mv` against a number read from a listing. The slug is the directory's own;
    the slug-in-use refusal exempts the directory being moved; `git mv` stages the rename when the
    directory is tracked (a plain rename otherwise); the ledger row records `renumbered_from`; and
    `.specify/feature.json` is left alone, because the feature being renumbered is not necessarily the
    one this clone is working on."""
    old_number: int | None = None
    if move_from is not None:
        m = NUMBERED.match(move_from.name)
        if not m or not (root / "specs" / move_from.name).is_dir():
            raise Refusal(f"{move_from} is not an existing specs/NNN-<slug>/ directory in {root}")
        old_number, slug = int(m.group(1)), m.group(2)
    if not SLUG_RE.match(slug):
        raise Refusal(f"slug {slug!r} is not lower-case kebab (letters, digits, single hyphens - the house style)")
    if root.resolve() == mirror.resolve():
        raise Refusal(f"{root} is the MIRROR - main is the integration point, never a workspace; run this from your session clone under {mirror}/.clones/")
    with Lock(mirror / ".specify" / LOCK_NAME, lock_timeout):
        sources = collect(root, mirror)
        for n, names in duplicates_in(sources["main"]):
            print(
                f"claim-feature: WARNING - main holds {n:03d} twice: {', '.join(names)} (reported, never renumbered on a claim - spec 197 D3; `claim-feature.py --renumber specs/<one of them>` moves it deliberately)",
                file=err,
            )
        every = [d for dirs in sources.values() for d in dirs]
        moving = move_from.name if move_from is not None else None
        in_use = sorted({name for _, name in every if name.split("-", 1)[1] == slug and name != moving})  # every name matched NUMBERED
        if in_use:
            raise Refusal(f"slug {slug!r} is already in use: {', '.join(in_use)} - a second directory with the same slug is a mistake nobody wants; pick another")
        top = max((n for n, _ in every), default=0)
        name = f"{top + 1:03d}-{slug}"
        maxima = "  ".join(f"{k}={max((n for n, _ in v), default=0):03d}" for k, v in sources.items())
        if dry_run:
            print(f"claim-feature: DRY RUN - next is {name}  ({maxima})", file=err)
            return name
        if move_from is not None:
            old, new = root / "specs" / move_from.name, root / "specs" / name
            if subprocess.run(["git", "-C", str(root), "mv", str(old), str(new)], capture_output=True).returncode != 0:
                old.rename(new)  # untracked (a claim not yet committed): a plain rename is the same move
        else:
            (root / "specs" / name).mkdir(parents=True, exist_ok=False)
        row = {
            "number": top + 1,
            "slug": slug,
            "clone": root.name,
            "utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if old_number is not None:
            row["renumbered_from"] = old_number
        with open(mirror / ".specify" / LEDGER_NAME, "a") as f:
            f.write(json.dumps(row) + "\n")
    if move_from is not None:
        print(
            f"claim-feature: renumbered specs/{move_from.name}/ -> specs/{name}/ in {root}  ({maxima}); now fix every reference to the old number (grep for it) and commit the move",
            file=err,
        )
        return name
    (root / ".specify").mkdir(exist_ok=True)
    (root / ".specify" / "feature.json").write_text(json.dumps({"feature_directory": f"specs/{name}"}, indent=2) + "\n")
    print(
        f"claim-feature: claimed specs/{name}/ in {root}  ({maxima}); .specify/feature.json points at it",
        file=err,
    )
    print(f"export SPECIFY_FEATURE={name}", file=err)
    print(f"export SPECIFY_FEATURE_DIRECTORY=specs/{name}", file=err)
    return name


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="claim the next spec-kit feature number under the host-wide lock")
    ap.add_argument("slug", nargs="?", default=None, help="lower-case kebab slug; the directory becomes specs/NNN-<slug>/")
    ap.add_argument(
        "--renumber",
        type=Path,
        default=None,
        metavar="specs/NNN-slug",
        help="RENUMBER an existing directory to the next number instead of claiming a new one (no slug)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print what the claim would be; create and record nothing",
    )
    ap.add_argument(
        "--root",
        type=Path,
        default=None,
        help="the clone (default: git's toplevel of the cwd)",
    )
    ap.add_argument(
        "--main",
        type=Path,
        default=None,
        help="the mirror (default: the clone's grandparent when under .clones/)",
    )
    ap.add_argument(
        "--lock-timeout",
        type=float,
        default=30.0,
        help="seconds to wait for the lock before refusing",
    )
    a = ap.parse_args(argv)
    try:
        if (a.slug is None) == (a.renumber is None):
            raise Refusal("give exactly one of a slug (claim a new number) or --renumber specs/NNN-slug (move an existing directory to the next number)")
        root = (a.root or repo_root()).resolve()
        mirror = (a.main or mirror_of(root)).resolve()
        print(claim(a.slug or "", root, mirror, a.dry_run, a.lock_timeout, move_from=a.renumber))
        return 0
    except Refusal as e:
        print(f"claim-feature: REFUSED - {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
