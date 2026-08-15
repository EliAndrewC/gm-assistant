# Research: Gate Check Registry (022)

**Date**: 2026-08-15. All numbers measured on this container (22 cpus, python 3.14.4), clone at
main tip. Raw statement inventory: scratchpad `gate-stmts.json` (regenerable by the analyzer in
`transform_gate.py` once it lands).

## R1. What gate() actually is (AST census)

**Decision-driving facts**, measured, not assumed:

- `gate()` has **604 top-level statements**: **216 carry literal `check()` calls** (555 literal
  call sites, **549 unique check names** - 189 is merely what one hamlet's scale runs), **11
  statements call `check()` with dynamic (f-string) names** (the parametrized verdicts like
  `field_ringed[<field>]`), **360 are infrastructure** (shared derivations, loops that build
  indexes), and **28 are nested helper `def`s**.
- Every verdict flows through the ONE local closure `check(name, ok, detail)` (defined at the top
  of gate(); `fails.append` appears nowhere else). Waiver semantics (`WAIVE` print, `_waived`,
  `_ran`) live entirely inside that closure. This uniformity is what makes a mechanical split
  sound.
- **Run-state readers are a closed set at the tail**: the waiver meta-checks
  (`waivers_are_documented`, `waivers_are_live`) plus the summary block, at lines ~15540-15553,
  read `_ran`/`_waived`/`fails`. NOTE - the spec guessed `every_feature_classified_*` were
  meta-checks; the census says they are NOT (they compare manifest keys against module-level
  registries, no run state). The meta set is smaller than specced: only the checks that read
  `_ran`, `_waived`, or `fails`.
- Check-statement sizes: median 11 lines, p90 78, and exactly ONE block past the constitution's
  ~1,000 threshold: `city_has_six_ministries` at 2,390 lines. Seven others sit at 240-905 lines.
- Cost distribution (from the 2026-08-15 corpus timing): 555 small fixtures gate in 8-25 ms; 210
  frozen whole-city fixtures (>50 KB, 97% of corpus bytes) gate in 2-6 s each and carry ~95%+ of
  the ~500 s serial replay.

## R2. Decomposition strategy

**Decision**: SEGMENT extraction with explicit parameters, script-generated, order-preserving.
Each of the ~600 top-level statements becomes (or joins) a module-level function
`def _seg_<name>(...free names...) -> dict[str, Any]` whose body is the statement VERBATIM
(dedented, never re-typed), receiving its free variables as parameters and returning the subset of
its written names that it actually bound (`{k: v for k, v in locals().items() if k in WRITES}` -
a name bound only under a branch merges only when bound, which reproduces the original NameError
behavior exactly). The new `gate()` is a small driver: run the prelude (manifest merge, meta,
`check` closure state), then execute segments in **original textual order**, threading a namespace
dict. Full mode = every segment in order -> stdout and failure-list order are preserved by
construction.

**Rationale**: bodies move without rewriting (the riskiest part of any refactor of 12,944 lines is
re-typing them); order is preserved trivially; the namespace threading makes every inter-segment
dependency EXPLICIT and machine-checkable; and the same free/writes metadata that generates the
wrappers gives targeted mode its dependency closure for free.

**Alternatives considered**:
- *Hand-refactor into semantic per-check functions with a curated context object*: cleanest end
  state, weeks of risk on the most load-bearing file in the skill; rejected for this feature -
  the segment registry does not preclude doing this incrementally later, per segment.
- *Rewrite name references to `ctx.attr`*: touches every line of every body; rejected (maximum
  diff, maximum risk, no additional benefit over parameters).
- *`only=` want-guards inside the monolith*: does not discharge clause 12, GM mandated the split;
  rejected.
- *Lazy cached-property context*: elegant but reorders side effects (mutating derivations run at
  first-touch time instead of textual position); rejected in favor of eager in-order closure
  execution, which cannot reorder anything.

## R3. Targeted execution (`only=`)

**Decision**: at generation time, compute for each segment `(free, writes, check base names,
is_meta)`. Targeted mode takes the requested base names, selects the check segments that can emit
them, computes the transitive dependency closure over `free`/`writes`, and runs THAT subset in
original order. Two conservative rules close the known soundness holes:

1. **Mutation counts as a write**: a segment calling a mutating method (`append`, `extend`,
   `add`, `update`, `insert`, `setdefault`, `pop`, `remove`, `sort`, `clear`) on a free name, or
   assigning to a subscript/attribute of one, is treated as WRITING that name, so later readers
   depend on it. (This is the "placement and check read the same geometry" lesson applied to
   dataflow: an invisible dependency is a future silent drift.)
2. **When in doubt, include**: any construct the analyzer cannot classify (e.g. `exec`-like
   dynamism, which the census says does not occur) degrades to "depends on everything before it".
   The failure direction is always "run more than strictly needed", never "skip a dependency" -
   the same direction gencache chose.

Dynamic check names: the f-string bases are static prefixes (`f"field_ringed[{...}]"`), so base
names are extracted statically from the JoinedStr's leading constant. `only` matches base names;
requesting a base name runs every segment that can emit it.

Meta-checks (the `_ran`/`_waived`/`fails` readers): excluded from targeted mode. Requesting one
raises `ValueError` (explicitly, with the name); the REPLAY handles the fallback by running the
full gate for fixtures whose `fires` include a meta name. Unknown names likewise raise - a
targeted run that silently runs nothing would be the "check that never ran looks exactly like a
check that passed" failure mode, which this skill has paid for three times.

## R4. The oracle (how we know nothing moved)

**Decision**: three sweeps, all automated, all diffed to zero:

1. **Full-mode identity**: for all 791 fixtures + all 28 pool manifests, capture
   `(sorted(gate(M)), sha256(stdout))` on the PRE-refactor code, re-capture after, diff. Stdout
   hash makes "byte-identical output" literal.
2. **Targeted-vs-full identity**: for every fixture, run targeted mode on its `fires` base names
   and assert the requested names' verdicts equal the full run's. This validates the dependency
   closure empirically across all 791 real geometries - the strongest available test of R3's
   rules.
3. **Teeth check**: neuter 3 sampled checks (temporarily invert their condition); their fixtures
   must go red in targeted mode. Proves the replay still bites after the switch.

Plus `make done` (the coverage gate holds: the bodies are the same covered lines, and new driver
branches get unit tests), and a timings.md ledger block for the measured speedup.

## R5. What the replay change looks like

`test_regressions.py` keeps its fixture format and its assertion; per fixture it calls
`gate(M, verbose=False, only=bases(fires))` unless `fires` intersects the meta set, in which case
it calls the full gate (measured: such fixtures are rare-to-nonexistent; verified during
implementation). The `__main__` replay path mirrors it.

## R6. Function-size disposition (clause 12)

Post-split sizes equal the statement sizes: median 11 lines, p90 78. **One** function exceeds the
~1,000 threshold (`city_has_six_ministries`, 2,390 lines): it receives the clause-12 inline
justification annotation ("mechanically extracted from the legacy gate; the ministry-complex audit
is one cohesive program; splitting it is recorded debt"), rather than an ad-hoc risky split inside
this feature. The seven 240-905-line blocks are within "suspect but legitimate for a deep engine
function" territory and are left as extracted. The new `gate()` driver itself is small. Net:
clause 12 discharged with one documented annotation.

## R7. Tooling placement and lifecycle

The transformer (`transform_gate.py`: census + wrapper generation + registry emission) is a
one-shot migration tool. It lives in the feature directory `specs/022-gate-check-registry/` (not
the skill directory) so it is preserved with its "why" but never mistaken for engine code, never
imported, and never under the coverage gate. The GENERATED check_village.py becomes the
hand-maintained source of truth the moment it lands; the transformer is not re-run after.

## R8. Risks and their controls

| Risk | Control |
|---|---|
| Hidden dependency the closure misses (mutation via alias, helper closing over a name) | R3 rule 1 + sweep 2 runs every fixture's real geometry through targeted mode; any miss shows as a verdict diff |
| Leaked loop variables (`i`, `k`, `p` leak from one statement into another's reads) | free/writes analysis preserves even accidental couplings as explicit parameters; oracle confirms |
| Generated wrappers break ruff/mypy | ruff format the generated file; check_village is on the mypy relaxed ratchet (verify in pyproject during implementation); wrappers get uniform `Any` signatures |
| Coverage regression from never-taken wrapper returns | full-mode gate still executes every segment on some manifest, same as today; driver branches get dedicated unit tests |
| Concurrency (pytest -n auto) | no module-level mutable state introduced; namespace is per-invocation |
| Budgets in test_villages calibrated against a slower gate | budgets are upper bounds; a faster suite cannot trip them |

## R9. What implementation taught the model (added after the sweeps, 2026-08-15)

The targeted-vs-full sweep (R4 sweep 2) and the big-fixture timing each caught a real hole in the
R2/R3 dataflow model; all three fixes are in the transformer, and the sweep re-validated 791/791
after each. Recorded because the SHAPE of each recurs in any dataflow-over-real-code work:

- **Mutation through a helper closure** (caught as 3 MISMATCHes): `_wtr_add` - a gate-local helper
  - appends into `_wtr`, so the segment CALLING the helper mutates a list it never names. Fix:
  calling a gate-local helper counts as writing everything that helper transitively mutates.
  Without it the closure skipped the producer and the check saw an empty list - a silent PASS,
  the worst failure direction.
- **Raw loads are not dependencies** (caught as "no speedup": 473.9 s ≈ the full-gate 480 s).
  Leaked generic loop variables (`b`, `c`, `i`, `p` - bound by 20-40 segments each) made almost
  every segment depend on almost every earlier one. Dependency edges must be UPWARD-EXPOSED reads
  (readable before definitely bound), while parameters keep the raw free set so runtime semantics
  are untouched. Closures fell from median 232 segments to median 7.
- **A comprehension's target is not a read of the outer name** (caught as "still only 1.4x"):
  `[.. for c in xs]` counted as reading outer `c`. Expression-scoped free-loads (comprehension
  targets and lambda params excluded) took the big-fixture cohort from 331 s to **57.8 s - 8.3x
  against the full-gate baseline**, closures median 7 / p90 48 / max 55 of 586.

Final measured state: full-mode byte-identity on all 814 manifests; targeted-vs-full identity on
all 791 fixtures with 0 meta fallbacks needed; teeth check red on 3 neutered checks; exactly one
function over the clause-12 threshold (1,040 logical statements, annotated); whole affected test
files 2,006 passed in 49 s.
