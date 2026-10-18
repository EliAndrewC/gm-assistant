"""Shrine builder (feature 216): a wizard where a player designs a shrine with no prices shown,
and a ledger that prices it and lets Tadashi haggle per contract - shown to the GM, and read-only
to a player whose grouped character has Commerce (FR-048).

The design lives in the page's query string (the link IS the save). Secrecy is structural: the
catalog data sits outside `static/` and the template receives a ledger only for those viewers.

    catalog.py  - the catalog data model, the one `when` rule grammar, loading and validation
    design.py   - resolving a design (one forward pass), links, the rules JSON for the browser
    pricing.py  - fair prices, porterage, negotiation, number formatting (ledger viewers only)
    access.py   - who besides the GM sees the ledger: Commerce, read from the character-sheet app

Index, rules and the historical grounding of the prices: `CLAUDE.md` next to this file.
"""

from l7r.shrines.catalog import *  # noqa: F403
from l7r.shrines.catalog import __all__ as _catalog_all
from l7r.shrines.design import *  # noqa: F403
from l7r.shrines.design import __all__ as _design_all
from l7r.shrines.pricing import *  # noqa: F403
from l7r.shrines.pricing import __all__ as _pricing_all

__all__ = [*_catalog_all, *_design_all, *_pricing_all]  # noqa: PLE0604
