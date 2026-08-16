"""T002: freeze the pre-collapse registry rows as the legacy oracle fixture (FR-001)."""

import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "diagram"
sys.path.insert(0, str(SKILL))
from check_village.registry import GATE_SEGMENTS, META_CHECKS

out = {
    "comment": "Feature 109: the pre-collapse hand-maintained registry rows, frozen 2026-08-16. NEVER regenerated - this is the permanent legacy oracle the derived registry is proven against (equality by name; fixture order is a subsequence of derived order).",
    "meta_checks": sorted(META_CHECKS),
    "rows": [
        {"name": r.fn.__name__, "free": list(r.free), "writes": list(r.writes), "checks": list(r.checks), "needs": list(r.needs), "meta": r.meta, "always": r.always}
        for r in GATE_SEGMENTS
    ],
}
dest = SKILL / "test_fixtures" / "registry_legacy_rows.json"
dest.write_text(json.dumps(out, indent=1) + "\n")
print(f"froze {len(out['rows'])} rows -> {dest} ({dest.stat().st_size} bytes)")
