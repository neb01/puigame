"""PlacedImage, a rendered image and where to draw it on a widget."""

from collections.abc import Iterable
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


def compose_layers(layers: Iterable[PlacedImage]) -> PlacedImage:
    """Combine layers into one placed image, drawn in the order given.

    The first layer is at the bottom, and each later layer is drawn on top of
    the ones before it. Layers with zero width or height are skipped. The result
    covers the union of the remaining layers' rects: its ``pos`` is the union's
    top-left corner, and each layer is drawn at its own ``pos`` minus that
    corner, so every layer keeps its position relative to the widget.

    Args:
        layers: Layers to combine, bottom first. Read once, so any
            iterable can be passed.

    Returns:
        The combined image and its position relative to the widget's
        ``rect.topleft``. If no layer has a non-zero size, including when
        ``layers`` is empty, a new 0x0 image at ``(0, 0)``. If exactly
        one does, that layer itself, unchanged.
    """
    # skip layers with zero width or height
    non_zero_layers = [layer for layer in layers if 0 not in layer.image.size]

    # no layers, or only zero-size ones
    if len(non_zero_layers) == 0:
        return PlacedImage(
            pg.Surface((0, 0), pg.SRCALPHA),
            (0, 0),
        )

    if len(non_zero_layers) == 1:  # nothing to combine
        return non_zero_layers[0]

    rects = [pg.Rect(layer.pos, layer.image.size) for layer in non_zero_layers]

    union_rect = rects[0].unionall(rects[1:])
    union_image = pg.Surface(union_rect.size, pg.SRCALPHA)
    union_image_pos = union_rect.topleft

    for layer in non_zero_layers:
        union_image.blit(
            layer.image,
            (
                layer.pos[0] - union_image_pos[0],
                layer.pos[1] - union_image_pos[1],
            ),
        )

    return PlacedImage(union_image, union_image_pos)
