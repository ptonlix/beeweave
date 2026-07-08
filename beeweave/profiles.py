"""BeeWeave profile config helpers."""

from __future__ import annotations

import sys
from pathlib import Path

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
        return f"default - {default_config}"
    path = config_path_for_profile(profile, config_dir=config_dir, default_config=default_config)
    return f"{profile} - {path}"


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
    print(f"   {len(profiles) + 1:2d}. new profile...")
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
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    profiles = available_profiles(config_dir)
    choices = [
        Choice(
            profile,
            name=profile_label(profile, config_dir=config_dir, default_config=default_config),
        )
        for profile in profiles
    ]
    choices.append(Choice(NEW_PROFILE_CHOICE, name="new profile..."))
    selected = str(
        inquirer.select(
            message="BeeWeave profile:",
            choices=choices,
            default="default",
            instruction="(↑↓ move, enter confirm; default selected)",
            cycle=False,
            height=min(8, len(choices)),
        ).execute()
    )
    if selected != NEW_PROFILE_CHOICE:
        return selected
    while True:
        name = str(inquirer.text(message="New profile name:").execute()).strip()
        try:
            return parse_profile(name)
        except ValueError as exc:
            print(f"  {exc}")


def choose_profile(raw_profile: str | None, *, config_dir: Path, default_config: Path) -> str:
    if raw_profile is not None:
        return parse_profile(raw_profile)
    if not sys.stdin.isatty():
        return "default"
    try:
        return choose_profile_select(config_dir=config_dir, default_config=default_config)
    except ImportError:
        return choose_profile_numbered(config_dir=config_dir, default_config=default_config)


def choose_activate_profile(profile: str, *, activate: bool) -> bool:
    return profile != "default" and activate


def activate_profile(profile: str, *, config_path: Path, default_config: Path) -> None:
    if profile == "default":
        return
    if default_config.exists() or default_config.is_symlink():
        default_config.unlink()
    default_config.symlink_to(config_path.name)
    print(f"✅  Active profile set to {profile} → {default_config}")
