"""Every project subagent definition opts out of auto-loading CLAUDE.md (docs/subagent-caching.md).

Why: a subagent that loads CLAUDE.md gets the project and user CLAUDE.md files (~18k tokens on
2026-10-17) in its first message, after the system prompt, and that part was measured being
written fresh to the cache on EVERY launch - typed review agents read 2-4k tokens and wrote 32-38k
per launch, whatever their prompt. `omitClaudeMd: true` drops it; each definition restates the
rules it actually enforces, in its own body, which is the part that IS reused across launches.

The list of definitions is read from the directory, never kept here, so a new agent cannot be
added without the flag.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

AGENTS = Path(__file__).resolve().parents[2] / '.claude' / 'agents'


def frontmatter(path: Path) -> str:
    match = re.match(r'---\n(.*?)\n---\n', path.read_text(), re.DOTALL)
    assert match, f'{path.name}: no YAML frontmatter'
    return match.group(1)


def test_there_are_agent_definitions() -> None:
    assert len(list(AGENTS.glob('*.md'))) >= 5


def test_every_agent_omits_claude_md() -> None:
    flag = re.compile(r'(?m)^omitClaudeMd: true$')
    missing = [p.name for p in sorted(AGENTS.glob('*.md')) if not flag.search(frontmatter(p))]
    assert not missing, (
        f'{missing} must set `omitClaudeMd: true` in their frontmatter. Without it every launch '
        'writes the whole project CLAUDE.md to the cache again (~18k tokens). If the agent needs a '
        'rule from CLAUDE.md, restate that rule in the definition body instead - see '
        'docs/subagent-caching.md.'
    )


def test_no_agent_sets_a_one_hour_cache() -> None:
    # Priced and declined 2026-10-17 (docs/subagent-caching.md): the 1h TTL doubles the write price
    # of everything the subagent writes for its whole run, to keep a ~4k-token prefix warm.
    ttl = re.compile(r'cacheTtl:\s*["\']?1h')
    offenders = [p.name for p in sorted(AGENTS.glob('*.md')) if ttl.search(frontmatter(p))]
    assert not offenders, f'{offenders} set a 1h cache TTL; docs/subagent-caching.md says why not'


def test_clone_claude_md_copies_are_not_loaded() -> None:
    # Measured 2026-10-17 (docs/subagent-caching.md): without this exclude a clone session and
    # every general-purpose subagent load BOTH /gm-assistant/CLAUDE.md and the clone's copy.
    settings = json.loads((AGENTS.parent / 'settings.json').read_text())
    assert '**/.clones/*/CLAUDE.md' in settings.get('claudeMdExcludes', [])
