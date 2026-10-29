"""Button, an interactive widget that activates when pressed and released."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from pygame.typing import Point

from puigame._components.skin import Skin
from puigame._components.text import Text
from puigame._layout.anchor import Anchor
from puigame.core.interactive_widget import InteractiveWidget
from puigame.core.state import State
from puigame.core.widget import Widget


class Button(InteractiveWidget):
    """Interactive widget that calls a callback when clicked.

    A Button draws its skin with one ``Text`` above it, both styled by the
    theme's style for the button's current state. A click is a left press that
    starts on the button and is released over it while it is enabled. The
    button then calls its ``on_click`` callback with itself.

    While pressed and under the cursor, the button shows ``PRESSED`` on top of
    ``HIGHLIGHTED``, so a theme's ``PRESSED`` override needs only what differs
    from the highlighted look. Dragging the cursor off during a press shows the
    base look, and dragging back shows the pressed look again. Releasing off
    the button cancels the click.
    """

    _possible_states: ClassVar[tuple[State, ...]] = (
        State.BASE,
        State.DISABLED,
        State.HIGHLIGHTED,
        State.PRESSED | State.HIGHLIGHTED,
    )

    def __init__(
        self,
        parent: Widget,
        *,
        size: Point,
        skin: Skin,
        text: str = "",
        on_click: Callable[[Button], object] | None = None,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        consumes_clicks: bool = True,
    ) -> None:
        """Create a button as the last child of ``parent``.

        Args:
            parent: Widget to anchor against and to be a child of. It cannot be
                changed later.
            size: Width and height in pixels. The text is placed against this
                rect.
            skin: Skin that draws the button's images. It cannot be changed
                later. For a button with no background, use a ``NoSkin``.
            text: The text to display. Defaults to an empty string, which draws
                nothing.
            on_click: Callback called with the button each time it is clicked.
                It cannot be changed later. It is called from inside
                ``UI.handle_event()``, so changes it makes to the widget tree,
                such as killing or disabling the button, show from the next
                ``update()``. Exceptions it raises propagate to the caller of
                ``handle_event()``. Its return value is ignored, so a coroutine
                function would never run its body. Defaults to ``None``, which
                does nothing on a click.
            anchor: Point on this button used for positioning.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the button responds to input. A disabled button is
                drawn in the theme's style for the disabled state, and is never
                highlighted, pressed, or clicked.
            visible: Whether the button is drawn.
            consumes_clicks: Whether mouse clicks over the button stop at it,
                rather than passing to the widgets below it and to the game. A
                disabled button still stops them. Defaults to ``True``.

        Raises:
            ValueError: If either dimension of ``size`` is negative. The button
                is not added to ``parent``.
            TypeError: If ``text`` is not a string, if ``on_click`` is neither
                ``None`` nor callable, or if ``margin`` or ``offset`` is a
                single number rather than an ``(x, y)`` pair. The button is not
                added to ``parent``.
        """
        # Widget.__init__() renders the components, so the text must exist first
        self._text = Text(text)

        if on_click is not None and not callable(on_click):
            raise TypeError(f"on_click must be callable, got {on_click!r}")
        self._on_click = on_click

        super().__init__(
            parent,
            size=size,
            skin=skin,
            anchor=anchor,
            parent_anchor=parent_anchor,
            margin=margin,
            offset=offset,
            enabled=enabled,
            visible=visible,
            consumes_clicks=consumes_clicks,
            components=[self._text],
        )

    @property
    def text(self) -> str:
        """The text the button displays.

        Assigning new text redraws the button's images; assigning the text it
        already has does nothing. Assigning a value that is not a string raises
        ``TypeError`` and leaves the text unchanged.
        """
        return self._text.content

    @text.setter
    def text(self, value: str) -> None:
        if value == self._text.content:
            return

        self._text.content = value
        self._rebuild_image_cache()

    @property
    def _current_state(self) -> State:
        """The button's current State, adding ``PRESSED`` while held down.

        ``PRESSED`` is added only on top of ``HIGHLIGHTED``, so the button looks
        pressed only while the press is held over it. It inherits the
        suppression by ``DISABLED`` from ``HIGHLIGHTED``, so a disabled button
        never looks pressed.
        """
        state = super()._current_state

        if State.HIGHLIGHTED in state and self._pressed:
            state |= State.PRESSED

        return state

    def _activate(self) -> None:
        """Call ``on_click`` with the button, if there is one.

        The ``UIManager`` calls this when a left press that started on the
        button is released over it while it is enabled.
        """
        if self._on_click is not None:
            self._on_click(self)
