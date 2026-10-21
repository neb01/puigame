import pygame as pg

from puigame.components.placed_image import PlacedImage, compose_layers

# region --- Constants --------------------------------------------------------

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)

# endregion


# region --- Helpers ----------------------------------------------------------


def _layer(size: tuple[int, int], pos: tuple[int, int]) -> PlacedImage:
    return PlacedImage(pg.Surface(size, pg.SRCALPHA), pos)


def _zero_size_layer(pos: tuple[int, int]) -> PlacedImage:
    return PlacedImage(pg.Surface((0, 0), pg.SRCALPHA), pos)


def _filled_layer(
    size: tuple[int, int],
    colour: tuple[int, int, int, int],
    pos: tuple[int, int],
) -> PlacedImage:
    surface = pg.Surface(size, pg.SRCALPHA)
    surface.fill(color=colour)

    return PlacedImage(surface, pos)


# endregion


# region --- Zero-size layers -------------------------------------------------


def test_compose_returns_0x0_at_origin_for_no_layers():
    layer = compose_layers([])

    assert layer.image.size == (0, 0)
    assert layer.pos == (0, 0)


def test_compose_returns_0x0_at_origin_for_all_zero_size_layers():
    zero_size_layer_1 = _zero_size_layer((1, 2))
    zero_size_layer_2 = _zero_size_layer((10, 20))
    zero_size_layer_3 = _zero_size_layer((-4, -6))

    composition = compose_layers(
        [
            zero_size_layer_1,
            zero_size_layer_2,
            zero_size_layer_3,
        ]
    )

    assert composition.image.size == (0, 0)
    assert composition.pos == (0, 0)


def test_compose_returns_only_non_zero_layer_itself():
    zero_size_layer_1 = _zero_size_layer((0, 0))
    zero_size_layer_2 = _zero_size_layer((0, 0))
    zero_size_layer_3 = _zero_size_layer((0, 0))
    layer_1 = _layer((10, 10), (0, 0))

    composition = compose_layers(
        [
            zero_size_layer_1,
            zero_size_layer_2,
            zero_size_layer_3,
            layer_1,
        ]
    )

    assert composition is layer_1


def test_compose_ignores_zero_size_layers():
    layer_1 = _filled_layer((5, 3), RED, (0, 0))
    layer_2 = _filled_layer((10, 15), BLUE, (5, 5))
    zero_size_layer_1 = _zero_size_layer((30, 50))
    zero_size_layer_2 = _zero_size_layer((-40, 20))
    zero_size_layer_3 = _zero_size_layer((40, -20))
    zero_axis_layer_1 = _layer((0, 10), (-20, 0))
    zero_axis_layer_2 = _layer((10, 0), (-30, 0))

    composition = compose_layers(
        [
            layer_1,
            zero_size_layer_1,
            zero_size_layer_2,
            zero_size_layer_3,
            zero_axis_layer_1,
            zero_axis_layer_2,
            layer_2,
        ]
    )

    assert composition.image.size == (15, 20)
    assert composition.pos == (0, 0)


# endregion


# region --- Union ------------------------------------------------------------


def test_compose_sizes_image_to_union_of_layers():
    layer_1 = _layer((10, 10), (0, 0))
    layer_2 = _layer((20, 20), (-10, -5))
    layer_3 = _layer((30, 40), (35, 40))

    composition = compose_layers([layer_1, layer_2, layer_3])

    assert composition.image.size == (75, 85)
    assert composition.pos == (-10, -5)


# endregion


# region --- Pixels -----------------------------------------------------------


def test_compose_assigns_layers_to_given_positions():
    layer_1 = _filled_layer((10, 15), RED, (-5, -20))
    layer_2 = _filled_layer((10, 120), BLUE, (5, 15))

    composition = compose_layers([layer_1, layer_2])

    assert composition.image.get_at((0, 0)) == RED
    assert composition.image.get_at((19, 154)) == BLUE


def test_compose_blits_layers_in_given_order():
    layer_1 = _filled_layer((10, 10), RED, (0, 0))
    layer_2 = _filled_layer((10, 10), BLUE, (5, 5))

    composition = compose_layers([layer_1, layer_2])

    assert composition.image.get_at((5, 5)) == BLUE


def test_compose_leaves_gaps_between_layers_transparent():
    layer_1 = _filled_layer((5, 5), RED, (0, 0))
    layer_2 = _filled_layer((5, 5), BLUE, (20, 20))

    composition = compose_layers([layer_1, layer_2])

    assert composition.image.get_at((10, 10))[3] == 0


# endregion


# region --- Inputs -----------------------------------------------------------


def test_compose_accepts_any_iterable():
    layer_1 = _filled_layer((5, 10), RED, (0, 0))
    layer_2 = _filled_layer((15, 10), BLUE, (5, 6))

    composition = compose_layers(iter([layer_1, layer_2]))

    assert composition.image.size == (20, 16)
    assert composition.pos == (0, 0)


def test_compose_leaves_inputs_unchanged():
    layer_1 = _filled_layer((5, 5), RED, (0, 0))
    layer_2 = _filled_layer((10, 10), BLUE, (0, 0))

    compose_layers([layer_1, layer_2])

    assert layer_1.image.get_at((0, 0)) == RED


# endregion
