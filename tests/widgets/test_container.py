import pytest

from puigame import (
    Anchor,
    BundledTypeface,
    Container,
    FadeProfile,
    Style,
    TextHorizontalExtent,
    Theme,
)
from puigame._ui.ui_root import UIRoot

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)

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


def test_image_is_zero_size(ui_root: UIRoot):
    container = Container(ui_root, size=(5, 10))

    assert container.image.size == (0, 0)


def test_rect_has_given_size(ui_root: UIRoot):
    container = Container(ui_root, size=(5, 10))

    assert container.rect.size == (5, 10)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("consumes_clicks", True),
    ],
)
def test_forwards_arguments_stored_as_attributes(ui_root: UIRoot, field_name, value):
    container = Container(ui_root, size=ANY_SIZE, **{field_name: value})

    assert getattr(container, field_name) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=ANY_THEME)
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
