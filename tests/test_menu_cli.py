"""CLI routing: bare `audit` opens the menu only on an interactive TTY."""

from audit import cli


def test_no_args_non_tty_prints_help_not_menu(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr(cli.menu, "run_menu",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("menu launched")))
    rc = cli.main([])
    assert rc == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_no_args_tty_launches_menu(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(cli.menu, "run_menu", lambda *a, **k: 7)
    assert cli.main([]) == 7


def test_json_flag_suppresses_menu_even_on_tty(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr(cli.menu, "run_menu",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("menu launched")))
    rc = cli.main(["--json"])
    assert rc == 0
