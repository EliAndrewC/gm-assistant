# Quickstart: working with `l7r.diagram` after feature 119

## The one thing that changed

Engine modules are now under `l7r.diagram`. You still work from the skill directory
(`.claude/skills/diagram/`), which is still the `sys.path` root - only the dotted name is longer.

```bash
cd .claude/skills/diagram

# gate one map
DIAGRAM_SKIP_RENDER=1 python3 pool/hamlets/inashiro.gen.py
python3 -m l7r.diagram.check_village pool/hamlets/inashiro.json

# regenerate through the cache
python3 -m l7r.diagram.pipeline.regen pool/hamlets/sawada.gen.py
python3 -m l7r.diagram.pipeline.regen pool/*/*.gen.py

# roll a hamlet cohort
python3 -m l7r.diagram.hamletgen --batch 24

# ask why something landed where it did
python3 -m l7r.diagram.tools.why_placed pool/hamlets/inashiro.json <feature>

# the gate
make done
```

In a generator or a test:

```python
from l7r.diagram.settlement import Settlement
from l7r.diagram.hamletgen import HamletSpec, generate
```

A pool generator's bootstrap block is unchanged - `SKILL = dirname(dirname(HERE))` still lands on
the skill directory, because `pool/` did not move.

## The webapp

```bash
cd webapp
cherryd --import l7r.app     # was: --import l7r
make serve
```

`import l7r` no longer mounts anything - it is a namespace with no code in it. Import `l7r.app` when
you want the CherryPy tree wired.

## The rule that keeps it working

**Never create `l7r/__init__.py`** - not in `webapp/l7r/`, not in `.claude/skills/diagram/l7r/`.
Doing so turns that directory into a regular package, which terminates the import search and makes
the OTHER portion silently stop existing. There is no error at the point of the mistake.

Each tree has a test asserting `l7r.__file__ is None`. If you ever see it fail, someone added an
`__init__.py`; delete it rather than "fixing" the test.

## Adding to `sitegen`

`l7r.diagram.sitegen` holds generation machinery that belongs to no one settlement tier - geometry
helpers, types and units, the worker-count courtesy. Two rules:

1. **Membership**: a module goes in `sitegen` only if it names no tier concept (no households,
   paddies, bunds, hamlet bands, headmen, walls, wards). If it does, it belongs to that tier's
   generator.
2. **Direction**: `hamletgen` (and any future `villagegen`, `towngen`) imports `sitegen`. `sitegen`
   never imports them. A test asserts this.

When a later tier needs a stage that currently lives in `hamletgen`, **MOVE it into `sitegen`** -
do not copy it. Copying is how two tiers quietly drift apart.

## Verifying a change the way this feature was verified

```bash
# baseline on unmodified code - a detached worktree, never a stash
git worktree add --detach /tmp/base HEAD

# regenerate everything, frozen legacy maps included, and hash it
python3 -m l7r.diagram.pipeline.regen --frozen-ok pool/*/*.gen.py
find pool -type f | sort | xargs sha256sum > /tmp/after-hashes.txt
diff /tmp/baseline-hashes.txt /tmp/after-hashes.txt   # must be empty for a pure refactor
```
