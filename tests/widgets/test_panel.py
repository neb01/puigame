import pytest

from puigame.components.skin import NoSkin
from puigame.core.anchor import Anchor
from puigame.core.ui_root import UIRoot
from puigame.themes.theme import DEFAULT_THEME
from puigame.widgets.panel import Panel
from stubs import FixedLayer

# region --- Constants --------------------------------------------------------

BLUE = (0, 0, 255, 255)

ANY_SIZE = (10, 10)
ANY_POINT = (3, 5)
ANY_SKIN = NoSkin()

# endregion


# region --- Construction -----------------------------------------------------


def test_image_comes_from_skin(ui_root: UIRoot):
    panel = Panel(ui_root, ANY_SIZE, FixedLayer((2, 3), BLUE, (10, 12)))

    assert panel.image.get_size() == (2, 3)
    assert panel.image_pos == (10, 12)


def test_rect_has_given_size(ui_root: UIRoot):
    panel = Panel(ui_root, (4, 5), FixedLayer(ANY_SIZE, BLUE, ANY_POINT))

    assert panel.rect.size == (4, 5)


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
    ],
    ids=["offset", "enabled", "visible"],
)
def test_forwards_public_keyword_arguments(ui_root: UIRoot, argument, value):
    panel = Panel(ui_root, ANY_SIZE, ANY_SKIN, **{argument: value})

    assert getattr(panel, argument) == value


def test_forwards_private_keyword_arguments():
    ui_root = UIRoot((20, 30), DEFAULT_THEME)
    panel = Panel(
        ui_root,
        (3, 5),
        ANY_SKIN,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert panel.rect.topleft == (-5, 21)


# endregion
