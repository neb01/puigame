import pygame as pg
import pytest

from puigame.core.anchor import Anchor, get_pos_from_anchor_match

# region --- Margin sign ------------------------------------------------------


@pytest.mark.parametrize(
    ("anchor", "margin_sign"),
    [
        (Anchor.CENTRE, pg.Vector2(0, 0)),
        (Anchor.TOP_LEFT, pg.Vector2(1, 1)),
        (Anchor.TOP_RIGHT, pg.Vector2(-1, 1)),
        (Anchor.BOTTOM_LEFT, pg.Vector2(1, -1)),
        (Anchor.BOTTOM_RIGHT, pg.Vector2(-1, -1)),
        (Anchor.MID_LEFT, pg.Vector2(1, 0)),
        (Anchor.MID_RIGHT, pg.Vector2(-1, 0)),
        (Anchor.MID_TOP, pg.Vector2(0, 1)),
        (Anchor.MID_BOTTOM, pg.Vector2(0, -1)),
    ],
)
def test_margin_sign_points_from_anchor_toward_centre(anchor, margin_sign):
    assert anchor.margin_sign == margin_sign


# endregion


# region --- New vectors ------------------------------------------------------


@pytest.mark.parametrize("property_name", ["margin_sign", "fractional_pos"])
def test_anchor_properties_return_new_vector(property_name):
    original_vector = getattr(Anchor.MID_BOTTOM, property_name).copy()

    mutated_vector = getattr(Anchor.MID_BOTTOM, property_name)
    mutated_vector.x += 2

    assert getattr(Anchor.MID_BOTTOM, property_name) == original_vector


# endregion


# region --- Matching anchors -------------------------------------------------


def test_get_pos_from_anchor_match_defaults_parent_anchor_to_child_anchor():
    child_size = (10, 20)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.BOTTOM_RIGHT,
        parent_size=parent_size,
        margin=(0, 0),
        offset=(0, 0),
    )

    assert child_pos == (90, 180)


@pytest.mark.parametrize(
    ("anchor", "expected_child_pos"),
    [
        (Anchor.TOP_LEFT, (0, 0)),
        (Anchor.TOP_RIGHT, (90, 0)),
        (Anchor.BOTTOM_LEFT, (0, 180)),
        (Anchor.BOTTOM_RIGHT, (90, 180)),
        (Anchor.CENTRE, (45, 90)),
        (Anchor.MID_LEFT, (0, 90)),
        (Anchor.MID_RIGHT, (90, 90)),
        (Anchor.MID_TOP, (45, 0)),
        (Anchor.MID_BOTTOM, (45, 180)),
    ],
)
def test_get_pos_from_anchor_match_puts_child_anchor_on_matching_parent_anchor(
    anchor,
    expected_child_pos,
):
    child_size = (10, 20)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=anchor,
        parent_size=parent_size,
        parent_anchor=anchor,
        margin=(0, 0),
        offset=(0, 0),
    )

    assert child_pos == expected_child_pos


# endregion


# region --- Mixed anchors ----------------------------------------------------


def test_get_pos_from_anchor_match_puts_child_anchor_on_given_parent_anchor():
    child_size = (10, 20)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.TOP_RIGHT,
        parent_size=parent_size,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    assert child_pos == (-10, 200)


# endregion


# region --- Margin -----------------------------------------------------------


def test_get_pos_from_anchor_match_moves_matching_anchors_inwards_with_margin():
    child_size = (10, 20)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.BOTTOM_RIGHT,
        parent_size=parent_size,
        margin=(3, 4),
        offset=(0, 0),
    )

    assert child_pos == (87, 176)


def test_get_pos_from_anchor_match_moves_opposite_anchors_outwards_with_margin():
    child_size = (10, 20)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.TOP_LEFT,
        parent_size=parent_size,
        parent_anchor=Anchor.BOTTOM_RIGHT,
        margin=(3, 4),
        offset=(0, 0),
    )

    assert child_pos == (103, 204)


@pytest.mark.parametrize(
    ("anchor", "expected_child_pos"),
    [
        (Anchor.MID_TOP, (45, 4)),
        (Anchor.MID_LEFT, (3, 90)),
    ],
)
def test_get_pos_from_anchor_match_ignores_margin_on_central_axis(
    anchor,
    expected_child_pos,
):
    child_size = (10, 20)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=anchor,
        parent_size=parent_size,
        margin=(3, 4),
        offset=(0, 0),
    )

    assert child_pos == expected_child_pos


# endregion


# region --- Offset -----------------------------------------------------------


def test_get_pos_from_anchor_match_never_flips_offset_sign():
    child_size = (10, 20)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.BOTTOM_RIGHT,
        parent_size=parent_size,
        margin=(0, 0),
        offset=(3, 4),
    )

    assert child_pos == (93, 184)


# endregion


# region --- Rounding ---------------------------------------------------------


def test_get_pos_from_anchor_match_rounds_down_odd_sizes_at_centre():
    child_size = (11, 21)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.CENTRE,
        parent_size=parent_size,
        margin=(0, 0),
        offset=(0, 0),
    )

    assert child_pos == (44, 89)


def test_get_pos_from_anchor_match_rounds_negatives_down_not_towards_zero():
    child_size = (11, 21)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.CENTRE,
        parent_size=parent_size,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
    )

    assert child_pos == (-6, -11)


def test_get_pos_from_anchor_match_only_rounds_once():
    child_size = (11, 21)
    parent_size = (100, 200)

    child_pos = get_pos_from_anchor_match(
        child_size=child_size,
        child_anchor=Anchor.CENTRE,
        parent_size=parent_size,
        margin=(0, 0),
        offset=(0.5, 0.5),
    )

    assert child_pos == (45, 90)


# endregion
