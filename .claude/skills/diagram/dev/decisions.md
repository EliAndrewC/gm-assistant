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

## Do not put a question to the GM that your OWN DOCUMENTATION already answers

**GM 2026-08-24**: *"you should do things the way that our documentation says you should do them
unless there is a specific reason not to."*

Said while declining to rule on the paddy-tint question, because the code's own doctrine already
stated what the colour meant. A session had read its documentation, found it clear, and queued a
ruling anyway - which costs the GM a decision they had effectively already made and stalls the work
until they make it twice.

The check is one line before you write the question: **does something we have already written answer
this?** If it does, follow it and say in the commit that you did. A specific reason to depart is a
real thing and it happens - the documentation can be stale, or wrong, or written before a constraint
existed - but then the departure is the thing to raise, with the reason, not the original question.

This sits directly above the older rule below and is the same family: the rungs of the ladder are
OUR DOCS -> the historical record -> a knob -> and only then the GM.

## Do not put a question to the GM that history can answer - and two answers means a KNOB

**GM 2026-08-18**, after three questions were escalated as "rulings wanted" and two of them turned
out to be settled in the vernacular-architecture literature the moment anyone searched. Now
constitution Principle XII; this is the diagram-side operational form of it.

**The ladder, in order. Do not skip a rung.**

1. **Research it.** Real sources, China first and Japan as tiebreaker per the project's standing
   geography rule. Write the finding into [`../research/`](../research/) whether or not it changes
   code - that is the record-the-why rule, and it is what stops the next session paying for the same
   search.
2. **If the research is decisive, implement the answer.** No knob, no ruling. Write down that it was
   decisive, so a later reviewer who finds the adjacency surprising reads the finding instead of
   re-opening it.
3. **If two forms are supportable, add a KNOB.** This is not tie-breaking; it is the point of the
   generator. The GM's framing: settlements should be *"within historical norms while being as
   different from one another as is justifiable by our historical research, for the benefit of
   players who need to be able to look at different maps and distinguish them from one another at a
   glance."* Two attested forms are therefore a gift, not an obstacle - roll between them per
   settlement in `_knobs.py` and let the maps differ.
4. **Only if the record is genuinely silent does the GM rule** - and the ask must state what was
   searched, what was found, and why it is still unsettled.

**The distinction that decides rung 3 vs. calibrated liberty:** liberty covers a DEGREE along a
continuum - how many temples per city, how dense a cluster - where the sources give a band and we
pick within it. It does NOT cover a choice between two distinct FORMS (alleys off a spine vs. a back
lane; a byre in the yard vs. under the house's roof). A form choice made once and hardcoded makes
every map the same in a way the history does not require, which is the failure this rule exists to
prevent.

**The worked example** is the back-rank lane question, and it is worth reading because the research
came back decisive on one axis and two-formed on the other in the same pass: *access* is
non-negotiable ("every house in the nucleated village is accessible via the interconnected system of
narrow lanes and alleys"), while the *form* of that access is genuinely two-shaped - accretive
alleys off the spine, or a planned back lane behind the plots. So one axis became a requirement and
the other became a knob. Full record in
[`../research/homesteads.md`](../research/homesteads.md) and `future-work.md` section C.

A corollary worth stating separately, from the same day's ruling on the twin detector: **when a knob
and the geometry disagree, that is a placer bug, not an axis-selection question.** Keep reading the
declared knob, and fix the drawing to match what was rolled - switching the measurement hides the
disagreement instead of resolving it.

## WHEN A FORM IS A KNOB, CHECK THAT BOTH FORMS CAN ACTUALLY DO THE JOB

Feature 123 rolled a `lane_web` knob over two attested forms - `alleys` (laterals off a spine) and
`back_lane` (ways parallel to the field margin behind the plots) - and shipped a first version in
which one of them could not possibly work.

**Parallel lanes never meet.** That is arithmetic, not a bug to tune around, and it means the
back-lane form was disconnected BY CONSTRUCTION: an alley crosses the spine it branches from, a back
lane runs beside its neighbor forever. Three settlement-reviews independently reported the maps
rolling `back_lane` as two and three separate lane components while the `alleys` maps came out fine,
and the knob is exactly why the defect landed on some maps and not others.

The source had already said what was missing, in the same sentence the form was taken from: the
planned form is back lanes "which, **together with the main street itself, provides a rectangular
FRAMEWORK** for the development of the village". A framework is the parallels PLUS the ties. Only the
parallels were being drawn.

**Two transferable rules.**

- **A knob multiplies your test surface, and the halves are not symmetric.** Both values need the
  same functional property demonstrated - here, "the ways form one network" - and a green cohort
  proves it only for the values that happened to roll. Ask what each form makes STRUCTURALLY
  impossible before trusting the rate.
- **Re-read the source sentence the form came from, in full, when the form misbehaves.** The clause
  that fixed this was in the same quotation the feature was built on, and had been skimmed past as
  scene-setting. A form taken from a source usually arrives with its own constraints attached.
