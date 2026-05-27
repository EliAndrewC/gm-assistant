"""L7R Toolkit package.

Importing this package wires the CherryPy tree. Used by `cherryd --import l7r`.
"""

from l7r import app  # noqa: F401 — side effect: mounts CherryPy tree
