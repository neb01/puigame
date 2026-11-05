from dataclasses import replace
from pathlib import Path

import pygame as pg
import pytest

from puigame import DEFAULT_THEME, Anchor, BundledTypeface, TextHorizontalExtent
from puigame._components.text import Text

# region --- Constants --------------------------------------------------------

NEBMON0FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "nebmon0font.ttf"
WIDGET_SIZE = (100, 50)

ANY_STRING = "snath is the specific word for the handle of a scythe"
ANY_TEXT_HORIZONTAL_EXTENT = TextHorizontalExtent.INK

WHITE = (255, 255, 255, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)

# endregion


# region --- Helpers ----------------------------------------------------------


def _centred_ink_rect(
    font_size: int,
    content: str,
    text_horizontal_extent: TextHorizontalExtent,
) -> pg.Rect:
    """Render centred text in the test font and return its ink in widget coordinates.

    The text is anchored ``CENTRE`` to ``CENTRE`` in a ``WIDGET_SIZE`` widget, with
    no margin or offset, in ``nebmon0font.ttf``. Tests that change any of these
    build their own style.
    """
    style = replace(
        DEFAULT_THEME.base_style,
        text_typeface=NEBMON0FONT_PATH,
        text_font_size=font_size,
        text_anchor=Anchor.CENTRE,
        text_parent_anchor=Anchor.CENTRE,
        text_horizontal_extent=text_horizontal_extent,
        text_margin=(0, 0),
        text_offset=(0, 0),
    )

    text = Text(content)
    placed_image = text.render(WIDGET_SIZE, style)
    return placed_image.image.get_bounding_rect().move(placed_image.pos)


# endregion


# region --- Empty text -------------------------------------------------------


def test_render_empty_string_creates_zero_size_image():
    text = Text("")
    placed_image = text.render(
        (1, 3),
        replace(
            DEFAULT_THEME.base_style,
            text_font_size=24,
            text_anchor=Anchor.TOP_LEFT,
            text_parent_anchor=Anchor.BOTTOM_LEFT,
            text_margin=(2, 4),
            text_offset=(1, 5),
        ),
    )

    assert placed_image.image.size == (0, 0)
    assert placed_image.pos == (0, 0)


# endregion


# region --- Vertical placement -----------------------------------------------


@pytest.mark.parametrize(
    ("font_size", "expected_top", "expected_bottom"),
    [(18, 19, 31), (24, 17, 33)],
    ids=["font size 18", "font size 24"],
)
def test_render_centres_capitals_vertically(font_size, expected_top, expected_bottom):
    ink_rect = _centred_ink_rect(font_size, "SPUD", ANY_TEXT_HORIZONTAL_EXTENT)

    assert ink_rect.top == expected_top
    assert ink_rect.bottom == expected_bottom


def test_render_centres_multiline_text_as_a_block():
    ink_rect = _centred_ink_rect(18, "SPUD\nSPUD", ANY_TEXT_HORIZONTAL_EXTENT)

    assert ink_rect.top == 10
    assert ink_rect.bottom == 40


@pytest.mark.parametrize(
    ("text_horizontal_extent", "expected_topleft", "expected_bottomright"),
    [
        (TextHorizontalExtent.INK, (27, 19), (72, 31)),
        (TextHorizontalExtent.LOGICAL, (26, 19), (71, 31)),
    ],
    ids=["ink", "logical"],
)
def test_render_ignores_trailing_newline(
    text_horizontal_extent,
    expected_topleft,
    expected_bottomright,
):
    ink_rect = _centred_ink_rect(18, "SPUD\n", text_horizontal_extent)

    assert ink_rect.topleft == expected_topleft
    assert ink_rect.bottomright == expected_bottomright


def test_render_hangs_descenders_below_baseline():
    ink_rect = _centred_ink_rect(18, "Spuddy", ANY_TEXT_HORIZONTAL_EXTENT)

    assert ink_rect.top == 19
    assert ink_rect.bottom == 34


# endregion


# region --- Horizontal extent ------------------------------------------------


@pytest.mark.parametrize(
    ("font_size", "expected_left", "expected_right"),
    [(18, 27, 72), (24, 20, 80)],
    ids=["font size 18", "font size 24"],
)
def test_render_centres_ink_horizontally(font_size, expected_left, expected_right):
    ink_rect = _centred_ink_rect(font_size, "SPUD", TextHorizontalExtent.INK)

    assert ink_rect.left == expected_left
    assert ink_rect.right == expected_right


@pytest.mark.parametrize(
    ("font_size", "expected_left", "expected_right"),
    [(18, 27, 72), (24, 20, 80)],
    ids=["font size 18", "font size 24"],
)
def test_render_ink_trims_whitespace_at_both_ends(
    font_size,
    expected_left,
    expected_right,
):
    ink_rect = _centred_ink_rect(font_size, "  SPUD       ", TextHorizontalExtent.INK)

    assert ink_rect.left == expected_left
    assert ink_rect.right == expected_right


@pytest.mark.parametrize(
    ("font_size", "expected_left", "expected_right"),
    [(18, 26, 71), (24, 18, 78)],
    ids=["font size 18", "font size 24"],
)
def test_render_logical_honours_font_bearings(font_size, expected_left, expected_right):
    ink_rect = _centred_ink_rect(font_size, "SPUD", TextHorizontalExtent.LOGICAL)

    assert ink_rect.left == expected_left
    assert ink_rect.right == expected_right


@pytest.mark.parametrize(
    ("content", "expected_left", "expected_right"),
    [("  SPUD", 38, 83), ("SPUD   ", 26, 71)],
    ids=["leading whitespace", "trailing whitespace"],
)
def test_render_logical_counts_leading_and_hangs_trailing_whitespace(
    content,
    expected_left,
    expected_right,
):
    ink_rect = _centred_ink_rect(18, content, TextHorizontalExtent.LOGICAL)

    assert ink_rect.left == expected_left
    assert ink_rect.right == expected_right


def test_render_logical_width_comes_from_longest_line():
    ink_rect = _centred_ink_rect(18, "MY\nSPUD", TextHorizontalExtent.LOGICAL)

    assert ink_rect.left == 26
    assert ink_rect.right == 71


def test_render_draws_nothing_for_spaces_only():
    ink_rect = _centred_ink_rect(18, "       ", ANY_TEXT_HORIZONTAL_EXTENT)

    assert ink_rect.size == (0, 0)
    assert ink_rect.topleft == (50, 19)


# endregion


# region --- Anchors, margin, and offset --------------------------------------


def test_render_matches_text_anchor_to_text_parent_anchor():
    style = replace(
        DEFAULT_THEME.base_style,
        text_typeface=NEBMON0FONT_PATH,
        text_font_size=18,
        text_anchor=Anchor.TOP_LEFT,
        text_parent_anchor=Anchor.BOTTOM_RIGHT,
        text_horizontal_extent=ANY_TEXT_HORIZONTAL_EXTENT,
        text_margin=(0, 0),
        text_offset=(0, 0),
    )

    text = Text("SPUD")
    placed_image = text.render(WIDGET_SIZE, style)
    ink_rect = placed_image.image.get_bounding_rect().move(placed_image.pos)

    assert ink_rect.topleft == (100, 50)


@pytest.mark.parametrize(
    ("anchor", "text_horizontal_extent", "expected_topleft", "expected_bottomright"),
    [
        (Anchor.TOP_LEFT, TextHorizontalExtent.INK, (4, 6), (49, 18)),
        (Anchor.BOTTOM_RIGHT, TextHorizontalExtent.INK, (51, 32), (96, 44)),
        (Anchor.TOP_LEFT, TextHorizontalExtent.LOGICAL, (4, 6), (49, 18)),
        (Anchor.BOTTOM_RIGHT, TextHorizontalExtent.LOGICAL, (48, 32), (93, 44)),
    ],
    ids=[
        "top_left, ink",
        "bottom_right, ink",
        "top_left, logical",
        "bottom_right, logical",
    ],
)
def test_render_honours_margins_and_anchors(
    anchor,
    text_horizontal_extent,
    expected_topleft,
    expected_bottomright,
):
    style = replace(
        DEFAULT_THEME.base_style,
        text_typeface=NEBMON0FONT_PATH,
        text_font_size=18,
        text_anchor=anchor,
        text_parent_anchor=anchor,
        text_horizontal_extent=text_horizontal_extent,
        text_margin=(4, 6),
        text_offset=(0, 0),
    )

    text = Text("SPUD")
    placed_image = text.render(WIDGET_SIZE, style)
    ink_rect = placed_image.image.get_bounding_rect().move(placed_image.pos)

    assert ink_rect.topleft == expected_topleft
    assert ink_rect.bottomright == expected_bottomright


@pytest.mark.parametrize(
    ("text_horizontal_extent", "expected_ink_topleft"),
    [
        (TextHorizontalExtent.INK, (0, 0)),
        (TextHorizontalExtent.LOGICAL, (1, 0)),
    ],
    ids=["ink", "logical"],
)
def test_render_corrects_for_space_above_capitals_left_bearing(
    text_horizontal_extent,
    expected_ink_topleft,
):
    style = replace(
        DEFAULT_THEME.base_style,
        text_typeface=BundledTypeface.PYGAME_DEFAULT,
        text_font_size=18,
        text_anchor=Anchor.TOP_LEFT,
        text_parent_anchor=Anchor.TOP_LEFT,
        text_horizontal_extent=text_horizontal_extent,
        text_margin=(0, 0),
        text_offset=(0, 0),
    )

    text = Text("SPUD")
    placed_image = text.render(WIDGET_SIZE, style)
    ink_rect = placed_image.image.get_bounding_rect().move(placed_image.pos)

    assert ink_rect.topleft == expected_ink_topleft


# endregion


# region --- Colour and antialiasing ------------------------------------------


def test_render_honours_text_colour_alpha():
    text = Text("I")
    placed_image = text.render(
        (30, 30),
        replace(
            DEFAULT_THEME.base_style,
            text_colour=(0, 0, 0, 128),
            text_typeface=BundledTypeface.PYGAME_DEFAULT,
            text_font_size=20,
            text_anchor=Anchor.CENTRE,
            text_parent_anchor=Anchor.CENTRE,
            text_offset=(0, 0),
        ),
    )

    background_surface = pg.Surface((30, 30))

    background_surface.fill(WHITE)
    background_surface.blit(placed_image.image, placed_image.pos)

    # black rendered onto white at alpha = 128 should be grey
    assert background_surface.get_at((15, 15)) == (127, 127, 127, 255)


def test_render_does_not_antialias():
    text = Text("o")
    placed_image = text.render(
        (30, 30),
        replace(
            DEFAULT_THEME.base_style,
            text_colour=BLACK,
            text_typeface=BundledTypeface.PYGAME_DEFAULT,
            text_font_size=24,
            text_anchor=Anchor.CENTRE,
            text_parent_anchor=Anchor.CENTRE,
            text_offset=(0, 0),
        ),
    )

    background_surface = pg.Surface((30, 30))

    background_surface.fill(BLUE)
    background_surface.blit(placed_image.image, placed_image.pos)

    colours_present = {
        tuple(background_surface.get_at((x, y)))
        for x in range(background_surface.width)
        for y in range(background_surface.height)
    }

    assert colours_present == {BLUE, BLACK}


# endregion


# region --- Font loading -----------------------------------------------------


@pytest.mark.parametrize("bundled_typeface", [*BundledTypeface])
def test_render_all_bundled_fonts_create_non_zero_images(bundled_typeface):
    text = Text(ANY_STRING)
    image = text.render(
        (30, 40),
        replace(
            DEFAULT_THEME.base_style,
            text_typeface=bundled_typeface,
            text_font_size=12,
        ),
    ).image

    assert image.width != 0
    assert image.height != 0


def test_render_missing_path_raises(tmp_path):
    text = Text(ANY_STRING)
    style = replace(
        DEFAULT_THEME.base_style,
        text_typeface=tmp_path / "missing.ttf",
    )

    with pytest.raises(FileNotFoundError):
        text.render((30, 40), style)


def test_render_can_take_typeface_path():
    text = Text(ANY_STRING)

    image = text.render(
        (30, 40),
        replace(
            DEFAULT_THEME.base_style,
            text_typeface=NEBMON0FONT_PATH,
        ),
    ).image

    assert image.width != 0
    assert image.height != 0


# endregion
