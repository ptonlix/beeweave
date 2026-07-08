from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from beeweave import cli


ROOT = Path(__file__).resolve().parents[1]


def _skill(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text("---\nname: test\n---\n", encoding="utf-8")


def test_list_skills_supports_grouped_layout(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "wiki" / "beeweave-update")
    _skill(root / "workbench" / "beeweave-article-writer")

    monkeypatch.setattr(cli, "skills_dir", lambda: root)

    assert cli.list_skills() == ["beeweave-article-writer", "beeweave-query", "beeweave-update"]


def test_install_skills_flattens_grouped_layout(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "workbench" / "beeweave-article-writer")
    target = tmp_path / "agent-skills"

    monkeypatch.setattr(cli, "skills_dir", lambda: root)

    count = cli.install_skills(target, "test", mode="copy", quiet=True)

    assert count == 2
    assert (target / "beeweave-query" / "SKILL.md").exists()
    assert (target / "beeweave-article-writer" / "SKILL.md").exists()
    assert not (target / "wiki").exists()
    assert not (target / "workbench").exists()


def test_iter_skill_dirs_rejects_duplicate_names(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "shared")
    _skill(root / "workbench" / "shared")

    monkeypatch.setattr(cli, "skills_dir", lambda: root)

    with pytest.raises(RuntimeError, match="duplicate skill names"):
        cli.iter_skill_dirs()


def test_project_layout_initializers_create_fixed_skeleton(tmp_path):
    vault = tmp_path / "vault"
    workbench = tmp_path / "workbench"

    cli.init_vault_layout(vault)
    cli.init_workbench_layout(workbench)

    for rel in cli.VAULT_DIRS:
        assert (vault / rel).is_dir()
        assert (vault / rel / ".gitkeep").exists()
    for rel in cli.WORKBENCH_DIRS:
        assert (workbench / rel).is_dir()
        assert (workbench / rel / ".gitkeep").exists()

    assert not (vault / "_raw").exists()
    assert not (vault / "journal").exists()
    assert not (vault / "_archived").exists()
    assert (vault / "_meta").is_dir()
    assert (workbench / "inbox" / "captures").is_dir()
    assert (workbench / "inbox" / "web").is_dir()
    assert (workbench / "inbox" / "archived").is_dir()
    assert (workbench / "inbox" / "rejected").is_dir()
    assert not (workbench / "inbox" / "_archived").exists()


def test_readme_runtime_layout_lists_generated_directories():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for rel in cli.VAULT_DIRS:
        assert f"{rel.split('/')[-1]}/" in readme
    for rel in cli.WORKBENCH_DIRS:
        assert f"{rel.split('/')[-1]}/" in readme


def test_write_project_env_does_not_overwrite_existing_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("BEEWEAVE_VAULT_PATH=/custom\n", encoding="utf-8")

    cli.write_project_env(tmp_path)

    assert env.read_text(encoding="utf-8") == "BEEWEAVE_VAULT_PATH=/custom\n"


def test_parse_agent_list_supports_all_none_and_commas():
    assert cli._parse_agent_list("claude,codex") == ["claude", "codex"]
    assert cli._parse_agent_list("none") == []
    assert cli._parse_agent_list("all") == list(cli.AGENTS)


def test_parse_menu_selection_supports_numbers_and_defaults():
    assert cli._parse_menu_selection("") == list(cli.DEFAULT_AGENTS)
    assert cli._parse_menu_selection("1 9") == ["claude", "codex"]
    assert cli._parse_menu_selection("none") == []


def test_install_project_only_selected_agent_dirs(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "workbench" / "beeweave-article-writer")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)

    cli.install_project(tmp_path, mode="copy", agents=["claude"])

    assert (tmp_path / ".claude" / "skills" / "beeweave-query" / "SKILL.md").exists()
    assert not (tmp_path / ".cursor").exists()
    assert not (tmp_path / ".agents").exists()
    assert (tmp_path / "vault" / "concepts").is_dir()
    assert (tmp_path / "workbench" / "library").is_dir()


def test_install_project_supports_codex_project_skills(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "workbench" / "beeweave-article-writer")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)

    cli.install_project(tmp_path, mode="copy", agents=["codex"])

    assert (tmp_path / ".codex" / "skills" / "beeweave-query" / "SKILL.md").exists()
    assert (tmp_path / ".codex" / "skills" / "beeweave-article-writer" / "SKILL.md").exists()


def test_install_project_uses_bootstrap_agents_template_and_aliases(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    boot = tmp_path / "bootstrap-root"
    _skill(root / "wiki" / "beeweave-query")
    (boot / "bootstrap").mkdir(parents=True)
    (boot / "bootstrap" / "AGENTS.md").write_text("USER PROJECT CONTEXT\n", encoding="utf-8")

    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: boot)

    cli.install_project(tmp_path / "project", mode="copy", agents=["claude", "gemini", "hermes"])

    project = tmp_path / "project"
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == "USER PROJECT CONTEXT\n"
    assert (project / "CLAUDE.md").is_symlink()
    assert (project / "GEMINI.md").is_symlink()
    assert (project / "HERMES.md").is_symlink()
    assert not (project / ".hermes.md").exists()
    assert (project / "CLAUDE.md").readlink() == Path("AGENTS.md")
    assert (project / "GEMINI.md").readlink() == Path("AGENTS.md")
    assert (project / "HERMES.md").readlink() == Path("AGENTS.md")


def test_setup_summary_points_to_direct_skill_usage(tmp_path, monkeypatch, capsys):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "wiki" / "beeweave-update")
    _skill(root / "wiki" / "beeweave-ingest")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")

    args = cli.build_parser().parse_args([
        "setup",
        "--vault",
        str(tmp_path / "vault"),
        "--project",
        str(tmp_path / "project"),
        "--agents",
        "none",
        "--no-global",
    ])

    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert "/beeweave-ingest workbench/inbox" in output
    assert "/beeweave-query what do I know about ..." in output
    assert 'Say: "set up my wiki"' not in output


def test_setup_defaults_to_project_vault_without_prompt(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "wiki" / "beeweave-update")
    _skill(root / "wiki" / "beeweave-ingest")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)

    def fail_input(prompt=""):
        raise AssertionError(f"setup should not prompt for vault path: {prompt}")

    monkeypatch.setattr("builtins.input", fail_input)
    project = tmp_path / "project"
    args = cli.build_parser().parse_args([
        "setup",
        "--project",
        str(project),
        "--agents",
        "none",
        "--no-global",
    ])

    assert args.func(args) == 0
    assert (project / "vault" / "concepts").is_dir()
    config = (tmp_path / ".beeweave" / "config").read_text(encoding="utf-8")
    assert f'BEEWEAVE_VAULT_PATH="{project / "vault"}"' in config
    assert f'BEEWEAVE_WORKBENCH_PATH="{project / "workbench"}"' in config
    env = (project / ".env").read_text(encoding="utf-8")
    assert 'BEEWEAVE_WORKBENCH_PATH="./workbench"' in env


def test_portable_skills_include_ingest_query_and_update(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-ingest")
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "wiki" / "beeweave-update")
    _skill(root / "workbench" / "beeweave-article-writer")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)

    assert cli._portable_skills() == ("beeweave-update", "beeweave-query", "beeweave-ingest")

    target = tmp_path / "global-skills"
    cli.install_skills(target, "global", subset=cli._portable_skills(), mode="copy", quiet=True)

    assert (target / "beeweave-ingest" / "SKILL.md").exists()
    assert (target / "beeweave-query" / "SKILL.md").exists()
    assert (target / "beeweave-update" / "SKILL.md").exists()
    assert not (target / "beeweave-article-writer").exists()


def test_portable_skills_include_explicit_global_extras(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-ingest")
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "wiki" / "beeweave-update")
    _skill(root / "wiki" / "beeweave-capture")
    _skill(root / "wiki" / "beeweave-context-pack")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)

    extras = cli._parse_global_extra("beeweave-capture,beeweave-context-pack,beeweave-capture")

    assert extras == ["beeweave-capture", "beeweave-context-pack"]
    assert cli._portable_skills(extras) == (
        "beeweave-update",
        "beeweave-query",
        "beeweave-ingest",
        "beeweave-capture",
        "beeweave-context-pack",
    )


def test_global_extra_rejects_non_recommended_skills(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-ingest")
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "wiki" / "beeweave-update")
    _skill(root / "wiki" / "beeweave-rebuild")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)

    with pytest.raises(ValueError, match="unsupported global extra"):
        cli._parse_global_extra("beeweave-rebuild")


def test_uninstall_removes_global_skills_and_config_only(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-ingest")
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "wiki" / "beeweave-update")
    _skill(root / "workbench" / "beeweave-article-writer")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "HOME", tmp_path)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")

    _skill(tmp_path / ".claude" / "skills" / "beeweave-query")
    _skill(tmp_path / ".claude" / "skills" / "beeweave-article-writer")
    _skill(tmp_path / ".claude" / "skills" / "other-skill")
    _skill(tmp_path / ".codex" / "skills" / "beeweave-update")
    (tmp_path / ".beeweave").mkdir()
    (tmp_path / ".beeweave" / "config").write_text("BEEWEAVE_VAULT_PATH=/vault\n", encoding="utf-8")
    (tmp_path / ".beeweave" / "sync.log").write_text("log\n", encoding="utf-8")

    args = cli.build_parser().parse_args([
        "uninstall",
        "--agents",
        "claude,codex",
        "--no-project-local",
        "--yes",
    ])

    assert args.func(args) == 0
    assert not (tmp_path / ".claude" / "skills" / "beeweave-query").exists()
    assert not (tmp_path / ".claude" / "skills" / "beeweave-article-writer").exists()
    assert not (tmp_path / ".codex" / "skills" / "beeweave-update").exists()
    assert (tmp_path / ".claude" / "skills" / "other-skill" / "SKILL.md").exists()
    assert not (tmp_path / ".beeweave").exists()


def test_uninstall_project_removes_managed_files_but_keeps_user_data(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    boot = tmp_path / "bootstrap-root"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "workbench" / "beeweave-article-writer")
    (boot / "bootstrap").mkdir(parents=True)
    (boot / "bootstrap" / "AGENTS.md").write_text("USER PROJECT CONTEXT\n", encoding="utf-8")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: boot)
    monkeypatch.setattr(cli, "GLOBAL_CONFIG_DIR", tmp_path / ".beeweave")
    monkeypatch.setattr(cli, "GLOBAL_CONFIG", tmp_path / ".beeweave" / "config")

    project = tmp_path / "project"
    cli.install_project(project, mode="copy", agents=["claude"])
    (project / "vault" / "concepts" / "note.md").write_text("keep\n", encoding="utf-8")
    (project / "workbench" / "library" / "source.md").write_text("keep\n", encoding="utf-8")

    args = cli.build_parser().parse_args([
        "uninstall",
        "--agents",
        "claude",
        "--project",
        str(project),
        "--no-global",
        "--keep-config",
        "--yes",
    ])

    assert args.func(args) == 0
    assert not (project / ".claude" / "skills" / "beeweave-query").exists()
    assert not (project / ".claude" / "skills" / "beeweave-article-writer").exists()
    assert not (project / "AGENTS.md").exists()
    assert not (project / "CLAUDE.md").exists()
    assert (project / "vault" / "concepts" / "note.md").read_text(encoding="utf-8") == "keep\n"
    assert (project / "workbench" / "library" / "source.md").read_text(encoding="utf-8") == "keep\n"


def test_uninstall_confirmation_uses_inquirerpy(monkeypatch):
    args = cli.build_parser().parse_args(["uninstall"])
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)

    class FakeConfirm:
        def execute(self):
            return True

    def fake_confirm(*, message, default):
        assert message == "Continue?"
        assert default is False
        return FakeConfirm()

    fake_inquirer = SimpleNamespace(confirm=fake_confirm)
    monkeypatch.setitem(cli.sys.modules, "InquirerPy", SimpleNamespace(inquirer=fake_inquirer))

    assert cli._confirm_uninstall(args, ["claude"], None) is True


def test_every_agent_can_install_project_local_skills(tmp_path, monkeypatch):
    root = tmp_path / ".skills"
    _skill(root / "wiki" / "beeweave-query")
    _skill(root / "workbench" / "beeweave-article-writer")
    monkeypatch.setattr(cli, "skills_dir", lambda: root)
    monkeypatch.setattr(cli, "bootstrap_dir", lambda: None)

    for agent in cli.AGENTS:
        project = tmp_path / agent
        cli.install_project(project, mode="copy", agents=[agent])
        skill_files = list(project.glob("*/skills/*/SKILL.md"))
        assert skill_files, f"{agent} did not install project-local skills"


def test_project_local_skill_summary_lists_wiki_and_workbench(capsys):
    cli._print_project_local_skill_summary()
    output = capsys.readouterr().out

    assert "Wiki/project-local skills:" in output
    assert "beeweave-agent" in output
    assert "agent runtime guide for BeeWeave projects" in output
    assert "beeweave-query" not in output
    assert "Workbench/project-local skills:" in output
    assert "beeweave-article-writer" in output


def test_pyproject_exposes_only_bwe_console_script():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    scripts_match = re.search(r"(?ms)^\[project\.scripts\]\n(?P<body>.*?)(?:\n\[|\Z)", text)

    assert 'name = "beeweave"' in text
    assert scripts_match is not None
    script_lines = [
        line.strip()
        for line in scripts_match.group("body").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert script_lines == ['bwe = "beeweave.cli:main"']


def test_project_cli_references_in_skills_use_bwe():
    stale_patterns = (
        "obsidian" "-wiki",
        "python3 -m " "obsidian" "_wiki",
        "python -m " "obsidian" "_wiki",
    )
    stale = []
    for skill_file in sorted((ROOT / ".skills").glob("*/*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        if any(pattern in text for pattern in stale_patterns):
            stale.append(skill_file.relative_to(ROOT).as_posix())

    assert stale == []
    assert "${BEEWEAVE_CLI:-bwe}" in (ROOT / ".skills/wiki/beeweave-query/SKILL.md").read_text(encoding="utf-8")


def test_bundled_skill_metadata_uses_beeweave_prefix():
    stale = []
    for skill_file in sorted((ROOT / ".skills").glob("*/*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        match = re.search(r"(?m)^name:\s*(?P<name>[a-z0-9-]+)\s*$", text)
        rel = skill_file.relative_to(ROOT).as_posix()
        if match is None:
            stale.append(f"{rel}: missing name")
            continue
        name = match.group("name")
        if name != skill_file.parent.name:
            stale.append(f"{rel}: name {name} != directory {skill_file.parent.name}")
        if not name.startswith("beeweave-"):
            stale.append(f"{rel}: name is not beeweave-prefixed")

    assert stale == []


def test_runtime_sources_do_not_reference_old_skill_names():
    old_names = (
        "wiki-context-pack",
        "wiki-history-ingest",
        "openclaw-history-ingest",
        "copilot-history-ingest",
        "claude-history-ingest",
        "hermes-history-ingest",
        "codex-history-ingest",
        "pi-history-ingest",
        "vault-skill-factory",
        "wiki-stage-commit",
        "wiki-synthesize",
        "wiki-dashboard",
        "wiki-capture",
        "wiki-research",
        "wiki-rebuild",
        "wiki-status",
        "wiki-digest",
        "wiki-export",
        "wiki-import",
        "wiki-ingest",
        "wiki-update",
        "wiki-query",
        "wiki-setup",
        "wiki-switch",
        "wiki-dedup",
        "wiki-agent",
        "wiki-lint",
        "llm-wiki",
        "memory-bridge",
        "article-writer",
        "social-writer",
        "skill-creator",
        "cross-linker",
        "tag-taxonomy",
        "impl-validator",
        "daily-update",
        "graph-colorize",
        "/wiki-claude",
        "/wiki-codex",
        "/wiki-hermes",
        "/wiki-openclaw",
        "/wiki-copilot",
        "/wiki-pi",
    )
    scan_roots = [
        ROOT / ".skills",
        ROOT / "beeweave",
        ROOT / "bootstrap",
        ROOT / ".github",
    ]
    scan_files = [
        ROOT / "README.md",
        ROOT / "SETUP.md",
        ROOT / "setup.sh",
        ROOT / "pyproject.toml",
    ]
    for scan_root in scan_roots:
        scan_files.extend(
            path
            for path in scan_root.rglob("*")
            if path.is_file()
            and path.suffix in {".md", ".py", ".sh", ".json", ".mdc", ".yml", ".yaml"}
        )

    stale = []
    for path in sorted(set(scan_files)):
        text = path.read_text(encoding="utf-8")
        for old_name in old_names:
            pattern = re.compile(rf"(?<!beeweave-){re.escape(old_name)}")
            if pattern.search(text):
                stale.append(f"{path.relative_to(ROOT).as_posix()}: {old_name}")
                break

    assert stale == []


def test_repository_root_has_single_development_agent_context():
    assert (ROOT / "AGENTS.md").is_file()
    assert not (ROOT / "CLAUDE.md").exists()
    assert not (ROOT / "GEMINI.md").exists()
    assert not (ROOT / "HERMES.md").exists()
    assert not (ROOT / ".hermes.md").exists()

    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Development Agent Context" in text
    assert "bootstrap/AGENTS.md" in text
