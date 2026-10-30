from dataclasses import replace
from typing import NoReturn

import pygame as pg
import pytest

from puigame import (
    DEFAULT_THEME,
    UI,
    Anchor,
    BundledTypeface,
    Button,
    NoSkin,
    State,
    StyleOverride,
    Theme,
)
from puigame._ui.ui_root import UIRoot
from stubs import BodyColourLayer

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 11)
ANY_SKIN = NoSkin()
ANY_STRING = "beans beans on toast"

WHITE = (255, 255, 255, 255)
RED = (255, 0, 0, 255)
BLACK = (0, 0, 0, 255)

BASE_COLOUR = (0, 0, 0, 255)
DISABLED_COLOUR = (255, 0, 0, 255)
HIGHLIGHTED_COLOUR = (0, 255, 0, 255)
PRESSED_COLOUR = (0, 0, 255, 255)

PRESS_THEME = Theme(
    base_style=replace(DEFAULT_THEME.base_style, body_colour=BASE_COLOUR),
    style_overrides={
        State.DISABLED: StyleOverride(body_colour=DISABLED_COLOUR),
        State.HIGHLIGHTED: StyleOverride(body_colour=HIGHLIGHTED_COLOUR),
        State.PRESSED: StyleOverride(body_colour=PRESSED_COLOUR),
    },
)

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


# region --- Fixtures ---------------------------------------------------------


@pytest.fixture
def press_ui() -> UI:
    """Return a UI whose theme gives each state its own body colour."""
    return UI(size=(300, 200), theme=PRESS_THEME)


# endregion


# region --- Construction -----------------------------------------------------


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("consumes_clicks", False),
    ],
    ids=["offset", "enabled", "visible", "consumes_clicks"],
)
def test_forwards_public_arguments(ui_root: UIRoot, argument, value):
    button = Button(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        **{argument: value},
    )

    assert getattr(button, argument) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=DEFAULT_THEME)
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
            DEFAULT_THEME.base_style,
            text_colour=BLACK,
            text_typeface=BundledTypeface.PYGAME_DEFAULT,
            text_font_size=20,
            text_anchor=Anchor.CENTRE,
            text_parent_anchor=Anchor.CENTRE,
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

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(10, 11))
    ui.handle_event(mouse_motion_event)
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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_down_event)
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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_down_event)
    press_ui.update()

    mouse_motion_event = pg.Event(pg.MOUSEMOTION, pos=(11, 12))
    press_ui.handle_event(mouse_motion_event)
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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_down_event)
    press_ui.update()

    mouse_motion_event_1 = pg.Event(pg.MOUSEMOTION, pos=(11, 12))
    press_ui.handle_event(mouse_motion_event_1)
    press_ui.update()

    mouse_motion_event_2 = pg.Event(pg.MOUSEMOTION, pos=(1, 2))
    press_ui.handle_event(mouse_motion_event_2)
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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_down_event)
    press_ui.update()

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_up_event)
    press_ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_button_down_released_off_button_shows_base_colour(press_ui: UI):
    button = Button(
        press_ui.root,
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
    press_ui.handle_event(button_down_event)
    press_ui.update()

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(11, 12),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_up_event)
    press_ui.update()

    assert button.image.get_at((1, 2)) == BASE_COLOUR


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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_down_event)
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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    press_ui.handle_event(button_down_event)
    press_ui.update()

    window_focus_lost_event = pg.Event(pg.WINDOWFOCUSLOST)
    press_ui.handle_event(window_focus_lost_event)
    press_ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_right_button_down_then_held_over_shows_highlighted_colour(press_ui: UI):
    button = Button(
        press_ui.root,
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
        button=pg.BUTTON_RIGHT,
    )
    press_ui.handle_event(button_down_event)
    press_ui.update()

    assert button.image.get_at((1, 2)) == HIGHLIGHTED_COLOUR


def test_pressed_keeps_highlighted_fields_that_it_does_not_override():
    theme = Theme(
        base_style=replace(DEFAULT_THEME.base_style, body_colour=BASE_COLOUR),
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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)
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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)

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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_up_event)


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

    button_down_event = pg.Event(
        pg.MOUSEBUTTONDOWN,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )
    ui.handle_event(button_down_event)

    button_up_event = pg.Event(
        pg.MOUSEBUTTONUP,
        pos=(1, 2),
        button=pg.BUTTON_LEFT,
    )

    with pytest.raises(OnClickError):
        ui.handle_event(button_up_event)


# endregion


# region --- Type checks ------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [5, 6.7, None, b"bytes object"],
    ids=["int", "float", "None", "bytes"],
)
def test_constructor_with_non_string_text_raises(ui_root: UIRoot, text):
    with pytest.raises(TypeError):
        Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN, text=text)

    assert ui_root.children == ()


@pytest.mark.parametrize(
    "text",
    [5, 6.7, None, b"bytes object"],
    ids=["int", "float", "None", "bytes"],
)
def test_text_setter_with_non_string_text_raises(ui_root: UIRoot, text):
    button = Button(ui_root, size=ANY_SIZE, skin=ANY_SKIN, text="corndog")

    with pytest.raises(TypeError):
        button.text = text

    assert button.text == "corndog"


@pytest.mark.parametrize(
    "on_click",
    [5, "poppycock"],
    ids=["int", "string"],
)
def test_non_callable_on_click_raises(ui: UI, on_click):
    with pytest.raises(TypeError):
        Button(
            ui.root,
            size=ANY_SIZE,
            skin=ANY_SKIN,
            on_click=on_click,
        )

    assert ui.root.children == ()


# endregion
