#!/usr/bin/env bash
#
# launch-container.sh - start or attach to a repo's Claude Code dev container.
#
# One container per repo, with a deterministic name, so you never again have to
# wonder "which of my containers is this, and did it get port mapping?".
#
# What it does:
#   * Derives a stable container name from the repo (<prefix>-<repo-dir-name>).
#   * If that container is ALREADY RUNNING, opens a fresh bash shell inside it
#     (podman exec) instead of starting a second container - and prints the
#     ports that container actually has published.
#   * Otherwise pulls the latest image, then starts a new container
#     (podman run --rm -it ... bash), mounting:
#       - the repo at /workspace (or the path it declares via container-workdir)
#       - the host's ~/.claude.json and ~/.claude/ into /home/agent so Claude
#         Code auth, config, skills, and memory persist across containers
#       - any extra host mounts the repo declares (see below)
#     and publishing the ports the repo declares.
#
# Because the container name is derived per repo (<prefix>-<repo-dir-name>),
# "already running" only ever matches the SAME repo: launching from gm-assistant
# twice attaches the second time, but launching from a different repo starts its
# own container.
#
# Per-repo config lives in the repo's CLAUDE.md as greppable HTML-comment lines.
# Format is HOST:CONTAINER (space-separated for multiples):
#
#   <!-- container-ports: 8080:8080 8091:8090 -->
#   <!-- container-mounts: ..:/host-l7r-repo -->
#   <!-- container-workdir: /gm-assistant -->
#
# container-workdir (optional, default /workspace) is where the repo is mounted
# and the shell starts. Give each repo a DISTINCT path (e.g. /gm-assistant,
# /character-sheet) so Claude Code's per-project memory/history under
# ~/.claude/projects/ does not collide - that namespace is keyed off the cwd
# path, and ~/.claude is shared across all of these containers.
#
# Port convention: first is the repo's primary webapp, second the secondary
# (e.g. a blind-eval webapp). Host and container ports may differ so several
# repos that all serve on 8080 inside the container each get a distinct host port.
#
# Mount HOST paths may be absolute, start with ~ (the invoking user's home), or
# be RELATIVE TO THE REPO ROOT - so "..:/host-l7r-repo" mounts the repo's parent
# directory (where the sibling l7r notes repo lives) at /host-l7r-repo, wherever
# the tree is checked out (/home/eli/l7r/<repo>, /data/dev/l7r/<repo>, ...).
#
# Usage:
#   launch-container.sh [--name NAME] [--no-ports] [--no-claude] [--no-pull]
#                       [--fresh] [--help]
#
# A fresh launch first runs `podman pull` for the latest image; --no-pull skips
# that (offline, or to save time). Attaching to a running container never pulls.
# --no-claude skips mounting the host ~/.claude.json and ~/.claude/ - use it on a
# shared/work machine so the container does NOT inherit that host's default Claude
# account (you log in fresh inside instead, on your own account). Point at a
# specific config dir with CLAUDE_SRC=/path (defaults to ~). Reusable across
# repos: run from any repo root; it reads the CURRENT repo's CLAUDE.md. Override
# the name prefix with CONTAINER_PREFIX, the image with CONTAINER_IMAGE.

set -euo pipefail

IMAGE="${CONTAINER_IMAGE:-docker.io/docker/sandbox-templates:claude-code}"
PREFIX="${CONTAINER_PREFIX:-claude}"
MEMORY="8g"

die() { echo "error: $*" >&2; exit 1; }

show_help() {
  sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^#\{0,1\} \{0,1\}//'
  exit 0
}

# ---- parse args ----
NAME=""
PUBLISH_PORTS=1
FRESH=0
MOUNT_CLAUDE=1
PULL=1
CLAUDE_SRC="${CLAUDE_SRC:-$HOME}"
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --no-ports) PUBLISH_PORTS=0; shift ;;
    --no-claude) MOUNT_CLAUDE=0; shift ;;
    --no-pull) PULL=0; shift ;;
    --fresh) FRESH=1; shift ;;
    -h|--help) show_help ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

command -v podman >/dev/null 2>&1 || die "podman not found on PATH"

# ---- locate the repo and its config ----
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REPO_NAME="$(basename "$REPO_ROOT")"
[ -n "$NAME" ] || NAME="${PREFIX}-${REPO_NAME}"
CLAUDE_MD="$REPO_ROOT/CLAUDE.md"

# Resolve a declared host path: ~ -> the invoking user's home, relative -> against
# the repo root (so ".." is the repo's parent), absolute kept as-is; canonicalize.
resolve_host_path() {
  local p="$1"
  case "$p" in
    "~") p="$HOME" ;;
    "~/"*) p="$HOME/${p#\~/}" ;;
    /*) : ;;
    *) p="$REPO_ROOT/$p" ;;
  esac
  realpath -m "$p" 2>/dev/null || readlink -f "$p" 2>/dev/null || printf '%s' "$p"
}

# Read a greppable "<!-- key: a:b c:d -->" directive from CLAUDE.md, one token
# per line. Matches the HTML-comment form specifically so prose that merely
# mentions the key (e.g. these docs) is never picked up.
read_directive() {
  [ -f "$CLAUDE_MD" ] || return 0
  grep -m1 "<!-- $1:" "$CLAUDE_MD" 2>/dev/null \
    | sed "s/.*<!-- $1://; s/-->.*//" \
    | tr -s ' \t' '\n' \
    | sed '/^$/d' || true
}

# Where to mount the repo and start the shell. Default /workspace; a repo can
# declare a distinct path via container-workdir so its Claude Code project memory
# (keyed off the cwd path) does not collide with other repos under shared
# ~/.claude.
WORKDIR="$(read_directive container-workdir | head -n1)"
[ -n "$WORKDIR" ] || WORKDIR="/workspace"
case "$WORKDIR" in
  /*) : ;;
  *) die "container-workdir must be an absolute path (got '$WORKDIR')" ;;
esac

# ---- if a container of this name exists, attach (or recreate with --fresh) ----
if [ "$FRESH" -eq 1 ] && podman container exists "$NAME" 2>/dev/null; then
  echo ">> --fresh: removing existing container '$NAME'"
  podman rm -f "$NAME" >/dev/null
fi

if [ -n "$(podman ps -q -f "name=^${NAME}$" 2>/dev/null)" ]; then
  echo ">> '$NAME' is already running; opening a new bash shell inside it."
  echo ">> ports published by the running container:"
  podman port "$NAME" 2>/dev/null | sed 's/^/     /' || true
  exec podman exec -it "$NAME" bash
fi

if podman container exists "$NAME" 2>/dev/null; then
  echo ">> '$NAME' exists but is stopped; starting it and attaching."
  podman start "$NAME" >/dev/null
  exec podman exec -it "$NAME" bash
fi

# ---- build a fresh run ----
#
# The uid/gid maps make the container's `agent` user (uid 1000) write files that
# the host sees as owned by YOU - without which everything the container touched
# in the bind-mounted repo would land owned by some subuid and need chown'ing.
#
# They do NOT hard-code your UID. Under ROOTLESS podman the middle field of
# CONTAINER:HOST:SIZE is not a real host id but a slot in the intermediate user
# namespace podman sets up, where slot 0 is the invoking user (whatever their UID
# is - 1000, 3000, 5000) and slots 1..65536 are their /etc/subuid range. So
# "1000:0:1" means "container uid 1000 -> the invoking user", and the script
# never has to know the number. The other two lines park container root (0..999)
# and everything above 1000 in the subuid range so they can't collide with it.
#
# What this DOES depend on is the SIZE of the subuid/subgid allocation: the maps
# reach intermediate slot 1001+64536-1 = 65536, and the near-universal default
# allocation is exactly 65536 entries - a perfect fit with zero headroom. A host
# handing out a smaller range makes `podman run` fail outright. Check with:
#   grep "^$USER:" /etc/subuid /etc/subgid    # third field must be >= 65536
#
# All of the above is rootless-only. Under `sudo podman` the middle field means a
# REAL host id, so "1000:0:1" would map the agent user to actual root and
# /etc/subuid is not consulted - do not run this script with sudo.
RUN_ARGS=(
  --interactive --tty --rm
  --name "$NAME"
  --uidmap 0:1:1000 --uidmap 1000:0:1 --uidmap 1001:1001:64536
  --gidmap 0:1:1000 --gidmap 1000:0:1 --gidmap 1001:1001:64536
  --env HOME=/home/agent
  --workdir "$WORKDIR"
  --memory "$MEMORY" --memory-swap "$MEMORY"
  --volume "${REPO_ROOT}:${WORKDIR}:Z"
)

# Host Claude Code config, mounted so auth, settings, skills, and per-project
# memory persist across these --rm containers. The host paths are created if
# missing so even the very first launch persists - otherwise an in-container
# login would be written container-internally and lost on exit (an empty {} is a
# valid starting config). Uses the shared SELinux relabel (:z), not the private
# :Z used for the workspace. Skip with --no-claude (e.g. on a work machine, so
# the container does not inherit that host's default Claude account); CLAUDE_SRC
# overrides where it is read from.
if [ "$MOUNT_CLAUDE" -eq 1 ]; then
  mkdir -p "$CLAUDE_SRC/.claude"
  [ -e "$CLAUDE_SRC/.claude.json" ] || echo '{}' > "$CLAUDE_SRC/.claude.json"
  RUN_ARGS+=( --volume "$CLAUDE_SRC/.claude.json:/home/agent/.claude.json:z" )
  RUN_ARGS+=( --volume "$CLAUDE_SRC/.claude:/home/agent/.claude:z" )
  echo ">> Claude config: mounting from $CLAUDE_SRC (created if missing, so login persists)"
else
  echo ">> --no-claude: NOT mounting host Claude config; log in fresh inside the"
  echo "   container to keep it separate from this host's default account."
fi

# Extra host mounts declared by the repo. The HOST side may be absolute, ~-based,
# or relative to the repo root (so ".." is the repo's parent directory).
#
# Existence alone is a weak check for a RELATIVE source: ".." always exists, so a
# repo cloned somewhere unexpected (~/projects/gm-assistant) would silently mount
# the wrong directory and only fail much later, when something looks for a file
# that isn't there. So a mount may also declare marker paths that must be present
# under the source for it to count as the right directory - here setting/ and
# rules/ identify the l7r notes repo. Missing markers means we skip the mount and
# say so, rather than mounting a lookalike.
mount_markers() {
  case "$1" in
    /host-l7r-repo) echo "setting rules" ;;
    *) : ;;
  esac
}

# Shared SELinux relabel (:z), not the private :Z used for the workspace: these
# are host directories used OUTSIDE the container too (the GM edits l7r.md from
# their laptop), and :Z would relabel them container-private and lock the host
# out. On non-SELinux distros both are no-ops.
while IFS= read -r m; do
  [ -n "$m" ] || continue
  host_raw="${m%%:*}"
  container_path="${m#*:}"
  host="$(resolve_host_path "$host_raw")"
  if [ ! -e "$host" ]; then
    echo ">> warning: mount source '$host_raw' -> '$host' does not exist; skipping." >&2
    continue
  fi
  missing=""
  for marker in $(mount_markers "$container_path"); do
    [ -d "$host/$marker" ] || missing="$missing $marker"
  done
  if [ -n "$missing" ]; then
    echo ">> warning: '$host' is missing${missing}/ so it does not look like the" >&2
    echo "   expected ${container_path} content; skipping that mount." >&2
    continue
  fi
  RUN_ARGS+=( --volume "${host}:${container_path}:z" )
  echo ">> mount: ${host} -> ${container_path}"
done < <(read_directive container-mounts)

# Ports declared by the repo.
if [ "$PUBLISH_PORTS" -eq 1 ]; then
  found_ports=0
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    case "$p" in
      [0-9]*:[0-9]*) : ;;
      *) echo ">> warning: ignoring malformed port '$p' (want HOST:CONTAINER)" >&2; continue ;;
    esac
    RUN_ARGS+=( --publish "$p" )
    echo ">> publish: host ${p%%:*} -> container ${p##*:}"
    found_ports=1
  done < <(read_directive container-ports)
  [ "$found_ports" -eq 1 ] || echo ">> note: no 'container-ports:' in CLAUDE.md; nothing published."
else
  echo ">> --no-ports: nothing published."
fi

if [ "$PULL" -eq 1 ]; then
  echo ">> pulling latest image: $IMAGE"
  podman pull "$IMAGE" || echo ">> warning: pull failed; using the local image if present." >&2
else
  echo ">> --no-pull: not pulling; using the local image."
fi

echo ">> starting '$NAME' (workdir $WORKDIR) from $IMAGE"
exec podman run "${RUN_ARGS[@]}" "$IMAGE" bash
