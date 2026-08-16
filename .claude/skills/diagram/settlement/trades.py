"""Split from settlement.py by feature 025 - see settlement/CLAUDE.md for the index."""

import math
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from ._geom import Pt, label_tilt, tilt_caption_seat

if TYPE_CHECKING:
    from .core import Settlement


class TradesMixin:
    # ---- TRADE WORKS (GM 2026-07-24; grounding in settlements.md "TRADE WORKS"): the trades whose
    # real premises outgrow the generic shop glyph - big attached works, yards, and outbuildings
    # that visibly show at map scale. Each records a first-class manifest entry (overlap-checked)
    # and blocks placement; sizes are TRUE feet via self.px. The long tail of trades (tofu,
    # noodles, apothecary, teahouse, cooper, and the ordinary town SMITH) deliberately stays inside
    # the generic shop rows - including the smith's hoof work. Rokugan DOES shoe horses in iron
    # (GM 2026-07-25, reversing the old "no farriers" null result), but that changes the smith's
    # repertoire, not his footprint; only where horses CONCENTRATE does farriery earn its own
    # premises, which is what s.farrier draws.

    def _trade_record(self: Settlement, key: str, x: float, y: float, w: float, h: float, rot: float, label: str, bm: float = 10.0, lab_off: float | None = None, label_xy: Pt | None = None) -> None:  # type: ignore[misc]
        """Record + block one trade-works footprint (shared tail of the trade glyph methods).

        `label_xy` hand-seats the caption (and its reserved band) when the default below-the-
        footprint seat collides with a neighbor the placement probe cannot see - the known
        label-probe limit (this skill's CLAUDE.md): a label box exists only at draw time, so a
        collision with an already-drawn TOP-layer fixture (Minami's lumber-yard caption grazing
        the log-boom pen by under a pixel, 2026-08-02) surfaces only at the gate, and the hand
        seat is the same remedy punishment_spot and the kosatsuba use."""
        self.M.setdefault(key, []).append({"x": round(x, 1), "y": round(y, 1), "w": round(w, 1), "h": round(h, 1), "rot": round(rot, 1), "label": label})
        self.placed.append((x, y, w, h))
        hw, hh = w / 2 + bm, h / 2 + bm
        # the block also reserves the LABEL band below the footprint - at the CAPTION's width,
        # which can exceed the feature's (the "bathhouse" text is wider than the 16px building) -
        # so the later packs cannot slide a house under the text (labels_clear_of_other_buildings;
        # the bathhouse/drum tower captions caught this on 2026-07-24's first regen)
        self.block_polys.append([(x - hw, y - hh), (x + hw, y - hh), (x + hw, y + hh), (x - hw, y + hh)])
        # the caption normally hangs off the RAW footprint half-height, but a ROTATED record's drawn
        # vertical extent is its axis-aligned half-height, (w/2)|sin| + (h/2)|cos| - and a caption
        # anchored at h/2 then lands INSIDE the record's own bbox, which
        # labels_clear_of_other_buildings reports as "'farrier' over a farrier" (GM 2026-07-25, the
        # rot=150 Hoshizora forge). A rotated caller passes its rotated half-height as `lab_off`.
        # NOT applied globally on purpose: the formula would also push the four rot=90 tanning-yard
        # captions ~5px down, which grows those maps' content crop, and on Tango a 5px taller frame
        # left an off-map channel anchor stranded INSIDE the frame (channel_field_anchored). Those
        # captions already clear their own footprints, so the churn would buy nothing.
        eh_ = h / 2 if lab_off is None else lab_off
        tilt_ = label_tilt(rot)
        if label and tilt_:
            # A DIAGONAL works captions ALONG ITS OWN TILT (label_tilt, GM 2026-08-02): the caption
            # hangs off the ROTATED lower edge - the local half-extent is exact there, so the
            # square-rotation `lab_off` escape does not apply - and the reserved band under the
            # text rotates with it, guarding the ground the tilted glyph run actually covers.
            bw_ = max(hw, 2.9 * len(label) + 10)
            lx_, ly_ = tilt_caption_seat(x, y, rot, tilt_, w / 2, h / 2, 11)
            ca_, sa_ = math.cos(math.radians(tilt_)), math.sin(math.radians(tilt_))
            self.block_polys.append([(lx_ + dx * ca_ - dy * sa_, ly_ + dx * sa_ + dy * ca_) for dx, dy in ((-bw_, -11.0), (bw_, -11.0), (bw_, 15.0), (-bw_, 15.0))])
            self.label(lx_, ly_, label, 9, italic=True, color="#5A4326", rot=tilt_)
        elif label:
            # the band anchors at the RAW footprint edge - the caption box starts ~edge+6, so
            # anchoring at the margin-inflated hh left its top half unguarded (the bathhouse
            # caption's merchant_house graze, 2026-07-24). +10 width slack because rowpack tests
            # corners but pack/place_wells test centers only (settlement init comment ~line 642).
            bw_ = max(hw, 2.9 * len(label) + 10)
            if label_xy is not None:
                lx_, ly_ = label_xy
                self.block_polys.append([(lx_ - bw_, ly_ - 11.0), (lx_ + bw_, ly_ - 11.0), (lx_ + bw_, ly_ + 15.0), (lx_ - bw_, ly_ + 15.0)])
                self.label(lx_, ly_, label, 9, italic=True, color="#5A4326")
            else:
                self.block_polys.append([(x - bw_, y + eh_), (x + bw_, y + eh_), (x + bw_, y + eh_ + 26), (x - bw_, y + eh_ + 26)])
                self.label(x, y + eh_ + 11, label, 9, italic=True, color="#5A4326")

    def brewery(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "brewery") -> None:  # type: ignore[misc]
        """A SAKE/MISO/SOY BREWERY compound - the biggest trade premises in a provincial seat
        (settlements.md "TRADE WORKS": a minimal sakagura is a 60-120 ft vat hall BEHIND a normal
        shopfront, 3-8x the shophouse footprint, very often the town's largest commercial building;
        1-2 per seat of ~3,000; brewers were town elite, sited IN town on good well water). Drawn
        as the long gabled VAT HALL (ridge + fermentation-vat circles + a masonry chimney), the
        street SHOPFRONT attached at one end, a rice KURA at the other, and the brewery's OWN WELL
        (mandatory water) in the working corner. Records M['breweries'] (city_has_brewery)."""
        hw_, hh_ = self.px(96) / 2, self.px(36) / 2  # the vat hall
        sw_, sh_ = self.px(40) / 2, self.px(26) / 2  # the shopfront
        kw_, kh_ = self.px(22) / 2, self.px(15) / 2  # the rice kura
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        hall_cy = -sh_  # hall strip on top, shop + kura row below
        g.append(f'<rect x="{-hw_:.1f}" y="{hall_cy - hh_:.1f}" width="{hw_ * 2:.1f}" height="{hh_ * 2:.1f}" rx="2" fill="#D9C8A4" stroke="#5A4326" stroke-width="1.8"/>')
        g.append(f'<line x1="{-hw_ + 2:.1f}" y1="{hall_cy:.1f}" x2="{hw_ - 2:.1f}" y2="{hall_cy:.1f}" stroke="#5A4326" stroke-width="0.9" opacity="0.7"/>')  # the ridge
        for vi in (
            -0.72,
            -0.28,
            0.2,
            0.6,
        ):  # the hall's fermentation tanks, drawn diagrammatically INSIDE the footprint (a vat is interior fixture, not a freestanding object - GM catch 2026-07-24: the old hw_*2*vi math pushed one past the hall's end wall)
            g.append(f'<circle cx="{hw_ * vi:.1f}" cy="{hall_cy + hh_ * 0.3:.1f}" r="1.7" fill="none" stroke="#5A4326" stroke-width="0.8" opacity="0.8"/>')
        g.append(f'<rect x="{hw_ - 4.6:.1f}" y="{hall_cy - hh_ - 2.6:.1f}" width="3.4" height="3.4" fill="#5A4326"/>')  # the masonry kamado chimney
        g.append(f'<rect x="{-hw_:.1f}" y="{hh_ - sh_ * 0 - 0.5:.1f}" width="{sw_ * 2:.1f}" height="{sh_ * 2:.1f}" rx="2" fill="#D8C49A" stroke="#6B4F2A" stroke-width="1.6"/>')  # the shopfront
        aw_ = max(5.0 * self.bscale, 2.4)
        g.append(f'<rect x="{-hw_:.1f}" y="{-0.5 + sh_ * 2 - aw_:.1f}" width="{sw_ * 2:.1f}" height="{aw_:.1f}" fill="#A8472E" opacity="0.95"/>')  # its awning band
        g.append(f'<rect x="{hw_ - kw_ * 2:.1f}" y="{-0.5:.1f}" width="{kw_ * 2:.1f}" height="{kh_ * 2:.1f}" rx="1" fill="#F2EFE4" stroke="#4A3318" stroke-width="1.4"/>')  # the rice kura
        g.append('</g>')
        self.add(''.join(g))
        th_ = math.radians(rot)
        wx_, wy_ = x + math.cos(th_) * hw_ * 0.35 + math.sin(th_) * (sh_ + 3), y + math.sin(th_) * hw_ * 0.35 + math.cos(th_) * (sh_ + 3)
        self.well(wx_, wy_, private=True)  # the brewery's OWN well (mandatory brewing water) - a premises fixture, excluded from the public idobata accounting
        self._trade_record("breweries", x, y, self.px(96), self.px(36) + self.px(26), rot, label)

    def dye_yard(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "dye works") -> None:  # type: ignore[misc]
        """A DYER's premises (kon-ya): the workshop fits a shophouse - the GROUND does not. Drying
        poles/racks dominated the dyer's block (Hiroshige's Kanda Konya-cho), and rinsing happened
        in open water, so the yard sits ON water: a stream, channel, canal, the pond, or the moat
        (city_has_dye_works enforces the adjacency; ~2,000-5,000 sq ft of racks at town scale,
        bolts run 35-40 ft). Drawn as the small vat WORKSHOP + rack lines hung with indigo cloth.
        Records M['dye_yards']."""
        yw_, yh_ = self.px(80), self.px(52)
        ww_, wh_ = self.px(36) / 2, self.px(24) / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(
            f'<rect x="{-yw_ / 2:.1f}" y="{-yh_ / 2:.1f}" width="{yw_:.1f}" height="{yh_:.1f}" rx="1.5" fill="#E7DBB8" fill-opacity="0.75" stroke="#B99F72" stroke-width="0.8"/>'
        )  # the yard's tamped ground - without it the racks read as stray marks at fit zoom (GM missed the whole works, 2026-07-24)
        g.append(f'<rect x="{-yw_ / 2:.1f}" y="{-yh_ / 2:.1f}" width="{ww_ * 2:.1f}" height="{wh_ * 2:.1f}" rx="2" fill="#C2B190" stroke="#6B5A3A" stroke-width="1.6"/>')  # the vat workshop
        for di_ in (0.62, 0.82):  # sunken indigo vats by the workshop door
            g.append(f'<circle cx="{-yw_ / 2 + ww_ * 2 * di_ + 2:.1f}" cy="{-yh_ / 2 + wh_ * 2 + 2.6:.1f}" r="1.6" fill="#3F5E7E" stroke="#2C3F52" stroke-width="0.6"/>')
        rx0_ = -yw_ / 2 + ww_ * 2 + 3
        for ri_ in range(4):  # the drying racks, hung with bolt-lengths of indigo cloth
            ry_ = -yh_ / 2 + 2.5 + ri_ * (yh_ - 5) / 3
            g.append(f'<line x1="{rx0_:.1f}" y1="{ry_:.1f}" x2="{yw_ / 2 - 1.5:.1f}" y2="{ry_:.1f}" stroke="#6B4F2A" stroke-width="1.3"/>')
            for ci_ in (0.12, 0.38, 0.62, 0.85):
                cx0_ = rx0_ + (yw_ / 2 - 1.5 - rx0_) * ci_
                g.append(f'<line x1="{cx0_:.1f}" y1="{ry_:.1f}" x2="{cx0_ + 3.4:.1f}" y2="{ry_:.1f}" stroke="#3F5E7E" stroke-width="2.8" opacity="0.92"/>')
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record("dye_yards", x, y, yw_, yh_, rot, label)

    def lumber_yard(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "lumber yard", label_xy: Pt | None = None) -> None:  # type: ignore[misc]
        """A riverside LUMBER YARD (zaimokuya) - stacked timber + a river landing; stock moves by
        water at scale, so this is a RIVER-PORT feature only (city_river_port_has_lumber_yard;
        a landlocked city has none - the GM's Tango/Nagahara split). Small office + stack rows.
        Records M['lumber_yards']."""
        yw_, yh_ = self.px(90), self.px(60)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-yw_ / 2:.1f}" y="{-yh_ / 2:.1f}" width="{self.px(24):.1f}" height="{self.px(16):.1f}" rx="2" fill="#D8C49A" stroke="#6B4F2A" stroke-width="1.5"/>')  # the office/house
        for sx_, sy_ in ((0.05, -0.25), (0.42, -0.25), (0.05, 0.28), (0.42, 0.28), (-0.32, 0.28)):
            ox_, oy_ = -yw_ / 2 + yw_ * (sx_ + 0.28), -yh_ / 2 + yh_ * (sy_ + 0.42)
            for li_ in range(4):  # one squared-timber stack
                g.append(f'<line x1="{ox_ - 4.6:.1f}" y1="{oy_ + li_ * 1.5 - 2.2:.1f}" x2="{ox_ + 4.6:.1f}" y2="{oy_ + li_ * 1.5 - 2.2:.1f}" stroke="#8A6B42" stroke-width="1.1"/>')
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record("lumber_yards", x, y, yw_, yh_, rot, label, label_xy=label_xy)

    def oil_press(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "oil press") -> None:  # type: ignore[misc]
        """An OIL PRESSER's barn (aburaya / youfang): the wedge-and-beam press is a massive timber
        machine plus an ox-driven edge-runner mill on a ~20-25 ft circular track - a barn-scale
        works (~40-60 x 25-30 ft), fire-conscious, toward the town edge. Barn + the mill ring.
        Records M['oil_presses'] (city_has_oil_press)."""
        bw_, bh_ = self.px(54) / 2, self.px(30) / 2
        ring_r = self.px(22) / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-bw_ - ring_r * 0.9:.1f}" y="{-bh_:.1f}" width="{bw_ * 2:.1f}" height="{bh_ * 2:.1f}" rx="2" fill="#C9A57A" stroke="#5A4326" stroke-width="1.7"/>')  # the press barn
        g.append(f'<line x1="{-bw_ - ring_r * 0.9 + 2:.1f}" y1="0" x2="{bw_ - ring_r * 0.9 - 2:.1f}" y2="0" stroke="#5A4326" stroke-width="0.9" opacity="0.7"/>')
        rcx_ = bw_ + ring_r * 0.35
        g.append(f'<circle cx="{rcx_:.1f}" cy="0" r="{ring_r:.1f}" fill="none" stroke="#7A5A30" stroke-width="1.1" stroke-dasharray="3,2"/>')  # the ox track
        g.append(f'<circle cx="{rcx_:.1f}" cy="0" r="1.3" fill="#5A4326"/>')  # the edge-runner post
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record("oil_presses", x, y, self.px(54) + ring_r * 2.5, self.px(30), rot, label)

    def pawnshop(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "pawnshop") -> None:  # type: ignore[misc]
        """A PAWNSHOP (shichiya): an ordinary shopfront whose tell is STORAGE - pledges are bulky,
        so the broker keeps 2-3 fireproof kura in a walled rear court (the existing kura glyph
        multiplied, per settlements.md "TRADE WORKS"). Records M['pawnshops'] (city_has_pawnshop)."""
        sw_, sh_ = self.px(48) / 2, self.px(32) / 2
        kw_, kh_ = self.px(20) / 2, self.px(14) / 2
        ch_ = kh_ * 2 + 4.5  # the rear court's depth
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(
            f'<rect x="{-sw_:.1f}" y="{-sh_ - ch_ / 2 + ch_:.1f}" width="{sw_ * 2:.1f}" height="{sh_ * 2:.1f}" rx="2" fill="#D8C49A" stroke="#6B4F2A" stroke-width="1.6"/>'
        )  # the shopfront (street side)
        aw_ = max(5.0 * self.bscale, 2.4)
        g.append(f'<rect x="{-sw_:.1f}" y="{-sh_ - ch_ / 2 + ch_ + sh_ * 2 - aw_:.1f}" width="{sw_ * 2:.1f}" height="{aw_:.1f}" fill="#A8472E" opacity="0.95"/>')
        g.append(f'<rect x="{-sw_ - 1.5:.1f}" y="{-sh_ - ch_ / 2 - 1.5:.1f}" width="{sw_ * 2 + 3:.1f}" height="{ch_ + 1.5:.1f}" fill="none" stroke="#4A3318" stroke-width="1.1"/>')  # the court wall
        for ki_ in (-0.52, 0.02):  # the pledge kura pair in the walled court
            g.append(f'<rect x="{sw_ * 2 * ki_:.1f}" y="{-sh_ - ch_ / 2 + 1.6:.1f}" width="{kw_ * 2:.1f}" height="{kh_ * 2:.1f}" rx="1" fill="#F2EFE4" stroke="#4A3318" stroke-width="1.4"/>')
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record("pawnshops", x, y, self.px(48) + 3, self.px(32) + ch_, rot, label)

    def bathhouse(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "bathhouse") -> None:  # type: ignore[misc]
        """A BATHHOUSE (sento; China-first correct - commercial baths are attested from the Song):
        a shophouse-scale bath building with a rear furnace + chimney, and the visible extra - the
        firewood stack yard behind. Records M['bathhouses'] (city_has_bathhouse)."""
        bw_, bh_ = self.px(48) / 2, self.px(32) / 2
        wd_ = self.px(22)  # the FUEL YARD band behind - the furnace's firewood store, the sento's visible extra (GM 2026-07-24: the first 3-line woodpile read too subtle to register as a yard)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(f'<rect x="{-bw_:.1f}" y="{-bh_ - wd_ / 2 + wd_:.1f}" width="{bw_ * 2:.1f}" height="{bh_ * 2:.1f}" rx="2" fill="#D8C49A" stroke="#6B4F2A" stroke-width="1.6"/>')
        g.append(f'<rect x="{bw_ - 4.4:.1f}" y="{-bh_ - wd_ / 2 + wd_ - 2.4:.1f}" width="3.2" height="3.2" fill="#5A4326"/>')  # the furnace chimney
        g.append(f'<line x1="{-bw_:.1f}" y1="{-bh_ - wd_ / 2:.1f}" x2="{bw_:.1f}" y2="{-bh_ - wd_ / 2:.1f}" stroke="#6B4F2A" stroke-width="0.9" opacity="0.7"/>')  # the fuel yard's back fence line
        for sxo_ in (-bw_ + 2, 1.5):  # two firewood stacks fill the fuel yard
            for li_ in range(4):
                g.append(
                    f'<line x1="{sxo_:.1f}" y1="{-bh_ - wd_ / 2 + 1.9 + li_ * 1.6:.1f}" x2="{sxo_ + self.px(18):.1f}" y2="{-bh_ - wd_ / 2 + 1.9 + li_ * 1.6:.1f}" stroke="#8A6B42" stroke-width="1.2"/>'
                )
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record("bathhouses", x, y, self.px(48), self.px(32) + wd_, rot, label)

    def bathhouses(self: Settlement, seats: Sequence[tuple[float, float]], count: int | None = None) -> int:  # type: ignore[misc]
        """Place the city's sento, COUNT ROLLED FROM POPULATION (GM formula 2026-07-24): ONE
        bathhouse per full 2,000 population, plus a chance of one EXTRA equal to the remainder
        fraction - a 2,500 seat keeps 1 + a 25% roll, a 3,000 seat 1 + 50%, a 4,000 seat exactly
        2 (floored at 1) - anchored on Edo's own peak ratio of ~1 sento per ~2,100 residents
        (1808: 523 sento for ~1.1M). Seats are hand-vetted
        (x, y) candidates, first n drawn - provide 2 so any roll can land; `count=` pins the
        roll (the merchant_estates analog). Recorded as meta['bathhouse_roll'] and gated by
        city_has_bathhouse, so a stale hand count can never ship. The roll consumes NO
        main-stream RNG (dedicated Random on the map seed): a map rolling its old count stays
        byte-identical."""
        pop = int(self.M.get("meta", {}).get("population") or 3000)
        # GM formula (2026-07-24, second refinement): 1 bathhouse per full 2,000 population, plus
        # a chance of ONE extra equal to the remainder fraction - a 2,500 seat has 1 guaranteed +
        # a 25% roll, a 3,000 seat 1 + 50%, a 4,000 seat exactly 2. Floored at 1; count= pins.
        rolled = max(1, pop // 2000 + (1 if random.Random(self.seed * 1409 + 53).random() < (pop % 2000) / 2000 else 0))
        n = int(count) if count is not None else rolled
        if n > len(seats):
            raise ValueError(f"bathhouses rolled {n} but only {len(seats)} vetted seats were provided - add candidates (the population band can ask for up to 2)")
        for bx_, by_ in seats[:n]:
            self.bathhouse(bx_, by_)
        self.M["meta"]["bathhouse_roll"] = n
        return n

    def farrier(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "farrier") -> None:  # type: ignore[misc]
        """A FARRIER's shoeing forge - the one hoof-care premises that earns its own footprint
        (grounding: settlements.md "TRADE WORKS", the FARRIERY sub-entry).

        Rokugan shoes horses in IRON where Edo Japan used woven straw, for two reasons that are
        both already in the GM's canon: continental ore makes iron a normal industrial good (the
        Tatarano/Kuroiwa/Ubame iron districts in l7r.md), and the Imperial relay puts institutional
        mileage on horses no island economy ever demanded (budgets.md staffs busy trunk waystations
        with "a smith for shoeing horses"; l7r.md's Moto Khuyag is a Rokugani-born farrier). Straw
        survives everywhere iron is not worth it - peasant pack horses, oxen on soft paddy tracks,
        poor and mountain provinces - because it is free, not because iron is unknown.

        An ORDINARY town smith still fits the generic shop glyph: shoeing changes his repertoire,
        not his premises. This feature is only for where horses CONCENTRATE - a city gate's caravan
        yard, an Imperial-road relay town - which is why it must stand beside a stables and nowhere
        else (farrier_serves_a_stables).

        Drawn as the open-sided forge SHED (hearth, smoke hood, anvil, quench tub) plus the working
        APRON in front, where the animal is actually stood. The apron carries the shoeing post and
        the OX-SHOEING FRAME - the timber stocks a cloven-hoofed ox has to be slung in, because it
        cannot balance on three legs while a foot is worked, and Rokugan's draft animal is mostly
        the ox.

        Sizes (TRUE feet, no legibility inflation): an 18-20 ft village smithy is the anchor, and
        the apron is a horse's length (~8 ft) plus room to lead one in and turn it. The shed is
        deliberately NOT attached to the stables - an open forge against a hay-and-timber stall
        range is a fire the yard does not survive, so real yards kept the smithy across the ground
        (farrier_keeps_fire_gap). Records M['farriers']."""
        sw_, sh_ = self.px(20), self.px(18)  # the forge shed
        aw_, ah_ = self.px(28), self.px(20)  # the working apron in front of it
        top_ = -(sh_ + ah_) / 2
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        # the APRON ground plane first, under everything - beaten earth, the same convention the dye
        # and tanning yards use: without a ground plane the furniture reads as stray marks at fit zoom
        g.append(
            f'<rect x="{-aw_ / 2:.1f}" y="{top_ + sh_:.1f}" width="{aw_:.1f}" height="{ah_:.1f}" rx="1.5" fill="#DCCBA6" fill-opacity="0.7" stroke="#B99F72" stroke-width="0.8" stroke-dasharray="3,2"/>'
        )  # DASHED edge: open working ground, not a roofed room (a solid box read as a second building at town scale)
        g.append(f'<rect x="{-sw_ / 2:.1f}" y="{top_:.1f}" width="{sw_:.1f}" height="{sh_:.1f}" rx="1" fill="#C2A87C" stroke="none"/>')
        # THREE walls and an OPEN front: the smoke and the horse both need the opening, so the
        # apron-side edge is drawn as an eaves line, never a wall stroke
        g.append(
            f'<path d="M {-sw_ / 2:.1f} {top_ + sh_:.1f} L {-sw_ / 2:.1f} {top_:.1f} L {sw_ / 2:.1f} {top_:.1f} L {sw_ / 2:.1f} {top_ + sh_:.1f}" fill="none" stroke="#5A4326" stroke-width="1.7"/>'
        )
        g.append(f'<line x1="{-sw_ / 2:.1f}" y1="{top_ + sh_:.1f}" x2="{sw_ / 2:.1f}" y2="{top_ + sh_:.1f}" stroke="#8A6B42" stroke-width="0.8" opacity="0.7"/>')
        hw_, hh_ = self.px(5), max(self.px(3), 1.2)  # the masonry hearth against the back wall
        g.append(f'<rect x="{-hw_ / 2:.1f}" y="{top_ + 0.8:.1f}" width="{hw_:.1f}" height="{hh_:.1f}" fill="#4A3318"/>')
        ch_ = max(self.px(2.5), 1.0)  # its smoke hood, breaking the back roofline
        g.append(f'<rect x="{-ch_ / 2:.1f}" y="{top_ - ch_:.1f}" width="{ch_:.1f}" height="{ch_:.1f}" fill="#5A4326"/>')
        av_ = max(self.px(2), 0.9)  # the anvil on its block, standing clear of the hearth
        g.append(f'<rect x="{-self.px(4) - av_ / 2:.1f}" y="{top_ + sh_ * 0.55:.1f}" width="{av_:.1f}" height="{max(self.px(1.6), 0.8):.1f}" fill="#3E3226"/>')
        g.append(f'<circle cx="{self.px(4):.1f}" cy="{top_ + sh_ * 0.6:.1f}" r="{max(self.px(2.4) / 2, 0.8):.1f}" fill="#8FA6B0" stroke="#5A6B72" stroke-width="0.6"/>')  # the quench tub
        apy_ = top_ + sh_ + ah_ / 2
        g.append(f'<circle cx="{-aw_ / 2 + self.px(5):.1f}" cy="{apy_:.1f}" r="{max(self.px(1.2), 0.7):.1f}" fill="#6B4F2A"/>')  # the shoeing post - a horse is tied short while its feet are worked
        # the OX-SHOEING FRAME (stocks), ~7 x 4 ft: four posts and two rails, the animal slung in a
        # belly band and its foot strapped up to a rail
        fx0_, fy0_, fw_, fh_ = self.px(1), apy_ - self.px(2), self.px(7), self.px(4)
        for ry_ in (fy0_, fy0_ + fh_):
            g.append(f'<line x1="{fx0_:.1f}" y1="{ry_:.1f}" x2="{fx0_ + fw_:.1f}" y2="{ry_:.1f}" stroke="#6B4F2A" stroke-width="1.1"/>')
        for pxp_ in (fx0_, fx0_ + fw_):
            for pyp_ in (fy0_, fy0_ + fh_):
                g.append(f'<circle cx="{pxp_:.1f}" cy="{pyp_:.1f}" r="{max(self.px(0.9), 0.6):.1f}" fill="#5A4326"/>')
        g.append(
            f'<ellipse cx="{-aw_ / 2 + self.px(3):.1f}" cy="{top_ + sh_ + self.px(3):.1f}" rx="{max(self.px(3) / 2, 1.0):.1f}" ry="{max(self.px(2) / 2, 0.8):.1f}" fill="#5C5750" opacity="0.85"/>'
        )  # the clinker heap - forge waste, swept out daily
        g.append('</g>')
        self.add(''.join(g))
        th_ = math.radians(rot)
        self._trade_record("farriers", x, y, aw_, sh_ + ah_, rot, label, lab_off=abs(aw_ / 2 * math.sin(th_)) + abs((sh_ + ah_) / 2 * math.cos(th_)))

    def kiln(self: Settlement, x: float, y: float, rot: Any = None, cottages: int = 2, label: str = "kiln works") -> None:  # type: ignore[misc]
        """A KILN WORKS at the settlement's periphery: the kiln itself, the throwing and drying
        shed, the clay pit, the fuel stack, its own well, and the two or three cottages of the
        households that work it. `rot` lays the kiln's UPSLOPE axis along local +x, so the stoke
        mouth is at local -x and the chimney at local +x.

        Historical grounding (the "why" - see settlements/urban-features.md "KILN WORKS", full
        record in research/urban-features.md). Two GM questions on 2026-07-27 drove the whole
        feature: *"would whoever works the kiln also live next to it?"* and *"why is it
        specifically a tile kiln and not just a kiln?"*

          - IT IS A KILN, NOT A TILE KILN. The old default caption was never argued for anywhere,
            and the volume reasoning behind it runs the WRONG WAY. Tile demand is lumpy and
            project-driven: a tiled roof lasts generations, and in a county seat tile reaches only
            the temple halls, the gates, the governor's compound and a few rich merchants - the
            rest is thatch and shingle. Pottery demand is CONTINUOUS: every household breaks and
            replaces bowls, pots and jars on a steady cycle, which is exactly why potsherds are
            the most reliable thing in an archaeological layer. The map's own brewery makes it
            worse - fermentation vessels and big storage jars are heavy and cheap per pound, so
            they are made near where they are used rather than freighted in. Per YEAR a seat this
            size burns more clay into vessels than into roof tiles. One works firing mixed loads
            is the honest drawing: coarse tile and coarse domestic ware share a clay source, an
            operator and a low firing. Fine stoneware needs its own hotter, longer firing and is a
            PROVINCE's specialty, not every county seat's. A map that knows what a particular
            works fires says so in its own `label`.
          - THE WORKERS LIVE HERE, which is why this is a works and not a lone glyph. A firing runs
            for DAYS, stoked in shifts around the clock until the ware is done and then sealed to
            cool - nobody walks back into town at dusk in the middle of one. And the kiln stands at
            the CLAY, not at the customer: siting follows the clay pit, the fuel, and a slope to
            build the chambers into, which pulls digging, weathering, throwing, drying and firing
            out to one spot together. CHINA FIRST: Song/Ming kiln districts were worked by
            registered kiln households living at their kilns, Jingdezhen being a whole city grown
            around them. Japan agrees - Seto, Tokoname, Bizen, Imado on Edo's fringe, Awataguchi
            and Kiyomizu at Kyoto's edge are kiln VILLAGES and kiln quarters, not commuter shops.
          - BANISHMENT IS ABOUT THE CITY, NOT THE OPERATOR. Fire law and smoke put the kiln outside
            the wall (city_kiln_outside_walls), but that is about keeping the risk out of the dense
            blocks; it says nothing against the households whose trade it is. They stand off the
            kiln by the same fire gap anyone else would (kiln_keeps_fire_gap).
          - A CHAMBERED CLIMBING KILN, NOT A MOUND. The glyph this replaces was a low earthen
            mound, which is a CHARCOAL or lime kiln's shape and read as one. A tile or pottery kiln
            in this culture is a long chambered tunnel built into a slope - firebox low, chambers
            climbing, chimney high - and that silhouette also carries the siting implication the
            mound hid: the works needs rising ground.
          - THE TOWN'S POTTERS ARE NOT MISSING. Only the FIRING is banished. A crockery dealer or a
            potter's shopfront inside the walls is an ordinary shophouse and stays in the generic
            shop rows with the tofu maker and the cooper - see the NULL results under "TRADE WORKS".

        Sizes are TRUE feet at the map's grain, pitched against the pool's other bulk works (the
        charcoal yard's 88x58, the brewery's 96 ft hall). The recorded FOOTPRINT is the whole
        tamped works ground rather than a `parts` list: unlike a ward gate, every part of this
        feature shares one set of permissions and stands on one patch of ground, so the yard rect
        is the honest extent and keeps the overlap matrix conservative.

        Records M['kilns'] with `body` (the kiln itself, world coords, which kiln_keeps_fire_gap
        measures from) and `quarters` (the works' own cottages). The cottages are recorded INSIDE
        this record and deliberately NOT in M['houses']: every dwelling rule in the gate - well
        reach, ward classification, the burakumin standoff - is written about the settlement's own
        housing stock, and a satellite works' two cottages would be adjudicated by rules that were
        never about them."""
        if rot is None:
            # a kiln hauls fuel and clay by CART, so it stands on its haul road and lies along it -
            # derived from the way at draw time, so a re-routed road turns the works with it
            _kd, _kb = self._way_bearing_near(x, y)
            rot = _kb if _kd < self.px(400) else 0.0
        rot = float(rot)
        f, g = self.px, [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        yw_, yh_ = f(140), f(120)
        th_ = math.radians(rot)

        def _world(lx: float, ly: float) -> tuple[float, float]:
            """Local (feet-derived px) offset -> world px, through this works' own rotation."""
            return x + lx * math.cos(th_) - ly * math.sin(th_), y + lx * math.sin(th_) + ly * math.cos(th_)

        g.append(
            f'<rect x="{-yw_ / 2:.1f}" y="{-yh_ / 2:.1f}" width="{yw_:.1f}" height="{yh_:.1f}" rx="1.5" fill="#E0D2AC" fill-opacity="0.75" stroke="#B99F72" stroke-width="0.9"/>'
        )  # the tamped works ground, the same ground-plane convention the charcoal/dye/tanning yards use
        # (A slope band behind the kiln was tried and cut: at city grain it read as a stray tab off
        # the kiln's shoulder rather than as ground. The CHAMBERED FORM already says "built up a
        # slope" - that is the whole difference between this and the mound it replaces.)
        # THE KILN: firebox at the low (-x) end, four chambers climbing, chimney at the high end
        bw_, bh_ = f(46), f(16)
        bcx_, bcy_ = f(6), -f(40)
        g.append(f'<rect x="{bcx_ - bw_ / 2:.1f}" y="{bcy_ - bh_ / 2:.1f}" width="{bw_:.1f}" height="{bh_:.1f}" rx="2" fill="#B08968" stroke="#5A4326" stroke-width="1.6"/>')
        for ci_ in range(4):  # the chamber divisions - a noborigama read from above is a row of joined chambers, not a dome
            g.append(
                f'<line x1="{bcx_ - bw_ / 2 + f(6) + ci_ * f(9):.1f}" y1="{bcy_ - bh_ / 2 + 0.8:.1f}" x2="{bcx_ - bw_ / 2 + f(6) + ci_ * f(9):.1f}" y2="{bcy_ + bh_ / 2 - 0.8:.1f}" stroke="#5A4326" stroke-width="0.9" opacity="0.8"/>'
            )
        g.append(f'<rect x="{bcx_ - bw_ / 2 - 2.2:.1f}" y="{bcy_ - 1.6:.1f}" width="3.4" height="3.2" fill="#4A3318"/>')  # the stoke mouth, at the firebox end
        g.append(f'<rect x="{bcx_ + bw_ / 2 - 2.6:.1f}" y="{bcy_ - bh_ / 2 - 2.6:.1f}" width="3.2" height="3.2" fill="#5A4326"/>')  # the chimney, at the top of the climb
        g.append(f'<path d="M {bcx_ + bw_ / 2 - 1:.1f} {bcy_ - bh_ / 2 - 3:.1f} q 2 -3.5 0.5 -7" fill="none" stroke="#9A9A92" stroke-width="1.1" opacity="0.75"/>')  # smoke
        # THE FUEL STACK, at the stoke end where the stoker wants it (a multi-day firing eats wood
        # continuously, so the stack is working stock, not a store set safely apart)
        for wi_ in range(4):
            g.append(f'<rect x="{-f(42) + wi_ * f(5):.1f}" y="{-f(46):.1f}" width="{f(3.4):.1f}" height="{f(12):.1f}" rx="1" fill="#8C7047" stroke="#5A4326" stroke-width="0.7"/>')
        # THE THROWING AND DRYING SHED - open-sided, the ware standing on boards out of the sun
        sw_, sh_ = f(32), f(18)
        scx_, scy_ = -f(46), f(4)
        g.append(f'<rect x="{scx_ - sw_ / 2:.1f}" y="{scy_ - sh_ / 2:.1f}" width="{sw_:.1f}" height="{sh_:.1f}" rx="1" fill="#C9A57A" stroke="#6B4F2A" stroke-width="1.6"/>')
        g.append(f'<line x1="{scx_ - sw_ / 2 + 2:.1f}" y1="{scy_:.1f}" x2="{scx_ + sw_ / 2 - 2:.1f}" y2="{scy_:.1f}" stroke="#6B4F2A" stroke-width="0.8" opacity="0.7"/>')  # the ridge
        for pi_ in range(4):  # drying ware on its boards
            g.append(f'<circle cx="{scx_ - sw_ / 2 + f(6) + pi_ * f(7):.1f}" cy="{scy_ + f(5):.1f}" r="{max(0.9, f(2)):.1f}" fill="none" stroke="#6B4F2A" stroke-width="0.7" opacity="0.85"/>')
        # THE CLAY PIT - dug open ground, dashed like the charcoal yard's apron because it is a
        # worked hole rather than a roofed room. The works stands at its clay; this is the reason.
        pw_, ph_ = f(30), f(24)
        pcx_, pcy_ = f(48), f(10)
        g.append(
            f'<rect x="{pcx_ - pw_ / 2:.1f}" y="{pcy_ - ph_ / 2:.1f}" width="{pw_:.1f}" height="{ph_:.1f}" rx="2" fill="#A8895C" fill-opacity="0.65" stroke="#7A5F35" stroke-width="0.9" stroke-dasharray="3,2"/>'
        )
        # ... with the WORKED FLOOR sunk inside it. The first draft drew two curved dig-faces here
        # and the pair read as barrel staves at city grain - a dashed ring around a darker floor is
        # what says "hole" at every scale this engine draws.
        g.append(
            f'<rect x="{pcx_ - pw_ / 2 + f(5):.1f}" y="{pcy_ - ph_ / 2 + f(4):.1f}" width="{pw_ - f(10):.1f}" height="{ph_ - f(8):.1f}" rx="1.5" fill="#8A6E42" fill-opacity="0.85" stroke="#6B5330" stroke-width="0.8"/>'
        )
        # THE OPEN DRYING GROUND between the shed and the pit: green ware and unfired tile stand out
        # in the air for days before they will take a firing at all, so this ground is working stock,
        # not slack (it is also what the fire gap's open middle would otherwise read as).
        for gi_ in range(3):
            g.append(f'<rect x="{f(0) + gi_ * f(9):.1f}" y="{f(2):.1f}" width="{f(6):.1f}" height="{f(11):.1f}" rx="0.8" fill="none" stroke="#8A7350" stroke-width="0.8" opacity="0.85"/>')
        # THE COTTAGES, along the works' low edge, a clear fire gap off the kiln (kiln_keeps_fire_gap)
        n_ = max(1, min(3, cottages))
        hw2_, hh2_ = f(28), f(18)
        cxs_ = {1: (0.0,), 2: (-f(22), f(22)), 3: (-f(40), 0.0, f(40))}[n_]
        quarters = []
        for hx_ in cxs_:
            hy_ = f(46)
            g.append(f'<rect x="{hx_ - hw2_ / 2:.1f}" y="{hy_ - hh2_ / 2:.1f}" width="{hw2_:.1f}" height="{hh2_:.1f}" rx="1" fill="#D8C49A" stroke="#5A4326" stroke-width="1.5"/>')
            g.append(f'<line x1="{hx_ - hw2_ / 2 + 1.5:.1f}" y1="{hy_:.1f}" x2="{hx_ + hw2_ / 2 - 1.5:.1f}" y2="{hy_:.1f}" stroke="#5A4326" stroke-width="0.8" opacity="0.7"/>')  # the ridge
            qx_, qy_ = _world(hx_, hy_)
            # [x, y, w, h, ROT] - the rotation is the 5th element and is not optional decoration.
            # A cottage is drawn inside the works' rotated group, so a record without it describes a
            # box at the right place with the wrong ORIENTATION, and every consumer reads the wrong
            # footprint: kiln_keeps_fire_gap measured Tango's 69 ft gap as 62 ft, and
            # wells_among_dwellings tests the works' own well against a mis-oriented cottage. Latent
            # until 2026-07-27, when the maps started passing `rot` so the kiln climbs its slope -
            # every works before that was rot=0, where the bug is invisible. (Older records with
            # only four elements still read as rot=0, which is what they were.)
            quarters.append([round(qx_, 1), round(qy_, 1), round(hw2_, 1), round(hh2_, 1), round(rot, 1)])
        g.append('</g>')
        self.add(''.join(g))
        # THE WORKS' OWN WELL, between the shed and the cottages. Clay cannot be weathered, wedged
        # or thrown without water, so this is a premises fixture like the brewery's - and private
        # for the same reason, so it never counts toward the settlement's public idobata.
        wx_, wy_ = _world(f(2), f(24))
        self.well(wx_, wy_, private=True)
        # A ROTATED works must report its rotated half-height, or the caption anchors at the raw h/2
        # and lands inside the record's own bbox - labels_clear_of_other_buildings then reports
        # "'kiln works' over a kiln works". Same fix the rot=150 Hoshizora farrier needed; see
        # _trade_record's `lab_off` note. Live from 2026-07-27, when the maps started passing `rot`
        # so the kiln climbs its slope instead of pointing east on every sheet.
        self._trade_record("kilns", x, y, yw_, yh_, rot, label, lab_off=abs(yw_ / 2 * math.sin(th_)) + abs(yh_ / 2 * math.cos(th_)))
        bx_, by_ = _world(bcx_, bcy_)
        self.M["kilns"][-1]["body"] = [round(bx_, 1), round(by_, 1), round(bw_, 1), round(bh_, 1), round(rot, 1)]
        self.M["kilns"][-1]["quarters"] = quarters

    def charcoal_yard(self: Settlement, x: float, y: float, rot: float = 0.0, sheds: int = 2, label: str = "charcoal yard") -> None:  # type: ignore[misc]
        """A CHARCOAL WHOLESALER's yard (sumi-don'ya) - the fuel store of a charcoal district.

        `rot` lays the yard's ROAD SIDE against local -y, the same convention the tanning yard uses
        for its water side: a charcoal yard is a CART frontage, and every bale crosses one edge.

        Historical grounding (the "why" - see settlements/urban-features.md "CHARCOAL YARDS"):
          - CHINA FIRST. Charcoal was an industrial input at state scale: Song iron-smelting
            households were government-regulated with support that explicitly included charcoal
            supplies, and a large Ming ironworks is recorded with 200 charcoal producers alongside
            200 furnace-tenders and 300 miners. So a charcoal store is a SUPERVISED, TALLIED
            commodity depot, not a shop's back room - which is exactly the relationship the Mode A
            magistracy sheet draws ("charcoal and bar iron, sealed here, never owned").
          - JAPAN CORROBORATING. The ton'ya / toiya was the wholesaler-warehouseman of the Edo
            economy, and fire-resistant stores were built precisely because urban timber burned.
          - THE STOCK MUST STAY DRY, which is why it draws under ROOFED sheds: white charcoal
            commands its premium for an odorless, smokeless burn, and damp stock loses it.
          - THE STOCK SELF-HEATS, which is why the yard draws an OPEN COOLING APRON set apart from
            those sheds. Fresh charcoal absorbs oxygen fast enough to heat itself to ignition, worst
            of all as tightly-packed FINES; the documented handling rule is to stand new charcoal in
            the open, separate from cooled and conditioned stock, for at least 24 hours (8 days of
            air exposure clears it). A yard that put arriving loads straight in with the conditioned
            stock would burn down, so the apron is not decoration - it is the rule made visible.
          - THE WEIGHING FLOOR is here because the charcoal tawara had NO standard weight in the
            traditional system (unlike rice). A commodity with no standard bale cannot be traded by
            count; it must be weighed at the point of sale. That is also why the magistracy's hold on
            this trade is documentary - a seal on the tally is worth something only because the
            quantity is not self-evident from the load.

        Sizes are TRUE feet at the map's grain (no legibility inflation), pitched against the pool's
        other bulk-goods yards - the lumber yard's 90x60 and the dye yard's 80x52.

        Records M['charcoal_yards'] with `sheds` and the `apron` rect (charcoal_yard_keeps_fire_gap,
        settlement_has_charcoal_yard)."""
        yw_, yh_ = self.px(88), self.px(58)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(
            f'<rect x="{-yw_ / 2:.1f}" y="{-yh_ / 2:.1f}" width="{yw_:.1f}" height="{yh_:.1f}" rx="1.5" fill="#E0D2AC" fill-opacity="0.8" stroke="#B99F72" stroke-width="0.9"/>'
        )  # the yard's tamped cart ground - the same ground-plane convention the dye/tanning yards use, without which the furniture reads as stray marks at fit zoom
        # THE ROOFED STACKING SHEDS, on the far side from the road: open-sided, mat-roofed, the
        # conditioned stock stacked in tawara on a raised timber floor (off the damp ground)
        shw_, shh_ = self.px(34), self.px(18)
        for si_ in range(max(1, sheds)):
            sy_ = -self.px(14) + si_ * self.px(26)
            sx_ = self.px(14)
            g.append(f'<rect x="{sx_ - shw_ / 2:.1f}" y="{sy_ - shh_ / 2:.1f}" width="{shw_:.1f}" height="{shh_:.1f}" rx="1" fill="#C9A57A" stroke="#6B4F2A" stroke-width="1.6"/>')
            g.append(f'<line x1="{sx_ - shw_ / 2 + 2:.1f}" y1="{sy_:.1f}" x2="{sx_ + shw_ / 2 - 2:.1f}" y2="{sy_:.1f}" stroke="#6B4F2A" stroke-width="0.8" opacity="0.7"/>')  # the ridge
            for bi_ in range(4):  # the stacked tawara bales, charcoal-dark
                bx_ = sx_ - shw_ / 2 + self.px(5) + bi_ * self.px(8)
                g.append(f'<rect x="{bx_:.1f}" y="{sy_ - self.px(4):.1f}" width="{self.px(5):.1f}" height="{self.px(8):.1f}" rx="1.4" fill="#2E2A26" opacity="0.9"/>')
        # THE COOLING APRON - open ground, deliberately SET APART from the covered sheds, where a
        # newly-arrived load stands until it has stopped taking up oxygen (the 24-hour rule above).
        # Dashed, because it is open working ground and not a roofed room.
        aw_, ah_ = self.px(30), self.px(20)
        acx_, acy_ = -self.px(26), self.px(12)
        g.append(
            f'<rect x="{acx_ - aw_ / 2:.1f}" y="{acy_ - ah_ / 2:.1f}" width="{aw_:.1f}" height="{ah_:.1f}" rx="1.5" fill="#D2C49E" fill-opacity="0.6" stroke="#A98E54" stroke-width="0.9" stroke-dasharray="3,2"/>'
        )
        for ci_ in range(3):  # new loads standing apart, not yet under cover
            g.append(
                f'<rect x="{acx_ - aw_ / 2 + self.px(4) + ci_ * self.px(8):.1f}" y="{acy_ - self.px(3):.1f}" width="{self.px(5):.1f}" height="{self.px(6):.1f}" rx="1.2" fill="#2E2A26" opacity="0.75"/>'
            )
        # THE WEIGHING FLOOR on the road edge, with its beam scale - the bale has no standard
        # weight, so nothing leaves this yard until it has been weighed
        wfw_, wfh_ = self.px(16), self.px(14)
        wfx_, wfy_ = -self.px(26), -self.px(14)
        g.append(f'<rect x="{wfx_ - wfw_ / 2:.1f}" y="{wfy_ - wfh_ / 2:.1f}" width="{wfw_:.1f}" height="{wfh_:.1f}" rx="1" fill="#D8C49A" stroke="#6B4F2A" stroke-width="1.4"/>')
        g.append(f'<line x1="{wfx_:.1f}" y1="{wfy_ - self.px(5):.1f}" x2="{wfx_:.1f}" y2="{wfy_ + self.px(4):.1f}" stroke="#5A4326" stroke-width="1.2"/>')  # the scale post
        g.append(f'<line x1="{wfx_ - self.px(5):.1f}" y1="{wfy_ - self.px(4):.1f}" x2="{wfx_ + self.px(5):.1f}" y2="{wfy_ - self.px(4):.1f}" stroke="#5A4326" stroke-width="1.2"/>')  # its beam
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record("charcoal_yards", x, y, yw_, yh_, rot, label)
        self.M["charcoal_yards"][-1]["sheds"] = max(1, sheds)
        self.M["charcoal_yards"][-1]["apron"] = [round(acx_, 1), round(acy_, 1), round(aw_, 1), round(ah_, 1)]

    def refining_forge(self: Settlement, x: float, y: float, rot: float = 0.0, label: str = "refining forge") -> None:  # type: ignore[misc]
        """A REFINING FORGE - an okaji 大鍛冶, where pig iron smelted out at the fuel is worked into
        wrought bar. `rot` lays the OPEN WORKING FRONT toward local +y.

        Historical grounding (the "why" - see settlements/urban-features.md "REFINING FORGES"):
          - CHINA FIRST. Ming ironworks converted blast-furnace pig to wrought iron by FINING,
            Chinese chao 炒, "stir-frying": an OPEN fire under a forced blast, fuelled with charcoal,
            into which wood, charcoal and broken cast iron were charged and then stirred with an iron
            rod once semi-molten. Song Yingxing describes a rectangular hearth with the workers
            standing on a wall above it, stirring with willow poles. The practice runs back to the
            Eastern Han (the smelting-and-fining site at Xuxiebian in Sichuan).
          - JAPAN CORROBORATING. The tatara's chief product was pig iron (zuku), and the 17th century
            answered it with a TWO-STAGE refining process, the okaji: kera went first to the doba to
            be crushed and sorted, then the low-carbon fractions to the okajiba, which turned out
            flat bars called wari-tetsu 割鉄. At their peak the Chugoku ironworks made 80% of Japan's
            iron this way.
          - THE ONE DISCLOSED DIVERGENCE. The CHINESE arrangement sets the fining hearth a few feet
            from the blast-furnace outlet so the iron runs in still molten - one site. Rokugan's
            charcoal counties cannot: a kiln reduces roughly six parts wood to one of charcoal, so
            the kiln goes to the wood and the furnace follows the fuel into the hills, miles from the
            seat. So this follows the JAPANESE two-site pattern - cold pig comes down and is
            re-melted here. The reason is economic, not aesthetic: the Chinese single site works
            precisely where ore, fuel and hundreds of workers can be concentrated, and DISPERSED FUEL
            FORCES TWO SITES. The smelting furnaces are never drawn; they are off in the hills.

        Drawn as the OPEN-SIDED shed over TWO hearths (the two-stage refining) with the blast between
        them, its own charcoal store, the quench trough, stacked bar iron, and the slag heap - the
        waste and the product together are what tell a reader this is a refinery and not a smithy.

        Records M['refining_forges'] with `hearths` (refining_forge_stands_off_dwellings,
        refining_forge_downwind, settlement_has_refining_forge)."""
        yw_, yh_ = self.px(74), self.px(48)
        shw_, shh_ = self.px(44), self.px(26)
        scx_, scy_ = -self.px(6), -self.px(10)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(
            f'<rect x="{-yw_ / 2:.1f}" y="{-yh_ / 2:.1f}" width="{yw_:.1f}" height="{yh_:.1f}" rx="1.5" fill="#DCCBA6" fill-opacity="0.7" stroke="#B99F72" stroke-width="0.9"/>'
        )  # the working ground
        g.append(f'<rect x="{scx_ - shw_ / 2:.1f}" y="{scy_ - shh_ / 2:.1f}" width="{shw_:.1f}" height="{shh_:.1f}" rx="1" fill="#C2A87C" stroke="none"/>')
        # THREE walls and an OPEN front: a fining hearth is an open fire and has to vent, and the
        # stock is worked from the front - so the working edge draws as an eaves line, never a wall
        g.append(
            f'<path d="M {scx_ - shw_ / 2:.1f} {scy_ + shh_ / 2:.1f} L {scx_ - shw_ / 2:.1f} {scy_ - shh_ / 2:.1f} '
            f'L {scx_ + shw_ / 2:.1f} {scy_ - shh_ / 2:.1f} L {scx_ + shw_ / 2:.1f} {scy_ + shh_ / 2:.1f}" fill="none" stroke="#5A4326" stroke-width="1.7"/>'
        )
        g.append(f'<line x1="{scx_ - shw_ / 2:.1f}" y1="{scy_ + shh_ / 2:.1f}" x2="{scx_ + shw_ / 2:.1f}" y2="{scy_ + shh_ / 2:.1f}" stroke="#8A6B42" stroke-width="0.8" opacity="0.7"/>')
        # THE RIDGE. Without it the shed is a plain tan rectangle - a casing - and everything inside
        # it reads as components mounted on a panel. A ridge line down the roof is the one mark that
        # says "this is a BUILDING seen from above", and it costs nothing.
        g.append(f'<line x1="{scx_ - shw_ / 2 + 1:.1f}" y1="{scy_ - shh_ / 6:.1f}" x2="{scx_ + shw_ / 2 - 1:.1f}" y2="{scy_ - shh_ / 6:.1f}" stroke="#8A6B42" stroke-width="1.1" opacity="0.55"/>')
        # THE WORKING RANGE, ranked along the back wall: hearth - hearth - bellows, in ONE row and
        # deliberately LEFT-WEIGHTED. The first draft set the two hearths symmetrically about the
        # center with the bellows below them and the fuel store beneath that, which rendered as a
        # FACE - two red eyes, a nose and a mouth - the same pareidolia that got the tethered-oxen
        # glyphs retired (GM 2026-07-25). A working range reads as a range only if it is a row and
        # the row is off-center, so nothing on this glyph is mirrored about its axis.
        # ONE hearth lit, ONE banked - they must not read as a matched PAIR (settlement-review round 2
        # judged the first anti-pareidolia pass only partial: the layout was no longer mirrored, but two
        # identical saturated marks side by side still read as eyes). Two hearths of a two-stage process
        # are genuinely at different heats at any moment, so the honest drawing is also the safe one.
        for hi_, hx_ in enumerate((-self.px(15), -self.px(2))):  # the TWO hearths - the two-stage refining
            g.append(f'<rect x="{scx_ + hx_ - self.px(5):.1f}" y="{scy_ - self.px(7):.1f}" width="{self.px(10):.1f}" height="{self.px(7):.1f}" rx="0.8" fill="#3E3226"/>')
            # the fire reads as a BAR banked at the hearth mouth, not a filled block centered in it
            if hi_ == 0:
                g.append(f'<rect x="{scx_ + hx_ - self.px(3.6):.1f}" y="{scy_ - self.px(2.4):.1f}" width="{self.px(7.2):.1f}" height="{self.px(1.6):.1f}" fill="#A8472E" opacity="0.85"/>')
            else:
                g.append(
                    f'<rect x="{scx_ + hx_ - self.px(3.0):.1f}" y="{scy_ - self.px(2.2):.1f}" width="{self.px(6.0):.1f}" height="{self.px(1.3):.1f}" fill="#6B6055" opacity="0.8"/>'
                )  # banked: raked ash, no flame
            g.append(
                f'<rect x="{scx_ + hx_ - self.px(1.4):.1f}" y="{scy_ - shh_ / 2 - self.px(2.6):.1f}" width="{self.px(2.8):.1f}" height="{self.px(2.8):.1f}" fill="#5A4326"/>'
            )  # its smoke hood, breaking the back roofline
        g.append(
            f'<rect x="{scx_ + self.px(8):.1f}" y="{scy_ - self.px(6.5):.1f}" width="{self.px(9):.1f}" height="{self.px(6):.1f}" rx="0.8" fill="#8A6B42" stroke="#5A4326" stroke-width="0.7"/>'
        )  # the blast - one bellows at the end of the range, serving both hearths
        g.append(f'<rect x="{scx_ - self.px(9):.1f}" y="{scy_ + self.px(4):.1f}" width="{self.px(5):.1f}" height="{self.px(3):.1f}" fill="#3E3226"/>')  # the anvil block on the working floor
        csw_, csh_ = self.px(24), self.px(16)  # THE CHARCOAL STORE: the fuel is the input this works consumes most of
        csx_, csy_ = self.px(20), self.px(13)
        g.append(f'<rect x="{csx_ - csw_ / 2:.1f}" y="{csy_ - csh_ / 2:.1f}" width="{csw_:.1f}" height="{csh_:.1f}" rx="1" fill="#C2B190" stroke="#6B5A3A" stroke-width="1.4"/>')
        # ONE charcoal bay with a single division, not three tabs. Three evenly-spaced dark chips
        # inside a light casing is the visual grammar of a CONTROL PANEL, and that is how the whole
        # glyph was reading at fit zoom (settlement-review: "a small machine"). A fuel store is one
        # heap under one roof; the division says it is filled from one end and drawn from the other.
        g.append(f'<rect x="{csx_ - csw_ / 2 + self.px(3):.1f}" y="{csy_ - self.px(3):.1f}" width="{csw_ - self.px(6):.1f}" height="{self.px(6):.1f}" rx="1.2" fill="#2E2A26" opacity="0.8"/>')
        g.append(f'<line x1="{csx_ + self.px(2):.1f}" y1="{csy_ - self.px(3):.1f}" x2="{csx_ + self.px(2):.1f}" y2="{csy_ + self.px(3):.1f}" stroke="#C2B190" stroke-width="1.1" opacity="0.9"/>')
        g.append(
            f'<rect x="{-self.px(14):.1f}" y="{self.px(13):.1f}" width="{self.px(10):.1f}" height="{self.px(5):.1f}" rx="1" fill="#9AA5A0" stroke="#66706B" stroke-width="0.7"/>'
        )  # the quench trough - a DESATURATED slate-green. It was the only saturated blue on the
        # whole sheet, which made a 10ft trough pull the eye like an indicator lamp on a machine;
        # water reads from the trough's SHAPE and its place by the anvil, not from being blue.
        for li_ in range(4):  # the stacked wari-tetsu - the flat bars this forge exists to make
            g.append(
                f'<line x1="{-self.px(32):.1f}" y1="{self.px(10) + li_ * self.px(2.2):.1f}" x2="{-self.px(19):.1f}" y2="{self.px(10) + li_ * self.px(2.2):.1f}" stroke="#5C5750" stroke-width="1.3"/>'
            )
        g.append(f'<ellipse cx="{self.px(2):.1f}" cy="{self.px(18):.1f}" rx="{self.px(9) / 2:.1f}" ry="{self.px(6) / 2:.1f}" fill="#4A453E" opacity="0.85"/>')  # the slag heap
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record("refining_forges", x, y, yw_, yh_, rot, label)
        self.M["refining_forges"][-1]["hearths"] = 2

    def border_line(self: Settlement, pts: Sequence[tuple[float, float]], label: str = "", label_xy: tuple[float, float] | None = None) -> None:  # type: ignore[misc]
        """A drawn CLAN / jurisdictional BORDER - a line of law, not a physical object.

        Historical grounding: linear, demarcated borders were not foreign to early modern Japan -
        domains were already building a territorial order with agreed boundaries and mutual
        exclusion, evidenced by boundary disputes, boundary markers and map-making. The worked
        example is the Nanbu-Date border mounds, ~130 km of earth mounds dividing Morioka from
        Sendai, re-confirmed by the shogunate in 1642. And the shogunate ordered every province to
        draw its boundaries on a kuniezu 国絵図 - so putting the line on a map is itself the
        authentic act, which is what this method does.

        The PHYSICAL period marker was a MOUND, and a mound is a structure that would then have to be
        kept clear of everything - which is the opposite of the arrangement a frontier magistracy
        wants (the Mode A ubame-magistracy sheet stands its east wall ON the line, with the border
        running across a parley room's floor). So the line is drawn as a LINE and classified in
        _OVERLAP_EXEMPT: it reserves nothing, blocks nothing, and is overlapped by design.

        Records M['borders'] with `poly` + `label` and deliberately NO w/h."""
        poly = [[round(px_, 1), round(py_, 1)] for px_, py_ in pts]
        d = "M " + " L ".join(f"{px_:.1f} {py_:.1f}" for px_, py_ in pts)
        self.add(f'<path d="{d}" fill="none" stroke="#6B2A18" stroke-width="{max(self.lw(3), 2.6):.1f}" stroke-dasharray="14,7,4,7" opacity="0.85"/>')
        if label:
            lx_, ly_ = label_xy if label_xy else (pts[len(pts) // 2][0], pts[len(pts) // 2][1] - 14)
            # Drawn through self.label(), NOT as raw <text>. A caption emitted straight into the SVG
            # is invisible to the label-collision checks - it is not in the registry, so nothing can
            # test it - and the first draft's border caption duly shipped sitting on a wellhead with
            # a green gate. A caption that is not registered cannot be checked, which looks exactly
            # like a caption that is fine (CLAUDE.md, "a check that never RUNS looks exactly like a
            # check that passes"). self.label() also puts it in the top layer, so no ground feature
            # paints over it.
            self.label(lx_, ly_, label, 12, italic=True, color="#6B2A18")
        self.M.setdefault("borders", []).append({"poly": poly, "label": label})

    def _intake_reach(self: Settlement, x: float, y: float, rot: float, edge: float) -> float | None:  # type: ignore[misc]
        """Distance in PX from a works' water-edge midpoint, straight out along its own outward
        normal (local -y at `rot`, `edge` px from the center), to the first DRAWN watercourse
        CENTERLINE the ray crosses - or None if it crosses none.

        Two deliberate choices, both of which a future reader will otherwise want to "fix":

        - **Measured against DRAWN geometry** (`drawn_channels` pts, `streams` poly), never the
          recorded topology polylines the checks read. This decides where INK goes, and the two
          diverge wherever a mouth was snapped onto open water (see `channel`'s docstring) - a cut
          drawn to a recorded centerline can stop short of the stroke the reader actually sees.
          On Hoshizora the recorded and drawn answers differ by 16 px, which is the whole defect.
        - **To the CENTERLINE, not the near bank.** A mouth that reaches the middle of the stroke
          merges into it the way a confluence does; one stopped at the computed edge butts against
          it and still reads as a separate object, because the bank has a stroke of its own and
          the widths taper (`w0`/`w1`) along the course.

        Ray-vs-segment, exact: no marching, so the answer does not depend on a step size."""
        ca, sa = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        px_, py_ = x + edge * sa, y - edge * ca  # local (0, -edge) in world coords
        dx_, dy_ = sa, -ca  # local (0, -1): straight out of the water side
        best: float | None = None
        for pts in [d["pts"] for d in self.M.get("drawn_channels") or []] + [d["poly"] for d in self.M.get("streams") or [] if d.get("poly")]:
            for i in range(len(pts) - 1):
                ax_, ay_ = pts[i][0], pts[i][1]
                ex_, ey_ = pts[i + 1][0] - ax_, pts[i + 1][1] - ay_
                den = dx_ * ey_ - dy_ * ex_
                if abs(den) < 1e-12:
                    continue  # the ray runs parallel to this reach and never crosses it
                t = ((ax_ - px_) * ey_ - (ay_ - py_) * ex_) / den
                s = ((py_ - ay_) * dx_ - (px_ - ax_) * dy_) / den  # = ((P-A) x D) / (E x D); E x D is -den, hence the flipped numerator
                if t > 0 and 0.0 <= s <= 1.0 and (best is None or t < best):
                    best = t  # ahead of the yard (t > 0) and within this segment's span, not its infinite line
        return best

    def tanning_yard(self: Settlement, x: float, y: float, rot: float = 0.0, pits: int = 4, water: str = "stream", label: str = "tanning yard", lab_off: float | None = None) -> None:  # type: ignore[misc]
        """A TANNING YARD - the burakumin trade, and the one that decides where their quarter sits.

        The GROUND, not the building, is the feature: soaking pits, drying racks, and a small work
        shed on marginal land at the settlement's edge, ON water. The `rot` should lay the yard's
        WATER SIDE (local -y, where the pits and the intake sit) against the bank - which means
        `rot` is the BANK'S OWN BEARING there, not a right angle off the map: a stream running at
        30 deg takes a yard at 30 deg. The pit rank and the staking frames share one edge of water,
        so a yard left square to the map on a slanted bank puts one corner in the stream and
        strands the far end of the rank inland. `tanning_yard_square_to_its_water` holds this to
        within 15 deg of any course whose bank lies inside the ~20 ft on-water reach.

        Historical grounding (the "why" - see settlements.md "TANNING YARDS"):
          - Hides come from FALLEN DRAFT STOCK, not butchery: the kawata held carcass rights over a
            defined territory (danna-ba), so a county town's burakumin work the whole county's dead
            oxen and horses. l7r.md agrees - daimyo push surplus horses onto farms as draft animals,
            and they are "often slaughtered and eaten" when the fodder runs short.
          - So THROUGHPUT IS SMALL and scales with the territory served, which is what `pits`
            encodes: a county of ~6,800 inhabitants sheds on the order of a couple dozen carcasses a
            year (~4 pits), a provincial city adds the daimyo's stable and the armor/saddle/drum/
            bellows demand of ~300 samurai (~12). This is a seasonal yard, never an industry.
          - WATER IS THE REAL GATE, not settlement size. Tanning is a water process - the Japanese
            shironameshi method stakes raw hides in the river for 1-2 weeks before de-hairing - and
            every archaeologically-known tannery sits on a watercourse at the settlement's edge.
            The caste's own name for itself was kawaramono, "riverbed people". A settlement with no
            running water keeps no tannery whatever its size.
          - Pit size is the excavated medieval figure: ~1.4 m (4.6 ft) across, ~0.4 m deep.

        `water="stream"` draws staking frames out in the shallows (live water, the shironameshi
        picture); `water="ditch"` draws a gated intake cut instead, for a yard that sits on an
        irrigation drain and must pond its own water. Records M['tanning_yards']."""
        rows = 1 if pits <= 5 else 2
        per_row = math.ceil(pits / rows)
        yw_, yh_ = self.px(14 + 11 * per_row), self.px(rows * 9 + 32)
        pw_, ph_ = self.px(9), self.px(5)
        g = [f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})">']
        g.append(
            f'<rect x="{-yw_ / 2:.1f}" y="{-yh_ / 2:.1f}" width="{yw_:.1f}" height="{yh_:.1f}" rx="1.5" fill="#D9CBA2" fill-opacity="0.9" stroke="#A98E54" stroke-width="1.0"/>'
        )  # the yard's tamped, sodden working ground - a shade dirtier than the dye yard's (same convention: without a ground plane the pits read as stray marks at fit zoom)
        drawn = 0
        for r_ in range(rows):  # the SOAKING / LIME PITS, ranked along the water side
            ry_ = -yh_ / 2 + self.px(4) + r_ * self.px(9)
            for c_ in range(per_row):
                if drawn >= pits:
                    break
                drawn += 1
                g.append(
                    f'<rect x="{-yw_ / 2 + self.px(7) + c_ * self.px(11) - pw_ / 2:.1f}" y="{ry_:.1f}" width="{pw_:.1f}" height="{ph_:.1f}" rx="0.6" fill="#8E8A6A" stroke="#544D33" stroke-width="0.8"/>'
                )
        rky_ = yh_ / 2 - self.px(14)  # the DRYING RACKS - hides pegged out to cure for 2-4 months
        for ri_ in range(2):
            ly_ = rky_ + ri_ * self.px(7)
            g.append(f'<line x1="{-yw_ / 2 + self.px(4):.1f}" y1="{ly_:.1f}" x2="{yw_ / 2 - self.px(20):.1f}" y2="{ly_:.1f}" stroke="#7A5A30" stroke-width="1.1"/>')
            # hides hung over the rail: one fewer than the pit columns, which is exactly how many
            # clear the shed's corner - the rail stops at yw_/2 - px(20), so hide i sits at
            # px(8) + 11i and the last one that fits is i = per_row - 2 (derived, not guarded).
            for hi_ in range(max(0, per_row - 1)):
                hx_ = -yw_ / 2 + self.px(8) + hi_ * self.px(11)
                g.append(f'<rect x="{hx_:.1f}" y="{ly_ - self.px(2.4):.1f}" width="{self.px(7):.1f}" height="{self.px(4.6):.1f}" rx="1" fill="#D8C9A6" stroke="#9A8358" stroke-width="0.6"/>')
        shw_, shh_ = self.px(14), self.px(10)  # the work shed - knives, salt, and the rapeseed oil for kneading
        g.append(
            f'<rect x="{yw_ / 2 - shw_ - self.px(3):.1f}" y="{yh_ / 2 - shh_ - self.px(3):.1f}" width="{shw_:.1f}" height="{shh_:.1f}" rx="1.5" fill="#C2B190" stroke="#6B5A3A" stroke-width="1.4"/>'
        )
        if water == "ditch":
            # a GATED INTAKE cut: a yard on an irrigation drain cannot stake hides in a current, so
            # it ponds its own water - the cut runs off the yard's water side to the ditch bank.
            # ITS LENGTH IS DERIVED, not fixed (settlement-review 2026-08-08). It was a flat px(11),
            # which reaches only while the yard happens to abut its bank and stops SHORT the moment
            # it does not: Hoshizora's yard, re-seated 15 ft off the drain so its ground could stay
            # clear of the water AND of the paddy, left the cut 4 ft of bare ground short of the
            # stroke, reading as a blue tab pinned to the yard rather than as a cut feeding it. The
            # gate never saw it - nothing checks that a cut ARRIVES, only that the yard is on water.
            cut_ = self._intake_reach(x, y, rot, yh_ / 2)
            cut_ = self.px(11) if cut_ is None or not (self.px(6) <= cut_ <= self.px(40)) else cut_
            cw_ = self.px(5)
            g.append(f'<rect x="{-cw_ / 2:.1f}" y="{-yh_ / 2 - cut_:.1f}" width="{cw_:.1f}" height="{cut_:.1f}" fill="#9CB4C8" stroke="#5C7488" stroke-width="0.7"/>')
            g.append(f'<line x1="{-cw_:.1f}" y1="{-yh_ / 2 - self.px(4):.1f}" x2="{cw_:.1f}" y2="{-yh_ / 2 - self.px(4):.1f}" stroke="#4A3318" stroke-width="1.4"/>')  # the sluice gate
        else:
            # STAKING FRAMES out in the shallows - raw hides pegged into the current to soften and
            # to let the water start the hair (the shironameshi soak: 1 week summer, 2 winter).
            for si_ in range(3):
                sx_ = -yw_ / 2 + self.px(10) + si_ * self.px(13)
                g.append(f'<line x1="{sx_:.1f}" y1="{-yh_ / 2 - self.px(9):.1f}" x2="{sx_:.1f}" y2="{-yh_ / 2 - self.px(2):.1f}" stroke="#6B4F2A" stroke-width="1.2"/>')
            g.append(
                f'<line x1="{-yw_ / 2 + self.px(8):.1f}" y1="{-yh_ / 2 - self.px(7):.1f}" x2="{-yw_ / 2 + self.px(38):.1f}" y2="{-yh_ / 2 - self.px(7):.1f}" stroke="#6B4F2A" stroke-width="1.0"/>'
            )
        g.append('</g>')
        self.add(''.join(g))
        self._trade_record(
            "tanning_yards", x, y, yw_, yh_, rot, label, lab_off=lab_off
        )  # lab_off: a ROTATED yard's drawn extent exceeds h/2, so its caption lands inside its own boundary stroke and renders struck through (settlement-review round 2). Opt-in per map rather than global - see _trade_record
