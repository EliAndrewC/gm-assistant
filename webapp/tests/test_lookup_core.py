"""Feature 218: the glossary, source tracking, links and the spending ledger."""

from __future__ import annotations

import datetime
import json
from pathlib import Path

import pytest

from l7r.lookup import glossary, links, sources
from l7r.lookup.ledger import Ledger

# --------------------------------------------------------------------------
# glossary
# --------------------------------------------------------------------------


def entry(**kw: object) -> str:
    raw: dict[str, object] = {
        'term': 'Gosonin',
        'kind': 'rank',
        'scope': 'wasp',
        'summary': 'Escorts under each Inspector.',
        'source': {'file': 'setting/l7r.md', 'section': 'The Wasp hierarchy'},
    }
    raw.update(kw)
    return json.dumps(raw)


class TestGlossary:
    def test_parses_every_field_and_renders_one_line(self) -> None:
        [e] = glossary.loads(
            entry(
                aliases=['Escort'],
                reading='gosonin',
                meaning='transport guard',
                related=['Metsuke'],
                link='https://example.org/wasp',
            )
        )
        assert e.aliases == ('Escort',)
        assert e.source.section == 'The Wasp hierarchy'
        assert glossary.line(e) == (
            'Gosonin (Escort; gosonin "transport guard") [rank, wasp]: Escorts under each '
            'Inspector. Related: Metsuke. Link: https://example.org/wasp'
        )

    def test_meaning_without_reading_and_a_bare_entry(self) -> None:
        [e] = glossary.loads(entry(meaning='transport guard'))
        assert glossary.line(e).startswith('Gosonin ("transport guard") [rank, wasp]')
        [bare] = glossary.loads(entry())
        assert glossary.line(bare) == 'Gosonin [rank, wasp]: Escorts under each Inspector.'

    def test_render_puts_wasp_then_world_then_other_campaigns(self) -> None:
        text = '\n'.join(
            [
                entry(term='A', scope='karmic-inquisitors'),
                entry(term='B', scope='world'),
                entry(term='C', scope='wasp'),
                '',
                entry(term='D', scope='wasp'),
            ]
        )
        rendered = glossary.render(glossary.loads(text)).splitlines()
        assert [r.split()[0] for r in rendered] == ['C', 'D', 'B', 'A']

    def test_links_collects_only_entries_with_one(self) -> None:
        es = glossary.loads(entry(term='A', link='https://x.org/a') + '\n' + entry(term='B'))
        assert glossary.links(es) == {'https://x.org/a'}

    @pytest.mark.parametrize(
        ('line', 'message'),
        [
            ('{nope', 'not JSON'),
            ('[1]', 'not a JSON object'),
            (entry(summary=''), 'missing summary'),
            (entry(kind='vibe'), "unknown kind 'vibe'"),
            (entry(scope='mars'), "unknown scope 'mars'"),
            (entry(link='www.x.org'), 'link must be an http'),
            (entry(source={'file': 'x'}), 'source must be'),
            (entry(aliases='Escort'), 'aliases must be a list'),
            (entry(related=['']), 'related must be a list'),
            (entry(reading=3), 'reading must be a string'),
        ],
    )
    def test_refuses_a_bad_line_and_says_where(self, line: str, message: str) -> None:
        with pytest.raises(glossary.GlossaryError, match=message) as info:
            glossary.loads('\n' + line, 'g.jsonl')
        assert str(info.value).startswith('g.jsonl:2:')

    def test_one_term_per_scope(self) -> None:
        glossary.loads(entry() + '\n' + entry(scope='world'))  # different scopes: fine
        with pytest.raises(
            glossary.GlossaryError, match="'gosonin' .wasp. already defined on line 1"
        ):
            glossary.loads(entry() + '\n' + entry(term='gosonin'))

    def test_the_shipped_glossary_loads(self) -> None:
        entries = glossary.load()
        assert entries, 'the glossary is empty'
        assert glossary.load(glossary.PATH) == entries


class TestShippedGlossary:
    """What the GM's five examples need is in the shipped glossary."""

    entries = glossary.load()
    text = glossary.render(entries)

    @pytest.mark.parametrize(
        'needle',
        [
            'haribugyo',
            'metsuke',
            'gosonin',
            'Tsuruchi Kyoma',
            'Bishamon',
            'Ebisu',
            'Ministry of Retainers',
            'https://waspbountyhunters.obsidianportal.com/wikis/imperial-bounties',
            'https://waspbountyhunters.obsidianportal.com/wikis/wasp-hierarchy',
        ],
    )
    def test_contains(self, needle: str) -> None:
        assert needle.casefold() in self.text.casefold()

    def test_every_link_points_at_the_campaign_or_the_sheet(self) -> None:
        for link in glossary.links(self.entries):
            assert link.startswith(
                (
                    'https://waspbountyhunters.obsidianportal.com/',
                    'https://l7r-character-sheet.fly.dev/',
                )
            ), link

    def test_no_numbers_or_procedures_rule_is_spot_checked(self) -> None:
        """The in/out rule (GM: a county magistrate's budget is out) cannot be fully
        tested - it is a judgment - but a koku figure in a summary is a red flag."""
        offenders = [e.term for e in self.entries if ' koku' in e.summary and e.kind == 'office']
        assert not offenders


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------

DOC = """intro text

# Book
lead

## Part
body one
```
# not a heading
```

### Detail
deep

## Part
again

# Other
## Part
elsewhere
"""


class TestSources:
    def test_split_names_sections_by_heading_path(self) -> None:
        names = [s.heading for s in sources.split(DOC, 'f.md')]
        assert names == [
            '(preamble)',
            'Book',
            'Book > Part',
            'Book > Part > Detail',
            'Book > Part #2',
            'Other > Part',
        ]

    def test_fenced_hash_does_not_cut_and_empty_sections_are_dropped(self) -> None:
        secs = {s.heading: s for s in sources.split(DOC + '\n# Empty\n', 'f.md')}
        assert '# not a heading' in secs['Book > Part'].text
        assert 'Empty' not in secs

    def test_digest_ignores_rewrapping(self) -> None:
        assert sources.digest('a  b\nc') == sources.digest('a b c') != sources.digest('a b d')

    def test_stale_and_mark(self) -> None:
        secs = sources.split(DOC, 'f.md')
        reviewed: dict[str, dict[str, str]] = {}
        assert len(sources.stale(secs, reviewed)) == 6
        marked = sources.mark(secs, reviewed, 'f.md', 'Book')
        assert len(marked) == 4
        assert [s.heading for s in sources.stale(secs, reviewed)] == ['(preamble)', 'Other > Part']
        changed = sources.split(DOC.replace('deep', 'deeper'), 'f.md')
        assert 'Book > Part > Detail' in [s.heading for s in sources.stale(changed, reviewed)]

    def test_corpus_reads_l7r_then_rules(self, tmp_path: Path) -> None:
        (tmp_path / 'setting').mkdir()
        (tmp_path / 'rules').mkdir()
        (tmp_path / 'setting' / 'l7r.md').write_text('# A\nx\n')
        (tmp_path / 'rules' / '02-b.md').write_text('# B\ny\n')
        (tmp_path / 'rules' / '01-a.md').write_text('# C\nz\n')
        files = [s.file for s in sources.corpus(tmp_path)]
        assert files == ['setting/l7r.md', 'rules/01-a.md', 'rules/02-b.md']

    def test_reviewed_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / 'r.json'
        assert sources.load_reviewed(path) == {}
        sources.save_reviewed({'b': {'y': '2', 'x': '1'}, 'a': {}}, path)
        assert list(json.loads(path.read_text())) == ['a', 'b']
        assert sources.load_reviewed(path) == {'a': {}, 'b': {'x': '1', 'y': '2'}}

    def test_cli(self, tmp_path: Path) -> None:
        said: list[str] = []
        path = tmp_path / 'r.json'

        def run(*argv: str) -> int:
            return sources.main(
                list(argv),
                load_corpus=lambda: sources.split(DOC, 'f.md'),
                reviewed_path=path,
                out=said.append,
            )

        assert run('stale') == 0
        assert said[-1].startswith('6 of 6 sections stale')
        assert run('mark', 'f.md', 'Book') == 0
        assert 'marked 4' in said[-1]
        assert run('mark', 'f.md', 'Nope') == 1
        assert 'nothing marked' in said[-1]
        assert run('mark', 'f.md') == 0
        assert 'marked 6' in said[-1]
        assert run('stale') == 0
        assert said[-1].startswith('0 of 6')
        assert run() == 2
        assert said[-1].startswith('usage')


# --------------------------------------------------------------------------
# links
# --------------------------------------------------------------------------

KYOMA = links.Person('Tsuruchi Kyoma', 'https://op/kyoma')
HIDEKI = links.Person('Tsuruchi Hideki', 'https://op/hideki')
FOUNDER = links.Person('Tsuruchi', 'https://op/tsuruchi')


class TestLinks:
    def test_roster_drops_gm_only_and_prefers_op_over_the_sheet(self) -> None:
        people = links.roster(
            [
                {
                    'name': 'Tsuruchi  Kyoma',
                    'character_url': 'https://op/kyoma',
                    'is_game_master_only': False,
                },
                {
                    'name': 'Secret Person',
                    'character_url': 'https://op/s',
                    'is_game_master_only': True,
                },
                {'name': 'No Url', 'character_url': ''},
                {'name': '  ', 'character_url': 'https://op/blank'},
            ],
            [('Tsuruchi Kyoma', 'https://sheet/1'), ('Kitsune  Moriko', 'https://sheet/17')],
        )
        assert people == [KYOMA, links.Person('Kitsune Moriko', 'https://sheet/17')]

    def test_full_name_then_unique_given_name_once_each(self) -> None:
        text = 'Your boss is Tsuruchi Kyoma. Kyoma likes sake; Kyoma and Hideki drink.'
        assert links.linkify(text, [KYOMA, HIDEKI]) == (
            'Your boss is [Tsuruchi Kyoma](https://op/kyoma). Kyoma likes sake; '
            'Kyoma and [Hideki](https://op/hideki) drink.'
        )

    def test_a_shared_given_name_is_not_linked(self) -> None:
        other = links.Person('Kyo Kyoma', 'https://op/kyo')
        assert links.linkify('Ask Kyoma.', [KYOMA, other]) == 'Ask Kyoma.'
        assert '[Kyo Kyoma](https://op/kyo)' in links.linkify('Ask Kyo Kyoma.', [KYOMA, other])

    def test_word_boundaries_existing_links_and_group_words(self) -> None:
        text = (
            'Kyomaru met [Tsuruchi Kyoma](https://op/kyoma) of the Tsuruchi lineage; '
            'Tsuruchi founded it.'
        )
        out = links.linkify(text, [KYOMA, FOUNDER])
        assert out == (
            'Kyomaru met [Tsuruchi Kyoma](https://op/kyoma) of the Tsuruchi lineage; '
            '[Tsuruchi](https://op/tsuruchi) founded it.'
        )

    def test_a_given_name_that_is_also_someones_full_name_is_not_a_given_form(self) -> None:
        founder_kin = links.Person('Bayushi Tsuruchi', 'https://op/bt')
        assert links.linkify('Tsuruchi rode.', [FOUNDER, founder_kin]) == (
            '[Tsuruchi](https://op/tsuruchi) rode.'
        )

    def test_empty_roster(self) -> None:
        assert links.linkify('Tsuruchi Kyoma', []) == 'Tsuruchi Kyoma'

    def test_scrub_keeps_known_and_drops_invented(self) -> None:
        text = (
            'See [the chart](https://op/wikis/wasp-hierarchy/) and https://op/kyoma. '
            'Also [made up](https://evil.example/x) and https://evil.example/y, ok?'
        )
        out, dropped = links.scrub(text, ['https://op/wikis/wasp-hierarchy', 'https://op/kyoma'])
        assert (
            out == 'See [the chart](https://op/wikis/wasp-hierarchy/) and https://op/kyoma. '
            'Also made up and , ok?'
        )
        assert dropped == ['https://evil.example/x', 'https://evil.example/y']

    def test_scrub_is_the_guard_and_it_fires(self) -> None:
        """Deleting the check in `scrub` must turn this red (constitution XVIII)."""
        _, dropped = links.scrub('[x](https://phish.example)', [])
        assert dropped == ['https://phish.example']


# --------------------------------------------------------------------------
# ledger
# --------------------------------------------------------------------------


class TestLedger:
    def make(self, tmp_path: Path, day: list[str], ceiling: float = 0.05) -> Ledger:
        return Ledger(tmp_path / 's.json', tmp_path / 'l.jsonl', ceiling, today=lambda: day[0])

    def test_ceiling_fires_and_rolls_over_at_midnight(self, tmp_path: Path) -> None:
        day = ['2026-10-17']
        ledger = self.make(tmp_path, day)
        assert ledger.spent() == 0.0
        assert ledger.allows()
        ledger.charge(0.03)
        assert ledger.allows()
        ledger.charge(0.03)
        assert ledger.spent() == pytest.approx(0.06)
        assert not ledger.allows()
        day[0] = '2026-10-18'
        assert ledger.spent() == 0.0
        assert ledger.allows()

    def test_unreadable_or_odd_spend_file_is_zero(self, tmp_path: Path) -> None:
        ledger = self.make(tmp_path, ['d'])
        (tmp_path / 's.json').write_text('not json')
        assert ledger.spent() == 0.0
        (tmp_path / 's.json').write_text('[1]')
        assert ledger.spent() == 0.0

    def test_default_day_is_today(self, tmp_path: Path) -> None:
        ledger = Ledger(tmp_path / 's.json', tmp_path / 'l.jsonl', 1.0)
        ledger.charge(0.25)
        assert json.loads((tmp_path / 's.json').read_text())['day'] == str(datetime.date.today())

    def test_log_appends_lines_with_the_day(self, tmp_path: Path) -> None:
        ledger = self.make(tmp_path, ['d'])
        ledger.log({'q': 'a'})
        ledger.log({'q': 'b'})
        rows = [json.loads(r) for r in (tmp_path / 'l.jsonl').read_text().splitlines()]
        assert rows == [{'day': 'd', 'q': 'a'}, {'day': 'd', 'q': 'b'}]
