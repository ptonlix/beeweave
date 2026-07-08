"""BeeWeave upgrade helpers.

This module keeps installer detection, version lookup, and setup replay state
separate from the CLI command tree so the behavior can be tested without
running real package-manager commands.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PYPI_JSON_URL = "https://pypi.org/pypi/beeweave/json"
INSTALL_STATE_FILENAME = "install-state.json"
INSTALL_STATE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class InstallMethod:
    kind: str
    executable: str
    package_file: str
    detail: str = ""


@dataclass(frozen=True)
class VersionCheck:
    current: str
    latest: str | None
    status: str
    error: str | None = None


@dataclass(frozen=True)
class UpgradeResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass(frozen=True)
class ReplayEntry:
    profile: str
    config_path: Path
    project_dir: Path | None
    vault_path: str
    workbench_path: str
    agents: list[str]
    global_extra: list[str]
    no_global: bool
    no_project_local: bool
    copy: bool
    last_setup_version: str
    last_setup_at: str


@dataclass(frozen=True)
class ReplayPlan:
    entries: list[ReplayEntry]
    skipped: list[tuple[str, str]]


def install_state_path(config_dir: Path) -> Path:
    return config_dir / INSTALL_STATE_FILENAME


def _version_parts(version: str) -> tuple[int, ...]:
    parts = [int(part) for part in re.findall(r"\d+", version.split("+", 1)[0])]
    return tuple(parts or [0])


def compare_versions(current: str, latest: str) -> int:
    left = list(_version_parts(current))
    right = list(_version_parts(latest))
    width = max(len(left), len(right))
    left.extend([0] * (width - len(left)))
    right.extend([0] * (width - len(right)))
    return (left > right) - (left < right)


def fetch_latest_version(
    *,
    url: str = PYPI_JSON_URL,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 5.0,
) -> str:
    with opener(url, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    version = payload.get("info", {}).get("version")
    if not isinstance(version, str) or not version:
        raise RuntimeError("PyPI response did not include info.version")
    return version


def check_version(current: str, latest: str | None = None) -> VersionCheck:
    if latest is None:
        try:
            latest = fetch_latest_version()
        except (OSError, RuntimeError, json.JSONDecodeError, urllib.error.URLError) as exc:
            return VersionCheck(current=current, latest=None, status="unknown", error=str(exc))
    cmp = compare_versions(current, latest)
    status = "update_available" if cmp < 0 else "up_to_date"
    return VersionCheck(current=current, latest=latest, status=status)


def _has_source_checkout_marker(path: Path) -> bool:
    return any((parent / ".git").exists() and (parent / "pyproject.toml").is_file() for parent in [path, *path.parents])


def detect_install_method(
    *,
    package_file: str,
    executable: str | None = None,
    prefix: str | None = None,
) -> InstallMethod:
    exe = executable or sys.executable
    pkg = str(Path(package_file).resolve())
    prefix_value = str(Path(prefix or sys.prefix).resolve())
    haystack = f"{exe}\n{pkg}\n{prefix_value}"

    if ".local/share/uv/tools/beeweave" in haystack or "/uv/tools/beeweave" in haystack:
        return InstallMethod("uv_tool", exe, pkg, "uv tool environment")

    pkg_path = Path(pkg)
    if _has_source_checkout_marker(pkg_path):
        return InstallMethod("source", exe, pkg, "source checkout or editable install")

    if "site-packages" in pkg or "dist-packages" in pkg:
        return InstallMethod("pip", exe, pkg, "site-packages install")

    return InstallMethod("unknown", exe, pkg, "unsupported or ambiguous install layout")


def upgrade_command(method: InstallMethod) -> list[str] | None:
    if method.kind == "uv_tool":
        return ["uv", "tool", "upgrade", "beeweave"]
    if method.kind == "pip":
        return [method.executable, "-m", "pip", "install", "--upgrade", "beeweave"]
    return None


def manual_upgrade_hint(method: InstallMethod) -> list[str]:
    if method.kind == "source":
        source = _source_root(Path(method.package_file))
        if source is not None:
            return [
                f"cd {source}",
                "git pull",
                "uv tool install --reinstall --editable .",
                "bwe setup",
            ]
        return ["git pull", "uv tool install --reinstall --editable /path/to/beeweave", "bwe setup"]
    if method.kind == "unknown":
        return [f"{method.executable} -m pip install --upgrade beeweave", "bwe setup"]
    return []


def _source_root(path: Path) -> Path | None:
    for parent in [path, *path.parents]:
        if (parent / ".git").exists() and (parent / "pyproject.toml").is_file():
            return parent
    return None


def run_upgrade_command(
    command: list[str], *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
) -> UpgradeResult:
    proc = runner(command, text=True, capture_output=True)
    return UpgradeResult(
        command=command,
        returncode=int(proc.returncode),
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )


def load_install_state(config_dir: Path) -> dict[str, Any]:
    path = install_state_path(config_dir)
    if not path.is_file():
        return {"schema_version": INSTALL_STATE_SCHEMA_VERSION, "profiles": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": INSTALL_STATE_SCHEMA_VERSION, "profiles": {}}
    if not isinstance(data, dict):
        return {"schema_version": INSTALL_STATE_SCHEMA_VERSION, "profiles": {}}
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        data["profiles"] = {}
    data.setdefault("schema_version", INSTALL_STATE_SCHEMA_VERSION)
    return data


def save_install_state(config_dir: Path, state: dict[str, Any]) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state["schema_version"] = INSTALL_STATE_SCHEMA_VERSION
    path = install_state_path(config_dir)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record_setup_state(
    *,
    config_dir: Path,
    profile: str,
    config_path: Path,
    project_dir: Path | None,
    vault_path: str,
    workbench_path: str | None,
    agents: list[str],
    global_extra: list[str],
    no_global: bool,
    no_project_local: bool,
    copy: bool,
    version: str,
    installer: InstallMethod | None = None,
    now: datetime | None = None,
) -> None:
    state = load_install_state(config_dir)
    if installer is not None:
        state["installer"] = {
            "method": installer.kind,
            "python": installer.executable,
            "package_file": installer.package_file,
            "detail": installer.detail,
        }
    profiles = state.setdefault("profiles", {})
    timestamp = (now or datetime.now().astimezone()).isoformat(timespec="seconds")
    profiles[profile] = {
        "config_path": str(config_path),
        "project_dir": str(project_dir) if project_dir is not None else None,
        "vault_path": vault_path,
        "workbench_path": workbench_path or "",
        "agents": list(agents),
        "global_extra": list(global_extra),
        "no_global": bool(no_global),
        "no_project_local": bool(no_project_local),
        "copy": bool(copy),
        "last_setup_version": version,
        "last_setup_at": timestamp,
    }
    save_install_state(config_dir, state)


def replay_plan(config_dir: Path) -> ReplayPlan:
    state = load_install_state(config_dir)
    raw_profiles = state.get("profiles", {})
    entries: list[ReplayEntry] = []
    skipped: list[tuple[str, str]] = []
    if not isinstance(raw_profiles, dict):
        return ReplayPlan(entries=[], skipped=[])

    for name, raw in sorted(raw_profiles.items()):
        if not isinstance(raw, dict):
            skipped.append((str(name), "invalid profile state"))
            continue
        project_raw = raw.get("project_dir")
        project_dir = Path(project_raw).expanduser() if isinstance(project_raw, str) and project_raw else None
        if project_dir is not None and not project_dir.exists():
            skipped.append((str(name), f"missing project directory: {project_dir}"))
            continue
        config_raw = raw.get("config_path")
        config_path = (
            Path(config_raw).expanduser() if isinstance(config_raw, str) and config_raw else config_dir / "config"
        )
        entries.append(
            ReplayEntry(
                profile=str(name),
                config_path=config_path,
                project_dir=project_dir.resolve() if project_dir is not None else None,
                vault_path=str(raw.get("vault_path") or ""),
                workbench_path=str(raw.get("workbench_path") or ""),
                agents=[str(agent) for agent in raw.get("agents", []) if isinstance(agent, str)],
                global_extra=[str(skill) for skill in raw.get("global_extra", []) if isinstance(skill, str)],
                no_global=bool(raw.get("no_global", False)),
                no_project_local=bool(raw.get("no_project_local", project_dir is None)),
                copy=bool(raw.get("copy", False)),
                last_setup_version=str(raw.get("last_setup_version") or ""),
                last_setup_at=str(raw.get("last_setup_at") or ""),
            )
        )
    return ReplayPlan(entries=entries, skipped=skipped)
