"""Shrine builder (feature 216): a wizard where a player designs a shrine with no prices shown,
and a GM ledger that prices it and lets Tadashi haggle per contract.

The design lives in the page's query string (the link IS the save). Secrecy is structural: the
catalog data sits outside `static/` and the template receives a ledger only for a GM session.

    catalog.py  - the catalog data model, the one `when` rule grammar, loading and validation
    design.py   - resolving a design (one forward pass), links, the rules JSON for the browser
    pricing.py  - fair prices, porterage, negotiation, number formatting (GM only)

Index, rules and the historical grounding of the prices: `CLAUDE.md` next to this file.
"""

from l7r.shrines.catalog import *  # noqa: F403
from l7r.shrines.catalog import __all__ as _catalog_all
from l7r.shrines.design import *  # noqa: F403
from l7r.shrines.design import __all__ as _design_all
from l7r.shrines.pricing import *  # noqa: F403
from l7r.shrines.pricing import __all__ as _pricing_all

__all__ = [*_catalog_all, *_design_all, *_pricing_all]  # noqa: PLE0604
