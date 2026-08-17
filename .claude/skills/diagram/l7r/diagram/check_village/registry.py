"""The ordered gate-segment registry - DERIVED, not maintained (feature 109).

Until 2026-08-16 this file was 8,432 hand-maintained lines: an import roster naming every
segment function plus 1,371 `_GateSeg` rows restating facts the `segments_*` modules already
carry. Constitution Principle X clause 14 makes that shape a defect, and every field proved
derivable (specs/109-registry-derive/research.md): `free` is the keyword-only signature,
`writes` is the literal `_kept` return tuple, `checks`/`needs`/`meta`/`always` re-run feature
022's AST analysis (ported in `registry_analysis.py`), and execution order is the numeric name
key plus the placement decisions below. The pre-collapse rows are frozen in
`tests/fixtures/registry_legacy_rows.json`; `tests/check_village/test_registry_derive.py` proves the derived rows
equal them and holds the structural guards.

Two invariants carried over unchanged:

- **Row order IS execution order** (feature 022). Order = segments sorted by the numeric key in
  their name (`_seg_NNNN` / `_seg_NNNN_NNN`; the sub-numbered form sorts after its plain
  prefix), then each `_PLACEMENTS` entry spliced immediately after its anchor. A new segment
  placed by sub-numbering its name needs no table entry; `_PLACEMENTS` exists for segments whose
  number is only a label (see the entries' comments and the segments' own docstrings).
- Derivation cost (~1.5 s of AST work) is paid only when a package source changes: rows are
  cached under `.gencache/` keyed by a hash of every package file (the gencache precedent,
  feature 026). The cache is failure-soft in both directions - unreadable or stale falls back to
  live derivation, and an unwritable cache only logs.
"""

import hashlib
import json
import logging
import os
import re
import tempfile
from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any, NamedTuple

from .registry_analysis import _DerivationError, _derive_fields, _SegFields

_log = logging.getLogger(__name__)


class _GateSeg(NamedTuple):
    fn: Any
    free: tuple[str, ...]
    writes: tuple[str, ...]
    checks: tuple[str, ...]
    needs: tuple[str, ...]
    meta: bool
    always: bool


# Hand-added segments numbered past the legacy range but REGISTERED mid-sequence: the registry
# order is the execution contract and the number is only a label, so the position is a DECISION
# (clause 14: derive the derivable facts, keep the decided ones). Value = the segment it runs
# immediately after; a value may itself be a placed segment (chains splice in dict order). Each
# segment's own docstring records the same decision.
_PLACEMENTS: dict[str, str] = {
    "_seg_0596__dry_plot_seams_shared": "_seg_0317__dry_plot_furrows_vary",  # beside the dry-plot checks whose dry_plots binding it shares
    "_seg_0595__paddy_bunds_clear_the_supply_channels": "_seg_0532__bund_beans_on_bunds",  # beside the bund checks whose fields binding it shares
    "_seg_0600__comb_floor_ends_at_the_collector": "_seg_0595__paddy_bunds_clear_the_supply_channels",  # registered beside 0595, whose fields binding it shares
    "_seg_0597__woodland_commons_within_the_frame": "_seg_0600__comb_floor_ends_at_the_collector",  # the 2026-08-16 hand-added cluster runs consecutively here
    "_seg_0599__woodland_commons_on_dry_ground": "_seg_0597__woodland_commons_within_the_frame",  # (registry order at the feature-109 freeze)
    "_seg_0598__nucleated_records_cluster_seeding": "_seg_0599__woodland_commons_on_dry_ground",  # ditto
}

# Hand-decided needs kept over the derived value. The analysis is conservative about loop-carried
# reads, so for this hand-added segment it would add _csf_bad/_csf_ext/_csf_reach - names the
# body itself initializes before every read and which no earlier segment writes, so the
# dependency set is identical either way (research.md R5). The author's tighter value is the
# recorded truth; keep it.
_NEEDS_OVERRIDES: dict[str, tuple[str, ...]] = {
    "_seg_0324_500__comb_supply_commands_both_flanks": ("M", "check", "meta"),
}

_PKG_DIR = Path(__file__).resolve().parent
_CACHE_PATH = _PKG_DIR.parent / ".gencache" / "registry_rows.json"
_DERIVATION_VERSION = 1  # bump to invalidate caches when the derivation scheme itself changes


def _segment_functions() -> dict[str, Callable[..., dict[str, Any]]]:
    fns: dict[str, Callable[..., dict[str, Any]]] = {}
    for path in sorted(_PKG_DIR.glob("segments_*.py")):
        mod = import_module(f".{path.stem}", __package__)
        for nm in vars(mod):
            if nm.startswith("_seg_"):
                if nm in fns:
                    raise _DerivationError(f"duplicate segment name {nm}")
                fns[nm] = getattr(mod, nm)
    return fns


def _numeric_key(name: str) -> tuple[int, int]:
    m = re.match(r"_seg_(\d+)(?:_(\d+))?(?=_)", name)
    if m is None:
        raise _DerivationError(f"segment name {name} has no numeric key")
    return (int(m.group(1)), int(m.group(2)) if m.group(2) else -1)


def _ordered_names(names: set[str], placements: dict[str, str]) -> list[str]:
    """Execution order: numeric-key sort of the non-placed segments, then each placement spliced
    immediately after its anchor (recursively, so chains work). Guards fire on a stale table."""
    for placed, anchor in placements.items():
        if placed not in names:
            raise _DerivationError(f"placement entry {placed} names no live segment")
        if anchor not in names:
            raise _DerivationError(f"placement anchor {anchor} (for {placed}) names no live segment")
    base = sorted((nm for nm in names if nm not in placements), key=_numeric_key)
    keys = [_numeric_key(nm) for nm in base]
    for a, b in zip(keys, keys[1:], strict=False):
        if a >= b:
            raise _DerivationError(f"duplicate numeric key {b} in segment names")
    children: dict[str, list[str]] = {}
    for placed, anchor in placements.items():
        children.setdefault(anchor, []).append(placed)
    order: list[str] = []

    def _emit(nm: str) -> None:
        order.append(nm)
        for child in children.get(nm, []):
            _emit(child)

    for nm in base:
        _emit(nm)
    if len(order) != len(names):  # an anchor chain that never reaches a base segment (a cycle)
        raise _DerivationError("placement chain does not resolve to the base order")
    return order


def _source_key() -> str:
    h = hashlib.sha256(f"registry-derivation-v{_DERIVATION_VERSION}".encode())
    for path in sorted(_PKG_DIR.glob("*.py")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _load_cached(key: str, names: set[str]) -> list[dict[str, Any]] | None:
    """Failure-soft: any unreadable, mismatched, or stale cache means 'derive live'."""
    try:
        data = json.loads(_CACHE_PATH.read_text())
        rows: list[dict[str, Any]] = data["rows"]
        if data["key"] != key or {r["name"] for r in rows} != names:
            return None
        return rows
    except OSError, ValueError, KeyError, TypeError:
        return None


def _store_cache(key: str, rows: list[dict[str, Any]]) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_CACHE_PATH.parent, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump({"key": key, "rows": rows}, f)
        os.replace(tmp, _CACHE_PATH)  # atomic publish, per the gencache precedent
    except OSError as exc:
        _log.warning("registry cache not written (%s); every import will re-derive", exc)


def _derive_rows(names: set[str]) -> list[dict[str, Any]]:
    fields = _derive_fields(_PKG_DIR)
    if set(fields) != names:
        raise _DerivationError(f"AST scan and import scan disagree on segments: {sorted(set(fields) ^ names)}")
    for nm, needs in _NEEDS_OVERRIDES.items():
        if nm not in fields:
            raise _DerivationError(f"needs override {nm} names no live segment")
        if not set(needs) <= set(fields[nm].free):
            raise _DerivationError(f"needs override {nm} is not a subset of its free set")
        fields[nm] = fields[nm]._replace(needs=needs)
    out: list[dict[str, Any]] = []
    for nm in _ordered_names(names, _PLACEMENTS):
        f = fields[nm]
        # JSON-shaped (lists, not tuples) so freshly derived rows compare equal to cached ones
        out.append({"name": nm, "free": list(f.free), "writes": list(f.writes), "checks": list(f.checks), "needs": list(f.needs), "meta": f.meta, "always": f.always})
    return out


def _row(d: dict[str, Any], fns: dict[str, Callable[..., dict[str, Any]]]) -> _GateSeg:
    f = _SegFields(tuple(d["free"]), tuple(d["writes"]), tuple(d["checks"]), tuple(d["needs"]), bool(d["meta"]), bool(d["always"]))
    return _GateSeg(fns[d["name"]], *f)


def _assemble(names: set[str]) -> list[dict[str, Any]]:
    key = _source_key()
    rows = _load_cached(key, names)
    if rows is None:
        rows = _derive_rows(names)
        _store_cache(key, rows)
    return rows


_fns = _segment_functions()

GATE_SEGMENTS: tuple[_GateSeg, ...] = tuple(_row(d, _fns) for d in _assemble(set(_fns)))

META_CHECKS: frozenset[str] = frozenset(c for r in GATE_SEGMENTS for c in r.checks if r.meta)


_SEG_DEPS: list[set[int]] = []
for _i, _s in enumerate(GATE_SEGMENTS):
    _f = set(_s.needs)
    _SEG_DEPS.append({_j for _j in range(_i) if _f & set(GATE_SEGMENTS[_j].writes)})
del _i, _s, _f
