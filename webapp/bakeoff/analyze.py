"""
Unblind the bakeoff votes and tabulate the results.

Joins votes -> tasks -> the tier/model truth and reports, per tier and per
model, how often each won the blind comparison, plus the quick-tags and free
notes grouped by the tier that actually won. Run this only when you are ready to
look (it reveals which tier is which).

Usage (from webapp/):

    python3 -m bakeoff.analyze

Like the rest of the harness this reads only the data files - no chargen or
Gemini dependency.
"""

import json
import os
from collections import Counter, defaultdict

from bakeoff import config


def _load_jsonl(path: str) -> list[dict]:
    rows = []
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def _latest_votes() -> dict[str, dict]:
    """Last vote wins if a task was voted more than once."""
    votes = {}
    for v in _load_jsonl(config.VOTES_PATH):
        votes[v['task_id']] = v
    return votes


def main() -> None:
    tasks = {t['task_id']: t for t in _load_jsonl(config.TASKS_PATH)}
    votes = _latest_votes()

    tier_wins: Counter = Counter()
    model_tier_wins: dict[str, Counter] = defaultdict(Counter)
    tag_by_tier: dict[str, Counter] = defaultdict(Counter)
    notes_by_tier: dict[str, list] = defaultdict(list)
    counted = skipped = orphan = 0

    for task_id, vote in votes.items():
        task = tasks.get(task_id)
        if task is None:
            orphan += 1
            continue
        if vote.get('skipped'):
            skipped += 1
            continue
        label_to_tier = {o['label']: o['tier'] for o in task['options']}
        tier = label_to_tier.get(vote['choice'])
        if tier is None:
            orphan += 1
            continue
        counted += 1
        tier_wins[tier] += 1
        model_tier_wins[task['model']][tier] += 1
        for tag in vote.get('tags', []):
            tag_by_tier[tier][tag] += 1
        if vote.get('notes'):
            notes_by_tier[tier].append(
                f'[{task["character_name"]} / {task["model"]}] {vote["notes"]}'
            )

    print('=' * 64)
    print('BAKEOFF RESULTS (unblinded)')
    print('=' * 64)
    print(
        f'tasks built: {len(tasks)}   votes: {len(votes)}   '
        f'counted: {counted}   skipped: {skipped}   orphaned: {orphan}'
    )
    if not counted:
        print('\nNo counted votes yet.')
        return

    print('\nWins by tier (across all models):')
    for tier in config.TIERS:
        n = tier_wins.get(tier, 0)
        pct = 100 * n / counted
        bar = '#' * round(pct / 2)
        print(f'  {tier}: {n:>3} ({pct:4.0f}%) {bar}')

    print('\nWins by tier, split by model:')
    for model, wins in model_tier_wins.items():
        total = sum(wins.values())
        parts = ', '.join(f'{t}={wins.get(t, 0)}' for t in config.TIERS)
        print(f'  {model} (n={total}): {parts}')

    print('\nQuick-tags by winning tier:')
    for tier in config.TIERS:
        if tag_by_tier.get(tier):
            tags = ', '.join(f'{tag} x{n}' for tag, n in tag_by_tier[tier].most_common())
            print(f'  {tier}: {tags}')

    print('\nNotes grouped by winning tier:')
    for tier in config.TIERS:
        if notes_by_tier.get(tier):
            print(f'  --- {tier} ---')
            for note in notes_by_tier[tier]:
                print(f'    {note}')


if __name__ == '__main__':
    main()
