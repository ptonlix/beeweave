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
from datetime import datetime
from pathlib import Path

from beeweave import __version__, external, illustrate_doctor, profiles, ui, uninstall, update_notice, upgrade

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
    "beeweave-article-illustration": "set up and run article illustration through Baoyu API image generation",
    "beeweave-article-publisher": "publish workbench drafts and ingest finished articles into the wiki",
    "beeweave-article-writer": "long-form articles, blog posts, essays, and opinion pieces",
    "beeweave-ppt-writer": "HTML PPT decks and presentation projects using external PPT skills",
    "beeweave-social-writer": "X/Twitter posts, threads, short takes, and social copy",
    "beeweave-writing-skill-evolver": "review, validate, activate, reject, and compact learned writing rules",
    "beeweave-writing-style-initializer": "initialize Workbench writing style asset templates",
    "beeweave-writing-style-learner": "extract pending writing style rules from articles, traces, diffs, and feedback",
    "beeweave-url-capture": "download URLs into workbench/inbox/web as raw capture bundles",
    "baoyu-url-to-markdown": "project-local URL extraction dependency for workbench captures",
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
        "Could not locate bundled skills. Reinstall beeweave (`pip install --force-reinstall beeweave`)."
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
        "project": ".agents/skills",
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
            f"unknown or unsupported global extra skill(s): {', '.join(unknown)}; recommended extras: {known}"
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
        if name not in CORE_PORTABLE_SKILLS and name not in RECOMMENDED_GLOBAL_EXTRA_SKILLS
    }
    ui.print_table(
        "Wiki/project-local skills",
        ("Skill", "Description", "Status"),
        [
            (name, description, "bundled" if name in available else "not bundled")
            for name, description in local_wiki.items()
        ],
    )
    print()
    ui.print_table(
        "Workbench/project-local skills",
        ("Skill", "Description", "Status"),
        [
            (name, description, "bundled" if name in available else "not bundled")
            for name, description in WORKBENCH_SKILL_DESCRIPTIONS.items()
        ],
    )


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
    print("  Global skills always installed:")
    for skill in CORE_PORTABLE_SKILLS:
        print(f"    [x] {skill}")
    _print_project_local_skill_summary()
    print()
    choices = [
        ui.PromptChoice(
            skill,
            name=f"{skill} - {GLOBAL_EXTRA_DESCRIPTIONS[skill]}",
            enabled=False,
        )
        for skill in RECOMMENDED_GLOBAL_EXTRA_SKILLS
    ]
    selected = ui.checkbox_prompt(
        message="Optional advanced global skills:",
        choices=choices,
        instruction="(↑↓ move, space select, enter confirm; default none)",
        height=min(8, len(choices)),
    )
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
    choices = [
        ui.PromptChoice(
            agent,
            name=f"{agent} - {meta['label']}",
            enabled=agent in DEFAULT_AGENTS,
        )
        for agent, meta in AGENTS.items()
    ]
    selected = ui.checkbox_prompt(
        message="Select agents:",
        choices=choices,
        instruction="(↑↓ move, space select, enter confirm)",
        height=min(12, len(choices)),
    )
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
    install_skills(
        HOME / ".hermes" / "skills", "~/.hermes/skills/ (Hermes default, portable)", subset=portable, mode=mode
    )
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

AGENTS_ALIASES: dict[str, tuple[str, ...]] = {
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
    "writing/style",
    "writing/traces",
    "writing/eval",
    "ppt",
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
        'BEEWEAVE_VAULT_PATH="./vault"\nBEEWEAVE_WORKBENCH_PATH="./workbench"\n',
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
    for rel, dest, bootstrap_agent in BOOTSTRAP_FILES:
        if bootstrap_agent is not None and bootstrap_agent not in selected:
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
    aliases = sorted({alias for agent in agents for alias in AGENTS_ALIASES.get(agent, ())})
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


# ── Config ───────────────────────────────────────────────────────────────────
def _read_config_value_from(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def _read_config_value(key: str) -> str:
    return _read_config_value_from(GLOBAL_CONFIG, key)


def resolve_vault_path(
    cli_vault: str | None,
    *,
    default_project_vault: Path | None = None,
    config_path: Path | None = None,
) -> str:
    if cli_vault:
        return os.path.expanduser(cli_vault)
    if default_project_vault is not None:
        return str(default_project_vault)
    existing = _read_config_value_from(config_path or GLOBAL_CONFIG, "BEEWEAVE_VAULT_PATH")
    if existing and existing != "/path/to/your/vault":
        return existing
    return existing


def _default_workbench_path(vault_path: str) -> str:
    if not vault_path:
        return ""
    vault = Path(vault_path).expanduser()
    return str(vault.parent / "workbench")


def write_config(vault_path: str, workbench_path: str | None = None, *, config_path: Path | None = None) -> None:
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # BEEWEAVE_REPO points at the bundled data root so skills that reference
    # framework assets (templates, references) can find them post-install.
    repo_root = skills_dir().parent
    resolved_workbench = workbench_path or _default_workbench_path(vault_path)
    target = config_path or GLOBAL_CONFIG
    target.write_text(
        f'BEEWEAVE_VAULT_PATH="{vault_path}"\n'
        f'BEEWEAVE_WORKBENCH_PATH="{resolved_workbench}"\n'
        f'BEEWEAVE_REPO="{repo_root}"\n'
        f'BEEWEAVE_VERSION="{__version__}"\n'
    )
    print(f"✅  BeeWeave config written to {target}")


def _check_stale() -> None:
    """Warn if the installed version doesn't match when setup last ran, or if skills are missing."""
    if not GLOBAL_CONFIG.is_file():
        print(
            f"⚠️  BeeWeave {__version__} is installed but setup has never been run.\n   Run: bwe setup",
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

    # Even if the version matches, check that ~/.claude/skills has the portable
    # global set. Project-local wiki/workbench skills intentionally do not live
    # in ~/.claude/skills.
    claude_skills_dir = HOME / ".claude" / "skills"
    if claude_skills_dir.is_dir():
        bundled = set(_portable_skills())
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
    ui.print_setup_banner(__version__)
    update_notice.maybe_print_update_notice(
        current_version=__version__,
        config_dir=GLOBAL_CONFIG_DIR,
        package_file=__file__,
    )

    try:
        selected_profile = profiles.choose_profile(
            args.profile,
            config_dir=GLOBAL_CONFIG_DIR,
            default_config=GLOBAL_CONFIG,
        )
        selected_global_extra = choose_global_extra(args.global_extra, no_global=args.no_global)
        selected_agents = choose_agents(args.agents)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    config_path = profiles.config_path_for_profile(
        selected_profile,
        config_dir=GLOBAL_CONFIG_DIR,
        default_config=GLOBAL_CONFIG,
    )

    project_dir: Path | None = None
    if not args.no_project_local:
        project_dir = Path(args.project or os.getcwd()).expanduser().resolve()

    default_project_vault = project_dir / "vault" if project_dir is not None else None
    vault_path = resolve_vault_path(args.vault, default_project_vault=default_project_vault, config_path=config_path)
    if vault_path:
        init_vault_layout(vault_path)
        print(f"✅  Initialized vault layout → {Path(vault_path).expanduser().resolve()}")
    workbench_path = str(project_dir / "workbench") if project_dir is not None else None
    write_config(vault_path, workbench_path, config_path=config_path)
    if not vault_path:
        print("    → Vault path not set yet. Re-run with `--vault /path/to/vault`")
        print(f"      or edit BEEWEAVE_VAULT_PATH in {config_path}.")

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
    summary_rows: list[tuple[str, str | int | None]] = [
        ("Skills installed", f"{n} (mode: {mode})"),
        ("Profile", selected_profile),
        ("Config", str(config_path)),
    ]
    if selected_agents:
        summary_rows.append(("Agents", ", ".join(selected_agents)))
    else:
        summary_rows.append(("Agents", "none"))
    if not args.no_global:
        summary_rows.append(("Global skills", ", ".join(_portable_skills(selected_global_extra))))
    else:
        summary_rows.append(("Global skills", "skipped"))
    if vault_path:
        summary_rows.append(("Vault", vault_path))
    if project_dir is not None:
        summary_rows.append(("Project", str(project_dir)))
        summary_rows.append(("Workbench", str(project_dir / "workbench")))
    summary_rows.append(("Install mode", mode))

    print()
    ui.print_summary_panel("Setup complete", summary_rows)
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
        print("      /beeweave-ingest /path/to/source")
        print("      /beeweave-update")
        print("      /beeweave-query what do I know about ...")
    print("\n From any project:")
    print("   /beeweave-ingest    → ingest files, folders, URLs, or workbench inbox content")
    print("   /beeweave-update    → sync project knowledge into your vault")
    print("   /beeweave-query     → ask questions against your compiled vault")
    print()
    if getattr(args, "_record_state", True):
        installer = upgrade.detect_install_method(package_file=__file__)
        recorded_workbench_path = workbench_path or _default_workbench_path(vault_path or "")
        upgrade.record_setup_state(
            config_dir=GLOBAL_CONFIG_DIR,
            profile=selected_profile,
            config_path=config_path,
            project_dir=project_dir,
            vault_path=vault_path or "",
            workbench_path=recorded_workbench_path,
            agents=selected_agents,
            global_extra=selected_global_extra,
            no_global=args.no_global,
            no_project_local=args.no_project_local,
            copy=args.copy,
            version=__version__,
            installer=installer,
        )
    return 0


def _uninstall_context() -> uninstall.UninstallContext:
    return uninstall.UninstallContext(
        home=HOME,
        global_config_dir=GLOBAL_CONFIG_DIR,
        global_config=GLOBAL_CONFIG,
        agents=AGENTS,
        bootstrap_files=BOOTSTRAP_FILES,
        agent_aliases=AGENTS_ALIASES,
        list_skills=list_skills,
        bootstrap_dir=bootstrap_dir,
        resolve_bootstrap_src=_resolve_bootstrap_src,
    )


def cmd_uninstall(args: argparse.Namespace) -> int:
    try:
        selected_agents = _parse_agent_list(args.agents or "all")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    update_notice.maybe_print_update_notice(
        current_version=__version__,
        config_dir=GLOBAL_CONFIG_DIR,
        package_file=__file__,
    )
    return uninstall.run_uninstall(_uninstall_context(), args, selected_agents)


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


def _external_paths() -> external.ExternalPaths:
    return external.external_paths(GLOBAL_CONFIG_DIR)


def cmd_external_install(args: argparse.Namespace) -> int:
    paths = _external_paths()
    source = external.parse_source(args.source)
    repo_root, commit = external.prepare_source_root(paths, source, ref=args.ref)
    candidates = external.select_candidates(
        repo_root,
        path=args.path,
        skill=args.skill,
        all_skills=args.all,
        tree_path=source.tree_path,
    )
    installed = external.install_candidates(
        paths,
        source=source,
        repo_root=repo_root,
        candidates=candidates,
        ref=args.ref,
        commit=commit,
        link_project=Path(args.link_project).expanduser().resolve() if args.link_project else None,
        agents=AGENTS,
    )
    for name in installed:
        print(f"installed {name}")
    return 0


def cmd_external_link(args: argparse.Namespace) -> int:
    paths = _external_paths()
    result = external.link_external_skill(
        paths,
        args.skill_name,
        Path(args.project).expanduser().resolve(),
        agents=AGENTS,
    )
    for path in result.linked:
        print(f"linked {path}")
    for path in result.skipped:
        print(f"already linked {path}")
    for path in result.conflicts:
        print(f"conflict {path}")
    for path, reason in result.failed:
        print(f"failed {path}: {reason}")
    return 1 if result.conflicts or result.failed else 0


def cmd_external_list(args: argparse.Namespace) -> int:
    paths = _external_paths()
    data = external.read_manifest(paths)
    skills = data.get("skills", {})
    if not skills:
        ui.print_status("info", "No external skills installed.")
        ui.print_status("info", "Install one with: bwe external install <source> --skill <name> --link-project .")
        return 0

    rows: list[tuple[str, str, str, str, str]] = []
    for name, record in skills.items():
        commit = str(record.get("resolved_commit") or "-")
        short_commit = commit[:12] if commit != "-" else "-"
        linked = len(record.get("linked_projects", []))
        rows.append(
            (
                name,
                str(record.get("source", "")),
                str(record.get("subpath", "") or "."),
                short_commit,
                str(linked),
            )
        )

    ui.print_table(
        "External skills",
        ("Skill", "Source", "Subpath", "Commit", "Project links"),
        rows,
        caption="Details: bwe external info <skill>",
    )
    return 0


def _external_info_rows(name: str, record: dict[str, object]) -> list[tuple[str, str | int | None]]:
    linked_projects = record.get("linked_projects", [])
    if isinstance(linked_projects, list):
        linked = "\n".join(str(path) for path in linked_projects) if linked_projects else "none"
    else:
        linked = str(linked_projects)
    license_value = record.get("license")
    return [
        ("Skill", name),
        ("Source", str(record.get("source", ""))),
        ("Subpath", str(record.get("subpath", "") or ".")),
        ("Install path", str(record.get("install_path", "") or record.get("path", "") or "(unknown)")),
        ("Commit", str(record.get("resolved_commit", "") or "-")),
        ("License", str(license_value) if license_value else "(unknown)"),
        ("Installed at", str(record.get("installed_at", "") or "(unknown)")),
        ("Linked projects", linked),
    ]


def cmd_external_info(args: argparse.Namespace) -> int:
    paths = _external_paths()
    data = external.read_manifest(paths)
    record = data.get("skills", {}).get(args.skill_name)
    if record is None:
        raise RuntimeError(f"external skill is not installed: {args.skill_name}")
    ui.print_detail_panel("External skill info", _external_info_rows(args.skill_name, record), preserve_values=True)
    return 0


def cmd_external_update(args: argparse.Namespace) -> int:
    paths = _external_paths()
    updated = external.update_external_skill(paths, args.skill_name)
    for name in updated:
        print(f"updated {name}")
    return 0


def cmd_external_remove(args: argparse.Namespace) -> int:
    paths = _external_paths()
    removed_links = external.remove_external_skill(paths, args.skill_name)
    print(f"removed {args.skill_name}")
    for path in removed_links:
        print(f"removed link {path}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    bundled = list_skills()
    boot = bootstrap_dir()
    config_status = str(GLOBAL_CONFIG) if GLOBAL_CONFIG.exists() else f"{GLOBAL_CONFIG} (not written yet)"
    vault_path = "(unset)"
    workbench_path = "(unset)"
    setup_ver = "(never)"
    if GLOBAL_CONFIG.exists():
        vault_path = _read_config_value("BEEWEAVE_VAULT_PATH") or "(unset)"
        workbench_path = _read_config_value("BEEWEAVE_WORKBENCH_PATH") or "(unset)"
        setup_ver = _read_config_value("BEEWEAVE_VERSION") or "(never)"

    core_set = set(_portable_skills())
    recommended_extra_set = set(RECOMMENDED_GLOBAL_EXTRA_SKILLS)
    seen_dirs: set[str] = set()
    agent_statuses: list[str] = []
    for _agent, meta in AGENTS.items():
        rel = meta["global"]
        if rel is None or rel in seen_dirs:
            continue
        seen_dirs.add(str(rel))
        agent_dir = HOME / str(rel)
        label = f"~/{rel}/ ({meta['label']}, portable)"
        if not agent_dir.is_dir():
            agent_statuses.append(f"{label}: not installed")
            continue
        installed = {p.name for p in agent_dir.iterdir() if p.is_dir()}
        wiki_installed = installed & core_set
        missing = core_set - installed
        extras_installed = sorted(installed & recommended_extra_set)
        status = f"{label}: core {len(wiki_installed)}/{len(core_set)}"
        if missing:
            status += " (run: bwe setup)"
        if extras_installed:
            status += f" extras: {', '.join(extras_installed)}"
        agent_statuses.append(status)

    ui.print_summary_panel(
        "BeeWeave info",
        [
            ("Version", __version__),
            ("Config", config_status),
            ("Vault", vault_path),
            ("Workbench", workbench_path),
            ("Repo", str(skills_dir().parent)),
            ("Skills", f"{len(bundled)} bundled"),
            ("Bootstrap", str(boot) if boot else "(not found)"),
            ("Setup ran", setup_ver),
            ("Agents", "; ".join(agent_statuses) if agent_statuses else "none"),
        ],
    )
    _check_stale()
    return 0


def cmd_illustrate_doctor(args: argparse.Namespace) -> int:
    profile = profiles.parse_profile(args.profile)
    config_path = profiles.config_path_for_profile(profile, config_dir=GLOBAL_CONFIG_DIR, default_config=GLOBAL_CONFIG)
    resolution = illustrate_doctor.resolve_project_root(
        Path.cwd(),
        explicit_project=args.project,
        config_path=config_path,
    )
    project_root = resolution.project_root
    if args.probe_image:
        ui.print_status("warning", "probe-image 会发起一次真实图片生成探测，可能产生 provider 费用。")
        result, reused = illustrate_doctor.run_probe_image(
            project_root,
            args.provider,
            force=args.force,
            profile=profile,
            install_state_path=upgrade.install_state_path(GLOBAL_CONFIG_DIR),
        )
    else:
        result, reused = illustrate_doctor.run_non_billing_checks(
            project_root,
            args.provider,
            force=args.force,
            profile=profile,
            install_state_path=upgrade.install_state_path(GLOBAL_CONFIG_DIR),
        )

    rows: list[tuple[str, str | int | None]] = [
        ("Project", str(project_root)),
        ("Project source", resolution.source),
        ("Profile", profile),
        ("Provider", result.provider),
        ("Model", result.model or "(missing)"),
        ("Status", result.status),
        ("Check level", result.check_level),
        ("Cache", "reused" if reused else str(illustrate_doctor.doctor_cache_path(project_root))),
        ("Base URL", result.base_url or "(provider default)"),
    ]
    if result.response_kind:
        rows.append(("Response kind", result.response_kind))
    if result.verification:
        rows.append(("Verification", result.verification))
    if result.latency_ms is not None:
        rows.append(("Latency", f"{result.latency_ms} ms"))
    if result.warnings:
        rows.append(("Notes", "; ".join(result.warnings)))
    if result.errors:
        rows.append(("Errors", "; ".join(result.errors)))
    ui.print_summary_panel("Article illustration doctor", rows)
    return 0 if result.status == "passed" else 1


def _print_version_check(result: upgrade.VersionCheck) -> None:
    if result.latest is None:
        rows: list[tuple[str, str | int | None]] = [
            ("Current", result.current),
            ("Latest", "unknown"),
            ("Status", "could not check latest version"),
        ]
        if result.error:
            rows.append(("Reason", result.error))
        ui.print_detail_panel("BeeWeave upgrade check", rows)
        return
    rows = [
        ("Current", result.current),
        ("Latest", result.latest),
        ("Status", "update available" if result.status == "update_available" else "up to date"),
    ]
    if result.status == "update_available":
        rows.append(("Run", "bwe upgrade"))
    ui.print_detail_panel("BeeWeave upgrade check", rows)


def _replay_setup(entry: upgrade.ReplayEntry) -> int:
    args = argparse.Namespace(
        vault=entry.vault_path or None,
        profile=entry.profile,
        project=str(entry.project_dir) if entry.project_dir is not None else None,
        agents=",".join(entry.agents) if entry.agents else "none",
        no_global=entry.no_global,
        global_extra=",".join(entry.global_extra) if entry.global_extra else "none",
        no_project_local=entry.no_project_local,
        copy=entry.copy,
        _record_state=True,
    )
    return cmd_setup(args)


def _bundled_skills_readable() -> tuple[bool, str]:
    try:
        root = skills_dir()
        sample = next(iter(iter_skill_dirs()), None)
        if sample is None:
            return False, f"no bundled skills found under {root}"
        skill_file = sample / "SKILL.md"
        skill_file.stat()
    except (FileNotFoundError, OSError, RuntimeError, StopIteration) as exc:
        return False, str(exc)
    return True, str(skill_file)


def cmd_upgrade(args: argparse.Namespace) -> int:
    check = upgrade.check_version(__version__)
    if args.check:
        _print_version_check(check)
        return 0

    if check.latest is None:
        _print_version_check(check)
        return 1

    if check.status != "update_available":
        _print_version_check(check)
        return 0

    method = upgrade.detect_install_method(package_file=__file__)
    command = upgrade.upgrade_command(method)
    ui.print_detail_panel(
        "BeeWeave upgrade",
        [
            ("Current", check.current),
            ("Latest", check.latest),
            ("Installer", method.kind),
        ],
    )

    if command is None:
        ui.print_status("warning", "BeeWeave does not know how to upgrade this install automatically.")
        if method.detail:
            ui.print_status("info", f"Detected: {method.detail}")
        ui.print_status("info", "Recommended:")
        for line in upgrade.manual_upgrade_hint(method):
            print(f"  {line}")
        return 1

    print()
    ui.print_status("info", f"Running: {' '.join(command)}")
    result = upgrade.run_upgrade_command(command)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    if not result.ok:
        print(f"error: upgrade command failed with exit code {result.returncode}", file=sys.stderr)
        return result.returncode or 1

    ui.print_status("success", "Package upgrade completed")
    # The current Python process keeps the already-imported CLI code, but setup
    # replay reads bundled skill files from disk through skills_dir(). For normal
    # uv/pip upgrades those package-data files are replaced in the same location,
    # so replay can refresh agent skill directories without spawning a new bwe.
    # If the installer swapped environments or made the package data unreadable,
    # skip replay and ask the user to run setup from the newly installed command.
    readable, detail = _bundled_skills_readable()
    if not readable:
        print()
        ui.print_status("warning", "Package data is not readable after upgrade; skipping setup replay.")
        ui.print_status("info", f"Reason: {detail}")
        ui.print_status("info", "Run: bwe setup")
        return 0

    plan = upgrade.replay_plan(GLOBAL_CONFIG_DIR)
    if not plan.entries:
        print()
        ui.print_status("warning", "No recorded setup replay state found.")
        ui.print_status("info", "Run: bwe setup")
        for profile, reason in plan.skipped:
            print(f"Skipped {profile}: {reason}")
        return 0

    print()
    ui.print_status("info", "Refreshing installed skills from recorded setup profiles...")
    refreshed: list[str] = []
    failed: list[tuple[str, int]] = []
    for entry in plan.entries:
        print()
        print(f"Replay setup: {entry.profile}")
        code = _replay_setup(entry)
        if code == 0:
            refreshed.append(entry.profile)
        else:
            failed.append((entry.profile, code))

    print()
    rows: list[tuple[str, str | int | None]] = [
        ("Previous version", check.current),
        ("Latest version", check.latest),
        ("Installer", method.kind),
        ("Refreshed profiles", ", ".join(refreshed) if refreshed else "none"),
    ]
    if plan.skipped:
        rows.append(("Skipped profiles", "; ".join(f"{name}: {reason}" for name, reason in plan.skipped)))
    if failed:
        rows.append(("Failed profiles", "; ".join(f"{name}: exit {code}" for name, code in failed)))
    ui.print_summary_panel("Upgrade complete", rows)
    return 1 if failed else 0


def _confirm_profile_overwrite() -> bool:
    if not sys.stdin.isatty():
        print("error: refusing to overwrite default config without interactive YES", file=sys.stderr)
        return False
    try:
        entered = ui.text_prompt(
            message="Type YES to overwrite the default profile:",
            validate=lambda value: value == "YES",
            invalid_message='Type exactly "YES" to continue',
        ).strip()
    except (EOFError, ImportError):
        entered = input("Type YES to continue: ").strip()
    if entered != "YES":
        print("Cancelled.")
        return False
    return True


def cmd_profile_set_default(args: argparse.Namespace) -> int:
    try:
        profile = profiles.validate_profile_name(args.name)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if profile == "default":
        print("error: default is already the default profile", file=sys.stderr)
        return 1

    source = profiles.config_path_for_profile(profile, config_dir=GLOBAL_CONFIG_DIR, default_config=GLOBAL_CONFIG)
    if not source.is_file():
        print(f"error: profile config not found: {source}", file=sys.stderr)
        return 1

    now = datetime.now()
    backup = (
        profiles.backup_path_for_default(GLOBAL_CONFIG, now=now)
        if GLOBAL_CONFIG.exists() or GLOBAL_CONFIG.is_symlink()
        else None
    )
    print("Set BeeWeave default profile")
    print(f"  Source: {source}")
    print(f"  Target: {GLOBAL_CONFIG}")
    if backup is not None:
        print(f"  Backup: {backup}")
        print()
        print("This will overwrite the current default BeeWeave profile.")
        if not _confirm_profile_overwrite():
            return 1

    try:
        source, target, actual_backup = profiles.set_default_profile(
            profile,
            config_dir=GLOBAL_CONFIG_DIR,
            default_config=GLOBAL_CONFIG,
            now=now,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows: list[tuple[str, str | int | None]] = [
        ("Default", str(target)),
        ("Copied from", str(source)),
        ("Named profile", "preserved"),
    ]
    if actual_backup is not None:
        rows.append(("Backup", str(actual_backup)))
    ui.print_summary_panel("Default profile updated", rows)
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

    ug = sub.add_parser("upgrade", help="upgrade BeeWeave and refresh installed skills")
    ug.add_argument("--check", action="store_true", help="check latest version without changing files")
    ug.set_defaults(func=cmd_upgrade)

    lp = sub.add_parser("list", help="list bundled skills")
    lp.set_defaults(func=cmd_list)

    ip = sub.add_parser("info", help="show install paths, version, and config")
    ip.set_defaults(func=cmd_info)

    ep = sub.add_parser("external", help="manage user-installed external agent skills")
    external_sub = ep.add_subparsers(dest="external_command")
    ei = external_sub.add_parser("install", help="install an external skill from a repository or path")
    ei.add_argument("source", help="GitHub URL, git URL, owner/repo shorthand, tree URL, or local path")
    ei.add_argument("--skill", help="skill name to install from a multi-skill source")
    ei.add_argument("--path", help="repository subpath containing SKILL.md")
    ei.add_argument("--all", action="store_true", help="install every discovered skill from the source")
    ei.add_argument("--ref", help="git ref, branch, or tag to checkout")
    ei.add_argument("--link-project", metavar="PATH", help="also link the installed skill into an existing project")
    ei.set_defaults(func=cmd_external_install)

    el = external_sub.add_parser("link", help="link an installed external skill into a project")
    el.add_argument("skill_name", help="installed external skill name")
    el.add_argument("--project", default=".", help="project directory to link into (default: current directory)")
    el.set_defaults(func=cmd_external_link)

    exl = external_sub.add_parser("list", help="list installed external skills")
    exl.set_defaults(func=cmd_external_list)

    einfo = external_sub.add_parser("info", help="show external skill manifest details")
    einfo.add_argument("skill_name", help="installed external skill name")
    einfo.set_defaults(func=cmd_external_info)

    eu = external_sub.add_parser("update", help="update one or all installed external skills")
    eu.add_argument("skill_name", nargs="?", help="installed external skill name (default: all)")
    eu.set_defaults(func=cmd_external_update)

    er = external_sub.add_parser("remove", help="remove an installed external skill")
    er.add_argument("skill_name", help="installed external skill name")
    er.set_defaults(func=cmd_external_remove)

    pp = sub.add_parser("profile", help="manage BeeWeave profile config files")
    profile_sub = pp.add_subparsers(dest="profile_command")
    psd = profile_sub.add_parser("set-default", help="copy a named profile to ~/.beeweave/config")
    psd.add_argument("name", help="named profile to copy from ~/.beeweave/config.NAME")
    psd.set_defaults(func=cmd_profile_set_default)

    il = sub.add_parser("illustrate", help="doctor article illustration provider configuration")
    illustrate_sub = il.add_subparsers(dest="illustrate_command")
    doctor = illustrate_sub.add_parser("doctor", help="validate article illustration provider configuration")
    doctor.add_argument("--provider", required=True, choices=illustrate_doctor.SUPPORTED_PROVIDERS)
    doctor.add_argument(
        "--project",
        metavar="PATH",
        help="workspace/project root that contains .baoyu-skills (default: discover from cwd or BeeWeave config)",
    )
    doctor.add_argument(
        "--profile",
        metavar="NAME",
        help='BeeWeave profile config to resolve project root from (default: "default")',
    )
    doctor.add_argument(
        "--probe-image",
        action="store_true",
        help="send one explicit real image generation probe; this may incur provider charges",
    )
    doctor.add_argument("--force", action="store_true", help="ignore any existing passed doctor cache")
    doctor.set_defaults(func=cmd_illustrate_doctor)

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
    bp.add_argument(
        "--include-code", action="store_true", help="include code files (default: excluded; use ast-extract instead)"
    )
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
        "--profile",
        metavar="NAME",
        help='BeeWeave profile to write: "default" for ~/.beeweave/config, or NAME for ~/.beeweave/config.NAME',
    )
    sp.add_argument(
        "--project",
        nargs="?",
        const="",
        default=None,
        metavar="DIR",
        help="project directory for vault/workbench and project-local skills (defaults to the current directory)",
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
        "beeweave-update,beeweave-query,beeweave-ingest; supported: " + ",".join(RECOMMENDED_GLOBAL_EXTRA_SKILLS),
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
        help='agents to uninstall from: comma-separated names, "all", or "none" (default: "all")',
    )
    sp.add_argument(
        "--project",
        nargs="?",
        const="",
        default=None,
        metavar="DIR",
        help="project directory to clean project-local skills/bootstrap files (defaults to the current directory)",
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
        "--all",
        action="store_true",
        help="also clean project-local installs inferred from all ~/.beeweave/config* profiles",
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
    if getattr(args, "command", None) not in ("setup", "uninstall", "info", "upgrade", "external", None):
        _check_stale()
    try:
        code = args.func(args)
    except KeyboardInterrupt:
        print("\nsetup cancelled.", file=sys.stderr)
        return 130
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if getattr(args, "command", None) in ("info",):
        update_notice.maybe_print_update_notice(
            current_version=__version__,
            config_dir=GLOBAL_CONFIG_DIR,
            package_file=__file__,
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
