# Feature 231: Work that was never paid

**Feature Branch**: none (main, in a session clone)

**Created**: 2026-10-26

**Status**: Draft

**Input**: `request.md` (the GM's words); research answer diagram#21 (questions 0311-0317)

## Why

The Money section prices a koku by what it buys and by the paid days it stands for. Neither sees the work a household
did for itself: cloth, food, fuel, straw goods, repairs, care. The GM asked for that work on the site: what the tasks
were, how long each took relative to the others, whether clothing out-ate farming for its maker, and how much of it a
city laborer did, single or with a family. He also asked that the page say plainly why so much of it is unknown:
women's household work was almost never written down.

## User Scenarios & Testing

### User Story 1 - The household's year, and where the time went (Priority: P1)

**Acceptance**:
1. A new page `/money/household`, listed as a third tool on `/money`, shows a farm household's year as a picture of
   where the days went: the one attested holding's figures (the Seiryoki: men's and women's field days a cho, and its
   counted man-days for fuel, animal care, house repair, ditches, silkworms, tools and mats), with the household cloth
   days beside them. The picture says what it is (one holding, mid-1600s, night work uncounted), not a general year.
2. Every figure carries its verdict (as the research gave it) and a link to its research question page.

### User Story 2 - The tasks, as near exhaustive as the sources allow (Priority: P1)

**Acceptance**:
1. A list of the household's tasks, grouped (cloth; food; fuel and water; straw; house and tools; care), each with who
   did it and its time where a figure exists. Every task the research names is listed, including those whose time is
   SILENT; a SILENT time reads "not recorded", never a blank or a guess presented as history.
2. The GM's clothing hypothesis is answered in both halves, by fiber: cotton-era Japan, the hemp and ramie era, and
   Jiangnan, each with its verdict, and the page says that only the cloth stage is counted, so cloth days are a
   minimum.

### User Story 3 - Homemade goods in days of work, beside their market price (Priority: P1)

**Acceptance**:
1. For each homemade good with an attested time (at least a tan of cotton cloth), the page shows the days of work it
   took and what the same thing cost at market (the ledger's price), and what those days were worth at the laborer's
   day wage. The arithmetic is shown.
2. A short note ties this to the two readings: goods dollars price the market good; the work behind a homemade one is
   a labor value, like wage dollars.

### User Story 4 - City households (Priority: P2)

**Acceptance**:
1. What a city household bought that a farm household made, with prices where attested (polished rice, cooked food,
   baths, used clothing, washing, water), each verdict shown.
2. The page answers the GM's question about a single tenement laborer against one with a family directly: the sources
   cannot tell them apart (SILENT), with what little is known.

### User Story 5 - Why so much is missing (Priority: P1)

**Acceptance**:
1. A section states explicitly that women's household work was almost never written down at the time, that this is
   why many figures on the page are missing, and that this gap is itself a fact about the past, with the historians'
   account (0316) and the sources historians use instead.
2. The landing page's "What the records leave out" links to it.

### User Story 6 - Can the sources count home work, class by class? (Priority: P2)

**Acceptance**:
1. A direct answer to the GM's main question, class by class, each with its verdict and research link:
   - **Farm household:** one holding is counted (the Seiryoki); no source splits the year by member (0312).
   - **City laborer, single or with a family:** the sources cannot tell them apart (User Story 4.2).
   - **Live-in servant, apprentice or clerk:** no household of their own to work for; leave home on the two yabuiri
     days; a side trade not recorded (0311).
   - **Porter, guard, footman:** what they did on days off is not recorded (0311).

### User Story 7 - The proverb's real halves (Priority: P3)

**Acceptance**:
1. Beside the Rokugani proverb's history: the 360-day form was not found; its halves are attested (早起三朝當一工,
   "three early mornings make a day's work", by 1213; the farming almanac of 1314), passing the kanji triangle. The
   Rokugani proverb stays captioned as Rokugani.

## Requirements

- **FR-001**: The page's figures live in one data file, each with its verdict and research source; the page renders
  from it. A test fails if a figure lacks either.
- **FR-002**: Research figures that are prices (baths, sushi, the Bunsei budgets) enter the ledger by the intake rule
  (`research.md`), with their labels.
- **FR-003**: Findings are recorded for estimates E0194-E0218 by `calibration.md` step 4 before the page is built.
- **FR-004**: The page uses the Money section's explainers (`_money_terms.html`) where a term needs one.
- **FR-005**: The page passes the DOM audit and the frontend review at GM, GM-200 and mobile.

## Edge Cases

- A comparative source (Mannering's wool, Buck's China of the 1920s) appears only labeled comparative, never as a
  Rokugani figure.
- A figure derived by the research project's arithmetic (the 512 hemp days) is shown as derived, with its inputs.
- Every figure comes from a research file verified on diagram's main (0311-0317, all there at aa9bbeb).

## Success Criteria

- **SC-001**: `/money/household` is live, linked from `/money`; every figure has a verdict and a source link; the gate
  passes.
- **SC-002**: The calibration report grades the household estimates that the research can grade.

## Review history

- 2026-10-26, spec-fidelity round 1: CHANGES REQUIRED. (1) The GM's "different classes" (clerks, guards, servants) had
  no story although 0311 answers it: User Story 6 added. (2) Showing the calibration line on the page was not asked:
  dropped from FR-003; the findings are still recorded.
