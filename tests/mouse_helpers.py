"""Mouse helpers for the tests: one place for every way of sending mouse input.

The helpers never call ``update()``, so a test shows where each frame falls.
"""

import pygame as pg

from puigame import UI


def left_press(ui: UI, *, pos: tuple[int, int]) -> bool:
    """Send a left button down at ``pos`` and return whether it was consumed.

    Args:
        ui: UI to send the event to.
        pos: Position of the event.

    Returns:
        Whether ``ui`` consumed the event.
    """
    mouse_button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=pos,
        button=pg.BUTTON_LEFT,
    )

    return ui.handle_event(mouse_button_down_event)


def left_release(ui: UI, *, pos: tuple[int, int]) -> bool:
    """Send a left button up at ``pos`` and return whether it was consumed.

    Args:
        ui: UI to send the event to.
        pos: Position of the event.

    Returns:
        Whether ``ui`` consumed the event.
    """
    mouse_button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=pos,
        button=pg.BUTTON_LEFT,
    )

    return ui.handle_event(mouse_button_up_event)


def left_click(ui: UI, *, pos: tuple[int, int]) -> None:
    """Send a left press and release at ``pos``, as one click.

    Args:
        ui: UI to send the events to.
        pos: Position of both events.
    """
    left_press(ui, pos=pos)
    left_release(ui, pos=pos)


def move_mouse(ui: UI, *, pos: tuple[int, int]) -> None:
    """Send a mouse motion to ``pos``.

    Motion is never consumed, so nothing is returned.

    Args:
        ui: UI to send the event to.
        pos: Position the cursor moves to.
    """
    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=pos)
    ui.handle_event(mouse_motion_event)


def scroll_mouse(ui: UI, *, pos: tuple[int, int]) -> bool:
    """Send a mouse wheel step at ``pos`` and return whether it was consumed.

    The step is a ``MOUSEWHEEL`` away from the user, with no horizontal scroll.
    The wheel button down and up that pygame also sends for each step are not
    sent.

    Args:
        ui: UI to send the event to.
        pos: Position of the event.

    Returns:
        Whether ``ui`` consumed the event.
    """
    mouse_wheel_event = pg.Event(pg.MOUSEWHEEL, x=0, y=1, pos=pos)
    return ui.handle_event(mouse_wheel_event)
