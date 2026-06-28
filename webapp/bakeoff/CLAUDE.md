# Bakeoff - context for a fresh session

This directory is a **temporary, local-only experiment**, not part of the
shipped app. If you are picking this up cold, read this file plus
[`README.md`](README.md) before touching anything here.

## What we are actually doing (the bigger arc)

The GM wants a **"Synthesize Backstory" button** in the character generator: after
the scripted/random chargen produces a character (clan, rank, honor, tags,
advantages/disadvantages, etc.), one click sends those traits to a Gemini text
model and gets back a 1-3 paragraph prose "gestalt" that reconciles the traits
into a believable person. It is the text twin of the existing AI portrait button.
Re-rolling and GM steering notes are part of the design.

The synthesis backend already exists:

- [`../chargen/synthesis.py`](../chargen/synthesis.py) - `synthesize(character,
  extra_notes, brief, model)`, `build_prompt`, `format_character`, plus a CLI
  harness (`_main`). Mirrors `chargen/art.py`.
- [`../chargen/synthesis_brief.md`](../chargen/synthesis_brief.md) - the shipped
  setting brief (this is **tier t0** in the bakeoff).
- Config knob `[gemini] text_model` added to `chargen/configspec.ini`; default is
  `gemini-3.1-pro-preview` (`synthesis.DEFAULT_TEXT_MODEL`).

The **open question this bakeoff answers**: how much (and what kind of) l7r.md
setting context should that prompt carry? Too little and outputs are generic; too
much is slow/expensive and can dilute or drag in off-topic campaign specifics.
We are comparing four context tiers, blind, on hard characters, to find the knee
of the curve before wiring the button.

## Status (as of this handoff)

- Scaffolding is **complete and verified end to end** (lint/format/mypy pass; a
  smoke run exercised generate -> build_tasks -> app -> vote -> analyze).
- **Generated so far:** only a 2-character demo (`hideki`, `emi`), 1 sample each,
  all 4 tiers x 2 models = 16 candidates, 4 tasks, in `data/` (gitignored but
  present on disk). **No real votes yet** (the smoke-test vote was cleared).
- The **full run has NOT been done.** Full matrix = 10 chars x 4 tiers x 2 models
  x 3 samples = 240 cells (`python3 -m bakeoff.generate --dry-run` to see cost;
  the t3 "everything" arm dominates at ~20M input tokens).

## How to run it (all from `webapp/`)

```
python3 -m bakeoff.generate --dry-run     # preview matrix + cost
python3 -m bakeoff.generate               # full run (resumable; skips done cells)
python3 -m bakeoff.build_tasks            # build blind comparison tasks
python3 -m bakeoff.app                    # vote blind in browser (host port 8091)
python3 -m bakeoff.analyze                # unblind + tabulate (only when ready)
```

## Things not to re-derive

- **The four tiers** are composed, not hand-maintained copies (see `briefs.py`):
  t0 = shipped brief (~3k tok); t1 = +clan/school flavor + few-shot GM NPC
  exemplars (~8k); t2 = +material/government/calendar/supernatural sliced
  verbatim from l7r.md (~39k); t3 = entire l7r.md + budgets.md (~337k). t2/t3
  pull exact text by heading via `extract_section`, so the GM's writing is never
  retyped.
- **Blinding is enforced server-side** in `app.py`: the template only ever gets
  the option label + text, never the tier or model. Keep it that way.
- **Variance control:** 3 samples/cell; one task per sample round so rounds act
  as repeats. **Hard characters** (`characters.json`, each has a `stress` note)
  are deliberately chosen to discriminate between tiers - do not swap in vanilla
  ones.
- **Circular-import quirk:** importing `chargen` cold fails; `generate.py` /
  `build_tasks.py` do `import l7r` first to dodge it (the app launches the same
  way). `app.py` and `analyze.py` are decoupled and need neither.
- **Lint/type gates:** `bakeoff/*.py` and `chargen/synthesis.py` are in the
  grace-list in `pyproject.toml`; `bakeoff/data/` is gitignored.

## Next steps / open decisions

1. Run the full generation, vote blind, run `analyze`. Interpret per the tier
   knee (see README "Design notes").
2. Tune candidates before/after a run: the **honor** section in
   `synthesis_brief.md` is the least-canon part (l7r.md does not define honor),
   and `flavor_clans.md` is my canon summary - both are fair game to edit.
3. Possible improvement if the t3 run is too costly: Gemini **context caching**
   for the big static brief (deliberately left out to keep the harness simple).
4. **When a tier wins:** wire an `@ajax def synthesize` route + a "Synthesize
   Backstory" button in `chargen/website.py` + `templates/index.html` (copy the
   `generate_art` pattern), add tests/coverage, then **delete this whole
   `bakeoff/` directory** and its `pyproject.toml` grace-list entries.
