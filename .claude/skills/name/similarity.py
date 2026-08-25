#!/usr/bin/env python3
"""Shim: the ONE implementation of the name-similarity rules lives in
``webapp/chargen/similarity.py`` (feature 200, FR-006). The skill's scripts and
the chargen engine share it; this file only re-exports it."""

import os
import sys

_WEBAPP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "webapp")
if _WEBAPP not in sys.path:
    sys.path.insert(0, os.path.abspath(_WEBAPP))

from chargen.similarity import (  # noqa: E402
    KO_RHYME_MIN_TAIL,
    RHYME_MIN_TAIL,
    edit_distance,
    is_too_similar,
    rhymes,
    set_conflict,
)

__all__ = [
    "KO_RHYME_MIN_TAIL",
    "RHYME_MIN_TAIL",
    "edit_distance",
    "is_too_similar",
    "rhymes",
    "set_conflict",
]
