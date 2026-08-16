# Feature Specification: Review-Loop Efficiency (scatter audit + three process rules)

**Feature Branch**: `108-review-loop-efficiency` (no git branch - `SPECIFY_FEATURE` convention, this project stays on main)

**Created**: 2026-08-16

**Status**: Draft

**Input**: User description: "Review-loop efficiency: scatter audit script + three process-rule fixes from the 2026-08-16 cut-bank-fix profile" (full text in the conversation; GM-approved Amdahl items 1-4 from the transcript profile of the cut-bank bug fix).

## Context (why this exists)

A transcript profile of the 2026-08-16 cut-bank bug fix (14m33s prompt-to-verified-in-main) broke down as: 60% LLM turn latency, 28% idle waiting on background work, 12% tool execution. The critical path was diagnosis -> design -> implementation -> **the settlement-review DELTA agent** (350s, of which 84s ran past the already-green gate) -> wrap-up. The gate itself was never on the critical path. Four GM-approved efficiency items follow, in the same spirit as the earlier iteration-loop work: convert LLM-driven analysis to tool-based analysis, and encode ordering rules that keep the slowest independent work off the critical path.

The GM also raised a standing value question about DELTA reviews ("is it actually catching things?"). The record says yes - 2026-08-16: `_fill_wedges` nesting 12 fillers inside carved paddies (Inashiro); 2026-08-15: the bund-edge second pass (via Sawada's review) - so the goal of this feature is making DELTA reviews CHEAP, not dropping them, while keeping the catch-rate answerable with data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scatter audit as a script (Priority: P1)

A settlement-review agent (or a session) reviewing a ground-cover/scatter change runs ONE diagnostic script that parses every scatter base point out of a rendered pool SVG and adjudicates them against the engine's own keep-out geometry, instead of hand-building that parse across ~21 tool uses and ~350 seconds of agent time.

**Why this priority**: This is the direct conversion of the profiled bottleneck (the review agent is the critical-path tail) from LLM-driven analysis to tool-based analysis - the pattern that produced the project's previous ~10x win.

**Independent Test**: Run the script against the current Inashiro render (a map known clean) and against a fixture derived from the pre-fix render or a doctored SVG (known violations) - it must report zero violations on the former and name the violations on the latter, in seconds.

**Acceptance Scenarios**:

1. **Given** a pool map directory (json + svg) whose scatter honors all margins, **When** the auditor runs the script, **Then** it reports zero violations plus near-margin density statistics, in seconds rather than minutes.
2. **Given** an SVG containing scatter bases inside a channel's cut-bank margin or a crop margin, **When** the script runs, **Then** each violation is reported with its position and the keep-out that owns it.
3. **Given** a future change to the engine's margin rules, **When** the script runs, **Then** its verdicts move with the engine automatically because the keep-outs are obtained from the engine itself, never re-implemented (observe-don't-restate).
4. **Given** a settlement-review DELTA pass on a scatter/ground-cover change, **When** the reviewer follows the agent instructions, **Then** those instructions direct the reviewer to run this script themselves and draw their own conclusions (independence preserved; the author's claims are not evidence).

---

### User Story 2 - Review launches before the author's own verification pass (Priority: P2)

A session that finishes a Mode B map change launches the settlement-review agent the moment the motivating map's regen + gate is green - BEFORE its own visual verification pass - so the review (the slowest independent work) overlaps the session's remaining work instead of trailing it.

**Why this priority**: Zero-effort ordering change worth ~45-60s per reviewed change; the review is reliably the critical-path tail.

**Independent Test**: The doctrine text in the diagram dev-loop doc states the sharpened rule with the measured rationale; a future session following the doc launches the review before reading its own crops.

**Acceptance Scenarios**:

1. **Given** the diagram dev-loop doc, **When** a session reads the review-invocation section, **Then** it says to launch the review agent as soon as the motivating artifact is regenerated and gated green, before the session's own visual pass, with the 2026-08-16 measurement as the why.

---

### User Story 3 - Open decisions carry an implementation sketch (Priority: P3)

A session that records a deliberately-not-decided rule (an "open decision") also records a 2-3 line implementation sketch - the call site, the test to extend, the deliberate exclusions - so the follow-up session that receives the GM's decision executes instead of re-deriving.

**Why this priority**: The cut-bank fix spent its single largest LLM turn (75s) plus part of diagnosis re-deriving what the prior session already knew when it wrote "no bank-margin rule exists". Worth ~60-120s on every task that follows a recorded open decision.

**Independent Test**: The convention is stated in the diagram dev-loop doc, and the existing cut-bank open-decision entry in the vegetation research file is retro-fitted as the worked example (pointing at the resolution that followed).

**Acceptance Scenarios**:

1. **Given** the diagram dev-loop doc, **When** a session records an open decision, **Then** the documented convention requires the entry to name where the change would land, what check/test would hold it, and any deliberate exclusions.

---

### User Story 4 - No redundant pre-gate sweep, and the profile recorded (Priority: P4)

A session about to background the full gate runs only the whole affected test file first - it does not also run a separate foreground pool-regen sweep that the gate re-covers. The rule's wording must first be verified against how the gate actually obtains renders (the stop-work ritual's render-sync needs renders present in the clone); if the gate's cache path does not produce them, the rule must say exactly where the regen still belongs. The 2026-08-16 profile itself is recorded as a dated block in the iteration-loop evidence doc.

**Why this priority**: ~38s of tool time per engine change, but only reaches the task's end time once Stories 1-2 shrink the review tail; recording the profile is what keeps the next efficiency pass honest.

**Independent Test**: The iteration-loop doc carries the dated 2026-08-16 profile block (categories, gate-never-critical-path finding, ~12min projected floor) and the sharpened pre-gate rule whose render caveat matches verified gate behavior.

**Acceptance Scenarios**:

1. **Given** the iteration-loop evidence doc, **When** a reader looks for the 2026-08-16 profile, **Then** the dated block reports the category breakdown, the critical-path finding, and the projected floor.
2. **Given** the pre-gate rule as written, **When** its render claim is checked against the gate's actual cache behavior, **Then** the rule's caveat matches reality (verified during implementation, not assumed).

### Edge Cases

- An SVG whose scatter styling changes (colors, bucketing) would silently blind a parser keyed to today's styles: the script must fail loudly (report zero bases parsed as an ERROR, never as a clean pass) - a diagnostic that never runs must not look like a diagnostic that passes.
- A map with no channels/crops at all: zero keep-outs is a legal state; the script reports the base count and zero violations, not an error.
- Frozen legacy maps: their renders are committed exhibits that predate current rules; the script may be pointed at them but its report must not be read as a defect list to "fix" (the freeze doctrine); no special handling required beyond running on whatever it is given.
- The pre-gate rule must not contradict the existing "run the WHOLE affected test file before the gate" rule - it narrows what ELSE runs, it does not touch that.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide a scatter-audit diagnostic that, given a pool map's artifacts, extracts every ground-cover scatter base point (grass blades, brush dots, pine trunks) from the rendered SVG and reports (a) each base standing inside a keep-out, with position and owning keep-out, and (b) density statistics in distance bands just beyond the margins (so a sterile-halo judgment stays possible).
- **FR-002**: The scatter-audit MUST obtain its keep-out geometry from the engine's own code paths operating on the map's real manifest (observe-don't-restate); it MUST NOT re-implement margin rules, so future rule changes are picked up with no script change.
- **FR-003**: The scatter-audit MUST cover at minimum: drawn watercourses at drawn widths with the irrigation cut-bank margin, and paddy/dry-plot crop margins. Its report MUST state which keep-out families it checked, so an unchecked family is visible rather than silently omitted.
- **FR-004**: The scatter-audit MUST treat "zero bases parsed" as a loud failure, and MUST complete on the largest current pool map in seconds (tool-speed, not agent-speed).
- **FR-005**: The settlement-review agent instructions MUST direct DELTA reviews of scatter/ground-cover changes to run the scatter-audit themselves and interpret its output independently; they MUST also preserve the standing requirement that reviewers verify claims rather than accept them.
- **FR-006**: The settlement-review agent instructions (or its companion doctrine) MUST record the DELTA-review value evidence to date and require future notes entries to keep recording what each review pass caught, so the keep/drop question stays answerable with data.
- **FR-007**: The diagram dev-loop doc MUST state the sharpened review-launch rule: launch the review agent the moment the motivating map's regen + gate is green, before the session's own visual pass, with the measured 2026-08-16 rationale.
- **FR-008**: The diagram dev-loop doc MUST state the open-decision convention: an entry recording a deliberately-open rule also records a short implementation sketch (landing site, holding test, deliberate exclusions); the cut-bank case is cited as the worked example.
- **FR-009**: The iteration-loop evidence doc MUST gain a dated 2026-08-16 profile block (category breakdown, gate-not-critical-path finding, projected floor) and the sharpened pre-gate rule; the rule's claim about renders MUST be verified against actual gate/cache behavior before the wording lands.
- **FR-010**: The scatter-audit's pure logic MUST meet the project's coverage standard, with SVG/manifest parsing exercised through fixtures derived from a real pool map.

### Key Entities

- **Scatter base point**: the anchor position of one ground-cover glyph (grass blade base, brush dot center, pine trunk base) as drawn in a pool SVG; not recorded in the manifest, so the SVG is its only source.
- **Keep-out**: a region scatter bases must not occupy, owned by a rule family (watercourse + cut-bank margin, crop margin); derived from the manifest by the engine's own geometry code.
- **Audit report**: violations (position + owning keep-out) plus near-margin density bands plus the list of families checked and base counts parsed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The scriptable portion of a scatter DELTA review (parse + adjudication) completes in under 30 seconds on the largest current pool map, versus ~350 seconds of agent time measured on 2026-08-16.
- **SC-002**: A settlement-review DELTA pass on a scatter change, following the updated instructions, reaches its verdict with at most half the tool uses of the 2026-08-16 baseline (21).
- **SC-003**: The scatter-audit reproduces the 2026-08-16 review's ground truth: zero violations on the current Inashiro render, and it flags every seeded violation in the negative fixture.
- **SC-004**: All three process rules are discoverable in the docs a session actually loads (diagram dev-loop doc, iteration-loop doc), each carrying its dated measurement as the why.
- **SC-005**: A future task of the cut-bank fix's shape has a documented projected floor of roughly 12 minutes; the next profile taken after these rules land can be compared against it.

## Assumptions

- The scatter-audit lives with the other diagram diagnostics and follows their conventions (a standalone script beside `crop_map.py` / `why_placed.py` / `site_justice.py`, invoked with a pool map path).
- The SVG's scatter glyphs remain identifiable by their current stable styling (the bucketed grass groups and distinct fill colors); the loud-failure requirement (FR-004) is the guard if this drifts.
- Doc-only pieces (FR-006..FR-009) need no test gate per the docs-only rule; the script and its tests ride the normal `make done` gate.
- The urban-clearance halo and other scatter keep-out families beyond FR-003's minimum are desirable but optional extensions; the report's checked-families line (FR-003) keeps any omission visible.
- DELTA reviews continue to exist; nothing here retires them. The GM's value question is answered by keeping catch-rate data flowing (FR-006), not by this feature.
