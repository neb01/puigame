from dataclasses import replace
from typing import NoReturn

import pygame as pg
import pytest

from puigame import (
    UI,
    Anchor,
    BundledTypeface,
    Button,
    FadeProfile,
    NoSkin,
    State,
    Style,
    StyleOverride,
    TextHorizontalExtent,
    Theme,
)
from puigame._ui.ui_root import UIRoot
from stubs import BodyColourLayer

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)
ANY_SKIN = NoSkin()
ANY_STRING = "beans beans on toast"

RED = (255, 0, 0, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

BASE_COLOUR = (0, 0, 0, 255)
HIGHLIGHTED_COLOUR = (0, 255, 0, 255)
PRESSED_COLOUR = (0, 0, 255, 255)
DISABLED_COLOUR = (255, 0, 0, 255)

ANY_STYLE = Style(
    body_colour=WHITE,
    border_colour=BLACK,
    border_thickness=2,
    corner_radius=2,
    halo_colour=(0, 0, 0, 0),
    halo_fade_profile=FadeProfile.SOLID,
    halo_thickness=0,
    swell=0,
    text_colour=BLACK,
    text_typeface=BundledTypeface.PYGAME_DEFAULT,
    text_font_size=12,
    text_anchor=Anchor.CENTRE,
    text_parent_anchor=Anchor.CENTRE,
    text_horizontal_extent=TextHorizontalExtent.INK,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

PRESS_THEME = Theme(
    base_style=replace(ANY_STYLE, body_colour=BASE_COLOUR),
    style_overrides={
        State.HIGHLIGHTED: StyleOverride(body_colour=HIGHLIGHTED_COLOUR),
        State.PRESSED: StyleOverride(body_colour=PRESSED_COLOUR),
        State.DISABLED: StyleOverride(body_colour=DISABLED_COLOUR),
    },
)

ANY_THEME = Theme(base_style=ANY_STYLE, style_overrides={})

# endregion


# region --- Stubs ------------------------------------------------------------


class OnClickError(Exception):
    """Error raised by ``on_click_error()``, distinct from any built-in error."""


def on_click_error(_button: Button) -> NoReturn:
    """Raise ``OnClickError``, as an ``on_click`` callback that fails.

    Args:
        _button: The clicked button. Not used.

    Raises:
        OnClickError: Always.
    """
    raise OnClickError


# endregion


# region --- Helpers ----------------------------------------------------------


def _left_press(ui: UI, *, pos: tuple[int, int]) -> bool:
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


def _left_release(ui: UI, *, pos: tuple[int, int]) -> bool:
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


def _left_click(ui: UI, *, pos: tuple[int, int]) -> None:
    """Send a left press and release at ``pos``, as one click.

    Args:
        ui: UI to send the events to.
        pos: Position of both events.
    """
    _left_press(ui, pos=pos)
    _left_release(ui, pos=pos)


def _move_mouse(ui: UI, *, pos: tuple[int, int]) -> None:
    """Send a mouse motion to ``pos``.

    Motion is never consumed, so nothing is returned.

    Args:
        ui: UI to send the event to.
        pos: Position the cursor moves to.
    """
    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=pos)
    ui.handle_event(mouse_motion_event)


# endregion


# region --- Fixtures ---------------------------------------------------------


@pytest.fixture
def press_ui() -> UI:
    """Return a UI whose theme gives each state its own body colour."""
    return UI(size=(300, 200), theme=PRESS_THEME)


# endregion


# region --- Construction -----------------------------------------------------


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("consumes_clicks", False),
    ],
)
def test_forwards_arguments_stored_as_attributes(ui_root: UIRoot, field_name, value):
    button = Button(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        **{field_name: value},
    )

    assert getattr(button, field_name) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=ANY_THEME)
    button = Button(
        ui_root,
        size=(3, 5),
        skin=ANY_SKIN,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert button.rect.topleft == (-5, 21)


def test_consumes_clicks_true_by_default(ui_root: UIRoot):
    button = Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN)

    assert button.consumes_clicks


# endregion


# region --- text -------------------------------------------------------------


def test_text_getter_returns_given_text(ui_root: UIRoot):
    button = Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN, text="sheep")

    assert button.text == "sheep"


def test_text_defaults_to_empty_string(ui_root: UIRoot):
    button = Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN)

    assert button.text == ""


# endregion


# region --- Image ------------------------------------------------------------


def test_text_setter_updates_image(ui_root: UIRoot):
    button = Button(ui_root, size=ANY_SIZE, skin=NoSkin(), text="")

    assert button.image.size == (0, 0)

    button.text = ANY_STRING

    assert 0 not in button.image.size


def test_text_setter_with_current_text_keeps_image(ui_root: UIRoot):
    button = Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN, text="cranium")
    image = button.image

    button.text = "cranium"

    assert button.image is image


def test_text_drawn_in_highlighted_style_when_button_is_highlighted():
    surface = pg.Surface((300, 200), pg.SRCALPHA)
    surface.fill(WHITE)

    theme = Theme(
        base_style=replace(
            ANY_STYLE,
            text_colour=BLACK,
            text_typeface=BundledTypeface.PYGAME_DEFAULT,
            text_font_size=20,
            text_anchor=Anchor.CENTRE,
            text_parent_anchor=Anchor.CENTRE,
            text_horizontal_extent=TextHorizontalExtent.INK,
            text_offset=(0, 0),
        ),
        style_overrides={State.HIGHLIGHTED: StyleOverride(text_colour=RED)},
    )
    ui = UI(size=(300, 200), theme=theme)

    Button(
        ui.root,
        size=(30, 30),
        skin=NoSkin(),
        text="I",
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    ui.update()
    ui.draw(surface)

    assert surface.get_at((15, 15)) == BLACK

    _move_mouse(ui, pos=(10, 11))
    ui.update()

    surface.fill(WHITE)
    ui.draw(surface)

    assert surface.get_at((15, 15)) == RED


# endregion


# region --- Pressed look -----------------------------------------------------


def test_button_down_held_over_shows_pressed_colour(press_ui: UI):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(press_ui, pos=(1, 2))
    press_ui.update()

    assert button.image.get_at((1, 2)) == PRESSED_COLOUR


def test_button_down_then_dragged_off_shows_base_colour(press_ui: UI):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(press_ui, pos=(1, 2))
    press_ui.update()

    _move_mouse(press_ui, pos=(10, 11))
    press_ui.update()

    assert button.image.get_at((1, 2)) == BASE_COLOUR


def test_button_down_then_dragged_off_then_back_on_shows_pressed_colour(press_ui: UI):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(press_ui, pos=(1, 2))
    press_ui.update()

    _move_mouse(press_ui, pos=(11, 12))
    press_ui.update()

    _move_mouse(press_ui, pos=(1, 2))
    press_ui.update()

    assert button.image.get_at((1, 2)) == PRESSED_COLOUR


def test_button_down_released_over_button_shows_highlighted_colour(press_ui: UI):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(press_ui, pos=(1, 2))
    press_ui.update()

    _left_release(press_ui, pos=(1, 2))
    press_ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_button_down_released_off_then_moved_back_on_shows_highlighted_colour(
    press_ui: UI,
):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(press_ui, pos=(1, 2))
    press_ui.update()

    _left_release(press_ui, pos=(11, 12))
    press_ui.update()

    _move_mouse(press_ui, pos=(1, 2))
    press_ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_disabled_during_press_shows_disabled_colour(press_ui: UI):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(press_ui, pos=(1, 2))
    press_ui.update()

    button.enabled = False
    press_ui.update()

    assert button.image.get_at((1, 2)) == DISABLED_COLOUR


def test_focus_lost_during_press_shows_highlighted_colour(press_ui: UI):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(press_ui, pos=(1, 2))
    press_ui.update()

    window_focus_lost_event = pg.Event(pg.WINDOWFOCUSLOST)
    press_ui.handle_event(window_focus_lost_event)
    press_ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_right_button_down_held_over_shows_highlighted_colour(press_ui: UI):
    button = Button(
        press_ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    mouse_button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_RIGHT,
    )
    press_ui.handle_event(mouse_button_down_event)
    press_ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_pressed_keeps_highlighted_fields_that_it_does_not_override():
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=BASE_COLOUR),
        style_overrides={
            State.HIGHLIGHTED: StyleOverride(body_colour=HIGHLIGHTED_COLOUR),
            State.PRESSED: StyleOverride(),
        },
    )
    ui = UI(size=(300, 200), theme=theme)

    button = Button(
        ui.root,
        size=(5, 6),
        skin=BodyColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(ui, pos=(1, 2))
    ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


# endregion


# region --- on_click ---------------------------------------------------------


def test_on_click_is_called_once_with_button_as_argument(ui: UI):
    on_click_calls = []

    button = Button(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        on_click=on_click_calls.append,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_click(ui, pos=(1, 2))

    assert on_click_calls == [button]


def test_button_down_alone_does_not_call_on_click(ui: UI):
    on_click_calls = []

    Button(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        on_click=on_click_calls.append,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(ui, pos=(1, 2))

    assert on_click_calls == []


def test_click_on_button_with_no_on_click_does_not_raise(ui: UI):
    Button(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        on_click=None,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_click(ui, pos=(1, 2))


def test_exceptions_propagate(ui: UI):
    Button(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        on_click=on_click_error,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    _left_press(ui, pos=(1, 2))

    with pytest.raises(OnClickError):
        _left_release(ui, pos=(1, 2))


# endregion


# region --- Validation -------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [5, 6.7, b"bytes object", None],
    ids=["int", "float", "bytes", "None"],
)
def test_constructor_with_non_string_text_raises(ui_root: UIRoot, text):
    with pytest.raises(TypeError):
        Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN, text=text)

    assert ui_root.children == ()


@pytest.mark.parametrize(
    "text",
    [5, 6.7, b"bytes object", None],
    ids=["int", "float", "bytes", "None"],
)
def test_text_setter_with_non_string_text_raises(ui_root: UIRoot, text):
    button = Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN, text="corndog")

    with pytest.raises(TypeError):
        button.text = text

    assert button.text == "corndog"


@pytest.mark.parametrize(
    "on_click",
    [5, "poppycock"],
    ids=["int", "str"],
)
def test_constructor_with_non_callable_on_click_raises(ui: UI, on_click):
    with pytest.raises(TypeError):
        Button(
            ui.root,
            size=ANY_SIZE,
            skin=ANY_SKIN,
            on_click=on_click,
        )

    assert ui.root.children == ()


# endregion
