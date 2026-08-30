#!/usr/bin/env python3
"""Drop into the L7R GM REPL - dice, roll-and-keep odds, name and place picks.

Works from either side of the container:

  * INSIDE the container (the repo is mounted at /gm-assistant): puts
    ``webapp/`` on ``sys.path`` and starts the prompt in this process.
  * ON THE HOST: ``podman exec -it`` into the repo's running dev container
    (the name ``launch-container.sh`` derives: ``$CONTAINER_PREFIX``,
    default ``claude``, plus the repo directory name) and runs this same
    script there. If that container is not running, it is started first by
    handing off to ``scripts/launch-container.sh --no-shell`` - so a cold
    host needs no separate launch step, and the container the REPL leaves
    behind is exactly the one a hand launch would have built (same mounts,
    ports, packages, Claude config).

  ./scripts/repl.py              interactive
  ./scripts/repl.py 'xky(6, 3)'  one statement, then exit (add -i to stay)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WEBAPP = REPO / "webapp"
LAUNCHER = REPO / "scripts" / "launch-container.sh"


def in_container() -> bool:
    return (WEBAPP / "l7r" / "repl").is_dir() and Path("/gm-assistant").is_dir()


def container_name() -> str:
    prefix = os.environ.get("CONTAINER_PREFIX", "claude")
    return f"{prefix}-{REPO.name}"


def runtime_bin() -> str:
    return shutil.which("podman") or shutil.which("docker") or "podman"


def container_running() -> bool:
    """True when a container of our name is up right now.

    ``podman ps`` filters on a substring, so anchor the name (``^name$``) - a
    sibling repo's container would otherwise count as ours.
    """
    result = subprocess.run(
        [runtime_bin(), "ps", "-q", "-f", f"name=^{container_name()}$"],
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


def start_container() -> int:
    """Bring the dev container up, without opening a shell in it.

    ``launch-container.sh`` reads the CURRENT repo's CLAUDE.md for its mounts,
    ports and workdir, and finds that repo with ``git rev-parse`` - so it must
    run with the repo as its cwd, not wherever the GM typed ``repl``.
    """
    if not LAUNCHER.is_file():
        sys.stderr.write(f"{LAUNCHER} is missing; start the container by hand\n")
        return 1
    sys.stderr.write(f">> {container_name()} is not running; starting it\n")
    return subprocess.call([str(LAUNCHER), "--no-shell"], cwd=str(REPO))


def host_command(argv: list[str]) -> list[str]:
    workdir = "/gm-assistant"
    return [
        runtime_bin(),
        "exec",
        "-it",
        container_name(),
        "python3",
        f"{workdir}/scripts/repl.py",
        *argv,
    ]


def main(argv: list[str]) -> int:
    if in_container():
        sys.path.insert(0, str(WEBAPP))
        from l7r.repl.shell import main as shell_main

        return shell_main(argv)
    try:
        if not container_running():
            code = start_container()
            if code != 0:
                sys.stderr.write("could not start the container; see the output above\n")
                return code
        return subprocess.call(host_command(argv))
    except FileNotFoundError:
        sys.stderr.write(f"{runtime_bin()} not found; run this inside the container instead\n")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
