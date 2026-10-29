"""State, the flags that describe what a widget is doing."""

from enum import Flag, auto


class State(Flag):
    """Possible widget state flags."""

    BASE = 0
    DISABLED = auto()
    HIGHLIGHTED = auto()
    PRESSED = auto()
    CHECKED = auto()
    EDITING = auto()
