"""Shared fixtures for the sitegen tests.

`SQUARE` is deliberately duplicated from `tests/hamletgen/_builders.py` rather than imported from
it: `tests/sitegen/` must not depend on a tier generator's test package (see this package's
docstring). It is four corners of a square - the cost of the duplication is four numbers, and the
cost of the dependency would be the whole point of the shared library.
"""

SQUARE: list[tuple[float, float]] = [(400.0, 400.0), (1000.0, 400.0), (1000.0, 1000.0), (400.0, 1000.0)]
