from dataclasses import replace

import pytest

from puigame._layout.anchor import Anchor
from puigame._styling.style import BundledTypeface, FadeProfile, Style, StyleOverride
from puigame._styling.theme import DEFAULT_THEME, Theme
from puigame._widgets.state import State

# region --- Constants --------------------------------------------------------

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

ANY_STYLE = Style(
    body_colour=WHITE,
    border_colour=BLACK,
    border_thickness_px=2,
    corner_radius_px=2,
    halo_colour=(0, 0, 0, 0),
    halo_fade_profile=FadeProfile.SOLID,
    halo_thickness_px=0,
    swell_px=0,
    text_colour=BLACK,
    text_typeface=BundledTypeface.PYGAME_DEFAULT,
    text_font_size=12,
    text_anchor=Anchor.CENTRE,
    text_parent_anchor=Anchor.CENTRE,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

ANY_STYLE_OVERRIDES = {
    State.DISABLED: StyleOverride(body_colour=RED),
    State.HIGHLIGHTED: StyleOverride(body_colour=BLUE),
}

# endregion


# region --- Theme.__post_init__ ----------------------------------------------


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
                State.DISABLED | State.HIGHLIGHTED: StyleOverride(body_colour=RED),
            },
        )


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


# region --- Theme.style_for --------------------------------------------------


def test_style_for_base_state_returns_base_style():
    theme = Theme(base_style=ANY_STYLE, style_overrides=ANY_STYLE_OVERRIDES)

    style = theme.style_for(State.BASE)

    assert style is ANY_STYLE


def test_single_flag_changes_field_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=BLUE),
        style_overrides=style_overrides,
    )

    style = theme.style_for(State.DISABLED)

    assert style.body_colour == RED


def test_single_flag_does_not_change_fields_not_set_in_style_override():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(
        base_style=replace(ANY_STYLE, border_colour=BLACK, border_thickness_px=2),
        style_overrides=style_overrides,
    )

    style = theme.style_for(State.DISABLED)

    assert style.border_colour == BLACK
    assert style.border_thickness_px == 2


def test_inactive_flag_does_not_affect_any_fields():
    """HIGHLIGHTED is not in the state, so its border colour must not apply."""
    style_overrides = {
        State.DISABLED: StyleOverride(body_colour=RED),
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
    }
    theme = Theme(
        base_style=replace(ANY_STYLE, border_colour=BLACK),
        style_overrides=style_overrides,
    )

    style = theme.style_for(State.DISABLED)

    assert style.border_colour == BLACK


def test_flag_not_in_theme_is_ignored():
    style_overrides = {State.DISABLED: StyleOverride(body_colour=RED)}
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=WHITE, border_colour=BLACK),
        style_overrides=style_overrides,
    )

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.body_colour == RED  # disabled still applies
    assert style.border_colour == BLACK  # highlighted request has not changed others


def test_multiple_flags_change_separate_fields_set_in_style_override():
    style_overrides = {
        State.DISABLED: StyleOverride(body_colour=RED),
        State.HIGHLIGHTED: StyleOverride(border_colour=BLUE),
    }
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=WHITE, border_colour=BLACK),
        style_overrides=style_overrides,
    )

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.body_colour == RED
    assert style.border_colour == BLUE


def test_later_override_wins_when_multiple_flags_change_same_field():
    """Later means later in ``style_overrides``, not later in ``State``."""
    style_overrides = {
        State.DISABLED: StyleOverride(body_colour=RED),
        State.HIGHLIGHTED: StyleOverride(body_colour=BLUE),
    }
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=WHITE),
        style_overrides=style_overrides,
    )

    style = theme.style_for(State.DISABLED | State.HIGHLIGHTED)

    assert style.body_colour == BLUE


# endregion


# region --- Structure --------------------------------------------------------


# iterating State itself skips BASE, which has no bits set
@pytest.mark.parametrize("state", State.__members__.values())
def test_default_theme_provides_style_for_every_state(state):
    assert isinstance(DEFAULT_THEME.style_for(state), Style)


# endregion
