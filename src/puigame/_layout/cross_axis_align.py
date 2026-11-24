"""CrossAxisAlign, where children sit across a row or column."""

from enum import Enum, auto


class CrossAxisAlign(Enum):
    """Where a row's or column's children sit across its main axis.

    A child narrower than its row or column, across the main axis, is placed
    at one of three points. ``START`` and ``END`` are the edges where
    coordinates begin and end, as in pygame:

    - ``START``: the left edge in a ``Column``, the top in a ``Row``.
    - ``CENTRE``: centred. When the space does not divide evenly, the
      position is rounded down, once the child's offset has been added.
    - ``END``: the right edge in a ``Column``, the bottom in a ``Row``.
    """

    START = auto()
    CENTRE = auto()
    END = auto()
