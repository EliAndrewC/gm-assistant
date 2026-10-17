"""Feature 218: profiles, the Gemini call, the prompt, and the lookup end to end."""

from __future__ import annotations

import io
import json
import re
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from l7r.lookup import bake, campaign, gemini, glossary, links, profiles, service
from l7r.lookup.ledger import Ledger
from l7r.lookup.profiles import Profile, Profiles

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'lookup'
RULES = Path('/host-l7r-repo/rules')

# --------------------------------------------------------------------------
# profiles
# --------------------------------------------------------------------------


def school_headings() -> list[str]:
    found: list[str] = []
    for name, level in (('04-schools.md', '###'), ('11-non_pc_schools.md', '##')):
        text = (RULES / name).read_text(encoding='utf-8')
        found += re.findall(rf'^{level} (.+)$', text, re.MULTILINE)
    return [h for h in found if not h.endswith('schools')]


class TestClanOfOrigin:
    @pytest.mark.skipif(not RULES.exists(), reason='needs the l7r rules mount')
    def test_every_school_in_the_rules_is_classified(self) -> None:
        """A new school in the rules must be given a clan (or listed as generic)
        here, or this goes red - it can never fall through to 'no clan' silently."""
        schools = school_headings()
        assert len(schools) > 25
        for school in schools:
            profiles.clan_of_school(school)  # raises for an unknown family

    @pytest.mark.parametrize(
        ('school', 'clan'),
        [
            ('Yogo Warden', 'Scorpion'),
            ('Isawa Ishi', 'Phoenix'),
            ('Matsu Bushi', 'Lion'),
            ('Kitsune Warden', 'Fox'),
            ('Mantis Wave-Treader', 'Mantis'),
            ('Courtier', None),
        ],
    )
    def test_examples(self, school: str, clan: str | None) -> None:
        assert profiles.clan_of_school(school) == clan

    def test_unknown_family_raises(self) -> None:
        with pytest.raises(ValueError, match='Zzz Dancer'):
            profiles.clan_of_school('Zzz Dancer')

    def test_profile_hides_an_unknown_school_as_unrecorded(self) -> None:
        p = Profile('1', 2, 'X', 'Monday Group', school='Zzz Dancer')
        assert p.clan_of_origin is None
        assert 'clan of origin not recorded' in p.describe()


class TestSheetPages:
    def test_parse_a_page_with_a_lineage_tooltip(self) -> None:
        found = profiles.parse_sheet((FIXTURES / 'sheet-2.html').read_text())
        assert found == {
            'school': 'Yogo Warden',
            'dan': 3,
            'player': 'Alex',
            'lineage': 'Tsuruchi lineage',
        }

    def test_parse_a_page_with_a_bare_lineage(self) -> None:
        found = profiles.parse_sheet((FIXTURES / 'sheet-14.html').read_text())
        assert found['school'] == 'Isawa Ishi'
        assert found['dan'] == 5
        assert found['lineage'] == 'Asako lineage'
        assert found['player'] == 'Marshall'

    def test_parse_nothing(self) -> None:
        assert profiles.parse_sheet('<html></html>') == {}

    def test_describe(self) -> None:
        p = Profile(
            '9',
            2,
            'Tsuruchi Hidemasa',
            'Monday Group',
            'Yogo Warden',
            3,
            'Tsuruchi lineage',
            'Alex',
        )
        assert p.describe() == (
            'Tsuruchi Hidemasa (character sheet https://l7r-character-sheet.fly.dev/characters/2); '
            'played by Alex; Yogo Warden school, 3rd Dan; Tsuruchi lineage; trained in a Scorpion '
            'school, so originally of the Scorpion Clan; plays in the Monday Group.'
        )
        bare = Profile('9', 3, 'Tsuruchi Jimen', 'Tuesday Group')
        assert bare.describe() == (
            'Tsuruchi Jimen (character sheet https://l7r-character-sheet.fly.dev/characters/3); '
            'clan of origin not recorded; plays in the Tuesday Group.'
        )
        assert profiles.from_json(p.to_json()) == p

    @pytest.mark.parametrize(
        ('n', 'text'), [(1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th'), (11, '11th'), (21, '21st')]
    )
    def test_ordinals(self, n: int, text: str) -> None:
        assert profiles._ordinal(n) == text

    def test_fetch_page_uses_the_public_url(self) -> None:
        seen: list[str] = []

        def opener(request: Any, timeout: float) -> io.BytesIO:
            seen.append(request.full_url)
            return io.BytesIO(b'<html>ok</html>')

        assert profiles.fetch_page(14, opener) == '<html>ok</html>'
        assert seen == ['https://l7r-character-sheet.fly.dev/characters/14']


SHEET_API = [
    {
        'id': 2,
        'name': 'Tsuruchi  Hidemasa',
        'is_npc': False,
        'owner_discord_id': '832',
        'gaming_group_name': 'Monday Group',
    },
    {
        'id': 14,
        'name': 'Asako Tadashi',
        'is_npc': False,
        'owner_discord_id': '316',
        'gaming_group_name': 'Monday Group',
    },
    {
        'id': 20,
        'name': 'Tsuruchi Yudai 勇大',
        'is_npc': False,
        'owner_discord_id': '213',
        'gaming_group_name': 'Tuesday Group',
    },
    {
        'id': 3,
        'name': 'Tsuruchi Jimen',
        'is_npc': False,
        'owner_discord_id': '153',
        'gaming_group_name': 'Tuesday Group',
    },
    {
        'id': 5,
        'name': 'Monk',
        'is_npc': False,
        'owner_discord_id': '153',
        'gaming_group_name': None,
    },
    {
        'id': 26,
        'name': 'Bayushi Koharu',
        'is_npc': True,
        'owner_discord_id': '1',
        'gaming_group_name': 'Monday Group',
    },
    {
        'id': 30,
        'name': 'Orphan',
        'is_npc': False,
        'owner_discord_id': None,
        'gaming_group_name': 'Monday Group',
    },
]


def pages(n: int) -> str:
    path = FIXTURES / f'sheet-{n}.html'
    if not path.exists():
        raise OSError('no page')
    return path.read_text()


class TestBuildAndRefresh:
    def test_build_keeps_campaign_pcs_only(self) -> None:
        built = profiles.build(SHEET_API, ['Monday Group', 'Tuesday Group'], pages)
        assert [(p.name, p.discord_id) for p in built] == [
            ('Tsuruchi Hidemasa', '832'),
            ('Asako Tadashi', '316'),
            ('Tsuruchi Yudai', '213'),
            ('Tsuruchi Jimen', '153'),
        ]
        assert built[0].school == 'Yogo Warden'
        assert built[3].school == ''

    def test_for_discord_refreshes_hourly_and_falls_back(self) -> None:
        now = [0.0]
        calls: list[int] = []
        html = {14: (FIXTURES / 'sheet-14.html').read_text()}

        def fetch(n: int) -> str:
            calls.append(n)
            if n not in html:
                raise OSError('down')
            return html[n]

        base = [
            Profile('316', 14, 'Asako Tadashi', 'Monday Group', 'Isawa Ishi', 4),
            Profile('153', 3, 'Tsuruchi Jimen', 'Tuesday Group', 'Akodo Bushi', 2),
        ]
        book = Profiles(base, fetch=fetch, clock=lambda: now[0])
        assert len(book) == 2
        assert book.all == base
        assert book.for_discord('316')[0].dan == 5
        assert calls == [14]
        book.for_discord('316')
        assert calls == [14]  # fresh for an hour
        now[0] = profiles.REFRESH_SECONDS
        book.for_discord('316')
        assert calls == [14, 14]
        assert book.for_discord('153')[0].dan == 2  # fetch failed: the baked profile stands
        assert book.for_discord('nobody') == []


# --------------------------------------------------------------------------
# gemini
# --------------------------------------------------------------------------


class Response(io.BytesIO):
    def __enter__(self) -> Response:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def opener_for(payload: dict[str, Any], seen: list[Any] | None = None) -> Any:
    def opener(request: Any, timeout: float) -> Response:
        if seen is not None:
            seen.append(request)
        return Response(json.dumps(payload).encode())

    return opener


GOOD: dict[str, Any] = {
    'candidates': [
        {'content': {'parts': [{'text': 'thinking...', 'thought': True}, {'text': ' Gosonin. '}]}}
    ],
    'usageMetadata': {
        'promptTokenCount': 1000,
        'cachedContentTokenCount': 800,
        'candidatesTokenCount': 10,
        'thoughtsTokenCount': 5,
    },
}


class TestGemini:
    def test_thinking_config(self) -> None:
        assert gemini.thinking_config('none') == {} == gemini.thinking_config('')
        assert gemini.thinking_config('budget0') == {'thinkingConfig': {'thinkingBudget': 0}}
        assert gemini.thinking_config('low') == {'thinkingConfig': {'thinkingLevel': 'low'}}

    def test_cost_bills_cached_tokens_at_the_cached_rate(self) -> None:
        usage = gemini.parse_usage(GOOD['usageMetadata'])
        price = gemini.Price(1.0, 0.1, 10.0)
        assert usage.cost(price) == pytest.approx((200 * 1.0 + 800 * 0.1 + 15 * 10.0) / 1e6)

    def test_generate_sends_the_key_in_a_header_and_skips_thoughts(self) -> None:
        seen: list[Any] = []
        ticks = iter([1.0, 3.5])
        reply = gemini.generate(
            key='K',
            model='m',
            system='S',
            prompt='P',
            thinking='minimal',
            opener=opener_for(GOOD, seen),
            clock=lambda: next(ticks),
        )
        assert reply.text == 'Gosonin.'
        assert reply.seconds == 2.5
        assert reply.usage.thoughts == 5
        request = seen[0]
        assert 'K' not in request.full_url
        assert request.get_header('X-goog-api-key') == 'K'
        body = json.loads(request.data)
        assert body['systemInstruction']['parts'][0]['text'] == 'S'
        assert body['generationConfig']['thinkingConfig'] == {'thinkingLevel': 'minimal'}

    def test_errors_never_carry_the_key(self) -> None:
        def http(request: Any, timeout: float) -> Any:
            raise urllib.error.HTTPError(request.full_url, 400, 'bad', {}, None)  # type: ignore[arg-type]

        def down(request: Any, timeout: float) -> Any:
            raise TimeoutError

        for opener, text in ((http, 'HTTP 400'), (down, 'TimeoutError')):
            with pytest.raises(gemini.GeminiError, match=text) as info:
                gemini.generate(key='SECRET', model='m', system='', prompt='', opener=opener)
            assert 'SECRET' not in str(info.value)

    def test_empty_reply_is_an_error(self) -> None:
        for payload, reason in (
            ({'candidates': [{'finishReason': 'SAFETY'}]}, 'SAFETY'),
            ({}, 'no candidates'),
        ):
            with pytest.raises(gemini.GeminiError, match=reason):
                gemini.generate(
                    key='k', model='m', system='', prompt='', opener=opener_for(payload)
                )


# --------------------------------------------------------------------------
# the prompt
# --------------------------------------------------------------------------


class TestCampaign:
    def test_system_is_stable_and_holds_the_glossary(self) -> None:
        assert campaign.system('G') == campaign.system('G')
        assert campaign.system('G').endswith('GLOSSARY\nG')
        assert 'Tsuruchi Kyoma' in campaign.system('G')

    def test_asker_forms(self) -> None:
        one = Profile('1', 2, 'A', 'Monday Group')
        two = Profile('1', 3, 'B', 'Monday Group')
        assert 'Not matched' in campaign.asker([])
        assert campaign.asker([one]).startswith('ASKER\nThe asker plays A (')
        assert 'more than one character' in campaign.asker([one, two])
        assert campaign.prompt('  who?  ', []).endswith('QUESTION\nwho?')


# --------------------------------------------------------------------------
# the service
# --------------------------------------------------------------------------

ENTRIES = glossary.loads(
    json.dumps(
        {
            'term': 'Wasp hierarchy',
            'kind': 'institution',
            'scope': 'wasp',
            'summary': 'The org chart.',
            'link': 'https://op/wikis/wasp-hierarchy',
            'source': {'file': 'f', 'section': 's'},
        }
    )
)
PEOPLE = [links.Person('Tsuruchi Kyoma', 'https://op/kyoma')]
SETTINGS = service.Settings(
    'm', 'none', gemini.Price(1.0, 0.1, 10.0), 0.05, 5.0, ('Monday Group',), key='k'
)


def fake(text: str, calls: list[dict[str, Any]] | None = None, fail: bool = False) -> Any:
    def generate(**kw: Any) -> gemini.Reply:
        if calls is not None:
            calls.append(kw)
        if fail:
            raise gemini.GeminiError('m: HTTP 500')
        return gemini.Reply(text, gemini.Usage(prompt=100, output=10), 1.25, kw['model'])

    return generate


class TestLookup:
    def make(
        self, tmp_path: Path, text: str, **kw: Any
    ) -> tuple[service.Lookup, Ledger, list[dict[str, Any]]]:
        calls: list[dict[str, Any]] = []
        ledger = Ledger(tmp_path / 's.json', tmp_path / 'l.jsonl', 0.05, today=lambda: 'd')
        book = Profiles(
            [Profile('832', 2, 'Tsuruchi Hidemasa', 'Monday Group')], fetch=lambda n: ''
        )
        lookup = service.Lookup(
            kw.pop('settings', SETTINGS),
            ENTRIES,
            PEOPLE,
            book,
            ledger,
            generate=fake(text, calls, **kw),
        )
        return lookup, ledger, calls

    def test_answer_links_people_keeps_glossary_links_and_drops_invented_ones(
        self, tmp_path: Path
    ) -> None:
        lookup, ledger, calls = self.make(
            tmp_path,
            'Your boss is Tsuruchi Kyoma. See [the chart](https://op/wikis/wasp-hierarchy) '
            'and [fake](https://evil.example).',
        )
        answer = lookup.answer('who is our boss?', '832', 'alex')
        assert answer.ok
        assert answer.dropped == ('https://evil.example',)
        assert answer.text == (
            'Your boss is [Tsuruchi Kyoma](https://op/kyoma). See [the chart]'
            '(https://op/wikis/wasp-hierarchy) and fake.'
        )
        assert 'The asker plays Tsuruchi Hidemasa' in calls[0]['prompt']
        assert calls[0]['system'] == lookup.system
        assert ledger.spent() == pytest.approx(answer.cost)
        assert answer.cost > 0
        row = json.loads((tmp_path / 'l.jsonl').read_text())
        assert row['characters'] == ['Tsuruchi Hidemasa']
        assert row['asker'] == 'alex'

    def test_no_key_no_call(self, tmp_path: Path) -> None:
        settings = service.Settings('m', 'none', SETTINGS.price, 1.0, 5.0, (), key='')
        lookup, _, calls = self.make(tmp_path, 'x', settings=settings)
        assert lookup.answer('q').text == service.NOT_CONFIGURED
        assert not calls

    def test_ceiling_stops_the_call(self, tmp_path: Path) -> None:
        lookup, ledger, calls = self.make(tmp_path, 'x')
        ledger.charge(1.0)
        answer = lookup.answer('q', '832')
        assert answer.text == service.CEILING
        assert not answer.ok
        assert not calls

    def test_failure_is_a_polite_reply_and_logged(self, tmp_path: Path) -> None:
        lookup, _, _ = self.make(tmp_path, 'x', fail=True)
        answer = lookup.answer('q')
        assert answer.text == service.FAILED
        assert not answer.ok
        assert 'HTTP 500' in (tmp_path / 'l.jsonl').read_text()

    def test_without_a_ledger(self, tmp_path: Path) -> None:
        book = Profiles([])
        ok = service.Lookup(SETTINGS, ENTRIES, PEOPLE, book, generate=fake('fine'))
        assert ok.answer('q').text == 'fine'
        bad = service.Lookup(SETTINGS, ENTRIES, PEOPLE, book, generate=fake('', fail=True))
        assert bad.answer('q').text == service.FAILED

    def test_hyphenate(self) -> None:
        em, en = chr(0x2014), chr(0x2013)
        assert service.hyphenate(f'a {em} b, c{em}d, 3{en}5') == 'a - b, c - d, 3-5'

    def test_trim_cuts_at_a_line(self) -> None:
        assert service.trim('short') == 'short'
        assert service.trim('aaaa\nbbbb\ncccc', 11) == 'aaaa\nbbbb'
        assert service.trim('x' * 20, 10) == 'x' * 10


DEFAULTS = """\
[lookup]
model = m1
campaign_groups = Monday Group, Tuesday Group
daily_ceiling_usd = 2.5
timeout_seconds = 9
[lookup_models]
m1 = minimal
[lookup_prices]
m1 = 0.3, 0.03, 2.5
m2 = 1, 0.1, 4
"""


class TestSettings:
    def test_load_reads_the_quoted_key_from_lookup_only(self, tmp_path: Path) -> None:
        (tmp_path / 'd.ini').write_text(DEFAULTS)
        (tmp_path / 's.ini').write_text(
            '[gemini]\napi_key = "MAIN"\n[lookup]\ngemini_api_key = "BOT"\n'
        )
        settings, defaults = service.load_settings(tmp_path / 'd.ini', tmp_path / 's.ini')
        assert settings.key == 'BOT'
        assert settings.model == 'm1'
        assert settings.thinking == 'minimal'
        assert settings.groups == ('Monday Group', 'Tuesday Group')
        assert settings.ceiling == 2.5
        assert settings.price == gemini.Price(0.3, 0.03, 2.5)
        other = settings.for_model('m2', defaults)
        assert other.thinking == 'none'
        assert other.price == gemini.Price(1.0, 0.1, 4.0)
        assert other.key == 'BOT'
        with pytest.raises(KeyError, match='no \\[lookup_prices\\] entry for m3'):
            settings.for_model('m3', defaults)

    def test_never_falls_back_to_the_main_key(self, tmp_path: Path) -> None:
        """The guard that keeps the portrait/backstory key off the box."""
        (tmp_path / 'd.ini').write_text(DEFAULTS)
        (tmp_path / 's.ini').write_text('[gemini]\napi_key = MAIN\n')
        assert service.load_settings(tmp_path / 'd.ini', tmp_path / 's.ini')[0].key == ''
        assert service.load_settings(tmp_path / 'd.ini', tmp_path / 'none.ini')[0].key == ''

    def test_the_real_defaults_load(self) -> None:
        settings, defaults = service.load_settings()
        assert settings.model in defaults['lookup_prices']

    def test_build_from_baked_data(self, tmp_path: Path) -> None:
        (tmp_path / 'd.ini').write_text(DEFAULTS)
        data = tmp_path / 'data'
        lookup = service.build(tmp_path / 'd.ini', tmp_path / 's.ini', data)
        assert lookup.people == []
        assert len(lookup.profiles) == 0
        assert data.is_dir()
        (data / 'roster.json').write_text(json.dumps([{'name': 'A B', 'url': 'https://x'}]))
        (data / 'profiles.json').write_text(
            json.dumps([Profile('1', 2, 'A B', 'Monday Group').to_json()])
        )
        (data / 'people.jsonl').write_text(
            json.dumps(
                {
                    'term': 'Zz Person',
                    'kind': 'person',
                    'scope': 'wasp',
                    'summary': 'baked one',
                    'source': {'file': 'f', 'section': 's'},
                }
            )
            + '\n'
        )
        again = service.build(tmp_path / 'd.ini', tmp_path / 's.ini', data)
        assert again.people == [links.Person('A B', 'https://x')]
        assert len(again.profiles) == 1
        assert 'Zz Person [person, wasp]: baked one' in again.system


# --------------------------------------------------------------------------
# bake
# --------------------------------------------------------------------------


class TestBake:
    def test_person_entries_from_taglines_and_tags(self) -> None:
        op: list[dict[str, Any]] = [
            {
                'name': 'Tsuruchi  Hideki',
                'slug': 'tsuruchi-hideki',
                'character_url': 'https://op/h',
                'tags': ['Wasp Clan', 'Escort'],
            },
            {
                'name': 'Tsuruchi Naomi',
                'slug': 'tsuruchi-naomi',
                'character_url': 'https://op/n',
                'tags': [],
            },
            {
                'name': 'Hidden',
                'slug': 'x',
                'character_url': 'https://op/x',
                'is_game_master_only': True,
            },
            {'name': 'Bare', 'slug': 'bare', 'character_url': 'https://op/b'},
            {'name': '', 'slug': 'none'},
        ]
        rows = bake.person_entries(
            op, {'tsuruchi-naomi': 'one of the crane wives of the Wasp chancellary'}
        )
        assert [r['term'] for r in rows] == ['Tsuruchi Hideki', 'Tsuruchi Naomi', 'Bare']
        assert rows[0]['summary'] == 'Tags: Wasp Clan, Escort.'
        assert rows[1]['summary'] == 'One of the crane wives of the Wasp chancellery.'
        assert rows[2]['summary'] == 'A character on the campaign wiki.'
        assert all(glossary.parse(r, 'x') for r in rows)

    def test_merge_keeps_hand_entries(self) -> None:
        hand = glossary.loads(
            json.dumps(
                {
                    'term': 'Tsuruchi Kyoma',
                    'aliases': ['Kyoma'],
                    'kind': 'person',
                    'scope': 'wasp',
                    'summary': 'hand',
                    'source': {'file': 'f', 'section': 's'},
                }
            )
        )
        baked = glossary.loads(
            '\n'.join(
                json.dumps(
                    {
                        'term': t,
                        'kind': 'person',
                        'scope': 'wasp',
                        'summary': 'baked',
                        'source': {'file': 'f', 'section': 's'},
                    }
                )
                for t in ('tsuruchi kyoma', 'Kyoma', 'Tsuruchi Hideki')
            )
        )
        assert [e.term for e in glossary.merge(hand, baked)] == [
            'Tsuruchi Kyoma',
            'Tsuruchi Hideki',
        ]

    def test_bake_writes_roster_and_profiles(self, tmp_path: Path) -> None:
        op = [
            {
                'name': 'Tsuruchi Kyoma',
                'slug': 'tsuruchi-kyoma',
                'character_url': 'https://op/kyoma',
                'is_game_master_only': False,
            }
        ]
        people, built = bake.bake(
            op, SHEET_API, ['Monday Group'], pages, tmp_path, {'tsuruchi-kyoma': 'the boss'}
        )
        assert json.loads((tmp_path / 'people.jsonl').read_text())['summary'] == 'The boss.'
        assert [p.name for p in built] == ['Tsuruchi Hidemasa', 'Asako Tadashi']
        assert people[0] == links.Person('Tsuruchi Kyoma', 'https://op/kyoma')
        assert people[1].url == 'https://l7r-character-sheet.fly.dev/characters/2'
        assert len(json.loads((tmp_path / 'roster.json').read_text())) == 3
        assert json.loads((tmp_path / 'profiles.json').read_text())[1]['school'] == 'Isawa Ishi'

    def test_main(self, tmp_path: Path) -> None:
        said: list[str] = []
        code = bake.main(
            sources=lambda: ([], SHEET_API, {}), fetch_page=pages, data=tmp_path, out=said.append
        )
        assert code == 0
        assert said[0].startswith('roster: 4 people; profiles: 4 PCs')
        assert any('Yogo Warden 3 Dan, Scorpion' in s for s in said)
        assert any('Tsuruchi Jimen: ? ? Dan, no clan' in s for s in said)
