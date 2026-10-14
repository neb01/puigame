import pytest

from puigame.core.anchor import Anchor
from puigame.core.ui_root import UIRoot
from puigame.widgets.container import Container

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)

# endregion


# region --- Construction -----------------------------------------------------


def test_image_is_size_zero(ui_root: UIRoot):
    container = Container(ui_root, (5, 10))

    assert container.image.get_size() == (0, 0)


def test_rect_has_given_size(ui_root: UIRoot):
    container = Container(ui_root, (5, 10))

    assert container.rect.size == (5, 10)


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
    container = Container(ui_root, ANY_SIZE, **{argument: value})

    assert getattr(container, argument) == value


# endregion
