import pytest

from puigame import (
    Anchor,
    BundledTypeface,
    FadeProfile,
    NoSkin,
    Panel,
    Style,
    TextHorizontalExtent,
    Theme,
)
from puigame._ui.ui_root import UIRoot
from stubs import FixedLayer

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)
ANY_POS = (3, 5)
ANY_SKIN = NoSkin()

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


def test_image_comes_from_skin(ui_root: UIRoot):
    panel = Panel(
        ui_root,
        size=ANY_SIZE,
        skin=FixedLayer(size=(2, 3), colour=BLUE, pos=(10, 12)),
    )

    assert panel.image.size == (2, 3)
    assert panel.image_pos == (10, 12)


def test_rect_has_given_size(ui_root: UIRoot):
    panel = Panel(
        ui_root,
        size=(4, 5),
        skin=FixedLayer(size=ANY_SIZE, colour=BLUE, pos=ANY_POS),
    )

    assert panel.rect.size == (4, 5)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("consumes_clicks", False),
    ],
)
def test_forwards_arguments_stored_as_attributes(ui_root: UIRoot, field_name, value):
    panel = Panel(ui_root, size=ANY_SIZE, skin=ANY_SKIN, **{field_name: value})

    assert getattr(panel, field_name) == value


def test_forwards_placement_field_names():
    ui_root = UIRoot(size=(20, 30), theme=ANY_THEME)
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
