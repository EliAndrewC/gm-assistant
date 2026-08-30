"""The REPL entry point (l7r.repl.shell) and the scripts/repl.py launcher."""

import importlib.util
import subprocess
import sys
import threading
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from l7r.repl import BANNER, COMMANDS, help_text, namespace, undocumented
from l7r.repl import shell as mod
from l7r.repl.shell import TITLE, build_namespace, main, run_snippet, set_title, setup_readline


def test_namespace_and_banner() -> None:
    ns = namespace()
    assert {'d10', 'xky', 'prob', 'name', 'place'} <= ns.keys()
    # The STARTUP banner is a subset now; the full listing carries every row.
    text = help_text(full=True)
    for command, _ in COMMANDS:
        assert command in text
    assert 'help_l7r()' in text


def test_build_namespace_has_help(capsys: pytest.CaptureFixture[str]) -> None:
    """help_l7r() defaults to the FULL listing - the GM's "easy way to look
    something up or confirm for myself that something exists"."""
    ns = build_namespace()
    ns['help_l7r']()
    assert help_text(full=True) in capsys.readouterr().out


def test_help_l7r_can_still_show_the_short_form(capsys: pytest.CaptureFixture[str]) -> None:
    ns = build_namespace()
    ns['help_l7r'](False)
    assert help_text() in capsys.readouterr().out


def test_run_snippet_echoes_expressions(capsys: pytest.CaptureFixture[str]) -> None:
    ns = build_namespace()
    run_snippet('actual_xky(12, 4)', ns)
    assert capsys.readouterr().out == '(10, 6, 0)\n'
    run_snippet('x = 3', ns)
    assert ns['x'] == 3
    run_snippet('def f(n):\n    return n + 1\n\nfor i in range(2):\n    print(f(i))\nf(9)', ns)
    assert capsys.readouterr().out == '1\n2\n'  # a script: the last expression is NOT echoed
    with pytest.raises(SyntaxError):
        run_snippet('if True:', ns)


def test_main_snippet_then_exit(capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[dict[str, Any]] = []
    assert main(['actual_xky(2,', '5)'], interact=lambda **kw: calls.append(kw)) == 0
    assert calls == []
    assert capsys.readouterr().out == '(2, 2, 0)\n'


def test_main_interactive_and_stay(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    ran: list[int] = []
    warmed: list[str] = []
    monkeypatch.setattr(mod, 'warm_caches', lambda: warmed.append('ok'))

    def fake_readline(history: Path, ns: dict[str, Any]) -> bool:
        assert history == mod.HISTORY
        assert 'discern_honor' in ns
        ran.append(1)
        return True

    assert main([], interact=lambda **kw: calls.append(kw), readline_setup=fake_readline) == 0
    assert calls[0]['banner'] == help_text()
    assert 'xky' in calls[0]['local']
    assert ran == [1]
    main(['percent()', '-i'], interact=lambda **kw: calls.append(kw), readline_setup=fake_readline)
    assert len(calls) == 2
    for t in threading.enumerate():
        if t.name == 'l7r-cache-warm':
            t.join(5)
    assert warmed == ['ok', 'ok']  # the warm-up thread ran once per interactive start


def test_set_title_only_on_a_terminal() -> None:
    import io

    class Tty(io.StringIO):
        def isatty(self) -> bool:
            return True

    tty = Tty()
    assert set_title(out=tty) is True
    assert tty.getvalue() == f'\033]0;{TITLE}\007'
    assert TITLE == 'L7R repl >>>'
    piped = io.StringIO()
    assert set_title(out=piped) is False
    assert piped.getvalue() == ''


def test_setup_readline_uses_history_file(tmp_path: Path) -> None:
    readline = pytest.importorskip('readline')
    history = tmp_path / 'hist'
    assert setup_readline(history, build_namespace()) is True  # no file yet: OSError suppressed
    completer = readline.get_completer()
    assert completer is not None
    assert completer('discern_hon', 0) == 'discern_honor('
    assert completer('xk', 0) == 'xky('
    readline.add_history('xky(6, 3)')
    mod._write_history(history)
    assert 'xky(6, 3)' in history.read_text()
    assert setup_readline(history) is True


def _load_launcher() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / 'scripts' / 'repl.py'
    spec = importlib.util.spec_from_file_location('repl_launcher', path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestLauncher:
    def test_container_name_and_host_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        launcher = _load_launcher()
        monkeypatch.setenv('CONTAINER_PREFIX', 'zz')
        assert launcher.container_name() == f'zz-{launcher.REPO.name}'
        monkeypatch.setattr(launcher.shutil, 'which', lambda _: None)
        cmd = launcher.host_command(['d10()'])
        assert cmd[:3] == ['podman', 'exec', '-it']
        assert cmd[-2:] == ['/gm-assistant/scripts/repl.py', 'd10()']

    def test_main_inside_container(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        launcher = _load_launcher()
        monkeypatch.setattr(launcher, 'in_container', lambda: True)
        assert launcher.main(['actual_xky(1, 1)']) == 0
        assert capsys.readouterr().out == '(1, 1, 0)\n'
        assert str(launcher.WEBAPP) in sys.path

    def test_container_running_anchors_the_name(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A substring filter would match a sibling repo's container."""
        launcher = _load_launcher()
        seen: list[list[str]] = []

        def up(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            seen.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout='c0ffee\n', stderr='')

        monkeypatch.setattr(launcher.subprocess, 'run', up)
        assert launcher.container_running() is True
        assert seen[0][1:] == ['ps', '-q', '-f', f'name=^{launcher.container_name()}$']

        def down(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(cmd, 0, stdout='', stderr='')

        monkeypatch.setattr(launcher.subprocess, 'run', down)
        assert launcher.container_running() is False

    def test_start_container_runs_the_launcher_from_the_repo(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--no-shell, and cwd = the repo, which is how the launcher finds its config."""
        launcher = _load_launcher()
        seen: list[tuple[list[str], str | None]] = []

        def record(cmd: list[str], cwd: str | None = None) -> int:
            seen.append((cmd, cwd))
            return 0

        monkeypatch.setattr(launcher.subprocess, 'call', record)
        assert launcher.start_container() == 0
        assert seen == [([str(launcher.LAUNCHER), '--no-shell'], str(launcher.REPO))]
        assert 'not running' in capsys.readouterr().err

    def test_start_container_without_the_launcher_script(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        launcher = _load_launcher()
        monkeypatch.setattr(launcher, 'LAUNCHER', tmp_path / 'gone.sh')
        assert launcher.start_container() == 1
        assert 'missing' in capsys.readouterr().err

    def test_main_on_host_with_the_container_already_up(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        launcher = _load_launcher()
        monkeypatch.setattr(launcher, 'in_container', lambda: False)
        monkeypatch.setattr(launcher, 'container_running', lambda: True)
        monkeypatch.setattr(launcher, 'start_container', lambda: pytest.fail('should not launch'))
        seen: list[list[str]] = []

        def record(cmd: list[str]) -> int:
            seen.append(cmd)
            return 0

        monkeypatch.setattr(launcher.subprocess, 'call', record)
        assert launcher.main([]) == 0
        assert seen[0][1] == 'exec'

    def test_main_on_host_starts_the_container_first(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The motivating case: `repl` on a host whose container is not up."""
        launcher = _load_launcher()
        monkeypatch.setattr(launcher, 'in_container', lambda: False)
        monkeypatch.setattr(launcher, 'container_running', lambda: False)
        launched: list[bool] = []

        def launch() -> int:
            launched.append(True)
            return 0

        monkeypatch.setattr(launcher, 'start_container', launch)
        seen: list[list[str]] = []

        def record(cmd: list[str]) -> int:
            seen.append(cmd)
            return 0

        monkeypatch.setattr(launcher.subprocess, 'call', record)
        assert launcher.main([]) == 0
        assert launched == [True]
        assert seen[0][1] == 'exec'

    def test_main_on_host_when_the_launch_fails(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        launcher = _load_launcher()
        monkeypatch.setattr(launcher, 'in_container', lambda: False)
        monkeypatch.setattr(launcher, 'container_running', lambda: False)
        monkeypatch.setattr(launcher, 'start_container', lambda: 3)
        monkeypatch.setattr(launcher.subprocess, 'call', lambda cmd: pytest.fail('should not exec'))
        assert launcher.main([]) == 3
        assert 'could not start the container' in capsys.readouterr().err

    def test_main_on_host_without_a_container_runtime(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        launcher = _load_launcher()
        monkeypatch.setattr(launcher, 'in_container', lambda: False)

        def missing() -> bool:
            raise FileNotFoundError

        monkeypatch.setattr(launcher, 'container_running', missing)
        assert launcher.main([]) == 1
        assert 'not found' in capsys.readouterr().err

    def test_in_container_is_true_here(self) -> None:
        launcher = _load_launcher()
        assert launcher.in_container() is (Path('/gm-assistant').is_dir())


class TestBannerAndShortcuts:
    """The GM trimmed the banner on 2026-08-29 and asked for bare `m` / `f`."""

    def test_the_startup_banner_lists_only_what_still_needs_reminding(self) -> None:
        listed = [command for command, _ in COMMANDS if command in BANNER]
        assert listed == [
            'name()',
            'names(f, 3)',
            'village_name()',
            'cache_status()',
            'discern_honor("Otsuki", Jimen)',
            'begin_conversation("Otsuki")',
            'annotate()',
            'end_conversation()',
            'conversation_status()',
        ]

    def test_dropping_a_row_does_not_remove_the_function(self) -> None:
        """The banner is a reminder, not the namespace - these are all still usable."""
        ns = namespace()
        for unlisted in (
            'd10',
            'xky',
            'initiative',
            'percent',
            'prob',
            'place',
            'province_name',
            'town_name',
            'hamlet_name',
            'bank',
            'names',
            'abandon_conversation',
        ):
            assert unlisted in ns, f'{unlisted} was delisted, not deleted'

    def test_the_pc_constants_survive_the_trim(self) -> None:
        ns = namespace()
        assert 'Jimen' in ns
        assert 'TSURUCHI_JIMEN' in ns

    def test_m_and_f_are_bare_at_the_prompt(self) -> None:
        """So `names(f, 3)` works without the quotes."""
        ns = namespace()
        assert ns['m'] == 'm'
        assert ns['f'] == 'f'

    def test_the_shortcuts_actually_drive_names(self) -> None:
        ns = namespace()
        picked = ns['name'](ns['f'])
        assert isinstance(picked, str)
        assert picked


class TestFullListing:
    """`help_l7r()` shows everything; the startup banner shows the short list."""

    def test_the_startup_banner_is_a_strict_subset(self) -> None:
        short = help_text()
        full = help_text(full=True)
        assert len(short.splitlines()) < len(full.splitlines())
        for command in BANNER:
            assert command in short

    def test_the_full_listing_carries_the_rows_the_banner_hides(self) -> None:
        full = help_text(full=True)
        for hidden in ('d10()', 'xky(6, 3)', 'prob(6, 3)', 'place("village")'):
            assert hidden in full
            assert hidden not in help_text()

    def test_every_banner_row_is_a_real_command(self) -> None:
        """A typo in BANNER would silently drop a row from the startup banner."""
        assert {command for command, _ in COMMANDS} >= BANNER

    def test_nothing_in_the_namespace_is_invisible(self) -> None:
        """The full listing plus the derived tail must cover the whole namespace."""
        full = help_text(full=True)
        for entry in namespace():
            if entry.startswith('_'):
                continue
            assert entry in full, f'{entry} appears nowhere in help_l7r()'

    def test_undocumented_is_derived_not_listed(self) -> None:
        """A new export shows up without anyone remembering to add a row."""
        assert 'actual_xky' in undocumented()
        assert 'knack_rank' in undocumented()

    def test_it_matches_whole_identifiers_not_substrings(self) -> None:
        """`dist` was counted as documented because "mutually distinct" contains it.

        A loose match loses exactly the names most likely to be looked up.
        """
        assert 'dist' in undocumented()
        for covered in ('bank', 'PCS', 'province_name', 'abandon_conversation'):
            assert covered not in undocumented(), f'{covered} is named in a row'
