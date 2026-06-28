"""
Generate the candidate matrix for the synthesis prompt bakeoff.

For every cell of (character x tier x model x sample) this calls the synthesis
backend once and appends the result to data/candidates.jsonl. The run is
**resumable**: cells already present in candidates.jsonl are skipped, so a large
matrix can be filled in over several runs (and a crash mid-run loses nothing).

Usage (from webapp/):

    # See the matrix, token volumes, and call count without spending anything:
    python3 -m bakeoff.generate --dry-run

    # A cheap smoke run: 2 characters, 1 sample, all tiers and models:
    python3 -m bakeoff.generate --characters hideki,emi --samples 1

    # The full run (uses config defaults):
    python3 -m bakeoff.generate

``import l7r`` first is only to sidestep a pre-existing circular import in the
chargen package; the app itself launches the same way.
"""

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import l7r  # noqa: F401 - import for side effect: resolves chargen circular import

from bakeoff import briefs, config
from chargen import synthesis

_write_lock = threading.Lock()


def cell_id(character_id: str, tier: str, model: str, sample: int) -> str:
    """Stable id for one matrix cell, used for resumability and task building."""
    key = f'{character_id}|{tier}|{model}|{sample}'
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def load_characters() -> list[dict]:
    with open(config.CHARACTERS_PATH, encoding='utf-8') as f:
        return json.load(f)


def load_done_ids() -> set[str]:
    """candidate_ids already generated (so we can skip them on a resumed run)."""
    if not os.path.exists(config.CANDIDATES_PATH):
        return set()
    done = set()
    with open(config.CANDIDATES_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                done.add(json.loads(line)['candidate_id'])
    return done


def append_candidate(record: dict) -> None:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with _write_lock, open(config.CANDIDATES_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Generate the bakeoff candidate matrix.')
    p.add_argument('--characters', default='all', help='comma-separated ids, or "all"')
    p.add_argument('--tiers', default=','.join(config.TIERS), help='comma-separated tier ids')
    p.add_argument('--models', default=','.join(config.MODELS), help='comma-separated model ids')
    p.add_argument('--samples', type=int, default=config.SAMPLES, help='samples per cell')
    p.add_argument('--workers', type=int, default=4, help='concurrent API calls')
    p.add_argument('--dry-run', action='store_true', help='print the matrix and exit')
    return p.parse_args()


def select_characters(characters: list[dict], spec: str) -> list[dict]:
    if spec == 'all':
        return characters
    wanted = [s.strip() for s in spec.split(',') if s.strip()]
    by_id = {c['id']: c for c in characters}
    missing = [w for w in wanted if w not in by_id]
    if missing:
        sys.exit(f'unknown character id(s): {", ".join(missing)}')
    return [by_id[w] for w in wanted]


def dry_run(characters: list[dict], tiers: list[str], models: list[str], samples: int) -> None:
    tier_tokens = {t: len(briefs.build_tier(t)) // 4 for t in tiers}
    print('Tier input sizes (brief only, excludes per-character + instructions):')
    for t in tiers:
        print(f'  {t}: ~{tier_tokens[t]:>7} tokens')
    n_cells = len(characters) * len(tiers) * len(models) * samples
    print(
        f'\nMatrix: {len(characters)} characters x {len(tiers)} tiers '
        f'x {len(models)} models x {samples} samples = {n_cells} cells'
    )
    # Rough input-token volume = brief tokens summed across cells (the
    # per-character sheet and instructions add a small fixed overhead per call).
    total_in = sum(
        tier_tokens[t] for _ in characters for t in tiers for _ in models for _ in range(samples)
    )
    print(f'Approx brief input tokens across the whole run: ~{total_in:,}')
    print('(Per-call output is short, ~300-600 tokens. T3 dominates input cost.)')


def main() -> None:
    args = parse_args()
    characters = select_characters(load_characters(), args.characters)
    tiers = [t.strip() for t in args.tiers.split(',') if t.strip()]
    models = [m.strip() for m in args.models.split(',') if m.strip()]

    if args.dry_run:
        dry_run(characters, tiers, models, args.samples)
        return

    # Build (and cache) each tier's brief once up front.
    brief_text = {t: briefs.build_tier(t) for t in tiers}
    done = load_done_ids()

    jobs = []
    for character in characters:
        for tier in tiers:
            for model in models:
                for sample in range(args.samples):
                    cid = cell_id(character['id'], tier, model, sample)
                    if cid not in done:
                        jobs.append((cid, character, tier, model, sample))

    total = len(characters) * len(tiers) * len(models) * args.samples
    print(f'{total} cells total; {total - len(jobs)} already done; running {len(jobs)}.')

    counter = {'n': 0}

    def run_job(job: tuple) -> None:
        cid, character, tier, model, sample = job
        try:
            text = synthesis.synthesize(character, brief=brief_text[tier], model=model)
        except Exception as exc:  # noqa: BLE001 - log and let a re-run retry this cell
            print(f'  [FAIL] {character["id"]}/{tier}/{model}/{sample}: {exc}')
            return
        append_candidate(
            {
                'candidate_id': cid,
                'character_id': character['id'],
                'tier': tier,
                'model': model,
                'sample': sample,
                'text': text,
                'prompt_chars': len(brief_text[tier]),
                'ts': time.time(),
            }
        )
        with _write_lock:
            counter['n'] += 1
            print(f'  [{counter["n"]}/{len(jobs)}] {character["id"]}/{tier}/{model}/{sample}')

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run_job, jobs))

    print('done.')


if __name__ == '__main__':
    main()
