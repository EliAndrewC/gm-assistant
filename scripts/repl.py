#!/usr/bin/env python3
"""Drop into the L7R GM REPL - dice, roll-and-keep odds, name and place picks.

Works from either side of the container:

  * INSIDE the container (the repo is mounted at /gm-assistant): puts
    ``webapp/`` on ``sys.path`` and starts the prompt in this process.
  * ON THE HOST: ``podman exec -it`` into the repo's running dev container
    (the name ``launch-container.sh`` derives: ``$CONTAINER_PREFIX``,
    default ``claude``, plus the repo directory name) and runs this same
    script there. Launch the container first if it is not running.

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


def in_container() -> bool:
    return (WEBAPP / "l7r" / "repl").is_dir() and Path("/gm-assistant").is_dir()


def container_name() -> str:
    prefix = os.environ.get("CONTAINER_PREFIX", "claude")
    return f"{prefix}-{REPO.name}"


def host_command(argv: list[str]) -> list[str]:
    runtime = shutil.which("podman") or shutil.which("docker") or "podman"
    workdir = "/gm-assistant"
    return [
        runtime,
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
    cmd = host_command(argv)
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        sys.stderr.write(f"{cmd[0]} not found; run this inside the container instead\n")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
