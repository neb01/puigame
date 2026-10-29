from collections.abc import Iterable
from dataclasses import replace

import pygame as pg
import pytest
from pygame.typing import Point

from puigame._components.component import Component
from puigame._components.skin import NoSkin, Skin
from puigame._layout.anchor import Anchor
from puigame._styling.style import StyleOverride
from puigame._styling.theme import DEFAULT_THEME, Theme
from puigame._widgets.container import Container
from puigame._widgets.interactive_widget import InteractiveWidget
from puigame._widgets.label import Label
from puigame._widgets.panel import Panel
from puigame._widgets.state import State
from puigame._widgets.widget import Widget
from puigame.core.ui import UI
from stubs import BodyColourLayer

# region --- Constants --------------------------------------------------------

ANY_SKIN = NoSkin()

BASE_COLOUR = (0, 0, 0, 255)
DISABLED_COLOUR = (255, 0, 0, 255)
HIGHLIGHTED_COLOUR = (0, 255, 0, 255)

HIGHLIGHT_THEME = Theme(
    base_style=replace(DEFAULT_THEME.base_style, body_colour=BASE_COLOUR),
    style_overrides={
        State.DISABLED: StyleOverride(body_colour=DISABLED_COLOUR),
        State.HIGHLIGHTED: StyleOverride(body_colour=HIGHLIGHTED_COLOUR),
    },
)

# endregion


# region --- Stubs ------------------------------------------------------------


class RecordingWidget(InteractiveWidget):
    """Interactive widget that counts how many times it is activated.

    Everything else is inherited from ``InteractiveWidget``, so tests can see
    clicks through ``activation_count``.
    """

    def __init__(
        self,
        parent: Widget,
        *,
        size: Point,
        skin: Skin,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        consumes_clicks: bool = True,
        components: Iterable[Component] = (),
    ) -> None:
        """Create the widget as the last child of ``parent``, never activated.

        Takes the same arguments as ``InteractiveWidget``.
        """
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
            components=components,
        )

        self.activation_count: int = 0

    def _activate(self) -> None:
        super()._activate()
        self.activation_count += 1


# endregion


# region --- Helpers ----------------------------------------------------------


def _left_click(ui: UI, *, pos: Point) -> None:
    """Send a left button down and up at ``pos``, as one click.

    Args:
        ui: UI to send the events to.
        pos: Position of both events.
    """
    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=pos,
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=pos,
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)


# endregion


# region --- Fixtures ---------------------------------------------------------


@pytest.fixture
def highlight_ui() -> UI:
    """Return a UI whose theme gives each state its own body colour."""
    return UI(size=(300, 200), theme=HIGHLIGHT_THEME)


# endregion


# region --- Consuming --------------------------------------------------------


def test_consuming_widget_consumes_mouse_button_down(ui: UI):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    assert ui.handle_event(button_down_event)


def test_empty_space_does_not_consume_mouse_button_down(ui: UI):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(6, 7),
        button=pg.BUTTON_LEFT,
    )

    assert not ui.handle_event(button_down_event)


@pytest.mark.parametrize("widget_class", [Container, Label])
def test_non_consuming_widget_does_not_consume_mouse_button_down(ui: UI, widget_class):
    widget_class(
        ui.root,
        size=(4, 5),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )

    assert not ui.handle_event(button_down_event)


def test_consuming_widget_consumes_right_mouse_button_down(ui: UI):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_RIGHT,
    )

    assert ui.handle_event(button_down_event)


@pytest.mark.parametrize(
    "event_type",
    [pg.MOUSEBUTTONUP, pg.MOUSEBUTTONDOWN],
    ids=["button up", "button down"],
)
@pytest.mark.parametrize(
    "event_button",
    [pg.BUTTON_WHEELUP, pg.BUTTON_WHEELDOWN],
    ids=["wheel up", "wheel down"],
)
def test_wheel_button_events_are_not_consumed(ui: UI, event_type, event_button):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    wheel_event = pg.Event(
        event_type,
        pos=(1, 2),
        button=event_button,
    )

    assert not ui.handle_event(wheel_event)


def test_up_off_widget_is_consumed_if_its_down_was_consumed(ui: UI):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(6, 7),
        button=pg.BUTTON_LEFT,
    )

    assert ui.handle_event(button_up_event)


def test_up_is_not_consumed_if_its_down_was_off_widget(ui: UI):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(6, 7),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )

    assert not ui.handle_event(button_up_event)


@pytest.mark.parametrize(
    "event_pos",
    [(1, 2), (6, 7)],
    ids=["on widget", "off widget"],
)
def test_widget_does_not_consume_lone_up_event(ui: UI, event_pos):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=event_pos,
        button=pg.BUTTON_LEFT,
    )

    assert not ui.handle_event(button_up_event)


def test_stale_down_event_is_cleared_by_non_consumed_down_of_same_button(ui: UI):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event_1 = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )

    ui.handle_event(button_down_event_1)

    button_down_event_2 = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(6, 7),
        button=pg.BUTTON_LEFT,
    )

    # the first down's up never arrived, so this down discards its record
    ui.handle_event(button_down_event_2)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )

    # its down's record was discarded, so the game gets this up
    assert not ui.handle_event(button_up_event)


def test_down_only_clears_record_of_own_button(ui: UI):
    Panel(
        ui.root,
        size=(4, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    right_button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(2, 3),
        button=pg.BUTTON_RIGHT,
    )
    ui.handle_event(right_button_down_event)

    # a left down discards only the left record, not the right
    left_button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(6, 7),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(left_button_down_event)

    left_button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(6, 7),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(left_button_up_event)

    # the right down was consumed, so its up still is, wherever it lands
    right_button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(6, 7),
        button=pg.BUTTON_RIGHT,
    )
    assert ui.handle_event(right_button_up_event)


@pytest.mark.parametrize(
    "event",
    [
        pg.Event(pg.MOUSEMOTION, pos=(2, 3)),
        pg.Event(pg.WINDOWLEAVE),
        pg.Event(pg.WINDOWFOCUSLOST),
        pg.Event(pg.KEYDOWN),
        pg.Event(pg.MOUSEWHEEL),
    ],
    ids=[
        "mouse motion",
        "window leave",
        "window focus lost",
        "key down",
        "mouse wheel",
    ],
)
def test_non_button_events_are_not_consumed(ui: UI, event):
    Panel(
        ui.root,
        size=(6, 7),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    assert not ui.handle_event(event)


# endregion


# region --- Hit-testing ------------------------------------------------------


def test_consuming_widget_prevents_widget_below_activation(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    Panel(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_click(ui, pos=(1, 2))

    assert recording_widget.activation_count == 0


def test_hidden_consuming_widget_allows_widget_below_activation(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    Panel(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        visible=False,
    )

    _left_click(ui, pos=(1, 2))

    assert recording_widget.activation_count == 1


def test_disabled_consuming_widget_prevents_widget_below_activation(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    Panel(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=False,
    )

    _left_click(ui, pos=(1, 2))

    assert recording_widget.activation_count == 0


def test_non_consuming_widget_allows_widget_below_activation(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    Panel(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        consumes_clicks=False,
    )

    _left_click(ui, pos=(1, 2))

    assert recording_widget.activation_count == 1


@pytest.mark.parametrize(
    ("pos", "consumed"),
    [
        ((5, 7), True),
        ((4, 8), True),
        ((5, 10), False),
        ((6, 8), False),
    ],
    ids=["top", "left", "bottom", "right"],
)
def test_hit_test_includes_top_left_edges_and_excludes_bottom_right_edges(
    ui: UI,
    pos,
    consumed,
):
    Panel(
        ui.root,
        size=(2, 3),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(3, 5),
        offset=(1, 2),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=pos,
        button=pg.BUTTON_LEFT,
    )
    assert ui.handle_event(button_down_event) is consumed


def test_top_consuming_widget_is_activated(ui: UI):
    recording_widget_1 = RecordingWidget(
        ui.root,
        size=(6, 7),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    recording_widget_2 = RecordingWidget(
        ui.root,
        size=(6, 7),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_click(ui, pos=(2, 3))

    assert recording_widget_1.activation_count == 0
    assert recording_widget_2.activation_count == 1


# endregion


# region --- Activation -------------------------------------------------------


def test_click_on_widget_activates(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_click(ui, pos=(3, 4))

    assert recording_widget.activation_count == 1


def test_click_release_off_widget_does_not_activate(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(10, 20),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 0


def test_click_that_started_off_widget_does_not_activate(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(10, 20),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 0


def test_right_click_does_not_activate(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_RIGHT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_RIGHT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 0


def test_click_on_disabled_widget_does_not_activate(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=False,
    )

    _left_click(ui, pos=(3, 4))

    assert recording_widget.activation_count == 0


def test_click_on_widget_disabled_during_click_does_not_activate(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    recording_widget.enabled = False

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 0


def test_click_on_widget_covered_during_click_does_not_activate(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    Panel(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 0


def test_click_on_widget_killed_during_click_does_not_activate(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    recording_widget.kill()

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 0


def test_click_on_widget_drag_off_then_back_on_during_click_activates(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    mouse_motion_event_1 = pg.Event(pg.MOUSEMOTION, pos=(10, 20))
    ui.handle_event(mouse_motion_event_1)

    mouse_motion_event_2 = pg.Event(pg.MOUSEMOTION, pos=(3, 4))
    ui.handle_event(mouse_motion_event_2)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 1


def test_up_after_lost_up_does_not_activate_stale_widget(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event_1 = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event_1)

    # the first down's up never arrived, so this down ends that press
    button_down_event_2 = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(10, 20),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event_2)

    # the press has ended, so this up cannot complete it
    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

    assert recording_widget.activation_count == 0


def test_lost_up_does_not_interfere_with_click_on_separate_widget(ui: UI):
    recording_widget_1 = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    recording_widget_2 = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(10, 0),
        offset=(0, 0),
    )

    button_down_event_1 = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event_1)

    # the first down's up never arrived, so pressing widget 2 replaces its press
    _left_click(ui, pos=(12, 2))

    assert recording_widget_1.activation_count == 0
    assert recording_widget_2.activation_count == 1


def test_focus_lost_during_click_does_not_activate_but_does_consume_up(ui: UI):
    recording_widget = RecordingWidget(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    focus_lost_event = pg.Event(pg.WINDOWFOCUSLOST)
    ui.handle_event(focus_lost_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(3, 4),
        button=pg.BUTTON_LEFT,
    )

    assert ui.handle_event(button_up_event)
    assert recording_widget.activation_count == 0


# endregion


# region --- Highlight --------------------------------------------------------


def test_initial_widget_shows_base_colour(highlight_ui: UI):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == BASE_COLOUR


def test_mouse_on_widget_shows_highlighted_colour(highlight_ui: UI):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_mouse_off_widget_shows_base_colour(highlight_ui: UI):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_motion_event_1 = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event_1)
    highlight_ui.update()

    mouse_motion_event_2 = pg.Event(pg.MOUSEMOTION, pos=(10, 20))
    highlight_ui.handle_event(mouse_motion_event_2)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == BASE_COLOUR


def test_mouse_on_widget_covered_by_consuming_widget_shows_base_colour(
    highlight_ui: UI,
):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    Panel(
        highlight_ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == BASE_COLOUR


def test_mouse_leaving_window_shows_base_colour(highlight_ui: UI):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    window_leave_event = pg.Event(pg.WINDOWLEAVE)
    highlight_ui.handle_event(window_leave_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == BASE_COLOUR


def test_focus_lost_shows_highlighted_colour(highlight_ui: UI):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    window_focus_lost_event = pg.Event(pg.WINDOWFOCUSLOST)
    highlight_ui.handle_event(window_focus_lost_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_widget_disabled_under_cursor_shows_disabled_colour(highlight_ui: UI):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR

    widget.enabled = False
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == DISABLED_COLOUR


def test_widget_moved_away_from_cursor_shows_base_colour(highlight_ui: UI):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR

    widget.offset = (10, 20)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == BASE_COLOUR


def test_widget_covered_by_hidden_consuming_widget_shows_highlighted_colour(
    highlight_ui: UI,
):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    panel = Panel(
        highlight_ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        visible=True,
    )

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == BASE_COLOUR

    panel.visible = False
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_press_and_drag_to_second_widget_shows_base_colour_on_second_widget(
    highlight_ui: UI,
):
    InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    widget_2 = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(10, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    highlight_ui.handle_event(button_down_event)
    highlight_ui.update()

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(11, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    assert widget_2.image.get_at((1, 2)) == BASE_COLOUR


def test_press_and_drag_off_widget_shows_base_colour(
    highlight_ui: UI,
):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    highlight_ui.handle_event(button_down_event)
    highlight_ui.update()

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(11, 2))
    highlight_ui.handle_event(mouse_motion_event)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == BASE_COLOUR


def test_press_and_drag_off_and_back_on_widget_shows_highlighted_colour(
    highlight_ui: UI,
):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    highlight_ui.handle_event(button_down_event)
    highlight_ui.update()

    mouse_motion_event_1 = pg.Event(pg.MOUSEMOTION, pos=(11, 2))
    highlight_ui.handle_event(mouse_motion_event_1)
    highlight_ui.update()

    mouse_motion_event_2 = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    highlight_ui.handle_event(mouse_motion_event_2)
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_click_and_keep_mouse_on_widget_shows_highlighted_colour(
    highlight_ui: UI,
):
    widget = InteractiveWidget(
        highlight_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_click(highlight_ui, pos=(1, 2))
    highlight_ui.update()

    assert widget.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


# endregion
