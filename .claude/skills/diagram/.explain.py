"""Why the reference map is failing, in detail. Run it with `make explain`.

A dotfile so `gencache.engine_files()` prunes it - a hidden .py is never an engine module, and this
one must not become part of any map's cache key.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from l7r.diagram import check_village as cv  # noqa: E402
from l7r.diagram import hamletgen as hg  # noqa: E402

# SEED=n explains a COHORT seed instead of the reference map. Added because the reference hamlet went
# clean while a tripwire seed did not, and there was no route to ask why - the same missing-route
# pattern this feature has now hit five times (durations, test-file, explain, overlap attribution,
# and this).
_seed = int(os.environ.get("SEED", "4"))
if _seed == 4:
    plan = hg.plan_site(hg.HamletSpec(name="Inashiro", seed=4, households=15, down_deg=90, water_sink="pond", windward="N"))
else:
    plan = hg.plan_site(hg.HamletSpec(name=f"Tripwire-{_seed}", seed=_seed, households=10 + (_seed * 7) % 11))
s = hg.build(plan)
with tempfile.TemporaryDirectory() as d:
    s.finish(os.path.join(d, "x"), render=False)

bad = cv.gate(s.M, verbose=False)
print()
print(f"\033[1mseed {_seed}:\033[0m", "CLEAN" if not bad else "FAILING")
if bad:
    print()
    cv.gate(s.M, verbose=True, only=set(bad))
    # ATTRIBUTE AN OVERLAP TO THE LANE THAT CAUSED IT. The matrix reports the pair and a point; it
    # cannot say WHICH lane, and with every lane now drawn after the houses the answer decides
    # whether the culprit is the track or the web - two different stages and two different fixes.
    if "features_do_not_overlap" in bad:
        import math

        for ln in s.M.get("lanes") or []:
            pts = ln["pts"]
            kind = "connector" if ln.get("connector") else ("web" if ln.get("web") else "skeleton/spur")
            for w in [{"x": h["x"], "y": h["y"], "what": "house"} for h in (s.M.get("houses") or [])] + [{"x": q["x"], "y": q["y"], "what": "well"} for q in (s.M.get("wells") or [])]:

                def seg_d(px, py, a, b):
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    L2 = dx * dx + dy * dy or 1.0
                    u = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
                    return math.hypot(px - (a[0] + u * dx), py - (a[1] + u * dy))

                # SEGMENT distance, not vertex distance: a lane passes a well BETWEEN its vertices,
                # and the first version of this attribution measured to vertices and printed nothing
                # while the matrix was reporting a real overlap.
                d2 = min(
                    (seg_d(w["x"], w["y"], pts[k], pts[k + 1]) for k in range(len(pts) - 1)),
                    default=1e9,
                )
                if d2 < 15:
                    print(f"    -> a {kind} lane passes {d2:.1f} px from the {w['what']} at ({w['x']:.0f}, {w['y']:.0f})")
    print()
