#!/usr/bin/env bash
#
# Deploy the Discord mention responder to an always-on box (the GM's AWS
# Lightsail server) and run it under systemd.
#
#     ./scripts/deploy_mention_bot.sh ubuntu@203.0.113.10
#
# Idempotent: run it again after any change and it re-syncs, restarts, and shows
# the log. There is no separate "update" path to get wrong.
#
# WHAT GOES OVER THE WIRE, AND WHAT DOES NOT
#
# The box gets a MINIMAL config file holding the two Discord bot tokens and
# nothing else. It does NOT get development-secrets.ini, which also holds the
# AWS keys, the GitHub PAT, the Gemini key, the Obsidian Portal credentials and
# the character-sheet bearer token. A joke bot on an internet-facing box has no
# business holding any of those, and a box is only as safe as the worst thing
# on it.
#
# The payload is built in a mode-700 temp directory and deleted on exit.

set -euo pipefail

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
    echo "usage: $0 <user@host>" >&2
    echo "  e.g. $0 ubuntu@203.0.113.10" >&2
    exit 64
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_DIR='l7r-mention'
SERVICE='l7r-mention'

# Optional, and how scripts/lightsail_access.py feeds this script: a TEMPORARY
# key plus the host keys the Lightsail API handed us. Host verification stays
# ON - the API tells us the fingerprints, so there is no reason to reach for
# StrictHostKeyChecking=no.
SSH_ARGS=()
if [ -n "${SSH_KEY:-}" ]; then
    SSH_ARGS+=(-i "$SSH_KEY" -o IdentitiesOnly=yes)
fi
if [ -n "${SSH_KNOWN_HOSTS:-}" ]; then
    SSH_ARGS+=(-o "UserKnownHostsFile=$SSH_KNOWN_HOSTS" -o StrictHostKeyChecking=yes)
fi
SSH_CMD=(ssh "${SSH_ARGS[@]}")
ssh_run() { "${SSH_CMD[@]}" "$@"; }

STAGE="$(mktemp -d)"
chmod 700 "$STAGE"
trap 'rm -rf "$STAGE"' EXIT

# --- the payload ------------------------------------------------------------
mkdir -p "$STAGE/webapp/l7r/mention" "$STAGE/scripts"
cp "$REPO"/webapp/l7r/mention/*.py "$STAGE/webapp/l7r/mention/"
cp "$REPO"/webapp/l7r/mention/CLAUDE.md "$STAGE/webapp/l7r/mention/"
cp "$REPO"/scripts/mention_bot.py "$STAGE/scripts/"
chmod +x "$STAGE/scripts/mention_bot.py"

# Just the [mention_bots] sections, from the files that already hold them, so
# this script never becomes a second place where a token is written down.
python3 - "$REPO" "$STAGE" <<'PYEOF'
import os
import sys
from configobj import ConfigObj

repo, stage = sys.argv[1], sys.argv[2]
secrets = ConfigObj(os.path.join(repo, 'webapp', 'development-secrets.ini'), encoding='utf-8')
defaults = ConfigObj(os.path.join(repo, 'webapp', 'development-defaults.ini'), encoding='utf-8')

tokens = secrets.get('mention_bots') or {}
listener = str((defaults.get('mention_bots') or {}).get('listener', '')).strip()
if not tokens:
    raise SystemExit('no [mention_bots] tokens in development-secrets.ini')
if not listener:
    raise SystemExit('no [mention_bots] listener in development-defaults.ini')
if listener not in tokens:
    raise SystemExit(f'listener {listener} has no token; the box would not start')

out = os.path.join(stage, 'webapp', 'development-secrets.ini')
with open(os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as fh:
    fh.write('# Deployed by scripts/deploy_mention_bot.sh. Bot tokens ONLY -\n')
    fh.write('# deliberately not a copy of the development secrets file.\n')
    fh.write('[mention_bots]\n')
    for app_id, token in tokens.items():
        fh.write(f'{app_id} = {token}\n')

pub = os.path.join(stage, 'webapp', 'development-defaults.ini')
with open(pub, 'w') as fh:
    fh.write('# The listener application id is public; see l7r/mention/bots.py.\n')
    fh.write('[mention_bots]\n')
    fh.write(f'listener = {listener}\n')

print(f'  payload: {len(tokens)} bot token(s), listener {listener}')
PYEOF

cat > "$STAGE/$SERVICE.service" <<EOF
[Unit]
Description=L7R Discord mention responder
Documentation=https://github.com/EliAndrewC/gm-assistant
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/$REMOTE_DIR
ExecStart=%h/$REMOTE_DIR/env/bin/python -u %h/$REMOTE_DIR/scripts/mention_bot.py
# It reconnects on its own; this is for the cases it cannot recover from, such
# as the box losing DNS for a while. RestartSec keeps a crash loop from becoming
# a login-attempt flood that Discord would rate-limit us for.
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

# --- ship it ----------------------------------------------------------------
echo "==> syncing to $TARGET:~/$REMOTE_DIR"
ssh_run "$TARGET" "mkdir -p ~/$REMOTE_DIR"
rsync -az --delete \
    -e "$(printf '%q ' "${SSH_CMD[@]}")" \
    --exclude '__pycache__' \
    "$STAGE"/webapp "$STAGE"/scripts \
    "$TARGET:~/$REMOTE_DIR/"
scp -q "${SSH_ARGS[@]}" "$STAGE/$SERVICE.service" "$TARGET:~/$REMOTE_DIR/$SERVICE.service"

echo '==> installing on the box'
ssh_run "$TARGET" "bash -seuo pipefail" <<REMOTE
cd ~/$REMOTE_DIR
chmod 600 webapp/development-secrets.ini

if [ ! -x env/bin/python ]; then
    echo '    creating the virtualenv'
    python3 -m venv env || { sudo apt-get update -qq && sudo apt-get install -y -qq python3-venv && python3 -m venv env; }
fi
# Only two third-party packages; everything else the bot uses is stdlib.
./env/bin/pip install --quiet --upgrade pip
./env/bin/pip install --quiet websockets configobj

# A user service, so this needs no root at run time. Lingering makes it start at
# boot rather than at the GM's next login - the whole point is "always on".
mkdir -p ~/.config/systemd/user
cp $SERVICE.service ~/.config/systemd/user/$SERVICE.service

# Enable lingering FIRST: it is what creates /run/user/<uid>, and without that
# directory every systemctl --user call over a non-login ssh session fails with
# "Failed to connect to bus". The export is needed for the same reason - a
# non-interactive ssh gets no XDG_RUNTIME_DIR.
sudo loginctl enable-linger "\$USER" || echo '    (could not enable lingering; it will start at login instead)'
export XDG_RUNTIME_DIR="/run/user/\$(id -u)"
systemctl --user daemon-reload
systemctl --user enable $SERVICE
systemctl --user restart $SERVICE
REMOTE

echo '==> waiting for it to announce itself'
ssh_run "$TARGET" "timeout 25 journalctl --user -u $SERVICE -n 20 -f --since '-1 min' | grep -m1 'listening as' || true"

echo
echo "==> status"
ssh_run "$TARGET" "systemctl --user is-active $SERVICE && systemctl --user status $SERVICE --no-pager -n 12" || true

cat <<DONE

Deployed. Useful commands on the box:

    systemctl --user status $SERVICE       # is it up
    journalctl --user -u $SERVICE -f       # watch it answer
    systemctl --user restart $SERVICE      # after a redeploy
    systemctl --user stop $SERVICE         # make it be quiet

Re-run this script to deploy a change; it is idempotent.
DONE
