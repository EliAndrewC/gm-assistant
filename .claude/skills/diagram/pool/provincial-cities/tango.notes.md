# Design notes: Tango, the walled provincial city that changed hands

*Reconstructed 2026-08-08 from the generator's docstring and comments, which until then were the
only record of this map's intent. Everything below is sourced from `tango.gen.py`.*

**Subject**: a walled provincial seat of ~3,000, drawn at 1 px = 3 ft. Historical model: a Chinese
walled provincial seat / Japanese *jokamachi* - a closed moated rampart sized to **hug** the ~600-
household city (a wall encloses what it must defend; no large unused ground inside), the Imperial
road as the N-S spine, and a connected GRID of streets dividing each quarter into blocks. Within a
block, street-facing buildings front the streets and the bulk of the housing packs into tight rows
behind them.

**Why it exists, and how to read it**: Tango is **the exception; Nagahara is the norm**. It was drawn
early and is atypical in several ways, each of which now declares itself in `meta` rather than
passing unremarked. Per the dev-loop doctrine: lock the rules in against ORDINARY settlements first
and let this one earn its exceptions - for a long time the defaults were being bent to fit Tango and
Hirameki instead of the other way round.

## The density argument, recorded so it is not re-derived

The wall's semi-axes are 487x457 px (~1,461 x 1,371 ft): **~59 walled hectares for ~3,000 people =
~51/ha**, the LOW end of the real 100-250/ha walled-settlement band. That is Tango's canon - an
average provincial-city population with above-average in-wall space per capita **because of its
agricultural district**.

Two corrections got it there, both worth keeping on record:

1. The first 1 px = 3 ft pass kept the old 840x780 ring and produced a **~17/ha ghost town**; the ring
   was then sized to hug the city.
2. Feature 006 (per-quarter density + no extramural commoners) then revealed the hugged ring had been
   meeting 3,000 partly by **SPILLING ~12 dwellings past the wall**. The ring was enlarged a hair
   (a uniform x1.015 from 480x450) - **the GM's call: keep the round 3,000 and let the honest-inside
   figure meet it, rather than trim the declared population.**

## Quarters

| Quarter | Contents |
|---|---|
| NW | the **agricultural district** (unusual, tunable via `agricultural_district=True`) - in-wall fields fed by an in-wall pond, plus the city's **in-wall burakumin neighborhood** (siege need) |
| NE | the laborer neighborhoods - terrace bands behind the street frontage |
| SW | the merchant district + a temple neighborhood (Benten + Daikoku, the Crane patron fortunes) holding the Ministry of Rites that oversees them |
| SE | the provincial government (governor's mansion + five of the six ministries) and the samurai neighborhood, with a Temple of Bishamon among them |
| outside SE | wealthy samurai keep walled estates of varying size and commute in |

All six ministries appear. Civic amenities ported up from the town tier: merchant-house kura, a
market flophouse, a theater stage in the Benten precinct.

## Declared exceptions - each one is a `meta` declaration, not an accident

- **`temple_exception="changed_hands"`.** Tango carries THREE major temples, one past the two-patron
  default: the city changed hands between Lion and Crane, so it keeps the **union of the two patron
  pairs** (Bishamon + Daikoku + Benten, Daikoku shared), and its Lion-legacy Temple of Bishamon is a
  **converted samurai estate**. Feature 016 made this exception declare itself rather than pass
  unremarked.
- **The nuisance axes DIVERGE, by declared override (GM 2026-07-27).** Everywhere else the burakumin
  quarter, the execution ground and the tanning yard share one bearing out of the settlement, because
  kegare leaves a place one way. Tango does not: **the Emperor lies SOUTHEAST**, so Tango gives its
  southeast to the governor's yamen and the samurai - a cultural claim that outranks the pollution
  geography - and the outcast quarter is pushed northwest opposite it. The yard cannot follow the
  quarter northwest because `tanning_yard_below_every_intake` pins it below fse1's irrigation tap in
  the south. So the two end up facing apart. This is Tango's specific history overriding a general
  rule, and it carries a live waiver on `tanning_yard_on_the_outcast_side`.
- **`crop_outlier_ok=True` (GM 2026-07-25).** The tanning yard's caption alone holds the frame ~180 px
  open to the south, and `crop_not_held_open_by_one_feature` is right to flag it. It stays because a
  RULE forces the yard out there, and the shallowest legal seat saves 8 px of a 1,402 px image and is
  still flagged - so there is nothing to gain by nudging. **The declaration is the point**: the extra
  image is a deliberate, reasoned cost rather than silent bloat.

## Review log

- **2026-08-08 caption pass.** The Governor's Mansion caption dropped to 11 pt and moved inside the
  walled court - Tango had already been hand-seating it there, with a comment explaining that the
  manor default's reserved band above the walls "was eating a full housing row". That hand seat is
  gone; `governor_mansion()` does it for every city now.
- **2026-08-08 RNG re-roll** (positional/scoped randomness, engine-wide). Two captions landed on
  features: the burakumin quarter caption dropped 22 px off a wellhead, and the 'Temple of Benten'
  reservation band was widened. The band is worth understanding - it was already there and already
  sized past the caption, but `block_polys` is **CENTRE-tested**, so a merchant seated just outside it
  still reached in with a rotated corner.

## Negative fixtures frozen from this map

- `tanning_yard_on_the_outcast_side_fires_on_the_pre_waiver_tango.json` - the manifest as it stood
  BEFORE the waiver, so the check still has a map holding it honest.

## Known open

- **No `notes.md` existed for this map until 2026-08-08**, so anything settled between its authoring
  and that date lives only in gen comments and may not be recorded here. Treat gaps as unrecorded
  rather than as decided.
