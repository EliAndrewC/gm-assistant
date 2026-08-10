#!/usr/bin/env python3
"""Budget-first city wall sizing (feature 009, specs/009-city-area-budget).

Every settlement mode grows from a first principle: villages from water flow, manors from a
declared square footage. This module gives provincial cities theirs - the SPACE BUDGET. From the
declared population and program it enumerates the full building inventory, costs it at calibrated
DRAWN-footprint gross ground costs (packed rows vs spaced compounds), adds the fixed civic
program, water, reserves, and a circulation fraction, and DERIVES the wall from the total. The
wall is the output of the budget, never a guess to iterate on: `city_wall_matches_budget` in
check_village.py then holds the drawn map to the promise recorded in `meta.budget`.

CALIBRATION (specs/009-city-area-budget/research.md, measured 2026-07 from the shipped pool):
every constant below carries its measured/researched basis inline. The two anchors: shipped
Tango (GM-accepted) back-predicts within ~1%; the pinned pre-feature Nagahara (GM-rejected,
~17% unaccounted open ground) prices as ~21% over-enclosed and fails the check.

Historical grounding (research.md B, China first per project doctrine): a Chinese county seat
ran a sparse street net (~10-20% of ground; ours draw at ~7% - deep blocks + alley warrens) and
NORMALLY enclosed 25-30% deliberately unbuilt ground (siege insurance, rank-sized walls). On a
diagram that roominess reads as emptiness unless drawn, so open ground enters the budget ONLY as
a declared, drawn line (agricultural district, drill ground, gardens) - never as ambient slack.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field

# ---- calibration constants (all px^2 / px at the 3 ft/px city scale) -----------------------

HOUSEHOLD = 5.0  # humans per family - budgets.md convention used across the skill

# Family share by caste for a provincial city - budgets.md "Provincial city" caste table
# (600 families at pop 3,000: servants 120 / laborers 240 / merchants 150 / burakumin 30 /
# samurai 60; ZERO farmers - city farmland is worked from surrounding villages, unless an
# agricultural district deliberately overrides that assumption).
CASTE_FAMILY_FRAC: dict[str, float] = {"servants": 0.20, "laborers": 0.40, "merchants": 0.25, "burakumin": 0.05, "samurai": 0.10}
PACKED_CASTES = ("servants", "laborers", "merchants", "burakumin")  # row-housing castes (party walls)

# 2/3 of samurai families live INSIDE the walls; the rest hold extramural walled estates and
# commute (the estate doctrine). Measured: Tango 33 in-wall samurai houses, Nagahara 41, of the
# caste table's 60 families -> 0.55-0.68; 2/3 is the round middle.
SAMURAI_INWALL_FRAC = 2.0 / 3.0

# GROSS ground cost per dwelling = drawn footprint + its share of eave gaps / roji / margins.
# Measured on Tango (research.md A): packed healthy-quarter gross 448-822 px^2 (858 over all
# res+mixed quarters), samurai-ward gross ~2,915 px^2 (ratio ~3.6x). The pair below solves the
# Tango back-prediction to +0.2% while keeping that measured ratio - budget at DRAWN footprints
# (legibility floors included), never real-world square footage (FR-011).
C_PACKED = 690.0
C_SPACED = 2480.0

# A CAPITAL's packed quarter is NOT a provincial city's packed quarter (021, measured on the
# drawn Shiro Daika after the GM caught 57% of the cohort standing outside the walls). Tango's
# C_PACKED (690) prices lean rows + eaves + roji; the capital pattern embeds merchant estates,
# trade works, private dojos, theater stages, the doss pocket, kido courts and wellhead courts
# INSIDE its commoner quarters, and its legibility floors sit at 3 ft/px - so the as-built
# in-wall machi ground came to 1,367 px^2/family (1,290,514 px^2 of machi-family districts
# holding 944 packed dwellings). Sizing the wall with 690 therefore under-builds the rampart
# by ~40% of interior area, and the shortfall has nowhere to go but unlawful suburbs.
# 1,350 = that measurement rounded ~1% down, acknowledging that a sliver of the measured
# ground (estates, works) is separately priced in the civic/estate lines. If a future capital's
# fabric misses this constant too, RESIZE THE WALL from the measured density - never spill the
# difference outside (the split band-target check now fails loudly on exactly that).
C_PACKED_CAPITAL = 1350.0

# The fixed civic program - a FLOOR, not per-capita (a pop-2,000 seat still carries the full
# mandatory program: governor's yamen, 6 ministries, temples, theater, gate furniture...).
# Itemized at Tango's measured compound footprints (research.md A) so program changes reprice
# honestly; historically civic ground is ~10% of a county seat's enclosure (research.md B).
CIVIC_PROGRAM: tuple[tuple[str, int | None, float], ...] = (
    ("governor's mansion (yamen)", 1, 17_730.0),
    ("six provincial ministries", 6, 7_980.0),
    # The TEMPLE PRECINCTS row used to sit here as ("temple precincts", 2, 16_250.0). Feature 016
    # moved it onto CityProgram knobs, because temple COUNT is not a fixed program floor: a Fox
    # city runs eight small precincts where an ordinary clan runs two great ones (l7r.md "Fox
    # Temples"; research/religion-and-death.md). It is re-inserted at exactly this position by
    # plan_city so line ORDER - and therefore every shipped manifest's bytes - is unchanged.
    ("minor civic (theater, flophouses, funerary, inspection, kura)", None, 17_440.0),
    ("shops, inns, stables", 21, 4_700.0),
    # Bell-and-drum tower (GM 2026-07-24; footprint RE-VERIFIED same day after the GM's eye caught
    # the first draft oversized): a ~36 ft platform (Pingyao's Market Tower, ATTESTED 133.4 m^2
    # plan ~ 38 ft square - these towers dominate by height, not plan) = 12 px + its clear block.
    ("bell-and-drum tower", 1, 250.0),
    # Trade works (GM 2026-07-24, settlements.md "TRADE WORKS"): the trades whose premises outgrow
    # the shop glyph. The brewery is the big one (vat hall + shopfront + kura + well, ~32x20 px
    # drawn + margins); the dye yard, oil press, pawnshop court, and 1-2 bathhouses (the sento
    # count rolls from the population band, s.bathhouses) together add ~1,100-1,350 px^2 drawn -
    # the line carries the 2-bath figure so a 2-roll never starves - and the FARRIER's shoeing
    # forge (GM 2026-07-25) adds ~120 px^2 more (a 28x38 ft shed-plus-apron is 9.3x12.7 px at
    # ftpx=3), so the line is 1,500. Kilns and lumber yards sit OUTSIDE the walls and cost no
    # interior.
    # Martial training (GM 2026-07-25; settlements.md "Historical grounding: martial training in a
    # provincial city"). The state PROVINCIAL MARTIAL HALL is a 130x100 ft walled compound (hall +
    # sensei's house + a 100 ft archery lane) = 43.3x33.3 px at 3 ft/px = 1,442 px^2; the PRIVATE
    # dojos are 76x44 ft lots = 372 px^2 each, and the line carries the 2-roll figure so a rolled
    # second dojo never starves. 1,442 + 2x372 ~ 2,200.
    ("provincial martial hall + 1-2 private dojos", None, 2_200.0),
    ("brewery compound", 1, 800.0),
    ("trade works (dye yard, oil press, pawn court, 1-2 bathhouses, farrier)", None, 1_500.0),
)

#: the civic row the temple line is re-inserted directly AFTER (see CIVIC_PROGRAM's comment).
#: Held as a constant, and pinned by test_the_temple_line_keeps_its_place_in_the_civic_sequence,
#: because a silent move would rewrite every shipped manifest's bytes without changing a number.
MINISTRIES_LABEL = "six provincial ministries"

#: Default temple program - the two great complexes the CIVIC_PROGRAM row used to hard-code.
#: Tango-measured; see settlements/cities/sizing.md and research/religion-and-death.md.
#: NOTE the CIVIC_PROGRAM convention: every row's third field is the row TOTAL, not a per-unit
#: cost (the six ministries are 7,980 px^2 for all six). The retired temple row read
#: ("temple precincts", 2, 16_250.0) - 16,250 for BOTH precincts - so the per-precinct figure is
#: half of it, ~8,125 px^2 (~73,000 sq ft, ~1.7 acres at 3 ft/px). Getting this backwards doubles
#: every city's temple ground; the pinned shipped-program test is what catches it.
TEMPLE_PRECINCTS = 2
TEMPLE_PRECINCT_PX2 = 8_125.0

#: Adept-monk households per precinct. The default 2.5 x 2 precincts = the 5 households the old
#: hard-coded line carried. A FOX precinct runs much higher (research/religion-and-death.md
#: finding 3): only its three Bonds are celibate and the rest of its clergy are hereditary
#: householders living out among the laity, so its families are drawn as ordinary houses around
#: the compound rather than implied inside it.
MONK_HOUSES_PER_PRECINCT = 2.5

# One in-wall water feature: a pond (landlocked) or the cargo canal + dock basin (river city).
# Measured: Tango pond 2,865 px^2; Nagahara canal-in-wall + dock 2,834 px^2 - same budget line.
WATER_AREA = 2_900.0

# Circulation (trunk road + ring road + streets + alleys) as a fraction of the interior, at
# DRAWN widths: measured 6.8% (Tango) / 7.0% (Nagahara). The historical band is 10-20% of
# ground (research.md B - itself triangulated, not measured), and our sparse end is consistent
# with the deep-block, alley-warren doctrine - so the MAP-calibrated figure wins.
CIRC_FRAC = 0.07
#: The CAPITAL's circulation + trunk-fabric overhead (021, measured from the drawn first
#: capital): a capital carries a street MESH, band lanes, block alleys, the ote-suji /
#: kagi / karamete system and forty-odd compound keep-out halos - measured at ~20% of the
#: interior against the provincial 7%. Recorded with the suburb share below; the two
#: corrections nearly cancel, which is why Shiro Daika's as-built rampart lands within the
#: wall check's tolerance of the corrected minimum.
CIRC_FRAC_CAPITAL = 0.20

# A Tango-style in-wall agricultural district, as a fraction of the interior. Measured: Tango's
# declared agri reserve is 103,577 px^2 of a 689k interior = 15.0%; also comfortably inside the
# feature-006 reserve cap (20%) and the historical 25-30% open-reserve norm (research.md B).
AGRI_FRAC = 0.15

# Canonical provincial-city population band (budgets.md). The CAPITAL tier has its own band and
# its own entry point (`plan_capital`) rather than widening this one - see the capital block below.
POP_MIN, POP_MAX = 2000, 4000

# ---- the DOMAIN-CAPITAL tier (feature 018, specs/018-capital-space-budget) ------------------
#
# A capital gets a PARALLEL entry point rather than a widened band, so the provincial path below
# executes zero new branches and its byte-identity is structural rather than merely tested. The
# tiers also differ in inventory STRUCTURE - three samurai housing types against one, a castle
# line, no agricultural district - so a shared function would be mostly branching anyway.
# Every number here is settled and recorded in settlements/capitals.md + research/cities/capitals.md.

#: Canonical capital population: the settled 12,000 of budgets.md's Capital city table plus the
#: ~360 relocated non-working samurai (the schooling-and-retirement cohort). The ~45 foreign
#: Imperial samurai are NOT in this figure - they are housed inside the Imperial Magistrate's
#: compound, which is a civic line rather than a housing line.
CAPITAL_POP = 12_360
CAPITAL_POP_MIN, CAPITAL_POP_MAX = 9_000, 16_000

#: Households by caste - ABSOLUTE counts from budgets.md's Capital city table, not fractions of
#: population, because the capital carries a cohort (the +72 relocated samurai families) that sits
#: outside the settled 12,000 breakdown. Sums to 2,472 = CAPITAL_POP / HOUSEHOLD exactly.
CAPITAL_FAMILIES: dict[str, int] = {"servants": 480, "laborers": 960, "merchants": 600, "burakumin": 120, "samurai": 312}

#: The samurai rank bands, stored as the RAW per-rank counts from budgets.md's "Samurai rank
#: distribution" capital column (800 working) so the split stays traceable to a published table
#: rather than being three magic percentages. Upper = Ranks 8-12, middle = 5-7, junior = 1-4.
#: The resulting 20 / 50 / 30 is the INVERSE of a provincial city's mix (27% senior / 73% junior):
#: a capital posting is prestigious even when the job is menial, and the capital absorbs the
#: rank-by-association cohort. So walled compounds are the MAJORITY texture here, not a minority.
CAPITAL_RANK_BANDS: dict[str, tuple[int, ...]] = {
    "yashiki": (1, 8, 7, 25, 119),  # R12, R11, R10, R9, R8 -> walled compounds
    "detached": (127, 134, 142),  # R7, R6, R5 -> detached houses
    "terrace": (103, 72, 47, 15),  # R4, R3, R2, R1 -> retainer terraces
}

#: Share of samurai families living INSIDE the wall. Higher than the provincial 2/3 because
#: proximity to the daimyo's court is the point of a capital posting, and the walled yashiki
#: removes the cramped-lot push that sends a provincial city's wealthiest samurai to country
#: estates. GM-approved 2026-08-08, and an ESTIMATE - a first candidate for re-derivation against
#: the first drawn capital.
CAPITAL_SAMURAI_INWALL_FRAC = 0.85

# GROSS ground cost for the two dwelling types the provincial model has never seen. Both are
# PROVISIONAL by design and must be re-derived against the first drawn capital, exactly as
# C_PACKED / C_SPACED were back-predicted from Tango.
#
# C_YASHIKI - a walled samurai compound inside the wall. Anchor: the Fukui archive's Suginuma
# plan (a 1,000-koku retainer, 1839), a 28 x 32.5 ken plot = ~167 x 194 ft = 3,600 px^2 at
# 3 ft/px, plus ~1.15x for street margin. A walled PLOT already contains its own yard - the wall
# IS the boundary - so it carries far less shared-margin overhead than a detached house in an
# open lot, which is why the gross-up is 1.15x and not the 7.5x C_SPACED takes. Sanity: 1.7x an
# ordinary in-wall samurai house, 1.3x a drawn merchant-estate court, under the ~1-acre country
# manor.
C_YASHIKI = 4_150.0
# C_TERRACE - a retainer terrace unit for a junior (Rank 1-4) samurai household. Bracketed by
# Shibata's ICP ashigaru-nagaya (8 households, 143 x 21 ft, 18 ft frontage each = 378 sq ft) below
# and the detached samurai house (2,322 sq ft drawn) above. THE SOFTEST NUMBER IN THIS MODULE:
# both ends are measured, but its position between them is a judgment. NOT "ashigaru" housing -
# in Rokugan ashigaru are PEASANTS living in villages (budgets.md), so that institution does not
# exist at this tier; this houses the junior samurai the historical kumi-yashiki would have held.
# It sits just BELOW C_PACKED, which looks wrong and is not: C_PACKED is the caste-WEIGHTED
# average of the packed castes and is pulled up by merchant houses (~200 px^2 footprint against a
# laborer's ~99), so a bare laborer row house is only ~550 gross. A retainer terrace is roomier
# than a laborer's row and tighter than the merchant-inflated average - and already generous
# against the anchor, which gave each nagaya household 378 sq ft to our laborer row's 891.
C_TERRACE = 660.0

#: px^2 per hectare at the 3 ft/px calibration scale (1 ha = 107,639 sq ft / 9 sq ft per px^2).
HECTARE_PX2 = 11_959.9
#: The castle's declared ground. Default ~50 ha - the HIROSAKI anchor (a 47,000-koku daimyo's
#: whole enceinte, every bailey plus all three moats), which is the MODEST end on purpose. The
#: band runs to Himeji's 233 ha. NOTE this is the enceinte, not the keep: Hirosaki's tenshu is
#: ~0.6 ha, 1.2% of the works, so a model that priced "the keep" would undersize this by two
#: orders of magnitude. It is DECLARED rather than derived because its governing variable is the
#: daimyo's rank, not the town's population.
CASTLE_PX2 = 598_000.0
CASTLE_HA_MIN, CASTLE_HA_MAX = 50.0, 230.0

#: A SOVEREIGN temple - the head house of a domain-wide Order, with a Grand Abbot and 50+ monks
#: (l7r.md) - against a provincial precinct's 8,125 px^2.
SOVEREIGN_PRECINCT_PX2 = 16_250.0

#: The two variant knobs. Neither has a privileged default; the dataclass needs one, that is all.
CASTLE_SEATS = ("ring", "edge")
IMPERIAL_GRANARY_SEATS = ("magistrate", "wharf")

#: The capital's fixed civic program. SAME ROW-TOTAL CONVENTION as CIVIC_PROGRAM: every third
#: field is the ROW TOTAL, not a per-unit cost. Reading it as per-unit is how feature 016 nearly
#: doubled every city's temple ground, which is why this table has its own pinned test.
#: The castle and the sovereign temples are deliberately NOT here - both are knob-driven declared
#: lines, so they reprice when declared rather than being frozen into a program floor.
CAPITAL_CIVIC_PROGRAM: tuple[tuple[str, int | None, float], ...] = (
    # The six DOMAIN ministries sit OUTSIDE the castle, flanking the ote-suji approach avenue -
    # both traditions converge on this at exactly this tier (Beijing's Six Ministries lined the
    # Corridor of a Thousand Steps outside Chengtianmen; a jokamachi's offices spilled out of the
    # ninomaru as they grew). So they are priced against CITY ground, not castle ground. Roughly
    # 2x the provincial six, whose ministers are three ranks junior.
    ("six domain ministries + government ward", 6, 16_000.0),
    ("House Chancellery (the domain's 5-10 lineage representatives)", 1, 2_000.0),
    # Foreign sovereign ground, and it houses its own ~12 households - which is why those families
    # are absent from CAPITAL_FAMILIES. budgets.md funds its "manor maintenance, grounds, stable,
    # fortified walls, ceremonial halls" at 700 koku/yr.
    ("Imperial Magistrate's compound (foreign; houses its own 12 households)", 1, 8_000.0),
    # Separate from the domain's stores and OUTSIDE the castle, because they face a different
    # threat: an invading neighbor would not attack the Emperor's granaries, so they need
    # protection from brigands rather than besiegers and a stout wall suffices (GM 2026-08-08).
    ("the Emperor's granaries", 1, 3_000.0),
    ("domain school (hanko)", 1, 4_000.0),
    # The capital is the COLLECTING-and-disbursing end of the rice trade, not the selling end -
    # rice comes up from the six provinces, most goes straight back out as stipends (kuramai), and
    # the surplus ships downriver. Modeled on Asakusa Okura / Kuramae, with a MERCHANT brokers' row
    # in front of the granary (GM 2026-08-08: budgets.md's ministry arbitrage line covers the
    # PAYING of stipends only; the contracts and lending made merchants rich, as the fudasashi).
    ("domain granary + wharf brokers' row", None, 12_000.0),
    # One state hall plus the SAME 1-per-200-samurai private roll a provincial city uses (~7-8 at
    # ~1,560 resident samurai). The capital's distinctive institution is the domain school above,
    # not a richer private tail - the machi-dojo boom was a million-person-city event.
    ("domain martial hall + rolled private dojos", None, 4_400.0),
    # The josui conduit is BURIED inside the wall (the open cut and the kakehi crossing are both
    # extramural), so it consumes almost no interior ground - this line is its works, not its
    # length. Pricing a surface channel across the interior would have inflated the wall.
    ("aqueduct in-wall works (the conduit itself is buried)", None, 500.0),
    ("minor civic (theaters, flophouses, funerary, inspection, kura)", None, 30_000.0),
    ("shops, inns, stables", 60, 13_400.0),
    # It now has a documented job: it sounds the curfew the machi kido enforce.
    ("bell-and-drum tower (sounds the kido curfew)", 1, 250.0),
    ("brewery compounds", 2, 1_600.0),
    ("trade works (dye yards, oil presses, pawn courts, bathhouses, farriers)", None, 3_000.0),
)

#: One in-wall water feature, at capital scale - twice the provincial figure.
CAPITAL_WATER_AREA = 5_800.0

# Clearance the wall needs to the canvas edge: moat gap (24) + moat (~22) + gate furniture,
# towers, labels and the crop margin - measured from both shipped gens' view margins.
WALL_MARGIN_PX = 150.0

CAL_FTPX = 3  # the scale every constant above is calibrated at (the city rung of the ladder)


@dataclass(frozen=True)
class BudgetLine:
    """One auditable row: what, how many, how much ground, and WHY that number."""

    label: str
    count: int | None
    area_px2: float
    basis: str


@dataclass(frozen=True)
class CityProgram:
    """The declaration made BEFORE anything is drawn - population plus the feature program."""

    population: int
    ftpx: int = CAL_FTPX
    river: bool = False
    agricultural_district: bool = False
    aspect: float = 0.93  # RY/RX; both shipped cities are near-round (Tango 0.938, Nagahara 0.931)
    nring: int = 20  # wall vertices; the shipped gens draw 20-22-gon rings
    extras: tuple[BudgetLine, ...] = field(default_factory=tuple)
    # The TEMPLE PROGRAM (feature 016). Defaults reproduce the old hard-coded civic row exactly.
    # A city declaring more than 2 precincts also owes meta(temple_exception=...) at the gate.
    temple_precincts: int = TEMPLE_PRECINCTS
    temple_precinct_px2: float = TEMPLE_PRECINCT_PX2
    monk_houses_per_precinct: float = MONK_HOUSES_PER_PRECINCT


@dataclass(frozen=True)
class CapitalProgram:
    """A domain capital's declaration, made BEFORE anything is drawn (feature 018).

    Parallel to CityProgram rather than derived from it: a capital is not a kind of provincial
    city, and keeping the two apart is what guarantees the provincial path runs no new branches.

    Every illegal combination raises HERE, in __post_init__, so a caller can never hold a program
    that plan_capital would reject - and every raise names the offending value AND the legal
    alternatives.
    """

    population: int = CAPITAL_POP
    ftpx: int = CAL_FTPX
    river: bool = False
    #: ALWAYS False. Present only so the shared budget_to_manifest needs no tier branch - a
    #: capital walls its farms out (GM 2026-08-08). Validated rather than merely defaulted, so a
    #: caller cannot set it and get a silently mis-priced wall.
    agricultural_district: bool = False
    aspect: float = 0.93
    nring: int = 20
    castle_seat: str = "ring"
    castle_px2: float = CASTLE_PX2
    imperial_granary_seat: str = "magistrate"
    temple_precincts: int = 2
    temple_precinct_px2: float = SOVEREIGN_PRECINCT_PX2
    monk_houses_per_precinct: float = 2.5
    #: The share of the PACKED cohort housed OUTSIDE the rampart (021 research): the kashi
    #: wharf belt and the guan-xiang gate wards. China-first: Suzhou's Changmen suburb
    #: out-traded the walled interior; the jokamachi machi-chi sprawled outside the moat
    #: lines. The wall is sized to the CEREMONIAL city; the commercial spill is the suburbs'.
    suburb_packed_frac: float = 0.30
    extras: tuple[BudgetLine, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.suburb_packed_frac <= 0.5:
            raise ValueError(
                f"suburb_packed_frac {self.suburb_packed_frac} outside [0, 0.5] - the research band: a capital houses SOME packed cohort outside (guan-xiang / kashi belt), but the majority stays in-wall"
            )
        if not CAPITAL_POP_MIN <= self.population <= CAPITAL_POP_MAX:
            raise ValueError(f"population {self.population} outside the domain-capital band [{CAPITAL_POP_MIN}, {CAPITAL_POP_MAX}] (budgets.md capital tier; a provincial city uses plan_city)")
        if self.castle_seat not in CASTLE_SEATS:
            raise ValueError(f"castle_seat {self.castle_seat!r} is not one of {CASTLE_SEATS}")
        # Every attested edge castle is a river or sea castle - Okayama diverted a branch of the
        # Asahi to moat its NE flank, Kitsuki sits on a promontory between two river mouths. On a
        # dry edge the castle's own works are not a stretch of the city's defense, so it is not a
        # variant but a weak wall.
        if self.castle_seat == "edge" and not self.river:
            raise ValueError("castle_seat='edge' requires river=True - an edge castle's own outer moat FORMS that stretch of the city's defense, so a dry edge is a weak wall rather than a variant")
        if self.imperial_granary_seat not in IMPERIAL_GRANARY_SEATS:
            raise ValueError(
                f"imperial_granary_seat {self.imperial_granary_seat!r} is not one of {IMPERIAL_GRANARY_SEATS} (neither is privileged - Hirosaki-style beside the overseeing magistrate, or on the water where grain moves)"
            )
        ha = self.castle_px2 / HECTARE_PX2
        if not CASTLE_HA_MIN <= ha <= CASTLE_HA_MAX:
            raise ValueError(
                f"castle_px2 {self.castle_px2:.0f} is {ha:.1f} ha, outside the documented band [{CASTLE_HA_MIN}, {CASTLE_HA_MAX}] ha (Hirosaki ~50 ha to Himeji ~233 ha) - a castle this far off is a program error, not a wall"
            )
        if self.agricultural_district:
            raise ValueError(
                "a domain capital has no agricultural district - the wall encloses all its inhabitants and no farmland (GM 2026-08-08); the field exists only so the shared serializer needs no tier branch"
            )
        if not 0.0 < self.aspect <= 1.0:
            raise ValueError(f"aspect must be in (0, 1] (RY/RX of a near-round ring), got {self.aspect}")


@dataclass(frozen=True)
class WallSpec:
    """The derived wall: a closed ellipse N-gon (research.md Decision 4: both shipped cities are
    full rings - even river-bank Nagahara; the river never enters the walls)."""

    shape: str
    rx: float
    ry: float
    nring: int
    interior_px2: float
    perimeter_px: float


@dataclass(frozen=True)
class CityBudget:
    #: Either tier's program. budget_to_manifest and format_budget touch only the fields BOTH
    #: types carry (population, ftpx, river, agricultural_district), so neither needs a tier
    #: branch - which is the whole reason CapitalProgram carries agricultural_district at all.
    program: CityProgram | CapitalProgram
    lines: tuple[BudgetLine, ...]
    required_interior_px2: float
    wall: WallSpec
    dwelling_target: dict[str, object]


def derive_wall(required_px2: float, *, aspect: float, nring: int = 20) -> WallSpec:
    """Solve the wall semi-axes so the DRAWN N-gon encloses `required_px2`.

    The gen scripts draw the wall as an ellipse N-gon whose polygon area is 0.5*N*sin(2pi/N)*rx*ry
    - slightly under the smooth ellipse's pi*rx*ry. Target the N-gon area, or every wall comes
    out systematically small (data-model.md)."""
    if not 0.0 < aspect <= 1.0:
        raise ValueError(f"aspect must be in (0, 1] (RY/RX of a near-round ring), got {aspect}")
    factor = 0.5 * nring * math.sin(2 * math.pi / nring)
    rx = math.sqrt(required_px2 / (factor * aspect))
    ry = aspect * rx
    pts = [(rx * math.cos(2 * math.pi * i / nring), ry * math.sin(2 * math.pi * i / nring)) for i in range(nring)]
    perimeter = sum(math.dist(pts[i], pts[(i + 1) % nring]) for i in range(nring))
    return WallSpec(shape="ring", rx=rx, ry=ry, nring=nring, interior_px2=factor * rx * ry, perimeter_px=perimeter)


def plan_city(program: CityProgram, canvas: tuple[float, float] | None = None) -> CityBudget:
    """Compute the full space budget and derive the wall - BEFORE anything is placed.

    Deterministic and pure. Raises ValueError (with the numbers) when the population is outside
    the provincial band or the derived wall cannot fit the canvas - never silently clamps."""
    pop = program.population
    if not POP_MIN <= pop <= POP_MAX:
        raise ValueError(f"population {pop} outside the canonical provincial-city band [{POP_MIN}, {POP_MAX}] (budgets.md; capitals are a future tier)")
    k = (CAL_FTPX / program.ftpx) ** 2  # constants are calibrated at 3 ft/px; drawn px^2 scale by (3/ftpx)^2

    families = {caste: round(pop / HOUSEHOLD * frac) for caste, frac in CASTE_FAMILY_FRAC.items()}
    packed_n = sum(families[c] for c in PACKED_CASTES)
    samurai_inwall = round(families["samurai"] * SAMURAI_INWALL_FRAC)

    lines: list[BudgetLine] = [
        BudgetLine(
            "packed row housing (laborer/servant/merchant/burakumin)",
            packed_n,
            packed_n * C_PACKED * k,
            f"{packed_n} families x C_PACKED {C_PACKED:.0f} px^2 gross (Tango-measured rows + eaves + roji)",
        ),
        BudgetLine(
            "samurai houses in-wall",
            samurai_inwall,
            samurai_inwall * C_SPACED * k,
            f"2/3 of {families['samurai']} samurai families x C_SPACED {C_SPACED:.0f} px^2 gross (Tango samurai-ward; rest hold extramural estates)",
        ),
    ]
    # The TEMPLE line is knob-driven (feature 016) but keeps the position the hard-coded civic row
    # held, directly after the ministries - line order is manifest bytes, so a move would dirty
    # every shipped city for no arithmetic reason.
    n_temples = program.temple_precincts
    temple_line = BudgetLine(
        "temple precincts",
        n_temples,
        n_temples * program.temple_precinct_px2 * k,
        f"{n_temples} precinct(s) x {program.temple_precinct_px2:.0f} px^2 (Tango-measured complex; a Fox city declares more, smaller ones - research/religion-and-death.md)",
    )
    for label, count, area in CIVIC_PROGRAM:
        lines.append(BudgetLine(label, count, area * k, "fixed civic program floor at Tango-measured compound footprints (research.md A)"))
        if label == MINISTRIES_LABEL:
            lines.append(temple_line)
    # Adept-monk housing (GM 2026-07-24): each temple precinct keeps ordinary homes in its
    # neighborhood for the married adepts among its monks (temple-density canon, settlements.md
    # "City temples"). Clergy are not a lay caste, so these households ride OUTSIDE the caste
    # table's 600 families - a small civic-adjacent line at packed gross cost. The count scales
    # with the precinct count because a city's clergy housing is a property of its temples, not a
    # constant: a Fox city's hereditary householder clergy need far more of it (feature 016).
    n_monk_houses = round(n_temples * program.monk_houses_per_precinct)
    lines.append(
        BudgetLine(
            "adept-monk houses by the temple precincts",
            n_monk_houses,
            n_monk_houses * C_PACKED * k,
            f"{n_temples} temple precinct(s) x {program.monk_houses_per_precinct:g} adept-monk households at C_PACKED gross (clergy live outside the lay caste table)",
        )
    )
    water_label = "cargo canal + dock basin" if program.river else "pond"
    lines.append(BudgetLine(water_label, 1, WATER_AREA * k, "one in-wall water feature - Tango pond 2,865 / Nagahara canal+dock 2,834 px^2 measured"))
    lines.extend(program.extras)

    fixed = sum(ln.area_px2 for ln in lines)
    denom = 1.0 - CIRC_FRAC - (AGRI_FRAC if program.agricultural_district else 0.0)
    required = fixed / denom
    lines.append(
        BudgetLine(
            "circulation (trunk + ring road + streets + alleys)",
            None,
            required * CIRC_FRAC,
            f"{CIRC_FRAC:.0%} of interior at drawn widths (measured 6.8-7.0%; historical envelope 10-20%, research.md B)",
        )
    )
    if program.agricultural_district:
        lines.append(
            BudgetLine(
                "agricultural district (in-wall farms, declared reserve)", None, required * AGRI_FRAC, f"{AGRI_FRAC:.0%} of interior (Tango's declared agri reserve; inside the 20% reserve cap)"
            )
        )

    wall = derive_wall(required, aspect=program.aspect, nring=program.nring)
    if canvas is not None:
        need_w, need_h = 2 * (wall.rx + WALL_MARGIN_PX), 2 * (wall.ry + WALL_MARGIN_PX)
        if need_w > canvas[0] or need_h > canvas[1]:
            raise ValueError(
                f"derived wall {wall.rx:.0f}x{wall.ry:.0f} needs {need_w:.0f}x{need_h:.0f} px incl. the {WALL_MARGIN_PX:.0f} px moat/margin clearance but the canvas is {canvas[0]:.0f}x{canvas[1]:.0f} - enlarge the canvas or trim the program; never clamp the wall"
            )

    target: dict[str, object] = {"families": families, "packed": packed_n, "samurai_inwall": samurai_inwall}
    return CityBudget(program=program, lines=tuple(lines), required_interior_px2=required, wall=wall, dwelling_target=target)


def plan_capital(program: CapitalProgram, canvas: tuple[float, float] | None = None) -> CityBudget:
    """Compute a DOMAIN CAPITAL's space budget and derive its wall - BEFORE anything is placed.

    Deterministic and pure, and the sibling of plan_city rather than a mode of it. A capital's
    wall cannot be predicted from population the way a provincial city's nearly can: a median
    castle alone is ~85% of an entire provincial city's interior, so the castle is a DECLARED
    line and the samurai cohort is priced by RANK BAND rather than as one undifferentiated group.
    """
    pop = program.population
    k = (CAL_FTPX / program.ftpx) ** 2  # constants are calibrated at 3 ft/px

    packed_n = sum(CAPITAL_FAMILIES[c] for c in PACKED_CASTES)
    samurai_inwall = round(CAPITAL_FAMILIES["samurai"] * CAPITAL_SAMURAI_INWALL_FRAC)
    # Split the in-wall cohort by rank band. Shares are DERIVED from the raw rank-table counts, so
    # the split is traceable to budgets.md rather than being three magic percentages; the last
    # band takes the remainder so the three always sum to samurai_inwall exactly.
    working = sum(sum(v) for v in CAPITAL_RANK_BANDS.values())
    n_yashiki = round(samurai_inwall * sum(CAPITAL_RANK_BANDS["yashiki"]) / working)
    n_detached = round(samurai_inwall * sum(CAPITAL_RANK_BANDS["detached"]) / working)
    n_terrace = samurai_inwall - n_yashiki - n_detached

    lines: list[BudgetLine] = [
        BudgetLine(
            "packed row housing IN-WALL (laborer/servant/merchant/burakumin)",
            round(packed_n * (1 - program.suburb_packed_frac)),
            packed_n * (1 - program.suburb_packed_frac) * C_PACKED_CAPITAL * k,
            f"~{1 - program.suburb_packed_frac:.0%} of {packed_n} families x C_PACKED_CAPITAL {C_PACKED_CAPITAL:.0f} px^2 gross (Shiro-Daika-measured: the capital machi embeds estates/works/dojos in its quarters)",
        ),
        BudgetLine(
            "packed row housing SUBURBAN (kashi wharf belt + guan-xiang gate wards)",
            round(packed_n * program.suburb_packed_frac),
            0.0,
            "ground OUTSIDE the rampart - excluded from the interior the wall must hold (021 research: Changmen / machi-chi; the drawn suburbs carry these families)",
        ),
        BudgetLine(
            "the castle (enceinte: baileys + moats; interior implied)",
            1,
            program.castle_px2 * k,
            f"declared {program.castle_px2 / HECTARE_PX2:.0f} ha, seat={program.castle_seat} - Hirosaki ~50 ha to Himeji ~233 ha; the ENCEINTE, not the keep (a tenshu is ~1.2% of the works)",
        ),
        BudgetLine(
            "samurai walled yashiki in-wall (Ranks 8-12)",
            n_yashiki,
            n_yashiki * C_YASHIKI * k,
            f"upper rank band x C_YASHIKI {C_YASHIKI:.0f} px^2 gross (Fukui Suginuma plan, a 1,000-koku plot + street margin)",
        ),
        BudgetLine(
            "samurai detached houses in-wall (Ranks 5-7)",
            n_detached,
            n_detached * C_SPACED * k,
            f"middle rank band x C_SPACED {C_SPACED:.0f} px^2 gross (Tango samurai-ward measurement)",
        ),
        BudgetLine(
            "retainer terraces in-wall (Ranks 1-4)",
            n_terrace,
            n_terrace * C_TERRACE * k,
            f"junior rank band x C_TERRACE {C_TERRACE:.0f} px^2 gross (Shibata ashigaru-nagaya floor, detached house ceiling) - NOT ashigaru, who are peasants in Rokugan",
        ),
    ]
    for label, count, area in CAPITAL_CIVIC_PROGRAM:
        lines.append(BudgetLine(label, count, area * k, "capital civic program floor - a seat carries its full mandatory program regardless of population"))
    n_temples = program.temple_precincts
    lines.append(
        BudgetLine(
            "sovereign temple precincts",
            n_temples,
            n_temples * program.temple_precinct_px2 * k,
            f"{n_temples} sovereign precinct(s) x {program.temple_precinct_px2:.0f} px^2 - the head house of a domain-wide Order, with a Grand Abbot and 50+ monks (l7r.md)",
        )
    )
    n_monk_houses = round(n_temples * program.monk_houses_per_precinct)
    lines.append(
        BudgetLine(
            "adept-monk houses by the temple precincts",
            n_monk_houses,
            n_monk_houses * C_PACKED * k,
            f"{n_temples} precinct(s) x {program.monk_houses_per_precinct:g} adept-monk households at C_PACKED gross (clergy live outside the lay caste table)",
        )
    )
    water_label = "cargo canal + dock basin" if program.river else "pond"
    lines.append(BudgetLine(water_label, 1, CAPITAL_WATER_AREA * k, "one in-wall water feature at capital scale (twice the provincial figure)"))
    lines.extend(program.extras)

    fixed = sum(ln.area_px2 for ln in lines)
    required = fixed / (1.0 - CIRC_FRAC_CAPITAL)
    lines.append(
        BudgetLine(
            "circulation (trunk + ring road + streets + alleys)",
            None,
            required * CIRC_FRAC_CAPITAL,
            f"{CIRC_FRAC_CAPITAL:.0%} of interior at drawn widths - MEASURED from the drawn first capital (street mesh, band lanes, alleys, compound halos), against the provincial 7%",
        )
    )

    wall = derive_wall(required, aspect=program.aspect, nring=program.nring)
    if canvas is not None:
        need_w, need_h = 2 * (wall.rx + WALL_MARGIN_PX), 2 * (wall.ry + WALL_MARGIN_PX)
        if need_w > canvas[0] or need_h > canvas[1]:
            raise ValueError(
                f"derived wall {wall.rx:.0f}x{wall.ry:.0f} needs {need_w:.0f}x{need_h:.0f} px incl. the {WALL_MARGIN_PX:.0f} px moat/margin clearance but the canvas is {canvas[0]:.0f}x{canvas[1]:.0f} - enlarge the canvas or trim the program; never clamp the wall"
            )

    families = dict(CAPITAL_FAMILIES)
    target: dict[str, object] = {
        "families": families,
        "packed": packed_n,
        "samurai_inwall": samurai_inwall,
        "samurai_yashiki": n_yashiki,
        "samurai_detached": n_detached,
        "samurai_terrace": n_terrace,
        "dwellings": round(pop / HOUSEHOLD),
        "packed_suburb": round(packed_n * program.suburb_packed_frac),
    }
    return CityBudget(program=program, lines=tuple(lines), required_interior_px2=required, wall=wall, dwelling_target=target)


def budget_to_manifest(budget: CityBudget) -> dict[str, object]:
    """JSON-serializable dict for `s.meta(budget=...)` - the promise the checks hold the map to."""
    return {
        "required_interior_px2": budget.required_interior_px2,
        "interior_px2": budget.wall.interior_px2,
        "lines": [{"label": ln.label, "count": ln.count, "area_px2": ln.area_px2, "basis": ln.basis} for ln in budget.lines],
        "circulation_frac": CIRC_FRAC,
        "flags": {"river": budget.program.river, "agricultural_district": budget.program.agricultural_district},
        "wall": {"shape": budget.wall.shape, "rx": budget.wall.rx, "ry": budget.wall.ry, "nring": budget.wall.nring},
        "dwelling_target": budget.dwelling_target,
    }


def format_budget(budget: CityBudget) -> str:
    """The itemized, auditable report (returns the string; only the CLI prints)."""
    ftpx = budget.program.ftpx
    sqft = ftpx * ftpx
    out = [
        f"SPACE BUDGET - population {budget.program.population}, {ftpx} ft/px"
        + (", river city" if budget.program.river else "")
        + (", agricultural district" if budget.program.agricultural_district else "")
    ]
    out.append(f"{'line':66} {'count':>5} {'px^2':>9} {'acres':>6}  basis")
    for ln in budget.lines:
        acres = ln.area_px2 * sqft / 43_560
        out.append(f"{ln.label:66} {ln.count if ln.count is not None else '-':>5} {ln.area_px2:>9.0f} {acres:>6.2f}  {ln.basis}")
    w = budget.wall
    out.append(f"required interior: {budget.required_interior_px2:.0f} px^2 ({budget.required_interior_px2 * sqft / 43_560:.1f} acres)")
    out.append(
        f"derived wall: {w.nring}-gon ring rx={w.rx:.0f} ry={w.ry:.0f} px ({w.rx * ftpx:.0f} x {w.ry * ftpx:.0f} ft semi-axes), perimeter {w.perimeter_px * ftpx:.0f} ft ({w.perimeter_px * ftpx / 5280:.2f} mi), encloses {w.interior_px2:.0f} px^2"
    )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    """CLI: `python3 citybudget.py --plan --population 3000 [--river] [--agri] [--canvas WxH]`."""
    ap = argparse.ArgumentParser(description="Budget-first city wall sizing (features 009, 018)")
    ap.add_argument("--plan", action="store_true", help="print the itemized budget + derived wall")
    ap.add_argument("--population", type=int, required=True)
    ap.add_argument("--tier", choices=("provincial", "capital"), default="provincial", help="settlement tier (default: provincial, so every existing invocation is unchanged)")
    ap.add_argument("--river", action="store_true")
    ap.add_argument("--agri", action="store_true", help="in-wall agricultural district (Tango-style; provincial tier only)")
    ap.add_argument("--castle-seat", choices=CASTLE_SEATS, default="ring", help="capital only: where the castle sits ('edge' requires --river)")
    ap.add_argument("--granary-seat", choices=IMPERIAL_GRANARY_SEATS, default="magistrate", help="capital only: where the Emperor's granaries sit")
    ap.add_argument("--aspect", type=float, default=0.93)
    ap.add_argument("--nring", type=int, default=20)
    ap.add_argument("--canvas", type=str, default=None, help="WxH px, e.g. 3200x2700")
    args = ap.parse_args(argv)
    canvas = None
    if args.canvas:
        cw, ch = args.canvas.lower().split("x")
        canvas = (float(cw), float(ch))
    try:
        if args.tier == "capital":
            # Refuse rather than silently ignore: dropping a flag the GM typed is how a wrong wall
            # gets trusted.
            if args.agri:
                raise ValueError("--agri is not available at capital tier - a domain capital walls its farms out, enclosing all its inhabitants and no farmland (GM 2026-08-08)")
            budget = plan_capital(
                CapitalProgram(population=args.population, river=args.river, castle_seat=args.castle_seat, imperial_granary_seat=args.granary_seat, aspect=args.aspect, nring=args.nring),
                canvas=canvas,
            )
            print(format_budget(budget))
            return 0
        budget = plan_city(CityProgram(population=args.population, river=args.river, agricultural_district=args.agri, aspect=args.aspect, nring=args.nring), canvas=canvas)
    except ValueError as e:
        import sys

        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(format_budget(budget))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
