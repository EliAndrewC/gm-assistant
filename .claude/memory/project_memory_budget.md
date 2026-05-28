---
name: container-memory-budget
description: The dev container has a 6 GB memory limit. Headless Chrome (Playwright) is the main consumer; plan around it.
metadata: 
  node_type: memory
  type: project
  originSessionId: cd64b507-f2da-48da-9deb-cb37eedecf7e
---

The dev container is capped at **6 GB RAM**, with earlyoom running on the host. Eli set this up on 2026-05-28 after a series of OOM-related crashes.

**Why:** OOM kills were terminating the session. Capping the container + running earlyoom outside it gives Eli a controlled fail-fast instead of a host-wide stall.

**How to apply:**
- The heaviest consumer in this project is headless Chromium (Playwright), used by `webapp/tests/screenshot.py` and `webapp/tests/dom_audit.py`. Each spins its own browser context.
- Never run those two scripts concurrently. The `make ui-verify` target already serializes them — prefer it over kicking them off in parallel.
- When the `frontend-review` subagent might also open Chromium, run it **after** the screenshot pass finishes, not in parallel — so only one Chromium instance is live at any time.
- Other work is safe at this budget: ordinary pytest runs (no browser), ruff/mypy, subagent fan-out for code search/reading, npm/pip installs.
- If you need to install Chromium system deps (libglib2.0-0t64, libgl1, the long list from `playwright install-deps chromium`), Eli has passwordless sudo in the container — `sudo apt install` works. The runtime container in production has them via Dockerfile, but fresh dev containers don't.
