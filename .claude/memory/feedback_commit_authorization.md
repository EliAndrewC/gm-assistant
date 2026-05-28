---
name: commit-authorization
description: Eli has standing authorization for Claude to create local git commits without confirming each one. Does NOT extend to pushing.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cd64b507-f2da-48da-9deb-cb37eedecf7e
---

Eli authorized me to create commits on his behalf without re-confirming for each one. This applies to local commits only — push remains a separate confirmation.

**Why:** Stated explicitly on 2026-05-28 after I held off on committing the access-control + secrets-fix bundle waiting for permission. Eli's words: "you are authorized to make commits on my behalf so please do that." The standing block on auto-commits (per the project's default git-safety convention and the spec-kit auto-commit hooks) creates friction when commits are the obvious next step after a verified change.

**How to apply:** When work is verified clean (`make done` passing, screenshots/dom_audit clean when UI changed, frontend-review passed when author=reviewer) and the user has approved the plan or the work is a direct execution of a stated request, go ahead and commit. Use a HEREDOC for the message, follow the project's style (1-2 sentence why + bullet body when complex), and add the `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer.

Still confirm before:
- Pushing to a remote.
- Any destructive git operation (reset --hard, force push, branch -D).
- Amending a commit that's already been shared.
- Skipping hooks (--no-verify) for any reason.

This is a [[reference_git_author_identity]] sibling — the author identity to use is captured there.
