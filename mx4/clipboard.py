"""Copy and paste keys that suit the focused app.

Terminals copy with Ctrl+Shift+C and paste with Ctrl+Shift+V; there a plain
Ctrl+C would interrupt whatever is running. Apps that hold a terminal next to
other views (VS Code) get Ctrl+Insert / Shift+Insert, which copy and paste in
both and never interrupt. Everything else gets Ctrl+C / Ctrl+V. When the
focused app is unknown, the safe pair is used.
"""

from __future__ import annotations

from . import uinput

CTRL, SHIFT = uinput.KEY_LEFTCTRL, uinput.KEY_LEFTSHIFT

KEYS = {
    "terminal": {"copy": (CTRL, SHIFT, uinput.KEY_C), "paste": (CTRL, SHIFT, uinput.KEY_V)},
    "insert": {"copy": (CTRL, uinput.KEY_INSERT), "paste": (SHIFT, uinput.KEY_INSERT)},
    "plain": {"copy": (CTRL, uinput.KEY_C), "paste": (CTRL, uinput.KEY_V)},
}

TERMINALS = "ptyxis gnome-terminal kgx org.gnome.console kitty alacritty foot wezterm konsole tilix terminator xterm ghostty herdr"
INSERT_APPS = "code vscode vscodium"


def kind_for(focus: str | None, terminals: str = TERMINALS, insert_apps: str = INSERT_APPS) -> str:
    """Which key pair suits the focused app ('wm-class app-id', lower case)."""
    if focus is None:
        return "insert"
    words = focus.replace(".desktop", "").replace(".", " ").replace("-", " ").split()
    joined = " ".join(words)
    for name in terminals.lower().split():
        if name.replace(".", " ").replace("-", " ") in joined:
            return "terminal"
    for name in insert_apps.lower().split():
        if name in words:
            return "insert"
    return "plain"


def keys_for(action: str, focus: str | None, terminals: str = TERMINALS, insert_apps: str = INSERT_APPS):
    return KEYS[kind_for(focus, terminals, insert_apps)][action]
