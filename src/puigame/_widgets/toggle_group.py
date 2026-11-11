"""ToggleGroup, a set of toggle buttons in which at most one is checked."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from puigame._widgets.toggle_button import ToggleButton


class ToggleGroup:
    """Set of toggle buttons in which at most one is checked.

    A button joins a group when it is created, by passing the group as its
    ``group``, and leaves it when it is killed. Checking a button in the
    group, by a click or from code, unchecks the button that was checked.

    A group can have no checked button: before any is checked, after its
    checked button is unchecked from code, or after its checked button is
    killed. Clicks cannot uncheck the checked button unless the group was
    created with ``can_uncheck=True``, but code always can.

    A ToggleGroup is not a widget and has no place in the tree, so its buttons
    can have different parents.
    """

    def __init__(self, *, can_uncheck: bool = False) -> None:
        """Create a group with no buttons.

        Args:
            can_uncheck: Whether clicking the group's checked button unchecks
                it. Code can uncheck it either way. Defaults to ``False``, so
                clicking the checked button does nothing.
        """
        self._can_uncheck = can_uncheck

        self._buttons: list[ToggleButton] = []

    @property
    def buttons(self) -> tuple[ToggleButton, ...]:
        """The group's buttons, in the order they joined.

        Returned as a tuple, so it cannot be changed directly. A button leaves
        the group when it is killed.
        """
        return tuple(self._buttons)

    @property
    def checked_button(self) -> ToggleButton | None:
        """The group's checked button, or ``None`` if no button is checked.

        Assigning a button in the group checks it, the same as assigning
        ``True`` to its ``checked``, so the button that was checked is
        unchecked. Assigning ``None`` unchecks the checked button, if there is
        one, and assigning the checked button does nothing. Assigning anything
        else, including a button that has been killed, raises ``ValueError``
        and changes nothing.
        """
        for button in self._buttons:
            if button.checked:
                return button

        return None

    @checked_button.setter
    def checked_button(self, value: ToggleButton | None) -> None:
        if value is None:
            checked_button = self.checked_button
            if checked_button is not None:
                checked_button.checked = False

            return

        if value not in self._buttons:
            raise ValueError(
                f"checked_button must be a button in this group or None, got {value!r}",
            )

        value.checked = True

    def _can_add(self, button: ToggleButton) -> bool:
        """Return whether ``button`` can join without a second checked button.

        ``ToggleButton.__init__`` calls this before the button joins its
        parent, so a button that cannot join raises before it changes
        anything.
        """
        return self.checked_button is None or not button.checked

    def _add(self, button: ToggleButton) -> None:
        """Add ``button`` to the group, and set the button's ``group`` to it.

        ``ToggleButton.__init__`` calls this once the button has joined its
        parent, after ``_can_add()`` has allowed it, so nothing here can fail.
        Both ends of the link are set here and cleared in ``_remove()``.
        """
        # ToggleButton.__init__ checked this with _can_add()
        assert not button.checked or self.checked_button is None

        self._buttons.append(button)
        button._group = self

    def _remove(self, button: ToggleButton) -> None:
        """Remove ``button`` from the group, and clear the button's ``group``.

        ``ToggleButton.kill()`` calls this. If the button was checked, the
        group is left with no checked button, and no callbacks are called.
        """
        # _group is set only while the button is a member, and kill() checks it
        assert button in self._buttons

        self._buttons.remove(button)
        button._group = None

    def _set_as_checked(self, button: ToggleButton) -> None:
        """Check ``button`` and uncheck the group's checked button, if any.

        Both values are stored before either callback is called, so each
        callback sees the group as it ends up. Then the unchecked button's
        ``on_toggle`` is called, then ``button``'s. If the first raises, the
        second is not called.

        The ``checked`` setter calls this to check a button in a group. It
        writes ``_checked`` directly, since assigning ``checked`` would call
        back into the group.
        """
        # the setter calls this only through the button's own _group
        assert button in self._buttons

        old_button = self.checked_button

        if old_button is not None:
            old_button._checked = False

        button._checked = True

        if old_button is not None:
            old_button._call_on_toggle()

        button._call_on_toggle()
