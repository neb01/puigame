import pygame as pg
import pytest

from puigame import BundledCursor, CursorImage

# region --- Constants --------------------------------------------------------

CURSOR_SIZE = (16, 16)

ANY_STRING = "correct horses and staple batteries"

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)

# endregion


# region --- Helpers ----------------------------------------------------------


def _filled_image(
    size: tuple[int, int],
    colour: tuple[int, int, int, int],
) -> pg.Surface:
    """Return a new image of one colour, with per-pixel alpha.

    Args:
        size: Width and height in pixels.
        colour: Colour to fill the image with.

    Returns:
        The filled image.
    """
    image = pg.Surface(size, pg.SRCALPHA)
    image.fill(colour)
    return image


# endregion


# region --- CursorImage ------------------------------------------------------


def test_cursor_image_keeps_image_size_and_colour():
    image = _filled_image((9, 10), RED)

    cursor_image = CursorImage(image, (3, 4))

    assert cursor_image.image.size == (9, 10)
    assert cursor_image.image.get_at((8, 9)) == RED


def test_cursor_image_is_unchanged_by_drawing_on_the_original_image():
    image = _filled_image((9, 10), RED)
    cursor_image = CursorImage(image, (3, 4))

    image.fill(BLUE)

    assert cursor_image.image.get_at((8, 9)) == RED


# endregion


# region --- CursorImage.bundled() --------------------------------------------


@pytest.mark.parametrize("bundled_cursor", [*BundledCursor])
def test_bundled_cursor_image_is_16_by_16_with_ink(bundled_cursor):
    cursor_image = CursorImage.bundled(bundled_cursor)

    assert cursor_image.image.size == CURSOR_SIZE
    assert pg.mask.from_surface(cursor_image.image, 0).count() != 0


@pytest.mark.parametrize(
    ("bundled_cursor", "expected_hotspot"),
    [
        (BundledCursor.DARK_ARROW, (0, 0)),
        (BundledCursor.DARK_CROSSHAIR, (4, 4)),
        (BundledCursor.DARK_HAND, (3, 0)),
        (BundledCursor.DARK_I_BEAM, (4, 7)),
        (BundledCursor.GREEN_ARROW, (0, 0)),
        (BundledCursor.GREEN_CROSSHAIR, (4, 4)),
        (BundledCursor.GREEN_HAND, (3, 0)),
        (BundledCursor.GREEN_I_BEAM, (4, 7)),
        (BundledCursor.LIGHT_ARROW, (0, 0)),
        (BundledCursor.LIGHT_CROSSHAIR, (4, 4)),
        (BundledCursor.LIGHT_HAND, (3, 0)),
        (BundledCursor.LIGHT_I_BEAM, (4, 7)),
    ],
    ids=[
        "dark arrow",
        "dark crosshair",
        "dark hand",
        "dark i-beam",
        "green arrow",
        "green crosshair",
        "green hand",
        "green i-beam",
        "light arrow",
        "light crosshair",
        "light hand",
        "light i-beam",
    ],
)
def test_bundled_cursor_has_its_shapes_hotspot(bundled_cursor, expected_hotspot):
    cursor_image = CursorImage.bundled(bundled_cursor)

    assert cursor_image.hotspot == expected_hotspot


def test_bundled_cursors_of_the_same_member_do_not_share_an_image():
    cursor_image_1 = CursorImage.bundled(BundledCursor.GREEN_ARROW)
    cursor_image_2 = CursorImage.bundled(BundledCursor.GREEN_ARROW)

    cursor_image_1.image.fill(BLUE)

    assert cursor_image_2.image.get_at((15, 15)) != BLUE


def test_drawing_on_a_bundled_cursor_does_not_change_later_ones():
    first_cursor_image = CursorImage.bundled(BundledCursor.GREEN_ARROW)

    first_cursor_image.image.fill(BLUE)
    later_cursor_image = CursorImage.bundled(BundledCursor.GREEN_ARROW)

    assert later_cursor_image.image.get_at((15, 15)) != BLUE


# endregion


# region --- Validation -------------------------------------------------------


@pytest.mark.parametrize(
    "hotspot",
    [(0, 0), (3, 4), (-3, 20), (1.5, 2.5)],
    ids=["zero", "inside the image", "outside the image", "floats"],
)
def test_cursor_image_hotspot_can_take_tuple_of_numbers(hotspot):
    cursor_image = CursorImage(_filled_image((9, 10), RED), hotspot)

    assert cursor_image.hotspot == hotspot


@pytest.mark.parametrize(
    "hotspot",
    [1, 3.5, [2, 3], pg.Vector2(4, 5)],
    ids=["int", "float", "list", "pg.Vector2"],
)
def test_constructor_with_non_tuple_hotspot_raises(hotspot):
    image = _filled_image((9, 10), RED)

    with pytest.raises(TypeError):
        CursorImage(image, hotspot)


@pytest.mark.parametrize(
    "hotspot",
    [(), (3,), (3, 4, 5), (True, 3), (3, True), ("3", 4), (None, 3), (3, None)],
    ids=[
        "empty",
        "1 item",
        "3 items",
        "bool x",
        "bool y",
        "str item",
        "None x",
        "None y",
    ],
)
def test_constructor_with_tuple_hotspot_that_is_not_two_numbers_raises(hotspot):
    image = _filled_image((9, 10), RED)

    with pytest.raises(TypeError):
        CursorImage(image, hotspot)


@pytest.mark.parametrize("bundled_cursor", [ANY_STRING, None], ids=["str", "None"])
def test_bundled_with_str_or_none_raises(bundled_cursor):
    with pytest.raises(TypeError):
        CursorImage.bundled(bundled_cursor)


# endregion
