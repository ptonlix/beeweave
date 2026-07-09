"""External Agent Skill management for BeeWeave."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

MANIFEST_VERSION = 1
IGNORED_SCAN_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


@dataclass(frozen=True)
class ExternalPaths:
    root: Path
    repos: Path
    skills: Path
    manifest: Path


@dataclass(frozen=True)
class SourceSpec:
    raw: str
    kind: str
    source_url: str
    repo_key: str
    tree_path: str | None = None
    ref: str | None = None
    local_path: Path | None = None


@dataclass(frozen=True)
class SkillCandidate:
    name: str
    root: Path
    subpath: str


@dataclass(frozen=True)
class LinkResult:
    linked: list[Path]
    skipped: list[Path]
    conflicts: list[Path]
    failed: list[tuple[Path, str]]


class ExternalSkillError(RuntimeError):
    pass


def external_paths(config_dir: Path) -> ExternalPaths:
    root = config_dir.expanduser() / "external"
    return ExternalPaths(
        root=root,
        repos=root / "repos",
        skills=root / "skills",
        manifest=root / "manifest.json",
    )


def init_external_storage(paths: ExternalPaths) -> None:
    paths.repos.mkdir(parents=True, exist_ok=True)
    paths.skills.mkdir(parents=True, exist_ok=True)
    if not paths.manifest.exists():
        write_manifest(paths, {"version": MANIFEST_VERSION, "skills": {}})


def read_manifest(paths: ExternalPaths) -> dict:
    if not paths.manifest.exists():
        return {"version": MANIFEST_VERSION, "skills": {}}
    try:
        data = json.loads(paths.manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": MANIFEST_VERSION, "skills": {}}
    if not isinstance(data, dict):
        return {"version": MANIFEST_VERSION, "skills": {}}
    if data.get("version") != MANIFEST_VERSION or not isinstance(data.get("skills"), dict):
        return {"version": MANIFEST_VERSION, "skills": {}}
    return data


def write_manifest(paths: ExternalPaths, data: dict) -> None:
    paths.root.mkdir(parents=True, exist_ok=True)
    skills = data.get("skills", {})
    ordered = {
        "version": MANIFEST_VERSION,
        "skills": {name: skills[name] for name in sorted(skills)},
    }
    paths.manifest.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_source(source: str) -> SourceSpec:
    raw = source.strip()
    path = Path(raw).expanduser()
    if path.exists():
        resolved = path.resolve()
        return SourceSpec(
            raw=raw,
            kind="local",
            source_url=str(resolved),
            repo_key=f"local/{_safe_key(str(resolved))}",
            local_path=resolved,
        )

    github_ssh = re.match(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", raw)
    if github_ssh:
        owner = github_ssh.group("owner")
        repo = github_ssh.group("repo")
        return SourceSpec(
            raw=raw,
            kind="git",
            source_url=f"https://github.com/{owner}/{repo}.git",
            repo_key=f"github.com/{owner}/{repo}",
        )

    shorthand = re.match(r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)$", raw)
    if shorthand and not raw.startswith((".", "/")):
        owner = shorthand.group("owner")
        repo = shorthand.group("repo")
        return SourceSpec(
            raw=raw,
            kind="git",
            source_url=f"https://github.com/{owner}/{repo}.git",
            repo_key=f"github.com/{owner}/{repo}",
        )

    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"} and parsed.netloc.lower() == "github.com":
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1].removesuffix(".git")
            ref = None
            tree_path = None
            if len(parts) >= 5 and parts[2] == "tree":
                ref = parts[3]
                tree_path = "/".join(parts[4:])
            return SourceSpec(
                raw=raw,
                kind="git",
                source_url=f"https://github.com/{owner}/{repo}.git",
                repo_key=f"github.com/{owner}/{repo}",
                tree_path=tree_path,
                ref=ref,
            )

    if raw.endswith(".git") or parsed.scheme in {"ssh", "git"}:
        return SourceSpec(raw=raw, kind="git", source_url=raw, repo_key=f"git/{_safe_key(raw)}")

    raise ExternalSkillError(f"unsupported external skill source: {source}")


def repo_cache_dir(paths: ExternalPaths, source: SourceSpec) -> Path:
    return paths.repos / source.repo_key


def prepare_source_root(paths: ExternalPaths, source: SourceSpec, ref: str | None = None) -> tuple[Path, str | None]:
    if source.kind == "local":
        assert source.local_path is not None
        return source.local_path, _git_commit(source.local_path)

    repo_dir = repo_cache_dir(paths, source)
    requested_ref = ref or source.ref
    if repo_dir.exists():
        if not (repo_dir / ".git").is_dir():
            raise ExternalSkillError(f"repository cache path exists but is not a git repository: {repo_dir}")
        _run_git(["fetch", "--all", "--tags"], cwd=repo_dir)
    else:
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        clone_cmd = ["clone", source.source_url, str(repo_dir)]
        if requested_ref:
            clone_cmd = ["clone", "--branch", requested_ref, source.source_url, str(repo_dir)]
        _run_git(clone_cmd, cwd=None)
    if requested_ref and repo_dir.exists():
        _run_git(["checkout", requested_ref], cwd=repo_dir)
    return repo_dir, _git_commit(repo_dir)


def discover_skills(root: Path) -> list[SkillCandidate]:
    candidates: list[SkillCandidate] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        if any(part in IGNORED_SCAN_DIRS for part in skill_md.relative_to(root).parts):
            continue
        skill_root = skill_md.parent
        candidates.append(
            SkillCandidate(
                name=skill_name(skill_root),
                root=skill_root,
                subpath="." if skill_root == root else skill_root.relative_to(root).as_posix(),
            )
        )
    return candidates


def select_candidates(
    repo_root: Path,
    *,
    path: str | None = None,
    skill: str | None = None,
    all_skills: bool = False,
    tree_path: str | None = None,
) -> list[SkillCandidate]:
    selected_path = path or tree_path
    if selected_path:
        skill_root = (repo_root / selected_path).resolve()
        try:
            skill_root.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ExternalSkillError(f"skill path escapes repository: {selected_path}") from exc
        validate_skill_root(skill_root)
        return [SkillCandidate(name=skill_name(skill_root), root=skill_root, subpath=selected_path.strip("/") or ".")]

    candidates = discover_skills(repo_root)
    if skill:
        matches = [candidate for candidate in candidates if candidate.name == skill or candidate.root.name == skill]
        if not matches:
            raise ExternalSkillError(f"skill not found in source: {skill}")
        if len(matches) > 1:
            paths = ", ".join(candidate.subpath for candidate in matches)
            raise ExternalSkillError(f"multiple skills matched {skill}: {paths}; use --path")
        return matches
    if all_skills:
        if not candidates:
            raise ExternalSkillError("no SKILL.md files found in source")
        return candidates
    root_skill = repo_root / "SKILL.md"
    if root_skill.is_file():
        return [SkillCandidate(name=skill_name(repo_root), root=repo_root, subpath=".")]
    if len(candidates) == 1:
        return candidates
    if not candidates:
        raise ExternalSkillError("no SKILL.md files found in source")
    lines = "\n".join(f"- {candidate.name}: {candidate.subpath}" for candidate in candidates)
    raise ExternalSkillError(f"multiple skills found; choose one with --skill or --path:\n{lines}")


def install_candidates(
    paths: ExternalPaths,
    *,
    source: SourceSpec,
    repo_root: Path,
    candidates: list[SkillCandidate],
    ref: str | None,
    commit: str | None,
    link_project: Path | None = None,
    agents: dict[str, dict[str, str | None]] | None = None,
) -> list[str]:
    init_external_storage(paths)
    manifest = read_manifest(paths)
    installed: list[str] = []
    for candidate in candidates:
        entry = paths.skills / candidate.name
        _replace_skill_entry(entry, candidate.root)
        record = {
            "source": source.source_url,
            "source_raw": source.raw,
            "repo_dir": str(repo_root),
            "subpath": candidate.subpath,
            "ref": ref or source.ref or "",
            "resolved_commit": commit or "",
            "install_path": str(entry),
            "license": discover_license(candidate.root, repo_root),
            "installed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "linked_projects": sorted(
                set(manifest.get("skills", {}).get(candidate.name, {}).get("linked_projects", []))
            ),
        }
        manifest["skills"][candidate.name] = record
        installed.append(candidate.name)
    write_manifest(paths, manifest)
    if link_project:
        if agents is None:
            raise ExternalSkillError("agent metadata is required for --link-project")
        for name in installed:
            link_external_skill(paths, name, link_project, agents=agents)
    return installed


def link_external_skill(
    paths: ExternalPaths,
    skill: str,
    project: Path,
    *,
    agents: dict[str, dict[str, str | None]],
) -> LinkResult:
    init_external_storage(paths)
    entry = paths.skills / skill
    validate_skill_root(entry)
    project_dir = project.expanduser().resolve()
    linked: list[Path] = []
    skipped: list[Path] = []
    conflicts: list[Path] = []
    failed: list[tuple[Path, str]] = []
    seen_dirs: set[Path] = set()
    for meta in agents.values():
        rel = meta.get("project")
        if rel is None:
            continue
        skills_dir = project_dir / str(rel)
        if skills_dir in seen_dirs or not skills_dir.is_dir():
            continue
        seen_dirs.add(skills_dir)
        target = skills_dir / skill
        if target.is_symlink():
            current = (
                (target.parent / os.readlink(target)).resolve()
                if not Path(os.readlink(target)).is_absolute()
                else Path(os.readlink(target)).resolve()
            )
            if current == entry.resolve():
                skipped.append(target)
                continue
            target.unlink()
        elif target.exists():
            conflicts.append(target)
            continue
        try:
            target.symlink_to(entry, target_is_directory=True)
            linked.append(target)
        except OSError as exc:
            failed.append((target, str(exc)))
    if linked or skipped:
        manifest = read_manifest(paths)
        record = manifest["skills"].get(skill)
        if record is not None:
            projects = set(record.get("linked_projects", []))
            projects.add(str(project_dir))
            record["linked_projects"] = sorted(projects)
            write_manifest(paths, manifest)
    return LinkResult(linked=linked, skipped=skipped, conflicts=conflicts, failed=failed)


def remove_external_skill(paths: ExternalPaths, skill: str) -> list[Path]:
    manifest = read_manifest(paths)
    record = manifest.get("skills", {}).get(skill)
    removed_links: list[Path] = []
    entry = paths.skills / skill
    if record:
        for project_raw in record.get("linked_projects", []):
            project = Path(project_raw)
            for link in project.glob("*/skills/" + skill):
                if link.is_symlink() and link.resolve() == entry.resolve():
                    link.unlink()
                    removed_links.append(link)
        manifest["skills"].pop(skill, None)
        write_manifest(paths, manifest)
    if entry.is_symlink() or entry.is_file():
        entry.unlink()
    elif entry.is_dir():
        shutil.rmtree(entry)
    return removed_links


def update_external_skill(paths: ExternalPaths, skill: str | None = None) -> list[str]:
    manifest = read_manifest(paths)
    names = [skill] if skill else sorted(manifest.get("skills", {}))
    updated: list[str] = []
    for name in names:
        record = manifest.get("skills", {}).get(name)
        if record is None:
            raise ExternalSkillError(f"external skill is not installed: {name}")
        repo_dir = Path(record["repo_dir"])
        if (repo_dir / ".git").is_dir():
            _run_git(["pull", "--ff-only"], cwd=repo_dir)
            commit = _git_commit(repo_dir) or ""
        else:
            commit = ""
        root = repo_dir if record["subpath"] == "." else repo_dir / record["subpath"]
        validate_skill_root(root)
        record["resolved_commit"] = commit
        updated.append(name)
    write_manifest(paths, manifest)
    return updated


def validate_skill_root(path: Path) -> None:
    if not (path / "SKILL.md").is_file():
        raise ExternalSkillError(f"no SKILL.md found at {path}")


def skill_name(path: Path) -> str:
    text = (path / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?m)^name:\s*([A-Za-z0-9_.-]+)\s*$", text)
    return match.group(1) if match else path.name


def discover_license(skill_root: Path, repo_root: Path) -> str:
    for root in (skill_root, repo_root):
        for name in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
            license_file = root / name
            if license_file.is_file():
                first = license_file.read_text(encoding="utf-8", errors="ignore").splitlines()[:3]
                return " ".join(line.strip() for line in first if line.strip())[:120]
    return ""


def _replace_skill_entry(entry: Path, target: Path) -> None:
    if entry.is_symlink() or entry.is_file():
        entry.unlink()
    elif entry.exists():
        raise ExternalSkillError(f"external skill entry already exists and is not managed: {entry}")
    entry.parent.mkdir(parents=True, exist_ok=True)
    try:
        entry.symlink_to(target, target_is_directory=True)
    except OSError:
        shutil.copytree(target, entry)


def _safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "source"


def _run_git(args: list[str], cwd: Path | None) -> None:
    cmd = ["git", *args]
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ExternalSkillError(detail)


def _git_commit(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(path), text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip()
