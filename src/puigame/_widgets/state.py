"""State, the flags that describe what a widget is doing."""

from enum import Flag, auto


class State(Flag):
    """Possible widget state flags."""

    BASE = 0
    CHECKED = auto()
    HIGHLIGHTED = auto()
    PRESSED = auto()
    EDITING = auto()
    DISABLED = auto()
