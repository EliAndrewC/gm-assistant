"""Serialize GATE_SEGMENTS so before/after can be diffed byte-for-byte (feature 122 oracle).

Run from the skill directory:  python3 <this> <out.json>

Deliberately field-agnostic: it dumps every field of `_GateSeg` by name, resolving the bound
segment function to its `__name__` and nothing else. The point is that this file states no
opinion about what the registry contains - it can only report what it found - so it cannot
agree with a broken registry by sharing its assumptions.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    sys.path.insert(0, ".")
    from l7r.diagram.check_village.registry import GATE_SEGMENTS  # noqa: PLC0415

    rows = []
    for i, seg in enumerate(GATE_SEGMENTS):
        row: dict[str, object] = {"_i": i}
        for field in seg._fields:
            v = getattr(seg, field)
            if callable(v):
                v = getattr(v, "__name__", repr(v))
            elif isinstance(v, tuple | list | set | frozenset):
                v = sorted(v) if isinstance(v, set | frozenset) else list(v)
            row[field] = v
        rows.append(row)
    with open(sys.argv[1], "w") as f:
        json.dump(rows, f, indent=1, sort_keys=True, default=repr)
    print(f"{len(rows)} rows -> {sys.argv[1]}  (fields: {', '.join(GATE_SEGMENTS[0]._fields)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
