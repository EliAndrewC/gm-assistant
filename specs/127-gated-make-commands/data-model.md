# Data model

## Operation (the registry)

Every runnable unit of this project's work. **Enumerated, never inferred** - a guard that guesses
which commands are expensive will guess wrong in both directions.

| field | meaning |
|---|---|
| `module` | the importable entry point, e.g. `l7r.diagram.tools.cohort_audit` |
| `target` | the make target that runs it - what a refusal message names (FR-006) |
| `cost` | `expensive` or `cheap` |

`cost` decides PROMPTING only. REFUSAL applies to every row regardless (spec, "Two properties,
deliberately separated").

**Why a registry rather than a rule**: the 18 entry points do not divide by name, path or package.
`tools/` holds both `cohort_audit` (25 minutes) and `why_placed` (a manifest read). Any heuristic
over module paths misclassifies, and a misclassified cheap operation that starts prompting is how a
session learns to reach for the override.

**Derived, not hand-maintained where possible** (constitution X clause 14): the row set is checked
against the filesystem by a guard test, so an entry point added later without a row fails the gate
rather than shipping ungated.

## Audit log entry (`dev/bypass-log.jsonl`)

Existing file, one JSON object per line. Gains `outcome`.

| field | meaning |
|---|---|
| `utc` | timestamp |
| `target` | the make target |
| `commit` | short HEAD at the time |
| `outcome` | `permitted` / `cancelled` / `refused` (NEW, FR-012) |
| `why` | the written reason; absent for `refused` |

**Why `outcome` matters**: without it a session that backed out looks identical to one that never
tried, and the log cannot answer the question it exists for. The GM's own use for it: a rising count
of `cancelled` is the early signal that the cheap path has stopped being sufficient, at which point
the right response is to make the fast path better rather than to keep refusing.

## Determination verdict (in-process, not persisted)

Computed once per process (research R4).

| field | meaning |
|---|---|
| `via_make` | bool - a qualifying make found in the ancestry |
| `reason` | why not, for the refusal message: no make at all / foreign cwd / foreign `-f` |
