"""ToggleButton, a button that switches between checked and unchecked."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from pygame.typing import Point

from puigame._components.skin import Skin
from puigame._layout.anchor import Anchor
from puigame._widgets.button import Button
from puigame._widgets.state import State
from puigame._widgets.widget import Widget


class ToggleButton(Button):
    """Button that switches between checked and unchecked when clicked.

    A ToggleButton looks and is clicked like a ``Button``, but each click
    toggles ``checked`` instead of calling an ``on_click`` callback. Every
    change to ``checked``, whether from a click, from ``toggle()``, or from
    assigning the property, calls the ``on_toggle`` callback with the button
    and its new value.

    While checked, the button adds ``CHECKED`` to its state, in every other
    state including ``DISABLED``. ``CHECKED`` has the lowest precedence of the
    state flags, so the theme's ``CHECKED`` override shows only in fields that
    the other active states' overrides leave alone. A theme shows the value in
    every state by giving ``CHECKED`` fields that no other override sets (see
    ``Theme``).
    """

    _possible_states: ClassVar[tuple[State, ...]] = (
        State.BASE,
        State.HIGHLIGHTED,
        State.CHECKED,
        State.HIGHLIGHTED | State.PRESSED,
        State.HIGHLIGHTED | State.CHECKED,
        State.HIGHLIGHTED | State.PRESSED | State.CHECKED,
        State.DISABLED,
        State.DISABLED | State.CHECKED,
    )

    def __init__(
        self,
        parent: Widget,
        *,
        size: Point,
        skin: Skin,
        text: str = "",
        on_toggle: Callable[[ToggleButton, bool], object] | None = None,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        consumes_clicks: bool = True,
        checked: bool = False,
    ) -> None:
        """Create a toggle button as the last child of ``parent``.

        Args:
            parent: Widget to anchor against and to be a child of. It cannot be
                changed later.
            size: Width and height in pixels. The text is placed against this
                rect.
            skin: Skin that draws the button's images. It cannot be changed
                later. For a button with no background, use a ``NoSkin``.
            text: The text to display. Defaults to an empty string, which draws
                nothing.
            on_toggle: Callback called with the button and its new ``checked``
                value each time the value changes, from a click or from code.
                It is not called when the button is created, or when
                ``checked`` is set to the value it already has. It cannot be
                changed later. A click calls it from inside
                ``UI.handle_event()``, so changes it makes to the widget tree
                show from the next ``update()``. Exceptions it raises propagate
                to the code that changed the value, which for a click is the
                caller of ``handle_event()``. Its return value is ignored, so a
                coroutine function would never run its body. Defaults to
                ``None``, which does nothing on a change.
            anchor: Point on this button used for positioning. Defaults to
                ``Anchor.CENTRE``.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the button responds to input. A disabled button is
                drawn in the theme's style for the disabled state, and is never
                highlighted, pressed, or clicked, but its value can still be
                changed from code. Defaults to ``True``.
            visible: Whether the button is drawn. Defaults to ``True``.
            consumes_clicks: Whether mouse clicks over the button stop at it,
                rather than passing to the widgets below it and to the game. A
                disabled button still stops them. Defaults to ``True``.
            checked: Whether the button starts checked. Defaults to ``False``.

        Raises:
            TypeError: If ``text`` is not a string, if ``on_toggle`` is neither
                ``None`` nor callable, if ``anchor`` is not an ``Anchor``, if
                ``parent_anchor`` is neither an ``Anchor`` nor ``None``, or if
                ``margin`` or ``offset`` is a single number rather than an
                ``(x, y)`` pair. The button is not added to ``parent``.
            ValueError: If either dimension of ``size`` is negative. The button
                is not added to ``parent``.
        """
        if on_toggle is not None and not callable(on_toggle):
            raise TypeError(f"on_toggle must be callable, got {on_toggle!r}")
        self._on_toggle = on_toggle

        self._checked = checked

        super().__init__(
            parent,
            size=size,
            skin=skin,
            text=text,
            on_click=None,
            anchor=anchor,
            parent_anchor=parent_anchor,
            margin=margin,
            offset=offset,
            enabled=enabled,
            visible=visible,
            consumes_clicks=consumes_clicks,
        )

    @property
    def _current_state(self) -> State:
        """The button's current State, adding ``CHECKED`` while checked.

        ``CHECKED`` is added on top of every other state, including
        ``DISABLED``, so a disabled button can still show its value.
        """
        state = super()._current_state

        if self.checked:
            state |= State.CHECKED

        return state

    @property
    def checked(self) -> bool:
        """Whether the button is checked.

        Assigning a different value changes the button's look from the next
        ``update()``, then calls ``on_toggle`` with the button and the new
        value. Assigning the value it already has does nothing.
        """
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        if value == self._checked:
            return

        self._checked = value

        if self._on_toggle is not None:
            self._on_toggle(self, self._checked)

    def _activate(self) -> None:
        """Toggle the button, which calls ``on_toggle``.

        The ``UIManager`` calls this when a left press that started on the
        button is released over it while it is enabled.
        """
        self.toggle()

    def toggle(self) -> None:
        """Switch the button between checked and unchecked.

        The same as assigning ``not checked`` to ``checked``, so it calls
        ``on_toggle`` with the new value. It works whether or not the button is
        enabled.
        """
        self.checked = not self.checked
