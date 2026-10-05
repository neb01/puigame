import pygame as pg
import pytest

from puigame.core.anchor import Anchor
from puigame.core.widget import Widget

ANY_SIZE = (10, 10)


@pytest.fixture
def family():
    """Return <Parent : Child : Grandchild> widgets in that order."""
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)
    grandchild = Widget(ANY_SIZE, parent=child)

    return parent, child, grandchild


def test_rect_has_given_size_at_origin():
    widget = Widget(ANY_SIZE)

    assert widget.rect.size == ANY_SIZE
    assert widget.rect.topleft == (0, 0)


@pytest.mark.parametrize(
    ("margin_values", "expected_vector"),
    [
        (1.0, pg.Vector2(1.0, 1.0)),
        ((1.0, 2.0), pg.Vector2(1.0, 2.0)),
        ([2.0, 3.0], pg.Vector2(2.0, 3.0)),
        (pg.Vector2(4.0, 2.0), pg.Vector2(4.0, 2.0)),
    ],
    ids=["single_float", "tuple", "list", "pg.Vector2"],
)
def test_margin_converts_to_vec2_on_correct_axes(margin_values, expected_vector):
    widget = Widget(ANY_SIZE, margin=margin_values)

    assert isinstance(widget.margin, pg.Vector2)
    assert widget.margin == expected_vector


@pytest.mark.parametrize(
    ("offset_values", "expected_vector"),
    [
        (1.0, pg.Vector2(1.0, 1.0)),
        ((1.0, 2.0), pg.Vector2(1.0, 2.0)),
        ([2.0, 3.0], pg.Vector2(2.0, 3.0)),
        (pg.Vector2(4.0, 2.0), pg.Vector2(4.0, 2.0)),
    ],
    ids=["single_float", "tuple", "list", "pg.Vector2"],
)
def test_offset_converts_to_vec2_on_correct_axes(offset_values, expected_vector):
    widget = Widget(ANY_SIZE, offset=offset_values)

    assert isinstance(widget.offset, pg.Vector2)
    assert widget.offset == expected_vector


@pytest.mark.parametrize("offset_values", [1, 2.0])
def test_offset_rejects_single_value(offset_value):
    with pytest.raises(TypeError):
        Widget(ANY_SIZE, offset=offset_value)


@pytest.mark.parametrize("anchor", Anchor)
def test_parent_anchor_defaults_to_anchor(anchor):
    widget = Widget(ANY_SIZE, anchor=anchor)

    assert widget.parent_anchor is anchor


def test_assigning_to_rect_raises():
    widget = Widget(ANY_SIZE)

    with pytest.raises(AttributeError):
        widget.rect = pg.Rect(1, 1, 1, 1)


def test_rect_can_change_in_place():
    widget = Widget(ANY_SIZE)
    original_rect = widget.rect

    widget.rect.topleft = (1, 1)

    assert widget.rect is original_rect
    assert widget.rect.topleft == (1, 1)

    widget.rect.x += 1

    assert widget.rect is original_rect
    assert widget.rect.topleft == (2, 1)
