"""BoxAlign, where a box's children sit across its main axis."""

from enum import Enum, auto


class BoxAlign(Enum):
    """Where a box's children sit across its main axis.

    A child narrower than its box, across the box's main axis, is placed at
    one of three points. ``START`` and ``END`` are the edges where
    coordinates begin and end, as in pygame:

    - ``START``: the left edge in a ``VBox``, the top in an ``HBox``.
    - ``CENTRE``: centred. When the space does not divide evenly, the
      position is rounded down, once the child's offset has been added.
    - ``END``: the right edge in a ``VBox``, the bottom in an ``HBox``.
    """

    START = auto()
    CENTRE = auto()
    END = auto()
