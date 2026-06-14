"""
logger.py
Simple logger for the RTL-to-GDS agent pipeline.
All agents use this — never use print() directly in agent code.
"""

from rich.console import Console
from rich.theme import Theme

theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "agent": "bold magenta",
})

console = Console(theme=theme)


def info(msg: str):
    console.print(f"[info][INFO][/info] {msg}")


def success(msg: str):
    console.print(f"[success][PASS][/success] {msg}")


def warning(msg: str):
    console.print(f"[warning][WARN][/warning] {msg}")


def error(msg: str):
    console.print(f"[error][FAIL][/error] {msg}")


def agent(name: str, msg: str):
    console.print(f"[agent][{name}][/agent] {msg}")


def divider():
    console.print("[info]" + "─" * 50 + "[/info]")
