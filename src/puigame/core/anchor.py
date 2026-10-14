"""Anchor, the named points on a rect, and positioning one rect in another by them."""

import math
from enum import Enum, unique

import pygame as pg
from pygame.typing import Point


@unique
class Anchor(Enum):
    """Nine named points on a rect, used to position widgets and their content.

    Each value is the point's position as a fraction of the rect's size, per
    axis, measured from the rect's top-left corner: ``(0, 0)`` is the top-left
    corner, ``(1, 1)`` the bottom-right corner, and ``(0.5, 0.5)`` the centre.
    As in pygame, ``+x`` is to the right and ``+y`` is down.
    """

    CENTRE = (0.5, 0.5)
    TOP_LEFT = (0, 0)
    TOP_RIGHT = (1, 0)
    BOTTOM_LEFT = (0, 1)
    BOTTOM_RIGHT = (1, 1)
    MID_LEFT = (0, 0.5)
    MID_RIGHT = (1, 0.5)
    MID_TOP = (0.5, 0)
    MID_BOTTOM = (0.5, 1)

    @property
    def fractional_pos(self) -> pg.Vector2:
        """The anchor's position as a fraction of the rect's size, per axis.

        Measured from the rect's top-left corner, so multiplying by a rect's
        size gives the anchor's position in pixels within that rect. Returns a
        new vector each time, so changing it does not change the anchor.
        """
        return pg.Vector2(self.value)

    @property
    def margin_sign(self) -> pg.Vector2:
        """The sign of each axis from the anchor towards the rect's centre.

        Each component is -1, 0, or +1, so multiplying a margin by it moves a
        positive margin inwards, from the anchor towards the centre, by exactly
        the margin in each axis. A component is 0 on an axis where the anchor
        is already central, so the margin has no effect on that axis. Returns a
        new vector each time.
        """
        return (pg.Vector2(0.5, 0.5) - self.fractional_pos) * 2


def _get_anchor_pos_in_rect_coords(size: Point, anchor: Anchor) -> pg.Vector2:
    """Return the position of an anchor within a rect of the given size.

    The position is measured from the rect's top-left corner, with ``+x`` to
    the right and ``+y`` down. It is not rounded, so it may be fractional.

    Args:
        size: ``(width, height)`` of the rect, in pixels.
        anchor: Point on the rect to locate.

    Returns:
        The anchor's position, in pixels from the rect's top-left corner.
    """
    return anchor.fractional_pos.elementwise() * pg.Vector2(size)


def get_pos_from_anchor_match(
    child_size: Point,
    child_anchor: Anchor,
    parent_size: Point,
    parent_anchor: Anchor | None = None,
    margin: Point = (0, 0),
    offset: Point = (0, 0),
) -> tuple[int, int]:
    """Return the child's top-left position that matches its anchor to the parent's.

    Places the child so that ``child_anchor`` on the child lands on
    ``parent_anchor`` on the parent, then applies the margin and offset. The
    position is relative to the parent's top-left corner, with ``+x`` to the
    right and ``+y`` down; the parent's own position plays no part, so the
    caller adds it when a position in another frame, such as the screen, is
    needed. The result is rounded down once, after all other steps.

    Args:
        child_size: ``(width, height)`` of the rect being placed, in pixels.
        child_anchor: Point on the child that is matched to the parent.
        parent_size: ``(width, height)`` of the rect the child is placed
            against, in pixels.
        parent_anchor: Point on the parent that ``child_anchor`` is matched
            to. Defaults to the same point as ``child_anchor``, which places
            the child inside the parent.
        margin: Space between the matched anchor points, per axis. Positive
            values move the child from its anchor towards its own centre, and
            negative values move it the other way. Has no effect on an axis
            where ``child_anchor`` is central. Defaults to no margin.
        offset: Shift applied after the anchor and margin, with ``+x`` to the
            right and ``+y`` down, whatever the anchors. Defaults to no shift.

    Returns:
        ``(x, y)`` position of the child's top-left corner, in whole pixels from
        the parent's top-left corner.
    """
    if parent_anchor is None:
        parent_anchor = child_anchor

    anchor_pos_in_parent = _get_anchor_pos_in_rect_coords(
        parent_size,
        parent_anchor,
    )

    anchor_pos_in_child = _get_anchor_pos_in_rect_coords(
        child_size,
        child_anchor,
    )

    margin_nudge = child_anchor.margin_sign.elementwise() * pg.Vector2(margin)
    pos = anchor_pos_in_parent - anchor_pos_in_child + margin_nudge + pg.Vector2(offset)

    return (math.floor(pos.x), math.floor(pos.y))
