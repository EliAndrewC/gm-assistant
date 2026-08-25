# Research: Scripted NPC Naming

## R1 - The two name sources, measured (2026-08-25)

- `/.claude/skills/name/`: 103 male + 97 female = 200 pool entries with explanation, format, notes, peasant flag. Picker `pick_name.py` draws at random (nothing is consumed) and excludes by similarity to `campaign-names.txt`.
- `webapp/chargen/male_names.txt` (574) / `female_names.txt` (288): the engine's private lists, name + meaning, no tags. Loaded into `constants.NAMES` at import.
- `campaign-names.txt`: 64 names, last refreshed 2026-05-25, cookie-scraped. Live roster on 2026-08-25: 117 characters; 114 missing from the file. Two pool names (`Chiyoko`, `Isao`) are live NPCs and the picker would hand them out. Usable pool against the live roster: 97 male / 85 female (61 / 69 peasant-flagged).

**Decision**: the skill pool is the single source (it has caste tags and the `/names` page already reads it). The engine's lists are deleted, not merged - merging would grow the pool, which the GM deferred. **Cost accepted and reported**: the engine's raw supply drops from 862 to 200 (about 180 usable after exclusion). Alternatives priced: (a) merge the 862 into the pool - rejected as pool growth by another name; (b) keep both lists and dedupe - rejected, that is the two-source problem the GM asked to end. The GM decides pool size with this number in view.

## R2 - Why `/chargen` could reuse a live name

`constants.USED_NAMES` is filled by `op.update_used_names`, a thread subscribed to `cherrypy.engine` `start`. The `/chargen` skill runs the engine from a plain script; the CherryPy engine never starts, the thread never runs, `USED_NAMES` is empty. Only `create_character` adds to it, in-process. So every `/chargen` roll was made against an empty exclusion set. **Decision**: the engine reads used names from the cache FILE on every pick (memoized by mtime); no dependency on process lifecycle.

## R3 - Where refreshes happen (network policy)

A name pick must be a file read: tests construct hundreds of characters, and a pick that could hit OP would make the engine untestable offline and slow. So OP is contacted only at explicit sites:

1. `op.create_character` after success: `opcache.refresh_cache_file()` inside try/except (op.py is grace-listed; fail-soft). Incremental: one list call + one body fetch for the new id, and it reconciles website-added characters in the same pass.
2. `pick_name.py`: `opcache.refresh_if_stale(3600)`; `--refresh` forces. Failure -> warning line, pick proceeds.
3. The `/chargen` Step 2 script: one `opcache.refresh_if_stale()` line before rolling.
4. The webapp's hourly thread: now calls `refresh_cache_file()` (keeps the file reconciled for the Generate button).

The one-hour window mirrors the retired `/loop 1h` cadence; deliberately not shorter so `/name` invocations in quick succession do not each pay an OP round trip.

## R4 - Concurrent read/write of the cache file

`save_cache` wrote in place; a reader could observe a truncated file and `load_cache` would return `{}` -> an EMPTY roster -> every name looks free. **Decision**: write to `<path>.tmp` then `os.replace` (atomic on POSIX); readers see either the old or the new file. The malformed-file branch stays (a genuinely corrupt file is logged), but it can no longer be produced by a concurrent write.

## R5 - Where the similarity code lives

One implementation (FR-006). The webapp cannot import from `.claude/` in deployment (only pool DATA is bundled), so the canonical module is `webapp/chargen/similarity.py` (typed, covered) and the skill's `similarity.py` becomes a shim that adds `webapp/` to `sys.path` and re-exports. The skill's existing similarity tests keep passing through the shim, which proves the shim.

## R6 - Given name = last whitespace token

Matches the existing convention in `op.py` (`name.split()[-1]`) and the roster's shapes: mononyms (`Denbei`), `Family Given` (`Kitsune Izumi`), `Family no House Given` (`Bayushi no Daika Bokuden`). Bare family/place entries (`Tsuruchi`, `Reiji`) are excluded like any other token - harmless, the rule is loose by design.

## R7 - Supporting-cast names in prose (FR-015, from the round-1 fidelity review)

`/synthesize` Step 2c and `/chargen` Step 3b invent parents, sensei, rivals and superiors by hand, and `backstory-review` then greps the campaign context for collisions - a hand loop inside a review cycle. **Decision**: one scripted call BEFORE the prose - `pick_name.py --bank 4 --avoid <subject given name>` - writes a bank of 4 male + 4 female vetted names to the scratch dir; the prose draws invented names only from it. The bank is one set (mutually distinct under the set rule, including against the subject). The review rule stays as a backstop and gains a line: an invented name not in the bank file is a FLAG. Bank size 4+4 is a judgment: a 1-3 paragraph backstory rarely names more than three or four others; the bank is cheap to regenerate larger with `--bank 6`.

## R8 - The gate went from 3 s to 686 s, and why (measured 2026-08-25)

Baseline `make done` pytest phase: 553 passed in 3.2 s. First run with the feature: 612 passed in
686 s - and the gate runs pytest twice (plain, then under coverage), so ~23 minutes. Two causes,
both mine, both found by measuring rather than guessing:

1. **Every name pick re-ran the loose similarity check across the whole pool against the whole
   roster** - 200 x 117 edit distances, ~50 ms - and the engine's existing tests roll characters
   thousands of times (`test_character_rank_bonus` alone rolls 400 per assertion). Fix: memoize the
   roster-filtered pool on `(pool, roster)` (`namepool.roster_clean`, lru_cache); the per-pick work
   is then only the set-rule check against the avoid list. 686 s -> 6.2 s serial.
2. **`create_character`'s new post-create cache refresh reached the real OP API from
   `test_op.py`** (1.1 s per test, network) because the test seams covered the browser session but
   not the new boundary. Fix: seam `opcache.refresh_cache_file` in the shared patch helper, plus two
   tests (it is called; a failure there does not fail the creation).

The GM asked whether this gate needs the diagram repository's short-circuit ladder. No: at 3-6 s of
pytest the whole gate is under a minute and every phase reporting together is worth more than a
cheaper rung. The 20-minute figure was a regression, and the rule that caught it is the one already
in CLAUDE.md - take a MEASURED baseline before judging.
