"""floor_pair(), the rounding that puts fractional positions on whole pixels.

puigame rounds every fractional position down on each axis, and this is the
one place that rule is written.
"""

import math

from pygame.typing import Point


def floor_pair(pair: Point) -> tuple[int, int]:
    """Round each number in ``pair`` down to a whole number.

    puigame rounds fractional positions down on each axis, so a position lands
    on the same pixel wherever it comes from.

    Args:
        pair: ``(x, y)`` pair of numbers.

    Returns:
        ``(x, y)`` pair of ints, each the largest int no greater than its
        number.
    """
    return (math.floor(pair[0]), math.floor(pair[1]))
