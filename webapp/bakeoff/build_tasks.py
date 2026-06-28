"""
Build blind comparison tasks from the generated candidate matrix.

Each task is one blind comparison screen: for a single (character, model, sample
round) it gathers the four tiers' outputs, shuffles them into opaque positions
(A/B/C/D), and stores them with the rendered character sheet. The tier behind
each position is recorded in the task file for later unblinding but is NEVER sent
to the browser by the webapp.

Pairing the same sample index across tiers, and producing one task per sample
round, means the three rounds act as repeats that average out generation
variance when the votes are tallied.

The build is deterministic and idempotent: option order is seeded from the
task_id, so re-running after generating more cells never reshuffles (or
invalidates the votes for) tasks that already existed.

Usage (from webapp/):

    python3 -m bakeoff.build_tasks
"""

import hashlib
import json
import os
import random

import l7r  # noqa: F401 - import for side effect: resolves chargen circular import

from bakeoff import config
from chargen import synthesis

_LABELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']


def task_id(character_id: str, model: str, round_: int) -> str:
    key = f'{character_id}|{model}|{round_}'
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def load_candidates() -> dict[tuple, dict]:
    """Index candidates by (character_id, tier, model, sample)."""
    index = {}
    if not os.path.exists(config.CANDIDATES_PATH):
        return index
    with open(config.CANDIDATES_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            c = json.loads(line)
            index[(c['character_id'], c['tier'], c['model'], c['sample'])] = c
    return index


def build() -> list[dict]:
    with open(config.CHARACTERS_PATH, encoding='utf-8') as f:
        characters = json.load(f)
    candidates = load_candidates()

    tiers = config.TIERS
    models = config.MODELS
    samples = config.SAMPLES

    tasks = []
    for character in characters:
        sheet = synthesis.format_character(character)
        for model in models:
            for round_ in range(samples):
                cells = [candidates.get((character['id'], tier, model, round_)) for tier in tiers]
                if any(cell is None for cell in cells):
                    continue  # this round is not fully generated yet; skip it
                tid = task_id(character['id'], model, round_)
                options = [
                    {'candidate_id': c['candidate_id'], 'tier': c['tier'], 'text': c['text']}
                    for c in cells
                ]
                # Deterministic shuffle keyed on task_id keeps order stable across rebuilds.
                random.Random(tid).shuffle(options)
                for label, opt in zip(_LABELS, options):
                    opt['label'] = label
                tasks.append(
                    {
                        'task_id': tid,
                        'character_id': character['id'],
                        'character_name': character.get('full_name', character['id']),
                        'model': model,
                        'round': round_,
                        'character_sheet': sheet,
                        'options': options,
                    }
                )
    return tasks


def main() -> None:
    tasks = build()
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.TASKS_PATH, 'w', encoding='utf-8') as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + '\n')
    print(f'wrote {len(tasks)} comparison tasks to {config.TASKS_PATH}')


if __name__ == '__main__':
    main()
