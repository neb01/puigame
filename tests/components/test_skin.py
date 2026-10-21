from dataclasses import replace

import pygame as pg
import pytest

from puigame.components.skin import DrawnSkin, NoSkin, Skin
from puigame.themes.theme import DEFAULT_THEME, FadeProfile

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)
ANY_STYLE = DEFAULT_THEME.base_style

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

# endregion


# region --- Skin contract ----------------------------------------------------


def test_base_skin_instantiated_raises():
    with pytest.raises(TypeError):
        Skin()  # pyright: ignore[reportAbstractUsage]


@pytest.mark.parametrize("make_skin", [DrawnSkin, NoSkin])
def test_rendered_surfaces_are_unique(make_skin):
    skin = make_skin()
    surface_1 = skin.render(ANY_SIZE, ANY_STYLE).image
    surface_2 = skin.render(ANY_SIZE, ANY_STYLE).image

    assert surface_1 is not surface_2


# endregion


# region --- NoSkin -----------------------------------------------------------


@pytest.mark.parametrize(
    "size",
    [
        (4, 4),
        (4, 10),
        (8, 4),
        (0.4, 0.5),
        pg.Vector2(2, 4),
        pg.Vector2(2.2, 4.9),
        [10, 4],
    ],
    ids=[
        "same height and width",
        "larger height",
        "larger width",
        "tuple of floats",
        "vec2 of ints",
        "vec2 of floats",
        "list",
    ],
)
def test_no_skin_always_returns_size_zero_surface(size):
    surface = NoSkin().render(size, ANY_STYLE).image

    assert surface.get_size() == (0, 0)


def test_no_skin_always_returns_zero_image_pos():
    image_pos = NoSkin().render(ANY_SIZE, ANY_STYLE).pos

    assert image_pos == (0, 0)


# endregion


# region --- DrawnSkin: size and offset ---------------------------------------


@pytest.mark.parametrize(
    ("point", "expected_size"),
    [
        ((10, 20), (10, 20)),
        ([20, 30], (20, 30)),
        (pg.Vector2(4, 10), (4, 10)),
        (pg.Vector2(5.2, 7.9), (5, 7)),
    ],
    ids=["tuple", "list", "pg.Vector2", "pg.Vector2 float"],
)
def test_drawn_skin_render_truncates_any_point_type(point, expected_size):
    # no halo, swell, or border, so DrawnSkin's surface is exactly the given size
    style = replace(
        ANY_STYLE,
        border_thickness_px=0,
        halo_thickness_px=0,
        swell_px=0,
    )

    surface = DrawnSkin().render(point, style).image

    assert surface.get_size() == expected_size


@pytest.mark.parametrize("swell_px", [-2, 0, 2])
@pytest.mark.parametrize("halo_thickness_px", [0, 2])
def test_drawn_skin_correct_size_surface_for_all_swell_and_halo(
    swell_px,
    halo_thickness_px,
):
    style = replace(
        ANY_STYLE,
        swell_px=swell_px,
        halo_thickness_px=halo_thickness_px,
    )

    placed_image = DrawnSkin().render((10, 10), style)
    image_pos = placed_image.pos
    surface_width, surface_height = placed_image.image.get_size()

    assert image_pos == (
        -swell_px - halo_thickness_px,
        -swell_px - halo_thickness_px,
    )
    assert surface_width == 10 + (swell_px + halo_thickness_px) * 2
    assert surface_height == 10 + (swell_px + halo_thickness_px) * 2


@pytest.mark.parametrize(
    "size",
    [(4, 4), (4, 10), (8, 4)],
    ids=["zero height and width", "zero width", "zero height"],
)
def test_drawn_skin_body_size_can_be_zero(size):
    style = replace(
        ANY_STYLE,
        border_thickness_px=2,
        swell_px=0,
    )

    DrawnSkin().render(size, style)  # body is 0 px on at least one axis: all border


@pytest.mark.parametrize(
    ("size", "border_thickness_px", "swell_px"),
    [
        ((2, 2), 3, 0),
        ((2, 2), 0, -3),
        ((2, 2), 1, -2),
        ((2, 10), 3, 0),
        ((2, 10), 0, -3),
        ((2, 10), 1, -2),
        ((10, 2), 3, 0),
        ((10, 2), 0, -3),
        ((10, 2), 1, -2),
    ],
    ids=[
        "thick border",
        "negative swell",
        "combined border swell",
        "thick border low width",
        "negative swell low width",
        "combined border swell low width",
        "thick border low height",
        "negative swell low height",
        "combined border swell low height",
    ],
)
def test_drawn_skin_negative_body_size_raises(size, border_thickness_px, swell_px):
    style = replace(
        ANY_STYLE,
        border_thickness_px=border_thickness_px,
        swell_px=swell_px,
    )

    with pytest.raises(ValueError):
        DrawnSkin().render(size, style)


# endregion


# region --- DrawnSkin: layers ------------------------------------------------


def test_drawn_skin_pixel_colours():
    style = replace(
        ANY_STYLE,
        body_colour=WHITE,
        border_colour=BLACK,
        border_thickness_px=2,
        corner_radius_px=3,
        halo_colour=BLUE,
        halo_fade_profile=FadeProfile.SOLID,
        halo_thickness_px=2,
        swell_px=1,
    )

    surface = DrawnSkin().render((10, 10), style).image

    assert surface.get_at((7, 7)) == WHITE  # centre
    assert surface.get_at((7, 3)) == BLACK  # border
    assert surface.get_at((7, 1)) == BLUE  # solid halo
    assert surface.get_at((0, 0)) == (0, 0, 0, 0)  # outside the rounded halo


@pytest.mark.parametrize("halo_fade_profile", FadeProfile)
@pytest.mark.parametrize("halo_thickness_px", [0, 1, 2, 5])
def test_drawn_skin_halo_fade_does_not_overlap_border(
    halo_fade_profile, halo_thickness_px
):
    style = replace(
        ANY_STYLE,
        border_colour=BLACK,
        border_thickness_px=1,
        corner_radius_px=0,
        halo_colour=BLUE,
        halo_fade_profile=halo_fade_profile,
        halo_thickness_px=halo_thickness_px,
        swell_px=0,
    )

    surface = DrawnSkin().render((10, 10), style).image

    # the first row inside the halo is border, whatever the fade profile
    assert surface.get_at((5, halo_thickness_px)) == BLACK


# endregion


# region --- DrawnSkin: halo fade ---------------------------------------------


@pytest.mark.parametrize(
    "halo_colour", [RED, BLUE, BLACK, WHITE], ids=["red", "blue", "black", "white"]
)
@pytest.mark.parametrize(
    ("halo_fade_profile", "alpha_values"),
    [
        (FadeProfile.SOLID, (255, 255, 255)),
        (FadeProfile.LINEAR, (255, 170, 85)),
        (FadeProfile.SOFT_QUADRATIC, (255, 113, 28)),
        (FadeProfile.HARD_QUADRATIC, (255, 227, 142)),
        (FadeProfile.SOFT_CUBIC, (255, 76, 9)),
        (FadeProfile.HARD_CUBIC, (255, 246, 179)),
    ],
    ids=[
        "solid",
        "linear",
        "soft quadratic",
        "hard quadratic",
        "soft cubic",
        "hard cubic",
    ],
)
def test_drawn_skin_halo_fade_profiles_give_correct_colour_and_transparency(
    halo_colour, halo_fade_profile, alpha_values
):
    style = replace(
        ANY_STYLE,
        corner_radius_px=0,
        halo_colour=halo_colour,
        halo_fade_profile=halo_fade_profile,
        halo_thickness_px=3,
        swell_px=0,
    )

    surface = DrawnSkin().render((10, 10), style).image

    # every ring keeps the halo colour's RGB; only the alpha fades
    assert surface.get_at((5, 0))[:3] == halo_colour[:3]
    assert surface.get_at((5, 1))[:3] == halo_colour[:3]
    assert surface.get_at((5, 2))[:3] == halo_colour[:3]

    assert surface.get_at((5, 2))[3] == alpha_values[0]  # no fade
    assert surface.get_at((5, 1))[3] == alpha_values[1]  # middle fade (none for SOLID)
    assert surface.get_at((5, 0))[3] == alpha_values[2]  # most faded (none for SOLID)


@pytest.mark.parametrize(
    ("halo_fade_profile", "alpha_values"),
    [
        (FadeProfile.SOLID, (255, 255, 255)),
        (FadeProfile.LINEAR, (255, 170, 85)),
        (FadeProfile.SOFT_QUADRATIC, (255, 113, 28)),
        (FadeProfile.HARD_QUADRATIC, (255, 227, 142)),
        (FadeProfile.SOFT_CUBIC, (255, 76, 9)),
        (FadeProfile.HARD_CUBIC, (255, 246, 179)),
    ],
    ids=[
        "solid",
        "linear",
        "soft quadratic",
        "hard quadratic",
        "soft cubic",
        "hard cubic",
    ],
)
@pytest.mark.parametrize("swell_px", [-2, 0, 5])
def test_drawn_skin_halo_fade_profile_is_not_affected_by_swell_px(
    halo_fade_profile,
    alpha_values,
    swell_px,
):
    style = replace(
        ANY_STYLE,
        corner_radius_px=0,
        halo_colour=BLUE,
        halo_fade_profile=halo_fade_profile,
        halo_thickness_px=3,
        swell_px=swell_px,
    )

    surface = DrawnSkin().render((10, 10), style).image
    surface_centre_x = surface.get_rect().centerx

    assert surface.get_at((surface_centre_x, 2))[3] == alpha_values[0]  # no fade
    assert surface.get_at((surface_centre_x, 1))[3] == alpha_values[1]  # middle fade
    assert surface.get_at((surface_centre_x, 0))[3] == alpha_values[2]  # most faded


def test_drawn_skin_different_fade_profiles_give_same_shape():
    style_1 = replace(
        ANY_STYLE,
        corner_radius_px=0,
        swell_px=-2,
        halo_colour=BLUE,
        halo_fade_profile=FadeProfile.SOLID,
        halo_thickness_px=3,
    )

    style_2 = replace(
        ANY_STYLE,
        corner_radius_px=0,
        swell_px=-2,
        halo_colour=BLUE,
        halo_fade_profile=FadeProfile.SOFT_QUADRATIC,
        halo_thickness_px=3,
    )

    surface_1 = DrawnSkin().render((10, 10), style_1).image
    surface_2 = DrawnSkin().render((10, 10), style_2).image

    # the fade changes only alpha, so the non-transparent pixels match
    non_transparent_mask_1 = pg.mask.from_surface(surface_1, 0)
    non_transparent_mask_2 = pg.mask.from_surface(surface_2, 0)

    overlap_bits = non_transparent_mask_1.overlap_area(non_transparent_mask_2, (0, 0))
    assert non_transparent_mask_1.count() == overlap_bits
    assert non_transparent_mask_2.count() == overlap_bits


# endregion


# region --- DrawnSkin: corner radius -----------------------------------------


def test_drawn_skin_oversize_radius_returns_pill_shape():
    style_1 = replace(
        ANY_STYLE,
        body_colour=WHITE,
        border_thickness_px=0,
        corner_radius_px=5,
        swell_px=0,
        halo_thickness_px=0,
    )
    style_2 = replace(
        ANY_STYLE,
        body_colour=WHITE,
        border_thickness_px=0,
        corner_radius_px=1000,
        swell_px=0,
        halo_thickness_px=0,
    )

    surface_1 = DrawnSkin().render((20, 10), style_1).image
    surface_2 = DrawnSkin().render((20, 10), style_2).image

    # corners are transparent, so both shapes are rounded, not rectangles
    assert surface_1.get_at((0, 0))[3] == 0
    assert surface_2.get_at((0, 0))[3] == 0

    # radius 1000 is clamped to 5, half the shorter side, so both give the
    # same pill
    non_transparent_mask_1 = pg.mask.from_surface(surface_1, 0)
    non_transparent_mask_2 = pg.mask.from_surface(surface_2, 0)

    overlap_bits = non_transparent_mask_1.overlap_area(non_transparent_mask_2, (0, 0))
    assert non_transparent_mask_1.count() == overlap_bits
    assert non_transparent_mask_2.count() == overlap_bits


def test_drawn_skin_negative_derived_corner_radius_gives_square_corner():
    style = replace(
        ANY_STYLE,
        body_colour=WHITE,
        corner_radius_px=0,
        border_thickness_px=0,
        swell_px=-2,
        halo_thickness_px=0,
    )

    surface = DrawnSkin().render((10, 10), style).image

    # a swell of -2 makes the derived radius -2, which is clamped to 0
    assert surface.get_at((0, 0)) == WHITE


# endregion
