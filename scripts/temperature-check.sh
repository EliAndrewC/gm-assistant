#!/usr/bin/env bash
#
# temperature-check.sh - read the CPU temperature and say plainly whether it is
# NORMAL, CONCERNING, or BAD.
#
# Run this on the laptop itself, not inside a container - a container may not
# expose the host's thermal chips. Prefers `lm-sensors` (coretemp) and falls
# back to the kernel's /sys/class/thermal zones if sensors is not installed.
#
#   ./scripts/temperature-check.sh
#
# Exit status mirrors the verdict, so it is scriptable:
#   0 = normal, 1 = concerning, 2 = bad, 3 = could not read a temperature.
#
set -euo pipefail

# ---- thresholds (degrees C) -------------------------------------------------
# A reading is BAD at/above BAD_ABS or within CRIT_BAD_MARGIN of the chip's own
# reported crit temp; CONCERNING at/above WARN_ABS or within CRIT_WARN_MARGIN of
# crit. The absolute numbers suit a typical Intel laptop (Tj max ~100C); the
# crit-margin guards catch chips that report a lower crit.
WARN_ABS=90
BAD_ABS=100
CRIT_WARN_MARGIN=12
CRIT_BAD_MARGIN=3
DEFAULT_CRIT=100   # assumed only when the chip reports no crit temp

# ---- colors (only when writing to a terminal) -------------------------------
if [[ -t 1 ]]; then
  RED=$'\e[31m'; YEL=$'\e[33m'; GRN=$'\e[32m'; BLD=$'\e[1m'; RST=$'\e[0m'
else
  RED=; YEL=; GRN=; BLD=; RST=
fi

# ge A B -> true if float A >= float B
ge() { awk "BEGIN{exit !($1 >= $2)}"; }

pkg_temp=""; crit=""; hottest_core=""; fans=""; source=""

if command -v sensors >/dev/null 2>&1; then
  source="lm-sensors"
  out="$(sensors 2>/dev/null || true)"

  # Package temp and its crit, from the "Package id N:" line.
  pkg_line="$(grep -m1 -E '^Package id' <<<"$out" || true)"
  if [[ -n "$pkg_line" ]]; then
    pkg_temp="$(sed -E 's/.*:[[:space:]]*\+?([0-9]+(\.[0-9]+)?).*/\1/' <<<"$pkg_line")"
    crit="$(sed -nE 's/.*crit[[:space:]]*=[[:space:]]*\+?([0-9]+(\.[0-9]+)?).*/\1/p' <<<"$pkg_line")"
  fi

  # Hottest individual core (a single core can spike above the package temp).
  hottest_core="$(grep -E '^Core [0-9]+:' <<<"$out" \
      | sed -E 's/.*:[[:space:]]*\+?([0-9]+(\.[0-9]+)?).*/\1/' \
      | sort -rn | head -1 || true)"

  # Fan RPMs, if the platform reports them (informational only).
  fans="$(grep -iE '(^| )fan[0-9]*:|Fan:' <<<"$out" | grep -i 'RPM' || true)"
fi

# Fallback: kernel thermal zones (value is millidegrees C).
if [[ -z "$pkg_temp" ]]; then
  source="sysfs"
  for z in /sys/class/thermal/thermal_zone*; do
    [[ -r "$z/temp" ]] || continue
    t=$(( $(cat "$z/temp") / 1000 ))
    [[ "$(cat "$z/type" 2>/dev/null || true)" == "x86_pkg_temp" ]] && pkg_temp="$t"
    if [[ -z "$hottest_core" || "$t" -gt "$hottest_core" ]]; then hottest_core="$t"; fi
  done
  [[ -z "$pkg_temp" ]] && pkg_temp="${hottest_core:-}"
fi

if [[ -z "$pkg_temp" ]]; then
  echo "Could not read any CPU temperature." >&2
  echo "Install and load the sensor, then retry:" >&2
  echo "  sudo apt install lm-sensors && sudo modprobe coretemp && sensors" >&2
  exit 3
fi

crit="${crit:-$DEFAULT_CRIT}"

# Judge on the hotter of package / hottest-core.
metric="$pkg_temp"
if [[ -n "$hottest_core" ]] && ge "$hottest_core" "$metric"; then metric="$hottest_core"; fi

warn_by_crit="$(awk "BEGIN{printf \"%.1f\", $crit - $CRIT_WARN_MARGIN}")"
bad_by_crit="$(awk "BEGIN{printf \"%.1f\", $crit - $CRIT_BAD_MARGIN}")"

sev=0; verdict="NORMAL - comfortable headroom"; color="$GRN"
if ge "$metric" "$WARN_ABS" || ge "$metric" "$warn_by_crit"; then
  sev=1; verdict="CONCERNING - running hot, keep an eye on it"; color="$YEL"
fi
if ge "$metric" "$BAD_ABS" || ge "$metric" "$bad_by_crit"; then
  sev=2; verdict="BAD - at or near the thermal limit"; color="$RED"
fi

headroom="$(awk "BEGIN{printf \"%.1f\", $crit - $metric}")"

# ---- report -----------------------------------------------------------------
printf '%sCPU thermal check%s (via %s)\n' "$BLD" "$RST" "$source"
printf '  Package temp : %s C\n' "$pkg_temp"
[[ -n "$hottest_core" ]] && printf '  Hottest core : %s C\n' "$hottest_core"
printf '  Crit / limit : %s C  (throttles near here)\n' "$crit"
printf '  Headroom     : %s C\n' "$headroom"
if [[ -n "$fans" ]]; then
  echo "  Fans:"
  sed -E 's/^[[:space:]]*/    /' <<<"$fans"
fi
printf '%s  => %s%s\n' "$color$BLD" "$verdict" "$RST"

exit "$sev"
