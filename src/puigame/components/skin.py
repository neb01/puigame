"""Skins, which turn a size and a state into a widget surface.

A skin reads its rules from a theme: for example, a rectangle with a given
colour and corner radius, 50% dimmer when disabled, and 20% lighter with a
halo when highlighted. It can build surfaces of any size from these rules,
so one skin can serve many widgets, each asking for its own size.

DrawnSkin draws surfaces in code from the theme's colours and shapes.
ImageSkin loads an image file and scales it with nine-slice scaling.

Widgets cache the surfaces their skin produces, one per state, and swap
between them as their state changes.
"""

from abc import ABC, abstractmethod

import pygame as pg
from pygame.typing import Point

from puigame.core.state import State


class Skin(ABC):
    """Abstract base class for skins.

    A skin turns a size and a state into a surface.
    Subclasses implement ``render()``
      Skin itself cannot be created.
    """

    @abstractmethod
    def render(self, size: Point, state: State) -> pg.surface.Surface:
        """Render a surface for a widget of the given size in the given state.

        Every subclass implements this. Widgets call it once per state they can
        be in, and cache the results.

        Args:
            size: Width and height of the surface in pixels.
            state: State to draw, for example ``State.HIGHLIGHTED``.

        Returns:
            A new surface of exactly ``size``.
        """


class TransparentSkin(Skin):
    """Skin that renders a fully transparent surface.

    Used for widgets with no background. The surface is the same in every
    state.
    """

    def render(self, size: Point, state: State) -> pg.surface.Surface:
        """Return a fully transparent surface of the requested size."""
        return pg.surface.Surface(size, pg.SRCALPHA)


class DrawnSkin(Skin):
    """Skin that draws its surfaces in code from theme values."""

    pass


class ImageSkin(Skin):
    """Skin that uses an image file, scaled with nine-slice scaling."""

    pass
