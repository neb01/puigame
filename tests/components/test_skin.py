import pygame as pg
import pytest

from puigame.components.skin import Skin, TransparentSkin
from puigame.core.state import State

ANY_SIZE = (10, 10)


def test_base_skin_instantiated_raises():
    with pytest.raises(TypeError):
        Skin()  # pyright: ignore[reportAbstractUsage]


@pytest.mark.parametrize(
    "size",
    [(0, 0), (1, 1), (100, 30), (30, 100), (1000, 1000)],
    ids=["empty", "tiny", "wide", "tall", "huge"],
)
@pytest.mark.parametrize("state", State.__members__.values())
def test_render_returns_requested_size(size, state):
    surface = TransparentSkin().render(size, state)

    assert surface.get_size() == size


def test_surfaces_are_unique():
    skin = TransparentSkin()

    surface_1 = skin.render(ANY_SIZE, State.BASE)
    surface_2 = skin.render(ANY_SIZE, State.BASE)

    assert surface_1 is not surface_2


def test_surface_transparency():
    # bounding box gives rect covering visible area
    # if surface is fully transparent, then bounding box should be size 0.
    surface = TransparentSkin().render(ANY_SIZE, State.BASE)
    bounding_box = surface.get_bounding_rect()

    assert bounding_box.size == (0, 0)


@pytest.mark.parametrize(
    ("point", "expected_size"),
    [
        ((10, 20), (10, 20)),
        ([20, 30], (20, 30)),
        (pg.Vector2(4, 10), (4, 10)),
        (pg.Vector2(5.2, 7.9), (5, 10)),
    ],
    ids=["tuple", "list", "pg.Vector2", "truncated_pg.Vector2_float"],
)
def test_size_can_be_any_point_type(point, expected_size):
    surface = TransparentSkin().render(point, State.BASE)

    assert surface.get_size() == expected_size
