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
#   * Otherwise pulls the latest image, then starts a new DETACHED container
#     (podman run -d ... sleep infinity) and opens a bash shell inside it
#     (podman exec), mounting:
#       - the repo at /workspace (or the path it declares via container-workdir)
#       - the host's ~/.claude.json and ~/.claude/ into /home/agent so Claude
#         Code auth, config, skills, and memory persist across containers
#       - any extra host mounts the repo declares (see below)
#     publishing the ports the repo declares, passing the host's sound devices
#     through (see "Audio" below), and apt-installing the packages the repo
#     declares via container-apt.
#
# Because the container name is derived per repo (<prefix>-<repo-dir-name>),
# "already running" only ever matches the SAME repo: launching from gm-assistant
# twice attaches the second time, but launching from a different repo starts its
# own container.
#
# Container lifetime is decoupled from every terminal: PID 1 is `sleep infinity`
# and EVERY shell - including the first launch's - is a podman exec session, so
# exiting or closing any terminal never stops the container or kills the other
# shells. The container runs until explicitly removed (--fresh, or
# `podman rm -f <name>`). There is deliberately no --rm: a container stopped
# from outside (host reboot, podman stop) stays on disk, and the next launch
# restarts and re-attaches it instead of rebuilding from scratch.
#
# Per-repo config lives in the repo's CLAUDE.md as greppable HTML-comment lines.
# Format is HOST:CONTAINER (space-separated for multiples):
#
#   <!-- container-ports: 8080:8080 8091:8090 -->
#   <!-- container-mounts: ..:/host-l7r-repo -->
#   <!-- container-workdir: /gm-assistant -->
#   <!-- container-apt: libmagic1 antiword libcairo2 -->
#
# container-apt (optional) lists apt packages installed as root on a FRESH
# launch, on top of the baseline the script always installs (see "Audio").
# Attaching to an existing container installs nothing, so a changed list takes
# effect on the next --fresh. It is best-effort: a failed update/install warns
# and still drops you into the shell (you may just be offline). Skip it for a
# launch with --no-apt. This is for SYSTEM packages only - language-level deps
# (pip, npm, playwright browsers) stay in the repo's own setup docs.
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
# Audio: the container gets the host's sound devices (--device /dev/snd, when
# the host has any), alsa-utils, and a generated /etc/asound.conf pointing
# ALSA's "default" at the detected mic and speaker - so Claude Code's /voice can
# record. All three are needed, and each missing piece fails differently:
#   * no device nodes -> /proc is NOT namespaced, so /proc/asound/cards shows
#     the host's mic and voice's availability probe passes; then the capture
#     floods the terminal with "cannot find card '0'" / "Unknown PCM default".
#   * devices but no asound.conf -> "audio open error: No such file or
#     directory", because stock ALSA aims "default" at hw:0,0 (see the
#     generation step near the bottom of this script for why that's wrong).
# This is raw ALSA access, bypassing the host's PulseAudio/PipeWire; that daemon
# suspends idle capture devices, so the mic is normally free, but a host app
# actively recording (a Zoom call) can make it "busy" until it lets go.
#
# Usage:
#   launch-container.sh [--name NAME] [--no-ports] [--no-claude] [--no-pull]
#                       [--no-apt] [--no-update] [--fresh] [--help]
#
# A fresh launch first runs `podman pull` for the latest image; --no-pull skips
# that (offline, or to save time), as --no-apt skips the package install and
# --no-update skips the in-container `claude update`. It also leaves
# `claude --dangerously-skip-permissions` in the shell history, so the first
# thing you do in the new container is Up-Enter.
# Attaching to a running container never pulls, installs, or updates.
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
APT=1
UPDATE=1
CLAUDE_SRC="${CLAUDE_SRC:-$HOME}"
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --no-ports) PUBLISH_PORTS=0; shift ;;
    --no-claude) MOUNT_CLAUDE=0; shift ;;
    --no-pull) PULL=0; shift ;;
    --no-apt) APT=0; shift ;;
    --no-update) UPDATE=0; shift ;;
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
  --detach
  --name "$NAME"
  --uidmap 0:1:1000 --uidmap 1000:0:1 --uidmap 1001:1001:64536
  --gidmap 0:1:1000 --gidmap 1000:0:1 --gidmap 1001:1001:64536
  --env HOME=/home/agent
  --workdir "$WORKDIR"
  --memory "$MEMORY" --memory-swap "$MEMORY"
  --volume "${REPO_ROOT}:${WORKDIR}:Z"
)

# Host sound devices, so Claude Code's /voice can record (see "Audio" above).
# Access comes from the uidmap: container uid 1000 IS the invoking user, and
# /dev/snd/* carries a logind ACL granting the seat user rw - verified by
# reading the nodes from inside, where they show up as nobody:nogroup with a
# trailing '+' (the ACL) and are still readable/writable. Conditional because
# `--device` on a missing path is a hard `podman run` failure: a host with no
# sound card at all (headless server, minimal VM) must still get a container.
AUDIO=0
if [ -d /dev/snd ]; then
  RUN_ARGS+=( --device /dev/snd )
  AUDIO=1
else
  echo ">> note: no /dev/snd on this host; container gets no audio (voice input won't work)."
fi

# Host Claude Code config, mounted so auth, settings, skills, and per-project
# memory persist across container recreations. The host paths are created if
# missing so even the very first launch persists - otherwise an in-container
# login would be written container-internally and lost when the container is
# removed (an empty {} is a valid starting config). Uses the shared SELinux relabel (:z), not the private
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

# Detached, with `sleep infinity` as PID 1, so that no terminal is special:
# every shell - this first one included - is an exec session, and exiting any
# of them leaves the container and the other shells running. (The old design
# ran bash as PID 1 with --rm, so a clean `exit` in the original terminal
# stopped the container and killed every other attached shell with it.)
# Teardown is explicit: --fresh or `podman rm -f`.
echo ">> starting '$NAME' detached (workdir $WORKDIR) from $IMAGE"
podman run "${RUN_ARGS[@]}" "$IMAGE" sleep infinity >/dev/null

# ---- system packages (fresh containers only) ----
#
# Baseline alsa-utils gives /voice a working `arecord` (its first-choice
# recorder after the bundled native one, and the way to debug the mic by hand:
# `arecord -l`), plus whatever the repo declares via container-apt. Runs as
# container root rather than `sudo` inside the agent user, so it does not
# depend on the image keeping passwordless sudo. `apt-get update` first because
# a freshly pulled image can carry a stale index. Best-effort by design: a
# broken install should not cost you the shell, so it warns and continues.
if [ "$APT" -eq 1 ]; then
  PACKAGES=(alsa-utils)
  while IFS= read -r pkg; do
    [ -n "$pkg" ] || continue
    PACKAGES+=( "$pkg" )
  done < <(read_directive container-apt)
  echo ">> installing packages: ${PACKAGES[*]}"
  if ! podman exec --user root --env DEBIAN_FRONTEND=noninteractive "$NAME" \
       bash -c 'apt-get update -qq && apt-get install -y -qq --no-install-recommends "$@"' \
       _ "${PACKAGES[@]}"; then
    echo ">> warning: package install failed (offline? stale mirror?); continuing." >&2
    echo "   Retry by hand inside the container with: sudo apt-get install -y ${PACKAGES[*]}" >&2
  fi
else
  echo ">> --no-apt: not installing packages."
fi

# ---- ALSA default device (fresh containers only) ----
#
# Passing /dev/snd through is necessary but NOT sufficient. ALSA's built-in
# "default" PCM is hw:0,0, and on plenty of modern cards device 0 is not a
# capture device at all - this laptop's SOF/soundwire card puts the mic on 0,4
# and the speaker on 0,2, with 0,3 being an amp-feedback loopback. So `arecord`
# with no -D, which is exactly what Claude Code's voice probe and its bundled
# libasound recorder use, dies with "audio open error: No such file or
# directory" even though `arecord -D plughw:0,4` records perfectly. It never
# bites on the host because PulseAudio/PipeWire ships an asound.conf aiming
# default at the sound server, which knows the right device.
#
# So generate one. Device numbers are DETECTED, not hardcoded: /proc/asound/pcm
# is readable in the container (that path is not namespaced) and names each
# device, so prefer a capture device that looks like a mic over a feedback or
# loopback, and a playback device that looks like speakers over HDMI. `plug`
# wraps both so voice's 16 kHz mono is resampled to whatever the hardware
# demands. Runs even under --no-apt: the native recorder links libasound
# directly and needs this whether or not alsa-utils is installed.
if [ "$AUDIO" -eq 1 ]; then
  echo ">> configuring ALSA default device"
  podman exec -i --user root "$NAME" bash -s <<'PROVISION_ALSA' || \
    echo ">> warning: could not configure ALSA default; /voice may fail to open the mic." >&2
set -eu
[ -r /proc/asound/pcm ] || { echo "no /proc/asound/pcm; skipping" >&2; exit 0; }

# Emit "card,device" for the best match in one direction, or nothing.
pick() {
  awk -F: -v want="$1" -v prefer="$2" -v avoid="$3" '
    BEGIN { best = -1 }
    {
      has = 0
      for (i = 4; i <= NF; i++) if ($i ~ want) has = 1
      if (!has) next
      split($1, a, "-"); nm = tolower($2)
      score = 1
      if (avoid  != "" && nm ~ avoid)  score = 0
      if (prefer != "" && nm ~ prefer) score = 2
      if (score > best) { best = score; res = (a[1] + 0) "," (a[2] + 0) }
    }
    END { if (best >= 0) print res }
  ' /proc/asound/pcm
}

capture=$(pick capture 'mic' 'feedback|loopback|monitor')
playback=$(pick playback 'speaker|analog|headphone' 'hdmi')

if [ -z "$capture" ]; then
  echo "no capture device found in /proc/asound/pcm; leaving ALSA default alone" >&2
  exit 0
fi
[ -n "$playback" ] || playback="$capture"

cat > /etc/asound.conf <<EOF
# Generated by launch-container.sh. ALSA's stock default is hw:0,0, which is
# not a capture device on every card; these were detected from
# /proc/asound/pcm at container-create time.
pcm.!default {
    type asym
    playback.pcm "plughw:${playback%,*},${playback#*,}"
    capture.pcm "plughw:${capture%,*},${capture#*,}"
}
ctl.!default {
    type hw
    card ${capture%,*}
}
EOF
echo "   capture -> plughw:${capture%,*},${capture#*,}   playback -> plughw:${playback%,*},${playback#*,}"
PROVISION_ALSA
fi

# ---- Claude Code update (fresh containers only) ----
#
# The image ships whatever `claude` build was current when it was published, and
# that binary lives in the CONTAINER's own ~/.local/bin - not in the mounted
# ~/.claude - so it does not persist, and every fresh container starts over from
# the image's version. `podman pull` above cannot fix that either: it refreshes
# the image, which is only rebuilt occasionally. So update in place instead.
#
# Runs as the container's default user (agent), NOT `--user root` like the apt
# step: ~/.local/bin belongs to agent, and as root the update would install into
# root's home where nothing looks for it. Best-effort by design, same as apt - an
# offline host should cost you a warning, not the shell.
if [ "$UPDATE" -eq 1 ]; then
  echo ">> updating Claude Code"
  podman exec "$NAME" bash -c '
    PATH="$HOME/.local/bin:$PATH"
    command -v claude >/dev/null 2>&1 || { echo "   no claude on PATH; skipping"; exit 0; }
    claude update' \
    || echo ">> warning: claude update failed (offline?); using the image's version." >&2
else
  echo ">> --no-update: not updating Claude Code."
fi

# ---- seed bash history (fresh containers only) ----
#
# The first command in a new container is nearly always Claude Code with
# permission prompts off, so pre-load it: an interactive bash reads $HISTFILE at
# startup, so writing the line here makes it the most recent history entry and
# Up-Enter runs it. Must be the LAST provisioning step so nothing lands after it.
#
# Written as the container's default user (agent), because a root-owned
# ~/.bash_history would silently stop every later shell from saving its history.
HISTORY_SEED='claude --dangerously-skip-permissions'
echo ">> seeding bash history with: $HISTORY_SEED"
podman exec "$NAME" bash -c 'printf "%s\n" "$1" >> "$HOME/.bash_history"' _ "$HISTORY_SEED" \
  || echo ">> warning: could not seed bash history; type the command by hand." >&2

exec podman exec -it "$NAME" bash
