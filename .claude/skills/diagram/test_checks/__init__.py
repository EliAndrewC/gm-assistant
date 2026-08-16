#!/usr/bin/env python3
"""Negative-fixture unit tests for the check_village GATE itself.

`test_villages.py` confirms the real pool maps PASS every check (integration). This file
confirms each check actually FIRES on a deliberately-broken synthetic manifest (unit) - so a
refactor that silently neuters a check (e.g. a `bad = []` left always-empty) is caught, which
`test_villages` cannot: every real map would still pass and the suite would stay green while
the check sat dead. Each fixture is a minimal manifest dict (`gate()` fills the rest from
`DEFAULT_MANIFEST`) that should trip ONE named check; we assert the name IS in the failures,
and where a paired 'good' variant exists, that it is NOT - guarding against a check that fires
on everything. Other checks failing on a sparse fixture is fine; we only assert the target.

Add a fixture here whenever you add or tighten a check. The act of writing "here is a map that
SHOULD fail" forces you to enumerate the ways the thing can be wrong - which is how the gap
that motivated this file (a lane "served" by a building fronting the perpendicular street) gets
caught next time.

    python3 -m pytest test_checks/ -q
    python3 -m pytest test_checks/
"""
