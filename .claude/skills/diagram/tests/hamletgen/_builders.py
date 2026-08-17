"""Shared fixtures for the hamletgen test package: a known square field, and a plan that uses it."""

from l7r.diagram import hamletgen as hg

SQUARE: list[tuple[float, float]] = [(400.0, 400.0), (1000.0, 400.0), (1000.0, 1000.0), (400.0, 1000.0)]


def a_plan(**kw: object) -> hg.SitePlan:
    """A plan with a known square field, for testing the derivations that read one."""
    spec = hg.HamletSpec(name="Test", seed=3, households=15, down_deg=90.0, windward="N", **kw)  # type: ignore[arg-type]
    plan = hg.plan_site(spec)
    plan.envelope = list(SQUARE)
    return plan
