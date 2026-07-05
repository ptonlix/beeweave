"""beeweave installer CLI.

Python port of ``setup.sh`` for the pip-installed package. The skill content
lives inside the installed package (``beeweave/_data/skills``) instead of a
cloned repo, so this wires the bundled skills into every supported AI agent's
skills directory and writes ``~/.beeweave/config`` so the skills resolve
the vault from any project.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from beeweave import __version__

HOME = Path.home()
GLOBAL_CONFIG_DIR = HOME / ".beeweave"
GLOBAL_CONFIG = GLOBAL_CONFIG_DIR / "config"

# Skills usable from any project through the global BeeWeave config. Keep the
# default set focused on the core cross-project workflows. Extra global skills
# are explicit opt-in only.
CORE_PORTABLE_SKILLS = ("beeweave-update", "beeweave-query", "beeweave-ingest")
RECOMMENDED_GLOBAL_EXTRA_SKILLS = (
    "beeweave-capture",
    "beeweave-context-pack",
    "beeweave-digest",
    "beeweave-status",
    "beeweave-memory-bridge",
)
GLOBAL_EXTRA_DESCRIPTIONS = {
    "beeweave-capture": "save current-session findings to inbox/wiki",
    "beeweave-context-pack": "package vault context for another task",
    "beeweave-digest": "generate recent knowledge digests",
    "beeweave-status": "show ingest status and vault health",
    "beeweave-memory-bridge": "compare knowledge by source agent",
}
LOCAL_WIKI_SKILL_DESCRIPTIONS = {
    "beeweave-agent": "agent runtime guide for BeeWeave projects",
    "beeweave-claude-ingest": "import Claude conversation history",
    "beeweave-codex-ingest": "import Codex conversation history",
    "beeweave-copilot-ingest": "import GitHub Copilot conversation history",
    "beeweave-core": "core vault structure and operating rules",
    "beeweave-cross-linker": "add wiki links between related notes",
    "beeweave-daily-update": "create daily knowledge updates",
    "beeweave-dashboard": "summarize vault status as a dashboard",
    "beeweave-dedup": "detect and reconcile duplicate knowledge",
    "beeweave-export": "export vault content for reuse",
    "beeweave-graph-colorize": "maintain graph color groups",
    "beeweave-hermes-ingest": "import Hermes conversation history",
    "beeweave-history-ingest": "unified agent-history import workflow",
    "beeweave-impl-validator": "validate implementation against specs",
    "beeweave-import": "import existing documents into the vault",
    "beeweave-lint": "check vault structure and note hygiene",
    "beeweave-openclaw-ingest": "import OpenClaw conversation history",
    "beeweave-pi-ingest": "import Pi conversation history",
    "beeweave-rebuild": "rebuild vault indexes and derived files",
    "beeweave-research": "run research capture and synthesis workflows",
    "beeweave-setup": "set up or repair a BeeWeave workspace",
    "beeweave-skill-creator": "create, improve, and evaluate skills",
    "beeweave-stage-commit": "prepare and commit vault changes",
    "beeweave-switch": "switch active vault or workbench context",
    "beeweave-synthesize": "synthesize notes into durable knowledge",
    "beeweave-tag-taxonomy": "maintain tag taxonomy and naming",
    "beeweave-vault-skill-factory": "turn vault practices into skills",
}
WORKBENCH_SKILL_DESCRIPTIONS = {
    "beeweave-article-writer": "long-form articles, blog posts, essays, and opinion pieces",
    "beeweave-social-writer": "X/Twitter posts, threads, short takes, and social copy",
}


# ── Data resolution ──────────────────────────────────────────────────────────
# Works for both a built wheel (data under <pkg>/_data) and an editable/source
# checkout (data at the repo root next to the package).
def _pkg_dir() -> Path:
    return Path(__file__).resolve().parent


def skills_dir() -> Path:
    """Return the directory holding the bundled skill folders."""
    for cand in (_pkg_dir() / "_data" / "skills", _pkg_dir().parent / ".skills"):
        if cand.is_dir():
            return cand
    raise FileNotFoundError(
        "Could not locate bundled skills. Reinstall beeweave "
        "(`pip install --force-reinstall beeweave`)."
    )


def bootstrap_dir() -> Path | None:
    """Return the directory containing agent bootstrap context files.

    For a wheel this is ``_data/bootstrap``; for a source checkout the files are
    spread across the repo root, so we return the repo root and resolve each
    file via the repo-relative layout in ``_bootstrap_files``.
    """
    built = _pkg_dir() / "_data" / "bootstrap"
    if built.is_dir():
        return built
    repo = _pkg_dir().parent
    if (repo / "AGENTS.md").is_file():
        return repo
    return None


def iter_skill_dirs() -> list[Path]:
    """Return real skill directories, supporting flat and grouped layouts.

    The source tree keeps skills grouped as ``.skills/wiki/<name>`` and
    ``.skills/workbench/<name>``. Older wheels may still contain the flat
    ``.skills/<name>`` layout. A real skill directory is identified by a
    ``SKILL.md`` file and installed by its directory name.
    """
    root = skills_dir()
    skills: list[Path] = []

    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if (child / "SKILL.md").is_file():
            skills.append(child)
            continue
        for nested in sorted(p for p in child.iterdir() if p.is_dir()):
            if (nested / "SKILL.md").is_file():
                skills.append(nested)

    seen: set[str] = set()
    duplicates: set[str] = set()
    for skill in skills:
        if skill.name in seen:
            duplicates.add(skill.name)
        seen.add(skill.name)
    if duplicates:
        names = ", ".join(sorted(duplicates))
        raise RuntimeError(f"duplicate skill names found: {names}")

    return skills


def list_skills() -> list[str]:
    return sorted(p.name for p in iter_skill_dirs())


# ── Skill installation ───────────────────────────────────────────────────────
def install_skills(
    target_dir: Path,
    label: str,
    *,
    subset: tuple[str, ...] | None = None,
    mode: str = "symlink",
    quiet: bool = False,
) -> int:
    """Install bundled skills into *target_dir*. Returns the count installed."""
    target_dir.mkdir(parents=True, exist_ok=True)
    installed = 0
    for skill in iter_skill_dirs():
        name = skill.name
        if subset is not None and name not in subset:
            continue
        link_path = target_dir / name

        if link_path.is_symlink() or link_path.is_file():
            link_path.unlink()
        elif link_path.is_dir():
            # A real directory we previously copied here is safe to replace;
            # anything else is the user's and we leave it alone.
            if (link_path / "SKILL.md").exists():
                shutil.rmtree(link_path)
            else:
                print(f"   ⚠️  {link_path} is not a managed skill, skipping")
                continue

        if mode == "symlink":
            link_path.symlink_to(skill, target_is_directory=True)
        else:  # copy
            shutil.copytree(skill, link_path)

        if not (link_path / "SKILL.md").exists():
            raise RuntimeError(f"broken skill install: {link_path} -> {skill}")
        installed += 1

    if not quiet:
        print(f"✅  Installed {installed} skills → {label}")
    return installed


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
    subset: tuple[str, ...] | None = None,
) -> int:
    """Remove BeeWeave bundled skills from *target_dir*. Returns removed count."""
    if not target_dir.is_dir():
        return 0
    managed = set(subset or tuple(list_skills()))
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
    _remove_empty_parents(target_dir, HOME)
    return removed


AGENTS: dict[str, dict[str, str | None]] = {
    "claude": {
        "label": "Claude Code",
        "project": ".claude/skills",
        "global": ".claude/skills",
    },
    "cursor": {
        "label": "Cursor",
        "project": ".cursor/skills",
        "global": None,
    },
    "windsurf": {
        "label": "Windsurf",
        "project": ".windsurf/skills",
        "global": None,
    },
    "generic": {
        "label": "OpenCode / Aider / Droid / generic",
        "project": ".agents/skills",
        "global": ".agents/skills",
    },
    "pi": {
        "label": "Pi",
        "project": ".pi/skills",
        "global": ".pi/agent/skills",
    },
    "kiro": {
        "label": "Kiro",
        "project": ".kiro/skills",
        "global": ".kiro/skills",
    },
    "gemini": {
        "label": "Gemini CLI",
        "project": ".gemini/skills",
        "global": ".gemini/skills",
    },
    "antigravity": {
        "label": "Google Antigravity",
        "project": ".agents/skills",
        "global": ".gemini/antigravity/skills",
    },
    "codex": {
        "label": "Codex",
        "project": ".codex/skills",
        "global": ".codex/skills",
    },
    "hermes": {
        "label": "Hermes",
        "project": ".hermes/skills",
        "global": ".hermes/skills",
    },
    "openclaw": {
        "label": "OpenClaw",
        "project": ".openclaw/skills",
        "global": ".openclaw/skills",
    },
    "copilot": {
        "label": "GitHub Copilot CLI",
        "project": ".copilot/skills",
        "global": ".copilot/skills",
    },
    "trae": {
        "label": "Trae",
        "project": ".trae/skills",
        "global": ".trae/skills",
    },
    "trae-cn": {
        "label": "Trae CN",
        "project": ".trae-cn/skills",
        "global": ".trae-cn/skills",
    },
}

DEFAULT_AGENTS = ("claude", "codex")


def _portable_skills(extras: list[str] | tuple[str, ...] = ()) -> tuple[str, ...]:
    available = set(list_skills())
    requested = [*CORE_PORTABLE_SKILLS, *extras]
    return tuple(skill for skill in dict.fromkeys(requested) if skill in available)


def _parse_global_extra(raw: str | None) -> list[str]:
    if raw is None:
        return []
    value = raw.strip().lower().replace(" ", "")
    if not value or value in {"none", "no", "skip"}:
        return []
    selected = [part for part in value.split(",") if part]
    allowed = set(RECOMMENDED_GLOBAL_EXTRA_SKILLS)
    unknown = [skill for skill in selected if skill not in allowed]
    if unknown:
        known = ", ".join(RECOMMENDED_GLOBAL_EXTRA_SKILLS)
        raise ValueError(
            f"unknown or unsupported global extra skill(s): {', '.join(unknown)}; "
            f"recommended extras: {known}"
        )
    available = set(list_skills())
    missing = [skill for skill in selected if skill not in available]
    if missing:
        raise ValueError(f"global extra skill(s) not bundled: {', '.join(missing)}")
    return list(dict.fromkeys(selected))


def _parse_global_extra_menu_selection(raw: str) -> list[str]:
    value = raw.strip().lower()
    if not value or value in {"none", "no", "skip"}:
        return []
    if value == "all":
        return _parse_global_extra(",".join(RECOMMENDED_GLOBAL_EXTRA_SKILLS))

    tokens = value.replace(",", " ").split()
    selected: list[str] = []
    names = list(RECOMMENDED_GLOBAL_EXTRA_SKILLS)
    for token in tokens:
        if token.isdigit():
            idx = int(token)
            if idx < 1 or idx > len(names):
                raise ValueError(f"selection out of range: {token}")
            selected.append(names[idx - 1])
        elif token in names:
            selected.append(token)
        else:
            raise ValueError(f"unknown selection: {token}")
    return _parse_global_extra(",".join(selected))


def _print_project_local_skill_summary() -> None:
    print()
    available = set(list_skills())
    local_wiki = {
        name: description
        for name, description in LOCAL_WIKI_SKILL_DESCRIPTIONS.items()
        if name not in CORE_PORTABLE_SKILLS
        and name not in RECOMMENDED_GLOBAL_EXTRA_SKILLS
    }
    print("  Wiki/project-local skills:")
    for name, description in local_wiki.items():
        suffix = "" if name in available else " (not bundled)"
        print(f"    {name:<28} {description}{suffix}")
    print()
    print("  Workbench/project-local skills:")
    for name, description in WORKBENCH_SKILL_DESCRIPTIONS.items():
        suffix = "" if name in available else " (not bundled)"
        print(f"    {name:<28} {description}{suffix}")


def _choose_global_extra_numbered() -> list[str]:
    print("  Global skills")
    print("    Always installed:")
    for skill in CORE_PORTABLE_SKILLS:
        print(f"      [x] {skill}")
    print()
    print("    Optional advanced global skills:")
    for idx, skill in enumerate(RECOMMENDED_GLOBAL_EXTRA_SKILLS, start=1):
        description = GLOBAL_EXTRA_DESCRIPTIONS[skill]
        print(f"     {idx:2d}. {skill:<18} {description}")
    print("        all              Install all optional advanced global skills")
    print("        none             Default: install only the core three")
    _print_project_local_skill_summary()
    print()
    while True:
        entered = input("  Extra global skills [none]: ").strip()
        try:
            return _parse_global_extra_menu_selection(entered)
        except ValueError as exc:
            print(f"  {exc}")


def _choose_global_extra_checkbox() -> list[str]:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    print("  Global skills always installed:")
    for skill in CORE_PORTABLE_SKILLS:
        print(f"    [x] {skill}")
    _print_project_local_skill_summary()
    print()
    choices = [
        Choice(
            skill,
            name=f"{skill} - {GLOBAL_EXTRA_DESCRIPTIONS[skill]}",
            enabled=False,
        )
        for skill in RECOMMENDED_GLOBAL_EXTRA_SKILLS
    ]
    selected = inquirer.checkbox(
        message="Optional advanced global skills:",
        choices=choices,
        instruction="(↑↓ move, space select, enter confirm; default none)",
        transformer=lambda result: f"{len(result)} selected",
        cycle=False,
        height=min(8, len(choices)),
    ).execute()
    return _parse_global_extra(",".join(selected))


def choose_global_extra(raw_extra: str | None, *, no_global: bool = False) -> list[str]:
    if no_global:
        return []
    if raw_extra is not None:
        return _parse_global_extra(raw_extra)
    if not sys.stdin.isatty():
        return []
    try:
        return _choose_global_extra_checkbox()
    except ImportError:
        return _choose_global_extra_numbered()


def _agent_label(agent: str) -> str:
    return str(AGENTS[agent]["label"])


def _parse_agent_list(raw: str) -> list[str]:
    value = raw.strip().lower().replace(" ", "")
    if not value:
        return list(DEFAULT_AGENTS)
    if value == "all":
        return list(AGENTS)
    if value in {"none", "no", "skip"}:
        return []
    selected = [part for part in value.split(",") if part]
    unknown = [agent for agent in selected if agent not in AGENTS]
    if unknown:
        known = ", ".join(AGENTS)
        raise ValueError(f"unknown agent(s): {', '.join(unknown)}; known agents: {known}")
    return list(dict.fromkeys(selected))


def _parse_menu_selection(raw: str) -> list[str]:
    value = raw.strip().lower()
    if not value:
        return list(DEFAULT_AGENTS)
    if value == "all":
        return list(AGENTS)
    if value in {"none", "no", "skip"}:
        return []

    tokens = value.replace(",", " ").split()
    selected: list[str] = []
    names = list(AGENTS)
    for token in tokens:
        if token.isdigit():
            idx = int(token)
            if idx < 1 or idx > len(names):
                raise ValueError(f"selection out of range: {token}")
            selected.append(names[idx - 1])
        elif token in AGENTS:
            selected.append(token)
        else:
            raise ValueError(f"unknown selection: {token}")
    return list(dict.fromkeys(selected))


def _choose_agents_numbered() -> list[str]:
    print("  Install skills for which agents?")
    for idx, (agent, meta) in enumerate(AGENTS.items(), start=1):
        marker = " (default)" if agent in DEFAULT_AGENTS else ""
        print(f"   {idx:2d}. {agent:<12} {meta['label']}{marker}")
    print("      all          Install every supported agent")
    print("      none         Only create vault/workbench/config")
    print("")
    while True:
        entered = input("  Select agents [1,10]: ").strip()
        try:
            return _parse_menu_selection(entered)
        except ValueError as exc:
            print(f"  {exc}")


def _choose_agents_checkbox() -> list[str]:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    choices = [
        Choice(
            agent,
            name=f"{agent} - {meta['label']}",
            enabled=agent in DEFAULT_AGENTS,
        )
        for agent, meta in AGENTS.items()
    ]
    selected = inquirer.checkbox(
        message="Select agents:",
        choices=choices,
        instruction="(↑↓ move, space select, enter confirm)",
        transformer=lambda result: f"{len(result)} selected",
        cycle=False,
        height=min(12, len(choices)),
    ).execute()
    return list(selected)


def choose_agents(raw_agents: str | None) -> list[str]:
    if raw_agents is not None:
        return _parse_agent_list(raw_agents)

    if not sys.stdin.isatty():
        return list(DEFAULT_AGENTS)

    try:
        return _choose_agents_checkbox()
    except ImportError:
        return _choose_agents_numbered()


def install_global_skills_for_agents(
    agents: list[str],
    mode: str,
    extra_skills: list[str] | tuple[str, ...] = (),
) -> None:
    portable = _portable_skills(extra_skills)
    for agent in agents:
        global_rel = AGENTS[agent]["global"]
        if global_rel is None:
            continue
        if agent == "hermes":
            install_hermes_portable(mode, portable)
            continue
        label = f"~/{global_rel}/ ({_agent_label(agent)}, portable)"
        install_skills(HOME / str(global_rel), label, subset=portable, mode=mode)


def install_hermes_portable(mode: str, portable: tuple[str, ...]) -> None:
    """Mirror setup.sh: install into the active and all named Hermes profiles."""
    install_skills(HOME / ".hermes" / "skills", "~/.hermes/skills/ (Hermes default, portable)", subset=portable, mode=mode)
    hermes_home = os.environ.get("HERMES_HOME")
    handled: set[Path] = set()
    if hermes_home:
        hp = Path(hermes_home).expanduser()
        if hp != HOME / ".hermes":
            install_skills(
                hp / "skills",
                f"{hp}/skills/ (Hermes active profile, portable)",
                subset=portable,
                mode=mode,
            )
            handled.add(hp)
    profiles = HOME / ".hermes" / "profiles"
    if profiles.is_dir():
        for prof in sorted(p for p in profiles.iterdir() if p.is_dir()):
            if prof in handled:
                continue
            install_skills(
                prof / "skills",
                f"~/.hermes/profiles/{prof.name}/skills/ (Hermes profile: {prof.name}, portable)",
                subset=portable,
                mode=mode,
            )


def _hermes_global_skill_dirs() -> list[Path]:
    dirs = [HOME / ".hermes" / "skills"]
    hermes_home = os.environ.get("HERMES_HOME")
    if hermes_home:
        hp = Path(hermes_home).expanduser()
        if hp != HOME / ".hermes":
            dirs.append(hp / "skills")
    profiles = HOME / ".hermes" / "profiles"
    if profiles.is_dir():
        dirs.extend(prof / "skills" for prof in sorted(p for p in profiles.iterdir() if p.is_dir()))
    return dirs


def global_skill_dirs_for_agents(agents: list[str]) -> list[tuple[Path, str]]:
    seen: set[Path] = set()
    result: list[tuple[Path, str]] = []
    for agent in agents:
        global_rel = AGENTS[agent]["global"]
        if global_rel is None:
            continue
        if agent == "hermes":
            for path in _hermes_global_skill_dirs():
                resolved = path.expanduser()
                if resolved not in seen:
                    seen.add(resolved)
                    result.append((resolved, f"{path} (Hermes, portable)"))
            continue
        path = HOME / str(global_rel)
        if path in seen:
            continue
        seen.add(path)
        result.append((path, f"~/{global_rel}/ ({_agent_label(agent)}, portable)"))
    return result


# ── Project-local install (opt-in) ───────────────────────────────────────────
# (bootstrap-relative source path, destination relative to project dir, agent key).
# The source path is resolved against bootstrap_dir() for a wheel, or mapped to
# the repo layout for a source checkout (see _resolve_bootstrap_src).
BOOTSTRAP_FILES = [
    ("AGENTS.md", "AGENTS.md", None),
    ("cursor/rules/beeweave.mdc", ".cursor/rules/beeweave.mdc", "cursor"),
    ("windsurf/rules/beeweave.md", ".windsurf/rules/beeweave.md", "windsurf"),
    ("kiro/steering/beeweave.md", ".kiro/steering/beeweave.md", "kiro"),
    ("agent/rules/beeweave.md", ".agent/rules/beeweave.md", "antigravity"),
    ("agent/workflows/beeweave.md", ".agent/workflows/beeweave.md", "antigravity"),
    ("github/copilot-instructions.md", ".github/copilot-instructions.md", "copilot"),
]

AGENTS_ALIASES = {
    "claude": ("CLAUDE.md",),
    "gemini": ("GEMINI.md",),
    "antigravity": ("GEMINI.md",),
    "hermes": ("HERMES.md",),
}


VAULT_DIRS = (
    "concepts",
    "entities",
    "skills",
    "references",
    "synthesis",
    "projects",
    "_meta",
    "_archives",
    "_staging",
    ".obsidian",
)

WORKBENCH_DIRS = (
    "inbox/captures",
    "inbox/web",
    "inbox/archived",
    "inbox/rejected",
    "articles/drafts",
    "articles/published",
    "library",
)


def _ensure_gitkeep(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()


def init_vault_layout(vault_path: str | Path) -> None:
    vault = Path(vault_path).expanduser().resolve()
    for rel in VAULT_DIRS:
        _ensure_gitkeep(vault / rel)


def init_workbench_layout(workbench_path: str | Path) -> None:
    workbench = Path(workbench_path).expanduser().resolve()
    for rel in WORKBENCH_DIRS:
        _ensure_gitkeep(workbench / rel)


def write_project_env(project_dir: Path) -> None:
    env = project_dir / ".env"
    if env.exists():
        return
    env.write_text(
        'BEEWEAVE_VAULT_PATH="./vault"\n'
        'BEEWEAVE_SOURCES_DIR="./workbench"\n',
        encoding="utf-8",
    )
    print("✅  Created project .env")


def _resolve_bootstrap_src(boot_root: Path, rel: str) -> Path | None:
    """Resolve a bootstrap source path under a wheel layout or repo layout."""
    built = boot_root / rel
    if built.exists():
        return built
    # Source checkout: boot_root is the repo root; bootstrap sources live under
    # bootstrap/ and are copied to the agent-specific destination paths.
    repo_rel = {
        "AGENTS.md": "bootstrap/AGENTS.md",
        "cursor/rules/beeweave.mdc": "bootstrap/cursor/rules/beeweave.mdc",
        "windsurf/rules/beeweave.md": "bootstrap/windsurf/rules/beeweave.md",
        "kiro/steering/beeweave.md": "bootstrap/kiro/steering/beeweave.md",
        "agent/rules/beeweave.md": "bootstrap/agent/rules/beeweave.md",
        "agent/workflows/beeweave.md": "bootstrap/agent/workflows/beeweave.md",
        "github/copilot-instructions.md": ".github/copilot-instructions.md",
    }.get(rel)
    if repo_rel and (boot_root / repo_rel).exists():
        return boot_root / repo_rel
    return None


def install_project(project_dir: Path, mode: str, agents: list[str]) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁  Installing project-local files → {project_dir}")
    write_project_env(project_dir)
    init_vault_layout(project_dir / "vault")
    init_workbench_layout(project_dir / "workbench")
    print("✅  Initialized project vault/ and workbench/ layout")

    installed_project_dirs: set[str] = set()
    for agent in agents:
        project_rel = AGENTS[agent]["project"]
        if project_rel is None or project_rel in installed_project_dirs:
            continue
        installed_project_dirs.add(str(project_rel))
        install_skills(project_dir / str(project_rel), f"{project_rel}/ ({_agent_label(agent)}, full)", mode=mode)

    boot_root = bootstrap_dir()
    if boot_root is None:
        print("   ⚠️  Bootstrap files not found in package; skipping context files")
        return

    selected = set(agents)
    installed_bootstrap = 0
    for rel, dest, agent in BOOTSTRAP_FILES:
        if agent is not None and agent not in selected:
            continue
        src = _resolve_bootstrap_src(boot_root, rel)
        if src is None:
            continue
        dst = project_dir / dest
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink() or dst.exists():
            if dst.is_dir() and not dst.is_symlink():
                continue
            dst.unlink()
        shutil.copyfile(src, dst)
        installed_bootstrap += 1
    print(f"✅  Installed {installed_bootstrap} bootstrap context file(s)")

    # AGENTS.md aliases as relative symlinks (copy fallback for symlink-hostile FS).
    aliases = sorted({
        alias
        for agent in agents
        for alias in AGENTS_ALIASES.get(agent, ())
    })
    for alias in aliases:
        link = project_dir / alias
        if link.is_symlink() or link.exists():
            link.unlink()
        try:
            link.symlink_to("AGENTS.md")
        except OSError:
            shutil.copyfile(project_dir / "AGENTS.md", link)
    if aliases:
        print(f"✅  Linked AGENTS.md aliases ({', '.join(aliases)})")


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


def uninstall_project(project_dir: Path, agents: list[str]) -> int:
    removed = 0
    if not project_dir.exists():
        return 0
    print(f"\n📁  Removing project-local BeeWeave files → {project_dir}")

    installed_project_dirs: set[str] = set()
    for agent in agents:
        project_rel = AGENTS[agent]["project"]
        if project_rel is None or project_rel in installed_project_dirs:
            continue
        installed_project_dirs.add(str(project_rel))
        removed += uninstall_skills(
            project_dir / str(project_rel),
            f"{project_rel}/ ({_agent_label(agent)}, full)",
        )

    boot_root = bootstrap_dir()
    selected = set(agents)
    removed_bootstrap = 0
    if boot_root is not None:
        for rel, dest, agent in BOOTSTRAP_FILES:
            if agent is not None and agent not in selected:
                continue
            src = _resolve_bootstrap_src(boot_root, rel)
            if src is not None and _remove_file_if_managed(project_dir / dest, src):
                removed_bootstrap += 1

    aliases = sorted({
        alias
        for agent in agents
        for alias in AGENTS_ALIASES.get(agent, ())
    })
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
            agents_source = _resolve_bootstrap_src(boot_root, "AGENTS.md") if boot_root is not None else None
            compare_to = agents_path if agents_path.is_file() else agents_source
            if compare_to is not None and alias_path.read_bytes() == compare_to.read_bytes():
                alias_path.unlink()
                removed_bootstrap += 1

    env = project_dir / ".env"
    default_env = 'BEEWEAVE_VAULT_PATH="./vault"\nBEEWEAVE_SOURCES_DIR="./workbench"\n'
    if env.is_file() and env.read_text(encoding="utf-8") == default_env:
        env.unlink()
        removed_bootstrap += 1

    if removed_bootstrap:
        print(f"✅  Removed {removed_bootstrap} project bootstrap/config file(s)")
    return removed + removed_bootstrap


# ── Config ───────────────────────────────────────────────────────────────────
def _read_config_value(key: str) -> str:
    if not GLOBAL_CONFIG.is_file():
        return ""
    for line in GLOBAL_CONFIG.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def resolve_vault_path(cli_vault: str | None, *, default_project_vault: Path | None = None) -> str:
    if cli_vault:
        return os.path.expanduser(cli_vault)
    if default_project_vault is not None:
        return str(default_project_vault)
    existing = _read_config_value("BEEWEAVE_VAULT_PATH")
    if existing and existing != "/path/to/your/vault":
        return existing
    return existing


def write_config(vault_path: str) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # BEEWEAVE_REPO points at the bundled data root so skills that reference
    # framework assets (templates, references) can find them post-install.
    repo_root = skills_dir().parent
    GLOBAL_CONFIG.write_text(
        f'BEEWEAVE_VAULT_PATH="{vault_path}"\n'
        f'BEEWEAVE_REPO="{repo_root}"\n'
        f'BEEWEAVE_VERSION="{__version__}"\n'
    )
    print(f"✅  Global config written to {GLOBAL_CONFIG}")


def _check_stale() -> None:
    """Warn if the installed version doesn't match when setup last ran, or if skills are missing."""
    if not GLOBAL_CONFIG.is_file():
        print(
            f"⚠️  BeeWeave {__version__} is installed but setup has never been run.\n"
            f"   Run: bwe setup",
            file=sys.stderr,
        )
        return

    setup_version = _read_config_value("BEEWEAVE_VERSION")
    if setup_version and setup_version != __version__:
        print(
            f"⚠️  BeeWeave upgraded {setup_version} → {__version__} but setup hasn't been re-run.\n"
            f"   New skills won't be available until you run: bwe setup",
            file=sys.stderr,
        )
        return

    # Even if the version matches, check that ~/.claude/skills has the full set.
    claude_skills_dir = HOME / ".claude" / "skills"
    if claude_skills_dir.is_dir():
        bundled = set(list_skills())
        installed = {p.name for p in claude_skills_dir.iterdir() if p.is_dir()}
        missing = bundled - installed
        if missing:
            print(
                f"⚠️  {len(missing)} skill(s) missing from ~/.claude/skills/ "
                f"(e.g. {', '.join(sorted(missing)[:3])}{', ...' if len(missing) > 3 else ''}).\n"
                f"   Run: bwe setup",
                file=sys.stderr,
            )


# ── Commands ─────────────────────────────────────────────────────────────────
def cmd_setup(args: argparse.Namespace) -> int:
    mode = "copy" if args.copy else "symlink"
    print("\n╔══════════════════════════════════════════════════╗")
    print("║               BeeWeave Agent Setup               ║")
    print("╚══════════════════════════════════════════════════╝\n")

    try:
        selected_global_extra = choose_global_extra(args.global_extra, no_global=args.no_global)
        selected_agents = choose_agents(args.agents)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    project_dir: Path | None = None
    if not args.no_project_local:
        project_dir = Path(args.project or os.getcwd()).expanduser().resolve()

    default_project_vault = project_dir / "vault" if project_dir is not None else None
    vault_path = resolve_vault_path(args.vault, default_project_vault=default_project_vault)
    if vault_path:
        init_vault_layout(vault_path)
        print(f"✅  Initialized vault layout → {Path(vault_path).expanduser().resolve()}")
    write_config(vault_path)
    if not vault_path:
        print("    → Vault path not set yet. Re-run with `--vault /path/to/vault`")
        print("      or edit BEEWEAVE_VAULT_PATH in ~/.beeweave/config.")

    if selected_agents:
        print(f"✅  Selected agents: {', '.join(selected_agents)}")
    else:
        print("✅  Selected agents: none")
    if not args.no_global:
        print(f"✅  Global skills: {', '.join(_portable_skills(selected_global_extra))}")

    if not args.no_global and selected_agents:
        install_global_skills_for_agents(selected_agents, mode, selected_global_extra)

    if project_dir is not None:
        install_project(project_dir, mode, selected_agents)

    n = len(list_skills())
    print("\n───────────────────────────────────────────────────")
    print(" Setup complete!\n")
    print(f" Skills installed: {n}  (mode: {mode})")
    if selected_agents:
        print(f" Agents:           {', '.join(selected_agents)}")
    if not args.no_global:
        print(f" Global skills:    {', '.join(_portable_skills(selected_global_extra))}")
    if vault_path:
        print(f" Vault:            {vault_path}")
    if project_dir is not None:
        print(f" Project:          {project_dir}")
    print("\n Next steps:")
    if project_dir is not None:
        print("   1. Open this project in your agent")
        print("   2. Start using the installed skills directly:")
        print("      /beeweave-ingest workbench/inbox")
        print("      /beeweave-query what do I know about ...")
        print("      /beeweave-update")
    else:
        print("   1. Open any project in your agent")
        print("   2. Use the portable skills installed for cross-project work:")
        print("      /beeweave-update")
        print("      /beeweave-query what do I know about ...")
    print("\n From any project:")
    print("   /beeweave-update    → sync project knowledge into your vault")
    print("   /beeweave-query     → ask questions against your compiled vault")
    print("───────────────────────────────────────────────────\n")
    return 0


def _confirm_uninstall(args: argparse.Namespace, agents: list[str], project_dir: Path | None) -> bool:
    if args.yes:
        return True
    print("BeeWeave uninstall will remove:")
    if not args.no_global:
        print(f"  - global BeeWeave skills for agents: {', '.join(agents)}")
    if project_dir is not None:
        print(f"  - project-local BeeWeave skills/bootstrap files under: {project_dir}")
    if not args.keep_config:
        print(f"  - BeeWeave config directory: {GLOBAL_CONFIG_DIR}")
    print("It will not remove your vault or workbench content.")
    if not sys.stdin.isatty():
        print("error: refusing to uninstall without --yes in a non-interactive shell", file=sys.stderr)
        return False
    from InquirerPy import inquirer

    return bool(inquirer.confirm(message="Continue?", default=False).execute())


def uninstall_global_config() -> int:
    if not GLOBAL_CONFIG_DIR.exists():
        return 0
    shutil.rmtree(GLOBAL_CONFIG_DIR)
    print(f"✅  Removed BeeWeave config → {GLOBAL_CONFIG_DIR}")
    return 1


def cmd_uninstall(args: argparse.Namespace) -> int:
    try:
        selected_agents = _parse_agent_list(args.agents or "all")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    project_dir: Path | None = None
    if not args.no_project_local:
        project_dir = Path(args.project or os.getcwd()).expanduser().resolve()

    if not _confirm_uninstall(args, selected_agents, project_dir):
        print("Uninstall cancelled.")
        return 1

    removed = 0
    if not args.no_global:
        for target, label in global_skill_dirs_for_agents(selected_agents):
            removed += uninstall_skills(target, label)

    if project_dir is not None:
        removed += uninstall_project(project_dir, selected_agents)

    if not args.keep_config:
        removed += uninstall_global_config()

    print("\n───────────────────────────────────────────────────")
    print(" Uninstall complete!")
    print(f" Removed items: {removed}")
    print(" Vault/workbench content was left in place.")
    print("───────────────────────────────────────────────────\n")
    return 0


def cmd_graph_query(args: argparse.Namespace) -> int:
    from beeweave.graphrag import query
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault not found: {vault}", file=sys.stderr)
        return 1
    result = query(vault, args.question, top_n=args.top, max_should_read=args.max_read)
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    return 0


def cmd_batch_plan(args: argparse.Namespace) -> int:
    from beeweave.batch import plan_batches
    source_dir = Path(args.source_dir).expanduser().resolve()
    vault = Path(args.vault).expanduser().resolve()
    if not source_dir.is_dir():
        print(f"error: source directory not found: {source_dir}", file=sys.stderr)
        return 1
    result = plan_batches(
        source_dir,
        vault,
        max_batch_mb=args.max_mb,
        max_batch_files=args.max_files,
        skip_unchanged=not args.no_cache,
        include_code=args.include_code,
    )
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    return 0


def cmd_graph_analyse(args: argparse.Namespace) -> int:
    from beeweave.graph_analysis import analyse_vault
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(f"error: vault not found: {vault}", file=sys.stderr)
        return 1
    result = analyse_vault(vault, top_n=args.top)
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    return 0


def cmd_cache_check(args: argparse.Namespace) -> int:
    from beeweave.cache import check_sources
    vault = Path(args.vault).expanduser().resolve()
    sources = [Path(p).expanduser().resolve() for p in args.sources]
    result = check_sources(vault, sources)
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    return 0


def cmd_cache_update(args: argparse.Namespace) -> int:
    from beeweave.cache import update_source
    vault = Path(args.vault).expanduser().resolve()
    source = Path(args.source).expanduser().resolve()
    pages = args.pages or []
    h = update_source(vault, source, pages_produced=pages)
    print(json.dumps({"path": str(source), "content_hash": h}))
    return 0


def cmd_cache_hash(args: argparse.Namespace) -> int:
    from beeweave.cache import hash_file
    path = Path(args.path).expanduser().resolve()
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 1
    print(json.dumps({"path": str(path), "sha256": hash_file(path)}))
    return 0


def cmd_ast_extract(args: argparse.Namespace) -> int:
    from pathlib import Path
    from beeweave.ast_extractor import extract
    path = Path(args.path).expanduser().resolve()
    try:
        result = extract(path)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    for name in list_skills():
        print(name)
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    bundled = list_skills()
    print(f"BeeWeave {__version__}")
    print(f"skills:    {skills_dir()}")
    boot = bootstrap_dir()
    print(f"bootstrap: {boot if boot else '(not found)'}")
    print(f"config:    {GLOBAL_CONFIG}{'' if GLOBAL_CONFIG.exists() else ' (not written yet)'}")
    if GLOBAL_CONFIG.exists():
        vp = _read_config_value("BEEWEAVE_VAULT_PATH")
        setup_ver = _read_config_value("BEEWEAVE_VERSION")
        print(f"vault:     {vp or '(unset)'}")
        print(f"setup ran: {setup_ver or '(never)'}")
    print(f"bundled skills: {len(bundled)}")
    print()
    print("Agent skill install status:")
    core_set = set(_portable_skills())
    recommended_extra_set = set(RECOMMENDED_GLOBAL_EXTRA_SKILLS)
    seen_dirs: set[str] = set()
    for agent, meta in AGENTS.items():
        rel = meta["global"]
        if rel is None or rel in seen_dirs:
            continue
        seen_dirs.add(str(rel))
        agent_dir = HOME / str(rel)
        label = f"~/{rel}/ ({meta['label']}, portable)"
        if not agent_dir.is_dir():
            print(f"  {label}: not installed")
            continue
        installed = {p.name for p in agent_dir.iterdir() if p.is_dir()}
        wiki_installed = installed & core_set
        missing = core_set - installed
        extras_installed = sorted(installed & recommended_extra_set)
        status = "✅" if not missing else "⚠️ "
        print(f"  {status} {label}: core {len(wiki_installed)}/{len(core_set)}", end="")
        if missing:
            print(f"  (run: bwe setup)", end="")
        if extras_installed:
            print(f"  extras: {', '.join(extras_installed)}", end="")
        print()
    _check_stale()
    return 0


# ── Argument parsing ─────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bwe",
        description="Install BeeWeave agent skills for capture, creation, querying, and compiled vault maintenance.",
    )
    p.add_argument("-V", "--version", action="version", version=f"BeeWeave {__version__}")
    sub = p.add_subparsers(dest="command")

    sp = sub.add_parser("setup", help="install skills into your agents and write config (default)")
    _add_setup_args(sp)
    sp.set_defaults(func=cmd_setup)

    up = sub.add_parser("uninstall", help="remove BeeWeave skills and config")
    _add_uninstall_args(up)
    up.set_defaults(func=cmd_uninstall)

    lp = sub.add_parser("list", help="list bundled skills")
    lp.set_defaults(func=cmd_list)

    ip = sub.add_parser("info", help="show install paths, version, and config")
    ip.set_defaults(func=cmd_info)

    gq = sub.add_parser(
        "graph-query",
        help="answer a question from the vault's wikilink index without reading page bodies",
    )
    gq.add_argument("vault", help="path to the Obsidian vault")
    gq.add_argument("question", help="question to answer")
    gq.add_argument("--top", type=int, default=8, help="number of candidate pages to rank (default: 8)")
    gq.add_argument("--max-read", type=int, default=3, help="max pages to return in should_read (default: 3)")
    gq.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    gq.set_defaults(func=cmd_graph_query)

    bp = sub.add_parser(
        "batch-plan",
        help="split a source directory into parallel-ingest batches, skipping unchanged files",
    )
    bp.add_argument("vault", help="path to the Obsidian vault")
    bp.add_argument("source_dir", help="directory of source documents to ingest")
    bp.add_argument("--max-mb", type=float, default=2.0, help="max MB per batch (default: 2)")
    bp.add_argument("--max-files", type=int, default=20, help="max files per batch (default: 20)")
    bp.add_argument("--no-cache", action="store_true", help="disable manifest-based skip of unchanged files")
    bp.add_argument("--include-code", action="store_true", help="include code files (default: excluded; use ast-extract instead)")
    bp.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    bp.set_defaults(func=cmd_batch_plan)

    ga = sub.add_parser(
        "graph-analyse",
        help="analyse the vault's wikilink graph: god nodes, communities, surprising connections",
    )
    ga.add_argument("vault", help="path to the Obsidian vault")
    ga.add_argument("--top", type=int, default=20, help="number of top results to return (default: 20)")
    ga.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    ga.set_defaults(func=cmd_graph_analyse)

    cc = sub.add_parser(
        "cache-check",
        help="check which sources are new/modified/unchanged vs. .manifest.json",
    )
    cc.add_argument("vault", help="path to the Obsidian vault")
    cc.add_argument("sources", nargs="+", help="source file or directory paths to check")
    cc.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    cc.set_defaults(func=cmd_cache_check)

    cu = sub.add_parser(
        "cache-update",
        help="record a source's current SHA-256 hash in .manifest.json after ingestion",
    )
    cu.add_argument("vault", help="path to the Obsidian vault")
    cu.add_argument("source", help="source file or directory that was just ingested")
    cu.add_argument("--pages", nargs="*", metavar="PAGE", help="vault-relative paths of pages produced")
    cu.set_defaults(func=cmd_cache_update)

    ch = sub.add_parser(
        "cache-hash",
        help="compute the SHA-256 hash of a file or directory (no manifest I/O)",
    )
    ch.add_argument("path", help="file or directory to hash")
    ch.set_defaults(func=cmd_cache_hash)

    ap = sub.add_parser(
        "ast-extract",
        help="extract code structure (classes, functions, imports) from a file or directory — no LLM, no API calls",
    )
    ap.add_argument("path", help="file or directory to extract from")
    ap.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    ap.set_defaults(func=cmd_ast_extract)

    return p


def _add_setup_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--vault", metavar="PATH", help="path to your Obsidian vault (default: project ./vault)")
    sp.add_argument(
        "--project",
        nargs="?",
        const="",
        default=None,
        metavar="DIR",
        help="project directory for vault/workbench and project-local skills "
        "(defaults to the current directory)",
    )
    sp.add_argument(
        "--agents",
        metavar="LIST",
        help='agents to install for: comma-separated names, "all", or "none". '
        "When omitted in a terminal, setup shows a numbered selection menu.",
    )
    sp.add_argument(
        "--no-global",
        action="store_true",
        help="skip global portable skill installs",
    )
    sp.add_argument(
        "--global-extra",
        metavar="LIST",
        help="comma-separated optional global skills to install in addition to "
        "beeweave-update,beeweave-query,beeweave-ingest; supported: "
        + ",".join(RECOMMENDED_GLOBAL_EXTRA_SKILLS),
    )
    sp.add_argument(
        "--no-project-local",
        action="store_true",
        help="skip project-local layout, skills, and bootstrap files",
    )
    sp.add_argument(
        "--project-only",
        action="store_true",
        dest="no_global",
        help=argparse.SUPPRESS,
    )
    sp.add_argument(
        "--copy",
        action="store_true",
        help="copy skill files instead of symlinking to the installed package",
    )


def _add_uninstall_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--agents",
        metavar="LIST",
        help='agents to uninstall from: comma-separated names, "all", or "none" '
        '(default: "all")',
    )
    sp.add_argument(
        "--project",
        nargs="?",
        const="",
        default=None,
        metavar="DIR",
        help="project directory to clean project-local skills/bootstrap files "
        "(defaults to the current directory)",
    )
    sp.add_argument(
        "--no-global",
        action="store_true",
        help="keep global agent skill installs",
    )
    sp.add_argument(
        "--no-project-local",
        action="store_true",
        help="skip project-local skill/bootstrap cleanup",
    )
    sp.add_argument(
        "--keep-config",
        action="store_true",
        help="keep ~/.beeweave config files",
    )
    sp.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="confirm uninstall without prompting",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    # No subcommand → default to `setup` (the common case).
    if not argv or (argv[0].startswith("-") and argv[0] not in ("-h", "--help", "-V", "--version")):
        argv = ["setup", *argv]
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    # Warn about stale installs on every command except `setup` (which fixes it)
    # and `info` (which calls _check_stale itself with richer output).
    if getattr(args, "command", None) not in ("setup", "uninstall", "info", None):
        _check_stale()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nsetup cancelled.", file=sys.stderr)
        return 130
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
