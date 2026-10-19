from dataclasses import replace
from pathlib import Path

import pygame as pg
import pytest

from puigame.components.text import Text
from puigame.core.anchor import Anchor
from puigame.themes.theme import DEFAULT_THEME, BundledTypeface

# region --- Constants --------------------------------------------------------

ANY_STRING = "snath is the specific word for the handle of a scythe"
ANY_FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "neb0font.ttf"

WHITE = (255, 255, 255, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)

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

    assert placed_image.image.get_size() == (0, 0)
    assert placed_image.pos == (0, 0)


# endregion


# region --- Position ---------------------------------------------------------


def test_render_pos_adds_style_margin_and_offset():
    text = Text(ANY_STRING)
    pos = text.render(
        (30, 40),
        replace(
            DEFAULT_THEME.base_style,
            text_anchor=Anchor.TOP_LEFT,
            text_parent_anchor=Anchor.TOP_LEFT,
            text_margin=(2, 4),
            text_offset=(-5, 5),
        ),
    ).pos

    expected_pos = (2 - 5, 4 + 5)

    assert pos == expected_pos


def test_render_pos_adds_style_margin_in_negative_direction():
    text = Text(ANY_STRING)
    placed_image = text.render(
        (30, 40),
        replace(
            DEFAULT_THEME.base_style,
            text_anchor=Anchor.BOTTOM_RIGHT,
            text_parent_anchor=Anchor.BOTTOM_RIGHT,
            text_margin=(4, 6),
            text_offset=(0, 0),
        ),
    )

    expected_bottom_right = (30 - 4, 40 - 6)
    image_rect = pg.Rect(placed_image.pos, placed_image.image.get_size())

    assert image_rect.width != 0
    assert image_rect.height != 0
    assert image_rect.bottomright == expected_bottom_right


def test_render_pos_matches_text_anchor_to_text_parent_anchor():
    text = Text(ANY_STRING)
    pos = text.render(
        (30, 40),
        replace(
            DEFAULT_THEME.base_style,
            text_anchor=Anchor.TOP_LEFT,
            text_parent_anchor=Anchor.BOTTOM_RIGHT,
            text_margin=(0, 0),
            text_offset=(0, 0),
        ),
    ).pos

    expected_pos = (30, 40)

    assert pos == expected_pos


# endregion


# region --- Colour and antialiasing ------------------------------------------


def test_render_honours_text_colour_alpha():
    text = Text("I")
    placed_image = text.render(
        (30, 30),
        replace(
            DEFAULT_THEME.base_style,
            text_colour=(0, 0, 0, 128),
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
            text_typeface=ANY_FONT_PATH,
        ),
    ).image

    assert image.width != 0
    assert image.height != 0


# endregion
