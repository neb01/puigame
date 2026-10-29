from dataclasses import replace

import pygame as pg

from puigame import (
    DEFAULT_THEME,
    UI,
    Anchor,
    DrawnSkin,
    NoSkin,
    State,
    StyleOverride,
    Theme,
    Widget,
)
from stubs import FixedLayer

# region --- Constants --------------------------------------------------------

ANY_SIZE = (10, 10)
ANY_SKIN = NoSkin()
ANY_THEME = DEFAULT_THEME

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
WHITE = (255, 255, 255, 255)

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
                DEFAULT_THEME.base_style,
                body_colour=BLUE,
                border_thickness_px=0,
                corner_radius_px=0,
                halo_thickness_px=0,
                swell_px=0,
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
    )
    parent_2 = Widget(
        ui.root,
        size=ANY_SIZE,
        skin=FixedLayer(size=(1, 2), colour=BLUE, pos=(5, 6)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    child_1 = Widget(
        parent_1,
        size=ANY_SIZE,
        skin=FixedLayer(size=(1, 2), colour=RED, pos=(0, 0)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    Widget(
        parent_2,
        size=ANY_SIZE,
        skin=FixedLayer(size=(1, 2), colour=RED, pos=(5, 6)),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    parent_2.visible = False
    child_1.visible = False

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
