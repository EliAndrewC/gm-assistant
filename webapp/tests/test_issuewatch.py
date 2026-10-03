"""Feature 215: issue watch. GitHub is a fake that honors ETags, so the conditional-request path
is exercised; nothing here touches the network or the real `~/.claude`."""

from __future__ import annotations

import hashlib
import io
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from l7r import issuewatch as iw

KEY = 'EliAndrewC/character-sheet#12'
NOW = 1_790_000_000.0


class Reply:
    def __init__(self, status: int, body: Any, etag: str) -> None:
        self.status = status
        self._body = json.dumps(body).encode()
        self.headers = {'ETag': etag}

    def __enter__(self) -> Reply:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class FakeGithub:
    """Issues and comments in memory; GETs carry ETags and honor If-None-Match."""

    def __init__(self) -> None:
        self.issues: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, str]] = []
        self.next_id = 100
        self.fail: int = 0

    def add_issue(self, key: str, title: str = 'Feature 214', body: str = 'the doc') -> None:
        self.issues[key] = {
            'title': title,
            'body': body,
            'state': 'open',
            'html_url': f'https://github.com/{key.replace("#", "/issues/")}',
            'comments': [],
        }

    def comment(self, key: str, body: str, login: str = 'EliAndrewC') -> dict[str, Any]:
        self.next_id += 1
        made = {
            'id': self.next_id,
            'body': body,
            'updated_at': f'2026-10-03T02:{self.next_id % 60:02d}:00Z',
            'html_url': f'https://github.com/x#c{self.next_id}',
            'user': {'login': login},
        }
        self.issues[key]['comments'].append(made)
        return made

    def __call__(self, request: urllib.request.Request) -> Reply:
        url = request.full_url.removeprefix(iw.API)
        self.calls.append((request.get_method(), url))
        if self.fail:
            raise urllib.error.HTTPError(url, self.fail, 'no', {}, io.BytesIO(b'{"message": "no"}'))  # type: ignore[arg-type]
        parts = url.split('?')[0].split('/')
        repo, number = f'{parts[2]}/{parts[3]}', parts[5] if len(parts) > 5 else ''
        key = f'{repo}#{number}'
        if request.get_method() == 'POST':
            data = json.loads(request.data or b'{}')  # type: ignore[arg-type]
            if url.endswith('/comments'):
                return Reply(201, self.comment(key, data['body']), '')
            new = len(self.issues) + 1
            self.add_issue(f'{repo}#{new}', data['title'], data['body'])
            return Reply(
                201, {'number': new, 'html_url': f'https://github.com/{repo}/issues/{new}'}, ''
            )
        issue = self.issues[key]
        body: Any = (
            issue['comments']
            if url.split('?')[0].endswith('/comments')
            else {k: v for k, v in issue.items() if k != 'comments'}
        )
        etag = '"' + hashlib.sha256(json.dumps(body).encode()).hexdigest()[:12] + '"'
        if request.get_header('If-none-match') == etag:
            raise urllib.error.HTTPError(url, 304, 'not modified', {}, io.BytesIO(b''))  # type: ignore[arg-type]
        return Reply(200, body, etag)


@pytest.fixture
def gh() -> FakeGithub:
    fake = FakeGithub()
    fake.add_issue(KEY)
    return fake


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / 'repo'
    (root / '.claude').mkdir(parents=True)
    (root / '.claude' / 'issue-watch.json').write_text(
        json.dumps(
            {
                'agent': 'gm-assistant',
                'token': {'ini': 'secrets.ini', 'section': 'github', 'key': 'push_pat'},
            }
        )
    )
    (root / 'secrets.ini').write_text('[github]\npush_pat = "tok-1"\n')
    monkeypatch.setenv('ISSUE_WATCH_DIR', str(tmp_path / 'state'))
    monkeypatch.setenv('CLAUDE_CODE_SESSION_ID', 'sid-1')
    monkeypatch.delenv('ISSUE_WATCH_TOKEN', raising=False)
    return root


def run(
    argv: list[str], gh: FakeGithub, root: Path | None, stdin: str = '', proc: str = 'pid:ns:7'
) -> tuple[int, str, str]:
    return iw.main(
        argv,
        stdin=lambda: stdin,
        opener=gh,
        cwd=lambda: Path('/anywhere'),
        root_of=lambda cwd: root,
        clock=lambda: NOW,
        process=lambda: proc,
    )


def hook(mode: str, gh: FakeGithub, sid: str = 'sid-1', **extra: Any) -> tuple[int, str, str]:
    payload = {'session_id': sid, 'hook_event_name': 'UserPromptSubmit', **extra.pop('payload', {})}
    return iw.hook(mode, payload, opener=gh, clock=extra.pop('clock', lambda: NOW + 100), **extra)


def other(gh: FakeGithub, text: str = 'Built B1-B4; deployed.') -> None:
    gh.comment(KEY, iw.sign('character-sheet', text))


class TestConfig:
    def test_ini_section_and_key(self, tmp_path: Path) -> None:
        path = tmp_path / 's.ini'
        path.write_text("x = 1\n[other]\npush_pat = wrong\n[github]\n  push_pat = 'right'\n")
        assert iw.read_secret(path, 'push_pat', 'github') == 'right'
        assert iw.read_secret(path, 'missing', 'github') == ''

    def test_env_file(self, tmp_path: Path) -> None:
        path = tmp_path / '.env'
        path.write_text('A=1\nGITHUB_TOKEN="abc"\n')
        assert iw.read_secret(path, 'GITHUB_TOKEN') == 'abc'

    def test_missing_file(self, tmp_path: Path) -> None:
        assert iw.read_secret(tmp_path / 'nope', 'k') == ''

    def test_settings_from_an_env_file_and_the_default_agent(self, tmp_path: Path) -> None:
        (tmp_path / '.claude').mkdir()
        (tmp_path / '.claude' / 'issue-watch.json').write_text(
            '{"token": {"env_file": ".env", "key": "GITHUB_TOKEN"}}'
        )
        (tmp_path / '.env').write_text('GITHUB_TOKEN=t\n')
        settings = iw.load_settings(tmp_path)
        assert (settings.agent, settings.token) == (tmp_path.name, 't')

    def test_the_env_override(self, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv('ISSUE_WATCH_TOKEN', 'override')
        assert iw.load_settings(repo).token == 'override'

    def test_no_opt_in_file_is_refused_with_the_fix(self, tmp_path: Path) -> None:
        with pytest.raises(iw.Refused, match='does not take part'):
            iw.load_settings(tmp_path)

    def test_no_token_is_refused(self, repo: Path) -> None:
        (repo / 'secrets.ini').write_text('[github]\n')
        with pytest.raises(iw.Refused, match='no GitHub token'):
            iw.load_settings(repo)

    def test_repo_root(self, tmp_path: Path) -> None:
        ok = lambda *a, **k: SimpleNamespace(returncode=0, stdout=f'{tmp_path}\n')  # noqa: E731
        bad = lambda *a, **k: SimpleNamespace(returncode=128, stdout='')  # noqa: E731
        assert iw.repo_root(tmp_path, run=ok) == tmp_path
        assert iw.repo_root(tmp_path, run=bad) is None
        assert iw.repo_root(Path(__file__).parent) is not None

    def test_state_dir_defaults_under_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('ISSUE_WATCH_DIR', raising=False)
        assert iw.state_dir() == Path.home() / '.claude' / 'issue-watch'


class TestGithubCall:
    def test_an_error_is_refused_with_its_status(self, gh: FakeGithub) -> None:
        gh.fail = 403
        with pytest.raises(iw.Refused, match='GitHub said 403'):
            iw.Github('t', gh).call('GET', '/repos/EliAndrewC/character-sheet/issues/12')

    def test_the_real_opener_is_the_default(self) -> None:
        assert iw.Github('t').opener is urllib.request.urlopen


class TestCommands:
    def test_start_counts_what_is_there_as_seen(self, repo: Path, gh: FakeGithub) -> None:
        other(gh, 'old news')
        code, out, _ = run(['start', KEY], gh, repo)
        assert code == 0
        assert 'Watching EliAndrewC/character-sheet#12' in out
        assert hook('deliver', gh) == (0, '', '')

    def test_status_and_stop(self, repo: Path, gh: FakeGithub) -> None:
        assert 'not watching anything' in run(['status'], gh, repo)[1]
        run(['start', KEY], gh, repo)
        gh.add_issue('EliAndrewC/character-sheet#13')
        run(['start', 'EliAndrewC/character-sheet#13'], gh, repo)
        assert run(['status'], gh, repo)[1] == (
            'gm-assistant watching EliAndrewC/character-sheet#12, EliAndrewC/character-sheet#13.'
        )
        assert (
            run(['stop', KEY], gh, repo)[1]
            == 'Stopped. Still watching: EliAndrewC/character-sheet#13.'
        )
        assert run(['stop'], gh, repo)[1] == 'Stopped. Still watching: nothing.'
        assert not iw.exists('sid-1')
        assert 'not watching' in run(['stop'], gh, repo)[1]

    def test_status_counts_what_is_waiting(self, repo: Path, gh: FakeGithub) -> None:
        run(['start', KEY], gh, repo)
        other(gh)
        with iw.locked('sid-1') as watch:
            assert watch is not None
            iw.check(watch, iw.Github('t', gh), NOW + 100)
        assert '1 item(s) waiting' in run(['status'], gh, repo)[1]

    def test_post_signs_the_comment(self, repo: Path, gh: FakeGithub) -> None:
        code, out, _ = run(['post', KEY], gh, repo, stdin='Requirements are ready.')
        assert code == 0
        assert out.startswith('Posted https://')
        body = gh.issues[KEY]['comments'][-1]['body']
        assert body.startswith('**[gm-assistant]** Requirements are ready.')
        assert '<!-- issue-watch agent=gm-assistant -->' in body

    def test_open_creates_and_watches(self, repo: Path, gh: FakeGithub) -> None:
        code, out, _ = run(
            ['open', 'EliAndrewC/character-sheet', 'Ishi boost'], gh, repo, stdin='See the doc.'
        )
        assert code == 0
        assert out.startswith('EliAndrewC/character-sheet#2 ')
        assert 'Watching EliAndrewC/character-sheet#2' in out

    @pytest.mark.parametrize(
        ('argv', 'message'),
        [
            (['frob'], 'commands:'),
            ([], 'commands:'),
            (['start'], 'missing its OWNER/REPO#N'),
            (['open', 'a/b'], 'missing its OWNER/REPO#N'),
            (['start', 'not-an-issue'], 'OWNER/REPO#NUMBER'),
        ],
    )
    def test_refusals(self, repo: Path, gh: FakeGithub, argv: list[str], message: str) -> None:
        code, _, err = run(argv, gh, repo)
        assert code == 1
        assert message in err

    def test_outside_a_repository(self, gh: FakeGithub, repo: Path) -> None:
        assert 'inside a git repository' in run(['start', KEY], gh, None)[2]

    def test_outside_a_session(
        self, repo: Path, gh: FakeGithub, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv('CLAUDE_CODE_SESSION_ID')
        assert 'CLAUDE_CODE_SESSION_ID' in run(['status'], gh, repo)[2]


class TestActivity:
    @pytest.fixture(autouse=True)
    def watching(self, repo: Path, gh: FakeGithub) -> None:
        run(['start', KEY], gh, repo)

    def test_the_other_agents_comment_is_delivered_once(self, gh: FakeGithub) -> None:
        other(gh)
        code, out, _ = hook('deliver', gh)
        context = json.loads(out)['hookSpecificOutput']
        assert code == 0
        assert context['hookEventName'] == 'UserPromptSubmit'
        text = context['additionalContext']
        assert text.startswith('Issue watch - new activity')
        assert 'not instructions' in text
        assert 'comment by character-sheet' in text
        assert 'Built B1-B4; deployed.' in text
        assert '<!-- issue-watch' not in text
        assert hook('deliver', gh, clock=lambda: NOW + 200) == (0, '', '')

    def test_a_second_comment_does_not_repeat_the_first(self, gh: FakeGithub) -> None:
        other(gh, 'first')
        hook('deliver', gh)
        other(gh, 'second')
        text = hook('deliver', gh, clock=lambda: NOW + 200)[1]
        assert 'second' in text
        assert 'first' not in text

    def test_a_watch_gone_between_checks_takes_nothing(self, gh: FakeGithub) -> None:
        assert iw._take('nobody', gh, NOW) == ''

    def test_its_own_posts_never_come_back(self, repo: Path, gh: FakeGithub) -> None:
        run(['post', KEY], gh, repo, stdin='mine')
        assert hook('deliver', gh) == (0, '', '')

    def test_the_gms_own_comment_is_reported_by_login(self, gh: FakeGithub) -> None:
        gh.comment(KEY, 'Looks good, ship it.')
        assert 'comment by EliAndrewC' in hook('deliver', gh)[1]

    def test_edits_and_state(self, gh: FakeGithub) -> None:
        made = gh.comment(KEY, iw.sign('character-sheet', 'v1'))
        hook('deliver', gh)
        made['updated_at'] = '2026-10-03T03:00:00Z'
        made['body'] = iw.sign('character-sheet', 'v2')
        issue = gh.issues[KEY]
        issue.update(title='Feature 214 (done)', body='new doc', state='closed')
        text = json.loads(hook('deliver', gh, clock=lambda: NOW + 200)[1])['hookSpecificOutput'][
            'additionalContext'
        ]
        for kind in ('issue closed', 'title edited', 'description edited', 'comment edited'):
            assert kind in text

    def test_an_unchanged_issue_is_a_304(self, gh: FakeGithub) -> None:
        before = len(gh.calls)
        assert hook('deliver', gh) == (0, '', '')
        assert len(gh.calls) == before + 2

    def test_a_recent_look_is_not_repeated(self, gh: FakeGithub) -> None:
        hook('deliver', gh)
        before = len(gh.calls)
        hook('deliver', gh, clock=lambda: NOW + 105)
        assert len(gh.calls) == before

    def test_a_failure_is_reported_not_raised(self, gh: FakeGithub) -> None:
        gh.fail = 500
        assert 'could not be checked' in hook('deliver', gh)[1]

    def test_a_lost_opt_in_file_is_reported(self, repo: Path, gh: FakeGithub) -> None:
        (repo / '.claude' / 'issue-watch.json').unlink()
        assert 'does not take part' in hook('deliver', gh)[1]

    def test_long_bodies_are_trimmed(self, gh: FakeGithub) -> None:
        other(gh, 'x' * (iw.TRIM + 50))
        assert 'x [...]' in hook('deliver', gh)[1]

    def test_nothing_is_dropped_unseen(self, gh: FakeGithub) -> None:
        for n in range(iw.SHOW_ITEMS + 2):
            other(gh, f'note {n}')
        text = json.loads(hook('deliver', gh)[1])['hookSpecificOutput']['additionalContext']
        assert 'Earlier, not shown in full:' in text
        assert 'note 0' not in text
        assert f'note {iw.SHOW_ITEMS + 1}' in text
        assert text.count('- [EliAndrewC/character-sheet#12] comment by character-sheet') == 2


class TestStopAndWait:
    @pytest.fixture(autouse=True)
    def watching(self, repo: Path, gh: FakeGithub) -> None:
        run(['start', KEY], gh, repo)

    def test_stop_blocks_once(self, gh: FakeGithub) -> None:
        other(gh)
        code, out, _ = hook('stop', gh)
        assert code == 0
        assert json.loads(out)['decision'] == 'block'
        assert hook('stop', gh, clock=lambda: NOW + 300) == (0, '', '')

    def test_stop_never_blocks_twice_in_a_row(self, gh: FakeGithub) -> None:
        other(gh)
        assert hook('stop', gh, payload={'stop_hook_active': True}) == (0, '', '')

    def test_wait_wakes_the_idle_session(self, gh: FakeGithub) -> None:
        naps: list[float] = []

        def sleep(seconds: float) -> None:
            naps.append(seconds)
            if len(naps) == 2:
                other(gh)

        code, out, err = hook(
            'wait', gh, sleep=sleep, parent=lambda: 99, clock=lambda: NOW + 100 * len(naps)
        )
        assert code == 2
        assert 'Built B1-B4' in err
        assert naps == [iw.WAIT_SECONDS, iw.WAIT_SECONDS]

    def test_the_gms_next_message_retires_the_wait(self, gh: FakeGithub) -> None:
        def sleep(seconds: float) -> None:
            hook('deliver', gh)

        assert hook('wait', gh, sleep=sleep, parent=lambda: 99) == (0, '', '')

    def test_a_gone_session_ends_the_wait(self, gh: FakeGithub) -> None:
        assert hook('wait', gh, sleep=lambda s: None, parent=lambda: 1) == (0, '', '')

    def test_a_stopped_watch_ends_the_wait(self, repo: Path, gh: FakeGithub) -> None:
        assert hook('wait', gh, sleep=lambda s: run(['stop'], gh, repo), parent=lambda: 99) == (
            0,
            '',
            '',
        )

    def test_an_unknown_mode_does_nothing(self, gh: FakeGithub) -> None:
        assert hook('frob', gh) == (0, '', '')


class TestOtherProjects:
    """SC-001: a session with no watch gets nothing, and GitHub is never asked."""

    def test_no_watch_no_output_no_call(self, repo: Path, gh: FakeGithub) -> None:
        for mode in ('deliver', 'stop', 'wait'):
            assert hook(mode, gh, sid='someone-else', process=lambda: 'pid:ns:999') == (0, '', '')
        assert gh.calls == []

    def test_no_watches_at_all_never_walks_proc(self, repo: Path, gh: FakeGithub) -> None:
        def boom() -> str:
            raise AssertionError('process looked up with no watch anywhere')

        assert iw.adopt('sid-x', boom) is False

    def test_bad_session_ids(self) -> None:
        assert iw.adopt('', lambda: 'p') is False
        assert iw.adopt('a/b', lambda: 'p') is False
        assert iw.exists('') is False

    def test_a_broken_hook_payload_still_exits_cleanly(self, gh: FakeGithub) -> None:
        assert iw.main(['hook', 'deliver'], stdin=lambda: '{not json', opener=gh) == (0, '', '')
        assert iw.main(['hook'], stdin=lambda: '', opener=gh) == (0, '', '')


class TestClear:
    """SC-004: a /clear mints a new session id in the same Claude process; the watch follows."""

    def test_activity_after_a_clear_is_delivered(self, repo: Path, gh: FakeGithub) -> None:
        run(['start', KEY], gh, repo, proc='pid:ns:7')
        other(gh)
        code, out, _ = hook('deliver', gh, sid='sid-2', process=lambda: 'pid:ns:7')
        assert code == 0
        assert 'Built B1-B4' in out
        assert iw.exists('sid-2')
        assert not iw.exists('sid-1')

    def test_another_process_does_not_adopt_it(self, repo: Path, gh: FakeGithub) -> None:
        run(['start', KEY], gh, repo, proc='pid:ns:7')
        assert iw.adopt('sid-2', lambda: 'pid:ns:8') is False
        assert iw.adopt('sid-2', lambda: '') is False

    def test_a_corrupt_watch_file_is_skipped(self, repo: Path, gh: FakeGithub) -> None:
        run(['start', KEY], gh, repo)
        (iw.state_dir() / 'watches' / 'junk.json').write_text('{')
        assert iw.adopt('sid-2', lambda: 'pid:ns:7') is True


class TestProcessKey:
    def _proc(self, tmp_path: Path, chain: list[tuple[int, str, int]]) -> Path:
        proc = tmp_path / 'proc'
        (proc / 'self' / 'ns').mkdir(parents=True)
        os.symlink('pid:[4026]', proc / 'self' / 'ns' / 'pid')
        for pid, name, parent in chain:
            (proc / str(pid)).mkdir()
            (proc / str(pid) / 'stat').write_text(f'{pid} ({name}) S {parent} 1 1')
        return proc

    def test_finds_the_claude_ancestor(self, tmp_path: Path) -> None:
        proc = self._proc(tmp_path, [(30, 'python3', 20), (20, 'bash', 10), (10, 'claude', 1)])
        assert iw.process_key(proc, 30) == 'pid:pid:[4026]:10'

    def test_none_above(self, tmp_path: Path) -> None:
        proc = self._proc(tmp_path, [(30, 'python3', 1)])
        assert iw.process_key(proc, 30) == ''

    def test_unreadable(self, tmp_path: Path) -> None:
        assert iw.process_key(tmp_path / 'nothing', 30) == ''

    def test_from_here(self) -> None:
        assert isinstance(iw.process_key(), str)


class TestInstall:
    def _home(self, tmp_path: Path) -> Path:
        home = tmp_path / 'home'
        (home / '.claude').mkdir(parents=True)
        other_hook = {'hooks': [{'type': 'command', 'command': 'bash memwatch-hook.sh wait'}]}
        (home / '.claude' / 'settings.json').write_text(
            json.dumps({'model': 'opus', 'hooks': {'Stop': [other_hook]}})
        )
        return home

    def _main(self, argv: list[str], home: Path) -> tuple[int, str, str]:
        return iw.main(argv, home=lambda: home)

    def test_install_check_and_idempotence(self, tmp_path: Path) -> None:
        home = self._home(tmp_path)
        code, out, _ = self._main(['install', '--check'], home)
        assert code == 1
        assert 'differs' in out
        assert 'Stop wait hook not registered' in out
        code, out, _ = self._main(['install'], home)
        assert code == 0
        assert 'UserPromptSubmit deliver, Stop stop, Stop wait' in out
        settings = json.loads((home / '.claude' / 'settings.json').read_text())
        assert settings['model'] == 'opus'
        assert settings['hooks']['Stop'][0]['hooks'][0]['command'] == 'bash memwatch-hook.sh wait'
        wait = settings['hooks']['Stop'][-1]['hooks'][0]
        assert wait['asyncRewake'] is True
        assert wait['timeout'] == 86400
        assert 'GUARD_EDIT_OK' in wait['command']
        assert (home / '.claude' / 'settings.json.bak-issue-watch').exists()
        installed = home / '.claude' / 'hooks' / 'issue_watch.py'
        assert installed.read_bytes() == Path(iw.__file__).read_bytes()
        assert 'none (already registered)' in self._main(['install'], home)[1]
        assert self._main(['install', '--check'], home)[0] == 0

    def test_install_into_a_home_with_no_settings(self, tmp_path: Path) -> None:
        home = tmp_path / 'bare'
        assert self._main(['install'], home)[0] == 0
        assert 'hooks' in json.loads((home / '.claude' / 'settings.json').read_text())
