"""CursorRole, what the mouse cursor means over a widget."""

from enum import Enum, auto


class CursorRole(Enum):
    """What the mouse cursor means over a widget, which picks its image.

    Roles are named by meaning rather than shape, so a theme may draw any
    shape for a role. Each widget class has one role, which does not change
    with its state:

    - ``DEFAULT``: nothing to act on, as over empty space, a label, or a
      disabled widget.
    - ``CLICKABLE``: the widget does something when clicked, such as a button
      or a toggle button.
    - ``TEXT``: the widget holds text that can be edited.
    """

    DEFAULT = auto()
    CLICKABLE = auto()
    TEXT = auto()
