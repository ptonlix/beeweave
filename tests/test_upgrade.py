from pathlib import Path
from types import SimpleNamespace

from beeweave import cli
from beeweave import upgrade


def _method_path(tmp_path: Path, *parts: str) -> str:
    path = tmp_path.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# file\n", encoding="utf-8")
    return str(path)


def test_detect_install_method_uv_tool(tmp_path):
    package_file = _method_path(
        tmp_path,
        ".local",
        "share",
        "uv",
        "tools",
        "beeweave",
        "lib",
        "python3.10",
        "site-packages",
        "beeweave",
        "cli.py",
    )

    method = upgrade.detect_install_method(
        package_file=package_file,
        executable=str(tmp_path / ".local" / "share" / "uv" / "tools" / "beeweave" / "bin" / "python"),
        prefix=str(tmp_path / ".local" / "share" / "uv" / "tools" / "beeweave"),
    )

    assert method.kind == "uv_tool"
    assert upgrade.upgrade_command(method) == ["uv", "tool", "upgrade", "beeweave"]


def test_detect_install_method_source_checkout(tmp_path):
    repo = tmp_path / "beeweave"
    (repo / ".git").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='beeweave'\n", encoding="utf-8")
    package_file = _method_path(repo, "beeweave", "cli.py")

    method = upgrade.detect_install_method(package_file=package_file, executable=str(repo / ".venv" / "bin" / "python"))

    assert method.kind == "source"
    assert upgrade.upgrade_command(method) is None
    assert "git pull" in upgrade.manual_upgrade_hint(method)


def test_detect_install_method_pip(tmp_path):
    package_file = _method_path(tmp_path, "venv", "lib", "python3.10", "site-packages", "beeweave", "cli.py")

    method = upgrade.detect_install_method(package_file=package_file, executable=str(tmp_path / "venv" / "bin" / "python"))

    assert method.kind == "pip"
    assert upgrade.upgrade_command(method) == [
        str(tmp_path / "venv" / "bin" / "python"),
        "-m",
        "pip",
        "install",
        "--upgrade",
        "beeweave",
    ]


def test_detect_install_method_unknown(tmp_path):
    package_file = _method_path(tmp_path, "app", "beeweave", "cli.py")

    method = upgrade.detect_install_method(package_file=package_file, executable=str(tmp_path / "python"))

    assert method.kind == "unknown"
    assert upgrade.upgrade_command(method) is None


def test_version_check_statuses(monkeypatch):
    assert upgrade.check_version("0.2.0", "0.2.1").status == "update_available"
    assert upgrade.check_version("0.2.1", "0.2.1").status == "up_to_date"
    assert upgrade.check_version("0.3.0", "0.2.1").status == "up_to_date"

    def fail_fetch():
        raise OSError("offline")

    monkeypatch.setattr(upgrade, "fetch_latest_version", fail_fetch)
    result = upgrade.check_version("0.2.0")

    assert result.status == "unknown"
    assert result.latest is None
    assert "offline" in (result.error or "")


def test_install_state_serialization_and_named_profiles(tmp_path):
    installer = upgrade.InstallMethod("uv_tool", "/bin/python", "/pkg/cli.py", "uv")

    upgrade.record_setup_state(
        config_dir=tmp_path,
        profile="default",
        config_path=tmp_path / "config",
        project_dir=tmp_path / "workspace",
        vault_path=str(tmp_path / "workspace" / "vault"),
        workbench_path=str(tmp_path / "workspace" / "workbench"),
        agents=["codex"],
        global_extra=["beeweave-status"],
        no_global=False,
        no_project_local=False,
        copy=False,
        version="0.2.0",
        installer=installer,
    )
    upgrade.record_setup_state(
        config_dir=tmp_path,
        profile="work",
        config_path=tmp_path / "config.work",
        project_dir=None,
        vault_path="/vault",
        workbench_path="/workbench",
        agents=[],
        global_extra=[],
        no_global=True,
        no_project_local=True,
        copy=True,
        version="0.2.0",
    )

    state = upgrade.load_install_state(tmp_path)

    assert state["schema_version"] == 1
    assert state["installer"]["method"] == "uv_tool"
    assert sorted(state["profiles"]) == ["default", "work"]
    assert state["profiles"]["default"]["agents"] == ["codex"]
    assert state["profiles"]["work"]["copy"] is True


def test_replay_plan_skips_missing_project_directories(tmp_path):
    existing = tmp_path / "workspace"
    existing.mkdir()
    state = {
        "schema_version": 1,
        "profiles": {
            "default": {
                "config_path": str(tmp_path / "config"),
                "project_dir": str(existing),
                "vault_path": str(existing / "vault"),
                "workbench_path": str(existing / "workbench"),
                "agents": ["codex"],
                "global_extra": [],
                "no_global": False,
                "no_project_local": False,
                "copy": False,
                "last_setup_version": "0.2.0",
                "last_setup_at": "2026-07-08T17:40:00+08:00",
            },
            "stale": {
                "config_path": str(tmp_path / "config.stale"),
                "project_dir": str(tmp_path / "missing"),
                "vault_path": "/missing/vault",
                "workbench_path": "/missing/workbench",
                "agents": ["codex"],
            },
        },
    }
    upgrade.save_install_state(tmp_path, state)

    plan = upgrade.replay_plan(tmp_path)

    assert [entry.profile for entry in plan.entries] == ["default"]
    assert plan.entries[0].agents == ["codex"]
    assert plan.skipped[0][0] == "stale"
    assert "missing project directory" in plan.skipped[0][1]


def test_cmd_upgrade_check_reports_update_available(monkeypatch, capsys):
    monkeypatch.setattr(cli.upgrade, "check_version", lambda current: upgrade.VersionCheck(current, "9.9.9", "update_available"))

    assert cli.main(["upgrade", "--check"]) == 0

    output = capsys.readouterr().out
    assert "update available" in output
    assert "bwe upgrade" in output


def test_cmd_upgrade_runs_supported_installer_and_replays_profiles(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cli.upgrade, "check_version", lambda current: upgrade.VersionCheck(current, "9.9.9", "update_available"))
    monkeypatch.setattr(
        cli.upgrade,
        "detect_install_method",
        lambda **kwargs: upgrade.InstallMethod("uv_tool", "/bin/python", "/pkg/cli.py", "uv"),
    )
    seen: dict[str, object] = {}

    def fake_run(command):
        seen["command"] = command
        return upgrade.UpgradeResult(command, 0, "ok\n", "")

    monkeypatch.setattr(cli.upgrade, "run_upgrade_command", fake_run)

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade.save_install_state(
        tmp_path,
        {
            "schema_version": 1,
            "profiles": {
                "default": {
                    "config_path": str(tmp_path / "config"),
                    "project_dir": str(workspace),
                    "vault_path": str(workspace / "vault"),
                    "workbench_path": str(workspace / "workbench"),
                    "agents": ["codex"],
                    "global_extra": ["beeweave-status"],
                    "no_global": False,
                    "no_project_local": False,
                    "copy": False,
                    "last_setup_version": "0.2.0",
                    "last_setup_at": "2026-07-08T17:40:00+08:00",
                }
            },
        },
    )
    replayed: list[str] = []
    monkeypatch.setattr(cli, "_replay_setup", lambda entry: replayed.append(entry.profile) or 0)

    assert cli.main(["upgrade"]) == 0

    assert seen["command"] == ["uv", "tool", "upgrade", "beeweave"]
    assert replayed == ["default"]
    assert "Package upgrade completed" in capsys.readouterr().out


def test_cmd_upgrade_skips_replay_when_bundled_skills_unreadable(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(cli.upgrade, "check_version", lambda current: upgrade.VersionCheck(current, "9.9.9", "update_available"))
    monkeypatch.setattr(
        cli.upgrade,
        "detect_install_method",
        lambda **kwargs: upgrade.InstallMethod("uv_tool", "/bin/python", "/pkg/cli.py", "uv"),
    )
    monkeypatch.setattr(
        cli.upgrade,
        "run_upgrade_command",
        lambda command: upgrade.UpgradeResult(command, 0, "ok\n", ""),
    )
    monkeypatch.setattr(cli, "_bundled_skills_readable", lambda: (False, "missing package data"))
    monkeypatch.setattr(cli, "_replay_setup", lambda entry: (_ for _ in ()).throw(AssertionError("should not replay")))

    assert cli.main(["upgrade"]) == 0

    output = capsys.readouterr().out
    assert "Package data is not readable after upgrade" in output
    assert "Run: bwe setup" in output


def test_cmd_upgrade_unsupported_installer_does_not_run_command(monkeypatch, capsys):
    monkeypatch.setattr(cli.upgrade, "check_version", lambda current: upgrade.VersionCheck(current, "9.9.9", "update_available"))
    monkeypatch.setattr(
        cli.upgrade,
        "detect_install_method",
        lambda **kwargs: upgrade.InstallMethod("source", "/bin/python", "/repo/beeweave/cli.py", "source"),
    )
    monkeypatch.setattr(cli.upgrade, "run_upgrade_command", lambda command: (_ for _ in ()).throw(AssertionError("should not run")))

    assert cli.main(["upgrade"]) == 1

    output = capsys.readouterr().out
    assert "does not know how to upgrade" in output
    assert "Recommended" in output


def test_cmd_upgrade_installer_failure_stops_before_replay(monkeypatch):
    monkeypatch.setattr(cli.upgrade, "check_version", lambda current: upgrade.VersionCheck(current, "9.9.9", "update_available"))
    monkeypatch.setattr(
        cli.upgrade,
        "detect_install_method",
        lambda **kwargs: upgrade.InstallMethod("pip", "/bin/python", "/venv/site-packages/beeweave/cli.py", "pip"),
    )
    monkeypatch.setattr(
        cli.upgrade,
        "run_upgrade_command",
        lambda command: upgrade.UpgradeResult(command, 7, "", "failed\n"),
    )
    monkeypatch.setattr(cli, "_replay_setup", lambda entry: (_ for _ in ()).throw(AssertionError("should not replay")))

    assert cli.main(["upgrade"]) == 7


def test_cmd_setup_records_install_state(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    (root / "wiki" / "beeweave-query").mkdir(parents=True)
    (root / "wiki" / "beeweave-query" / "SKILL.md").write_text("---\nname: beeweave-query\n---\n", encoding="utf-8")
    (root / "wiki" / "beeweave-update").mkdir(parents=True)
    (root / "wiki" / "beeweave-update" / "SKILL.md").write_text("---\nname: beeweave-update\n---\n", encoding="utf-8")
    (root / "wiki" / "beeweave-ingest").mkdir(parents=True)
    (root / "wiki" / "beeweave-ingest" / "SKILL.md").write_text("---\nname: beeweave-ingest\n---\n", encoding="utf-8")

    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)
    monkeypatch.setattr(cli, "HOME", tmp_path)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")

    project = tmp_path / "workspace"
    assert cli.main(["setup", "--project", str(project), "--agents", "codex", "--global-extra", "none"]) == 0

    state = upgrade.load_install_state(tmp_path / ".beeweave")
    default = state["profiles"]["default"]
    assert default["project_dir"] == str(project.resolve())
    assert default["agents"] == ["codex"]
    assert default["no_project_local"] is False
