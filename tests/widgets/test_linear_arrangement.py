import pytest

from mouse_helpers import left_click, left_press
from puigame import (
    UI,
    Anchor,
    BundledTypeface,
    Column,
    Container,
    CrossAxisAlign,
    FadeProfile,
    NoSkin,
    Row,
    Style,
    TextAlign,
    TextHorizontalExtent,
    Theme,
    ToggleButton,
    ToggleGroup,
)
from puigame._widgets.linear_arrangement import Axis, _to_xy_order

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


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_image_is_zero_size(ui: UI, arrangement_class):
    arrangement = arrangement_class(ui)
    Container(arrangement, size=(5, 10))

    ui.update()

    assert arrangement.image.size == (0, 0)


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_rect_is_zero_size_before_first_update(ui: UI, arrangement_class):
    arrangement = arrangement_class(ui)
    Container(arrangement, size=(5, 10))

    assert arrangement.rect.size == (0, 0)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("offset", (3, 5)),
        ("enabled", False),
        ("visible", False),
        ("hit_testable", True),
    ],
)
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_forwards_arguments_stored_as_attributes(
    ui: UI,
    arrangement_class,
    field_name,
    value,
):
    arrangement = arrangement_class(ui, **{field_name: value})

    assert getattr(arrangement, field_name) == value


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_forwards_placement_arguments(arrangement_class):
    ui = UI(size=(20, 30), theme=ANY_THEME)
    arrangement = arrangement_class(
        ui,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )
    Container(arrangement, size=(3, 5))

    ui.update()

    assert arrangement.rect.topleft == (-5, 21)


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_hit_testable_false_by_default(ui: UI, arrangement_class):
    arrangement = arrangement_class(ui)

    assert not arrangement.hit_testable


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("main_axis_spacing", -3),
        ("main_axis_reversed", True),
        ("cross_axis_align", CrossAxisAlign.END),
    ],
)
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_layout_arguments_stored_as_attributes(
    ui: UI,
    arrangement_class,
    field_name,
    value,
):
    arrangement = arrangement_class(ui, **{field_name: value})

    assert getattr(arrangement, field_name) == value


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
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_child_can_take_default_placement_arguments_and_any_offset(
    ui: UI,
    arrangement_class,
    field_name,
    value,
):
    arrangement = arrangement_class(ui)

    container = Container(arrangement, size=ANY_SIZE, **{field_name: value})

    assert arrangement.children == (container,)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("anchor", Anchor.TOP_LEFT),
        ("parent_anchor", Anchor.TOP_LEFT),
        ("margin", (3, 5)),
    ],
)
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_child_constructor_with_non_default_placement_argument_raises(
    ui: UI,
    arrangement_class,
    field_name,
    value,
):
    arrangement = arrangement_class(ui)

    with pytest.raises(ValueError):
        Container(arrangement, size=ANY_SIZE, **{field_name: value})

    assert arrangement.children == ()


def test_refused_toggle_button_does_not_join_its_group(ui: UI):
    arrangement = Column(ui)
    toggle_group = ToggleGroup()

    with pytest.raises(ValueError):
        ToggleButton(
            arrangement,
            size=ANY_SIZE,
            skin=ANY_SKIN,
            group=toggle_group,
            margin=(3, 5),
        )

    assert toggle_group.buttons == ()


def test_row_can_be_child_of_column(ui: UI):
    column = Column(ui)

    row = Row(column)

    assert column.children == (row,)


# endregion


# region --- Validation: spacing and alignment --------------------------------


@pytest.mark.parametrize("main_axis_spacing", [0, -3], ids=["zero", "negative"])
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_zero_or_negative_main_axis_spacing_is_allowed(
    ui: UI,
    arrangement_class,
    main_axis_spacing,
):
    arrangement = arrangement_class(ui, main_axis_spacing=main_axis_spacing)

    assert ui.children == (arrangement,)


@pytest.mark.parametrize(
    "main_axis_spacing",
    [True, 2.5, "3", None],
    ids=["bool", "float", "str", "None"],
)
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_non_int_main_axis_spacing_raises(ui: UI, arrangement_class, main_axis_spacing):
    with pytest.raises(TypeError):
        arrangement_class(ui, main_axis_spacing=main_axis_spacing)

    assert ui.children == ()


@pytest.mark.parametrize("main_axis_spacing", [0, -3], ids=["zero", "negative"])
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_main_axis_spacing_setter_can_take_zero_or_negative(
    ui: UI,
    arrangement_class,
    main_axis_spacing,
):
    arrangement = arrangement_class(ui, main_axis_spacing=5)

    arrangement.main_axis_spacing = main_axis_spacing

    assert arrangement.main_axis_spacing == main_axis_spacing


@pytest.mark.parametrize(
    "main_axis_spacing",
    [True, 2.5, "3", None],
    ids=["bool", "float", "str", "None"],
)
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_main_axis_spacing_setter_with_non_int_raises(
    ui: UI,
    arrangement_class,
    main_axis_spacing,
):
    arrangement = arrangement_class(ui, main_axis_spacing=5)

    with pytest.raises(TypeError):
        arrangement.main_axis_spacing = main_axis_spacing

    assert arrangement.main_axis_spacing == 5


@pytest.mark.parametrize(
    "cross_axis_align",
    ["CENTRE", None, 1],
    ids=["str", "None", "int"],
)
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_non_cross_axis_align_raises(ui: UI, arrangement_class, cross_axis_align):
    with pytest.raises(TypeError):
        arrangement_class(ui, cross_axis_align=cross_axis_align)

    assert ui.children == ()


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_cross_axis_align_setter_can_take_cross_axis_align(ui: UI, arrangement_class):
    arrangement = arrangement_class(ui, cross_axis_align=CrossAxisAlign.START)

    arrangement.cross_axis_align = CrossAxisAlign.END

    assert arrangement.cross_axis_align == CrossAxisAlign.END


@pytest.mark.parametrize(
    "cross_axis_align",
    [1, "CENTRE", None],
    ids=["int", "str", "None"],
)
@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_cross_axis_align_setter_with_non_cross_axis_align_raises(
    ui: UI,
    arrangement_class,
    cross_axis_align,
):
    arrangement = arrangement_class(ui, cross_axis_align=CrossAxisAlign.START)

    with pytest.raises(TypeError):
        arrangement.cross_axis_align = cross_axis_align

    assert arrangement.cross_axis_align == CrossAxisAlign.START


# endregion


# region --- Measuring --------------------------------------------------------


def test_main_axis_spacing_defaults_to_zero():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(ui)
    Container(column, size=(10, 4))
    Container(column, size=(6, 8))

    ui.update()

    assert column.rect.size == (10, 12)


def test_row_with_negative_spacing_overlaps_children():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=-4,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(row, size=(10, 4))
    container_2 = Container(row, size=(6, 8))
    container_3 = Container(row, size=(8, 2))

    ui.update()

    assert row.rect.size == (16, 8)
    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (16, 20)
    assert container_3.rect.topleft == (18, 20)


def test_column_with_negative_spacing_overlaps_children():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=-2,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(column, size=(10, 4))
    container_2 = Container(column, size=(6, 8))
    container_3 = Container(column, size=(8, 2))

    ui.update()

    assert column.rect.size == (10, 10)
    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (10, 22)
    assert container_3.rect.topleft == (10, 28)


@pytest.mark.parametrize(
    ("arrangement_class", "expected_size"),
    [(Row, (10, 12)), (Column, (10, 12))],
    ids=["Row", "Column"],
)
def test_child_overlapped_inside_earlier_child_does_not_shrink_size(
    arrangement_class,
    expected_size,
):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    arrangement = arrangement_class(ui, main_axis_spacing=-6)
    Container(arrangement, size=(10, 12))
    Container(arrangement, size=(2, 3))

    ui.update()

    assert arrangement.rect.size == expected_size


@pytest.mark.parametrize(
    ("arrangement_class", "expected_size"),
    [(Row, (22, 8)), (Column, (10, 20))],
    ids=["Row", "Column"],
)
def test_overlap_larger_than_children_sizes_to_enclose_them(
    arrangement_class,
    expected_size,
):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    arrangement = arrangement_class(ui, main_axis_spacing=-14)
    Container(arrangement, size=(10, 4))
    Container(arrangement, size=(6, 8))
    Container(arrangement, size=(8, 2))

    ui.update()

    assert arrangement.rect.size == expected_size


def test_row_with_overlap_larger_than_children_shifts_them_inside():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=-14,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(row, size=(10, 4))
    container_2 = Container(row, size=(6, 8))
    container_3 = Container(row, size=(8, 2))

    ui.update()

    assert container_1.rect.topleft == (22, 20)
    assert container_2.rect.topleft == (18, 20)
    assert container_3.rect.topleft == (10, 20)


def test_column_with_overlap_larger_than_children_shifts_them_inside():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=-14,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(column, size=(10, 4))
    container_2 = Container(column, size=(6, 8))
    container_3 = Container(column, size=(8, 2))

    ui.update()

    assert container_1.rect.topleft == (10, 36)
    assert container_2.rect.topleft == (10, 26)
    assert container_3.rect.topleft == (10, 20)


def test_column_is_as_tall_as_children_and_spacing_and_as_wide_as_widest_child():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(ui, main_axis_spacing=3)
    Container(column, size=(10, 4))
    Container(column, size=(6, 8))
    Container(column, size=(8, 2))

    ui.update()

    assert column.rect.size == (10, 20)


def test_row_is_as_wide_as_children_and_spacing_and_as_tall_as_tallest_child():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(ui, main_axis_spacing=3)
    Container(row, size=(10, 4))
    Container(row, size=(6, 8))
    Container(row, size=(8, 2))

    ui.update()

    assert row.rect.size == (30, 8)


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_arrangement_with_one_child_has_no_spacing(arrangement_class):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    arrangement = arrangement_class(ui, main_axis_spacing=3)
    Container(arrangement, size=(7, 5))

    ui.update()

    assert arrangement.rect.size == (7, 5)


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_arrangement_with_no_children_is_zero_size(arrangement_class):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    arrangement = arrangement_class(ui, main_axis_spacing=3)

    ui.update()

    assert arrangement.rect.size == (0, 0)


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_arrangement_with_only_hidden_children_is_zero_size(arrangement_class):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    arrangement = arrangement_class(ui, main_axis_spacing=3)
    Container(arrangement, size=(7, 5), visible=False)
    Container(arrangement, size=(6, 4), visible=False)

    ui.update()

    assert arrangement.rect.size == (0, 0)


def test_hidden_child_takes_no_space_or_spacing():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(ui, main_axis_spacing=3)
    Container(column, size=(10, 4))
    Container(column, size=(16, 8), visible=False)
    Container(column, size=(8, 2))

    ui.update()

    assert column.rect.size == (10, 9)


def test_nested_arrangements_are_measured_inside_out_in_one_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(ui, main_axis_spacing=3)
    row = Row(column, main_axis_spacing=3)
    Container(row, size=(4, 6))
    Container(row, size=(5, 2))
    Container(column, size=(8, 4))

    ui.update()

    assert row.rect.size == (12, 6)
    assert column.rect.size == (12, 13)


def test_arrangement_is_placed_by_its_new_size_in_the_same_update():
    ui = UI(size=(100, 80), theme=ANY_THEME)
    column = Column(ui, anchor=Anchor.CENTRE)
    Container(column, size=(10, 4))

    ui.update()

    assert column.rect.topleft == (45, 38)


# endregion


# region --- Placement --------------------------------------------------------


@pytest.mark.parametrize(
    (
        "cross_axis_align",
        "expected_topleft_1",
        "expected_topleft_2",
        "expected_topleft_3",
    ),
    [
        (CrossAxisAlign.START, (10, 20), (10, 27), (10, 38)),
        (CrossAxisAlign.CENTRE, (10, 20), (12, 27), (11, 38)),
        (CrossAxisAlign.END, (10, 20), (14, 27), (12, 38)),
    ],
)
def test_column_stacks_children_top_to_bottom_aligned_across(
    cross_axis_align,
    expected_topleft_1,
    expected_topleft_2,
    expected_topleft_3,
):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=cross_axis_align,
    )
    container_1 = Container(column, size=(10, 4))
    container_2 = Container(column, size=(6, 8))
    container_3 = Container(column, size=(8, 2))

    ui.update()

    assert container_1.rect.topleft == expected_topleft_1
    assert container_2.rect.topleft == expected_topleft_2
    assert container_3.rect.topleft == expected_topleft_3


@pytest.mark.parametrize(
    (
        "cross_axis_align",
        "expected_topleft_1",
        "expected_topleft_2",
        "expected_topleft_3",
    ),
    [
        (CrossAxisAlign.START, (10, 20), (23, 20), (32, 20)),
        (CrossAxisAlign.CENTRE, (10, 22), (23, 20), (32, 23)),
        (CrossAxisAlign.END, (10, 24), (23, 20), (32, 26)),
    ],
)
def test_row_stacks_children_left_to_right_aligned_across(
    cross_axis_align,
    expected_topleft_1,
    expected_topleft_2,
    expected_topleft_3,
):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=cross_axis_align,
    )
    container_1 = Container(row, size=(10, 4))
    container_2 = Container(row, size=(6, 8))
    container_3 = Container(row, size=(8, 2))

    ui.update()

    assert container_1.rect.topleft == expected_topleft_1
    assert container_2.rect.topleft == expected_topleft_2
    assert container_3.rect.topleft == expected_topleft_3


def test_cross_axis_align_defaults_to_centre():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(ui, anchor=Anchor.TOP_LEFT, margin=(10, 20), main_axis_spacing=3)
    Container(column, size=(10, 4))
    container = Container(column, size=(6, 8))

    ui.update()

    assert container.rect.topleft == (12, 27)


@pytest.mark.parametrize(
    ("arrangement_class", "size_1", "size_2", "expected_topleft"),
    [(Row, (2, 5), (2, 2), (15, 21)), (Column, (5, 2), (2, 2), (11, 25))],
    ids=["Row", "Column"],
)
def test_centring_rounds_half_pixel_down(
    arrangement_class,
    size_1,
    size_2,
    expected_topleft,
):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    arrangement = arrangement_class(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.CENTRE,
    )
    Container(arrangement, size=size_1)
    container = Container(arrangement, size=size_2)

    ui.update()

    assert container.rect.topleft == expected_topleft


def test_child_offset_applies_after_placement():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    Container(column, size=(10, 4))
    container = Container(column, size=(6, 8), offset=(2, 5))

    ui.update()

    assert container.rect.topleft == (12, 32)


@pytest.mark.parametrize(
    ("offset", "expected_topleft"),
    [((-0.5, 0), (11, 25)), ((0.5, 0), (12, 25)), ((0, 0.5), (11, 25))],
    ids=["negative half x", "positive half x", "positive half y"],
)
def test_centred_child_with_fractional_offset_is_rounded_down_once(
    offset,
    expected_topleft,
):
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.CENTRE,
    )
    Container(column, size=(5, 2))
    container = Container(column, size=(2, 2), offset=offset)

    ui.update()

    assert container.rect.topleft == expected_topleft


def test_hidden_child_is_placed_at_arrangement_top_left():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.CENTRE,
    )
    Container(column, size=(10, 4))
    container = Container(column, size=(6, 8), visible=False)

    ui.update()

    assert container.rect.topleft == (10, 20)


def test_children_are_at_arrangement_top_left_before_first_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.CENTRE,
    )
    container_1 = Container(column, size=(10, 4))
    container_2 = Container(column, size=(6, 8))

    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (10, 20)


def test_nested_arrangements_place_children_in_one_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.CENTRE,
    )
    row = Row(column, main_axis_spacing=3, cross_axis_align=CrossAxisAlign.CENTRE)
    container_1 = Container(row, size=(4, 6))
    container_2 = Container(row, size=(5, 2))
    container_3 = Container(column, size=(8, 4))

    ui.update()

    assert row.rect.topleft == (10, 20)
    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (17, 22)
    assert container_3.rect.topleft == (12, 29)


def test_main_axis_reversed_defaults_to_false():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(row, size=(10, 4))
    container_2 = Container(row, size=(6, 8))

    ui.update()

    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (23, 20)


def test_reversed_row_stacks_children_right_to_left():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        main_axis_reversed=True,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(row, size=(10, 4))
    container_2 = Container(row, size=(6, 8))
    container_3 = Container(row, size=(8, 2))

    ui.update()

    assert row.rect.size == (30, 8)
    assert container_1.rect.topleft == (30, 20)
    assert container_2.rect.topleft == (21, 20)
    assert container_3.rect.topleft == (10, 20)


def test_reversed_column_stacks_children_bottom_to_top():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        main_axis_reversed=True,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(column, size=(10, 4))
    container_2 = Container(column, size=(6, 8))
    container_3 = Container(column, size=(8, 2))

    ui.update()

    assert column.rect.size == (10, 20)
    assert container_1.rect.topleft == (10, 36)
    assert container_2.rect.topleft == (10, 25)
    assert container_3.rect.topleft == (10, 20)


def test_reversed_row_with_overlap_larger_than_children_shifts_them_inside():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=-14,
        main_axis_reversed=True,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(row, size=(10, 4))
    container_2 = Container(row, size=(6, 8))
    container_3 = Container(row, size=(8, 2))

    ui.update()

    assert row.rect.size == (22, 8)
    assert container_1.rect.topleft == (10, 20)
    assert container_2.rect.topleft == (18, 20)
    assert container_3.rect.topleft == (24, 20)


# endregion


# region --- Tree changes -----------------------------------------------------


def test_new_child_is_stacked_after_existing_children_at_next_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    Container(column, size=(10, 4))

    ui.update()

    container = Container(column, size=(6, 8))
    ui.update()

    assert column.rect.size == (10, 15)
    assert container.rect.topleft == (10, 27)


def test_killed_child_frees_its_space_at_next_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    Container(column, size=(10, 4))
    middle_container = Container(column, size=(16, 8))
    last_container = Container(column, size=(8, 2))

    ui.update()

    middle_container.kill()
    ui.update()

    assert column.rect.size == (10, 9)
    assert last_container.rect.topleft == (10, 27)


def test_shown_child_takes_its_space_at_next_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    Container(column, size=(10, 4))
    middle_container = Container(column, size=(16, 8), visible=False)
    last_container = Container(column, size=(8, 2))

    ui.update()

    middle_container.visible = True
    ui.update()

    assert column.rect.size == (16, 20)
    assert last_container.rect.topleft == (10, 38)


def test_hidden_child_moves_to_arrangement_top_left_at_next_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.CENTRE,
    )
    Container(column, size=(10, 4))
    container = Container(column, size=(6, 8))

    ui.update()

    container.visible = False
    ui.update()

    assert container.rect.topleft == (10, 20)


@pytest.mark.parametrize("arrangement_class", [Row, Column], ids=["Row", "Column"])
def test_killing_child_twice_does_not_raise(ui: UI, arrangement_class):
    arrangement = arrangement_class(ui)
    container = Container(arrangement, size=ANY_SIZE)

    container.kill()
    container.kill()


# endregion


# region --- Assigning layout settings ----------------------------------------


def test_assigned_main_axis_spacing_applies_at_next_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    Container(row, size=(10, 4))
    container = Container(row, size=(6, 8))
    ui.update()

    row.main_axis_spacing = -2
    ui.update()

    assert row.rect.size == (14, 8)
    assert container.rect.topleft == (18, 20)


def test_assigned_main_axis_reversed_applies_at_next_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    container_1 = Container(row, size=(10, 4))
    container_2 = Container(row, size=(6, 8))
    ui.update()

    row.main_axis_reversed = True
    ui.update()

    assert container_1.rect.topleft == (19, 20)
    assert container_2.rect.topleft == (10, 20)


def test_assigned_cross_axis_align_applies_at_next_update():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=3,
        cross_axis_align=CrossAxisAlign.START,
    )
    Container(column, size=(10, 4))
    container = Container(column, size=(6, 8))
    ui.update()

    column.cross_axis_align = CrossAxisAlign.END
    ui.update()

    assert container.rect.topleft == (14, 27)


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
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    column = Column(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        enabled=True,
        visible=True,
        hit_testable=hit_testable,
        main_axis_spacing=3,
    )
    Container(column, size=(10, 4), hit_testable=True)
    Container(column, size=(10, 8), hit_testable=True)

    ui.update()

    assert left_press(ui, pos=(15, 25)) is consumed


def test_reversed_row_still_hits_later_child_where_children_overlap():
    ui = UI(size=UI_SIZE, theme=ANY_THEME)
    row = Row(
        ui,
        anchor=Anchor.TOP_LEFT,
        margin=(10, 20),
        main_axis_spacing=-4,
        main_axis_reversed=True,
        cross_axis_align=CrossAxisAlign.START,
    )
    toggle_button_1 = ToggleButton(
        row,
        size=(10, 6),
        skin=ANY_SKIN,
        enabled=True,
        visible=True,
        hit_testable=True,
    )
    toggle_button_2 = ToggleButton(
        row,
        size=(10, 6),
        skin=ANY_SKIN,
        enabled=True,
        visible=True,
        hit_testable=True,
    )
    ui.update()

    left_click(ui, pos=(17, 23))

    assert toggle_button_1.checked is False
    assert toggle_button_2.checked is True


# endregion


# region --- Axis -------------------------------------------------------------


@pytest.mark.parametrize(
    ("axis", "expected_cross"),
    [(Axis.HORIZONTAL, Axis.VERTICAL), (Axis.VERTICAL, Axis.HORIZONTAL)],
)
def test_axis_cross_is_other_axis(axis, expected_cross):
    assert axis.cross is expected_cross


@pytest.mark.parametrize(
    ("axis", "expected_value"),
    [(Axis.HORIZONTAL, 9), (Axis.VERTICAL, 10)],
)
def test_axis_indexes_its_value_in_xy_pair(axis, expected_value):
    assert (9, 10)[axis] == expected_value


# endregion


# region --- _to_xy_order() ---------------------------------------------------


@pytest.mark.parametrize(
    ("main_axis", "expected_pair"),
    [(Axis.HORIZONTAL, (3, 5)), (Axis.VERTICAL, (5, 3))],
)
def test_to_xy_order_puts_main_axis_value_in_main_axis_slot(main_axis, expected_pair):
    assert _to_xy_order(main_axis, 3, 5) == expected_pair


# endregion
