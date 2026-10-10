from dataclasses import fields, replace

import pytest

from puigame.core.anchor import Anchor
from puigame.core.state import State
from puigame.themes.theme import (
    DEFAULT_THEME,
    FadeProfile,
    Style,
    StyleOverride,
    Theme,
)

# region --- Constants --------------------------------------------------------


RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

BASE_STYLE = Style(
    body_colour=WHITE,
    border_colour=BLACK,
    border_thickness_px=2,
    corner_radius_px=2,
    halo_colour=(0, 0, 0, 0),
    halo_fade_profile=FadeProfile.SOLID,
    halo_thickness_px=0,
    swell_px=0,
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
    State.DISABLED: StyleOverride(body_colour=RED),
    State.HIGHLIGHTED: StyleOverride(body_colour=BLUE),
}

# endregion


# region --- Style and StyleOverride validation -------------------------------


@pytest.mark.parametrize("swell_px", [-5, 0, 5])
def test_style_swell_px_can_take_any_int(swell_px):
    style = replace(BASE_STYLE, swell_px=swell_px)

    assert style.swell_px == swell_px


@pytest.mark.parametrize("swell_px", [-5, 0, 5])
def test_style_override_swell_px_can_take_any_int(swell_px):
    style_override = StyleOverride(swell_px=swell_px)

    assert style_override.swell_px == swell_px


@pytest.mark.parametrize(
    "field_name",
    ["corner_radius_px", "border_thickness_px", "halo_thickness_px"],
)
def test_style_negative_radius_or_thicknesses_raise(field_name):
    with pytest.raises(ValueError):
        replace(BASE_STYLE, **{field_name: -5})


def test_style_override_negative_halo_thickness_raises():
    with pytest.raises(ValueError):
        StyleOverride(halo_thickness_px=-5)


@pytest.mark.parametrize(
    "field_name",
    ["corner_radius_px", "border_thickness_px", "halo_thickness_px"],
)
def test_style_radius_or_thicknesses_can_be_zero(field_name):
    style = replace(BASE_STYLE, **{field_name: 0})

    assert getattr(style, field_name) == 0


def test_style_override_halo_thickness_can_be_zero():
    style_override = StyleOverride(halo_thickness_px=0)

    assert style_override.halo_thickness_px == 0


@pytest.mark.parametrize("text_font_size", [0, -5])
def test_style_non_positive_font_size_raises(text_font_size):
    with pytest.raises(ValueError):
        replace(BASE_STYLE, text_font_size=text_font_size)


# endregion


# region --- Theme.__post_init__ ----------------------------------------------


def test_base_state_in_style_overrides_raises():
    with pytest.raises(ValueError):
        Theme(
            BASE_STYLE,
            {State.BASE: StyleOverride(body_colour=RED)},
        )


def test_combined_state_in_style_overrides_raises():
    with pytest.raises(ValueError):
        Theme(
            BASE_STYLE,
            {State.DISABLED | State.HIGHLIGHTED: StyleOverride(body_colour=RED)},
        )


def test_stored_style_overrides_copy_is_same_as_given():
    theme = Theme(BASE_STYLE, ANY_STYLE_OVERRIDES)

    assert theme.style_overrides == ANY_STYLE_OVERRIDES


def test_assigning_to_theme_style_overrides_raises():
    theme = Theme(
        BASE_STYLE,
        {
            State.DISABLED: StyleOverride(body_colour=RED),
            State.HIGHLIGHTED: StyleOverride(body_colour=BLUE),
        },
    )

    with pytest.raises(TypeError):
        theme.style_overrides[State.CHECKED] = StyleOverride(body_colour=RED)  # pyright: ignore[reportIndexIssue]


def test_changing_source_style_overrides_dict_does_not_affect_theme():
    source_style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(BASE_STYLE, source_style_overrides)

    source_style_overrides[State.DISABLED] = StyleOverride(body_colour=BLACK)

    assert theme.style_overrides[State.DISABLED].body_colour == RED


# endregion


# region --- Theme.style_for --------------------------------------------------


def test_style_for_base_state_returns_base_style():
    theme = Theme(BASE_STYLE, ANY_STYLE_OVERRIDES)

    style = theme.style_for(State.BASE)

    assert style is BASE_STYLE


def test_single_flag_changes_field_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED)

    assert style.body_colour == RED


def test_single_flag_does_not_change_fields_not_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED)

    assert style.border_colour == BLACK
    assert style.border_thickness_px == 2


def test_inactive_flag_does_not_affect_any_fields():
    """HIGHLIGHTED is not in the state, so its border colour must not apply."""
    style_overrides = {
        State.DISABLED: StyleOverride(body_colour=RED),
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
    }
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED)

    assert style.border_colour == BLACK


def test_flag_not_in_theme_is_ignored():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.body_colour == RED  # disabled still applies
    assert style.border_colour == BLACK  # highlighted request has not changed others


def test_multiple_flags_change_separate_fields_set_in_style_override():
    style_overrides = {
        State.DISABLED: StyleOverride(body_colour=RED),
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
    }
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.body_colour == RED
    assert style.border_colour == BLUE


def test_later_override_wins_when_multiple_flags_change_same_field():
    """Later means later in ``style_overrides``, not later in ``State``."""
    style_overrides = {
        State.DISABLED: StyleOverride(body_colour=RED),
        State.HIGHLIGHTED: StyleOverride(body_colour=BLUE),
    }
    theme = Theme(BASE_STYLE, style_overrides)

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.body_colour == BLUE


# endregion


# region --- Structure --------------------------------------------------------


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
