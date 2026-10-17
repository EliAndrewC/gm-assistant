"""The efficacy experiment (spec 218, Story 7): a fixed question set, scored mechanically.

    python3 -m l7r.lookup.eval --model gemini-3.1-flash-lite [--runs 2] [--only gm-]

Each question carries the facts a correct answer must contain (`must`, groups of
alternatives), the pages it must link (`links`), and whether the notes can
answer it at all. An unanswerable question passes when the reply says the notes
do not cover it. The run calls `Lookup.answer` - the exact path a player's
question takes, link post-processing included - and writes a JSON record plus a
markdown summary to the feature directory.

WHY MECHANICAL SCORING FIRST: it is free and reproducible, which is what makes
the set a regression test whenever the glossary or the model changes. Its blind
spot is an answer that is right in other words, so after a run Claude reads
every failing answer and fixes whichever is wrong - the glossary, the prompt,
or the question's grading - and says which (see this package's CLAUDE.md).
"""

from __future__ import annotations

import datetime
import json
import re
import statistics
import sys
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from l7r.lookup import service
from l7r.lookup.profiles import Profile

QUESTIONS = Path(__file__).resolve().parent / 'questions.jsonl'
RESULTS = Path(__file__).resolve().parents[4] / 'specs' / '218-lookup-command' / 'eval'

#: Phrases that mean "the notes do not say". Lowercase, after normalization.
ABSTAIN = (
    'do not cover',
    "don't cover",
    'does not cover',
    "doesn't cover",
    'not covered',
    'not in the notes',
    'notes do not',
    'no information',
    'not recorded',
    'ask the gm',
)

#: More lines than this is not "brief" (the instructions ask for at most five).
MAX_LINES = 6


@dataclass(frozen=True)
class Question:
    id: str
    question: str
    must: tuple[tuple[str, ...], ...] = ()
    links: tuple[tuple[str, ...], ...] = ()
    asker: int | None = None
    answerable: bool = True
    note: str = ''


def load(path: Path = QUESTIONS) -> list[Question]:
    out: list[Question] = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        out.append(
            Question(
                id=raw['id'],
                question=raw['question'],
                must=tuple(tuple(g) for g in raw.get('must', [])),
                links=tuple(tuple(g) for g in raw.get('links', [])),
                asker=raw.get('asker'),
                answerable=raw.get('answerable', True),
                note=raw.get('note', ''),
            )
        )
    return out


def normalize(text: str) -> str:
    """Lowercase, macrons and accents folded, so "Ōsano" and "osano" match."""
    folded = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in folded if not unicodedata.combining(c)).casefold()


_ADDRESS = re.compile(r'\((https?://[^)\s]+)\)|(https?://\S+)')


@dataclass(frozen=True)
class Score:
    facts: bool
    links: bool
    abstained: bool
    lines: int
    missing: tuple[str, ...] = field(default=())

    @property
    def passed(self) -> bool:
        return self.facts and self.links

    @property
    def brief(self) -> bool:
        return self.lines <= MAX_LINES


def score(q: Question, reply: str) -> Score:
    text = normalize(reply)
    addresses = [normalize(a or b) for a, b in _ADDRESS.findall(reply)]
    abstained = any(p in text for p in ABSTAIN)
    lines = len([ln for ln in reply.splitlines() if ln.strip()])
    if not q.answerable:
        return Score(abstained, True, abstained, lines, () if abstained else ('an abstention',))
    missing = [
        ' / '.join(group) for group in q.must if not any(normalize(alt) in text for alt in group)
    ]
    missing_links = [
        ' / '.join(group)
        for group in q.links
        if not any(normalize(alt) in a for alt in group for a in addresses)
    ]
    return Score(not missing, not missing_links, abstained, lines, tuple(missing + missing_links))


@dataclass
class Result:
    question: Question
    reply: str
    score: Score
    cost: float
    seconds: float
    ok: bool


def run(
    lookup: service.Lookup,
    questions: Iterable[Question],
    profiles: Mapping[int, Profile],
    *,
    runs: int = 1,
) -> list[Result]:
    """Ask every question `runs` times as its asker (by sheet id), and score each reply."""
    results: list[Result] = []
    for _ in range(runs):
        for q in questions:
            asker = profiles.get(q.asker) if q.asker is not None else None
            discord_id = asker.discord_id if asker else ''
            answer = lookup.answer(q.question, discord_id, asker=f'eval:{q.id}')
            results.append(
                Result(
                    q, answer.text, score(q, answer.text), answer.cost, answer.seconds, answer.ok
                )
            )
    return results


def summarize(results: list[Result]) -> dict[str, Any]:
    answerable = [r for r in results if r.question.answerable]
    unanswerable = [r for r in results if not r.question.answerable]
    costs = [r.cost for r in results if r.ok]
    seconds = sorted(r.seconds for r in results if r.ok)

    def pct(part: int, whole: int) -> float:
        return round(100.0 * part / whole, 1) if whole else 0.0

    return {
        'questions': len(results),
        'correct_pct': pct(sum(r.score.passed for r in answerable), len(answerable)),
        'facts_pct': pct(sum(r.score.facts for r in answerable), len(answerable)),
        'links_pct': pct(sum(r.score.links for r in answerable), len(answerable)),
        'abstained_when_unanswerable_pct': pct(
            sum(r.score.passed for r in unanswerable), len(unanswerable)
        ),
        'brief_pct': pct(sum(r.score.brief for r in results), len(results)),
        'errors': sum(not r.ok for r in results),
        'median_usd': round(statistics.median(costs), 5) if costs else 0.0,
        'mean_usd': round(statistics.fmean(costs), 5) if costs else 0.0,
        'median_seconds': round(statistics.median(seconds), 2) if seconds else 0.0,
        'p95_seconds': round(seconds[int(0.95 * (len(seconds) - 1))], 2) if seconds else 0.0,
    }


def report(model: str, results: list[Result], summary: Mapping[str, Any]) -> str:
    lines = [
        f'# Evaluation: {model}',
        '',
        '| measure | value |',
        '|---|---|',
        *(f'| {k} | {v} |' for k, v in summary.items()),
        '',
        '## Failures',
        '',
    ]
    for r in results:
        if r.score.passed:
            continue
        reply = r.reply.replace('\n', ' / ')
        lines.append(
            f'- **{r.question.id}** ({r.question.question}) missing {", ".join(r.score.missing)}: '
            f'{reply}'
        )
    return '\n'.join(lines) + '\n'


def main(
    argv: list[str],
    *,
    make: Callable[[str], service.Lookup] | None = None,
    profiles: Iterable[Profile] | None = None,
    out_dir: Path = RESULTS,
    today: Callable[[], str] = lambda: datetime.date.today().isoformat(),
    say: Callable[[str], None] = print,
) -> int:
    args = dict(zip(argv[::2], argv[1::2], strict=False))
    model = args.get('--model')
    if not model:
        say('usage: python3 -m l7r.lookup.eval --model MODEL [--runs N] [--only PREFIX]')
        return 2
    lookup = (make or _make)(model)
    book = {p.sheet_id: p for p in (profiles if profiles is not None else service.load_profiles())}
    questions = [q for q in load() if q.id.startswith(args.get('--only', ''))]
    results = run(lookup, questions, book, runs=int(args.get('--runs', '1')))
    summary = summarize(results)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Not Path.with_suffix: a model name has dots in it ('gemini-3.1-...'), so the
    # suffix would replace half the name (measured: it wrote 'gemini-3.json').
    stem = f'{model}-{today()}'
    (out_dir / f'{stem}.json').write_text(
        json.dumps(
            {
                'model': model,
                'summary': summary,
                'results': [
                    {
                        'id': r.question.id,
                        'question': r.question.question,
                        'reply': r.reply,
                        'passed': r.score.passed,
                        'missing': list(r.score.missing),
                        'lines': r.score.lines,
                        'usd': round(r.cost, 6),
                        'seconds': round(r.seconds, 2),
                    }
                    for r in results
                ],
            },
            indent=1,
            ensure_ascii=False,
        )
        + '\n',
        encoding='utf-8',
    )
    (out_dir / f'{stem}.md').write_text(report(model, results, summary), encoding='utf-8')
    for key, value in summary.items():
        say(f'{key}: {value}')
    return 0


def _make(model: str) -> service.Lookup:  # pragma: no cover - reads the real secrets
    """The bot's Lookup with `model`, keyed for a LOCAL evaluation run.

    Uses `[lookup] gemini_api_key` when present, else the GM's main `[gemini]`
    key. That fallback is for this command only, which runs on the GM's machine;
    the bot itself never falls back (service.load_settings), so the main key
    never reaches the box."""
    from configobj import ConfigObj

    lookup = service.build()
    _, defaults = service.load_settings()
    settings = lookup.settings.for_model(model, defaults)
    if not settings.key:
        secrets = ConfigObj(str(service.WEBAPP / 'development-secrets.ini'), encoding='utf-8')
        settings = replace(settings, key=str(secrets['gemini']['api_key']))
    lookup.settings = settings
    lookup.ledger = None
    return lookup


if __name__ == '__main__':  # pragma: no cover - the CLI entry point
    sys.exit(main(sys.argv[1:]))
