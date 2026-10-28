import pytest

from puigame.core.anchor import Anchor
from puigame.core.ui_root import UIRoot
from puigame.themes.theme import DEFAULT_THEME
from puigame.widgets.container import Container

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)

# endregion


# region --- Construction -----------------------------------------------------


def test_image_is_size_zero(ui_root: UIRoot):
    container = Container(ui_root, size=(5, 10))

    assert container.image.get_size() == (0, 0)


def test_rect_has_given_size(ui_root: UIRoot):
    container = Container(ui_root, size=(5, 10))

    assert container.rect.size == (5, 10)


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("consumes_clicks", True),
    ],
    ids=["offset", "enabled", "visible", "consumes_clicks"],
)
def test_forwards_public_arguments(ui_root: UIRoot, argument, value):
    container = Container(ui_root, size=ANY_SIZE, **{argument: value})

    assert getattr(container, argument) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=DEFAULT_THEME)
    container = Container(
        ui_root,
        size=(3, 5),
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert container.rect.topleft == (-5, 21)


def test_consumes_clicks_false_by_default(ui_root: UIRoot):
    container = Container(ui_root, size=ANY_SIZE)

    assert not container.consumes_clicks


# endregion
