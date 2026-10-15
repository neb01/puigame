"""PlacedImage, a rendered image and where to draw it on a widget."""

from dataclasses import dataclass

import pygame as pg


@dataclass(frozen=True)
class PlacedImage:
    """A rendered image and where to draw it relative to the widget.

    A component's ``render(size, style)`` returns one. The dataclass is
    frozen, so its fields cannot be reassigned once it is made.

    Attributes:
        image: The rendered surface. Its size is independent of the widget's:
            for example, text is the size of its glyphs.
        pos: Position of ``image``'s top-left corner relative to the widget's
            ``rect.topleft``, as ``(x, y)`` in whole pixels, with ``+x`` to
            the right and ``+y`` down. Add it to ``rect.topleft`` to get the
            drawing position. Negative on an axis where the image starts above
            or to the left of the rect.
    """

    image: pg.Surface
    pos: tuple[int, int]
