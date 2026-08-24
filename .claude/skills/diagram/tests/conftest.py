"""The test suite itself runs through make, or not at all (feature 127, FR-002).

WHY THE SUITE AND NOT JUST THE GENERATORS. `pytest` is the single most expensive thing in this
project that is not a map: the full suite is ~4.5 minutes, and it was reached for directly over and
over while `make quick` (~33 s) sat unused. The command-shape hook refuses a bare `pytest` before it
runs, and this is the layer beneath it - it catches the invocations the hook's patterns do not
anticipate, and it cannot be walked around by spelling the command differently.

IT IS A NO-OP ON THE LEGITIMATE PATH. Every make target that runs tests satisfies the determination,
and so does every pytest-xdist worker and every subprocess they spawn - ancestry is inherited
(verified in `test_invocation.py`). So this fires only when someone runs pytest by hand outside make,
which is the case it exists for.

THE REFUSAL NAMES THE TARGET, as every refusal in this feature must: a guard that blocks a legitimate
action without offering the route is a guard that gets worked around, which is not a theory - gating
bare pytest before `make durations` and `make test-file` existed left "why is this slow" and "re-run
the file I just changed" with no answer but the override.
"""

from __future__ import annotations

from l7r.diagram._invocation import assert_via_make

# At import of the suite's root conftest - once, before any test runs.
assert_via_make("the test suite", "quick   (~33 s)  or  make done   (~5.5 min, the full gate)")
