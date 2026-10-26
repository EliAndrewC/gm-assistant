# Guards: what is enforced, and how to add one

*Project reference, moved out of [`../CLAUDE.md`](../CLAUDE.md) on 2026-10-17 so it is loaded on demand rather than in every session (and every subagent) context. CLAUDE.md keeps the one-line always-on version of each rule.*

**Load this file when:** a hook blocked you and you want to know why it exists, you are adding or changing a guard (hook, gate check, guard test), or you are deciding whether a rule should be enforced at all.

---

**WHAT IS ENFORCED, AND WHERE** (audit 2026-08-24). Fourteen guards, each with a test companion that
`make hooks-test` runs as a gate phase - a guard without one turns the gate red (constitution XVIII).

| rule | mechanism |
|---|---|
| never `git push --force` | [`scripts/repo-safety-hooks.sh`](../scripts/repo-safety-hooks.sh) - no escape; "never" stops meaning never the moment one exists |
| no git writes to `/host-l7r-repo` | same script; EDITS there stay legal, the intake workflow needs them |
| the GM's SOURCE blocks are not editable (V) | [`scripts/source-block-hooks.sh`](../scripts/source-block-hooks.sh) - checks containment against the file on disk |
| hyphens only; American spellings | [`scripts/house-style-hooks.sh`](../scripts/house-style-hooks.sh) - exempts the GM's writing and the files that must quote the rule |
| a README is the GM's to write (XVII) | [`scripts/readme-hooks.sh`](../scripts/readme-hooks.sh) |
| guard files are not edited casually | [`scripts/guard-file-hooks.sh`](../scripts/guard-file-hooks.sh) |
| a spec is reviewed before implementation (XVI) | [`scripts/review-gate.sh`](../scripts/review-gate.sh), run by `sync-with-main.sh` at PUSH time |
| no `-k` subset before the gate; no branches; no polling; batching | the pre-existing `gate`/`no-branch`/`no-poll`/`batching` hooks |
| shared subagent instructions live in a definition, not repeated launch prompts | [`scripts/subagent-cache-hooks.sh`](../scripts/subagent-cache-hooks.sh) (general-purpose launches, once per session); `omitClaudeMd` on every definition by `webapp/tests/test_agent_definitions.py` |
| INI files are read with ConfigObj (`l7r.inifile.read_ini`), never configparser | `webapp/tests/test_ini_reader.py`, which parses every tracked `.py` for a configparser import (2026-10-26: configparser keeps the quotes `development-secrets.ini` writes around values, so a quoted Gemini key was sent with its quotes and rejected as invalid - for the second time, after feature 218) |
| a clone deploys main's secrets, never its own stale copy | [`scripts/deploy-secrets-hooks.sh`](../scripts/deploy-secrets-hooks.sh), run by `make prepare-deploy` (2026-10-18: a stale clone copy would have shipped production without the /look-up key) |

**Deliberately NOT enforced**, because a guard that fires on correct work teaches a session to bypass
every guard: the caste sense of "people" (correct in narrative and vow voice), gender-neutral
office-holders (named characters keep their pronouns), Principle XI's kanji triangle, and the
behavioral principles XII/XIV/XV. File size past ~1,000 lines is REPORTED by `make audit`, never
gated - the rule prompts a question rather than forbidding a size.

**A GUIDELINE THAT LIVES ONLY IN PROSE IS NOT A RULE** (GM 2026-08-31: *"automated tests are the
solution for not making people correctly remember how to do everything all the time"*). Where a
standard can be counted, assert the count - and set the threshold at the STANDARD, never at wherever
the code currently sits. Measured the same day: the mention bot's reply pools were documented as
needing "about a dozen" responses each and asserted at `>= 3`, so a median of four shipped through a
green gate with the docstring still claiming twelve. The corollary is knowing what cannot be tested
- whether a joke is in voice is a judgment call - and saying so in the doc rather than leaving the
next reader to guess which rules are enforced.

**When you add a guard**, four properties, each learned by getting it wrong: match INVOCATIONS not
mentions (seven false positives in one feature - a grep, a commit message, a docstring, a fixture
argument, a redirect, a test harness, and a hook that blocked its own repair); check the ESCAPE FIRST
or the guard cannot be repaired through the channel it guards; prove it FIRES by deleting it and
watching a test go red; and **DERIVE the guard's list from the thing it guards - never hand-maintain
it, and never let the test keep its own copy**. Measured 2026-08-30: `chargen/website.py` stripped
secret config sections using a frozenset of six names commented *"add new secret sections here
whenever development-secrets.ini grows"*, and `tests/test_chargen_security.py` listed the same six.
The file had since grown three more, so AWS keys, a bearer token and a GitHub PAT were being
serialized into `index.html` - and because the guard and the guarded agreed with each other, the leak
was invisible from both sides. Both now read the file. A list that must be updated from memory is not
a security boundary.
