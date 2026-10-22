import pytest

from puigame.core.ui_root import UIRoot
from puigame.widgets.label import Label

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)
ANY_STRING = "ordinary northumbrian spokeshaver's coracle"

# endregion


# region --- text -------------------------------------------------------------


def test_text_getter_returns_given_text(ui_root: UIRoot):
    label = Label(ui_root, ANY_SIZE, text="schmip")

    assert label.text == "schmip"


def test_text_defaults_to_empty_string(ui_root: UIRoot):
    label = Label(ui_root, ANY_SIZE)

    assert label.text == ""


# endregion


# region --- Image ------------------------------------------------------------


def test_label_with_text_has_non_zero_size_image(ui_root: UIRoot):
    label = Label(ui_root, ANY_SIZE, text="coracle")

    assert 0 not in label.image.size


def test_label_without_text_has_zero_size_image(ui_root: UIRoot):
    label = Label(ui_root, ANY_SIZE, text="")

    assert label.image.size == (0, 0)


def test_text_setter_updates_image(ui_root: UIRoot):
    label = Label(ui_root, ANY_SIZE, text="")

    assert label.image.size == (0, 0)

    label.text = ANY_STRING

    assert 0 not in label.image.size


def test_text_setter_with_current_text_keeps_image(ui_root: UIRoot):
    label = Label(ui_root, ANY_SIZE, text="calcium")
    image_1 = label.image

    label.text = "calcium"

    assert label.image is image_1


# endregion


# region --- Type checks ------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [5, 6.7, None, b"bytes object"],
    ids=["int", "float", "None", "bytes"],
)
def test_constructor_with_non_string_text_raises(ui_root: UIRoot, text):
    with pytest.raises(TypeError):
        Label(ui_root, ANY_SIZE, text=text)

    assert ui_root.children == ()


@pytest.mark.parametrize(
    "text",
    [5, 6.7, None, b"bytes object"],
    ids=["int", "float", "None", "bytes"],
)
def test_text_setter_with_non_string_text_raises(ui_root: UIRoot, text):
    label = Label(ui_root, ANY_SIZE, text="vociferous")

    with pytest.raises(TypeError):
        label.text = text

    assert label.text == "vociferous"


# endregion
