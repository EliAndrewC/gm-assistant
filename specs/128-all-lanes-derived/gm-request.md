# The GM's request, verbatim

**This file exists so the `spec-fidelity` reviewer grades `spec.md` against the GM's OWN WORDS**
(constitution XVI). Written before the spec, and never edited. Transcription of speech, so the
punctuation is as dictated.

---

## The original question, which feature 126 was supposed to answer (2026-08-23)

> "So here is a question about the ordering of things on the maps. We are currently putting the lanes
> on the map before we put the houses. But is that realistic? ... in real life, lanes are things that
> are trodden as villagers walk around them. But doesn't it make more sense to put the houses there
> first ... I have a suspicion that the real issue is with the ordering of things being placed"

## Reading the walk-through page afterwards, and finding it had not happened (2026-08-24)

> "But plate four still has lanes. We are constructing a settlement from scratch, and you are still
> putting lanes down before the farmhouses. Is that correct? I just want to make sure that I
> understand because we explicitly made a feature that was entirely about putting lanes down after
> the farmhouses were placed because the lanes being there was the thing that was making it difficult
> to lay out the farmhouses. And then I just want to make sure that I understand that what happened
> is that the lanes are still being put there first."

## Authorizing this feature (2026-08-24)

> "Thanks, yes please proceed with feature 128, from start to finish. It'll be a good test of our new
> system."

## The standing scope limit, which this feature does NOT change

> "keep in mind that the scope for all of our changes right now is only a working reference hamlet
> with a single seed. and that is enough for us to push back to Maine. And we should not attempt more
> than that."

---

## What the record already establishes, and the reviewer should hold the spec to

These are NOT the GM's words; they are findings the GM has already been shown and has not disputed.
They are here so the reviewer can tell the difference between a requirement traceable to the request
and one the author invented.

- Feature 126's `spec.md` FR-003 says the connector to the off-map road AND the spur to the field
  MUST still be laid before the houses. **The GM never asked for that exception**; it was written by
  the implementing session on a provenance argument.
- Both of those ways register a no-build corridor (`s.lane(..., clearance=...)`, refused by `_fits`
  at `settlement/houses.py:309`), so both still constrain farmhouse placement - which the GM names
  as the whole problem: *"the lanes being there was the thing that was making it difficult to lay out
  the farmhouses."*
- The provenance argument holds for the connector and does not hold for the spur: a road to the
  county town can predate a hamlet, but the path from a hamlet to its own paddy cannot exist before
  the hamlet does, and it is trodden by the same households who tread the internal lanes.
- Feature 126's task T009 - re-origin the connector from the seat band rather than the skeleton's
  gateway - was planned and never done. `stage_ways` still calls `skeleton_layout` only to locate the
  connector's start, so the connector's origin is derived from the PREDICTED seat band rather than
  from the placed houses.
