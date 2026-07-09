"""Low-noise update notices for interactive BeeWeave CLI commands."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from beeweave import upgrade

UPDATE_CHECK_FILENAME = "update-check.json"
DEFAULT_INTERVAL = timedelta(hours=24)
NETWORK_TIMEOUT_SECONDS = 0.75


@dataclass(frozen=True)
class UpdateNotice:
    current: str
    latest: str
    install_method: upgrade.InstallMethod


def update_check_path(config_dir: Path) -> Path:
    return config_dir / UPDATE_CHECK_FILENAME


def load_update_cache(config_dir: Path) -> dict[str, Any]:
    path = update_check_path(config_dir)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_update_cache(config_dir: Path, data: dict[str, Any]) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    update_check_path(config_dir).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _cache_due(cache: dict[str, Any], *, now: datetime, interval: timedelta) -> bool:
    checked_at = _parse_timestamp(cache.get("last_checked_at"))
    if checked_at is None:
        return True
    return now - checked_at >= interval


def _notice_from_latest(
    *,
    current_version: str,
    latest_version: object,
    package_file: str,
) -> UpdateNotice | None:
    if not isinstance(latest_version, str) or not latest_version:
        return None
    result = upgrade.check_version(current_version, latest_version)
    if result.status != "update_available" or result.latest is None:
        return None
    return UpdateNotice(
        current=current_version,
        latest=result.latest,
        install_method=upgrade.detect_install_method(package_file=package_file),
    )


def check_for_update_notice(
    *,
    current_version: str,
    config_dir: Path,
    package_file: str,
    now: datetime | None = None,
    interval: timedelta = DEFAULT_INTERVAL,
    fetch_latest: Callable[..., str] = upgrade.fetch_latest_version,
) -> UpdateNotice | None:
    """Return an update notice when a newer version is known.

    Network failures are intentionally quiet and still refresh the checked time,
    so normal commands do not repeatedly pause in offline environments.
    """

    current_time = now or datetime.now(timezone.utc)
    cache = load_update_cache(config_dir)
    if _cache_due(cache, now=current_time, interval=interval):
        latest: str | None
        try:
            latest = fetch_latest(timeout=NETWORK_TIMEOUT_SECONDS)
        except (OSError, RuntimeError, json.JSONDecodeError):
            latest = None
        cache["last_checked_at"] = current_time.isoformat(timespec="seconds")
        if latest:
            cache["latest_version"] = latest
        try:
            save_update_cache(config_dir, cache)
        except OSError:
            return None

    return _notice_from_latest(
        current_version=current_version,
        latest_version=cache.get("latest_version"),
        package_file=package_file,
    )


def print_update_notice(notice: UpdateNotice) -> None:
    print(file=sys.stderr)
    print(f"⚠️  BeeWeave update available: {notice.current} → {notice.latest}", file=sys.stderr)
    if notice.install_method.kind == "source":
        print("   Current install is source/editable. Recommended:", file=sys.stderr)
        for line in upgrade.manual_upgrade_hint(notice.install_method):
            print(f"   {line}", file=sys.stderr)
    else:
        print("   Run: bwe upgrade", file=sys.stderr)
    print(file=sys.stderr)


def maybe_print_update_notice(
    *,
    current_version: str,
    config_dir: Path,
    package_file: str,
    stdout_is_tty: Callable[[], bool] | None = None,
) -> None:
    if not (stdout_is_tty or sys.stdout.isatty)():
        return
    notice = check_for_update_notice(
        current_version=current_version,
        config_dir=config_dir,
        package_file=package_file,
    )
    if notice is not None:
        print_update_notice(notice)
