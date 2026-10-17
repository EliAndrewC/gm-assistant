"""Feature 218: the evaluation runner's scoring, which is what makes it a regression test."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from l7r.lookup import eval as ev
from l7r.lookup.profiles import Profile


def q(**kw: Any) -> ev.Question:
    base: dict[str, Any] = {'id': 'x', 'question': 'q?'}
    base.update(kw)
    return ev.Question(**base)


class TestScore:
    def test_every_must_group_needs_one_alternative(self) -> None:
        question = q(must=(('Inspector', 'metsuke'), ('Escort', 'gosonin')))
        assert ev.score(question, 'Inspectors and GOSONIN').passed
        miss = ev.score(question, 'Inspectors only')
        assert not miss.passed
        assert miss.missing == ('Escort / gosonin',)

    def test_macrons_fold(self) -> None:
        assert ev.score(q(must=(('osano-wo',),)), 'Ōsano-Wo').facts

    def test_links_are_matched_against_addresses_only(self) -> None:
        question = q(links=(('wasp-hierarchy',),))
        linked = '[chart](https://op/wikis/wasp-hierarchy) or https://op/wikis/other'
        assert ev.score(question, linked).links
        assert not ev.score(question, 'the wasp-hierarchy page').links

    def test_unanswerable_passes_only_by_abstaining(self) -> None:
        question = q(answerable=False)
        assert ev.score(question, 'The notes do not cover that; ask the GM.').passed
        made_up = ev.score(question, 'His horse is called Thunder.')
        assert not made_up.passed
        assert made_up.missing == ('an abstention',)

    def test_brevity(self) -> None:
        assert ev.score(q(), 'a\nb\n\nc').brief
        assert not ev.score(q(), '\n'.join('x' * 8)).brief


class FakeLookup:
    def __init__(self, replies: dict[str, str]) -> None:
        self.replies = replies
        self.asked: list[tuple[str, str]] = []

    def answer(self, question: str, discord_id: str = '', asker: str = '') -> Any:
        self.asked.append((question, discord_id))
        text = self.replies.get(question, '')
        return type('A', (), {'text': text, 'cost': 0.001, 'seconds': 0.5, 'ok': bool(text)})()


QUESTIONS = [
    q(id='a', question='boss?', must=(('Kyoma',),), asker=2),
    q(id='b', question='horse?', answerable=False),
    q(id='c', question='broken?', must=(('x',),)),
]


class TestRun:
    def test_run_summarize_and_report(self) -> None:
        lookup = FakeLookup({'boss?': 'Tsuruchi Kyoma', 'horse?': 'Not covered; ask the GM.'})
        book = {2: Profile('832', 2, 'Tsuruchi Hidemasa', 'Monday Group')}
        results = ev.run(lookup, QUESTIONS, book, runs=2)  # type: ignore[arg-type]
        assert len(results) == 6
        assert lookup.asked[0] == ('boss?', '832')
        assert lookup.asked[1] == ('horse?', '')
        summary = ev.summarize(results)
        assert summary['correct_pct'] == 50.0
        assert summary['abstained_when_unanswerable_pct'] == 100.0
        assert summary['errors'] == 2
        assert summary['median_usd'] == 0.001
        text = ev.report('m', results, summary)
        assert '| correct_pct | 50.0 |' in text
        assert '**c** (broken?) missing x' in text
        assert '**a**' not in text

    def test_summarize_nothing(self) -> None:
        summary = ev.summarize([])
        assert summary['correct_pct'] == 0.0
        assert summary['median_seconds'] == 0.0


class TestMain:
    def test_usage(self) -> None:
        said: list[str] = []
        assert ev.main([], say=said.append) == 2
        assert said[0].startswith('usage')

    def test_writes_json_and_markdown_with_the_whole_model_name(self, tmp_path: Path) -> None:
        said: list[str] = []
        lookup = FakeLookup(
            {'what are our minions called?': 'Inspector (metsuke), Escort (gosonin)'}
        )
        code = ev.main(
            ['--model', 'gemini-3.1-flash-lite', '--only', 'gm-minions'],
            make=lambda model: lookup,  # type: ignore[arg-type,return-value]
            profiles=[],
            out_dir=tmp_path,
            today=lambda: '2026-10-17',
            say=said.append,
        )
        assert code == 0
        record = json.loads((tmp_path / 'gemini-3.1-flash-lite-2026-10-17.json').read_text())
        assert record['summary']['correct_pct'] == 100.0
        assert record['results'][0]['id'] == 'gm-minions'
        assert (tmp_path / 'gemini-3.1-flash-lite-2026-10-17.md').exists()
        assert 'correct_pct: 100.0' in said

    def test_the_shipped_question_set(self) -> None:
        questions = ev.load()
        assert len(questions) >= 60, 'the spec asks for at least 60 questions'
        assert len({x.id for x in questions}) == len(questions)
        verbatim = {
            'what are our minions called?',
            'Who is our boss?',
            'who are the fortunes that the crab worship?',
            'what are the imperial bounties?',
            'what is the WASP org chart?',
        }
        assert verbatim <= {x.question for x in questions}, "the GM's five examples, verbatim"
        assert any(not x.answerable for x in questions)
        for x in questions:
            assert x.must or x.links or not x.answerable, x.id


def test_load_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / 'q.jsonl'
    path.write_text('\n' + json.dumps({'id': 'a', 'question': 'q?', 'must': [['x']]}) + '\n\n')
    [only] = ev.load(path)
    assert only.must == (('x',),)
    assert only.answerable


def test_module_entry_point_prints_usage(monkeypatch: Any) -> None:
    import runpy
    import sys

    import pytest

    monkeypatch.setattr(sys, 'argv', ['l7r.lookup.eval'])
    with pytest.raises(SystemExit) as info:
        runpy.run_module('l7r.lookup.eval', run_name='__main__')
    assert info.value.code == 2
