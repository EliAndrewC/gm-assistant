# Feature 220: Estimate log and calibration for the money skill

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-18

**Status**: Draft

**Input**: `request.md` (the GM, 2026-10-18). Builds on feature 219 (`specs/219-money-skill/`).

## Why

The GM will often ask the price of something never priced before. The skill estimates it from its model (the anchors:
an unskilled day's wage, a koku of rice, woven cloth, worked metal) and answers at once; the research comes later. The
GM wants every such estimate logged, then compared with what the research shows, *"because that tells us how well
calibrated our model is"*: a constant miss in one direction adjusts the model; staying inside some error bars is a good
sign; guesses all over the place say the method is weak there (*"Markets are ultimately the thing that determine actual
prices, and we are creating a much more simplistic set of tools to attempt to approximate"* them).

## User Scenarios & Testing

### User Story 1 - Estimate, record, file (Priority: P1)

The GM asks *"what do we think ... a replacement katana handguard cost"*. The skill answers with an estimate derived
from its model (as in feature 219), **records the estimate in an append-only log** with what it rested on, and **files a
GitHub issue** on `EliAndrewC/diagram` asking for the research. Items asked together may share one issue.

**Independent Test**: one command records an estimate (item, the GM's question, range, unit, category, method, the
rows it used) and the model inputs in force (basket snapshot, koku mass, wage, laborer's year); the log gains a line
with a new id and today's date; the skill text says to file the issue and record its link.

**Acceptance Scenarios**:

1. **Given** an item never priced, **When** the GM asks, **Then** the answer gives the estimate and the estimate is
   logged with an id, the date, the GM's question, the range, the method and the model inputs.
2. **Given** a logged estimate, **When** the issue is filed, **Then** the link between the estimate and the issue is
   recorded.
3. **Given** a logged estimate, **When** anyone later edits or deletes it, **Then** the gate fails: the log of guesses is
   never rewritten after the fact.

### User Story 2 - Take in the research, keep both (Priority: P1)

The diagram session posts its findings. The skill records a **finding** against the estimate (the research-supported
range, the question file, the verdict) without touching the estimate, and updates the ledger's price as feature 219
already does. The guess and what the research showed stay side by side.

**Acceptance**: a finding names an existing estimate; a SILENT or NOT ATTESTED verdict is recorded too, and counts as
"no measurement" rather than as a hit or a miss.

### User Story 3 - How well calibrated is the model? (Priority: P1)

One command reports, overall and per category: how many estimates have a finding; the **bias** (do we guess high or
low, and by what factor); the **spread** (typical size of the miss, either direction); and the **hit rate** (how often
the research's figure fell inside our range). Each with its count, so a category with two findings is not over-read.

**Acceptance**: with sample estimates and findings, the report shows the right bias direction and factor, spread and
hit rate per category and overall.

### User Story 4 - Adjust the model (Priority: P2)

When a category shows a consistent bias or a wide spread over enough findings, the skill text says what to do: revise
that category's recipe or anchors (feature 219's `questions.md`), and record the adjustment with its date and the
calibration that prompted it. Estimates logged after the adjustment can then be compared with those before it.

**Acceptance**: the recipe adjustment procedure exists and names the evidence threshold it uses.

### Edge Cases

- **A finding gives a point, not a range**, or the estimate is a point: use the midpoint of each range.
- **The research disagrees with itself** (two periods, two places): the finding records the range the research
  supports; the comparison uses its midpoint, and notes keep the detail.
- **Units differ** (the research prices a bundle, the estimate one item): the finding converts to the estimate's unit
  and says how.
- **The model changes** (a new basket snapshot, the koku mass settled): estimates keep the model inputs they were made
  under, so calibration can be read before and after.
- **Comparative sources** (feature 219 FR-014) never serve as a finding: they cannot set a Rokugani price, so they cannot
  grade one.

## Requirements

### Functional Requirements

- **FR-001**: An append-only estimate log MUST record each estimate: id, date, item, the GM's question, low and high
  (sen), unit, category, method, the ledger rows it used, and the model inputs in force.
- **FR-002**: A command MUST record a new estimate and print its id.
- **FR-003**: The link between an estimate and its diagram issue MUST be recorded without editing the estimate.
- **FR-004**: The gate MUST fail if any committed estimate line is changed or removed.
- **FR-005**: Findings MUST be recorded separately (estimate id, date, low, high, unit note, source question file,
  verdict, notes) and MUST name an existing estimate; only ATTESTED or ATTESTED ONLY FOR findings count as measurements,
  and a finding may not rest on a comparative source.
- **FR-006**: A calibration command MUST report, overall and per category, the count, bias (geometric mean of
  estimate-midpoint / finding-midpoint), spread (median absolute log ratio, as a factor) and hit rate (finding midpoint
  inside the estimate range).
- **FR-007**: The skill text MUST make estimate -> record -> file -> take in -> grade the standard path for any price
  not already backed by research, and MUST give the model-adjustment procedure.
- **FR-008**: The first answers to the twelve campaign questions (feature 219, already filed as diagram#3 and #4) MUST
  be logged as the first estimates, since they were made before their research.

### Key Entities

- **Estimate**: one logged guess and what it rested on.
- **Request link**: estimate id -> diagram issue.
- **Finding**: what the research showed for one estimate.

## Success Criteria

- **SC-001**: Recording an estimate adds exactly one line; editing a committed line fails the gate.
- **SC-002**: The calibration report reproduces hand-computed bias, spread and hit rate on a fixture.
- **SC-003**: The twelve campaign questions' first answers are in the log, linked to diagram#3 and #4.

## Decisions Recorded

| Decision | Why | Recorded at |
|---|---|---|
| Three files (estimates, request links, findings), not one mutable record | the guess must never be rewritten; links and findings arrive later | plan.md |
| Bias as a geometric mean of ratios, spread as the median absolute log ratio | prices span sen to koku; a factor (1.5x high) reads the same at every scale, an arithmetic mean would be dominated by the dearest items | plan.md |
| Append-only enforced against git HEAD | catches any edit before it is committed, without a separate signature scheme | plan.md |
| One issue per ask; items asked together share one | the GM: "file a GitHub issue" each time; diagram batches its own write sessions | spec |

## Assumptions

- The diagram session answers in the format of feature 219's research protocol (question file, verdict per figure).
