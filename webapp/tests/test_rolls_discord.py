"""The Discord boundary: snowflakes, one-directional paging, and message shapes.

Tested against saved real messages and a fake fetch, never against the network.
"""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from l7r.repl.rolls import discord

FIXTURE = Path(__file__).parent / 'fixtures' / 'discord' / 'messages.json'


@pytest.fixture(scope='module')
def real_messages() -> list[dict[str, Any]]:
    return list(json.loads(FIXTURE.read_text())['messages'])


class TestSnowflake:
    def test_round_trips_through_discords_epoch(self) -> None:
        when = datetime(2026, 8, 12, 1, 53, tzinfo=UTC)
        produced = int(discord.snowflake(when))
        assert (produced >> 22) + discord.EPOCH_MS == int(when.timestamp() * 1000)

    def test_later_times_give_larger_ids(self) -> None:
        early = discord.snowflake(datetime(2026, 8, 12, 1, 0, tzinfo=UTC))
        late = discord.snowflake(datetime(2026, 8, 12, 2, 0, tzinfo=UTC))
        assert int(late) > int(early)

    def test_a_naive_datetime_is_refused(self) -> None:
        with pytest.raises(ValueError, match='timezone-aware'):
            discord.snowflake(datetime(2026, 8, 12, 1, 53))  # noqa: DTZ001


class TestBotToken:
    def test_reads_the_token(self, tmp_path: Path) -> None:
        secrets = tmp_path / 's.ini'
        secrets.write_text('[discord]\nbot_token = abc.def\n')
        assert discord.bot_token(secrets) == 'abc.def'

    def test_a_missing_token_explains_which_credential_is_wanted(self, tmp_path: Path) -> None:
        secrets = tmp_path / 's.ini'
        secrets.write_text('[discord]\nclient_id = 123\n')
        with pytest.raises(discord.DiscordUnavailable, match='different credential'):
            discord.bot_token(secrets)


def page(*ids: int, ts: str = '2026-08-12T01:53:39.000000+00:00') -> list[dict[str, Any]]:
    return [{'id': str(i), 'timestamp': ts, 'author': {'id': '1'}, 'attachments': []} for i in ids]


class TestMessagesSince:
    def test_pages_forward_until_a_short_page(self) -> None:
        calls: list[str] = []

        def fake(url: str, token: str, timeout: float) -> Any:
            calls.append(url)
            return page(3, 2, 1) if len(calls) == 1 else page(4)

        found = discord.messages_since(
            'c', datetime(2026, 8, 12, tzinfo=UTC), token='t', limit=3, fetch=fake
        )
        assert [m['id'] for m in found] == ['1', '2', '3', '4']
        # Oldest-first, and the cursor advances to the newest id of the last page.
        assert 'after=3' in calls[1]

    def test_stops_on_an_empty_page(self) -> None:
        def fake(url: str, token: str, timeout: float) -> Any:
            return []

        assert (
            discord.messages_since('c', datetime(2026, 8, 12, tzinfo=UTC), token='t', fetch=fake)
            == []
        )

    def test_resumes_from_a_message_id(self) -> None:
        seen: list[str] = []

        def fake(url: str, token: str, timeout: float) -> Any:
            seen.append(url)
            return []

        discord.messages_since('c', '999', token='t', fetch=fake)
        assert 'after=999' in seen[0]

    def test_the_far_end_is_bounded_in_python(self) -> None:
        # `before` and `after` are mutually exclusive in the API (research.md R9),
        # so `until` has to be applied here.
        def fake(url: str, token: str, timeout: float) -> Any:
            return [
                {'id': '1', 'timestamp': '2026-08-12T01:00:00+00:00', 'author': {}},
                {'id': '2', 'timestamp': '2026-08-12T09:00:00+00:00', 'author': {}},
            ]

        found = discord.messages_since(
            'c',
            datetime(2026, 8, 12, tzinfo=UTC),
            until=datetime(2026, 8, 12, 2, tzinfo=UTC),
            token='t',
            limit=2,
            max_pages=1,
            fetch=fake,
        )
        assert [m['id'] for m in found] == ['1']

    def test_max_pages_bounds_a_runaway(self) -> None:
        def fake(url: str, token: str, timeout: float) -> Any:
            return page(1, 2)

        found = discord.messages_since(
            'c', datetime(2026, 8, 12, tzinfo=UTC), token='t', limit=2, max_pages=3, fetch=fake
        )
        assert len(found) == 6


class TestFetchErrors:
    def _raise(self, exc: Exception) -> Any:
        def opener(*args: Any, **kwargs: Any) -> Any:
            raise exc

        return opener

    def test_403_explains_the_private_channel_case(self, monkeypatch: pytest.MonkeyPatch) -> None:
        error = urllib.error.HTTPError('u', 403, 'Forbidden', {}, None)  # type: ignore[arg-type]
        monkeypatch.setattr(urllib.request, 'urlopen', self._raise(error))
        with pytest.raises(discord.DiscordUnavailable, match='permission overrides'):
            discord._fetch('https://x', 't', 1.0)

    def test_other_http_errors_carry_the_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        error = urllib.error.HTTPError('u', 429, 'Too Many', {}, None)  # type: ignore[arg-type]
        monkeypatch.setattr(urllib.request, 'urlopen', self._raise(error))
        with pytest.raises(discord.DiscordUnavailable, match='429'):
            discord._fetch('https://x', 't', 1.0)

    def test_a_transport_failure_is_reported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(urllib.request, 'urlopen', self._raise(urllib.error.URLError('down')))
        with pytest.raises(discord.DiscordUnavailable, match='could not reach Discord'):
            discord._fetch('https://x', 't', 1.0)

    def test_a_good_response_is_decoded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class Fake:
            def read(self) -> bytes:
                return b'[{"id": "1"}]'

            def __enter__(self) -> Fake:
                return self

            def __exit__(self, *args: object) -> None:
                return None

        monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **k: Fake())
        assert discord._fetch('https://x', 't', 1.0) == [{'id': '1'}]


class TestMessageShapes:
    def test_parse_timestamp_is_utc_aware(self) -> None:
        when = discord.parse_timestamp('2026-08-12T01:53:39.000000+00:00')
        assert when.tzinfo is not None
        assert when.hour == 1

    def test_parse_timestamp_accepts_a_trailing_z(self) -> None:
        assert discord.parse_timestamp('2026-08-12T01:53:39Z').minute == 53

    def test_has_image_on_real_messages(self, real_messages: list[dict[str, Any]]) -> None:
        withimg = [m for m in real_messages if discord.has_image(m)]
        assert withimg, 'the fixture should carry image posts'
        assert all(m['attachments'] for m in withimg)

    def test_has_image_is_false_without_attachments(self) -> None:
        assert not discord.has_image({'attachments': []})
        assert not discord.has_image({})

    def test_a_non_image_attachment_does_not_count(self) -> None:
        assert not discord.has_image(
            {'attachments': [{'filename': 'notes.txt', 'content_type': 'text/plain'}]}
        )

    def test_author_helpers(self) -> None:
        message = {'author': {'id': '42', 'global_name': 'Queen of Rats', 'username': 'qor'}}
        assert discord.author_id(message) == '42'
        assert discord.author_name(message) == 'Queen of Rats'

    def test_author_helpers_fall_back_and_tolerate_absence(self) -> None:
        assert discord.author_name({'author': {'username': 'qor'}}) == 'qor'
        assert discord.author_id({}) == ''
        assert discord.author_name({}) == ''


def test_the_known_channels() -> None:
    assert discord.CHANNELS['monday'] == '832075590726844436'
    assert discord.CHANNELS['tuesday'] == '832075722516201492'
    # The scratch server, so a test run never touches the players' channels.
    assert discord.CHANNELS['test'] == '1543009572359241840'
