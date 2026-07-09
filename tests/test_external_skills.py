import json
from pathlib import Path

import pytest
from beeweave import cli, external


def _skill(path: Path, name: str) -> None:
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")


def test_parse_github_tree_source():
    source = external.parse_source("https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-url-to-markdown")

    assert source.source_url == "https://github.com/JimLiu/baoyu-skills.git"
    assert source.repo_key == "github.com/JimLiu/baoyu-skills"
    assert source.ref == "main"
    assert source.tree_path == "skills/baoyu-url-to-markdown"


def test_select_path_from_multi_skill_source(tmp_path):
    repo = tmp_path / "repo"
    _skill(repo / "skills" / "one", "one")
    _skill(repo / "skills" / "two", "two")

    selected = external.select_candidates(repo, path="skills/two")

    assert [candidate.name for candidate in selected] == ["two"]
    assert selected[0].subpath == "skills/two"


def test_multi_skill_source_requires_explicit_selection(tmp_path):
    repo = tmp_path / "repo"
    _skill(repo / "skills" / "one", "one")
    _skill(repo / "skills" / "two", "two")

    with pytest.raises(external.ExternalSkillError, match="multiple skills found"):
        external.select_candidates(repo)


def test_external_install_writes_manifest_and_links_project(tmp_path, monkeypatch):
    source_root = tmp_path / "source"
    _skill(source_root / "skills" / "demo-skill", "demo-skill")
    project = tmp_path / "project"
    (project / ".codex" / "skills").mkdir(parents=True)

    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")

    args = cli.build_parser().parse_args(
        [
            "external",
            "install",
            str(source_root),
            "--skill",
            "demo-skill",
            "--link-project",
            str(project),
        ]
    )

    assert args.func(args) == 0
    paths = external.external_paths(tmp_path / ".beeweave")
    manifest = json.loads(paths.manifest.read_text(encoding="utf-8"))
    record = manifest["skills"]["demo-skill"]
    assert record["subpath"] == "skills/demo-skill"
    assert record["linked_projects"] == [str(project.resolve())]
    assert (paths.skills / "demo-skill" / "SKILL.md").exists()
    assert (project / ".codex" / "skills" / "demo-skill").is_symlink()


def test_external_link_reports_real_directory_conflict(tmp_path):
    paths = external.external_paths(tmp_path / ".beeweave")
    external.init_external_storage(paths)
    skill_root = tmp_path / "skill"
    _skill(skill_root, "demo-skill")
    external.install_candidates(
        paths,
        source=external.parse_source(str(skill_root)),
        repo_root=skill_root,
        candidates=[external.SkillCandidate("demo-skill", skill_root, ".")],
        ref=None,
        commit=None,
    )
    project = tmp_path / "project"
    real = project / ".codex" / "skills" / "demo-skill"
    _skill(real, "demo-skill")

    result = external.link_external_skill(paths, "demo-skill", project, agents=cli.AGENTS)

    assert result.linked == []
    assert result.conflicts == [real]


def test_external_parser_supports_subcommands():
    parser = cli.build_parser()

    assert parser.parse_args(["external", "list"]).func is cli.cmd_external_list
    assert parser.parse_args(["external", "info", "demo"]).func is cli.cmd_external_info
    assert parser.parse_args(["external", "update"]).func is cli.cmd_external_update
    assert parser.parse_args(["external", "remove", "demo"]).func is cli.cmd_external_remove


def test_external_commands_do_not_run_stale_check(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "_check_stale", lambda: (_ for _ in ()).throw(AssertionError("stale check ran")))

    assert cli.main(["external", "list"]) == 0

    assert capsys.readouterr().err == ""


def test_external_list_uses_labeled_table(monkeypatch, tmp_path, capsys):
    paths = external.external_paths(tmp_path / ".beeweave")
    external.init_external_storage(paths)
    manifest = external.read_manifest(paths)
    manifest["skills"]["demo-skill"] = {
        "source": "https://github.com/example/demo.git",
        "subpath": "skills/demo-skill",
        "resolved_commit": "1234567890abcdef",
        "linked_projects": ["/project"],
    }
    external.write_manifest(paths, manifest)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")

    args = cli.build_parser().parse_args(["external", "list"])

    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert "External skills:" in output
    assert "Skill" in output
    assert "Source" in output
    assert "Subpath" in output
    assert "Commit" in output
    assert "Project links" in output
    assert "demo-skill" in output
    assert "1234567890ab" in output
    assert "Details: bwe external info <skill>" in output


def test_external_list_empty_state_uses_clear_help(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")

    args = cli.build_parser().parse_args(["external", "list"])

    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert "No external skills installed" in output
    assert "bwe external install <source> --skill <name> --link-project ." in output


def test_external_info_uses_readable_detail_view(monkeypatch, tmp_path, capsys):
    paths = external.external_paths(tmp_path / ".beeweave")
    external.init_external_storage(paths)
    manifest = external.read_manifest(paths)
    manifest["skills"]["demo-skill"] = {
        "source": "https://github.com/example/demo.git",
        "source_raw": "example/demo",
        "repo_dir": str(tmp_path / "repo"),
        "subpath": "skills/demo-skill",
        "ref": "main",
        "resolved_commit": "1234567890abcdef",
        "install_path": str(paths.skills / "demo-skill"),
        "license": "MIT",
        "installed_at": "2026-07-09T00:00:00+00:00",
        "linked_projects": ["/project/a", "/project/b"],
    }
    external.write_manifest(paths, manifest)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")

    args = cli.build_parser().parse_args(["external", "info", "demo-skill"])

    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert "External skill info" in output
    assert "Skill:" in output
    assert "demo-skill" in output
    assert "Source:" in output
    assert "https://github.com/example/demo.git" in output
    assert "Subpath:" in output
    assert "skills/demo-skill" in output
    assert "Install path:" in output
    assert str(paths.skills / "demo-skill") in output
    assert "Commit:" in output
    assert "1234567890abcdef" in output
    assert "License:" in output
    assert "MIT" in output
    assert "Installed at:" in output
    assert "2026-07-09T00:00:00+00:00" in output
    assert "Linked projects:" in output
    assert "/project/a" in output
    assert "/project/b" in output


def test_external_info_missing_skill_stays_nonzero(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    args = cli.build_parser().parse_args(["external", "info", "missing-skill"])

    with pytest.raises(RuntimeError, match="external skill is not installed: missing-skill"):
        args.func(args)
