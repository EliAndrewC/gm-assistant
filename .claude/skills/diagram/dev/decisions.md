# Recording decisions: what was actually decided, and what is still open

**Load this file when:** You are about to build on a property of the engine nobody decided, or you are leaving a decision open for a later session.

Split out of [`../CLAUDE.md`](../CLAUDE.md) so it is not in every diagram session's
context. The text is verbatim; the short always-on version of each rule stays in the index.

## A side effect is not a rule - check what was actually DECIDED before you build on it

The toe marsh spanned the canvas edge to edge for weeks, and three separate pieces of work treated
that as the settled shape of wet ground: a routing rule, four re-routed connectors, and a claim to
the GM that "a real valley floor has a dry footslope on at least one side" offered as though it were
research. The GM asked where both halves came from. Neither survived:

- **The width was never decided.** It arrived with the 2026-07 fix that made the toe a CONTOUR band
  so it would rotate with the fall - that fix was right and the rotation was its point; the extent
  came from the canvas corners because that was the easy way to write the polygon. The only stated
  rule was `marsh_on_low_ground` (the marsh is downhill of the field), and this file's own Akagahara
  note already recorded the opposite of wall-to-wall wetness: low ground beside the drain that sits
  at rice height is DRY, and "do not fix the gap".
- **The justification was invented.** The footslope claim was a plausible-sounding generalization
  with nothing behind it. Under the record-the-why rule that makes it not a finding at all.

The research the GM then asked for settled it in the opposite direction from the code, and the fix
is now in `research/water.md` ("The wet toe is as wide as the FAN"): an alluvial fan's spring line
follows the FAN's toe, and a floodplain's backswamp is bounded by its natural levees - wet ground is
FEATURE-bounded in both landforms. `toe_band` derives its width from the ground the fan waters.

**Two transferable rules.** First, when a feature's extent comes from the CANVAS, suspect it: a
canvas is not a fact about the world, and every other feature here is derived from something on the
map. This is `feedback_derive_dont_pin` one level up - not a pinned coordinate but a pinned FRAME.
Second, and more expensive: when you are about to build on a property of the engine, check whether
anyone decided it. Two of the four connector re-routes it caused were pure waste - restored to their
original routes the same day, once the width was right - and they were re-routes of the GM's own
maps, each with a review pass spent on it.

## An OPEN DECISION carries an implementation sketch, not just the question

When a session deliberately leaves a rule undecided ("no bank-margin rule exists; if the GM wants
one, that is its own rule with its own research entry"), the entry recording the open decision
MUST also record the 2-3 line implementation sketch the deciding session would execute: WHERE the
change lands (the call site), WHAT holds it (the check or test to extend), and the deliberate
exclusions. The open decision's author has all three in their head at zero marginal cost; the
follow-up session re-derives them at full cost. Measured 2026-08-16: the cut-bank follow-up spent
its single largest LLM turn (75s) plus part of its diagnosis re-deriving exactly what the
open-decision author knew - the commons scatter's `wat_b` grid was the landing site, the
drawn-channels margin test was the one to extend, streams/marsh were the exclusions.
`research/vegetation.md` "Scrub stays off open water" carries the retro-fitted worked example.
