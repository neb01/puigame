import os
import subprocess
import sys
from dataclasses import replace

import pygame as pg
import pytest

from puigame import (
    DEFAULT_THEME,
    Anchor,
    BundledCursor,
    BundledTypeface,
    CursorImage,
    CursorRole,
    FadeProfile,
    State,
    Style,
    StyleOverride,
    TextAlign,
    TextHorizontalExtent,
    Theme,
)
from puigame._styling.theme import _STATE_PRECEDENCE, _get_default_cursors

# region --- Constants --------------------------------------------------------

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

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

ANY_STYLE_OVERRIDES = {
    State.DISABLED: StyleOverride(body_colour=RED),
    State.HIGHLIGHTED: StyleOverride(body_colour=BLUE),
}

# endregion


# region --- Helpers ----------------------------------------------------------


def _cursor_image(size: tuple[int, int]) -> CursorImage:
    """Return a cursor image of a given size, for telling images apart.

    Args:
        size: Width and height in pixels.

    Returns:
        A cursor image with a blank image of that size and hotspot ``(0, 0)``.
    """
    return CursorImage(pg.Surface(size), (0, 0))


# endregion


# region --- Validation -------------------------------------------------------


def test_base_state_in_style_overrides_raises():
    with pytest.raises(ValueError):
        Theme(
            base_style=ANY_STYLE,
            style_overrides={State.BASE: StyleOverride(body_colour=RED)},
        )


def test_combined_state_in_style_overrides_raises():
    with pytest.raises(ValueError):
        Theme(
            base_style=ANY_STYLE,
            style_overrides={
                State.HIGHLIGHTED | State.DISABLED: StyleOverride(body_colour=RED),
            },
        )


def test_theme_without_cursors_stores_none():
    theme = Theme(base_style=ANY_STYLE, style_overrides={})

    assert theme.cursors is None


@pytest.mark.parametrize(
    "cursor_image",
    [BundledCursor.GREEN_ARROW, pg.Surface((9, 10)), None],
    ids=["BundledCursor", "pg.Surface", "None"],
)
def test_cursors_value_that_is_not_cursor_image_raises(cursor_image):
    with pytest.raises(TypeError):
        Theme(
            base_style=ANY_STYLE,
            style_overrides={},
            cursors={CursorRole.DEFAULT: cursor_image},
        )


def test_empty_cursors_raises():
    with pytest.raises(ValueError):
        Theme(base_style=ANY_STYLE, style_overrides={}, cursors={})


def test_cursors_without_default_raises():
    clickable_cursor_image = _cursor_image((11, 12))

    with pytest.raises(ValueError):
        Theme(
            base_style=ANY_STYLE,
            style_overrides={},
            cursors={CursorRole.CLICKABLE: clickable_cursor_image},
        )


# endregion


# region --- style_overrides copy ---------------------------------------------


def test_stored_style_overrides_copy_is_same_as_given():
    theme = Theme(base_style=ANY_STYLE, style_overrides=ANY_STYLE_OVERRIDES)

    assert theme.style_overrides == ANY_STYLE_OVERRIDES


def test_adding_key_to_style_overrides_raises():
    theme = Theme(base_style=ANY_STYLE, style_overrides=ANY_STYLE_OVERRIDES)

    with pytest.raises(TypeError):
        theme.style_overrides[State.CHECKED] = StyleOverride(body_colour=RED)  # pyright: ignore[reportIndexIssue]


def test_changing_source_style_overrides_dict_does_not_affect_theme():
    source_style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(base_style=ANY_STYLE, style_overrides=source_style_overrides)

    source_style_overrides[State.DISABLED] = StyleOverride(body_colour=BLACK)

    assert theme.style_overrides[State.DISABLED].body_colour == RED


# endregion


# region --- cursors copy -----------------------------------------------------


def test_stored_cursors_copy_is_same_as_given():
    default_cursor_image = _cursor_image((9, 10))
    clickable_cursor_image = _cursor_image((11, 12))
    cursors = {
        CursorRole.DEFAULT: default_cursor_image,
        CursorRole.CLICKABLE: clickable_cursor_image,
    }

    theme = Theme(base_style=ANY_STYLE, style_overrides={}, cursors=cursors)

    assert theme.cursors == cursors


def test_adding_key_to_cursors_raises():
    default_cursor_image = _cursor_image((9, 10))
    text_cursor_image = _cursor_image((13, 14))
    theme = Theme(
        base_style=ANY_STYLE,
        style_overrides={},
        cursors={CursorRole.DEFAULT: default_cursor_image},
    )

    with pytest.raises(TypeError):
        theme.cursors[CursorRole.TEXT] = text_cursor_image  # pyright: ignore[reportIndexIssue, reportOptionalSubscript]


def test_changing_source_cursors_dict_does_not_affect_theme():
    default_cursor_image = _cursor_image((9, 10))
    other_cursor_image = _cursor_image((11, 12))
    source_cursors = {CursorRole.DEFAULT: default_cursor_image}
    theme = Theme(base_style=ANY_STYLE, style_overrides={}, cursors=source_cursors)

    source_cursors[CursorRole.DEFAULT] = other_cursor_image

    assert theme.cursors == {CursorRole.DEFAULT: default_cursor_image}


# endregion


# region --- Theme._style_for() -----------------------------------------------


def test_style_for_base_state_returns_base_style():
    theme = Theme(base_style=ANY_STYLE, style_overrides=ANY_STYLE_OVERRIDES)

    style = theme._style_for(State.BASE)

    assert style is ANY_STYLE


def test_style_for_single_flag_changes_field_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=BLUE),
        style_overrides=style_overrides,
    )

    style = theme._style_for(State.DISABLED)

    assert style.body_colour == RED


def test_style_for_single_flag_does_not_change_fields_not_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(
        base_style=replace(ANY_STYLE, border_colour=BLACK, border_thickness=2),
        style_overrides=style_overrides,
    )

    style = theme._style_for(State.DISABLED)

    assert style.border_colour == BLACK
    assert style.border_thickness == 2


def test_style_for_inactive_flag_does_not_affect_any_fields():
    # HIGHLIGHTED is not in the state, so its border colour must not apply
    style_overrides = {
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
        State.DISABLED: StyleOverride(body_colour=RED),
    }
    theme = Theme(
        base_style=replace(ANY_STYLE, border_colour=BLACK),
        style_overrides=style_overrides,
    )

    style = theme._style_for(State.DISABLED)

    assert style.border_colour == BLACK


def test_style_for_flag_not_in_theme_is_ignored():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=WHITE, border_colour=BLACK),
        style_overrides=style_overrides,
    )

    style = theme._style_for(State.HIGHLIGHTED | State.DISABLED)

    assert style.body_colour == RED  # disabled still applies
    assert style.border_colour == BLACK  # highlighted request has not changed others


def test_style_for_multiple_flags_change_separate_fields_set_in_style_override():
    style_overrides = {
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
        State.DISABLED: StyleOverride(body_colour=RED),
    }
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=WHITE, border_colour=BLACK),
        style_overrides=style_overrides,
    )

    style = theme._style_for(State.HIGHLIGHTED | State.DISABLED)

    assert style.body_colour == RED
    assert style.border_colour == BLUE


@pytest.mark.parametrize(
    ("combined_flag", "style_overrides"),
    [
        (
            State.CHECKED | State.HIGHLIGHTED,
            {
                State.HIGHLIGHTED: StyleOverride(body_colour=BLUE),
                State.CHECKED: StyleOverride(body_colour=RED),
            },
        ),
        (
            State.HIGHLIGHTED | State.PRESSED,
            {
                State.PRESSED: StyleOverride(body_colour=BLUE),
                State.HIGHLIGHTED: StyleOverride(body_colour=RED),
            },
        ),
        (
            State.PRESSED | State.EDITING,
            {
                State.EDITING: StyleOverride(body_colour=BLUE),
                State.PRESSED: StyleOverride(body_colour=RED),
            },
        ),
        (
            State.EDITING | State.DISABLED,
            {
                State.DISABLED: StyleOverride(body_colour=BLUE),
                State.EDITING: StyleOverride(body_colour=RED),
            },
        ),
    ],
    ids=[
        "checked | highlighted",
        "highlighted | pressed",
        "pressed | editing",
        "editing | disabled",
    ],
)
def test_style_for_honours_precedence_order(combined_flag, style_overrides):
    # each style_overrides lists the higher-precedence flag first, so the test
    # fails if dict order decides instead of precedence
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=WHITE),
        style_overrides=style_overrides,
    )

    style = theme._style_for(combined_flag)

    assert style.body_colour == BLUE


# endregion


# region --- Theme._cursor_for() ----------------------------------------------


def test_cursor_for_mapped_role_returns_its_image():
    default_cursor_image = _cursor_image((9, 10))
    clickable_cursor_image = _cursor_image((11, 12))
    theme = Theme(
        base_style=ANY_STYLE,
        style_overrides={},
        cursors={
            CursorRole.DEFAULT: default_cursor_image,
            CursorRole.CLICKABLE: clickable_cursor_image,
        },
    )

    cursor_image = theme._cursor_for(CursorRole.CLICKABLE)

    assert cursor_image is clickable_cursor_image


def test_cursor_for_role_left_out_returns_default_image():
    default_cursor_image = _cursor_image((9, 10))
    clickable_cursor_image = _cursor_image((11, 12))
    theme = Theme(
        base_style=ANY_STYLE,
        style_overrides={},
        cursors={
            CursorRole.DEFAULT: default_cursor_image,
            CursorRole.CLICKABLE: clickable_cursor_image,
        },
    )

    cursor_image = theme._cursor_for(CursorRole.TEXT)

    assert cursor_image is default_cursor_image


@pytest.mark.parametrize(
    ("cursor_role", "expected_bundled_cursor", "expected_hotspot"),
    [
        (CursorRole.DEFAULT, BundledCursor.GREEN_ARROW, (0, 0)),
        (CursorRole.CLICKABLE, BundledCursor.GREEN_HAND, (3, 0)),
        (CursorRole.TEXT, BundledCursor.GREEN_I_BEAM, (4, 7)),
    ],
    ids=["default", "clickable", "text"],
)
def test_cursor_for_without_cursors_returns_bundled_green_cursor(
    cursor_role,
    expected_bundled_cursor,
    expected_hotspot,
):
    theme = Theme(base_style=ANY_STYLE, style_overrides={})
    expected_image = CursorImage.bundled(expected_bundled_cursor).image

    cursor_image = theme._cursor_for(cursor_role)

    assert cursor_image.hotspot == expected_hotspot
    assert pg.image.tobytes(cursor_image.image, "RGBA") == pg.image.tobytes(
        expected_image,
        "RGBA",
    )


def test_cursor_for_without_cursors_returns_same_image_every_call():
    theme_1 = Theme(base_style=ANY_STYLE, style_overrides={})
    theme_2 = Theme(base_style=ANY_STYLE, style_overrides={})

    cursor_image_1 = theme_1._cursor_for(CursorRole.DEFAULT)
    cursor_image_2 = theme_2._cursor_for(CursorRole.DEFAULT)

    assert cursor_image_1 is cursor_image_2


def test_cursor_for_without_cursors_leaves_cursors_none():
    theme = Theme(base_style=ANY_STYLE, style_overrides={})

    theme._cursor_for(CursorRole.DEFAULT)

    assert theme.cursors is None


# a fresh interpreter, since this session's cache may already be filled
def test_importing_puigame_does_not_load_bundled_cursors():
    code = (
        "import puigame._styling.theme as theme; "
        "print(theme._get_default_cursors.cache_info().currsize)"
    )

    # hide pygame's greeting, which would come before the printed size
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYGAME_HIDE_SUPPORT_PROMPT": "1"},
    )

    assert result.stdout.strip() == "0"


# endregion


# region --- Structure --------------------------------------------------------


# iterating State itself skips BASE, which has no bits set
@pytest.mark.parametrize("state", State.__members__.values())
def test_default_theme_provides_style_for_every_state(state):
    assert isinstance(DEFAULT_THEME._style_for(state), Style)


def test_state_precedence_lists_exactly_non_base_states():
    expected_states = {
        state for state in State.__members__.values() if state is not State.BASE
    }

    assert set(_STATE_PRECEDENCE) == expected_states


def test_no_duplicates_in_state_precedence():
    assert len(_STATE_PRECEDENCE) == len(set(_STATE_PRECEDENCE))


# _cursor_for() would quietly show DEFAULT's image for a role missing here, so
# a new role without a bundled cursor would go unnoticed
def test_default_cursors_map_exactly_every_cursor_role():
    assert set(_get_default_cursors()) == set(CursorRole)


# endregion
