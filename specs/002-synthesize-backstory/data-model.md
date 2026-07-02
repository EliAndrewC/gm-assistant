# Phase 1 Data Model: Synthesize Backstory

No persistent storage. These are the in-memory shapes the feature passes around.

## Entity: Character (input)

The generated NPC, already produced by chargen. Consumed by `synthesis.format_character`.

- Identity: `full_name` / `personal_name`, optional `name_meaning`.
- Mechanical: `clan`, `family`, `lineage`, `school`, `rank` (float, upper/lower), `recognition` (float), `xp`, `honor` (1-5).
- Descriptive: `tags` (list), `traits` (list of advantages/disadvantages/physical/behavioral).
- Rendered (preferred when present): `public`, `private` blocks from `Character.to_dict`.

Validation/handling: missing rendered blocks fall back to assembling from raw fields (existing behavior). No new validation introduced; the feature treats Character as read-only input.

## Entity: BriefSources (new, in `chargen/brief.py`)

The resolved file inputs that compose the full brief.

- `brief_path` -> `chargen/synthesis_brief.md` (design brief; honor model + calendar instruction).
- `flavor_path` -> `chargen/flavor_clans.md` (relocated; per-clan materialist summary).
- `corpus_dir` -> resolved setting directory containing `l7r.md` and `budgets.md`. Resolution order: explicit config/env path -> bundled `webapp/setting/` -> dev mount `/host-l7r-repo/setting/`.
- Derived: `clan_blurb` = the "The Great Clans" section extracted by heading from `l7r.md`.

Rules:
- If `corpus_dir` cannot be resolved or required files are absent -> raise a clear, typed error (FR-010); never produce a degraded brief.
- Files are read verbatim (no mutation; Principle V).

## Entity: FullBrief (value produced by `brief.py`)

The assembled setting-brief string: `synthesis_brief.md` + clan blurb + `flavor_clans.md` + entire `l7r.md` + a labeled `budgets.md` block. MUST equal `bakeoff.briefs.build_tier('full')` for the same inputs (FR-009) until bakeoff is removed.

## Entity: SynthesisRequest (the @ajax call)

- `character` data (the displayed character's fields, as the portrait route already passes character data), and
- `extra_notes` (optional GM steering string).

## Entity: SynthesisResult (the @ajax response)

- On success: `{ ok: true, backstory: <1-3 paragraph string> }`.
- On failure: `{ ok: false, error: <human-readable message> }` for: missing credential, model/API error or timeout, missing bundled corpus, empty model output. The route surfaces these; it never falls back to a thinner prompt (FR-010).
