---
name: memory-persistence-setup
description: How Claude Code memory survives container rebuilds in this repo. Files live in /workspace, symlink bridges to the loader path.
metadata:
  type: reference
---

Claude Code's auto-memory loader reads from `/home/agent/.claude/projects/-workspace/memory/`. In Eli's setup, `/home/agent` is an overlay-FS upper dir — wiped on container rebuild. `/workspace` is a real ext4 mount and the only persistent location.

**Resolution:** memory files live at `/workspace/.claude/memory/` (committed to this repo). On container start, a bootstrap script creates the loader-side symlink:

```
/home/agent/.claude/projects/-workspace/memory → /workspace/.claude/memory
```

The symlink itself can't be checked into git (its target path doesn't exist on the host), so the bootstrap script *is* the committed artifact.

**Run after starting a fresh container:**

```
bash /workspace/.claude/bootstrap-container.sh
```

The script is idempotent — safe to re-run.

**Why this direction (workspace files, ephemeral symlink) and not the reverse:** if the symlink lived in `/workspace/.claude/` pointing into `/home/agent/...`, the symlink would be persistent but the *target* (where files actually go) would be ephemeral — useless. The storage has to live on the persistent side, and the loader-expected path has to be the symlink.

**If a future fresh container has memory files but the loader returns empty:** the symlink wasn't recreated. Run the bootstrap script.

Related: [[feedback_commit_authorization]] (since this whole setup involves committing memory content to the repo).
