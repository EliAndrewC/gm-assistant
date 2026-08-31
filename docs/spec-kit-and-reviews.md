# Spec-kit hooks and the subagent-check TDD procedure

*Project reference, split out of [`../CLAUDE.md`](../CLAUDE.md) so it is loaded on demand rather than in every session's context. CLAUDE.md keeps the short always-on version of these rules and points here for the full spec.*

**Load this file when:** the GM asks for a new rule that a REVIEW SUBAGENT should enforce (backstory-review, frontend-review), or you need the spec-kit auto-commit hook details.

---

**Subagent-check TDD (REQUIRED procedure for improving review subagents)**: when the GM asks for a new rule that a review subagent (e.g. `backstory-review`) should enforce, do NOT simply apply the fix and write the rule into the agent. The current artifacts contain the motivating defect - that is the failing test. Procedure:

1. Add only the **general, category-level rule** to the agent definition. Never name the specific instance yet - that would test nothing about whether the check generalizes.
2. Run the agent against the artifact that contains the known defect, unfixed.
3. **If it flags the defect**, the rule generalizes: now fix the artifacts, and only now record the specific instance in the agent definition as a validated example for future runs.
4. **If it misses**, sharpen the general rule and re-run - do not shortcut by naming the instance. Escalation ladder from the first application (2026-07): a trait buried in a checklist gets skimmed; adding a protocol step barely helps; what reliably works is making the agent's **output format demand an enumerated sweep** (a mandatory report section listing every item checked) - models do what the required output structure forces.
5. Record the red/green outcome in the artifact's review log.

**Worked example, 2026-08-31: `mention-context-review`.** The GM asked for an audit of whether each
Discord bot reply makes sense to somebody not already in on the joke, and quoted two shipped replies
as his evidence. Procedure as written above: the general rule went into the agent definition with
neither instance named; a `general-purpose` agent was told to read that file and adopt it, and was
handed the two categories UNFIXED. **It flagged both of the GM's lines** (`GM_MIRUMOTO#8`, the
"four-fifty on a Friday" one, and `ministry_of_revenue#6`, the four smuggling methods) while passing
the self-contained replies sitting beside them - 10 of 11 and 7 of 10 respectively, with reasons
that matched the GM's own. Red established, the two were then recorded in the agent file as
validated examples, and only then was anything edited.

The output format is what makes it work, and it is the same lesson as the first application: the
agent must return **a row per reply, by index, with a verdict**, not a highlight reel. That is what
stops a defect two lines from a flagged one going unopened - and across nine sweeps it turned up
things nobody was looking for, including fourteen replies with words missing out of the middle of
them.

**Gotcha (harness behavior)**: agent definitions are snapshotted when the session registers them - mid-session edits to `.claude/agents/*.md` do NOT reach agents launched by type, which silently invalidates the TDD run. When iterating on an agent definition, launch a `general-purpose` agent instructed to Read the definition file and adopt it; the registered type picks up the changes next session.

**Spec-kit hooks**: `.specify/extensions.yml` defines auto-commit hooks before each spec-kit step. Under the session-clone workflow (below), spec-kit work happens inside the session's clone, where committing is the session's job - the auto-commit hooks may run there. Never run them against main `/gm-assistant` or `/host-l7r-repo`.
