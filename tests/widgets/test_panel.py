from dataclasses import replace

import pytest

from puigame import (
    UI,
    Anchor,
    BundledTypeface,
    Container,
    FadeProfile,
    NoSkin,
    Panel,
    Style,
    TextAlign,
    TextHorizontalExtent,
    Theme,
    VBox,
)
from stubs import BodyColourLayer, FixedLayer

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
    box_gap=0,
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


def test_image_comes_from_skin(ui: UI):
    panel = Panel(
        ui,
        size=ANY_SIZE,
        skin=FixedLayer(size=(2, 3), colour=BLUE, pos=(10, 12)),
    )

    ui.update()

    assert panel.image.size == (2, 3)
    assert panel.image_pos == (10, 12)


def test_rect_has_given_size(ui: UI):
    panel = Panel(
        ui,
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
        ("hit_testable", False),
    ],
)
def test_forwards_arguments_stored_as_attributes(ui: UI, field_name, value):
    panel = Panel(ui, size=ANY_SIZE, skin=ANY_SKIN, **{field_name: value})

    assert getattr(panel, field_name) == value


def test_forwards_placement_field_names():
    ui = UI(size=(20, 30), theme=ANY_THEME)
    panel = Panel(
        ui,
        size=(3, 5),
        skin=ANY_SKIN,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert panel.rect.topleft == (-5, 21)


def test_hit_testable_true_by_default(ui: UI):
    panel = Panel(ui, size=ANY_SIZE, skin=ANY_SKIN)

    assert panel.hit_testable


# endregion


# region --- Fitted size ------------------------------------------------------


def test_size_defaults_to_fitting_children(ui: UI):
    panel = Panel(ui, skin=ANY_SKIN)
    Container(panel, size=(10, 4))
    Container(panel, size=(6, 8))

    ui.update()

    assert panel.rect.size == (10, 8)


def test_fitted_panel_with_no_children_is_zero_size(ui: UI):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)

    ui.update()

    assert panel.rect.size == (0, 0)


def test_fitted_panel_is_zero_size_before_first_update(ui: UI):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 8))

    assert panel.rect.size == (0, 0)


def test_fitted_panel_is_as_big_as_largest_child_on_each_axis(ui: UI):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 4))
    Container(panel, size=(6, 8))

    ui.update()

    assert panel.rect.size == (10, 8)


@pytest.mark.parametrize(
    ("size", "expected_size"),
    [
        ((None, 25.7), (10, 25)),
        ((30.9, None), (30, 8)),
    ],
    ids=["width fitted", "height fitted"],
)
def test_fixed_axis_beside_fitted_axis_keeps_its_size_rounded_down(
    ui: UI, size, expected_size
):
    panel = Panel(ui, size=size, skin=ANY_SKIN)
    Container(panel, size=(10, 8))

    ui.update()

    assert panel.rect.size == expected_size


@pytest.mark.parametrize(
    ("anchor", "parent_anchor"),
    [
        (Anchor.TOP_LEFT, Anchor.TOP_RIGHT),
        (Anchor.TOP_LEFT, Anchor.BOTTOM_LEFT),
        (Anchor.TOP_LEFT, Anchor.BOTTOM_RIGHT),
    ],
    ids=["differs across", "differs down", "differs on both axes"],
)
def test_child_whose_anchor_differs_from_its_parent_anchor_is_not_counted(
    ui: UI, anchor, parent_anchor
):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 8))
    Container(panel, size=(40, 30), anchor=anchor, parent_anchor=parent_anchor)

    ui.update()

    assert panel.rect.size == (10, 8)


@pytest.mark.parametrize(
    "parent_anchor",
    [Anchor.TOP_LEFT, None],
    ids=["given", "defaulted"],
)
def test_child_whose_anchor_matches_its_parent_anchor_is_counted(ui: UI, parent_anchor):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 8))
    Container(panel, size=(40, 30), anchor=Anchor.TOP_LEFT, parent_anchor=parent_anchor)

    ui.update()

    assert panel.rect.size == (40, 30)


@pytest.mark.parametrize(
    ("margin", "expected_size"),
    [
        ((2, 3), (14, 14)),
        ((1.25, 0.75), (12, 9)),
        ((-2, -1), (6, 6)),
        ((-6, -5), (0, 0)),
    ],
    ids=["positive", "fractional rounded down", "negative", "negative floored at 0"],
)
def test_child_margin_counts_on_both_sides(ui: UI, margin, expected_size):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 8), margin=margin)

    ui.update()

    assert panel.rect.size == expected_size


def test_hidden_child_is_not_counted(ui: UI):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 8))
    Container(panel, size=(40, 30), visible=False)

    ui.update()

    assert panel.rect.size == (10, 8)


def test_hiding_only_child_shrinks_panel_to_zero_at_next_update(ui: UI):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    child = Container(panel, size=(10, 8))
    ui.update()

    child.visible = False
    ui.update()

    assert panel.rect.size == (0, 0)


def test_new_child_grows_panel_at_next_update(ui: UI):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 4))
    ui.update()

    Container(panel, size=(6, 8))
    ui.update()

    assert panel.rect.size == (10, 8)


def test_killed_child_frees_its_size_at_next_update(ui: UI):
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN)
    Container(panel, size=(10, 4))
    child = Container(panel, size=(6, 8))
    ui.update()

    child.kill()
    ui.update()

    assert panel.rect.size == (10, 4)


def test_fitted_panel_fits_nested_vbox_in_one_update():
    theme = Theme(base_style=replace(ANY_STYLE, box_gap=3), style_overrides={})
    ui = UI(size=(300, 200), theme=theme)
    panel = Panel(ui, size=(200, None), skin=ANY_SKIN)
    vbox = VBox(panel)
    Container(vbox, size=(10, 4))
    Container(vbox, size=(6, 8))

    ui.update()

    assert panel.rect.size == (200, 15)


def test_fitted_panel_is_placed_by_its_new_size_in_the_same_update():
    ui = UI(size=(100, 80), theme=ANY_THEME)
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN, anchor=Anchor.CENTRE)
    Container(panel, size=(10, 4))

    ui.update()

    assert panel.rect.topleft == (45, 38)


def test_children_are_placed_against_fitted_size_in_the_same_update():
    ui = UI(size=(100, 80), theme=ANY_THEME)
    panel = Panel(ui, size=(None, None), skin=ANY_SKIN, anchor=Anchor.CENTRE)
    Container(panel, size=(10, 8))
    hanging_child = Container(
        panel, size=(4, 6), anchor=Anchor.TOP_LEFT, parent_anchor=Anchor.TOP_RIGHT
    )

    ui.update()

    assert hanging_child.rect.topleft == (55, 36)


def test_image_is_rebuilt_when_fitted_size_changes(ui: UI):
    panel = Panel(ui, size=(None, None), skin=BodyColourLayer())
    Container(panel, size=(10, 8))

    ui.update()

    assert panel.image.size == (10, 8)


def test_image_is_kept_when_fitted_size_does_not_change(ui: UI):
    panel = Panel(ui, size=(None, None), skin=BodyColourLayer())
    Container(panel, size=(10, 8))
    ui.update()
    image_after_first_update = panel.image

    ui.update()

    assert panel.image is image_after_first_update


# endregion
