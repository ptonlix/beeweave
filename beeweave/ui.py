"""Shared terminal UI helpers for the BeeWeave CLI."""

from __future__ import annotations

import os
import sys
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

ANSI = {
    "reset": "\033[0m",
    "dim": "\033[2m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "magenta": "\033[35m",
    "yellow": "\033[33m",
}


@dataclass(frozen=True)
class PromptChoice:
    value: str
    name: str
    enabled: bool = False


def use_color() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def ansi(text: str, *styles: str) -> str:
    if not use_color():
        return text
    prefix = "".join(ANSI[style] for style in styles)
    return f"{prefix}{text}{ANSI['reset']}"


def prompt_style() -> Any:
    try:
        from InquirerPy.utils import get_style
    except ImportError:
        return None

    return get_style(
        {
            "questionmark": "#36d399 bold",
            "answermark": "#36d399 bold",
            "answer": "#a7f3d0 bold",
            "input": "#e5e7eb",
            "question": "#f8fafc bold",
            "answered_question": "#94a3b8",
            "instruction": "#64748b",
            "pointer": "#36d399 bold",
            "checkbox": "#36d399",
            "separator": "#64748b",
            "skipped": "#64748b",
            "validator": "#f87171",
            "marker": "#22c55e bold",
        },
        style_override=False,
    )


def _style_kwargs() -> dict[str, Any]:
    style = prompt_style()
    return {"style": style} if style is not None else {}


def _to_inquirer_choices(choices: Sequence[PromptChoice]) -> list[Any]:
    from InquirerPy.base.control import Choice

    return [
        Choice(choice.value, name=choice.name, enabled=choice.enabled)
        for choice in choices
    ]


def select_prompt(
    *,
    message: str,
    choices: Sequence[PromptChoice],
    default: str | None = None,
    instruction: str | None = None,
    height: int | None = None,
) -> str:
    from InquirerPy import inquirer

    return str(
        inquirer.select(
            message=message,
            choices=_to_inquirer_choices(choices),
            default=default,
            instruction=instruction,
            cycle=False,
            height=height or min(8, len(choices)),
            **_style_kwargs(),
        ).execute()
    )


def checkbox_prompt(
    *,
    message: str,
    choices: Sequence[PromptChoice],
    instruction: str | None = None,
    height: int | None = None,
) -> list[str]:
    from InquirerPy import inquirer

    selected = inquirer.checkbox(
        message=message,
        choices=_to_inquirer_choices(choices),
        instruction=instruction,
        transformer=lambda result: f"{len(result)} selected",
        cycle=False,
        height=height or min(8, len(choices)),
        **_style_kwargs(),
    ).execute()
    return [str(item) for item in selected]


def text_prompt(
    *,
    message: str,
    validate: Callable[[str], bool | str] | None = None,
    invalid_message: str | None = None,
) -> str:
    from InquirerPy import inquirer

    return str(
        inquirer.text(
            message=message,
            validate=validate,
            invalid_message=invalid_message,
            **_style_kwargs(),
        ).execute()
    )


def confirm_prompt(*, message: str, default: bool = False) -> bool:
    from InquirerPy import inquirer

    return bool(inquirer.confirm(message=message, default=default, **_style_kwargs()).execute())


def _box_line(text: str, *, width: int, styles: tuple[str, ...] = ()) -> str:
    content = f"  {text}".ljust(width)
    return ansi("│", "cyan") + ansi(content, *styles) + ansi("│", "cyan")


def setup_banner(version: str) -> str:
    width = 66
    wordmark = [
        " ____  _____ _____        _______    ___     _______",
        "| __ )| ____| ____|_      _| ____|  / \\ \\   / / ____|",
        "|  _ \\|  _| |  _| \\ \\ /\\ / /  _|   / _ \\ \\ / /|  _|",
        "| |_) | |___| |___ \\ V  V /| |___ / ___ \\ V / | |___",
        "|____/|_____|_____| \\_/\\_/ |_____/_/   \\_\\_/  |_____|",
    ]
    lines = ["", ansi(f"╭{'─' * width}╮", "cyan")]
    lines.extend(_box_line(line, width=width, styles=("bold", "green")) for line in wordmark)
    lines.append(_box_line("agent-native knowledge workbench", width=width, styles=("bold",)))
    lines.append(_box_line(f"version {version}", width=width, styles=("dim",)))
    lines.append(ansi(f"╰{'─' * width}╯", "cyan"))
    lines.append("")
    return "\n".join(lines)


def print_setup_banner(version: str) -> None:
    print(setup_banner(version))


def summary_panel(title: str, rows: Sequence[tuple[str, str | int | None]], *, width: int = 72) -> str:
    visible_rows = [(key, "" if value is None else str(value)) for key, value in rows]
    key_width = max((len(key) for key, _ in visible_rows), default=0)
    lines = [ansi(f"╭{'─' * width}╮", "cyan")]
    lines.append(_box_line(title, width=width, styles=("bold", "green")))
    lines.append(ansi(f"├{'─' * width}┤", "cyan"))
    for key, value in visible_rows:
        label = f"{key}:".ljust(key_width + 1)
        prefix = f"  {label} "
        body_width = max(16, width - len(prefix))
        wrapped = textwrap.wrap(value, width=body_width) if value else [""]
        for idx, part in enumerate(wrapped):
            row_prefix = prefix if idx == 0 else " " * len(prefix)
            body = f"{row_prefix}{part}".ljust(width)
            lines.append(ansi("│", "cyan") + body + ansi("│", "cyan"))
    lines.append(ansi(f"╰{'─' * width}╯", "cyan"))
    return "\n".join(lines)


def print_summary_panel(title: str, rows: Sequence[tuple[str, str | int | None]], *, width: int = 72) -> None:
    print(summary_panel(title, rows, width=width))
