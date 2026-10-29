"""Stubs shared by more than one test file."""

import pygame as pg
from pygame.typing import Point

from puigame._styling.style import RGBA, Style
from puigame.components.placed_image import PlacedImage
from puigame.components.skin import Skin


class FixedLayer(Skin):
    """Skin or component that draws a fixed-size block of colour.

    Ignores the size and style it is given, so a layer can differ from the
    widget's rect.
    """

    def __init__(self, *, size: Point, colour: RGBA, pos: tuple[int, int]) -> None:
        """Set up a layer of ``size``, filled with ``colour``, placed at ``pos``."""
        super().__init__()

        self.size = size
        self.colour = colour
        self.pos = pos

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Return a new surface of the layer's colour and size at its position."""
        image = pg.Surface(self.size, pg.SRCALPHA)
        image.fill(self.colour)

        return PlacedImage(image, self.pos)


class BodyColourLayer(Skin):
    """Skin or component that fills its whole size with the style's body colour.

    Unlike ``FixedLayer``, it reads the style, so its image shows which state's
    style it was given.
    """

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Return a new surface of ``size``, filled with the body colour, at (0, 0)."""
        image = pg.Surface(size, pg.SRCALPHA)
        image.fill(style.body_colour)

        return PlacedImage(image, (0, 0))
