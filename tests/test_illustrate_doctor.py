import json
from pathlib import Path

import pytest
from beeweave import cli, illustrate_doctor


def _write(path: Path, text: str = "ok") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_project_config(project: Path, *, provider: str = "openai", model: str = "gpt-image-2") -> None:
    _write(
        project / ".baoyu-skills/baoyu-article-illustrator/EXTEND.md",
        """---
version: 1
preferred_image_backend: baoyu-image-gen
---
""",
    )
    _write(
        project / ".baoyu-skills/baoyu-image-gen/EXTEND.md",
        f"""---
version: 1
default_provider: {provider}
default_image_api_dialect: openai-native
default_model:
  google: null
  openai: {model}
  azure: null
  dashscope: qwen-image-2.0-pro
---
""",
    )
    if provider == "dashscope":
        env_text = "DASHSCOPE_API_KEY=sk-dashscope\n"
    else:
        env_text = "OPENAI_API_KEY=sk-test\nOPENAI_BASE_URL=https://new.fastaicode.top\n"
    _write(project / ".baoyu-skills/.env", env_text)


def _write_upstream_skills(project: Path) -> None:
    article = project / ".codex/skills/baoyu-article-illustrator"
    _write(article / "SKILL.md")
    _mkdir(article / "references")
    _write(article / "references/workflow.md")
    _write(article / "references/prompt-construction.md")
    _write(article / "references/style-presets.md")

    image = project / ".codex/skills/baoyu-image-gen"
    _write(image / "SKILL.md")
    _write(image / "scripts/main.ts")
    _write(image / "scripts/build-batch.ts")
    _write(image / "scripts/types.ts")
    _mkdir(image / "scripts/providers")
    _write(image / "scripts/providers/openai.ts")
    _write(image / "scripts/providers/dashscope.ts")
    _write(image / "references/usage-examples.md")


def _write_install_state(path: Path, project: Path, *, agents: list[str], profile: str = "default") -> None:
    _write(
        path,
        json.dumps(
            {
                "schema_version": 1,
                "profiles": {
                    profile: {
                        "project_dir": str(project),
                        "agents": agents,
                        "no_project_local": False,
                    }
                },
            },
            indent=2,
        )
        + "\n",
    )


def _ready_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    _write_project_config(project)
    _write_upstream_skills(project)
    return project


def test_illustrate_parser_supports_doctor_only():
    parser = cli.build_parser()

    args = parser.parse_args(["illustrate", "doctor", "--provider", "openai", "--probe-image", "--force"])
    assert args.func is cli.cmd_illustrate_doctor
    assert args.provider == "openai"
    assert args.probe_image is True
    assert args.force is True

    args = parser.parse_args(
        ["illustrate", "doctor", "--provider", "openai", "--project", "/tmp/work", "--profile", "work"]
    )
    assert args.project == "/tmp/work"
    assert args.profile == "work"

    with pytest.raises(SystemExit):
        parser.parse_args(["illustrate", "setup"])
    with pytest.raises(SystemExit):
        parser.parse_args(["illustrate", "config", "show"])
    with pytest.raises(SystemExit):
        parser.parse_args(["illustrate", "run", "article.md"])


def test_resolve_project_root_prefers_explicit_project(tmp_path):
    explicit = tmp_path / "workspace"

    resolution = illustrate_doctor.resolve_project_root(Path.cwd(), explicit_project=str(explicit))

    assert resolution.project_root == explicit.resolve()
    assert resolution.source == "--project"


def test_resolve_project_root_discovers_from_cwd(tmp_path):
    project = tmp_path / "workspace"
    _write_project_config(project)

    resolution = illustrate_doctor.resolve_project_root(project / "workbench" / "drafts")

    assert resolution.project_root == project.resolve()
    assert resolution.source == "current-directory"


def test_resolve_project_root_falls_back_to_beeweave_config(tmp_path):
    project = tmp_path / "workspace"
    (project / "workbench").mkdir(parents=True)
    (project / "vault").mkdir()
    config = tmp_path / ".beeweave" / "config"
    _write(
        config,
        f'BEEWEAVE_VAULT_PATH="{project / "vault"}"\n'
        f'BEEWEAVE_WORKBENCH_PATH="{project / "workbench"}"\n',
    )

    resolution = illustrate_doctor.resolve_project_root(tmp_path / "elsewhere", config_path=config)

    assert resolution.project_root == project.resolve()
    assert resolution.source == "beeweave-config"


def test_non_billing_doctor_writes_and_reuses_cache(tmp_path, monkeypatch):
    project = _ready_project(tmp_path)
    monkeypatch.setattr(illustrate_doctor.shutil, "which", lambda name: "/usr/bin/bun" if name == "bun" else None)

    result, reused = illustrate_doctor.run_non_billing_checks(project, "openai")

    assert result.status == "passed"
    assert reused is False
    cache = json.loads((project / ".baoyu-skills/doctor.json").read_text(encoding="utf-8"))
    assert cache["status"] == "passed"
    assert cache["provider"] == "openai"
    assert cache["base_url"] == "https://new.fastaicode.top"
    assert "sk-test" not in json.dumps(cache)

    result, reused = illustrate_doctor.run_non_billing_checks(project, "openai")

    assert result.status == "passed"
    assert reused is True


def test_cache_stales_when_env_changes(tmp_path, monkeypatch):
    project = _ready_project(tmp_path)
    monkeypatch.setattr(illustrate_doctor.shutil, "which", lambda name: "/usr/bin/bun" if name == "bun" else None)
    first, _ = illustrate_doctor.run_non_billing_checks(project, "openai")
    cache = illustrate_doctor.read_doctor_cache(project)
    assert illustrate_doctor.is_cache_valid(cache, first.fingerprint)

    _write(
        project / ".baoyu-skills/.env",
        "OPENAI_API_KEY=sk-changed\nOPENAI_BASE_URL=https://new.fastaicode.top\n",
    )
    loaded = illustrate_doctor.load_doctor_config(project, "openai")
    assert loaded.config is not None
    assert loaded.errors == []
    changed_fingerprint = illustrate_doctor.build_fingerprint(loaded.config)

    assert not illustrate_doctor.is_cache_valid(cache, changed_fingerprint)


def test_force_recheck_ignores_valid_cache(tmp_path, monkeypatch):
    project = _ready_project(tmp_path)
    monkeypatch.setattr(illustrate_doctor.shutil, "which", lambda name: "/usr/bin/bun" if name == "bun" else None)
    _first, _ = illustrate_doctor.run_non_billing_checks(project, "openai")

    result, reused = illustrate_doctor.run_non_billing_checks(project, "openai", force=True)

    assert result.status == "passed"
    assert reused is False


def test_non_billing_doctor_does_not_call_image_generation_endpoint(tmp_path, monkeypatch):
    project = _ready_project(tmp_path)
    monkeypatch.setattr(illustrate_doctor.shutil, "which", lambda name: "/usr/bin/bun" if name == "bun" else None)

    result, _reused = illustrate_doctor.run_non_billing_checks(project, "openai")

    assert result.status == "passed"


def test_doctor_checks_only_installed_agent_skill_dirs(tmp_path, monkeypatch):
    project = _ready_project(tmp_path)
    state = tmp_path / ".beeweave/install-state.json"
    monkeypatch.setattr(illustrate_doctor.shutil, "which", lambda name: "/usr/bin/bun" if name == "bun" else None)

    _write_install_state(state, project, agents=["claude"])
    result, _reused = illustrate_doctor.run_non_billing_checks(
        project,
        "openai",
        force=True,
        install_state_path=state,
    )
    assert result.status == "failed"
    assert "缺少项目本地 skill: baoyu-image-gen/SKILL.md" in result.errors

    _write_install_state(state, project, agents=["codex"])
    result, _reused = illustrate_doctor.run_non_billing_checks(
        project,
        "openai",
        force=True,
        install_state_path=state,
    )
    assert result.status == "passed"


def test_probe_image_uses_baoyu_provider_for_non_openai(tmp_path, monkeypatch):
    project = tmp_path / "project"
    _write_project_config(project, provider="dashscope", model="qwen-image-2.0-pro")
    _write_upstream_skills(project)
    monkeypatch.setattr(illustrate_doctor.shutil, "which", lambda name: "/usr/bin/bun" if name == "bun" else None)

    calls = []

    def fake_probe(config):
        calls.append(config.provider)
        return 12, "file", "write-ok"

    monkeypatch.setattr(illustrate_doctor, "_probe_with_baoyu_provider", fake_probe)

    result, reused = illustrate_doctor.run_probe_image(project, "dashscope")

    assert result.status == "passed"
    assert reused is False
    assert calls == ["dashscope"]
    assert result.response_kind == "file"
    assert result.verification == "write-ok"
