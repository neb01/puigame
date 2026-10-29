import pytest

from puigame._components.skin import NoSkin
from puigame._styling.theme import DEFAULT_THEME
from puigame._widgets.panel import Panel
from puigame.core.anchor import Anchor
from puigame.core.ui_root import UIRoot
from stubs import FixedLayer

# region --- Constants --------------------------------------------------------

BLUE = (0, 0, 255, 255)

ANY_SIZE = (10, 10)
ANY_POS = (3, 5)
ANY_SKIN = NoSkin()

# endregion


# region --- Construction -----------------------------------------------------


def test_image_comes_from_skin(ui_root: UIRoot):
    panel = Panel(
        ui_root,
        size=ANY_SIZE,
        skin=FixedLayer(size=(2, 3), colour=BLUE, pos=(10, 12)),
    )

    assert panel.image.get_size() == (2, 3)
    assert panel.image_pos == (10, 12)


def test_rect_has_given_size(ui_root: UIRoot):
    panel = Panel(
        ui_root,
        size=(4, 5),
        skin=FixedLayer(size=ANY_SIZE, colour=BLUE, pos=ANY_POS),
    )

    assert panel.rect.size == (4, 5)


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("consumes_clicks", False),
    ],
    ids=["offset", "enabled", "visible", "consumes_clicks"],
)
def test_forwards_public_arguments(ui_root: UIRoot, argument, value):
    panel = Panel(ui_root, size=ANY_SIZE, skin=ANY_SKIN, **{argument: value})

    assert getattr(panel, argument) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=DEFAULT_THEME)
    panel = Panel(
        ui_root,
        size=(3, 5),
        skin=ANY_SKIN,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert panel.rect.topleft == (-5, 21)


def test_consumes_clicks_true_by_default(ui_root: UIRoot):
    panel = Panel(ui_root, size=ANY_SIZE, skin=ANY_SKIN)

    assert panel.consumes_clicks


# endregion
