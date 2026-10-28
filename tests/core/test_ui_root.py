from dataclasses import replace

import pytest

from puigame.components.skin import NoSkin
from puigame.core.ui_root import UIRoot
from puigame.themes.theme import DEFAULT_THEME, Theme

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)
ANY_SKIN = NoSkin()

BLUE = (0, 0, 255, 255)

# endregion


# region --- Construction -----------------------------------------------------


def test_parent_is_none(ui_root: UIRoot):
    assert ui_root.parent is None


def test_rect_has_given_size():
    ui_root = UIRoot(size=(10, 20), theme=DEFAULT_THEME)

    assert ui_root.rect.size == (10, 20)


def test_root_position_is_origin():
    ui_root = UIRoot(size=ANY_SIZE, theme=DEFAULT_THEME)

    assert ui_root.rect.topleft == (0, 0)


def test_theme_is_given_theme():
    theme = Theme(
        base_style=replace(DEFAULT_THEME.base_style, body_colour=BLUE),
        style_overrides={},
    )
    ui_root = UIRoot(size=ANY_SIZE, theme=theme)

    assert ui_root.theme is theme


def test_image_is_size_zero():
    ui_root = UIRoot(size=(10, 20), theme=DEFAULT_THEME)

    assert ui_root.image.get_size() == (0, 0)


def test_negative_size_raises():
    with pytest.raises(ValueError):
        UIRoot(size=(-1, 0), theme=DEFAULT_THEME)


def test_consumes_clicks_false_by_default(ui_root: UIRoot):
    assert not ui_root.consumes_clicks


# endregion


# region --- kill -------------------------------------------------------------


def test_kill_raises(ui_root: UIRoot):
    with pytest.raises(TypeError):
        ui_root.kill()


# endregion


# region --- Layout -----------------------------------------------------------


def test_given_offset_is_floored():
    ui_root = UIRoot(size=ANY_SIZE, theme=DEFAULT_THEME)

    assert ui_root.rect.topleft == (0, 0)

    ui_root.offset = (-1.4, 2.5)
    # white-box: nothing public runs the layout pass until UI does
    ui_root._place_tree()

    assert ui_root.rect.topleft == (-2, 2)


# endregion
