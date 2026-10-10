from dataclasses import replace

import pygame as pg
import pytest

from puigame.components.skin import DrawnSkin, Skin, TransparentSkin
from puigame.core.state import State
from puigame.themes.theme import DEFAULT_THEME, FadeProfile, StyleOverride, Theme

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

# endregion

# region --- Skin -------------------------------------------------------------


def test_base_skin_instantiated_raises():
    with pytest.raises(TypeError):
        Skin()  # pyright: ignore[reportAbstractUsage]


# endregion

# region --- TransparentSkin --------------------------------------------------


@pytest.mark.parametrize(
    "size",
    [(0, 0), (1, 1), (100, 30), (30, 100), (1000, 1000)],
    ids=["empty", "tiny", "wide", "tall", "huge"],
)
@pytest.mark.parametrize("state", State.__members__.values())
def test_render_returns_requested_size(size, state):
    surface = TransparentSkin().render(size, state).image

    assert surface.get_size() == size


def test_surfaces_are_unique():
    skin = TransparentSkin()

    surface_1 = skin.render(ANY_SIZE, State.BASE).image
    surface_2 = skin.render(ANY_SIZE, State.BASE).image

    assert surface_1 is not surface_2


def test_surface_transparency():
    # bounding box gives rect covering visible area
    # if surface is fully transparent, then bounding box should be size 0.
    surface = TransparentSkin().render(ANY_SIZE, State.BASE).image
    bounding_box = surface.get_bounding_rect()

    assert bounding_box.size == (0, 0)


@pytest.mark.parametrize(
    "make_skin",
    [
        lambda: TransparentSkin(),
        lambda: DrawnSkin(
            Theme(
                replace(DEFAULT_THEME.base_style, halo_thickness_px=0, swell_px=0), {}
            )
        ),
    ],
    ids=["TransparentSkin", "DrawnSkin"],
)
@pytest.mark.parametrize(
    ("point", "expected_size"),
    [
        ((10, 20), (10, 20)),
        ([20, 30], (20, 30)),
        (pg.Vector2(4, 10), (4, 10)),
        (pg.Vector2(5.2, 7.9), (5, 7)),
    ],
    ids=["tuple", "list", "pg.Vector2", "truncated_pg.Vector2_float"],
)
def test_render_truncates_any_point_type(make_skin, point, expected_size):
    surface = make_skin().render(point, State.BASE).image

    assert surface.get_size() == expected_size


# endregion

# region --- DrawnSkin ------------------------------------------------------


@pytest.mark.parametrize("swell_px", [-2, 0, 2])
@pytest.mark.parametrize("halo_thickness_px", [0, 2])
def test_drawn_skin_correct_size_surface_for_all_swell_and_halo(
    swell_px,
    halo_thickness_px,
):
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                swell_px=swell_px,
                halo_thickness_px=halo_thickness_px,
            ),
            {},
        )
    )

    blit_offset_image = drawn_skin.render(ANY_SIZE, State.BASE)
    blit_offset = blit_offset_image.blit_offset
    surface_width, surface_height = blit_offset_image.image.get_size()

    assert blit_offset == (swell_px + halo_thickness_px, swell_px + halo_thickness_px)
    assert surface_width == ANY_SIZE[0] + (swell_px + halo_thickness_px) * 2
    assert surface_height == ANY_SIZE[1] + (swell_px + halo_thickness_px) * 2


def test_drawn_skin_pixel_colours():
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                body_colour=WHITE,
                border_colour=BLACK,
                border_thickness_px=2,
                corner_radius_px=3,
                halo_colour=BLUE,
                halo_fade_profile=FadeProfile.SOLID,
                halo_thickness_px=2,
                swell_px=1,
            ),
            {},
        )
    )

    surface = drawn_skin.render((10, 10), State.BASE).image

    assert surface.get_at((7, 7)) == WHITE  # centre
    assert surface.get_at((7, 3)) == BLACK  # border
    assert surface.get_at((7, 1)) == BLUE  # solid halo
    assert surface.get_at((0, 0)) == (0, 0, 0, 0)  # transparent given corner radius


def test_drawn_skin_body_size_can_be_zero():
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                border_thickness_px=2,
                swell_px=0,
            ),
            {},
        )
    )

    drawn_skin.render((4, 4), State.BASE)  # body is entirely subsumed by border


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
    ids=(
        "thick border",
        "negative swell",
        "combined border swell",
        "thick border low width",
        "negative swell low width",
        "combined border swell low width",
        "thick border low height",
        "negative swell low height",
        "combined border swell low height",
    ),
)
def test_drawn_skin_negative_body_size_raises(size, border_thickness_px, swell_px):
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                border_thickness_px=border_thickness_px,
                swell_px=swell_px,
            ),
            {},
        )
    )

    with pytest.raises(ValueError):
        drawn_skin.render(size, State.BASE)


@pytest.mark.parametrize(
    "halo_colour",
    [RED, BLUE, BLACK, WHITE],
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
)
def test_halo_fade_profiles_give_correct_colour_and_transparency(
    halo_colour, halo_fade_profile, alpha_values
):
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                corner_radius_px=0,
                halo_colour=halo_colour,
                halo_fade_profile=halo_fade_profile,
                halo_thickness_px=3,
                swell_px=0,
            ),
            {},
        )
    )

    surface = drawn_skin.render((10, 10), State.BASE).image

    assert surface.get_at((5, 0))[:3] == halo_colour[:3]  # all rings still blue
    assert surface.get_at((5, 1))[:3] == halo_colour[:3]
    assert surface.get_at((5, 2))[:3] == halo_colour[:3]

    assert surface.get_at((5, 2))[3] == alpha_values[0]  # no fade
    assert surface.get_at((5, 1))[3] == alpha_values[1]  # mid fade (apart from SOLID)
    assert surface.get_at((5, 0))[3] == alpha_values[2]  # most faded (apart from SOLID)


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
)
@pytest.mark.parametrize("swell_px", [-2, 0, 5])
def test_halo_fade_profile_is_not_affected_by_swell_px(
    halo_fade_profile,
    alpha_values,
    swell_px,
):
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                corner_radius_px=0,
                halo_colour=BLUE,
                halo_fade_profile=halo_fade_profile,
                halo_thickness_px=3,
                swell_px=swell_px,
            ),
            {},
        )
    )

    surface = drawn_skin.render((10, 10), State.BASE).image
    surface_center_x = surface.get_rect().centerx

    assert surface.get_at((surface_center_x, 2))[3] == alpha_values[0]  # no fade
    assert surface.get_at((surface_center_x, 1))[3] == alpha_values[1]  # middle fade
    assert surface.get_at((surface_center_x, 0))[3] == alpha_values[2]  # most faded


@pytest.mark.parametrize("halo_fade_profile", list(FadeProfile))
@pytest.mark.parametrize("halo_thickness_px", [0, 1, 2, 5])
def test_halo_fade_does_not_overlap_border(halo_fade_profile, halo_thickness_px):
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                border_colour=BLACK,
                border_thickness_px=1,
                corner_radius_px=0,
                halo_colour=BLUE,
                halo_fade_profile=halo_fade_profile,
                halo_thickness_px=halo_thickness_px,
            ),
            {},
        )
    )

    surface = drawn_skin.render((10, 10), State.BASE).image

    assert surface.get_at((5, halo_thickness_px)) == BLACK


def test_different_fade_profiles_give_same_shape():
    drawn_skin_1 = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                corner_radius_px=0,
                swell_px=-2,
                halo_colour=BLUE,
                halo_fade_profile=FadeProfile.SOLID,
                halo_thickness_px=3,
            ),
            {},
        )
    )

    drawn_skin_2 = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                corner_radius_px=0,
                swell_px=-2,
                halo_colour=BLUE,
                halo_fade_profile=FadeProfile.SOFT_QUADRATIC,
                halo_thickness_px=3,
            ),
            {},
        )
    )

    surface_1 = drawn_skin_1.render((10, 10), State.BASE).image
    surface_2 = drawn_skin_2.render((10, 10), State.BASE).image

    non_transparent_mask_1 = pg.mask.from_surface(surface_1, 0)
    non_transparent_mask_2 = pg.mask.from_surface(surface_2, 0)

    overlap_bits = non_transparent_mask_1.overlap_area(non_transparent_mask_2, (0, 0))
    assert non_transparent_mask_1.count() == overlap_bits
    assert non_transparent_mask_2.count() == overlap_bits


def test_render_state_change_returns_changed_surface():
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                body_colour=WHITE,
                border_thickness_px=1,
                corner_radius_px=1,
                halo_thickness_px=0,
            ),
            {State.DISABLED: StyleOverride(body_colour=BLUE)},
        )
    )

    base_state_surface = drawn_skin.render((10, 10), State.BASE).image
    disabled_state_surface = drawn_skin.render((10, 10), State.DISABLED).image

    assert base_state_surface.get_at((5, 5)) == WHITE
    assert disabled_state_surface.get_at((5, 5)) == BLUE


def test_render_instances_return_unique_surfaces():
    drawn_skin = DrawnSkin(DEFAULT_THEME)

    surface_1 = drawn_skin.render(ANY_SIZE, State.BASE).image
    surface_2 = drawn_skin.render(ANY_SIZE, State.BASE).image

    assert surface_1 is not surface_2


def test_oversize_radius_returns_pill_shape():
    drawn_skin_1 = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                body_colour=WHITE,
                border_thickness_px=0,
                corner_radius_px=5,
                swell_px=0,
                halo_thickness_px=0,
            ),
            {},
        )
    )

    drawn_skin_2 = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                body_colour=WHITE,
                border_thickness_px=0,
                corner_radius_px=1000,
                swell_px=0,
                halo_thickness_px=0,
            ),
            {},
        )
    )

    surface_1 = drawn_skin_1.render((20, 10), State.BASE).image
    surface_2 = drawn_skin_2.render((20, 10), State.BASE).image

    # check that image is a pill shape not a rectangle
    assert surface_1.get_at((0, 0))[3] == 0
    assert surface_2.get_at((0, 0))[3] == 0

    non_transparent_mask_1 = pg.mask.from_surface(surface_1, 0)
    non_transparent_mask_2 = pg.mask.from_surface(surface_2, 0)

    overlap_bits = non_transparent_mask_1.overlap_area(non_transparent_mask_2, (0, 0))
    assert non_transparent_mask_1.count() == overlap_bits
    assert non_transparent_mask_2.count() == overlap_bits


def test_negative_derived_corner_radius_gives_square_corner():
    drawn_skin = DrawnSkin(
        Theme(
            replace(
                DEFAULT_THEME.base_style,
                body_colour=WHITE,
                corner_radius_px=0,
                border_thickness_px=0,
                swell_px=-2,
                halo_thickness_px=0,
            ),
            {},
        )
    )

    surface = drawn_skin.render((10, 10), State.BASE).image

    assert surface.get_at((0, 0)) == WHITE


# endregion
