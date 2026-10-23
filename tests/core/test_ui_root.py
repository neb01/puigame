from dataclasses import replace

import pytest

from puigame.components.skin import NoSkin
from puigame.core.anchor import Anchor
from puigame.core.ui_root import UIRoot
from puigame.core.widget import Widget
from puigame.themes.theme import DEFAULT_THEME, Theme

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)
ANY_POINT = (3, 5)
ANY_SKIN = NoSkin()

BLUE = (0, 0, 255, 255)

# endregion


# region --- Construction -----------------------------------------------------


def test_parent_is_none(ui_root: UIRoot):
    assert ui_root.parent is None


def test_rect_has_given_size():
    ui_root = UIRoot((10, 20), DEFAULT_THEME)

    assert ui_root.rect.size == (10, 20)


def rest_root_position_is_origin():
    ui_root = UIRoot(ANY_SIZE, DEFAULT_THEME)

    assert ui_root.rect.topleft == (0, 0)


def test_theme_is_given_theme():
    theme = Theme(replace(DEFAULT_THEME.base_style, body_colour=BLUE), {})
    ui_root = UIRoot(ANY_SIZE, theme)

    assert ui_root.theme is theme


def test_image_is_size_zero():
    ui_root = UIRoot((10, 20), DEFAULT_THEME)

    assert ui_root.image.get_size() == (0, 0)


def test_negative_size_raises():
    with pytest.raises(ValueError):
        UIRoot((-1, 0), DEFAULT_THEME)


# endregion


# region --- kill -------------------------------------------------------------


def test_kill_raises(ui_root: UIRoot):
    with pytest.raises(TypeError):
        ui_root.kill()


# endregion


# region --- Layout -----------------------------------------------------------


def test_offset_change_passes_down_to_descendants():
    ui_root = UIRoot((10, 20), DEFAULT_THEME)
    parent = Widget(
        ui_root,
        (3, 5),
        ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(1, 3),
    )

    child = Widget(
        parent,
        (1, 2),
        ANY_SKIN,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_RIGHT,
        margin=(0, 0),
        offset=(-1, 0),
    )

    assert parent.rect.topleft == (1, 3)
    assert child.rect.topleft == (2, 6)

    ui_root.offset = (1, -2)
    # white-box: nothing public runs the layout pass until UI does
    ui_root._place_tree()

    assert parent.rect.topleft == (2, 1)
    assert child.rect.topleft == (3, 4)


def test_given_offset_is_floored():
    ui_root = UIRoot(ANY_SIZE, DEFAULT_THEME)

    assert ui_root.rect.topleft == (0, 0)

    ui_root.offset = (-1.4, 2.5)
    # white-box: nothing public runs the layout pass until UI does
    ui_root._place_tree()

    assert ui_root.rect.topleft == (-2, 2)


# endregion
