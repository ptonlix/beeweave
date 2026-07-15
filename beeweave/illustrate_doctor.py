"""Article illustration provider doctor helpers."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUPPORTED_PROVIDERS = (
    "google",
    "openai",
    "azure",
    "openrouter",
    "dashscope",
    "zai",
    "minimax",
    "replicate",
    "jimeng",
    "seedream",
    "agnes",
)

PROJECT_CONFIG_DIR = ".baoyu-skills"
DOCTOR_CACHE_NAME = "doctor.json"

_AGENT_PROJECT_SKILL_DIRS = {
    "claude": ".claude/skills",
    "cursor": ".cursor/skills",
    "windsurf": ".windsurf/skills",
    "generic": ".agents/skills",
    "pi": ".pi/skills",
    "kiro": ".kiro/skills",
    "gemini": ".gemini/skills",
    "antigravity": ".agents/skills",
    "codex": ".codex/skills",
    "hermes": ".hermes/skills",
    "openclaw": ".agents/skills",
    "copilot": ".copilot/skills",
    "trae": ".trae/skills",
    "trae-cn": ".trae-cn/skills",
}

_PROJECT_SKILL_DIRS = tuple(dict.fromkeys(_AGENT_PROJECT_SKILL_DIRS.values()))

_ARTICLE_REQUIRED = (
    "SKILL.md",
    "references",
    "references/workflow.md",
    "references/prompt-construction.md",
    "references/style-presets.md",
)

_IMAGE_GEN_REQUIRED = (
    "SKILL.md",
    "scripts/main.ts",
    "scripts/build-batch.ts",
    "scripts/types.ts",
    "scripts/providers",
    "references/usage-examples.md",
)

_CREDENTIAL_GROUPS = {
    "google": (("GOOGLE_API_KEY", "GEMINI_API_KEY"),),
    "openai": (("OPENAI_API_KEY",),),
    "azure": (("AZURE_OPENAI_API_KEY",), ("AZURE_OPENAI_BASE_URL",)),
    "openrouter": (("OPENROUTER_API_KEY",),),
    "dashscope": (("DASHSCOPE_API_KEY",),),
    "zai": (("ZAI_API_KEY", "BIGMODEL_API_KEY"),),
    "minimax": (("MINIMAX_API_KEY",),),
    "replicate": (("REPLICATE_API_TOKEN",),),
    "jimeng": (("JIMENG_ACCESS_KEY_ID",), ("JIMENG_SECRET_ACCESS_KEY",)),
    "seedream": (("ARK_API_KEY",),),
    "agnes": (("AGNES_API_KEY",),),
}

_BASE_URL_VARS = {
    "google": ("GOOGLE_BASE_URL",),
    "openai": ("OPENAI_BASE_URL",),
    "azure": ("AZURE_OPENAI_BASE_URL",),
    "openrouter": ("OPENROUTER_BASE_URL",),
    "dashscope": ("DASHSCOPE_BASE_URL",),
    "zai": ("ZAI_BASE_URL", "BIGMODEL_BASE_URL"),
    "minimax": ("MINIMAX_BASE_URL",),
    "replicate": ("REPLICATE_BASE_URL",),
    "jimeng": ("JIMENG_BASE_URL",),
    "seedream": ("SEEDREAM_BASE_URL",),
    "agnes": ("AGNES_BASE_URL",),
}


@dataclass(frozen=True)
class ProjectRootResolution:
    project_root: Path
    source: str
    detail: str | None = None


@dataclass(frozen=True)
class DoctorConfig:
    project_root: Path
    provider: str
    model: str | None
    base_url: str | None
    api_dialect: str | None
    env: dict[str, str]
    env_source: dict[str, str]
    image_extend: Path
    article_extend: Path
    article_skill_root: Path | None
    image_gen_skill_root: Path | None


@dataclass(frozen=True)
class DoctorConfigLoad:
    config: DoctorConfig | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProbeRequest:
    provider_path: Path
    output_path: Path
    args: dict[str, Any]
    prompt: str = "A simple one-color square icon for provider connectivity testing."


@dataclass
class DoctorResult:
    provider: str
    model: str | None
    base_url: str | None
    api_dialect: str | None
    check_level: str
    checked_at: str
    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    latency_ms: int | None = None
    response_kind: str | None = None
    verification: str | None = None
    fingerprint: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cache(cls, cache: dict[str, Any], fingerprint: dict[str, Any]) -> DoctorResult:
        return cls(
            provider=str(cache.get("provider")),
            model=cache.get("model"),
            base_url=cache.get("base_url"),
            api_dialect=cache.get("api_dialect"),
            check_level=str(cache.get("check_level", "config")),
            checked_at=str(cache.get("checked_at")),
            status="passed",
            errors=list(cache.get("errors") or []),
            warnings=list(cache.get("warnings") or []),
            latency_ms=cache.get("latency_ms"),
            response_kind=cache.get("response_kind"),
            verification=cache.get("verification"),
            fingerprint=fingerprint,
        )


def doctor_cache_path(project_root: Path) -> Path:
    return project_root / PROJECT_CONFIG_DIR / DOCTOR_CACHE_NAME


def _read_config_value_from(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _project_root_from_config(config_path: Path) -> Path | None:
    workbench = _read_config_value_from(config_path, "BEEWEAVE_WORKBENCH_PATH")
    vault = _read_config_value_from(config_path, "BEEWEAVE_VAULT_PATH")
    candidates: list[Path] = []
    if workbench:
        workbench_path = Path(workbench).expanduser()
        if workbench_path.name == "workbench":
            candidates.append(workbench_path.parent)
    if vault:
        vault_path = Path(vault).expanduser()
        if vault_path.name == "vault":
            candidates.append(vault_path.parent)
    if workbench and vault:
        workbench_path = Path(workbench).expanduser()
        vault_path = Path(vault).expanduser()
        if workbench_path.parent == vault_path.parent:
            candidates.insert(0, workbench_path.parent)
    for candidate in candidates:
        if candidate:
            return candidate.resolve()
    return None


def _looks_like_project_root(path: Path) -> bool:
    if (path / PROJECT_CONFIG_DIR).exists():
        return True
    if (path / "workbench").is_dir() and (path / "vault").is_dir():
        return True
    return any((path / rel).is_dir() for rel in _PROJECT_SKILL_DIRS)


def _discover_project_root_from_cwd(cwd: Path) -> Path | None:
    current = cwd.expanduser().resolve()
    if current.name in {"workbench", "vault"} and _looks_like_project_root(current.parent):
        return current.parent
    for candidate in (current, *current.parents):
        if _looks_like_project_root(candidate):
            return candidate
    return None


def resolve_project_root(
    cwd: Path,
    *,
    explicit_project: str | None = None,
    config_path: Path | None = None,
) -> ProjectRootResolution:
    if explicit_project:
        return ProjectRootResolution(
            project_root=Path(explicit_project).expanduser().resolve(),
            source="--project",
            detail=explicit_project,
        )

    local = _discover_project_root_from_cwd(cwd)
    if local is not None:
        return ProjectRootResolution(project_root=local, source="current-directory", detail=str(cwd))

    if config_path is not None:
        configured = _project_root_from_config(config_path)
        if configured is not None:
            return ProjectRootResolution(project_root=configured, source="beeweave-config", detail=str(config_path))

    return ProjectRootResolution(project_root=cwd.expanduser().resolve(), source="current-directory", detail=str(cwd))


def read_doctor_cache(project_root: Path) -> dict[str, Any] | None:
    path = doctor_cache_path(project_root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_doctor_cache(project_root: Path, result: DoctorResult) -> Path:
    path = doctor_cache_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def is_cache_valid(cache: dict[str, Any] | None, fingerprint: dict[str, Any]) -> bool:
    return bool(cache and cache.get("status") == "passed" and cache.get("fingerprint") == fingerprint)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[1]
    return text


def _parse_scalar(frontmatter: str, key: str) -> str | None:
    prefix = f"{key}:"
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        value = stripped[len(prefix) :].strip()
        if value in {"", "null", "None", "~"}:
            return None
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        return value
    return None


def _parse_nested_scalar(frontmatter: str, section: str, key: str) -> str | None:
    in_section = False
    for raw in frontmatter.splitlines():
        if raw.strip() == f"{section}:":
            in_section = True
            continue
        if in_section and raw and not raw.startswith((" ", "\t")):
            break
        if not in_section:
            continue
        stripped = raw.strip()
        prefix = f"{key}:"
        if stripped.startswith(prefix):
            value = stripped[len(prefix) :].strip()
            if value in {"", "null", "None", "~"}:
                return None
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            return value
    return None


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _merged_env(project_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    file_env = read_env_file(project_root / PROJECT_CONFIG_DIR / ".env")
    merged = dict(file_env)
    source = {key: "file" for key in file_env}
    for key, value in os.environ.items():
        if value:
            merged[key] = value
            source[key] = "process"
    return merged, source


def _first_env(env: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = env.get(key)
        if value:
            return value
    return None


def _default_install_state_path() -> Path:
    return Path.home() / ".beeweave" / "install-state.json"


def _read_install_state(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _skill_dirs_from_install_state(
    project_root: Path,
    *,
    profile: str,
    install_state_path: Path | None,
) -> tuple[str, ...] | None:
    state = _read_install_state(install_state_path or _default_install_state_path())
    raw_profiles = state.get("profiles") if state else None
    if not isinstance(raw_profiles, dict):
        return None
    raw_profile = raw_profiles.get(profile)
    if not isinstance(raw_profile, dict):
        return None

    project_raw = raw_profile.get("project_dir")
    if isinstance(project_raw, str) and project_raw:
        recorded_project = Path(project_raw).expanduser().resolve()
        if recorded_project != project_root.expanduser().resolve():
            return None

    if raw_profile.get("no_project_local") is True:
        return ()

    agents = raw_profile.get("agents")
    if not isinstance(agents, list):
        return None

    dirs: list[str] = []
    for agent in agents:
        rel = _AGENT_PROJECT_SKILL_DIRS.get(str(agent))
        if rel and rel not in dirs:
            dirs.append(rel)
    return tuple(dirs)


def _project_skill_dirs(
    project_root: Path,
    *,
    profile: str,
    install_state_path: Path | None,
) -> tuple[str, ...]:
    configured = _skill_dirs_from_install_state(
        project_root,
        profile=profile,
        install_state_path=install_state_path,
    )
    return configured if configured is not None else _PROJECT_SKILL_DIRS


def _find_skill_root(project_root: Path, skill_name: str, skill_dirs: tuple[str, ...]) -> Path | None:
    for rel in skill_dirs:
        root = project_root / rel / skill_name
        if (root / "SKILL.md").is_file():
            return root
    return None


def load_doctor_config(
    project_root: Path,
    requested_provider: str,
    *,
    profile: str = "default",
    install_state_path: Path | None = None,
) -> DoctorConfigLoad:
    errors: list[str] = []
    warnings: list[str] = []
    if requested_provider not in SUPPORTED_PROVIDERS:
        return DoctorConfigLoad(config=None, errors=[f"不支持的 provider: {requested_provider}"], warnings=warnings)

    config_dir = project_root / PROJECT_CONFIG_DIR
    article_extend = config_dir / "baoyu-article-illustrator" / "EXTEND.md"
    image_extend = config_dir / "baoyu-image-gen" / "EXTEND.md"
    if not article_extend.is_file():
        errors.append(f"缺少配置文件: {article_extend}")
    if not image_extend.is_file():
        errors.append(f"缺少配置文件: {image_extend}")
    if errors:
        return DoctorConfigLoad(config=None, errors=errors, warnings=warnings)

    article_fm = _frontmatter(article_extend)
    image_fm = _frontmatter(image_extend)
    backend = _parse_scalar(article_fm, "preferred_image_backend")
    if backend != "baoyu-image-gen":
        errors.append("baoyu-article-illustrator 必须配置 preferred_image_backend: baoyu-image-gen")

    configured_provider = _parse_scalar(image_fm, "default_provider")
    if not configured_provider:
        errors.append("baoyu-image-gen 必须配置非空 default_provider")
    elif configured_provider != requested_provider:
        errors.append(f"请求检测 provider={requested_provider}，但当前 default_provider={configured_provider}")

    model = _parse_nested_scalar(image_fm, "default_model", requested_provider)
    if not model:
        errors.append(f"baoyu-image-gen 必须配置非空 default_model.{requested_provider}")

    env, env_source = _merged_env(project_root)
    base_url = _first_env(env, _BASE_URL_VARS.get(requested_provider, ()))
    api_dialect = _parse_scalar(image_fm, "default_image_api_dialect")

    skill_dirs = _project_skill_dirs(project_root, profile=profile, install_state_path=install_state_path)
    article_skill_root = _find_skill_root(project_root, "baoyu-article-illustrator", skill_dirs)
    image_gen_skill_root = _find_skill_root(project_root, "baoyu-image-gen", skill_dirs)

    config = DoctorConfig(
        project_root=project_root,
        provider=requested_provider,
        model=model,
        base_url=base_url,
        api_dialect=api_dialect,
        env=env,
        env_source=env_source,
        image_extend=image_extend,
        article_extend=article_extend,
        article_skill_root=article_skill_root,
        image_gen_skill_root=image_gen_skill_root,
    )
    return DoctorConfigLoad(config=config, errors=errors, warnings=warnings)


def _load_checked_config(
    project_root: Path,
    provider: str,
    *,
    profile: str,
    install_state_path: Path | None,
) -> tuple[DoctorConfigLoad, dict[str, Any]]:
    loaded = load_doctor_config(
        project_root,
        provider,
        profile=profile,
        install_state_path=install_state_path,
    )
    fingerprint = build_fingerprint(loaded.config) if loaded.config is not None else {}
    return loaded, fingerprint


def _credential_errors(config: DoctorConfig) -> list[str]:
    missing: list[str] = []
    for group in _CREDENTIAL_GROUPS[config.provider]:
        if not any(config.env.get(name) for name in group):
            missing.append(" 或 ".join(group))
    return [f"缺少 provider 凭证变量: {name}" for name in missing]


def _runtime_errors() -> tuple[list[str], str | None]:
    if shutil.which("bun"):
        return [], "bun"
    if shutil.which("npx"):
        return [], "npx -y bun"
    return ["baoyu-image-gen 需要 bun 或 npx -y bun，但当前 PATH 中二者都不可用"], None


def _skill_integrity_errors(config: DoctorConfig) -> list[str]:
    errors: list[str] = []
    if config.article_skill_root is None:
        errors.append("缺少项目本地 skill: baoyu-article-illustrator/SKILL.md")
    else:
        for rel in _ARTICLE_REQUIRED:
            if not (config.article_skill_root / rel).exists():
                errors.append(f"baoyu-article-illustrator 缺少必需文件: {rel}")
    if config.image_gen_skill_root is None:
        errors.append("缺少项目本地 skill: baoyu-image-gen/SKILL.md")
    else:
        for rel in _IMAGE_GEN_REQUIRED:
            if not (config.image_gen_skill_root / rel).exists():
                errors.append(f"baoyu-image-gen 缺少必需文件: {rel}")
    return errors


def build_fingerprint(config: DoctorConfig) -> dict[str, Any]:
    env_keys = sorted({name for group in _CREDENTIAL_GROUPS[config.provider] for name in group} | set(_BASE_URL_VARS[config.provider]))
    env_fingerprint = {
        key: {
            "present": bool(config.env.get(key)),
            "source": config.env_source.get(key),
            "sha256": _hash_text(config.env[key]) if config.env.get(key) else None,
        }
        for key in env_keys
    }
    upstream_files: dict[str, str | None] = {
        "article_extend": _hash_file(config.article_extend),
        "image_extend": _hash_file(config.image_extend),
    }
    if config.article_skill_root is not None:
        for rel in _ARTICLE_REQUIRED:
            path = config.article_skill_root / rel
            if path.is_file():
                upstream_files[f"baoyu-article-illustrator/{rel}"] = _hash_file(path)
            elif path.exists():
                upstream_files[f"baoyu-article-illustrator/{rel}"] = "directory"
            else:
                upstream_files[f"baoyu-article-illustrator/{rel}"] = None
    if config.image_gen_skill_root is not None:
        for rel in _IMAGE_GEN_REQUIRED:
            path = config.image_gen_skill_root / rel
            if path.is_file():
                upstream_files[f"baoyu-image-gen/{rel}"] = _hash_file(path)
            elif path.exists():
                upstream_files[f"baoyu-image-gen/{rel}"] = "directory"
            else:
                upstream_files[f"baoyu-image-gen/{rel}"] = None

    return {
        "provider": config.provider,
        "model": config.model,
        "base_url": config.base_url,
        "api_dialect": config.api_dialect,
        "env": env_fingerprint,
        "upstream_files": upstream_files,
    }


def _missing_config_result(provider: str, loaded: DoctorConfigLoad) -> DoctorResult:
    return DoctorResult(
        provider=provider,
        model=None,
        base_url=None,
        api_dialect=None,
        check_level="config",
        checked_at=_now_iso(),
        status="failed",
        errors=loaded.errors,
        warnings=loaded.warnings,
        fingerprint={},
    )


def _build_config_check_result(config: DoctorConfig, loaded: DoctorConfigLoad, fingerprint: dict[str, Any]) -> DoctorResult:
    runtime_errors, runner = _runtime_errors()
    errors = list(loaded.errors)
    warnings = list(loaded.warnings)
    errors.extend(_credential_errors(config))
    errors.extend(runtime_errors)
    errors.extend(_skill_integrity_errors(config))
    if runner:
        warnings.append(f"Bun-compatible runner: {runner}")

    return DoctorResult(
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        api_dialect=config.api_dialect,
        check_level="config",
        checked_at=_now_iso(),
        status="failed" if errors else "passed",
        errors=errors,
        warnings=warnings,
        fingerprint=fingerprint,
    )


def run_non_billing_checks(
    project_root: Path,
    provider: str,
    *,
    force: bool = False,
    profile: str = "default",
    install_state_path: Path | None = None,
) -> tuple[DoctorResult, bool]:
    loaded, fingerprint = _load_checked_config(
        project_root,
        provider,
        profile=profile,
        install_state_path=install_state_path,
    )
    config = loaded.config
    if config is None:
        result = _missing_config_result(provider, loaded)
        write_doctor_cache(project_root, result)
        return result, False

    cache = read_doctor_cache(project_root)
    if not force and is_cache_valid(cache, fingerprint):
        assert cache is not None
        return DoctorResult.from_cache(cache, fingerprint), True

    result = _build_config_check_result(config, loaded, fingerprint)
    write_doctor_cache(project_root, result)
    return result, False


def _bun_command() -> list[str]:
    bun = shutil.which("bun")
    if bun:
        return [bun]
    npx = shutil.which("npx")
    if npx:
        return [npx, "-y", "bun"]
    raise RuntimeError("缺少 bun 或 npx -y bun")


def _probe_args(config: DoctorConfig, output_path: Path) -> dict[str, Any]:
    return {
        "prompt": None,
        "promptFiles": [],
        "imagePath": str(output_path),
        "provider": config.provider,
        "model": config.model,
        "aspectRatio": "1:1",
        "aspectRatioSource": "cli",
        "size": None,
        "quality": "normal",
        "imageSize": "1K",
        "imageSizeSource": "cli",
        "imageApiDialect": config.api_dialect,
        "responseFormat": "file",
        "referenceImages": [],
        "n": 1,
        "batchFile": None,
        "jobs": None,
        "json": True,
        "help": False,
    }


def _build_probe_request(config: DoctorConfig, output_path: Path) -> ProbeRequest:
    if config.image_gen_skill_root is None:
        raise RuntimeError("缺少项目本地 baoyu-image-gen skill")
    provider_path = (config.image_gen_skill_root / "scripts" / "providers" / f"{config.provider}.ts").resolve()
    if not provider_path.is_file():
        raise RuntimeError(f"缺少 provider module: {provider_path}")
    return ProbeRequest(provider_path=provider_path, output_path=output_path, args=_probe_args(config, output_path))


def _probe_script(request: ProbeRequest) -> str:
    output_json = json.dumps(str(request.output_path), ensure_ascii=False)
    provider_url = request.provider_path.as_uri()
    args_json = json.dumps(request.args, ensure_ascii=False)
    prompt_json = json.dumps(request.prompt, ensure_ascii=False)
    return f"""
import {{ mkdir, readFile, rm, stat, writeFile }} from "node:fs/promises";
import path from "node:path";
import * as providerModule from "{provider_url}";

const outputPath = {output_json};
const args = {args_json};
const prompt = {prompt_json};
const model = args.model || providerModule.getDefaultModel();

try {{
  providerModule.validateArgs?.(model, args);
  const started = Date.now();
  const imageData = await providerModule.generateImage(prompt, model, args);
  await mkdir(path.dirname(outputPath), {{ recursive: true }});
  await writeFile(outputPath, imageData);
  const info = await stat(outputPath);
  const sample = await readFile(outputPath);
  await rm(outputPath, {{ force: true }});
  console.log(JSON.stringify({{
    ok: true,
    provider: args.provider,
    model,
    latencyMs: Date.now() - started,
    bytes: info.size,
    nonEmpty: sample.length > 0
  }}));
}} catch (error) {{
  await rm(outputPath, {{ force: true }}).catch(() => undefined);
  console.log(JSON.stringify({{
    ok: false,
    provider: args.provider,
    model,
    error: error instanceof Error ? error.message : String(error)
  }}));
  process.exit(1);
}}
"""


def _probe_with_baoyu_provider(config: DoctorConfig) -> tuple[int, str, str]:
    if config.image_gen_skill_root is None:
        raise RuntimeError("缺少项目本地 baoyu-image-gen skill")
    probe_dir = config.project_root / PROJECT_CONFIG_DIR / "doctor-probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    script_path = probe_dir / f"probe-{config.provider}-{int(time.time() * 1000)}.ts"
    output_path = probe_dir / f"probe-{config.provider}-{int(time.time() * 1000)}.img"
    request = _build_probe_request(config, output_path)
    script_path.write_text(_probe_script(request), encoding="utf-8")
    env = os.environ.copy()
    env.update(config.env)
    try:
        completed = subprocess.run(
            [*_bun_command(), str(script_path)],
            cwd=config.project_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
    finally:
        script_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)

    stdout = completed.stdout.strip()
    payload: dict[str, Any] = {}
    if stdout:
        last_line = stdout.splitlines()[-1]
        try:
            parsed = json.loads(last_line)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = {}
    if completed.returncode != 0 or not payload.get("ok"):
        detail = str(payload.get("error") or completed.stderr or stdout or "unknown provider probe failure")
        raise RuntimeError(detail[:800])
    latency_ms = int(payload.get("latencyMs") or 0)
    byte_count = int(payload.get("bytes") or 0)
    if byte_count <= 0:
        raise RuntimeError("provider probe 返回空图片数据")
    return latency_ms, "file", "write-ok"


def run_probe_image(
    project_root: Path,
    provider: str,
    *,
    force: bool = False,
    profile: str = "default",
    install_state_path: Path | None = None,
) -> tuple[DoctorResult, bool]:
    loaded, fingerprint = _load_checked_config(
        project_root,
        provider,
        profile=profile,
        install_state_path=install_state_path,
    )
    config = loaded.config
    if config is None:
        config_result = _missing_config_result(provider, loaded)
        write_doctor_cache(project_root, config_result)
        return config_result, False

    config_result = _build_config_check_result(config, loaded, fingerprint)
    if config_result.status != "passed":
        write_doctor_cache(project_root, config_result)
        return config_result, False

    try:
        latency_ms, response_kind, verification = _probe_with_baoyu_provider(config)
        status = "passed"
        probe_errors: list[str] = []
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        latency_ms = None
        response_kind = "unknown"
        verification = "failed"
        status = "failed"
        probe_errors = [f"真实图片探测失败: {exc}"]

    result = DoctorResult(
        provider=config.provider,
        model=config.model,
        base_url=config.base_url,
        api_dialect=config.api_dialect,
        check_level="probe-image",
        checked_at=_now_iso(),
        status=status,
        errors=probe_errors,
        warnings=config_result.warnings,
        latency_ms=latency_ms,
        response_kind=response_kind,
        verification=verification,
        fingerprint=fingerprint,
    )
    write_doctor_cache(project_root, result)
    return result, False
