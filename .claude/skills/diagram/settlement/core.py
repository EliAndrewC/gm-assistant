"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import contextlib
import random
from collections.abc import Iterator
from typing import Any

from ._geom import LAND, Indexed, Manifest, PointGrid, Poly
from ._knobs import crop_boxes, resolve_knob, scope_seed
from .castle_civic import CastleCivicMixin
from .city import CityMixin
from .civic_grounds import CivicGroundsMixin
from .fields import FieldsMixin
from .finish import FinishMixin
from .homestead_parts import HomesteadPartsMixin
from .houses import HousesMixin
from .land import LandMixin
from .rolling import RollingMixin
from .shrines_wells import ShrinesWellsMixin
from .structures import StructuresMixin
from .trades import TradesMixin
from .water_ways import WaterWaysMixin


class Settlement(
    FieldsMixin, WaterWaysMixin, ShrinesWellsMixin, StructuresMixin, TradesMixin, HomesteadPartsMixin, LandMixin, CivicGroundsMixin, CityMixin, CastleCivicMixin, HousesMixin, RollingMixin, FinishMixin
):
    def __init__(self: Settlement, W: int = 1820, H: int = 1180, seed: int = 23) -> None:
        random.seed(seed)
        self.W, self.H = W, H
        self.seed = seed  # drives every unpinned knob's independent deterministic roll (feature 005)
        self.knob_pins: dict[str, Any] = {}  # knobs the spec pinned explicitly (bypass the roll)
        self._resolved_knobs: dict[str, Any] = {}  # knobs resolved so far, fed into later knobs' typing context
        self.out: list[str] = []
        self._pending_yards: list[
            tuple[float, float, float, float, float, Any]
        ] = []  # stable-yard scatters queued at stables()/animal_ground() time, DRAWN at crop time when every way/footprint exists (GM 2026-07-24: a yard drawn at stables-time could not see later-drawn streets, so its furniture landed on them)
        # DEFERRED: drawn at crop time, not where it is called. See "DRAW ORDER" in CLAUDE.md.
        self._pending_stands: list[
            tuple[Poly, int, bool]
        ] = []  # tree-stand canopies queued at forest()/forest_patch() time, DRAWN at crop time when every building + well exists (see flush_tree_stands)
        self.top: list[str] = []  # deferred TOP layer (gate furniture, torii, kido) - over roads/buildings
        self.toplabels: list[str] = []  # deferred LABEL layer - the very last thing drawn, so TEXT is never
        #                           covered by anything (a label must always be fully readable)
        self.frontage_rot: float = 0.0  # the LAST frontage() row's street axis in degrees (see frontage)
        self.frontage_box: tuple[float, float, float, float] | None = None  # extent of the LAST frontage() row,
        #                           for place_caption (see frontage's note)
        self._captions: list[tuple[Any, ...]] = []  # deferred place_caption() seats - flushed in finish()
        self.walls: list[str] = []  # deferred WALL layer (city rampart) - over the ground lanes + buildings,
        #                           under the TOP layer, so a street running INTO a wall passes beneath it
        self.ground: list[dict[str, Any]] = []  # deferred LINEAR ground features (alley < street < road): the wider
        self._ground_idx: int | None = None  # lane renders on top. Flushed as one ordered block (below buildings).
        self.water: list[dict[str, Any]] = []  # deferred WATERCOURSES (streams, channels, moat): all BEDS in one
        self._water_idx: int | None = None  # shared-opacity group, then all SHEENS in another, so crossings MERGE
        self._late_water_idx: int | None = None  # a SECOND water block for comb-field channels (opt-in via
        self.late_water: list[dict[str, Any]] = []  # field_channel(late=True)): spliced at its own first-call
        self._pond_entry: dict[str, Any] | None = None  # the pond's deferred water entry, so flush can RELOCATE
        # its fill+sheen into the late block when a late-block channel joins it (pond_fill_covers_channel_mouths)
        # position, AFTER the field's plots - a city draws its moat/river first, which anchors the shared
        # block early and would composite the whole ditch network UNDER the later-drawn paddy plots (the
        # network invisible + its uncovered corridors reading as parchment pinstripes; 2026-07-21). The
        # villages never hit this (their gens reach water after the fields), so late defaults False and
        # their output is byte-identical. Late ends are clipped to abut other water (never overlap), so
        # the two blocks cannot double-composite into a dark seam.
        #                           into a continuous confluence instead of stacking opacity (a dark seam).
        self.bscale = 1.0  # urban-building footprint scale (a large town packs at a finer grain)
        self.ftpx = 1.0  # declared REAL scale, feet per pixel - set via meta(ftpx=...); the
        #                           glyph library is calibrated at town scale (1 ft/px), so 1.0 = identity
        # THE THREE PLACEMENT REGISTRIES. Which one a feature registers in decides which placers
        # avoid it, and they are NOT equivalent - `_fits` (urban packs) point-tests block_polys but
        # DISTANCE-tests placed/grove_rects, so block_polys alone does not keep a whole footprint
        # out. Before adding to any of them, or changing when a feature is drawn relative to them,
        # read the "DRAW ORDER" section of this skill's CLAUDE.md and settle the sequence first -
        # ordering bugs surface far from the code that causes them.
        self.placed: list[Any] = Indexed()  # (x, y, w, h) - Indexed: _fits keeps a reach index on it, and the two filter-rebinds below stay Indexed so the index cannot go stale
        self.grove_rects: list[Any] = Indexed()  # (x, y, w, h) homestead-grove arms - kept OUT of `placed` so adjacent groves
        #                           may MERGE (abut) where houses cluster; `_fits` still steers wells off them
        self._pending_farmsteads: list[Any] = []  # farmhouses awaiting their threshing yard (drawn by farmsteads())
        self._rng_scope_n: dict[tuple[Any, ...], int] = {}  # per-key call counter for rng_scope (see its docstring)
        self.corridors: list[Any] = Indexed()  # polylines houses must avoid (Indexed: _near_corridor keeps a spatial index on it)
        # THE DRAWN TREAD of every way, as (polyline, half-width). Distinct from `corridors`, which
        # is a SOFT reservation (clearance, slack, standoff) tested against a candidate's CENTRE.
        # The tread is the hard thing - the surface a cart runs on - and a building's FOOTPRINT may
        # not overlap it at any angle. See `_fits`, which tests them differently on purpose.
        self.treads: list[Any] = []
        self._samurai_ward_interiors: list[Poly] = []  # closed samurai-ward region(s), cached by s.ward - s.building refuses WARD_BARRED_KINDS inside them
        self.bound: Any = None  # optional bounding polygon: placement stays inside it (city wall)
        self.view: Any = None  # optional (ox,oy,w,h) viewBox crop - render/checks treat it as the map edge
        self.field_polys: list[Any] = Indexed()  # smoothed outlines used for blocking (Indexed: _in_blocked keeps a spatial index on it)
        self.ellipses: list[Any] = []  # (cx, cy, rx, ry) hill/pond/manor - block houses
        self.block_polys: list[Any] = Indexed()  # arbitrary no-build polygons (e.g. forest) (Indexed: _in_blocked keeps a spatial index on it)
        # HARD no-build ground, tested against a candidate's whole FOOTPRINT rather than its center.
        # `block_polys` deliberately mixes two different things - hard ground (crop, pond, bog) and
        # SOFT reservations (caption bands, civic aprons, fence standoffs) that a footprint routinely
        # overhangs by a few px - which is why footprint-testing all of it was tried once and reverted
        # (it cost Nagahara a well and pushed Hoshizora's punishment ground off its street). The split
        # IS the fix: hard ground gets the footprint test it always needed, soft reservations keep the
        # center test they were tuned for. GM 2026-07-26: "if placement is only testing the house's
        # center while the matrix tests its footprint, then maybe the placement test is wrong?"
        self.hard_polys: list[Any] = []
        self._hard_cache_key: tuple[int, int, int] | None = None
        self._hard_cache: list[Any] = []
        # SWEPT/TENDED GROUND around sacred + funerary features - a keep-out for the LOOSE HINTERLAND
        # SCATTER (commons scrub + marsh reeds) ONLY, not for building placement and not for the grove.
        # A shrine precinct, the ground under a torii and along its sando, and the collar tended around
        # graves were kept clear of wild scrub in reality (raked gravel precinct; the tomb-swept grave
        # collar); the surrounding waste stays scrubby. So this clears a small verge around each, while a
        # shrine's deliberate fengshui/chinju-no-mori grove (a separate feature) is left untouched. See
        # settlements.md 'Swept ground around sacred + funerary features'.
        self.clearings: list[Any] = []
        self._verge_centers: list[tuple[float, float]] = []  # one (x, y) per clearings entry - _clear_ground's same-center dedupe key
        self._cover_n = 0  # ground-cover scatter ordinal (commons + marsh draws). Each cover entry and each
        #                    swept clearing records it, so the scatter_respects_swept_clearings check can see
        #                    ORDER: a scatter only skips clearings that exist when it runs, so a cover whose
        #                    seq <= a clearing's seq drew before the clearing was registered and may have
        #                    dotted scrub/reeds over the swept ground (fix: s.reserve_clearing FIRST).
        self._frozen_wells: tuple[tuple[PointGrid, PointGrid, PointGrid], Any] | None = None  # the well index while a frozen_terrain scope is open
        self._frozen_depth = 0
        self.dry_polys: list[Any] = Indexed()  # dry crop plots (comb hems, vegetable tracts): FOOTPRINT-aware no-build (Indexed: _in_blocked)
        #                           cropland - block_polys test only a candidate's CENTER, which let a house
        #                           centered just off a hem strip stand half its footprint on the crop (GM,
        #                           2026-07); these get an edge margin in _in_blocked + a rect test for groves
        self._bbox_cache: dict[Any, Any] = {}  # id(poly-list) -> (len, [per-poly (minx,miny,maxx,maxy)]) for the collision
        #                           pre-filter: reject a far polygon cheaply before the O(vertices) corner /
        #                           segment tests (the homestead solver probes _rect_blocked ~100k+ times)
        self._water_obs_cache: Any = None  # (lengths-key, [(poly, keep-out half-width, bbox)]) - same pre-filter idea
        #                                for _rect_on_water's irrigation lines (channels / ditches / streams)
        self._clip = 0
        self._nbig = 0
        self.M: Manifest = {
            "houses": [],
            "fields": [],
            "fallow_patches": [],
            "channels": [],
            "lane": [],
            "taxfree": [],
            "torii": [],
            "shrines": [],
            "manors": [],
            "streams": [],
            "buildings": [],
            "pastures": [],
            "forest_patches": [],
            "religious": [],
            "flower_fields": [],
            "labels": [],
            "pond": None,
            "storehouses": [],
            "flophouses": [],
            "hill": None,
            "summit": None,
            "shrine": None,
            "forest": None,
            "forest_edge": None,
            "tree_crowns": [],
            "road": None,
            "wall": None,
            "gate": None,
            "gates": [],
            "moat": None,
            "governor_mansion": None,
            "ministries": [],
            "inspection_stations": [],
            "wells": [],
            "bridges": [],
            "threshing_yards": [],
            "gardens": [],
            "groves": [],
            "cemeteries": [],
            "mausoleums": [],
            "cremation_grounds": [],
            "ossuaries": [],
            "punishment_spots": [],
            "execution_grounds": [],
            "boundary_markers": [],
            "moat_layer": None,
            "fire_towers": [],
            "kosatsuba": [],
            "field_ditches": [],
            "village_groves": [],
            "commons": [],
            "dry_plots": [],
            "marshes": [],
            "byres": [],
            "farm_sheds": [],
            "quarters": [],
            "meta": {"W": W, "H": H},
        }
        self._header()

    # ---- low level
    # draw-order index (z): base-layer items keep their position; TOP-layer items get a
    # huge offset so they always render above the base (roads must pass UNDER them)
    TOPZ = 10_000_000
    LABELZ = 20_000_000  # the LABEL layer renders above even the TOP layer - text is never covered
    WALLZ = 1_000_000  # the WALL layer renders above every ground lane and building (which sit in
    #                          self.out, z < len(out)), below the TOP layer - so lanes pass UNDER walls

    def add(self: Settlement, s: str) -> int:
        z = len(self.out)
        self.out.append(s)
        return z

    def add_wall(self: Settlement, s: str) -> int:
        z = self.WALLZ + len(self.walls)
        self.walls.append(s)
        return z

    def add_label(self: Settlement, s: str) -> int:
        z = self.LABELZ + len(self.toplabels)
        self.toplabels.append(s)
        return z

    def add_top(self: Settlement, s: str) -> int:
        z = self.TOPZ + len(self.top)
        self.top.append(s)
        return z

    def _ground(self: Settlement, zpri: float, rec: Any, zkey: str, edge: Any = None, bed: Any = None, top: Any = None) -> None:
        """Defer a linear ground feature (alley/street/road/ring road). The whole set renders as ONE
        block, in THREE sub-layers so crossings read as clean CROSSROADS: all EDGE strokes (the dark
        borders) at the bottom, then all BED strokes (the paved surfaces), then all TOP marks (center
        dashes / gravel speckle). Because every edge sits below every bed, no edge line ever cuts across
        another lane's bed at a junction - the beds merge into a continuous crossroads. Within each
        sub-layer the wider lane (higher zpri = WIDTH) is on top, so the wider road still wins where two
        beds overlap (road 26 > avenue 22 > street 18 > alley 10). Each feature records its BED's final
        draw position (rec[zkey]) for the width-layering check."""
        if self._ground_idx is None:
            self._ground_idx = len(self.out)
            self.out.append("")  # placeholder, replaced by the sorted block at finish()
        self.ground.append({"zpri": zpri, "seq": len(self.ground), "edge": edge, "bed": bed, "top": top, "rec": rec, "zkey": zkey})

    def _water(self: Settlement, bed: Any, rec: Any, sheen: Any = None, edge: Any = None, clip: Any = None, pond_fill: bool = False, late: bool = False) -> None:
        """Defer a watercourse (stream / channel / moat / POND) so the whole set renders as ONE block, in
        THREE sub-layers: all EDGES (pond rims - the only water feature with a border) at the bottom, then
        all BEDS (the blue water bodies, same color) inside one shared-opacity group, then all SHEENS (the
        lighter mid-current highlights) inside another above it. The shared bed-group opacity means
        overlapping water does NOT stack opacity into a dark seam where two courses cross - the beds
        composite into a single continuous body (a confluence), exactly as the ground beds merge into a
        clean crossroads. And because every EDGE sits below every bed, a feeder's bed COVERS a pond's rim
        where it meets it - so the stream/channel JOINS the pond at the rim (a clean gap) instead of the rim
        cutting across its mouth. Each course records its bed's / sheen's draw position on `rec` (bedz /
        sheenz) for waterways_merge_at_crossings. Spliced at the FIRST water call's position, so later fields
        still paint over a channel's end. `clip` (optional {'pts','bed_t','sheen_t'}) marks a pond-anchored
        feeder whose bed/sheen are RE-EMITTED at flush, snapped to the rim - deferred so it works even when the
        feeder is drawn BEFORE the pond (M['pond'] is not known at call time). `pond_fill` marks the pond's
        water body, drawn LAST among the beds so it paints over any feeder's inside-the-rim overshoot."""
        if late:
            # (RE-)ANCHOR the late block at EVERY late call, not just the first: a multi-comb map
            # emits plots-then-channels per field, so a block pinned at the FIRST field's position
            # would sit UNDER every later field's plots (GM 2026-07-21: Hoshizora/Hirameki nets
            # invisible; Tango/Nagahara's per-gen late=True had the same residual hole on their
            # 2nd+ fans). Anchoring at the LAST call puts the whole net above the last-drawn
            # plots - and every earlier field's plots too. The abandoned placeholders are empty
            # strings, inert in the final SVG.
            self._late_water_idx = len(self.out)
            self.out.append("")  # placeholder for the LATE block (see __init__)
            self.late_water.append({"bed": bed, "sheen": sheen, "edge": edge, "rec": rec, "clip": clip, "pond_fill": pond_fill})
            return
        if self._water_idx is None:
            self._water_idx = len(self.out)
            self.out.append("")  # placeholder, replaced by the three-group block at finish()
        self.water.append({"bed": bed, "sheen": sheen, "edge": edge, "rec": rec, "clip": clip, "pond_fill": pond_fill})

    def _cid(self: Settlement, prefix: str) -> str:
        self._clip += 1
        return f'{prefix}{self._clip}'

    def _header(self: Settlement) -> None:
        self.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W} {self.H}" font-family="Georgia, \'Times New Roman\', serif">')
        self.add('<defs>')
        self.add(
            '<pattern id="drycrop" width="12" height="12" patternUnits="userSpaceOnUse">'
            '<rect width="12" height="12" fill="#CDB57E"/>'
            '<line x1="0" y1="3" x2="12" y2="3" stroke="#A98E54" stroke-width="0.7"/>'
            '<line x1="0" y1="8" x2="12" y2="8" stroke="#A98E54" stroke-width="0.7"/></pattern>'
        )
        self.add(
            '<pattern id="fallow" width="14" height="14" patternUnits="userSpaceOnUse">'
            '<rect width="14" height="14" fill="#D7C49A"/>'
            '<circle cx="3" cy="4" r="0.9" fill="#A89464"/>'
            '<circle cx="9" cy="9" r="0.9" fill="#A89464"/>'
            '<circle cx="11" cy="3" r="0.7" fill="#B7A06C"/></pattern>'
        )
        self.add('</defs>')
        self.add(f'<rect width="{self.W}" height="{self.H}" fill="{LAND}"/>')

    def meta(self: Settlement, **kw: Any) -> None:
        if "ftpx" in kw:
            # The map's declared real scale in FEET PER PIXEL - the GM's ladder: hamlet/town 1,
            # village 2, provincial city 3 (the round numbers are deliberate; a human should be
            # able to read distances off the map). Buildings follow automatically via
            # bscale = 1/ftpx: the urban glyph library is calibrated at town scale (a 44x29px
            # farmhouse ~ the 46x28 ft minka anchor), so the building grain IS the scale change -
            # this is what keeps a "merchant house" the same real ~57 ft on every map.
            # VILLAGE maps are exempt: their placement constants (23x14 farmhouse, garden/yard
            # caps, grove bands, the well 0.52 factor) were hand-pre-scaled to 2 ft/px before
            # ftpx existed, and re-deriving them through bscale would perturb every tuned
            # village map for zero visual gain - so a village declares ftpx=2 for the record
            # (and for the checks) but keeps bscale = 1.0.
            self.ftpx = kw["ftpx"]
            if kw.get("scale", self.M["meta"].get("scale")) != "village":
                self.bscale = 1.0 / self.ftpx
        self.M["meta"].update(kw)

    def pin_knob(self: Settlement, name: str, value: Any) -> None:
        """Pin a knob to an explicit value, bypassing the roll. The pin is still validated against the
        knob's value_space + typing_rule when `resolve` is called (an invalid pin is a loud error)."""
        self.knob_pins[name] = value

    def knob_context(self: Settlement) -> dict[str, Any]:
        """The geography/other-knob context a typing_rule reads: the map meta (scale, down_deg, region,
        water-source kind, ...) plus every knob resolved so far, so a later knob's rule can depend on an
        earlier resolved one."""
        ctx = dict(self.M["meta"])
        ctx.update(self._resolved_knobs)
        return ctx

    def resolve(self: Settlement, name: str, do_roll: bool = True) -> Any:
        """Resolve a knob (pinned -> rolled -> default) against the running context, record it so later
        knobs' typing rules can read it, and return the value."""
        val = resolve_knob(name, self.seed, self.knob_context(), self.knob_pins, do_roll=do_roll)
        self._resolved_knobs[name] = val
        return val

    @contextlib.contextmanager
    def rng_scope(self: Settlement, name: str, *key: Any) -> Iterator[None]:
        """Run a block against an RNG stream that depends ONLY on (map seed, name, key) - never on
        how much randomness the map has drawn so far - and restore the outer stream on the way out.

        WHY (GM 2026-08-08). Everything in this engine drew from one global stream, so any change
        that altered the NUMBER of draws made before a phase re-rolled that phase, however unrelated.
        Measured on a caption-resize: one extra draw at the top of a gen left a hamlet's manifest
        alone in 61 of 63 keys, but moved 12 of a provincial city's 101 - houses, wells, gardens,
        groves, buildings, 11,058 tree crowns - and one of the collisions that fell out of it was a
        farm shed on a garden 700 px from the nearest thing that had changed. Debugging a map you did
        not touch is the expensive kind of work; this makes the blast radius the thing you edited.

        It is a SEEDED generalization of an idiom already in this file: `forest()` and a dozen others
        already save and restore the stream so their decorative draws do not shift later placement.
        Save/restore alone protects everything AFTER the block; re-seeding on entry protects the
        block itself from everything BEFORE it. Both halves are needed for a scope to be isolated.

        The key is what makes two calls distinct: pass the region rect (or whatever identifies this
        instance) and repeated calls on the SAME key get a per-key sequence number, so a second pack
        over the same ground does not redraw the first one's numbers. That sequence is per-key, so
        adding a pack in one quarter cannot renumber another quarter's."""
        k = (name, *key)
        n = self._rng_scope_n.get(k, 0)
        self._rng_scope_n[k] = n + 1
        st = random.getstate()
        random.seed(scope_seed(self.seed, name, (*key, n)))
        try:
            yield
        finally:
            random.setstate(st)

    def px(self: Settlement, ft: float) -> float:
        """A real-world size in FEET -> drawn pixels at this map's declared scale (meta ftpx)."""
        return ft / self.ftpx

    def lw(self: Settlement, ft: float) -> float:
        """Linework width in px for a real width in FEET, floored at 4px. Standard cartographic
        practice: thin linear features (a 5 ft roji, a hairline gutter) are drawn at a minimum
        visible width rather than to scale, because at 3 ft/px they would be under 2px and vanish.
        True-width-or-floored, never inflated past the floor - so wide features stay honest and
        the floor only rescues features that would otherwise be invisible."""
        return max(ft / self.ftpx, 4.0)

    def set_view(self: Settlement, ox: float, oy: float, w: float, h: float) -> None:
        """Crop the rendered map to (ox,oy,w,h) instead of the full canvas. Placement still uses
        the full coordinate space, so off-view features (estates, farmland) simply run off the
        edge. The checks read meta['view'] and treat this crop - not the canvas - as the map edge.
        Used for city maps, which 'just barely encompass' the walled city and let the countryside
        run off the edge (a city map is about the city; a town map is about its surroundings)."""
        self.view = (ox, oy, w, h)
        self.M["meta"]["view"] = [ox, oy, w, h]

    # solid HARD footprints the frame must fully contain (+ margin); the fields and pond are added specially.
    # Everything NOT listed here - the commons scrub, streams/channels/lanes - does not set the frame: it is
    # drawn and simply CLIPS at the crop edge (the frame stays tight to the settlement + its fields).
    # NOT "village_groves" (GM 2026-07-20): the COMMUNAL windbreak/copse may CLIP at the frame edge - a
    # partially visible belt reads as "the wood continues", and a smaller crop beats a larger one whose only
    # extra content is more of the same grove (this held Kikuta's frame open north of the village). The belt
    # hugs the cluster, so the houses' own margin always keeps part of it in view; hard_features_within_frame
    # requires partial visibility (not containment) for it, and crop_hugs_content gates the tightness.
    # Homestead "groves" stay: each hugs its own farmhouse, so it never drags the frame anyway.
    # A WOOD is drawn as individual trees at true density (see _tree_stand for the research).
    CANOPY_SPACING_FT = 13.0  # ~600 canopy stems/ha - one tree per ~180 sq ft
    CANOPY_R_FT = 8.5  # mean crown radius; a real canopy crown is ~5-8 m across
    FOREST_FLOOR = "#5C7042"  # shaded litter/understory between the crowns, not a terrain wash
    # How deep a canvas-filling wood is REVEALED by the crop: ~8 ranks of trees past the tree line.
    # That is enough for the canopy to close and read as a wood running off the frame; beyond it the
    # image is undifferentiated crowns (GM 2026-07-25: "only enough to make it clear the forest is
    # there"). Bounded copses (forest_patch) are framed whole - their shape is the point.
    FOREST_REVEAL_FT = 110.0
    CANOPY_PAD = 0.6  # placement-only clearance so a kept crown survives the manifest's 0.1px rounding (see _crown_covers)

    _CROP_HARD = (
        "houses",
        "gardens",
        "threshing_yards",
        "groves",
        "dry_plots",
        "buildings",
        "manors",
        "religious",
        "shrines",
        "flophouses",
        "storehouses",
        "farm_sheds",
        "merchant_estates",
        "wells",
        "fire_towers",
        "ministries",
        "inspection_stations",
        "cemeteries",
        "mausoleums",
        "cremation_grounds",
        "ossuaries",
        "punishment_spots",
        "execution_grounds",
        "boundary_markers",
        "forest_patches",
        "pastures",
    )

    # what sets a CITY frame (crop_city): the walled city + its KEPT satellites. Deliberately NOT the
    # farm fans, dry hems, farmhouses, or field infrastructure - on a city map the farmland's job is to
    # SHOW IT IS THERE, not to be fully contained ("it's okay if farms get cut off... the point is to
    # show they're there, not to show the entire field" - GM 2026-07-23), so fields CLIP at the edge
    # like a village's commons. Estates (manors) also clip: a fraction-off-edge estate with its land
    # running on is the wanted signal (city_estates_multiple_shown needs >= 1 visible - verify per map).
    _CROP_CITY = (
        "buildings",  # in-wall stock + extramural caravan clusters; the extramural gate-market/wharf SHOP string is excluded below - it clips at the frame per the slice doctrine (GM 2026-07-24)
        "flophouses",
        "cemeteries",
        "cremation_grounds",
        "ossuaries",
        "mausoleums",
        # the justice works are KEPT satellites too: an execution ground that clipped at the frame
        # would read as "somewhere off that way", which is the one thing its siting is not
        "punishment_spots",
        "execution_grounds",
        "boundary_markers",
        "religious",
        "ministries",
        "inspection_stations",
        "fire_towers",
        "storehouses",
        "merchant_estates",
        # the KILN WORKS is a kept satellite too (GM 2026-07-27). It was excluded while it was a
        # 28x18 ft mound whose caption was wider than it was - the note in presentation.md about
        # Tango's frame being set by the words "tanning yard" is from that era. A works with its
        # own housing is now wider than any caption of it, and a kiln clipped at the frame would
        # read as "there is a kiln somewhere off that way", which is the one thing a satellite
        # whose whole point is WHERE it stands must not read as.
        "kilns",
    )

    def crop_city(self: Settlement, margin: float = 35, west: float | None = None, north: float | None = None, east: float | None = None, south: float | None = None) -> None:
        """CITY content crop (GM 2026-07-23, replacing the hand-tuned wide MARGIN frames): frame the map to
        the moat ring + every KEPT satellite feature (gate markets, flophouses, funerary grounds, wharf
        stalls - the `_CROP_CITY` keys) + every placed LABEL box (labels_within_image demands containment),
        plus `margin`. The paddy fans, hems, farmhouses, and estates do NOT set the frame - they clip at
        the edge, reading as country that continues (the whole point of the wide-frame doctrine is kept by
        `margin`: ~100px past the moat still shows a working band of every fan that hugs the rim). Call
        AFTER every feature and label, BEFORE `title()` (the title drops into the framed window).
        Per-side margin overrides (west/north/east/south) keep a REPRESENTATIVE FARM BAND on a flank
        with no satellite to anchor the frame - e.g. Tango's west, where nothing but fans lies beyond
        the moat and the bare `margin` would re-create the pre-2026-07-23 sliver crop.
        THE AGGRESSIVE 35px MARGIN IS THE DEFAULT FOR ALL CITIES (GM 2026-07-23: "I would like the
        aggressive crop to be the default for all cities unless I state otherwise") - a new city gen
        calls `s.crop_city()` bare and adds only the farm-band override for its satellite-less flank
        (which flank that is varies by city; both current cities happen to use west=100)."""
        self.flush_stable_yards()  # yards draw HERE, seeing the complete map (GM 2026-07-24); their labels must exist before the frame is computed
        self.flush_tree_stands()  # ... and so does every wood's canopy, so no crown lands on a building placed after it
        _cboxes = self._crop_boxes(city=True)
        hx = [v for b in _cboxes for v in (b[0], b[1])]
        hy = [v for b in _cboxes for v in (b[2], b[3])]
        x0, y0 = max(0, min(hx) - (west if west is not None else margin)), max(0, min(hy) - (north if north is not None else margin))
        x1, y1 = min(self.W, max(hx) + (east if east is not None else margin)), min(self.H, max(hy) + (south if south is not None else margin))
        self.set_view(round(x0), round(y0), round(x1 - x0), round(y1 - y0))

    def _crop_boxes(self: Settlement, city: bool) -> list[tuple[float, float, float, float, str]]:
        """This map's frame-setting boxes - see the module-level `crop_boxes`, which check_village
        reads too so the crop and the check that gates it cannot drift apart."""
        return crop_boxes(self.M, city, self.ftpx, self.W, self.H)

    def crop_to_content(self: Settlement, margin: float = 30) -> None:
        """Frame the map to its CONTENT: set the render viewBox to the bounding box of the HARD features placed
        SO FAR plus `margin`, so the image is exactly as large as the settlement + its fields, tight to `margin`
        on every side (nonstandard sizes are fine, and the checks already treat the crop - not the canvas - as
        the map edge). Call this AFTER the large features (water, fields, houses) AND after any SET-APART
        hard feature that would otherwise sit outside the frame (a back-slope graveyard, an outlying shrine -
        those must be placed BEFORE the crop so it includes them), and BEFORE the small features that DROP INTO
        the framed space (wells among the houses, monk plots) AND the title.
        HARD (`_CROP_HARD` + torii arches + the fields' VISIBLE extent + the pond) is what sets the frame. Everything else -
        the BLEED commons scrub AND the linear/off-map RUNNERS (streams, channels, lanes) - does NOT affect the
        frame: it is drawn and simply CLIPS at the edge, trailing off as 'more wild ground / more map this way'.
        (We used to extend the frame to preserve 2/3 of a trailing commons, but the GM wants the frame tight to
        the real content - a graveyard, the pond - never held open by empty back-slope grazing, so the commons
        now clips like the marsh instead of dragging the frame out.)"""
        self.flush_tree_stands()  # the woods' canopy draws HERE, seeing the complete map (see flush_tree_stands)
        _boxes = self._crop_boxes(city=False)
        hx = [v for b in _boxes for v in (b[0], b[1])]
        hy = [v for b in _boxes for v in (b[2], b[3])]
        if not hx:  # pragma: no cover - crop is called only after the hard features are placed
            return
        # clamp the frame to the canvas: never open the view PAST the map edge (an EDGE feature like the forest
        # fills to the canvas edge, so its side must be the frame edge with no margin gap - else it reads as
        # "stopping short"). Content within the canvas is unaffected (villages crop tighter than this anyway).
        x0, y0 = max(0, min(hx) - margin), max(0, min(hy) - margin)
        x1, y1 = min(self.W, max(hx) + margin), min(self.H, max(hy) + margin)
        self.set_view(round(x0), round(y0), round(x1 - x0), round(y1 - y0))
