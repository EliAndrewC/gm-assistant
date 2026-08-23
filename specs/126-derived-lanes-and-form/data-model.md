# Data model: derived lanes, and settlement form

**Feature**: 126-derived-lanes-and-form

This tier has no database. The "entities" are the fields a map's manifest carries and the structures
the pipeline passes between stages, which is what a downstream check or reviewer can actually read.

## Manifest metadata (`M["meta"]`)

| field | values | written by | read by |
|---|---|---|---|
| `settlement_form` | `nucleated` \| `dispersed` \| `linear` | `stage_water_frame` (rolled from the seed) | seating, lane derivation, grove choice, gate segments 0607/0610 |
| `settlement_form_asked` | same domain | `stage_water_frame` | diagnostics only |
| `settlement_form_substituted` | absent, or the form that was asked for | the stage that could not build the asked form | the gate, and any reviewer asking why a map is not the form it rolled |
| `nucleated` | bool | `stage_water_frame` | existing consumers - retained, derived from `settlement_form == "nucleated"` so the two cannot disagree |

**`settlement_form_asked` and `_substituted` exist because of the fallback rule.** A form that cannot
be built on a site is replaced by one that can, and a silent substitution would make the knob
untrustworthy - a reader would see a nucleated map, believe the roll produced nucleated, and never
learn the site refused the dispersed form. Recording both makes the substitution auditable and lets
the cohort report how often it happens, which is the number that tells us whether the roll weights
are honest.

## Way records (`M["lanes"][*]`)

Existing flags `connector` and `web` already partition the lanes. This feature adds the provenance
that those flags imply but never state:

| field | values | meaning |
|---|---|---|
| `provenance` | `exogenous` \| `endogenous` | Whether the way predates the settlement (the connector, the field spur) or was worn by it (the internal skeleton, the web). Satisfies FR-004. |

**Why an explicit field rather than inferring from `connector`/`web`**: the internal skeleton is
neither `connector` nor `web` today, so inference would need a rule that says "not connector and not
web means endogenous" - which is exactly the kind of derived-by-absence rule that breaks silently
when a fourth kind of lane arrives. The provenance is a DECISION this feature makes; it should be
recorded, not reconstructed.

## Seat band (`plan.seat`, in-memory)

Unchanged in shape, but its role changes from supporting-actor to load-bearing: with the internal
skeleton gone from the pre-house stage, the band is the ONLY organizing structure the houses have.
Keys consumed by seating: `cx`, `cy`, `along`, `out`, `lat`, `dep`, `anchor`.

Computed by `seat_cluster` in what is now `stage_track`. **It must stay before the houses** - that is
the constraint that decided the whole split (research R1).

## Shadow corridor (derived, not stored)

Not a manifest record - a predicate used during placement.

| input | source |
|---|---|
| roof ridge height | ~20 ft, from the *kayabuki* 45-degree pitch already documented at `BUNDLE_PITCH` |
| reference altitude | ~27 degrees, recovered from the existing 39 ft shadow (research R4) |
| bearing from house to yard | computed per candidate pair |

Yields the minimum separation for that bearing: full reach through the northern arc, footprint plus
working room east and west. Replaces a single scalar compared in all directions.

## State transitions

The only stateful sequence is the form fallback:

```
roll form  ->  attempt to build it
               |
               +-- succeeds  ->  settlement_form = asked
               |
               +-- refuses   ->  settlement_form = a buildable form
                                 settlement_form_asked = what was rolled
                                 settlement_form_substituted = what was rolled
```

A substitution is a normal outcome, not an error. It is recorded rather than logged-and-forgotten so
the cohort can report the rate.
