import pytest

from puigame import (
    UI,
    Anchor,
    BundledTypeface,
    Container,
    FadeProfile,
    Panel,
    Style,
    TextAlign,
    TextHorizontalExtent,
    Theme,
)

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
    text_align=TextAlign.LEFT,
    text_horizontal_extent=TextHorizontalExtent.INK,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

ANY_THEME = Theme(base_style=ANY_STYLE, style_overrides={})

# endregion


# region --- Construction -----------------------------------------------------


def test_image_is_zero_size(ui: UI):
    container = Container(ui, size=(5, 10))

    ui.update()

    assert container.image.size == (0, 0)


def test_rect_has_given_size(ui: UI):
    container = Container(ui, size=(5, 10))

    assert container.rect.size == (5, 10)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("hit_testable", True),
    ],
)
def test_forwards_arguments_stored_as_attributes(ui: UI, field_name, value):
    container = Container(ui, size=ANY_SIZE, **{field_name: value})

    assert getattr(container, field_name) == value


def test_forwards_placement_arguments():
    ui = UI(size=(20, 30), theme=ANY_THEME)
    container = Container(
        ui,
        size=(3, 5),
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert container.rect.topleft == (-5, 21)


def test_hit_testable_false_by_default(ui: UI):
    container = Container(ui, size=ANY_SIZE)

    assert not container.hit_testable


def test_is_a_panel(ui: UI):
    container = Container(ui, size=ANY_SIZE)

    assert isinstance(container, Panel)


# endregion


# region --- Fitted size ------------------------------------------------------


def test_size_defaults_to_fitting_children(ui: UI):
    container = Container(ui)
    Container(container, size=(10, 4))
    Container(container, size=(6, 8))

    ui.update()

    assert container.rect.size == (10, 8)


@pytest.mark.parametrize(
    ("size", "expected_size"),
    [((None, 25), (10, 25)), ((30, None), (30, 8))],
    ids=["width fitted", "height fitted"],
)
def test_none_axis_fits_children(ui: UI, size, expected_size):
    container = Container(ui, size=size)
    Container(container, size=(10, 8))

    ui.update()

    assert container.rect.size == expected_size


# endregion
