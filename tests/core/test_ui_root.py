from dataclasses import replace

import pytest

from puigame.core.ui_root import UIRoot
from puigame.themes.theme import DEFAULT_THEME, Theme

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)
ANY_POINT = (3, 5)

BLUE = (0, 0, 255, 255)

# endregion


# region --- Construction -----------------------------------------------------


def test_parent_is_none(ui_root: UIRoot):
    assert ui_root.parent is None


def test_rect_has_given_size_and_position():
    ui_root = UIRoot((10, 20), (4, 5), DEFAULT_THEME)

    assert ui_root.rect.size == (10, 20)
    assert ui_root.rect.topleft == (4, 5)


def test_theme_is_given_theme():
    theme = Theme(replace(DEFAULT_THEME.base_style, body_colour=BLUE), {})
    ui_root = UIRoot(ANY_SIZE, ANY_POINT, theme)

    assert ui_root.theme is theme


def test_image_is_size_zero():
    ui_root = UIRoot((10, 20), ANY_POINT, DEFAULT_THEME)

    assert ui_root.image.get_size() == (0, 0)


def test_negative_size_raises():
    with pytest.raises(ValueError):
        UIRoot((-1, 0), ANY_POINT, DEFAULT_THEME)


# endregion


# region --- kill -------------------------------------------------------------


def test_kill_raises(ui_root: UIRoot):
    with pytest.raises(TypeError):
        ui_root.kill()


# endregion
