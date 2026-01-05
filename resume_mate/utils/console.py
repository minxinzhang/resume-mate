from rich.console import Console
from rich.theme import Theme
from rich.syntax import Syntax
import difflib

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

console = Console(theme=custom_theme)

def print_yaml_diff(old_yaml: str, new_yaml: str):
    """
    Computes and prints a colored diff between two YAML strings.
    """
    diff = difflib.unified_diff(
        old_yaml.splitlines(),
        new_yaml.splitlines(),
        fromfile="Original Profile",
        tofile="New Profile",
        lineterm=""
    )
    diff_text = "\n".join(list(diff))
    
    if not diff_text:
        console.print("[info]No changes detected.[/info]")
        return

    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)