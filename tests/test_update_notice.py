import sys
from datetime import datetime, timedelta, timezone

from beeweave import cli, update_notice, upgrade


def test_check_for_update_notice_fetches_and_caches_latest(tmp_path, monkeypatch):
    package_file = tmp_path / "venv" / "lib" / "python3.10" / "site-packages" / "beeweave" / "cli.py"
    package_file.parent.mkdir(parents=True)
    package_file.write_text("# cli\n", encoding="utf-8")

    notice = update_notice.check_for_update_notice(
        current_version="0.3.0",
        config_dir=tmp_path,
        package_file=str(package_file),
        now=datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc),
        fetch_latest=lambda **kwargs: "0.3.1",
    )

    assert notice is not None
    assert notice.latest == "0.3.1"
    assert notice.install_method.kind == "pip"
    cache = update_notice.load_update_cache(tmp_path)
    assert cache["latest_version"] == "0.3.1"
    assert cache["last_checked_at"] == "2026-07-09T10:00:00+00:00"


def test_check_for_update_notice_uses_cache_before_interval(tmp_path):
    update_notice.save_update_cache(
        tmp_path,
        {
            "last_checked_at": "2026-07-09T10:00:00+00:00",
            "latest_version": "0.3.1",
        },
    )

    def fail_fetch(**kwargs):
        raise AssertionError("should not fetch before interval")

    notice = update_notice.check_for_update_notice(
        current_version="0.3.0",
        config_dir=tmp_path,
        package_file=__file__,
        now=datetime(2026, 7, 9, 11, 0, tzinfo=timezone.utc),
        fetch_latest=fail_fetch,
    )

    assert notice is not None
    assert notice.latest == "0.3.1"


def test_check_for_update_notice_silences_fetch_failure_and_throttles(tmp_path):
    def fail_fetch(**kwargs):
        raise OSError("offline")

    notice = update_notice.check_for_update_notice(
        current_version="0.3.0",
        config_dir=tmp_path,
        package_file=__file__,
        now=datetime(2026, 7, 9, 10, 0, tzinfo=timezone.utc),
        fetch_latest=fail_fetch,
    )

    assert notice is None
    cache = update_notice.load_update_cache(tmp_path)
    assert cache["last_checked_at"] == "2026-07-09T10:00:00+00:00"
    assert "latest_version" not in cache


def test_print_update_notice_uses_source_upgrade_hint(tmp_path, capsys):
    repo = tmp_path / "beeweave"
    (repo / ".git").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='beeweave'\n", encoding="utf-8")
    package_file = repo / "beeweave" / "cli.py"
    package_file.parent.mkdir()
    package_file.write_text("# cli\n", encoding="utf-8")

    notice = update_notice.UpdateNotice(
        current="0.3.0",
        latest="0.3.1",
        install_method=upgrade.detect_install_method(package_file=str(package_file)),
    )

    update_notice.print_update_notice(notice)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "⚠️  BeeWeave update available" in captured.err
    assert "source/editable" in captured.err
    assert "git pull" in captured.err
    assert "uv tool install --reinstall --editable ." in captured.err
    assert captured.err.endswith("\n\n")


def test_print_update_notice_ends_with_blank_line_for_upgrade_command(capsys):
    notice = update_notice.UpdateNotice(
        current="0.3.0",
        latest="0.3.1",
        install_method=upgrade.InstallMethod("pip", "/bin/python", "/pkg/cli.py", "site-packages install"),
    )

    update_notice.print_update_notice(notice)

    captured = capsys.readouterr()
    assert "Run: bwe upgrade" in captured.err
    assert captured.err.endswith("\n\n")


def test_maybe_print_update_notice_skips_non_tty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        update_notice,
        "check_for_update_notice",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("should not check without TTY")),
    )

    update_notice.maybe_print_update_notice(
        current_version="0.3.0",
        config_dir=tmp_path,
        package_file=__file__,
        stdout_is_tty=lambda: False,
    )

    assert capsys.readouterr().out == ""


def test_cli_prints_update_notice_for_info_but_not_machine_command(tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(
        cli.update_notice, "maybe_print_update_notice", lambda **kwargs: calls.append(kwargs["package_file"])
    )
    monkeypatch.setattr(cli, "_check_stale", lambda: None)
    monkeypatch.setattr(cli, "list_skills", lambda: [])
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)
    monkeypatch.setattr(cli, "skills_dir", lambda: tmp_path)

    assert cli.main(["info"]) == 0
    assert calls == [cli.__file__]

    sample = tmp_path / "sample.txt"
    sample.write_text("content\n", encoding="utf-8")
    assert cli.main(["cache-hash", str(sample)]) == 0
    assert calls == [cli.__file__]


def test_setup_prints_update_notice_before_profile_prompt(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")
    monkeypatch.setattr(cli.ui, "print_setup_banner", lambda version: print("setup banner"))
    monkeypatch.setattr(
        cli.update_notice, "maybe_print_update_notice", lambda **kwargs: print("⚠️  update notice", file=sys.stderr)
    )
    monkeypatch.setattr(
        cli.profiles,
        "choose_profile",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("profile prompt would start here")),
    )

    assert cli.main(["setup"]) == 1

    captured = capsys.readouterr()
    assert "setup banner" in captured.out
    assert "⚠️  update notice" in captured.err
    assert "profile prompt would start here" in captured.err


def test_profile_command_does_not_print_update_notice(tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")
    monkeypatch.setattr(cli.update_notice, "maybe_print_update_notice", lambda **kwargs: calls.append("notice"))

    assert cli.main(["profile", "set-default", "work"]) == 1
    assert calls == []


def test_uninstall_prints_update_notice_before_uninstall_flow(tmp_path, monkeypatch, capsys):
    calls: list[str] = []
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")
    monkeypatch.setattr(
        cli.update_notice,
        "maybe_print_update_notice",
        lambda **kwargs: calls.append("notice") or print("⚠️  update notice", file=sys.stderr),
    )
    monkeypatch.setattr(
        cli.uninstall,
        "run_uninstall",
        lambda ctx, args, selected_agents: print("uninstall flow") or 0,
    )

    assert cli.main(["uninstall", "--agents", "none"]) == 0

    captured = capsys.readouterr()
    assert calls == ["notice"]
    assert "⚠️  update notice" in captured.err
    assert "uninstall flow" in captured.out


def test_cli_prints_update_notice_after_info_stale_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "HOME", tmp_path)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")
    monkeypatch.setattr(cli, "list_skills", lambda: [])
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)
    monkeypatch.setattr(cli, "skills_dir", lambda: tmp_path)
    monkeypatch.setattr(
        cli.update_notice, "maybe_print_update_notice", lambda **kwargs: print("⚠️  update notice", file=sys.stderr)
    )

    assert cli.main(["info"]) == 0

    captured = capsys.readouterr()
    assert "setup has never been run" in captured.err
    assert "⚠️  update notice" in captured.err
    assert captured.err.index("setup has never been run") < captured.err.index("⚠️  update notice")


def test_cache_due_respects_interval():
    cache = {"last_checked_at": "2026-07-09T10:00:00+00:00"}

    assert not update_notice._cache_due(
        cache,
        now=datetime(2026, 7, 10, 9, 59, tzinfo=timezone.utc),
        interval=timedelta(hours=24),
    )
    assert update_notice._cache_due(
        cache,
        now=datetime(2026, 7, 10, 10, 0, tzinfo=timezone.utc),
        interval=timedelta(hours=24),
    )
