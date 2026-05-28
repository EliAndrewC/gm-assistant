---
name: git-author-identity
description: Git author/email to use for commits in the /workspace L7R repo. Differs from the session-env email (gmail).
metadata: 
  node_type: memory
  type: reference
  originSessionId: cd64b507-f2da-48da-9deb-cb37eedecf7e
---

For commits in the /workspace repo, use:

```
Eli Courtwright <eli@courtwright.org>
```

This matches the existing commit history in the repo (verified via `git log --format="%an <%ae>"` on 2026-05-28).

Note: this is **not** the session-env email (`eli.courtwright@gmail.com`). The session env carries Eli's personal/login email; this repo uses his code-author identity. Don't conflate them.

If a fresh container has no git identity configured (`fatal: unable to auto-detect email address`), set it repo-locally — not globally:

```
git config user.name "Eli Courtwright"
git config user.email "eli@courtwright.org"
```

Per Eli's standing rule (see [[feedback_commit_authorization]]), this one-time local config is OK to do without re-asking. Never set `--global`.
