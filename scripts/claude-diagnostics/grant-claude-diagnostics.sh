#!/usr/bin/env bash
#
# grant-claude-diagnostics.sh - give Claude Code, running in the dev container, READ-ONLY
# diagnostic access to this host. Run ON THE HOST, with sudo. Idempotent: every item is checked
# first and applied only when missing or different, and each line of output says which.
#
#   sudo scripts/claude-diagnostics/grant-claude-diagnostics.sh           apply
#   sudo scripts/claude-diagnostics/grant-claude-diagnostics.sh --check   report only; exit 1 if anything would change
#   sudo scripts/claude-diagnostics/grant-claude-diagnostics.sh --revoke  remove everything this grants
#        ... [--user NAME]   the host user who owns the containers (default: $SUDO_USER, else eli)
#
# WHAT IT GRANTS - an unprivileged system account, claude-diag, that can:
#   * read the whole systemd journal, every user's included    (group systemd-journal; no sudo)
#   * read /var/log                                             (group adm; the root-only rest via varlog-read)
#   * read cgroup, /proc and unit state                         (world-readable already; no grant needed)
#   * run read-only rootless podman commands AS the host user   (sudo -> libexec/podman-diag)
#   * read the host user's systemd manager, read-only           (sudo -> libexec/user-systemctl)
#   * dump systemd-oomd's state                                 (sudo -> oomctl dump, exactly)
# The full sudo grant is files/sudoers; each wrapper's header says what it allows and why a
# sudoers wildcard would not be safe in its place.
#
# WHAT IT DOES NOT GRANT: a password, a network login, root, write access anywhere outside its
# own home (/var/lib/claude-diag), or any read of the host user's home. The script checks that
# the home is closed to "other" (Ubuntu's default since 21.04 is 0750) and closes it if not,
# because claude-diag is "other" to it; that is the whole of the protection for ~/.ssh and any
# unencrypted secrets, so it is enforced here, not assumed.
#
# HOW CLAUDE REACHES IT - ssh over a Unix socket, not a network port. The container cannot reach
# the host's loopback (rootless podman's slirp4netns blocks it), and an sshd on 0.0.0.0 would be
# on the LAN. So systemd listens on a socket in ~/.claude/host-diag/ - the one host directory
# launch-container.sh already mounts into every container - and starts a private sshd (its own
# config, host key and authorized_keys under /etc/claude-diag; `sshd -i`) per connection. No
# launch-script change and no container restart. The container side is client/host-diag.
# openssh-server is installed if missing, with the stock ssh.service MASKED first so installing
# it opens no port; if it was already installed, the stock service is left exactly as it was.
#
# The key pair is generated in the container (~/.claude/host-diag/id_ed25519, which is this
# user's ~/.claude/host-diag/ on the host); this script only reads the .pub. It pins the host key
# for the client in ~/.claude/host-diag/known_hosts.
#
# AND ONE HOST SETTING, not a grant: systemd-oomd's memory-pressure kill is turned off for user
# sessions (files/oomd-user-pressure.conf), because it killed whole dev containers five times,
# Sunday 2026-09-27's six-session crash among them. The file's header has the evidence and the cost.
#
# Assumes Ubuntu (apt, systemd, the adm and systemd-journal groups) and rootless podman.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACCOUNT=claude-diag
ACCOUNT_HOME=/var/lib/claude-diag
ETC=/etc/claude-diag
LIBEXEC=/usr/local/libexec/claude-diag
SUDOERS=/etc/sudoers.d/claude-diag
TMPFILES=/etc/tmpfiles.d/claude-diag-sshd.conf
SOCKET_UNIT=/etc/systemd/system/claude-diag-ssh.socket
SERVICE_UNIT=/etc/systemd/system/claude-diag-ssh@.service
OOMD_DROPIN=/etc/systemd/system/user@.service.d/90-no-oomd-pressure.conf
GROUPS_WANTED=adm,systemd-journal

MODE=apply
HOST_USER="${SUDO_USER:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE=check; shift ;;
    --revoke) MODE=revoke; shift ;;
    --user) HOST_USER="${2:?--user needs a name}"; shift 2 ;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1 (try --help)" >&2; exit 2 ;;
  esac
done
[ -n "$HOST_USER" ] && [ "$HOST_USER" != root ] || HOST_USER=eli

die() { echo "error: $*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || die "run with sudo"
getent passwd "$HOST_USER" >/dev/null || die "no such user: $HOST_USER (pass --user NAME)"
HOST_HOME="$(getent passwd "$HOST_USER" | cut -d: -f6)"
DIAG_DIR="$HOST_HOME/.claude/host-diag"
grep -qx 'ID=ubuntu' /etc/os-release 2>/dev/null || echo ">> warning: not Ubuntu; carrying on, but this was written for Ubuntu." >&2

PENDING=0          # items --check found would change
UNITS_CHANGED=0
ok()      { printf '  [ok]      %s\n' "$1"; }
changed() { printf '  [changed] %s\n' "$1"; }
pending() { printf '  [missing] %s\n' "$1"; PENDING=$((PENDING + 1)); }

# item LABEL TEST APPLY: run TEST; if it fails, report and (unless --check) run APPLY.
item() {
  if eval "$2"; then ok "$1"
  elif [ "$MODE" = check ]; then pending "$1"
  else eval "$3"; changed "$1"; fi
}

# put_file SRC DEST MODE OWNER:GROUP - install SRC at DEST when the content, mode or owner differs.
put_file() {
  local src="$1" dest="$2" mode="$3" owner="$4"
  if [ -f "$dest" ] && cmp -s "$src" "$dest" \
     && [ "$(stat -c '%a %U:%G' "$dest")" = "$mode $owner" ]; then
    ok "$dest"
  elif [ "$MODE" = check ]; then
    pending "$dest"
  else
    install -D -m "$mode" -o "${owner%%:*}" -g "${owner##*:}" "$src" "$dest"
    changed "$dest"
    case "$dest" in /etc/systemd/*) UNITS_CHANGED=1 ;; esac
  fi
}

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
render() { sed -e "s|@HOST_USER@|$HOST_USER|g" -e "s|@HOST_HOME@|$HOST_HOME|g" "$1" > "$2"; }

# ---------------------------------------------------------------------------------------------
if [ "$MODE" = revoke ]; then
  echo ">> revoking claude-diag diagnostics"
  systemctl disable --now claude-diag-ssh.socket 2>/dev/null || true
  rm -f "$SOCKET_UNIT" "$SERVICE_UNIT" "$OOMD_DROPIN" "$SUDOERS" "$TMPFILES" "$DIAG_DIR/sshd.sock" "$DIAG_DIR/known_hosts"
  rm -rf "$LIBEXEC"
  systemctl daemon-reload
  if [ -f "$ETC/masked-ssh" ]; then
    systemctl unmask ssh.service ssh.socket
    echo "   unmasked ssh.service/ssh.socket (masked by the grant); openssh-server stays installed."
  fi
  rm -rf "$ETC"
  if getent passwd "$ACCOUNT" >/dev/null; then
    pkill -u "$ACCOUNT" 2>/dev/null || true
    userdel --remove "$ACCOUNT"
  fi
  echo ">> done. The key pair in $DIAG_DIR is left for you to delete."
  exit 0
fi

echo ">> host user: $HOST_USER ($HOST_HOME); mode: $MODE"

echo ">> protecting $HOST_HOME"
item "$HOST_HOME closed to other users" \
  '[ $(( 0$(stat -c %a "$HOST_HOME") & 07 )) -eq 0 ]' \
  'chmod o-rwx "$HOST_HOME"'

echo ">> the container's key"
PUBKEY="$DIAG_DIR/id_ed25519.pub"
[ -f "$PUBKEY" ] || die "no $PUBKEY - create it from inside the container first:
    mkdir -p ~/.claude/host-diag && ssh-keygen -t ed25519 -N '' -C claude-diag-container -f ~/.claude/host-diag/id_ed25519"
grep -q '^ssh-ed25519 ' "$PUBKEY" || die "$PUBKEY is not an ed25519 public key"
ok "$PUBKEY"

echo ">> openssh-server (for /usr/sbin/sshd only)"
if dpkg-query -W -f='${Status}' openssh-server 2>/dev/null | grep -q 'install ok installed'; then
  ok "openssh-server installed (its own ssh.service left as it is)"
elif [ "$MODE" = check ]; then
  pending "openssh-server (would mask ssh.service/ssh.socket, then install)"
else
  systemctl mask ssh.service ssh.socket
  install -d -m 0755 "$ETC"; : > "$ETC/masked-ssh"
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server \
    || { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server; }
  changed "openssh-server installed; ssh.service and ssh.socket MASKED (no port opened)"
fi

echo ">> the $ACCOUNT account"
item "user $ACCOUNT" \
  'getent passwd "$ACCOUNT" >/dev/null' \
  'useradd --system --user-group --create-home --home-dir "$ACCOUNT_HOME" --shell /bin/bash --comment "Claude Code read-only host diagnostics" "$ACCOUNT"'
if getent passwd "$ACCOUNT" >/dev/null || [ "$MODE" = apply ]; then
  item "$ACCOUNT has no password (key login only)" \
    '[ "$(getent shadow "$ACCOUNT" | cut -d: -f2)" = "*" ]' \
    'usermod -p "*" "$ACCOUNT"'
  item "$ACCOUNT groups are exactly $ACCOUNT + $GROUPS_WANTED" \
    '[ "$(id -nG "$ACCOUNT" | tr " " "\n" | sort | tr "\n" " ")" = "$(printf "%s\n" "$ACCOUNT" ${GROUPS_WANTED//,/ } | sort | tr "\n" " ")" ]' \
    'usermod -G "$GROUPS_WANTED" "$ACCOUNT"'
fi

echo ">> the private sshd ($ETC)"
put_file "$HERE/files/sshd_config" "$ETC/sshd_config" 644 root:root
item "$ETC/ssh_host_ed25519_key" \
  '[ -f "$ETC/ssh_host_ed25519_key" ]' \
  'ssh-keygen -q -t ed25519 -N "" -C claude-diag-host -f "$ETC/ssh_host_ed25519_key"'
printf 'restrict %s\n' "$(cut -d' ' -f1,2 "$PUBKEY") claude-diag-container" > "$TMP/authorized_keys"
put_file "$TMP/authorized_keys" "$ETC/authorized_keys" 644 root:root
if [ -f "$ETC/ssh_host_ed25519_key.pub" ]; then
  printf 'claude-diag-host %s\n' "$(cut -d' ' -f1,2 "$ETC/ssh_host_ed25519_key.pub")" > "$TMP/known_hosts"
  put_file "$TMP/known_hosts" "$DIAG_DIR/known_hosts" 644 "$HOST_USER:$(id -gn "$HOST_USER")"
fi
put_file "$HERE/files/tmpfiles.conf" "$TMPFILES" 644 root:root
[ "$MODE" = check ] || systemd-tmpfiles --create "$TMPFILES"

echo ">> the sudo wrappers ($LIBEXEC)"
for w in podman-diag user-systemctl varlog-read; do
  put_file "$HERE/libexec/$w" "$LIBEXEC/$w" 755 root:root
done

echo ">> sudoers"
render "$HERE/files/sudoers" "$TMP/sudoers"
visudo -cqf "$TMP/sudoers" || die "files/sudoers does not parse; nothing installed"
put_file "$TMP/sudoers" "$SUDOERS" 440 root:root

echo ">> the socket"
render "$HERE/files/claude-diag-ssh.socket" "$TMP/claude-diag-ssh.socket"
put_file "$TMP/claude-diag-ssh.socket" "$SOCKET_UNIT" 644 root:root
put_file "$HERE/files/claude-diag-ssh@.service" "$SERVICE_UNIT" 644 root:root
if [ "$MODE" = apply ]; then
  [ "$UNITS_CHANGED" = 0 ] || systemctl daemon-reload
  sshd -t -f "$ETC/sshd_config" || die "sshd rejects $ETC/sshd_config"
  if [ "$UNITS_CHANGED" = 1 ] && systemctl is-active -q claude-diag-ssh.socket; then
    systemctl restart claude-diag-ssh.socket
  fi
fi
item "claude-diag-ssh.socket enabled and listening" \
  'systemctl is-enabled -q claude-diag-ssh.socket 2>/dev/null && systemctl is-active -q claude-diag-ssh.socket' \
  'systemctl enable --now -q claude-diag-ssh.socket'

echo ">> systemd-oomd: no memory-pressure kill of user sessions (see files/oomd-user-pressure.conf)"
UNITS_CHANGED=0
put_file "$HERE/files/oomd-user-pressure.conf" "$OOMD_DROPIN" 644 root:root
[ "$MODE" = check ] || [ "$UNITS_CHANGED" = 0 ] || systemctl daemon-reload
HOST_UID="$(id -u "$HOST_USER")"
if systemctl is-active -q "user@$HOST_UID.service"; then
  item "user@$HOST_UID.service no longer under oomd's pressure kill" \
    '[ "$(systemctl show "user@$HOST_UID.service" -p ManagedOOMMemoryPressure --value)" = auto ]' \
    'die "user@$HOST_UID.service still shows ManagedOOMMemoryPressure=$(systemctl show "user@$HOST_UID.service" -p ManagedOOMMemoryPressure --value) after daemon-reload; log out and back in"'
fi

if [ "$MODE" = check ]; then
  echo ">> $PENDING item(s) would change."
  [ "$PENDING" = 0 ]
else
  echo ">> done. From inside the container: scripts/claude-diagnostics/client/host-diag id"
fi
