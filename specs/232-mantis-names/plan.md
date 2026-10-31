# Implementation Plan: Mantis Clan names

**Spec**: [spec.md](spec.md) (spec-fidelity: round 1 revise, round 2 faithful)

## Summary

A Mantis name list (`pool-mantis.jsonl`) beside the Rokugani pool, a pure module that rolls a
Mantis's naming case and builds the name and meaning text, wired into the chargen engine (Mantis
Clan samurai) and the `/name` picker (a `mantis` option), with the four odds as config.

## Technical context

- Python 3, chargen engine (`webapp/chargen/`), `/name` skill scripts (`.claude/skills/name/`).
  `pick_name.py` already puts `webapp/` on `sys.path` (via `similarity.py`) and imports `chargen`,
  so ONE module, `webapp/chargen/mantisnames.py`, serves both - no duplicated odds or rules.
- Data: `.claude/skills/name/pool-mantis.jsonl`, one JSON object per line:
  `{name, gender: male|female|neutral, meaning, source, rokuganized, gm}`. Read from
  `namepool.pool_dir()`, so the deploy bundle (`make prepare-deploy`) copies it too.
- Odds: `[mantis_names]` in `development-defaults.ini` (`rokugani = 20`, `alias = 10`,
  `rokuganized = 10`, `mantis = 60`), declared in `configspec.ini` with those defaults so the
  picker gets them even with no config section.
- Tests: pytest beside the code, 100% coverage on `mantisnames.py`.

## Design decisions

1. **Name the character goes by = full name and record name** (spec FR-006). The meaning line
   carries the real Mantis name in both "goes by" cases (spec-fidelity round 1).
2. **Rokugani-syllable check** (`is_rokugani`): greedy parse into Hepburn morae - the five vowels;
   k g s z t d n h b p m y r w + vowel minus the gaps (si ti tu di du hu zi yi ye wi wu we wo);
   shi chi tsu ji fu; youon (kya ... pyo, sha shu sho, cha chu cho, ja ju jo); syllabic n not
   before a vowel or y. `rokuganized` must parse; validated by a test over the whole list.
3. **Rokuganized case draws only entries whose `rokuganized` differs from `name`** (spec edge
   case). An empty eligible set in any Mantis case falls back to the Rokugani case (FR-007).
4. **Exclusion applies to the name the character goes by** - that is the name the players hear,
   which is what the roster and set-distinctness rules protect.
5. **Neutral entries serve both genders.**
6. **Meaning text**:
   - mantis: `Marama is a Mantis name from the Islands of Spice and Silk, which Rokugani hear as gaijin; it means "moon, the moon goddess".`
   - rokuganized: `Amari is the Rokugani form of the Mantis name Amar, which means "immortal, eternal".`
   - alias: `<Rokugani explanation> <Name> is the name she goes by among Rokugani; her Mantis name is Fatama, which means "daughter of the prophet".`
   - rokugani: the Rokugani explanation unchanged.
7. `/name`: a full-word `mantis` token (the single letter `m` already means male). Output keeps the
   existing `**Name** - explanation` shape with the Mantis meaning text as the explanation.
8. Engine: `Character.__init__` takes the Mantis path when `getattr(self, 'clan', '') == 'mantis'`
   (Samurai sets `clan` before calling it; Monk and Peasant have none). `to_dict` gains
   `mantis_name` and `naming_case`.

## Constitution check

- I (independent review): spec-fidelity ran twice; no UI change, so no frontend-review.
- X (tests, 100% coverage on pure logic): `mantisnames.py` is pure; tests beside it.
- XI (kanji triangle): Mantis names carry no kanji; Rokugani names come from the vetted pool.
- XII (research): names researched from Indonesian, Malay, Javanese, Arabic, Sanskrit and Maori
  sources; each entry records its source.
- XIII (no regressions): baseline the gate before; non-Mantis naming untouched (FR-008).
- XVI (literal): GM odds as defaults; no unrequested secrecy rule.
