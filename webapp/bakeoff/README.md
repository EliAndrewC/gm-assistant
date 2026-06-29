# Synthesis prompt bakeoff

A temporary, local-only harness for answering one question empirically: **how
much (and what kind of) setting context should the "Synthesize Backstory" prompt
carry?** It generates backstories for a fixed set of hard test characters across
four prompt tiers and two models, then lets you vote on them **blind** (you do
not see which tier or model produced which output) so your taste is measured, not
your expectations. Afterwards you unblind and tabulate.

Everything here is disposable. When the winning tier is chosen, delete the
`bakeoff/` directory and its entries in `pyproject.toml`.

## The active comparison: the clan-flavor dimension

The live question is how to handle clan identity without making the model
over-apply clan stereotypes. Both arms carry the GM's materialist "The Great
Clans" framing (sliced live from l7r.md); the comparison isolates whether the
per-clan summary helps on top of it. Defined in `briefs.py` (`config.TIERS`); run
`python3 -m bakeoff.briefs` for live sizes:

| Arm | ~tokens | Contents | Question |
|------|---------|----------|----------|
| `blurb` | ~3.7k | shipped brief + the "The Great Clans" framing from l7r.md | Is the framing alone enough? |
| `flavor` | ~6.3k | `blurb` + `flavor_clans.md` (the per-clan summary, rewritten in that materialist spirit) | Does per-clan flavor add value, or just invite stereotyping? |

The blurb and the t2/t3 sections slice exact text out of the canonical notes at
build time (via `extract_section`), so the GM's writing is never retyped or
allowed to drift.

### The earlier context-amount sweep (preserved)

Before the clan-flavor question, the bakeoff compared how *much* context to
carry. Those tiers (`config.CONTEXT_TIERS`) still build and can be re-run by
swapping them into `config.TIERS`:

| Tier | ~tokens | Contents | Question |
|------|---------|----------|----------|
| `t0` | ~3k | The shipped philosophy-only brief (`chargen/synthesis_brief.md`) | Can principles alone carry it? |
| `t1` | ~8k | t0 + clan/school flavor (`flavor_clans.md`) + few-shot GM-written NPC exemplars | Lean but textured |
| `t2` | ~39k | t1 + material/government/calendar/supernatural sections pulled verbatim from l7r.md | Does the full texture layer help? |
| `t3` | ~337k | The entire l7r.md + budgets.md | Does curation even matter? |

## Workflow

All commands run from `webapp/`.

1. **Preview the matrix and cost** (no API calls):
   ```
   python3 -m bakeoff.generate --dry-run
   ```

2. **Generate candidates.** Resumable - already-generated cells are skipped, so
   you can start small and fill in later.
   ```
   # cheap smoke run first:
   python3 -m bakeoff.generate --characters hideki,emi --samples 1
   # the full matrix (10 chars x 2 arms x 2 models x 3 samples = 120 calls):
   python3 -m bakeoff.generate
   ```

3. **Build the blind comparison tasks:**
   ```
   python3 -m bakeoff.build_tasks
   ```

4. **Vote, blind, in the browser:**
   ```
   python3 -m bakeoff.app
   ```
   Open the printed URL. Each screen shows one character's sheet and the active
   arms' outputs as shuffled A/B (A/B/C/D for the 4-tier sweep) cards; pick the
   one you would actually use, optionally add quick-tags and notes. Progress
   persists - restart and resume.
   (In a container, the app binds `0.0.0.0:8090`; publish that port or set
   `BAKEOFF_PORT`.)

5. **Unblind and tabulate** (reveals which tier is which - only run when ready):
   ```
   python3 -m bakeoff.analyze
   ```

## Files

| File | Role |
|------|------|
| `config.py` | Paths, the active arm list + preserved context-sweep tiers, model list, sample count |
| `briefs.py` | Tier/arm assembly + the heading-based section extractor |
| `flavor_clans.md` | Per-clan/family/school flavor, materialist framing (the `flavor` arm) |
| `characters.json` | The 10 hard test characters (each with a `stress` note) |
| `generate.py` | Resumable candidate generation across the matrix |
| `build_tasks.py` | Deterministic blind task builder |
| `app.py` + `templates/` | The local blind-eval webapp |
| `analyze.py` | Unblinding + tabulation |
| `data/` | Generated candidates, tasks, votes (gitignored) |

## Design notes

- **Blinding** is enforced server-side: the webapp template only ever receives
  the option label and text, never the tier or model.
- **Variance control:** three samples per cell; one task per sample round, so the
  rounds act as repeats that average out the large run-to-run swings.
- **Model dimension:** each task compares the active arms within a single
  (hidden) model; `analyze.py` reports arm wins both pooled and split by model.
  Direct model-vs-model screens are intentionally not built yet.
- **Hard characters:** the test set deliberately stresses trait contradictions,
  edge castes, rank/recognition mismatches, clan-stereotype tensions, real vs.
  ambiguous supernatural, and the family-rank promotion mechanic. Easy
  characters would not discriminate between tiers.
