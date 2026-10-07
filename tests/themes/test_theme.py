from dataclasses import fields

import pytest

from puigame.core.anchor import Anchor
from puigame.core.state import State
from puigame.themes.theme import DEFAULT_THEME, Style, StyleOverride, Theme

# region --- Constants --------------------------------------------------------


RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

BASE_STYLE = Style(
    background_colour=WHITE,
    border_colour=BLACK,
    border_width_pixels=2,
    background_corner_radius_pixels=2,
    halo_colour=(0, 0, 0, 0),
    halo_colour_fade_to_clear=False,
    halo_thickness_pixels=0,
    swell_increase_pixels=0,
    text_colour=BLACK,
    text_font_name=None,
    text_font_size=12,
    text_anchor=Anchor.CENTRE,
    text_parent_anchor=Anchor.CENTRE,
    text_margin=(0, 0),
    text_is_bold=False,
    text_is_underlined=False,
    text_is_italic=False,
)

ANY_STYLE_OVERRIDES = {
    State.DISABLED: StyleOverride(background_colour=RED),
    State.HIGHLIGHTED: StyleOverride(background_colour=BLUE),
}

# endregion


# region --- Theme.__post_init__ ----------------------------------------------


def test_base_state_in_style_overrides_raises():
    with pytest.raises(ValueError):
        Theme(
            BASE_STYLE,
            {State.BASE: StyleOverride(background_colour=RED)},
        )


def test_stored_style_overrides_copy_is_same_as_given():
    theme = Theme(BASE_STYLE, ANY_STYLE_OVERRIDES)

    assert theme.style_overrides == ANY_STYLE_OVERRIDES


def test_assigning_to_theme_style_overrides_raises():
    theme = Theme(
        BASE_STYLE,
        {
            State.DISABLED: StyleOverride(background_colour=RED),
            State.HIGHLIGHTED: StyleOverride(background_colour=BLUE),
        },
    )

    with pytest.raises(TypeError):
        theme.style_overrides[State.CHECKED] = StyleOverride(background_colour=RED)  # pyright: ignore[reportIndexIssue]


def test_changing_source_style_overrides_dict_does_not_affect_theme():
    source_style_overrides = {State.DISABLED: StyleOverride(background_colour=RED)}
    theme = Theme(BASE_STYLE, source_style_overrides)

    source_style_overrides[State.DISABLED] = StyleOverride(background_colour=BLACK)

    assert theme.style_overrides[State.DISABLED].background_colour == RED


# endregion


# region --- Theme.style_for ---------------------------------------------------


def test_style_for_base_state_returns_base_style():
    """No flags are set, so no override applies and the base itself is returned."""
    theme = Theme(BASE_STYLE, ANY_STYLE_OVERRIDES)

    style = theme.style_for(State.BASE)

    assert style is BASE_STYLE


def test_single_flag_changes_field_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(background_colour=RED)}
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED)

    assert style.background_colour == RED


def test_single_flag_does_not_change_fields_not_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(background_colour=RED)}
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED)

    assert style.border_colour == BLACK
    assert style.border_width_pixels == 2


def test_inactive_flag_does_not_affect_any_fields():
    """HIGHLIGHTED is not in the state, so its border colour must not apply."""
    style_overrides = {
        State.DISABLED: StyleOverride(background_colour=RED),
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
    }
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED)

    assert style.border_colour == BLACK


def test_multiple_flags_change_separate_fields_set_in_style_override():
    style_overrides = {
        State.DISABLED: StyleOverride(background_colour=RED),
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
    }
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.background_colour == RED
    assert style.border_colour == BLUE


def test_later_override_wins_when_multiple_flags_change_same_field():
    """Later means later in ``style_overrides``, not later in ``State``."""
    style_overrides = {
        State.DISABLED: StyleOverride(background_colour=RED),
        State.HIGHLIGHTED: StyleOverride(background_colour=BLUE),
    }
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.background_colour == BLUE


# endregion


# region --- Structure ---------------------------------------------------------


def test_style_override_fields_are_subset_of_style():
    style_field_names = []
    for field in fields(Style):
        style_field_names.append(field.name)

    for field in fields(StyleOverride):
        assert field.name in style_field_names


@pytest.mark.parametrize("state", State.__members__.values())
def test_default_theme_provides_style_for_every_state(state):
    assert isinstance(DEFAULT_THEME.style_for(state), Style)


# endregion
