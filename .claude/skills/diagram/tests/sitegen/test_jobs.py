"""Unit tests for `sitegen/jobs.py` - the worker-count courtesy every fan-out extends.

Moved here from the hamlet driver tests by feature 119 with its subject: the rule is about
this box's cpu count, not about any one tier.
"""

import os

from l7r.diagram import sitegen as sg


def test_default_jobs_leaves_headroom_and_never_exceeds_the_cohort() -> None:
    """The fan-out courtesy rule (2026-08-16), defined once in the driver and reused by
    cohort_audit.py: never more workers than maps, never every cpu on the box."""
    assert sg.default_jobs(1) == 1
    assert sg.default_jobs(2) <= 2
    assert sg.default_jobs(10_000) == max(1, (os.cpu_count() or 2) - 2)
