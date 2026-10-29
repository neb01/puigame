import pytest

from puigame._styling.theme import DEFAULT_THEME
from puigame.core.anchor import Anchor
from puigame.core.ui_root import UIRoot
from puigame.widgets.label import Label

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)
ANY_STRING = "ordinary northumbrian spokeshaver's coracle"

# endregion


# region --- Construction -----------------------------------------------------


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
    label = Label(ui_root, size=ANY_SIZE, **{argument: value})

    assert getattr(label, argument) == value


def test_forwards_placement_arguments():
    ui_root = UIRoot(size=(20, 30), theme=DEFAULT_THEME)
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


# region --- Type checks ------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [5, 6.7, None, b"bytes object"],
    ids=["int", "float", "None", "bytes"],
)
def test_constructor_with_non_string_text_raises(ui_root: UIRoot, text):
    with pytest.raises(TypeError):
        Label(ui_root, size=ANY_SIZE, text=text)

    assert ui_root.children == ()


@pytest.mark.parametrize(
    "text",
    [5, 6.7, None, b"bytes object"],
    ids=["int", "float", "None", "bytes"],
)
def test_text_setter_with_non_string_text_raises(ui_root: UIRoot, text):
    label = Label(ui_root, size=ANY_SIZE, text="vociferous")

    with pytest.raises(TypeError):
        label.text = text

    assert label.text == "vociferous"


# endregion
