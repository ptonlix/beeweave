"""BeeWeave profile config helpers."""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

from beeweave import ui

NEW_PROFILE_CHOICE = "__new_profile__"


def validate_profile_name(profile: str) -> str:
    value = profile.strip()
    if not value:
        raise ValueError("profile name cannot be empty")
    if value == "default":
        return value
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if any(ch not in allowed for ch in value):
        raise ValueError("profile name may only contain letters, numbers, '-' and '_'")
    if value.startswith("."):
        raise ValueError("profile name cannot start with '.'")
    return value


def parse_profile(raw_profile: str | None) -> str:
    if raw_profile is None or raw_profile.strip() == "":
        return "default"
    return validate_profile_name(raw_profile)


def config_path_for_profile(profile: str, *, config_dir: Path, default_config: Path) -> Path:
    if profile == "default":
        return default_config
    return config_dir / f"config.{profile}"


def available_profiles(config_dir: Path) -> list[str]:
    profiles = ["default"]
    if config_dir.is_dir():
        for path in sorted(config_dir.glob("config.*")):
            name = path.name.removeprefix("config.")
            if name:
                profiles.append(name)
    return list(dict.fromkeys(profiles))


def profile_label(profile: str, *, config_dir: Path, default_config: Path) -> str:
    if profile == "default":
        return f"default   active config     {default_config}"
    path = config_path_for_profile(profile, config_dir=config_dir, default_config=default_config)
    return f"{profile:<9} named profile     {path}"


def new_profile_label(*, config_dir: Path) -> str:
    return f"+ new     create profile    {config_dir / 'config.<name>'}"


def parse_profile_menu_selection(raw: str, profiles: list[str]) -> str:
    value = raw.strip()
    if not value:
        return "default"
    if value in {"new", "n"}:
        return NEW_PROFILE_CHOICE
    if value.isdigit():
        idx = int(value)
        max_idx = len(profiles) + 1
        if idx < 1 or idx > max_idx:
            raise ValueError(f"selection out of range: {value}")
        if idx == max_idx:
            return NEW_PROFILE_CHOICE
        return profiles[idx - 1]
    if value in profiles:
        return value
    raise ValueError(f"unknown profile: {value}")


def choose_profile_numbered(*, config_dir: Path, default_config: Path) -> str:
    profiles = available_profiles(config_dir)
    print("  BeeWeave profile:")
    for idx, profile in enumerate(profiles, start=1):
        marker = " (default)" if profile == "default" else ""
        label = profile_label(profile, config_dir=config_dir, default_config=default_config)
        print(f"   {idx:2d}. {label}{marker}")
    print(f"   {len(profiles) + 1:2d}. {new_profile_label(config_dir=config_dir)}")
    print("")
    while True:
        entered = input("  Select profile [1]: ").strip()
        try:
            selected = parse_profile_menu_selection(entered, profiles)
        except ValueError as exc:
            print(f"  {exc}")
            continue
        if selected != NEW_PROFILE_CHOICE:
            return selected
        name = input("  New profile name: ").strip()
        try:
            return parse_profile(name)
        except ValueError as exc:
            print(f"  {exc}")


def choose_profile_select(*, config_dir: Path, default_config: Path) -> str:
    profiles = available_profiles(config_dir)
    choices = [
        ui.PromptChoice(
            profile,
            name=profile_label(profile, config_dir=config_dir, default_config=default_config),
        )
        for profile in profiles
    ]
    choices.append(ui.PromptChoice(NEW_PROFILE_CHOICE, name=new_profile_label(config_dir=config_dir)))
    selected = ui.select_prompt(
        message="BeeWeave profile:",
        choices=choices,
        default="default",
        instruction="(↑↓ move, enter confirm; default selected)",
        height=min(8, len(choices)),
    )
    if selected != NEW_PROFILE_CHOICE:
        return selected

    def validate_name(value: str) -> bool | str:
        try:
            parse_profile(value)
        except ValueError:
            return False
        return True

    name = ui.text_prompt(
        message="New profile name:",
        validate=validate_name,
        invalid_message="profile name may only contain letters, numbers, '-' and '_'",
    ).strip()
    return parse_profile(name)


def choose_profile(raw_profile: str | None, *, config_dir: Path, default_config: Path) -> str:
    if raw_profile is not None:
        return parse_profile(raw_profile)
    if not sys.stdin.isatty():
        return "default"
    try:
        return choose_profile_select(config_dir=config_dir, default_config=default_config)
    except ImportError:
        return choose_profile_numbered(config_dir=config_dir, default_config=default_config)


def backup_path_for_default(default_config: Path, *, now: datetime | None = None) -> Path:
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    base = default_config.with_name(f"{default_config.name}.backup-{stamp}")
    candidate = base
    suffix = 2
    while candidate.exists() or candidate.is_symlink():
        candidate = default_config.with_name(f"{default_config.name}.backup-{stamp}-{suffix}")
        suffix += 1
    return candidate


def set_default_profile(
    profile: str,
    *,
    config_dir: Path,
    default_config: Path,
    now: datetime | None = None,
) -> tuple[Path, Path, Path | None]:
    name = validate_profile_name(profile)
    if name == "default":
        raise ValueError("default is already the default profile")

    source = config_path_for_profile(name, config_dir=config_dir, default_config=default_config)
    if not source.is_file():
        raise FileNotFoundError(f"profile config not found: {source}")

    config_dir.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if default_config.exists() or default_config.is_symlink():
        backup = backup_path_for_default(default_config, now=now)
        shutil.copy2(default_config, backup)
        default_config.unlink()

    shutil.copy2(source, default_config)
    return source, default_config, backup
