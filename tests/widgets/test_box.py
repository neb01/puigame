from dataclasses import replace

import pytest

from mouse_helpers import left_press
from puigame import (
    UI,
    Anchor,
    BoxAlign,
    BundledTypeface,
    Container,
    FadeProfile,
    HBox,
    NoSkin,
    Style,
    TextAlign,
    TextHorizontalExtent,
    Theme,
    ToggleButton,
    ToggleGroup,
    VBox,
)
from puigame._widgets.box import Axis, _to_xy_order

# region --- Constants --------------------------------------------------------

UI_SIZE = (300, 200)

ANY_SIZE = (9, 10)
ANY_SKIN = NoSkin()

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


# region --- Helpers ----------------------------------------------------------


def make_ui(*, box_gap: int) -> UI:
    """Return a UI of ``UI_SIZE`` whose theme has the given ``box_gap``."""
    theme = Theme(base_style=replace(ANY_STYLE, box_gap=box_gap), style_overrides={})

    return UI(size=UI_SIZE, theme=theme)


# endregion


# region --- Construction -----------------------------------------------------


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_image_is_zero_size(ui: UI, box_class):
    box = box_class(ui)
    Container(box, size=(5, 10))

    ui.update()

    assert box.image.size == (0, 0)


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_rect_is_zero_size_before_first_update(ui: UI, box_class):
    box = box_class(ui)
    Container(box, size=(5, 10))

    assert box.rect.size == (0, 0)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("hit_testable", True),
    ],
)
@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_forwards_arguments_stored_as_attributes(ui: UI, box_class, field_name, value):
    box = box_class(ui, **{field_name: value})

    assert getattr(box, field_name) == value


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_forwards_placement_arguments(box_class):
    ui = UI(size=(20, 30), theme=ANY_THEME)
    box = box_class(
        ui,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )
    Container(box, size=(3, 5))

    ui.update()

    assert box.rect.topleft == (-5, 21)


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_hit_testable_false_by_default(ui: UI, box_class):
    box = box_class(ui)

    assert not box.hit_testable


# endregion


# region --- Validation: children ---------------------------------------------


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("anchor", Anchor.CENTRE),
        ("parent_anchor", Anchor.CENTRE),
        ("parent_anchor", None),
        ("margin", (0, 0)),
        ("offset", (3, 5)),
    ],
)
@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_child_can_take_default_placement_arguments_and_any_offset(
    ui: UI,
    box_class,
    field_name,
    value,
):
    box = box_class(ui)

    container = Container(box, size=ANY_SIZE, **{field_name: value})

    assert box.children == (container,)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("anchor", Anchor.TOP_LEFT),
        ("parent_anchor", Anchor.TOP_LEFT),
        ("margin", (3, 5)),
    ],
)
@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_child_constructor_with_non_default_placement_argument_raises(
    ui: UI,
    box_class,
    field_name,
    value,
):
    box = box_class(ui)

    with pytest.raises(ValueError):
        Container(box, size=ANY_SIZE, **{field_name: value})

    assert box.children == ()


def test_refused_toggle_button_does_not_join_its_group(ui: UI):
    box = VBox(ui)
    toggle_group = ToggleGroup()

    with pytest.raises(ValueError):
        ToggleButton(
            box,
            size=ANY_SIZE,
            skin=ANY_SKIN,
            group=toggle_group,
            margin=(3, 5),
        )

    assert toggle_group.buttons == ()


def test_box_can_be_child_of_box(ui: UI):
    vbox = VBox(ui)

    hbox = HBox(vbox)

    assert vbox.children == (hbox,)


# endregion


# region --- Measuring --------------------------------------------------------


def test_vbox_is_as_tall_as_children_and_gaps_and_as_wide_as_widest_child():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui)
    Container(vbox, size=(10, 4))
    Container(vbox, size=(6, 8))
    Container(vbox, size=(8, 2))

    ui.update()

    assert vbox.rect.size == (10, 20)


def test_hbox_is_as_wide_as_children_and_gaps_and_as_tall_as_tallest_child():
    ui = make_ui(box_gap=3)
    hbox = HBox(ui)
    Container(hbox, size=(10, 4))
    Container(hbox, size=(6, 8))
    Container(hbox, size=(8, 2))

    ui.update()

    assert hbox.rect.size == (30, 8)


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_box_with_one_child_has_no_gap(box_class):
    ui = make_ui(box_gap=3)
    box = box_class(ui)
    Container(box, size=(7, 5))

    ui.update()

    assert box.rect.size == (7, 5)


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_box_with_no_children_is_zero_size(box_class):
    ui = make_ui(box_gap=3)
    box = box_class(ui)

    ui.update()

    assert box.rect.size == (0, 0)


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_box_with_only_hidden_children_is_zero_size(box_class):
    ui = make_ui(box_gap=3)
    box = box_class(ui)
    Container(box, size=(7, 5), visible=False)
    Container(box, size=(6, 4), visible=False)

    ui.update()

    assert box.rect.size == (0, 0)


def test_hidden_child_takes_no_space_or_gap():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui)
    Container(vbox, size=(10, 4))
    Container(vbox, size=(16, 8), visible=False)
    Container(vbox, size=(8, 2))

    ui.update()

    assert vbox.rect.size == (10, 9)


def test_nested_boxes_are_measured_inside_out_in_one_update():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui)
    hbox = HBox(vbox)
    Container(hbox, size=(4, 6))
    Container(hbox, size=(5, 2))
    Container(vbox, size=(8, 4))

    ui.update()

    assert hbox.rect.size == (12, 6)
    assert vbox.rect.size == (12, 13)


def test_box_is_placed_by_its_new_size_in_the_same_update():
    ui = UI(size=(100, 80), theme=ANY_THEME)
    vbox = VBox(ui, anchor=Anchor.CENTRE)
    Container(vbox, size=(10, 4))

    ui.update()

    assert vbox.rect.topleft == (45, 38)


# endregion


# region --- Placement --------------------------------------------------------


@pytest.mark.parametrize(
    ("align", "expected_topleft_1", "expected_topleft_2", "expected_topleft_3"),
    [
        (BoxAlign.START, (10, 20), (10, 27), (10, 38)),
        (BoxAlign.CENTRE, (10, 20), (12, 27), (11, 38)),
        (BoxAlign.END, (10, 20), (14, 27), (12, 38)),
    ],
)
def test_vbox_stacks_children_top_to_bottom_aligned_across(
    align,
    expected_topleft_1,
    expected_topleft_2,
    expected_topleft_3,
):
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=align)
    container_1 = Container(vbox, size=(10, 4))
    container_2 = Container(vbox, size=(6, 8))
    container_3 = Container(vbox, size=(8, 2))

    ui.update()

    assert container_1.rect.topleft == expected_topleft_1
    assert container_2.rect.topleft == expected_topleft_2
    assert container_3.rect.topleft == expected_topleft_3


@pytest.mark.parametrize(
    ("align", "expected_topleft_1", "expected_topleft_2", "expected_topleft_3"),
    [
        (BoxAlign.START, (10, 20), (23, 20), (32, 20)),
        (BoxAlign.CENTRE, (10, 22), (23, 20), (32, 23)),
        (BoxAlign.END, (10, 24), (23, 20), (32, 26)),
    ],
)
def test_hbox_stacks_children_left_to_right_aligned_across(
    align,
    expected_topleft_1,
    expected_topleft_2,
    expected_topleft_3,
):
    ui = make_ui(box_gap=3)
    hbox = HBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=align)
    container_1 = Container(hbox, size=(10, 4))
    container_2 = Container(hbox, size=(6, 8))
    container_3 = Container(hbox, size=(8, 2))

    ui.update()

    assert container_1.rect.topleft == expected_topleft_1
    assert container_2.rect.topleft == expected_topleft_2
    assert container_3.rect.topleft == expected_topleft_3


def test_align_defaults_to_centre():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20))
    Container(vbox, size=(10, 4))
    container = Container(vbox, size=(6, 8))

    ui.update()

    assert container.rect.topleft == (12, 27)


@pytest.mark.parametrize(
    ("box_class", "size_1", "size_2", "expected_topleft"),
    [
        (HBox, (2, 5), (2, 2), (15, 21)),
        (VBox, (5, 2), (2, 2), (11, 25)),
    ],
    ids=["HBox", "VBox"],
)
def test_centring_rounds_half_pixel_down(box_class, size_1, size_2, expected_topleft):
    ui = make_ui(box_gap=3)
    box = box_class(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.CENTRE)
    Container(box, size=size_1)
    container = Container(box, size=size_2)

    ui.update()

    assert container.rect.topleft == expected_topleft


def test_child_offset_applies_after_placement():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.START)
    Container(vbox, size=(10, 4))
    container = Container(vbox, size=(6, 8), offset=(2, 5))

    ui.update()

    assert container.rect.topleft == (12, 32)


@pytest.mark.parametrize(
    ("offset", "expected_topleft"),
    [
        ((-0.5, 0), (11, 25)),
        ((0.5, 0), (12, 25)),
        ((0, 0.5), (11, 25)),
    ],
    ids=["negative half x", "positive half x", "positive half y"],
)
def test_centred_child_with_fractional_offset_is_rounded_down_once(
    offset,
    expected_topleft,
):
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.CENTRE)
    Container(vbox, size=(5, 2))
    container = Container(vbox, size=(2, 2), offset=offset)

    ui.update()

    assert container.rect.topleft == expected_topleft


def test_hidden_child_is_placed_at_box_top_left():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.CENTRE)
    Container(vbox, size=(10, 4))
    container = Container(vbox, size=(6, 8), visible=False)

    ui.update()

    assert container.rect.topleft == (10, 20)


def test_children_are_at_box_top_left_before_first_update():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.CENTRE)
    container_1 = Container(vbox, size=(10, 4))
    container_2 = Container(vbox, size=(6, 8))

    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (10, 20)


def test_nested_boxes_place_children_in_one_update():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.CENTRE)
    hbox = HBox(vbox, align=BoxAlign.CENTRE)
    container_1 = Container(hbox, size=(4, 6))
    container_2 = Container(hbox, size=(5, 2))
    container_3 = Container(vbox, size=(8, 4))

    ui.update()

    assert hbox.rect.topleft == (10, 20)
    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (17, 22)
    assert container_3.rect.topleft == (12, 29)


# endregion


# region --- Tree changes -----------------------------------------------------


def test_new_child_is_stacked_after_existing_children_at_next_update():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.START)
    Container(vbox, size=(10, 4))

    ui.update()

    container = Container(vbox, size=(6, 8))
    ui.update()

    assert vbox.rect.size == (10, 15)
    assert container.rect.topleft == (10, 27)


def test_killed_child_frees_its_space_at_next_update():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.START)
    Container(vbox, size=(10, 4))
    middle_container = Container(vbox, size=(16, 8))
    last_container = Container(vbox, size=(8, 2))

    ui.update()

    middle_container.kill()
    ui.update()

    assert vbox.rect.size == (10, 9)
    assert last_container.rect.topleft == (10, 27)


def test_shown_child_takes_its_space_at_next_update():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.START)
    Container(vbox, size=(10, 4))
    middle_container = Container(vbox, size=(16, 8), visible=False)
    last_container = Container(vbox, size=(8, 2))

    ui.update()

    middle_container.visible = True
    ui.update()

    assert vbox.rect.size == (16, 20)
    assert last_container.rect.topleft == (10, 38)


def test_hidden_child_moves_to_box_top_left_at_next_update():
    ui = make_ui(box_gap=3)
    vbox = VBox(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), align=BoxAlign.CENTRE)
    Container(vbox, size=(10, 4))
    container = Container(vbox, size=(6, 8))

    ui.update()

    container.visible = False
    ui.update()

    assert container.rect.topleft == (10, 20)


@pytest.mark.parametrize("box_class", [HBox, VBox], ids=["HBox", "VBox"])
def test_killing_child_twice_does_not_raise(ui: UI, box_class):
    box = box_class(ui)
    container = Container(box, size=ANY_SIZE)

    container.kill()
    container.kill()


# endregion


# region --- Hit-testing ------------------------------------------------------


@pytest.mark.parametrize(
    ("hit_testable", "consumed"),
    [(False, False), (True, True)],
    ids=["not hit-testable", "hit-testable"],
)
def test_press_in_gap_between_children_is_consumed_only_if_hit_testable(
    hit_testable,
    consumed,
):
    ui = make_ui(box_gap=3)
    vbox = VBox(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        enabled=True,
        visible=True,
        hit_testable=hit_testable,
    )
    Container(vbox, size=(10, 4), hit_testable=True)
    Container(vbox, size=(10, 8), hit_testable=True)

    ui.update()

    assert left_press(ui, pos=(15, 25)) is consumed


# endregion


# region --- Axis -------------------------------------------------------------


@pytest.mark.parametrize(
    ("axis", "expected_cross"),
    [
        (Axis.HORIZONTAL, Axis.VERTICAL),
        (Axis.VERTICAL, Axis.HORIZONTAL),
    ],
)
def test_axis_cross_is_other_axis(axis, expected_cross):
    assert axis.cross is expected_cross


@pytest.mark.parametrize(
    ("axis", "expected_value"),
    [
        (Axis.HORIZONTAL, 9),
        (Axis.VERTICAL, 10),
    ],
)
def test_axis_indexes_its_value_in_xy_pair(axis, expected_value):
    assert (9, 10)[axis] == expected_value


# endregion


# region --- _to_xy_order() ---------------------------------------------------


@pytest.mark.parametrize(
    ("main_axis", "expected_pair"),
    [
        (Axis.HORIZONTAL, (3, 5)),
        (Axis.VERTICAL, (5, 3)),
    ],
)
def test_to_xy_order_puts_main_axis_value_in_main_axis_slot(main_axis, expected_pair):
    assert _to_xy_order(main_axis, 3, 5) == expected_pair


# endregion
