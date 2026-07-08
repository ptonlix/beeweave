"""BeeWeave uninstall helpers."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beeweave import ui


@dataclass(frozen=True)
class UninstallContext:
    home: Path
    global_config_dir: Path
    global_config: Path
    agents: dict[str, dict[str, str | None]]
    bootstrap_files: Sequence[tuple[str, str, str | None]]
    agent_aliases: dict[str, tuple[str, ...]]
    list_skills: Callable[[], list[str]]
    bootstrap_dir: Callable[[], Path | None]
    resolve_bootstrap_src: Callable[[Path, str], Path | None]


def _agent_label(ctx: UninstallContext, agent: str) -> str:
    return str(ctx.agents[agent]["label"])


def _remove_empty_parents(path: Path, stop: Path) -> None:
    """Remove empty generated parent directories without crossing *stop*."""
    current = path
    stop = stop.resolve()
    while True:
        try:
            current_resolved = current.resolve()
        except FileNotFoundError:
            current_resolved = current.parent.resolve() / current.name
        if current_resolved == stop or stop not in current_resolved.parents:
            return
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def uninstall_skills(
    target_dir: Path,
    label: str,
    *,
    ctx: UninstallContext,
    subset: tuple[str, ...] | None = None,
) -> int:
    """Remove BeeWeave bundled skills from *target_dir*. Returns removed count."""
    if not target_dir.is_dir():
        return 0
    managed = set(subset or tuple(ctx.list_skills()))
    removed = 0
    for name in sorted(managed):
        path = target_dir / name
        if path.is_symlink() or path.is_file():
            path.unlink()
            removed += 1
        elif path.is_dir() and (path / "SKILL.md").exists():
            shutil.rmtree(path)
            removed += 1
    if removed:
        print(f"✅  Removed {removed} skills → {label}")
    _remove_empty_parents(target_dir, ctx.home)
    return removed


def _hermes_global_skill_dirs(ctx: UninstallContext) -> list[Path]:
    dirs = [ctx.home / ".hermes" / "skills"]
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home:
        hp = Path(hermes_home).expanduser()
        if hp != ctx.home / ".hermes":
            dirs.append(hp / "skills")
    profiles = ctx.home / ".hermes" / "profiles"
    if profiles.is_dir():
        dirs.extend(prof / "skills" for prof in sorted(p for p in profiles.iterdir() if p.is_dir()))
    return dirs


def global_skill_dirs_for_agents(ctx: UninstallContext, agents: list[str]) -> list[tuple[Path, str]]:
    seen: set[Path] = set()
    result: list[tuple[Path, str]] = []
    for agent in agents:
        global_rel = ctx.agents[agent]["global"]
        if global_rel is None:
            continue
        if agent == "hermes":
            for path in _hermes_global_skill_dirs(ctx):
                resolved = path.expanduser()
                if resolved not in seen:
                    seen.add(resolved)
                    result.append((resolved, f"{path} (Hermes, portable)"))
            continue
        path = ctx.home / str(global_rel)
        if path in seen:
            continue
        seen.add(path)
        result.append((path, f"~/{global_rel}/ ({_agent_label(ctx, agent)}, portable)"))
    return result


def _same_file_content(left: Path, right: Path) -> bool:
    try:
        return left.read_bytes() == right.read_bytes()
    except OSError:
        return False


def _remove_file_if_managed(path: Path, source: Path | None = None) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_symlink():
        path.unlink()
        return True
    if path.is_dir():
        return False
    if source is not None and not _same_file_content(path, source):
        print(f"   ⚠️  {path} was modified, leaving it in place")
        return False
    path.unlink()
    return True


def uninstall_project(ctx: UninstallContext, project_dir: Path, agents: list[str]) -> int:
    removed = 0
    if not project_dir.exists():
        return 0
    print(f"\n📁  Removing project-local BeeWeave files → {project_dir}")

    installed_project_dirs: set[str] = set()
    for agent in agents:
        project_rel = ctx.agents[agent]["project"]
        if project_rel is None or project_rel in installed_project_dirs:
            continue
        installed_project_dirs.add(str(project_rel))
        removed += uninstall_skills(
            project_dir / str(project_rel),
            f"{project_rel}/ ({_agent_label(ctx, agent)}, full)",
            ctx=ctx,
        )

    boot_root = ctx.bootstrap_dir()
    selected = set(agents)
    removed_bootstrap = 0
    if boot_root is not None:
        for rel, dest, bootstrap_agent in ctx.bootstrap_files:
            if bootstrap_agent is not None and bootstrap_agent not in selected:
                continue
            src = ctx.resolve_bootstrap_src(boot_root, rel)
            if src is not None and _remove_file_if_managed(project_dir / dest, src):
                removed_bootstrap += 1

    aliases = sorted({alias for agent in agents for alias in ctx.agent_aliases.get(agent, ())})
    for alias in aliases:
        alias_path = project_dir / alias
        if alias_path.is_symlink():
            try:
                if alias_path.readlink() != Path("AGENTS.md"):
                    continue
            except OSError:
                pass
            alias_path.unlink()
            removed_bootstrap += 1
        elif alias_path.is_file():
            agents_path = project_dir / "AGENTS.md"
            agents_source = ctx.resolve_bootstrap_src(boot_root, "AGENTS.md") if boot_root is not None else None
            compare_to = agents_path if agents_path.is_file() else agents_source
            if compare_to is not None and alias_path.read_bytes() == compare_to.read_bytes():
                alias_path.unlink()
                removed_bootstrap += 1

    env = project_dir / ".env"
    default_envs = {
        'BEEWEAVE_VAULT_PATH="./vault"\nBEEWEAVE_WORKBENCH_PATH="./workbench"\n',
    }
    if env.is_file() and env.read_text(encoding="utf-8") in default_envs:
        env.unlink()
        removed_bootstrap += 1

    if removed_bootstrap:
        print(f"✅  Removed {removed_bootstrap} project bootstrap/config file(s)")
    return removed + removed_bootstrap


def _read_config_value_from(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def _profile_config_paths(ctx: UninstallContext) -> list[Path]:
    paths: list[Path] = []
    if ctx.global_config.exists() or ctx.global_config.is_symlink():
        paths.append(ctx.global_config)
    if ctx.global_config_dir.is_dir():
        for path in sorted(ctx.global_config_dir.glob("config.*")):
            if path.name.startswith("config.backup-"):
                continue
            if path.is_file() or path.is_symlink():
                paths.append(path)
    return list(dict.fromkeys(paths))


def _project_root_from_profile_config(config_path: Path) -> Path | None:
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
        return candidate.resolve()
    return None


def discover_project_dirs(ctx: UninstallContext, base_project_dir: Path | None, *, all_profiles: bool) -> list[Path]:
    project_dirs: list[Path] = []
    if base_project_dir is not None:
        project_dirs.append(base_project_dir)
    if all_profiles:
        for config_path in _profile_config_paths(ctx):
            project_dir = _project_root_from_profile_config(config_path)
            if project_dir is not None:
                project_dirs.append(project_dir)
    return list(dict.fromkeys(project_dirs))


def confirm_uninstall(
    *,
    yes: bool,
    no_global: bool,
    keep_config: bool,
    agents: list[str],
    project_dirs: list[Path],
    config_dir: Path,
) -> bool:
    if yes:
        return True
    print("BeeWeave uninstall will remove:")
    if not no_global:
        print(f"  - global BeeWeave skills for agents: {', '.join(agents)}")
    if project_dirs:
        print("  - project-local BeeWeave skills/bootstrap files under:")
        for project_dir in project_dirs:
            print(f"    - {project_dir}")
    if not keep_config:
        print(f"  - BeeWeave config directory: {config_dir}")
    print("It will not remove your vault or workbench content.")
    if not sys.stdin.isatty():
        print("error: refusing to uninstall without --yes in a non-interactive shell", file=sys.stderr)
        return False
    try:
        return ui.confirm_prompt(message="Continue?", default=False)
    except ImportError:
        return input("Continue? [y/N]: ").strip().lower() in {"y", "yes"}


def uninstall_global_config(ctx: UninstallContext) -> int:
    if not ctx.global_config_dir.exists():
        return 0
    shutil.rmtree(ctx.global_config_dir)
    print(f"✅  Removed BeeWeave config → {ctx.global_config_dir}")
    return 1


def run_uninstall(ctx: UninstallContext, args: Any, selected_agents: list[str]) -> int:
    if args.all and args.no_project_local:
        print("error: --all cannot be used with --no-project-local", file=sys.stderr)
        return 1

    project_dir: Path | None = None
    if not args.no_project_local:
        project_dir = Path(args.project or os.getcwd()).expanduser().resolve()
    project_dirs = discover_project_dirs(ctx, project_dir, all_profiles=args.all)

    if not confirm_uninstall(
        yes=args.yes,
        no_global=args.no_global,
        keep_config=args.keep_config,
        agents=selected_agents,
        project_dirs=project_dirs,
        config_dir=ctx.global_config_dir,
    ):
        print("Uninstall cancelled.")
        return 1

    removed = 0
    if not args.no_global:
        for target, label in global_skill_dirs_for_agents(ctx, selected_agents):
            removed += uninstall_skills(target, label, ctx=ctx)

    for project_dir in project_dirs:
        removed += uninstall_project(ctx, project_dir, selected_agents)

    if not args.keep_config:
        removed += uninstall_global_config(ctx)

    config_status = "kept" if args.keep_config else "removed"
    ui.print_summary_panel(
        "Uninstall complete",
        [
            ("Removed items", removed),
            ("Affected agents", ", ".join(selected_agents) if selected_agents else "none"),
            ("Projects", str(len(project_dirs)) if project_dirs else "none"),
            ("Config", config_status),
            ("Vault/workbench", "left in place"),
        ],
    )
    return 0
