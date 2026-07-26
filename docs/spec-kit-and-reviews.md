# Spec-kit hooks and the subagent-check TDD procedure

*Project reference, split out of [`../CLAUDE.md`](../CLAUDE.md) so it is loaded on demand rather than in every session's context. CLAUDE.md keeps the short always-on version of these rules and points here for the full spec.*

**Load this file when:** the GM asks for a new rule that a REVIEW SUBAGENT should enforce (building-review, backstory-review, frontend-review), or you need the spec-kit auto-commit hook details.

---

**Subagent-check TDD (REQUIRED procedure for improving review subagents)**: when the GM asks for a new rule that a review subagent (e.g. `building-review`) should enforce, do NOT simply apply the fix and write the rule into the agent. The current artifacts contain the motivating defect - that is the failing test. Procedure:

1. Add only the **general, category-level rule** to the agent definition. Never name the specific instance yet - that would test nothing about whether the check generalizes.
2. Run the agent against the artifact that contains the known defect, unfixed.
3. **If it flags the defect**, the rule generalizes: now fix the artifacts, and only now record the specific instance in the agent definition as a validated example for future runs.
4. **If it misses**, sharpen the general rule and re-run - do not shortcut by naming the instance. Escalation ladder from the first application (2026-07): a trait buried in a checklist gets skimmed; adding a protocol step barely helps; what reliably works is making the agent's **output format demand an enumerated sweep** (a mandatory report section listing every item checked) - models do what the required output structure forces.
5. Record the red/green outcome in the artifact's review log.

**Gotcha (harness behavior)**: agent definitions are snapshotted when the session registers them - mid-session edits to `.claude/agents/*.md` do NOT reach agents launched by type, which silently invalidates the TDD run. When iterating on an agent definition, launch a `general-purpose` agent instructed to Read the definition file and adopt it; the registered type picks up the changes next session.

**Spec-kit hooks**: `.specify/extensions.yml` defines auto-commit hooks before each spec-kit step. Under the session-clone workflow (below), spec-kit work happens inside the session's clone, where committing is the session's job - the auto-commit hooks may run there. Never run them against main `/gm-assistant` or `/host-l7r-repo`.
