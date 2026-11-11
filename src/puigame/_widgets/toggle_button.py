"""ToggleButton, a button that switches between checked and unchecked."""

from __future__ import annotations

from collections.abc import Callable
from typing import ClassVar

from pygame.typing import Point

from puigame._components.skin import Skin
from puigame._layout.anchor import Anchor
from puigame._widgets.button import Button
from puigame._widgets.state import State
from puigame._widgets.toggle_group import ToggleGroup
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

    In a ``ToggleGroup``, checking the button unchecks the group's checked
    button, and the group decides whether a click can uncheck the button
    (see ``ToggleGroup``).
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
        hit_testable: bool = True,
        group: ToggleGroup | None = None,
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
                value each time the value changes, from a click, from code, or
                because another button in its group was checked. It is not
                called when the button is created, or when ``checked`` is set
                to the value it already has. It cannot be changed later. A
                click calls it from inside ``UI.handle_event()``, so changes it
                makes to the widget tree show from the next ``update()``.
                Exceptions it raises propagate to the code that changed the
                value, which for a click is the caller of ``handle_event()``.
                Its return value is ignored, so a coroutine function would
                never run its body. Defaults to ``None``, which does nothing on
                a change.
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
            hit_testable: Whether the mouse can hit the button, so that it can
                be highlighted and pressed, and clicks over it stop at it
                rather than passing to the widgets below it and to the game. A
                disabled button is still hit. Defaults to ``True``.
            group: ``ToggleGroup`` to join, in which checking a button unchecks
                the group's checked button. It cannot be changed later, so a
                button belongs to at most one group. Defaults to ``None``,
                which joins no group.
            checked: Whether the button starts checked. At most one button in a
                group can start checked. Defaults to ``False``.

        Raises:
            TypeError: If ``text`` is not a string, if ``on_toggle`` is neither
                ``None`` nor callable, if ``anchor`` is not an ``Anchor``, if
                ``parent_anchor`` is neither an ``Anchor`` nor ``None``, if
                ``margin`` or ``offset`` is a single number rather than an
                ``(x, y)`` pair, or if ``group`` is neither a ``ToggleGroup``
                nor ``None``. The button is not added to ``parent`` or
                ``group``.
            ValueError: If either dimension of ``size`` is negative, or if
                ``checked`` is ``True`` and ``group`` already has a checked
                button. The button is not added to ``parent`` or ``group``.
        """
        if on_toggle is not None and not callable(on_toggle):
            raise TypeError(f"on_toggle must be callable, got {on_toggle!r}")
        self._on_toggle = on_toggle

        self._checked = checked

        if group is not None:
            if not isinstance(group, ToggleGroup):
                raise TypeError(f"group must be a ToggleGroup or None, got {group!r}")

            if not group._can_add(self):
                raise ValueError(
                    "checked cannot be True when group already has a checked button",
                )

        self._group: ToggleGroup | None = None

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
            hit_testable=hit_testable,
        )

        if group is not None:
            group._add(self)

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

        Assigning ``True`` to a button in a group also unchecks the group's
        checked button. Both values change first, then the unchecked button's
        ``on_toggle`` is called, then this button's, so each callback sees the
        group as it ends up. Assigning ``False`` unchecks the button even when
        clicks cannot, leaving the group with no checked button.
        """
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        if value == self._checked:
            return

        # only checking affects another button, so unchecking needs no group
        if value and self._group is not None:
            self._group._set_as_checked(self)

        else:
            self._checked = value

            self._call_on_toggle()

    @property
    def group(self) -> ToggleGroup | None:
        """The group the button belongs to, or ``None`` if it has none.

        Set on creation and never changed, so it is read-only, except that it
        becomes ``None`` when the button is killed, since killing the button
        removes it from its group.
        """
        return self._group

    def _activate(self) -> None:
        """Toggle the button, unless its group stops clicks unchecking it.

        The ``UIManager`` calls this when a left press that started on the
        button is released over it while it is enabled. A click on the checked
        button of a group created with ``can_uncheck=False`` does nothing.
        Code can still uncheck it, so the check is here rather than in
        ``toggle()`` or the ``checked`` setter.
        """
        if self._group is not None and not self._group._can_uncheck and self._checked:
            return

        self.toggle()

    def _call_on_toggle(self) -> None:
        """Call ``on_toggle`` with the button and its value, if there is one.

        The ``checked`` setter and the button's group call this once the value
        is stored.
        """
        if self._on_toggle is not None:
            self._on_toggle(self, self._checked)

    def toggle(self) -> None:
        """Switch the button between checked and unchecked.

        The same as assigning ``not checked`` to ``checked``, so it calls
        ``on_toggle`` with the new value. It works whether or not the button is
        enabled, and, unlike a click, it can uncheck the checked button of a
        group created with ``can_uncheck=False``.
        """
        self.checked = not self._checked

    def kill(self) -> None:
        """Remove the button from its group, if any, then from the tree.

        Overrides ``Widget.kill()``. If the button was checked, its group is
        left with no checked button, and no callbacks are called. Afterwards
        ``group`` is ``None``.
        """
        if self._group is not None:
            self._group._remove(self)

        super().kill()
