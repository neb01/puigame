import pytest

from puigame import (
    Anchor,
    BundledTypeface,
    FadeProfile,
    Label,
    Style,
    TextHorizontalExtent,
    Theme,
)
from puigame._ui.ui_root import UIRoot

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)
ANY_STRING = "ordinary northumbrian spokeshaver's coracle"

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
    label = Label(ui_root, size=ANY_SIZE, **{field_name: value})

    assert getattr(label, field_name) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=ANY_THEME)
    label = Label(
        ui_root,
        size=(3, 5),
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(2, 4),
    )

    assert label.rect.topleft == (-5, 21)


def test_consumes_clicks_false_by_default(ui_root: UIRoot):
    label = Label(ui_root, size=ANY_SIZE)

    assert not label.consumes_clicks


# endregion


# region --- text -------------------------------------------------------------


def test_text_getter_returns_given_text(ui_root: UIRoot):
    label = Label(ui_root, size=ANY_SIZE, text="schmip")

    assert label.text == "schmip"


def test_text_defaults_to_empty_string(ui_root: UIRoot):
    label = Label(ui_root, size=ANY_SIZE)

    assert label.text == ""


# endregion


# region --- Image ------------------------------------------------------------


def test_label_with_text_has_non_zero_size_image(ui_root: UIRoot):
    label = Label(ui_root, size=ANY_SIZE, text="coracle")

    assert 0 not in label.image.size


def test_label_without_text_has_zero_size_image(ui_root: UIRoot):
    label = Label(ui_root, size=ANY_SIZE, text="")

    assert label.image.size == (0, 0)


def test_text_setter_updates_image(ui_root: UIRoot):
    label = Label(ui_root, size=ANY_SIZE, text="")

    assert label.image.size == (0, 0)

    label.text = ANY_STRING

    assert 0 not in label.image.size


def test_text_setter_with_current_text_keeps_image(ui_root: UIRoot):
    label = Label(ui_root, size=ANY_SIZE, text="calcium")
    image = label.image

    label.text = "calcium"

    assert label.image is image


# endregion


# region --- Validation -------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [5, 6.7, b"bytes object", None],
    ids=["int", "float", "bytes", "None"],
)
def test_constructor_with_non_string_text_raises(ui_root: UIRoot, text):
    with pytest.raises(TypeError):
        Label(ui_root, size=ANY_SIZE, text=text)

    assert ui_root.children == ()


@pytest.mark.parametrize(
    "text",
    [5, 6.7, b"bytes object", None],
    ids=["int", "float", "bytes", "None"],
)
def test_text_setter_with_non_string_text_raises(ui_root: UIRoot, text):
    label = Label(ui_root, size=ANY_SIZE, text="vociferous")

    with pytest.raises(TypeError):
        label.text = text

    assert label.text == "vociferous"


# endregion
