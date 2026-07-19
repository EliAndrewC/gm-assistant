# Quickstart: Dreams Section

## Run it locally

From `webapp/`:

```bash
cherryd --import l7r          # serves http://0.0.0.0:8080 (or 127.0.0.1 off-container)
```

- Visit `/dreams` - framework writeup + the examples gallery (the Daikoku scene).
- Visit `/dreams/daikoku-masamune-sword-akishi` - the full rendered scene.
- Confirm **Dreams** appears in the top nav alongside Relics / Names / Places.

The dev server reads scenes from `.claude/skills/dream/pool/` automatically (walked up from the package). Override with `L7R_DREAM_POOL_DIR=/path/to/pool`.

## Verify (before "done")

Python (Principle X):

```bash
cd webapp
ruff check . && ruff format --check .
mypy --strict l7r/dreams.py l7r/app.py
pytest tests/test_dreams.py -v --cov=l7r/dreams --cov-report=term-missing --cov-fail-under=100
```

UI (Principle I):

```bash
python tests/screenshot.py            # multi-scroll contact sheets, GM-100/GM-200/tablet/mobile
python tests/dom_audit.py             # MUST report zero issues across all pages x viewports
```

Then a persona pass: open the GM-200 contact sheet for `/dreams` and `/dreams/<slug>` with "a player wants to understand how dream divination works and read one example" in mind, and invoke the `frontend-review` subagent for an independent look (author != reviewer).

## Spoiler-tier smoke check (FR-007)

```bash
# The loader must never see pool-local. Quick manual check:
ls .claude/skills/dream/pool-local/     # local spoiler scenes exist here
curl -s localhost:8080/dreams | grep -i ebisu      # must NOT appear (Ebisu scene is pool-local)
curl -s -o /dev/null -w '%{http_code}\n' localhost:8080/dreams/ebisu-dreams-shiro-reiji   # expect 404
```

The automated regression in `test_dreams.py` (INV-1) is the durable guard; this is the eyeball confirmation.

## Deploy note

`make prepare-deploy` must copy the public pool into the build context:

```
cp -r ../.claude/skills/dream/pool skills/dream/pool     # pool/ ONLY - never pool-local/
```

and the runtime sets `L7R_DREAM_POOL_DIR` to the bundled path. `pool-local/` is gitignored and never enters the image.
