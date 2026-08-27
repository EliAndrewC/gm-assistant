"""The REPL entry point (l7r.repl.shell) and the scripts/repl.py launcher."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from l7r.repl import COMMANDS, help_text, namespace
from l7r.repl import shell as mod
from l7r.repl.shell import build_namespace, main, run_snippet, setup_readline


def test_namespace_and_banner() -> None:
    ns = namespace()
    assert {'d10', 'xky', 'prob', 'name', 'place'} <= ns.keys()
    text = help_text()
    for command, _ in COMMANDS:
        assert command in text
    assert 'help_l7r()' in text


def test_build_namespace_has_help(capsys: pytest.CaptureFixture[str]) -> None:
    ns = build_namespace()
    ns['help_l7r']()
    assert help_text() in capsys.readouterr().out


def test_run_snippet_echoes_expressions(capsys: pytest.CaptureFixture[str]) -> None:
    ns = build_namespace()
    run_snippet('actual_xky(12, 4)', ns)
    assert capsys.readouterr().out == '(10, 6, 0)\n'
    run_snippet('x = 3', ns)
    assert ns['x'] == 3
    with pytest.raises(SyntaxError, match='incomplete'):
        run_snippet('if True:', ns)


def test_main_snippet_then_exit(capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[dict[str, Any]] = []
    assert main(['actual_xky(2,', '5)'], interact=lambda **kw: calls.append(kw)) == 0
    assert calls == []
    assert capsys.readouterr().out == '(2, 2, 0)\n'


def test_main_interactive_and_stay() -> None:
    calls: list[dict[str, Any]] = []
    ran: list[int] = []

    def fake_readline() -> bool:
        ran.append(1)
        return True

    assert main([], interact=lambda **kw: calls.append(kw), readline_setup=fake_readline) == 0
    assert calls[0]['banner'] == help_text()
    assert 'xky' in calls[0]['local']
    assert ran == [1]
    main(['percent()', '-i'], interact=lambda **kw: calls.append(kw), readline_setup=fake_readline)
    assert len(calls) == 2


def test_setup_readline_uses_history_file(tmp_path: Path) -> None:
    readline = pytest.importorskip('readline')
    history = tmp_path / 'hist'
    assert setup_readline(history) is True  # no file yet: OSError suppressed
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

    def test_main_on_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        launcher = _load_launcher()
        monkeypatch.setattr(launcher, 'in_container', lambda: False)
        seen: list[list[str]] = []

        def record(cmd: list[str]) -> int:
            seen.append(cmd)
            return 0

        monkeypatch.setattr(launcher.subprocess, 'call', record)
        assert launcher.main([]) == 0
        assert seen[0][1] == 'exec'

        def missing(cmd: list[str]) -> int:
            raise FileNotFoundError

        monkeypatch.setattr(launcher.subprocess, 'call', missing)
        assert launcher.main([]) == 1

    def test_in_container_is_true_here(self) -> None:
        launcher = _load_launcher()
        assert launcher.in_container() is (Path('/gm-assistant').is_dir())
