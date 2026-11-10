from dataclasses import replace

import pygame as pg

from puigame import (
    UI,
    Anchor,
    BundledTypeface,
    DrawnSkin,
    FadeProfile,
    NoSkin,
    State,
    Style,
    StyleOverride,
    TextAlign,
    TextHorizontalExtent,
    Theme,
    Widget,
)
from stubs import FixedLayer

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)
ANY_SKIN = NoSkin()

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
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
    text_align=TextAlign.LEFT,
    text_horizontal_extent=TextHorizontalExtent.INK,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

ANY_THEME = Theme(base_style=ANY_STYLE, style_overrides={})

# endregion


# region --- update() ---------------------------------------------------------


def test_update_applies_root_offset_to_descendants():
    ui = UI(size=(10, 20), theme=ANY_THEME)
    parent = Widget(
        ui.root,
        size=(3, 5),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(1, 3),
    )

    child = Widget(
        parent,
        size=(1, 2),
        skin=ANY_SKIN,
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_RIGHT,
        margin=(0, 0),
        offset=(-1, 0),
    )

    assert parent.rect.topleft == (1, 3)
    assert child.rect.topleft == (2, 6)

    ui.root.offset = (1, -2)
    ui.update()

    assert parent.rect.topleft == (2, 1)
    assert child.rect.topleft == (3, 4)


def test_update_refreshes_widget_image():
    surface = pg.Surface((10, 20), pg.SRCALPHA)

    ui = UI(
        size=(10, 20),
        theme=Theme(
            base_style=replace(
                ANY_STYLE,
                body_colour=BLUE,
                border_thickness=0,
                corner_radius=0,
                halo_thickness=0,
                swell=0,
            ),
            style_overrides={State.DISABLED: StyleOverride(body_colour=RED)},
        ),
    )

    widget = Widget(
        ui.root,
        size=(3, 5),
        skin=DrawnSkin(),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    ui.update()
    ui.draw(surface)

    assert surface.get_at((0, 0)) == BLUE

    widget.enabled = False
    ui.draw(surface)

    # setters only store; update() applies the change
    assert surface.get_at((0, 0)) == BLUE

    ui.update()
    ui.draw(surface)

    assert surface.get_at((0, 0)) == RED


# endregion


# region --- draw() -----------------------------------------------------------


def test_draw_uses_widget_image_pos():
    surface = pg.Surface((10, 20), pg.SRCALPHA)
    ui = UI(size=(10, 20), theme=ANY_THEME)

    Widget(
        ui.root,
        size=(3, 5),
        skin=FixedLayer(size=(3, 5), colour=BLUE, pos=(-2, -1)),
        anchor=Anchor.BOTTOM_RIGHT,
        parent_anchor=Anchor.BOTTOM_RIGHT,
        margin=(0, 0),
        offset=(0, 0),
    )

    ui.update()
    ui.draw(surface)
    drawn_non_transparent_mask = pg.mask.from_surface(surface, 0)

    expected_surface = pg.Surface((10, 20), pg.SRCALPHA)
    expected_surface.fill(BLUE, ((5, 14), (3, 5)))
    expected_non_transparent_mask = pg.mask.from_surface(expected_surface, 0)

    overlap_bits = expected_non_transparent_mask.overlap_area(
        drawn_non_transparent_mask,
        (0, 0),
    )
    assert drawn_non_transparent_mask.count() == overlap_bits
    assert expected_non_transparent_mask.count() == overlap_bits


def test_draw_skips_hidden_subtree():
    surface = pg.Surface((10, 20), pg.SRCALPHA)
    surface.fill(WHITE)
    ui = UI(size=(10, 20), theme=ANY_THEME)

    parent_1 = Widget(
        ui.root,
        size=ANY_SIZE,
        skin=FixedLayer(size=(1, 2), colour=BLUE, pos=(0, 0)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        visible=True,
    )
    parent_2 = Widget(
        ui.root,
        size=ANY_SIZE,
        skin=FixedLayer(size=(1, 2), colour=BLUE, pos=(5, 6)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        visible=False,
    )

    Widget(
        parent_1,
        size=ANY_SIZE,
        skin=FixedLayer(size=(1, 2), colour=RED, pos=(0, 0)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        visible=False,
    )

    Widget(
        parent_2,
        size=ANY_SIZE,
        skin=FixedLayer(size=(1, 2), colour=RED, pos=(5, 6)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        visible=True,
    )

    ui.update()
    ui.draw(surface)

    assert surface.get_at((0, 0)) == BLUE
    assert surface.get_at((5, 6)) == WHITE


def test_draw_blits_siblings_in_order():
    surface = pg.Surface((10, 20), pg.SRCALPHA)
    surface.fill(WHITE)
    ui = UI(size=(10, 20), theme=ANY_THEME)

    parent_1 = Widget(
        ui.root,
        size=ANY_SIZE,
        skin=FixedLayer(size=(3, 2), colour=BLUE, pos=(0, 0)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    Widget(
        parent_1,
        size=ANY_SIZE,
        skin=FixedLayer(size=(3, 2), colour=RED, pos=(1, 0)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )
    Widget(
        ui.root,
        size=ANY_SIZE,
        skin=FixedLayer(size=(3, 2), colour=WHITE, pos=(0, 1)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    ui.update()
    ui.draw(surface)

    assert surface.get_at((0, 0)) == BLUE
    assert surface.get_at((1, 0)) == RED
    assert surface.get_at((0, 1)) == WHITE
    assert surface.get_at((1, 1)) == WHITE


# endregion
