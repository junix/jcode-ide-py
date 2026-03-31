from __future__ import annotations

from difflib import unified_diff
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax

from ._logging import get_logger

logger = get_logger(__name__)

_SUFFIX_TO_LANGUAGE: dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "jsx": "jsx",
    "tsx": "tsx",
    "rs": "rust",
    "go": "go",
    "java": "java",
    "c": "c",
    "cpp": "cpp",
    "h": "c",
    "hpp": "cpp",
    "rb": "ruby",
    "php": "php",
    "sh": "bash",
    "bash": "bash",
    "zsh": "bash",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "toml": "toml",
    "xml": "xml",
    "html": "html",
    "css": "css",
    "scss": "scss",
    "md": "markdown",
    "sql": "sql",
}


def suffix_to_language(suffix: str) -> str:
    return _SUFFIX_TO_LANGUAGE.get(suffix.lower(), "text")


class TerminalConfirmation:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    async def confirm_write(self, file_path: str, new_content: str, *, show_diff: bool = True) -> bool:
        self.console.print()
        self.console.print(f"[bold yellow]File:[/] {file_path}")

        if show_diff:
            original = ""
            path = Path(file_path)
            if path.exists():
                try:
                    original = path.read_text()
                except Exception as exc:
                    self.console.print(f"[dim]Could not read original file: {exc}[/]")

            diff_lines = list(
                unified_diff(
                    original.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"a/{path.name}",
                    tofile=f"b/{path.name}",
                )
            )

            if diff_lines:
                self.console.print()
                self.console.print(Syntax("".join(diff_lines), "diff", theme="monokai", line_numbers=False))
            else:
                self.console.print("[dim]No changes[/]")

        self.console.print()
        return Confirm.ask("[bold]Apply these changes?[/]", default=False, console=self.console)

    async def confirm_delete(self, file_path: str) -> bool:
        self.console.print()
        self.console.print(f"[bold red]Delete file:[/] {file_path}")

        path = Path(file_path)
        if path.exists():
            try:
                content = path.read_text()
                lines = content.count("\n") + 1
                self.console.print(f"[dim]({lines} lines will be deleted)[/]")
            except Exception:
                logger.debug("Failed to count lines for file pending deletion: {}", file_path, exc_info=True)

        self.console.print()
        return Confirm.ask("[bold red]Are you sure you want to delete this file?[/]", default=False, console=self.console)

    async def show_preview(self, file_path: str, content: str, *, language: str | None = None) -> None:
        if language is None:
            language = suffix_to_language(Path(file_path).suffix.lstrip("."))

        self.console.print()
        self.console.print(f"[bold]Preview:[/] {file_path}")
        self.console.print()
        self.console.print(Syntax(content, language, theme="monokai", line_numbers=True))
