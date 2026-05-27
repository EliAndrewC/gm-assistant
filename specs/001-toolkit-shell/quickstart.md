# Quickstart — L7R Toolkit Phase 1

## Run locally

```bash
cd /workspace/webapp
# install deps (idempotent on the dev sandbox; uses user-site install)
pip3 install --user --break-system-packages -r requirements.txt

# start the toolkit
make serve
# equivalent: cherryd --import l7r
```

Open <http://127.0.0.1:8080/> in Chrome.

## Verify "done"

```bash
cd /workspace/webapp
make done
# runs ruff check + ruff format --check + mypy --strict + pytest + coverage on l7r/
```

For UI verification:

```bash
# in one terminal
make serve

# in another terminal
cd /workspace/webapp/tests
python3 screenshot.py
# captures gm-100, gm-200, tablet, mobile screenshots of every section
# checks DOM-overflow audit and reports zero / non-zero findings
```

## What you should see

1. `/` — landing page with the L7R Toolkit name, a brief description, and nav to Characters / Relics / Names.
2. `/relics` — 7 Fortune sections with vermillion-stamped kanji headers and 6 cards each (42 total).
3. `/relics/<slug>` — detail view of one relic; prev/next within Fortune at the foot.
4. `/chargen` — the existing chargen UI inside the new shell; generate-and-upload flows unchanged.
5. `/names` — coming-soon placeholder card.

## Stop the server

`Ctrl-C` in the `make serve` terminal.

## Where things live

- New Python code: `/workspace/webapp/l7r/`
- New tests: `/workspace/webapp/tests/`
- Static assets: `/workspace/webapp/l7r/static/`
- Templates (new + shared): `/workspace/webapp/l7r/templates/`
- Legacy chargen (unchanged behavior, new visual shell): `/workspace/webapp/chargen/`
- Relic pool (source of truth for relic content): `/workspace/.claude/skills/relic/pool/`
- Spec/plan/tasks for this work: `/workspace/specs/001-toolkit-shell/`
