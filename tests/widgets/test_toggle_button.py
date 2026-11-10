from dataclasses import replace
from typing import NoReturn

import pygame as pg
import pytest
from pygame.typing import Point

from puigame import (
    DEFAULT_THEME,
    UI,
    Anchor,
    BundledTypeface,
    FadeProfile,
    NoSkin,
    State,
    Style,
    StyleOverride,
    TextAlign,
    TextHorizontalExtent,
    Theme,
    ToggleButton,
)
from puigame._components.placed_image import PlacedImage
from puigame._components.skin import Skin
from puigame._ui.ui_root import UIRoot

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)
ANY_SKIN = NoSkin()


RED = (255, 0, 0, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

BODY_BASE_COLOUR = (0, 100, 50, 255)
BORDER_BASE_COLOUR = (250, 100, 50, 255)
CHECKED_COLOUR = (100, 100, 100, 255)
HIGHLIGHTED_COLOUR = (0, 255, 0, 255)
PRESSED_COLOUR = (0, 0, 255, 255)
DISABLED_COLOUR = RED

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
    text_align=TextAlign.LEFT,
    text_horizontal_extent=TextHorizontalExtent.INK,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

STATE_COLOUR_THEME = Theme(
    base_style=replace(
        ANY_STYLE,
        body_colour=BODY_BASE_COLOUR,
        border_colour=BORDER_BASE_COLOUR,
    ),
    style_overrides={
        State.CHECKED: StyleOverride(border_colour=CHECKED_COLOUR),
        State.HIGHLIGHTED: StyleOverride(body_colour=HIGHLIGHTED_COLOUR),
        State.PRESSED: StyleOverride(body_colour=PRESSED_COLOUR),
        State.DISABLED: StyleOverride(body_colour=DISABLED_COLOUR),
    },
)

ANY_THEME = Theme(base_style=ANY_STYLE, style_overrides={})

# endregion


# region --- Stubs ------------------------------------------------------------


class BodyAndBorderColourLayer(Skin):
    """Skin that shows the style's body colour and border colour side by side.

    The top row is the border colour and the rest is the body colour, at fixed
    positions whatever the border thickness, so a test can read both fields
    from one image, such as ``CHECKED``'s border with ``PRESSED``'s body.
    """

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Return a new surface of ``size`` at (0, 0), top row in the border colour."""
        image = pg.Surface(size, pg.SRCALPHA)
        image.fill(style.body_colour)
        image.fill(style.border_colour, pg.Rect((0, 0), (size[0], 1)))

        return PlacedImage(image, (0, 0))


class OnToggleError(Exception):
    """Error raised by ``on_toggle_error()``, distinct from any built-in error."""


def on_toggle_error(_toggle_button: ToggleButton, _checked: bool) -> NoReturn:
    """Raise ``OnToggleError``, as an ``on_toggle`` callback that fails.

    Args:
        _toggle_button: The toggled button. Not used.
        _checked: The button's new value. Not used.

    Raises:
        OnToggleError: Always.
    """
    raise OnToggleError


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
def state_colour_ui() -> UI:
    """Return a UI whose theme gives each state its own colour.

    ``CHECKED`` changes the border colour and every other state the body
    colour, so a checked look shows alongside each of the others.
    """
    return UI(size=(300, 200), theme=STATE_COLOUR_THEME)


# endregion


# region --- Construction -----------------------------------------------------


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("hit_testable", False),
    ],
)
def test_forwards_arguments_stored_as_attributes(ui_root: UIRoot, field_name, value):
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        **{field_name: value},
    )

    assert getattr(toggle_button, field_name) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=ANY_THEME)
    toggle_button = ToggleButton(
        ui_root,
        size=(3, 5),
        skin=ANY_SKIN,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert toggle_button.rect.topleft == (-5, 21)


def test_hit_testable_true_by_default(ui_root: UIRoot):
    toggle_button = ToggleButton(ui_root, size=ANY_SIZE, skin=ANY_SKIN)

    assert toggle_button.hit_testable


def test_checked_false_by_default(ui_root: UIRoot):
    toggle_button = ToggleButton(ui_root, size=ANY_SIZE, skin=ANY_SKIN)

    assert not toggle_button.checked


def test_checked_true_when_created_checked(ui_root: UIRoot):
    toggle_button = ToggleButton(ui_root, size=ANY_SIZE, skin=ANY_SKIN, checked=True)

    assert toggle_button.checked


def test_on_toggle_not_called_when_created_checked(ui_root: UIRoot):
    on_toggle_calls = []
    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        checked=True,
    )

    assert on_toggle_calls == []


# endregion


# region --- text -------------------------------------------------------------


def test_text_getter_returns_given_text(ui_root: UIRoot):
    toggle_button = ToggleButton(ui_root, size=ANY_SIZE, skin=ANY_SKIN, text="carapace")

    assert toggle_button.text == "carapace"


def test_text_defaults_to_empty_string(ui_root: UIRoot):
    toggle_button = ToggleButton(ui_root, size=ANY_SIZE, skin=ANY_SKIN)

    assert toggle_button.text == ""


# endregion


# region --- checked ----------------------------------------------------------


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_checked_setter_with_other_value_changes_checked(
    ui_root: UIRoot,
    checked,
    expected_checked,
):
    toggle_button = ToggleButton(ui_root, size=ANY_SIZE, skin=ANY_SKIN, checked=checked)

    toggle_button.checked = expected_checked

    assert toggle_button.checked is expected_checked


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_checked_setter_with_other_value_calls_on_toggle_once_with_new_value(
    ui_root: UIRoot,
    checked,
    expected_checked,
):
    on_toggle_calls = []
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        checked=checked,
    )

    toggle_button.checked = expected_checked

    assert on_toggle_calls == [(toggle_button, expected_checked)]


@pytest.mark.parametrize(
    "checked",
    [False, True],
    ids=["initial unchecked", "initial checked"],
)
def test_checked_setter_with_same_value_does_not_call_on_toggle(
    ui_root: UIRoot,
    checked,
):
    on_toggle_calls = []
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        checked=checked,
    )

    toggle_button.checked = checked

    assert on_toggle_calls == []


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_on_toggle_sees_new_checked_value(ui_root: UIRoot, checked, expected_checked):
    on_toggle_calls = []
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, _checked: on_toggle_calls.append(
            (toggle_button, toggle_button.checked),
        ),
        checked=checked,
    )

    toggle_button.checked = expected_checked

    assert on_toggle_calls == [(toggle_button, expected_checked)]


def test_changing_checked_with_no_on_toggle_does_not_raise(ui_root: UIRoot):
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=None,
        checked=True,
    )

    toggle_button.checked = False


# endregion


# region --- toggle() ---------------------------------------------------------


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_toggle_toggles_checked(ui_root: UIRoot, checked, expected_checked):
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        checked=checked,
    )

    toggle_button.toggle()

    assert toggle_button.checked is expected_checked


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_toggle_calls_on_toggle_once_with_new_value(
    ui_root: UIRoot,
    checked,
    expected_checked,
):
    on_toggle_calls = []
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        checked=checked,
    )

    toggle_button.toggle()

    assert on_toggle_calls == [(toggle_button, expected_checked)]


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_toggle_on_disabled_button_toggles_checked(
    ui_root: UIRoot,
    checked,
    expected_checked,
):
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        enabled=False,
        checked=checked,
    )

    toggle_button.toggle()

    assert toggle_button.checked is expected_checked


# endregion


# region --- Clicks -----------------------------------------------------------


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_click_toggles_checked(ui: UI, checked, expected_checked):
    toggle_button = ToggleButton(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        checked=checked,
    )

    _left_click(ui, pos=(1, 2))

    assert toggle_button.checked is expected_checked


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, True),
        (True, False),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_click_calls_on_toggle_once_with_new_value(ui: UI, checked, expected_checked):
    on_toggle_calls = []
    toggle_button = ToggleButton(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        checked=checked,
    )

    _left_click(ui, pos=(1, 2))

    assert on_toggle_calls == [(toggle_button, expected_checked)]


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, False),
        (True, True),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_press_alone_does_not_toggle_checked(ui: UI, checked, expected_checked):
    toggle_button = ToggleButton(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        checked=checked,
    )

    _left_press(ui, pos=(1, 2))

    assert toggle_button.checked is expected_checked


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, False),
        (True, True),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_release_off_button_does_not_toggle_checked(ui: UI, checked, expected_checked):
    toggle_button = ToggleButton(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        checked=checked,
    )

    _left_press(ui, pos=(1, 2))
    _left_release(ui, pos=(10, 20))

    assert toggle_button.checked is expected_checked


@pytest.mark.parametrize(
    ("checked", "expected_checked"),
    [
        (False, False),
        (True, True),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_click_on_disabled_button_does_not_toggle_checked(
    ui: UI,
    checked,
    expected_checked,
):
    toggle_button = ToggleButton(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=False,
        visible=True,
        hit_testable=True,
        checked=checked,
    )

    _left_click(ui, pos=(1, 2))

    assert toggle_button.checked is expected_checked


def test_exceptions_propagate(ui: UI):
    ToggleButton(
        ui.root,
        size=(5, 6),
        skin=ANY_SKIN,
        on_toggle=on_toggle_error,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
    )

    _left_press(ui, pos=(1, 2))

    with pytest.raises(OnToggleError):
        _left_release(ui, pos=(1, 2))


# endregion


# region --- Checked look -----------------------------------------------------


def test_checked_button_shows_checked_border_colour(state_colour_ui: UI):
    toggle_button = ToggleButton(
        state_colour_ui.root,
        size=(5, 6),
        skin=BodyAndBorderColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        checked=True,
    )

    state_colour_ui.update()

    assert toggle_button.image.get_at((1, 0)) == CHECKED_COLOUR


def test_checked_and_highlighted_button_shows_checked_border_and_highlighted_body(
    state_colour_ui: UI,
):
    toggle_button = ToggleButton(
        state_colour_ui.root,
        size=(5, 6),
        skin=BodyAndBorderColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        checked=True,
    )

    _move_mouse(state_colour_ui, pos=(1, 2))
    state_colour_ui.update()

    assert toggle_button.image.get_at((1, 0)) == CHECKED_COLOUR
    assert toggle_button.image.get_at((1, 3)) == HIGHLIGHTED_COLOUR


def test_checked_and_pressed_button_shows_checked_border_and_pressed_body(
    state_colour_ui: UI,
):
    toggle_button = ToggleButton(
        state_colour_ui.root,
        size=(5, 6),
        skin=BodyAndBorderColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        checked=True,
    )

    _left_press(state_colour_ui, pos=(1, 2))
    state_colour_ui.update()

    assert toggle_button.image.get_at((1, 0)) == CHECKED_COLOUR
    assert toggle_button.image.get_at((1, 3)) == PRESSED_COLOUR


def test_checked_and_disabled_button_shows_checked_border_and_disabled_body(
    state_colour_ui: UI,
):
    toggle_button = ToggleButton(
        state_colour_ui.root,
        size=(5, 6),
        skin=BodyAndBorderColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=False,
        checked=True,
    )

    state_colour_ui.update()

    assert toggle_button.image.get_at((1, 0)) == CHECKED_COLOUR
    assert toggle_button.image.get_at((1, 3)) == DISABLED_COLOUR


@pytest.mark.parametrize(
    ("initial_checked", "updated_checked", "expected_border_colour"),
    [
        (False, True, CHECKED_COLOUR),
        (True, False, BORDER_BASE_COLOUR),
    ],
    ids=["initial unchecked", "initial checked"],
)
def test_checked_setter_updates_image_after_update(
    state_colour_ui: UI,
    initial_checked,
    updated_checked,
    expected_border_colour,
):
    toggle_button = ToggleButton(
        state_colour_ui.root,
        size=(5, 6),
        skin=BodyAndBorderColourLayer(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        checked=initial_checked,
    )

    toggle_button.checked = updated_checked
    state_colour_ui.update()

    assert toggle_button.image.get_at((1, 0)) == expected_border_colour


# endregion


# region --- Validation -------------------------------------------------------


@pytest.mark.parametrize(
    "on_toggle",
    [3, "large rooster mayhem"],
    ids=["int", "str"],
)
def test_constructor_with_non_callable_on_toggle_raises(ui: UI, on_toggle):
    with pytest.raises(TypeError):
        ToggleButton(
            ui.root,
            size=ANY_SIZE,
            skin=ANY_SKIN,
            on_toggle=on_toggle,
        )

    assert ui.root.children == ()


def test_constructor_with_non_string_text_raises(ui_root: UIRoot):
    with pytest.raises(TypeError):
        ToggleButton(
            ui_root,
            size=ANY_SIZE,
            skin=ANY_SKIN,
            text=6.7,  # pyright: ignore[reportArgumentType]
        )

    assert ui_root.children == ()


# endregion


# region --- DEFAULT_THEME ----------------------------------------------------


@pytest.mark.parametrize(
    "state",
    [
        State.BASE,
        State.HIGHLIGHTED,
        State.HIGHLIGHTED | State.PRESSED,
        State.DISABLED,
    ],
)
def test_default_theme_checked_changes_style_in_every_toggle_button_state(state):
    checked_style = DEFAULT_THEME._style_for(state | State.CHECKED)
    unchecked_style = DEFAULT_THEME._style_for(state)

    assert checked_style != unchecked_style


# endregion
