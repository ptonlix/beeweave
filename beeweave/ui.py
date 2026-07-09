"""Shared terminal UI helpers for the BeeWeave CLI."""

from __future__ import annotations

import os
import sys
import textwrap
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, cast

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


def use_rich() -> bool:
    return use_color()


def ansi(text: str, *styles: str) -> str:
    if not use_color():
        return text
    prefix = "".join(ANSI[style] for style in styles)
    return f"{prefix}{text}{ANSI['reset']}"


def console() -> Any:
    from rich.console import Console
    from rich.theme import Theme

    theme = Theme(
        {
            "bee.title": "bold bright_cyan",
            "bee.accent": "cyan",
            "bee.success": "bold green",
            "bee.warning": "bold yellow",
            "bee.error": "bold red",
            "bee.info": "bright_cyan",
            "bee.dim": "dim",
            "bee.key": "bold cyan",
        }
    )
    return Console(
        file=sys.stdout,
        force_terminal=use_rich(),
        color_system="auto" if use_rich() else None,
        no_color=not use_color(),
        theme=theme,
        highlight=False,
    )


def _plain_table(
    title: str, columns: Sequence[str], rows: Sequence[Sequence[str]], *, caption: str | None = None
) -> str:
    values = [[str(cell) for cell in row] for row in rows]
    widths = [
        max(len(str(columns[idx])), *(len(row[idx]) for row in values)) if values else len(str(columns[idx]))
        for idx in range(len(columns))
    ]
    lines = [f"{title}:"]
    lines.append("  " + "  ".join(str(columns[idx]).ljust(widths[idx]) for idx in range(len(columns))))
    lines.append("  " + "  ".join("-" * widths[idx] for idx in range(len(columns))))
    for row in values:
        lines.append("  " + "  ".join(row[idx].ljust(widths[idx]) for idx in range(len(row))))
    if caption:
        lines.extend(["", caption])
    return "\n".join(lines)


def print_table(
    title: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[str | int | None]],
    *,
    caption: str | None = None,
) -> None:
    values = [["" if cell is None else str(cell) for cell in row] for row in rows]
    if not use_rich():
        print(_plain_table(title, columns, values, caption=caption))
        return

    from rich import box
    from rich.table import Table

    table = Table(
        title=title,
        title_style="bee.title",
        header_style="bee.key",
        border_style="bee.accent",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
        caption=caption,
        caption_style="bee.dim",
    )
    for column in columns:
        table.add_column(str(column), overflow="fold")
    for row in values:
        table.add_row(*row)
    console().print(table)


def detail_panel(title: str, rows: Sequence[tuple[str, str | int | None]], *, width: int = 72) -> str:
    del width
    visible_rows = [(key, "" if value is None else str(value)) for key, value in rows]
    key_width = max((len(key) for key, _ in visible_rows), default=0)
    lines = [f"{title}:"]
    for key, value in visible_rows:
        parts = value.splitlines() or [""]
        label = f"{key}:".ljust(key_width + 1)
        lines.append(f"  {label} {parts[0]}")
        for part in parts[1:]:
            lines.append(f"  {' ' * (key_width + 1)} {part}")
    return "\n".join(lines)


def print_detail_panel(
    title: str,
    rows: Sequence[tuple[str, str | int | None]],
    *,
    width: int = 72,
    preserve_values: bool = False,
) -> None:
    if preserve_values and use_rich():
        _print_rich_detail_panel(title, rows)
        return
    if preserve_values or not use_rich():
        print(detail_panel(title, rows, width=width))
        return
    print_summary_panel(title, rows, width=width)


def _print_rich_detail_panel(title: str, rows: Sequence[tuple[str, str | int | None]]) -> None:
    from rich.text import Text

    visible_rows = [(key, "" if value is None else str(value)) for key, value in rows]
    key_width = max((len(key) for key, _ in visible_rows), default=0)
    output = console()
    output.rule(f"[bee.title]{title}[/]", style="bee.accent")
    for key, value in visible_rows:
        parts = value.splitlines() or [""]
        label = f"{key}:".ljust(key_width + 1)
        first = Text("  ")
        first.append(label, style="bee.key")
        first.append(" ")
        first.append(parts[0])
        output.print(first, soft_wrap=True)
        for part in parts[1:]:
            continuation = Text(f"  {' ' * (key_width + 1)} {part}")
            output.print(continuation, soft_wrap=True)
    output.rule(style="bee.accent")


def print_status(level: str, message: str, *, detail: str | None = None) -> None:
    normalized = level.lower()
    labels = {
        "success": "OK",
        "warning": "WARN",
        "error": "ERROR",
        "info": "INFO",
    }
    label = labels.get(normalized, normalized.upper())
    text = f"{label}: {message}"
    if detail:
        text = f"{text}\n  {detail}"
    if not use_rich():
        print(text)
        return

    style = {
        "success": "bee.success",
        "warning": "bee.warning",
        "error": "bee.error",
        "info": "bee.info",
    }.get(normalized, "bee.info")
    console().print(f"[{style}]{label}[/]: {message}")
    if detail:
        console().print(f"  [bee.dim]{detail}[/]")


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

    return [Choice(choice.value, name=choice.name, enabled=choice.enabled) for choice in choices]


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
            instruction=instruction or "",
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
        instruction=instruction or "",
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
            validate=cast(Any, validate),
            invalid_message=invalid_message or "",
            **_style_kwargs(),
        ).execute()
    )


def confirm_prompt(*, message: str, default: bool = False) -> bool:
    from InquirerPy import inquirer

    try:
        prompt = inquirer.confirm(message=message, default=default, **_style_kwargs())
    except TypeError:
        prompt = inquirer.confirm(message=message, default=default)
    return bool(prompt.execute())


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
    if not use_rich():
        print(setup_banner(version))
        return

    from rich import box
    from rich.align import Align
    from rich.panel import Panel
    from rich.text import Text

    wordmark = "\n".join(
        [
            " ____  _____ _____        _______    ___     _______",
            "| __ )| ____| ____|_      _| ____|  / \\ \\   / / ____|",
            "|  _ \\|  _| |  _| \\ \\ /\\ / /  _|   / _ \\ \\ / /|  _|",
            "| |_) | |___| |___ \\ V  V /| |___ / ___ \\ V / | |___",
            "|____/|_____|_____| \\_/\\_/ |_____/_/   \\_\\_/  |_____|",
        ]
    )
    body = Text()
    body.append(wordmark, style="bee.success")
    body.append("\nagent-native knowledge workbench", style="bold")
    body.append(f"\nversion {version}", style="bee.dim")
    console().print(
        Panel(
            Align.center(body),
            border_style="bee.accent",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )


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
    if not use_rich():
        print(summary_panel(title, rows, width=width))
        return

    from rich import box
    from rich.panel import Panel
    from rich.table import Table

    key_width = max((len(key) + 1 for key, _ in rows), default=0)
    table = Table.grid(padding=(0, 2), expand=True)
    table.add_column(style="bee.key", no_wrap=True, width=key_width)
    table.add_column(overflow="fold", ratio=1)
    for key, value in rows:
        table.add_row(f"{key}:", "" if value is None else str(value))
    console().print(
        Panel(
            table,
            title=title,
            title_align="left",
            border_style="bee.accent",
            box=box.ROUNDED,
            expand=True,
        )
    )
