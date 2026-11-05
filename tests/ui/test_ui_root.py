from dataclasses import replace

import pytest

from puigame import (
    Anchor,
    BundledTypeface,
    FadeProfile,
    Style,
    TextHorizontalExtent,
    Theme,
)
from puigame._ui.ui_root import UIRoot

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)

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
    text_horizontal_extent=TextHorizontalExtent.INK,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

ANY_THEME = Theme(base_style=ANY_STYLE, style_overrides={})

# endregion


# region --- Construction -----------------------------------------------------


def test_parent_is_none(ui_root: UIRoot):
    assert ui_root.parent is None


def test_rect_has_given_size():
    ui_root = UIRoot(size=(10, 20), theme=ANY_THEME)

    assert ui_root.rect.size == (10, 20)


def test_root_position_is_origin():
    ui_root = UIRoot(size=ANY_SIZE, theme=ANY_THEME)

    assert ui_root.rect.topleft == (0, 0)


def test_theme_is_given_theme():
    theme = Theme(
        base_style=replace(ANY_STYLE, body_colour=BLUE),
        style_overrides={},
    )
    ui_root = UIRoot(size=ANY_SIZE, theme=theme)

    assert ui_root.theme is theme


def test_image_is_zero_size():
    ui_root = UIRoot(size=(10, 20), theme=ANY_THEME)

    assert ui_root.image.size == (0, 0)


def test_constructor_with_negative_size_raises():
    with pytest.raises(ValueError):
        UIRoot(size=(-1, 0), theme=ANY_THEME)


def test_consumes_clicks_false_by_default(ui_root: UIRoot):
    assert not ui_root.consumes_clicks


# endregion


# region --- kill() -----------------------------------------------------------


def test_kill_raises(ui_root: UIRoot):
    with pytest.raises(TypeError):
        ui_root.kill()


# endregion


# region --- Layout -----------------------------------------------------------


def test_given_offset_is_floored():
    ui_root = UIRoot(size=ANY_SIZE, theme=ANY_THEME)

    assert ui_root.rect.topleft == (0, 0)

    ui_root.offset = (-1.4, 2.5)
    # white-box: nothing public runs the layout pass until UI does
    ui_root._place_tree()

    assert ui_root.rect.topleft == (-2, 2)


# endregion
