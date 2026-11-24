import pygame as pg
import pytest

from puigame import BundledTypeface, TextAlign
from puigame._components.text import _get_font

# region --- Constants --------------------------------------------------------

# every printable ASCII character except the space, 0x21 to 0x7E
VISIBLE_ASCII = (
    "!\"#$%&'()*+,-./0123456789:;<=>?@"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
    "abcdefghijklmnopqrstuvwxyz{|}~"
)
PRINTABLE_ASCII = " " + VISIBLE_ASCII
DIGITS = "0123456789"

WHITE = (255, 255, 255, 255)

# endregion


# region --- Helpers ----------------------------------------------------------


def _render(typeface: BundledTypeface, font_size: int, content: str) -> pg.Surface:
    """Render text in a bundled font as ``Text`` does, without antialiasing.

    Args:
        typeface: Bundled typeface to render in.
        font_size: Font size, in pixels.
        content: Text to render.

    Returns:
        The rendered text, white on a transparent background.
    """
    font = _get_font(typeface=typeface, size=font_size, text_align=TextAlign.LEFT)
    return font.render(content, antialias=False, color=WHITE)


def _advance(typeface: BundledTypeface, font_size: int, character: str) -> int:
    """Return how far a character moves the pen, in pixels.

    Args:
        typeface: Bundled typeface to measure.
        font_size: Font size, in pixels.
        character: Character to measure.

    Returns:
        The character's advance.
    """
    font = _get_font(typeface=typeface, size=font_size, text_align=TextAlign.LEFT)
    (metrics,) = font.metrics(character)
    assert metrics is not None
    _minx, _maxx, _miny, _maxy, advance = metrics
    return advance


def _has_same_ink(surface_1: pg.Surface, surface_2: pg.Surface) -> bool:
    """Return whether two surfaces are the same size with the same ink.

    Args:
        surface_1: First surface to compare.
        surface_2: Second surface to compare.

    Returns:
        ``True`` if the surfaces are the same size and their non-transparent
        pixels are in the same places.
    """
    if surface_1.size != surface_2.size:
        return False

    non_transparent_mask_1 = pg.mask.from_surface(surface_1, 0)
    non_transparent_mask_2 = pg.mask.from_surface(surface_2, 0)
    overlap_bits = non_transparent_mask_1.overlap_area(non_transparent_mask_2, (0, 0))
    return (
        non_transparent_mask_1.count() == overlap_bits
        and non_transparent_mask_2.count() == overlap_bits
    )


# endregion


# region --- Character coverage -----------------------------------------------


@pytest.mark.parametrize(
    "typeface",
    [BundledTypeface.NEB0FONT, BundledTypeface.NEBMON0FONT],
)
def test_bundled_fonts_draw_every_printable_ascii_character(typeface):
    placeholder_image = _render(typeface, 6, "£")

    characters_drawn_as_placeholder = [
        character
        for character in PRINTABLE_ASCII
        if _has_same_ink(_render(typeface, 6, character), placeholder_image)
    ]

    assert characters_drawn_as_placeholder == []


@pytest.mark.parametrize(
    "typeface",
    [BundledTypeface.NEB0FONT, BundledTypeface.NEBMON0FONT],
)
def test_bundled_fonts_draw_other_characters_as_the_same_placeholder(typeface):
    pound_image = _render(typeface, 6, "£")
    e_acute_image = _render(typeface, 6, "é")

    assert pg.mask.from_surface(pound_image, 0).count() != 0
    assert _has_same_ink(pound_image, e_acute_image)


# endregion


# region --- Advances ---------------------------------------------------------


def test_nebmon0font_gives_every_character_the_same_advance():
    advances = {
        _advance(BundledTypeface.NEBMON0FONT, 6, character)
        for character in PRINTABLE_ASCII
    }

    assert advances == {4}


def test_neb0font_gives_every_digit_the_same_advance():
    advances = {_advance(BundledTypeface.NEB0FONT, 6, digit) for digit in DIGITS}

    assert advances == {4}


@pytest.mark.parametrize(
    ("character", "expected_advance"),
    [("i", 2), ("l", 3), ("W", 4)],
)
def test_neb0font_gives_characters_advances_by_width(character, expected_advance):
    advance = _advance(BundledTypeface.NEB0FONT, 6, character)

    assert advance == expected_advance


# INK centring in the default theme relies on Neb0Font's blank space all
# coming after each glyph
def test_neb0font_glyphs_start_at_their_origin():
    ink_lefts = {
        character: _render(BundledTypeface.NEB0FONT, 6, character)
        .get_bounding_rect()
        .left
        for character in VISIBLE_ASCII
    }

    characters_with_left_space = [
        character for character, ink_left in ink_lefts.items() if ink_left != 0
    ]

    assert characters_with_left_space == []


# endregion


# region --- Pixel grid -------------------------------------------------------


@pytest.mark.parametrize(
    ("font_size", "scale"),
    [(12, 2), (18, 3), (24, 4)],
    ids=["size 12", "size 18", "size 24"],
)
@pytest.mark.parametrize(
    "typeface",
    [BundledTypeface.NEB0FONT, BundledTypeface.NEBMON0FONT],
)
def test_bundled_fonts_render_multiples_of_6_as_scaled_up_size_6(
    typeface,
    font_size,
    scale,
):
    size_6_image = _render(typeface, 6, PRINTABLE_ASCII)
    expected_image = pg.transform.scale_by(size_6_image, scale)

    image = _render(typeface, font_size, PRINTABLE_ASCII)

    assert image.size == expected_image.size
    assert _has_same_ink(image, expected_image)


# endregion
