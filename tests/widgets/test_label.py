from dataclasses import replace
from pathlib import Path

import pytest

from puigame import (
    UI,
    Anchor,
    BundledTypeface,
    FadeProfile,
    Label,
    Style,
    TextAlign,
    TextHorizontalExtent,
    Theme,
)

# region --- Constants --------------------------------------------------------

NEBMON0FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "nebmon0font.ttf"

ANY_SIZE = (9, 10)
ANY_STRING = "ordinary northumbrian spokeshaver's coracle"

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


def _text_fitting_ui(*, font_size: int, text_margin: tuple[int, int]) -> UI:
    """Return a 300x200 UI whose theme sets the text's font size and margin.

    The text is in ``nebmon0font.ttf``, measured by its ink, and anchored
    ``CENTRE`` to ``CENTRE`` with no offset. Tests that change any of these
    build their own theme.
    """
    style = replace(
        ANY_STYLE,
        text_typeface=NEBMON0FONT_PATH,
        text_font_size=font_size,
        text_anchor=Anchor.CENTRE,
        text_parent_anchor=Anchor.CENTRE,
        text_horizontal_extent=TextHorizontalExtent.INK,
        text_margin=text_margin,
        text_offset=(0, 0),
    )

    return UI(size=(300, 200), theme=Theme(base_style=style, style_overrides={}))


# endregion


# region --- Construction -----------------------------------------------------


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
    label = Label(ui, size=ANY_SIZE, **{field_name: value})

    assert getattr(label, field_name) == value


def test_forwards_placement_arguments():
    ui = UI(size=(20, 30), theme=ANY_THEME)
    label = Label(
        ui,
        size=(3, 5),
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert label.rect.topleft == (-5, 21)


def test_hit_testable_false_by_default(ui: UI):
    label = Label(ui, size=ANY_SIZE)

    assert not label.hit_testable


# endregion


# region --- text -------------------------------------------------------------


def test_text_getter_returns_given_text(ui: UI):
    label = Label(ui, size=ANY_SIZE, text="schmip")

    assert label.text == "schmip"


def test_text_defaults_to_empty_string(ui: UI):
    label = Label(ui, size=ANY_SIZE)

    assert label.text == ""


# endregion


# region --- Fitted size ------------------------------------------------------


def test_size_defaults_to_fitting_both_axes_to_text():
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, text="SPUD")

    assert label.rect.size == (51, 22)


@pytest.mark.parametrize(
    ("size", "expected_size"),
    [((None, 40), (51, 40)), ((60, None), (60, 22))],
    ids=["width fitted", "height fitted"],
)
def test_none_axis_fits_to_text_and_fixed_axis_keeps_its_size(size, expected_size):
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, size=size, text="SPUD")

    assert label.rect.size == expected_size


def test_empty_text_fits_to_margins_and_one_line_high():
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, text="")

    assert label.rect.size == (6, 22)


@pytest.mark.parametrize(
    ("size", "expected_size"),
    [
        ((None, None), (111, 40)),
        ((None, 30), (111, 30)),
        ((60, None), (60, 40)),
        ((60, 30), (60, 30)),
    ],
    ids=["both fitted", "width fitted", "height fitted", "neither fitted"],
)
def test_text_setter_fits_none_axes_to_new_text(size, expected_size):
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, size=size, text="SPUD")

    label.text = "SPUD SPUD\nSPUD"

    assert label.rect.size == expected_size


def test_text_setter_keeps_fixed_float_axis_rounded_down():
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, size=(60.7, None), text="SPUD")

    label.text = "SPUD SPUD\nSPUD"

    assert label.rect.size == (60, 40)


def test_text_setter_resizes_the_same_rect():
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, text="SPUD")
    rect = label.rect

    label.text = "SPUD SPUD\nSPUD"

    assert label.rect is rect


def test_text_setter_keeps_rect_top_left_until_update():
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, text="SPUD", anchor=Anchor.CENTRE, parent_anchor=Anchor.CENTRE)

    label.text = "SPUD SPUD\nSPUD"

    assert label.rect.topleft == (124, 89)


def test_update_after_text_setter_places_refitted_rect():
    ui = _text_fitting_ui(font_size=18, text_margin=(3, 5))
    label = Label(ui, text="SPUD", anchor=Anchor.CENTRE, parent_anchor=Anchor.CENTRE)

    label.text = "SPUD SPUD\nSPUD"
    ui.update()

    assert label.rect.topleft == (94, 80)


# endregion


# region --- Image ------------------------------------------------------------


def test_label_with_text_has_non_zero_size_image(ui: UI):
    label = Label(ui, size=ANY_SIZE, text="coracle")

    ui.update()

    assert 0 not in label.image.size


def test_label_without_text_has_zero_size_image(ui: UI):
    label = Label(ui, size=ANY_SIZE, text="")

    ui.update()

    assert label.image.size == (0, 0)


def test_text_setter_updates_image(ui: UI):
    label = Label(ui, size=ANY_SIZE, text="")

    ui.update()

    assert label.image.size == (0, 0)

    label.text = ANY_STRING
    ui.update()

    assert 0 not in label.image.size


def test_text_setter_with_current_text_keeps_image(ui: UI):
    label = Label(ui, size=ANY_SIZE, text="calcium")

    ui.update()
    image = label.image

    label.text = "calcium"
    ui.update()

    assert label.image is image


# endregion


# region --- Validation -------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [5, 6.7, b"bytes object", None],
    ids=["int", "float", "bytes", "None"],
)
def test_constructor_with_non_string_text_raises(ui: UI, text):
    with pytest.raises(TypeError):
        Label(ui, size=ANY_SIZE, text=text)

    assert ui.children == ()


@pytest.mark.parametrize(
    "text",
    [5, 6.7, b"bytes object", None],
    ids=["int", "float", "bytes", "None"],
)
def test_text_setter_with_non_string_text_raises(ui: UI, text):
    label = Label(ui, size=ANY_SIZE, text="vociferous")

    with pytest.raises(TypeError):
        label.text = text

    assert label.text == "vociferous"


# endregion
