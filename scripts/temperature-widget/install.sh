#!/usr/bin/env bash
#
# install.sh - install (or update) the CPU Temperature Bar GNOME extension.
#
# Run this ON THE LAPTOP, not inside a container - the extension has to be
# installed into the host's GNOME session.
#
#   ./scripts/temperature-widget/install.sh
#
# After the first install (and after any update to extension.js) GNOME Shell
# must reload the extension:
#   - X11: press Alt+F2, type "r", press Enter
#   - Wayland: log out and back in
#
set -euo pipefail

if [[ -e /run/.containerenv || -e /.dockerenv ]]; then
  echo "This looks like a container. Run this script on the laptop itself." >&2
  exit 1
fi

UUID="temperature-bar@mujina"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HOME/.local/share/gnome-shell/extensions/$UUID"

mkdir -p "$DEST"
cp "$SRC/metadata.json" "$SRC/extension.js" "$SRC/history.js" "$DEST/"
echo "Installed to $DEST"

# Enable by writing the gsettings key directly. The gnome-extensions CLI
# cannot do this for a freshly copied extension: it asks the RUNNING shell,
# which only scans the extensions directory at startup, so until the next
# shell reload it answers "extension does not exist". The gsettings key is
# what the shell (real or nested) consults at startup, so writing it directly
# works regardless.
python3 - "$UUID" <<'EOF'
import ast, subprocess, sys

uuid = sys.argv[1]
raw = subprocess.check_output(
    ["gsettings", "get", "org.gnome.shell", "enabled-extensions"],
    text=True).strip()
# Empty typed arrays print as "@as []"; non-empty as a Python-parsable list.
current = [] if raw.startswith("@as") else list(ast.literal_eval(raw))
if uuid not in current:
    current.append(uuid)
    value = "[" + ", ".join(f"'{u}'" for u in current) + "]"
    subprocess.check_call(
        ["gsettings", "set", "org.gnome.shell", "enabled-extensions", value])
    print(f"Added {uuid} to enabled-extensions.")
else:
    print(f"{uuid} already in enabled-extensions.")
EOF

session="${XDG_SESSION_TYPE:-unknown}"
if [[ "$session" == "x11" ]]; then
  echo "Now reload GNOME Shell: press Alt+F2, type 'r', press Enter."
else
  echo "For your real panel: log out and back in ($session session)."
  echo "To iterate without logging out, test in a nested shell:"
  echo "  dbus-run-session -- gnome-shell --nested --wayland"
fi
