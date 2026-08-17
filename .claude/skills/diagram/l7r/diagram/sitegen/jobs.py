"""How many worker processes a fan-out may take.

Moved verbatim out of `hamletgen/driver.py` by feature 119. It was already the single definition of
the cpus-minus-2 courtesy that `regen.py` and `cohort_audit.py` extend by hand, and it has nothing
to do with any one tier - every tier generator's cohort roll wants the same answer.
"""

from __future__ import annotations

import os


def default_jobs(count: int) -> int:
    """Leave two cpus for the harness and whatever else is on the box (the same courtesy `regen.py`
    and `cohort_audit.py` extend); never spawn more workers than there are maps to roll."""
    return max(1, min(count, (os.cpu_count() or 2) - 2))
