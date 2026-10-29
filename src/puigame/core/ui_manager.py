"""UIManager, the object that handles a UI's input.

UIManager takes the pygame events passed to ``UI.handle_event()``, decides which
ones the UI consumes, and tracks the highlighted widget and any press in
progress. Games reach it through ``UI``, which passes the calls through.
"""

import pygame as pg
from pygame.typing import Point

from puigame._widgets.interactive_widget import InteractiveWidget
from puigame._widgets.widget import Widget
from puigame.core.ui_root import UIRoot


class UIManager:
    """Input handler for one UI: consuming events, the highlight, and presses.

    The manager hit-tests mouse events against the UI's widget tree, reports
    whether the UI consumed each one, and presses and activates interactive
    widgets. It stores the cursor position from events and recomputes the
    highlight from it once per frame, in ``UI.update()``. It never polls pygame
    for events or the mouse position, so it sees only the events it is given.
    """

    def __init__(self, *, root: UIRoot) -> None:
        """Create a manager for the widget tree under ``root``.

        Args:
            root: Root of the widget tree whose input the manager handles.
        """
        self._root = root
        self._mouse_pos: tuple[int, int] | None = None
        self._buttons_down: set[int] = set()
        self._pressed_widget: InteractiveWidget | None = None
        self._highlighted_widget: InteractiveWidget | None = None

    def handle_event(self, event: pg.Event) -> bool:
        """Handle one pygame event and report whether the UI consumed it.

        A mouse button down over a widget that consumes clicks is consumed, and
        so is its matching up, wherever it lands. A left down on an enabled
        interactive widget starts a press, and the left up activates the widget
        if it is still under the cursor. Wheel buttons, mouse motion, and window
        events are never consumed, and every other event is ignored.

        Args:
            event: The event to handle.

        Returns:
            ``True`` if the UI consumed the event, so the game should not handle
            it, otherwise ``False``.
        """
        match event.type:
            case pg.MOUSEBUTTONDOWN:
                return self._handle_mouse_button_down(event)

            case pg.MOUSEBUTTONUP:
                return self._handle_mouse_button_up(event)

            case pg.MOUSEMOTION:
                return self._handle_mouse_motion(event)

            case pg.WINDOWLEAVE:
                return self._handle_window_leave()

            case pg.WINDOWFOCUSLOST:
                return self._handle_window_focus_lost()

        return False

    def _handle_mouse_button_down(self, event: pg.Event) -> bool:
        """Record a mouse button down, and start a press if it hits a widget.

        The down first drops anything left over from an earlier down of the same
        button whose up never arrived. A left down on an enabled interactive
        widget then starts a press on it.

        Args:
            event: A ``MOUSEBUTTONDOWN`` event.

        Returns:
            ``True`` if the down was over a widget that consumes clicks,
            otherwise ``False``. Always ``False`` for the wheel buttons.
        """
        self._mouse_pos = event.pos

        # wheel buttons pass through until a scrollable widget needs them
        if event.button in (pg.BUTTON_WHEELUP, pg.BUTTON_WHEELDOWN):
            return False

        # a down for a button already recorded as down means its up was lost
        self._buttons_down.discard(event.button)

        # a press lasts from a left down to its up, so one still recorded is stale
        if event.button == pg.BUTTON_LEFT:
            self._clear_pressed_widget()

        hit_widget = self._hit_test(event.pos)
        if hit_widget is None:  # nothing here consumes clicks, so the game gets it
            return False

        self._buttons_down.add(event.button)

        # consumed whatever the button, but only a left down can start a press
        if (
            event.button == pg.BUTTON_LEFT
            and isinstance(hit_widget, InteractiveWidget)
            and hit_widget.enabled_in_tree
        ):
            self._set_pressed_widget(hit_widget)

        return True

    def _handle_mouse_button_up(self, event: pg.Event) -> bool:
        """Consume a mouse button up whose down was consumed, and end any press.

        A left up ends the press in progress, and activates the pressed widget
        if the up is over it and it is still enabled. The press is cleared
        before the widget is activated, since activation may change the tree.

        Args:
            event: A ``MOUSEBUTTONUP`` event.

        Returns:
            ``True`` if the UI consumed the matching down, otherwise ``False``.
            Always ``False`` for the wheel buttons.
        """
        self._mouse_pos = event.pos

        # wheel buttons pass through until a scrollable widget needs them
        if event.button in (pg.BUTTON_WHEELUP, pg.BUTTON_WHEELDOWN):
            return False

        # the down went to the game, so the up does too, such as a drag's release
        if event.button not in self._buttons_down:
            return False

        self._buttons_down.remove(event.button)

        # no press to end
        if self._pressed_widget is None:
            return True

        # only a left up ends a press
        if event.button != pg.BUTTON_LEFT:
            return True

        # clear the press before calling out, since activation may change the tree
        erstwhile_pressed_widget = self._pressed_widget
        self._clear_pressed_widget()

        hit_widget = self._hit_test(event.pos)

        # releasing anywhere but on the pressed widget cancels the click
        if (
            hit_widget is erstwhile_pressed_widget
            and erstwhile_pressed_widget.enabled_in_tree
        ):
            erstwhile_pressed_widget._activate()

        return True

    def _handle_mouse_motion(self, event: pg.Event) -> bool:
        """Store the cursor position for the next highlight update.

        Args:
            event: A ``MOUSEMOTION`` event.

        Returns:
            Always ``False``, so the game also sees the motion.
        """
        self._mouse_pos = event.pos
        return False

    def _handle_window_leave(self) -> bool:
        """Forget the cursor position, so that nothing is highlighted.

        Returns:
            Always ``False``, so the game also sees the event.
        """
        self._mouse_pos = None
        return False

    def _handle_window_focus_lost(self) -> bool:
        """End any press, since another window may receive its release.

        The cursor position and the buttons recorded as down are kept: the
        cursor may still be over the window, and an up that does arrive still
        belongs to a consumed down.

        Returns:
            Always ``False``, so the game also sees the event.
        """
        self._clear_pressed_widget()
        return False

    def _update_highlight(self) -> None:
        """Highlight the widget under the stored cursor position, or none.

        ``UI.update()`` calls this each frame, after layout, so the highlight
        follows widgets that moved, were hidden, or were disabled under a still
        cursor. The candidate is the hit-test result, so a widget covered by
        another that consumes clicks is not highlighted. Only an enabled
        interactive widget can be highlighted, and during a press only the
        pressed widget can be.
        """
        # the cursor has left the window
        if self._mouse_pos is None:
            self._clear_highlighted_widget()
            return

        hit_widget = self._hit_test(self._mouse_pos)

        if hit_widget is None:  # nothing under the cursor consumes clicks
            self._clear_highlighted_widget()
            return

        # during a press nothing else highlights, as with native mouse capture, and
        # the pressed widget only while it is under the cursor and still enabled
        if self._pressed_widget is not None:
            if (
                self._pressed_widget is hit_widget
                and self._pressed_widget.enabled_in_tree
            ):
                self._set_highlighted_widget(self._pressed_widget)
            else:
                self._clear_highlighted_widget()

        # with no press, highlight the hit widget if it can take input
        elif isinstance(hit_widget, InteractiveWidget) and hit_widget.enabled_in_tree:
            self._set_highlighted_widget(hit_widget)

        else:
            self._clear_highlighted_widget()

    def _hit_test(self, pos: Point) -> Widget | None:
        """Return the topmost visible widget at ``pos`` that consumes clicks.

        Widgets are checked in reverse drawing order, so the one drawn on top
        wins. Hidden subtrees are skipped, disabled widgets still count, and a
        widget that does not consume clicks lets the walk carry on to the
        widgets below it. Each widget is tested against its ``rect``, which
        excludes the right and bottom edges.

        Args:
            pos: Position to test, in the coordinates of the UI's draw surface.

        Returns:
            The topmost such widget, or ``None`` if there is none.
        """
        for widget in reversed(list(self._root._iter_visible_subtree())):
            if widget.rect.collidepoint(pos) and widget.consumes_clicks:
                return widget

        return None

    def _set_pressed_widget(self, interactive_widget: InteractiveWidget) -> None:
        """Record ``interactive_widget`` as pressed, ending any other press.

        Args:
            interactive_widget: Widget the press started on.
        """
        if interactive_widget is self._pressed_widget:
            return

        self._clear_pressed_widget()
        self._pressed_widget = interactive_widget
        interactive_widget._pressed = True

    def _clear_pressed_widget(self) -> None:
        """End the press in progress, if any, without activating anything."""
        if self._pressed_widget is not None:
            self._pressed_widget._pressed = False
            self._pressed_widget = None

    def _set_highlighted_widget(self, interactive_widget: InteractiveWidget) -> None:
        """Highlight ``interactive_widget``, clearing any other highlight.

        Args:
            interactive_widget: Widget to highlight.
        """
        if interactive_widget is self._highlighted_widget:
            return

        self._clear_highlighted_widget()
        self._highlighted_widget = interactive_widget
        interactive_widget._highlighted = True

    def _clear_highlighted_widget(self) -> None:
        """Clear the highlight, if a widget has it."""
        if self._highlighted_widget is not None:
            self._highlighted_widget._highlighted = False
            self._highlighted_widget = None
