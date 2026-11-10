"""State, the flags that describe what a widget is doing."""

from enum import Flag, auto


class State(Flag):
    """Flags describing what a widget is doing, which pick its style.

    A widget's state combines any number of flags. Its theme styles each
    combination by applying the override for each flag set to its base style.
    No widget uses ``EDITING`` yet: it is reserved for widgets such as text
    boxes, so that themes can style it already.

    Attributes:
        BASE: No flags set. Every state includes it, so a theme styles it with
            its base style and cannot override it.
        CHECKED: The widget is checked, as a ``ToggleButton`` is while its
            ``checked`` is true. Unlike ``HIGHLIGHTED`` and ``PRESSED``, it is
            kept alongside ``DISABLED``.
        HIGHLIGHTED: The cursor is over the widget, which is interactive and
            enabled. During a press, only the pressed widget is highlighted.
        PRESSED: A left press that started on the widget is held while the
            cursor is over it. Only set together with ``HIGHLIGHTED``.
        EDITING: The widget is being edited. Not used yet.
        DISABLED: The widget or one of its ancestors is disabled. It hides
            ``HIGHLIGHTED`` and ``PRESSED``.
    """

    BASE = 0
    CHECKED = auto()
    HIGHLIGHTED = auto()
    PRESSED = auto()
    EDITING = auto()
    DISABLED = auto()
