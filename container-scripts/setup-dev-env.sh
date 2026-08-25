#!/bin/bash
# Install every dependency this repo needs, INSIDE the dev container. Idempotent - safe to re-run.
#
#   container-scripts/setup-dev-env.sh          install anything missing, then verify
#   container-scripts/setup-dev-env.sh --check  verify only (fast, no network), exit 1 if anything is missing
#
# Run this on a fresh container, and any time something that used to work stops working with a
# "command not found" / "No module named" error. A container rebuild does NOT preserve apt or pip
# state (only the bind-mounted repo and ~/.claude survive), so a rebuilt container looks subtly
# broken until this has run: the symptom on 2026-07-25 was three tests failing because a system
# binary had vanished, which cost a full gate run to diagnose.
#
# Since feature 131 (2026-08-25) nothing here needs an apt package of its own: `resvg`, the DejaVu
# italic face and `shapely` all served the diagram skill, which now lives in its own repository
# with its own copy of this script. The only OS-level install left is what Playwright's
# `--with-deps` pulls in for Chromium.
#
# This lives in container-scripts/, NOT scripts/. scripts/ is for things run OUTSIDE the container
# (launch-container.sh creates the container; sync-with-main.sh is run by a session but manages the
# host-side clone/main relationship). Anything here assumes it is running inside the container and
# may freely apt-get install.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

in_container() { [ -f /run/.containerenv ] || [ -f /.dockerenv ]; }

if ! in_container && [ "${SETUP_ALLOW_HOST:-}" != 1 ]; then
    echo "ERROR: this installs system packages and is meant to run INSIDE the dev container."
    echo "Start one with scripts/launch-container.sh, then run this from the repository root."
    echo "(Override on a machine you are sure about: SETUP_ALLOW_HOST=1)"
    exit 1
fi

# ---- what "installed" means, as testable facts ------------------------------------------------
# Each is (label, test command). The SAME list drives --check and the post-install verification, so
# the script can never report success for something it did not actually establish.
check_all() {
    local bad=0
    _t() { # label, test
        if eval "$2" >/dev/null 2>&1; then
            [ "$CHECK_ONLY" = 1 ] && echo "  ok      $1"
        else
            echo "  MISSING $1"
            bad=1
        fi
    }
    # webapp prod deps (also used by the skills: OP API, portraits, weather, name scraping)
    _t "python: cherrypy jinja2 configobj yaml"  "python3 -c 'import cherrypy, jinja2, configobj, yaml'"
    _t "python: requests + oauthlib + bs4"       "python3 -c 'import requests, requests_oauthlib, bs4'"
    _t "python: pillow numpy cv2 google.genai"   "python3 -c 'import PIL, numpy, cv2, google.genai'"
    # dev deps - the quality gate itself
    _t "python: pytest + cov + xdist"            "python3 -c 'import pytest, pytest_cov, xdist'"
    _t "python: ruff mypy"                       "python3 -m ruff --version; python3 -m mypy --version"
    _t "playwright chromium (UI screenshots)"    "python3 -c 'from playwright.sync_api import sync_playwright
with sync_playwright() as p: p.chromium.launch().close()'"
    # the claude() wrapper that appends this repo's standing authorizations to the system prompt.
    # ~/.bashrc is NOT on a bind mount (only the repo and ~/.claude survive a rebuild), so this has
    # to be re-established on every fresh container exactly like the apt and pip state.
    _t "claude() system-prompt wrapper"          "grep -qF 'gm-assistant append-system-prompt' $HOME/.bashrc"
    return $bad
}

if [ "$CHECK_ONLY" = 1 ]; then
    echo "checking dev environment..."
    if check_all; then
        echo "dev environment OK"
        exit 0
    fi
    echo
    echo "run container-scripts/setup-dev-env.sh (no arguments) to install the missing pieces"
    exit 1
fi

# ---- install ----------------------------------------------------------------------------------
# Passwordless sudo is available in this container precisely so a session can install what it needs
# without asking. Never work around a missing dependency - install it.
echo "==> python packages (pip)"
# --break-system-packages: this container's python is the system python and there is no venv by
# design (every skill and the webapp share one interpreter).
pip install --quiet --break-system-packages \
    -r "$REPO/webapp/requirements.txt" \
    -r "$REPO/webapp/requirements-dev.txt"

echo "==> playwright browser + its OS libraries"
# --with-deps is REQUIRED, not optional (learned 2026-07-25): a bare `playwright install chromium`
# downloads the browser and reports success, but the binary then dies on launch with
# "libglib-2.0.so.0: cannot open shared object file" because the OS libraries it links against are
# not in this image. --with-deps apt-installs those too (it shells out to sudo, which is why this
# script belongs inside the container). ~180MB download, skipped when already unpacked.
python3 -m playwright install --with-deps chromium >/dev/null

# ---- the claude() wrapper ----------------------------------------------------------------------
# WHY a system-prompt append and not a CLAUDE.md line: CLAUDE.md sits BELOW the system prompt in the
# instruction hierarchy, so Claude Code's default "do not call the Agent tool unless the user
# requested it" outranks this project's own mandate to run a review subagent before declaring work
# done. On 2026-07-27 that silently suppressed the required settlement-review pass on three city
# maps - nothing broke and nothing warned, the mandate just lost. --append-system-prompt lands
# after that line with the same authority. The TEXT lives in container-scripts/append-system-prompt.md
# (version-controlled and reviewable); this only installs the loader.
echo "==> claude() system-prompt wrapper"
# rewrite rather than append-if-absent, so editing the block below actually reaches an existing container
touch "$HOME/.bashrc"
if grep -qF '>>> gm-assistant append-system-prompt >>>' "$HOME/.bashrc"; then
    sed -i '/# >>> gm-assistant append-system-prompt >>>/,/# <<< gm-assistant append-system-prompt <<</d' "$HOME/.bashrc"
fi
cat >> "$HOME/.bashrc" <<'BASHRC_BLOCK'
# >>> gm-assistant append-system-prompt >>>
# Appends this repo's standing authorizations to every session's system prompt.
# Edit the text in container-scripts/append-system-prompt.md - this only loads it.
claude() {
    # THIS repo's copy, wherever the repo is mounted (feature 131): the wrapper is per container,
    # and each repository's container mounts it at its own workdir.
    local _asp="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/container-scripts/append-system-prompt.md"
    if [ -r "$_asp" ]; then
        command claude --append-system-prompt "$(cat "$_asp")" "$@"
    else
        command claude "$@"
    fi
}
# <<< gm-assistant append-system-prompt <<<
BASHRC_BLOCK
echo "    installed - takes effect in NEW shells (or run: source ~/.bashrc)"

echo "==> verifying"
if check_all; then
    echo
    echo "dev environment ready. Next: cd webapp && make done   (from a .clones/ workspace, never main)"
else
    echo
    echo "ERROR: something is still missing after install - see MISSING lines above"
    exit 1
fi
