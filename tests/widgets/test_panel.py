import pytest

from puigame.components.skin import NoSkin
from puigame.core.anchor import Anchor
from puigame.core.ui_root import UIRoot
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
        ("anchor", Anchor.TOP_RIGHT),
        ("parent_anchor", Anchor.MID_BOTTOM),
        ("margin", (2, 4)),
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
    ],
    ids=["anchor", "parent anchor", "margin", "offset", "enabled", "visible"],
)
def test_forwards_keyword_arguments(ui_root: UIRoot, argument, value):
    panel = Panel(ui_root, ANY_SIZE, ANY_SKIN, **{argument: value})

    assert getattr(panel, argument) == value


# endregion
