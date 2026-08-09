# Quickstart: Capital Housing Layer (021)

The one-map iteration loop for this feature (the skill CLAUDE.md doctrine, specialized):

```bash
cd /gm-assistant/.clones/diagram-city/.claude/skills/diagram

# iterate on THE map (seconds, not the sweep)
DIAGRAM_SKIP_RENDER=1 python3 wip/shiro-daika.gen.py && python3 check_village.py wip/shiro-daika.json | grep -v PASS

# look at what changed (batch every crop in ONE call)
python3 wip/shiro-daika.gen.py && python3 crop_map.py wip/shiro-daika X,Y,R X,Y,R ...

# who placed this / who refused this seat
python3 why_placed.py wip/shiro-daika.gen.py --at X,Y
python3 site_justice.py wip/shiro-daika.json <feature> --limit=25

# cheap linters BEFORE any gate
python3 -m ruff format . && python3 -m ruff check . && python3 -m mypy

# whole test files before the gate, never -k
python3 -m pytest test_settlement.py test_checks.py -q -n auto --no-cov

# the gate: backgrounded, never polled, log tail is the authority
make done > /tmp/gate021.log 2>&1 &

# perf: score the ONE gen solo, A/B against HEAD (never trust profile seconds)
DIAGRAM_SKIP_RENDER=1 python3 -c "import time,runpy; t=time.process_time(); runpy.run_path('wip/shiro-daika.gen.py', run_name='__main__'); print(time.process_time()-t)"
```

Ship sequence (last tasks): move gen+json to `pool/capitals/`, add the `GEN_TIME_BUDGETS`
entry (~4x solo), full sweep, FULL settlement-review (launched the moment the map is final,
one map per agent), the XII closing bookend against the PNG, then the stop-work ritual.
