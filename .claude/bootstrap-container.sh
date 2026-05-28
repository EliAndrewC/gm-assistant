#!/usr/bin/env bash
#
# Bootstrap script for Claude Code memory persistence in a fresh container.
#
# Background: Claude Code's auto-memory system reads from
#   /home/agent/.claude/projects/-workspace/memory/
# which is in the container's home directory — wiped on container rebuild.
# This script symlinks that path to /workspace/.claude/memory/ (this repo,
# persistent ext4 mount), so memories survive rebuilds and travel with the
# code.
#
# Run once per fresh container:
#   bash /workspace/.claude/bootstrap-container.sh
#
# Idempotent — safe to re-run.

set -euo pipefail

PERSISTENT_DIR="/workspace/.claude/memory"
EPHEMERAL_LINK="/home/agent/.claude/projects/-workspace/memory"

mkdir -p "$PERSISTENT_DIR"
mkdir -p "$(dirname "$EPHEMERAL_LINK")"

if [[ -L "$EPHEMERAL_LINK" ]]; then
    current_target="$(readlink "$EPHEMERAL_LINK")"
    if [[ "$current_target" == "$PERSISTENT_DIR" ]]; then
        echo "[bootstrap] memory symlink already correct"
        exit 0
    fi
    echo "[bootstrap] removing stale symlink (was → $current_target)"
    rm "$EPHEMERAL_LINK"
elif [[ -e "$EPHEMERAL_LINK" ]]; then
    echo "[bootstrap] ERROR: $EPHEMERAL_LINK exists and is not a symlink." >&2
    echo "[bootstrap] Move its contents into $PERSISTENT_DIR/ first, then re-run." >&2
    exit 1
fi

ln -s "$PERSISTENT_DIR" "$EPHEMERAL_LINK"
echo "[bootstrap] memory: $EPHEMERAL_LINK → $PERSISTENT_DIR"
