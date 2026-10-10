"""Skins, which turn a size and a state into a widget surface.

A skin draws a widget's appearance for a given size and state. It can build
surfaces of any size, so one skin can serve many widgets, each asking for its
own size.

Effects such as a halo or a swell can make the surface larger or smaller than
the widget. Each render therefore returns the surface together with an offset
that keeps the drawing centred on the widget's rect.

TransparentSkin draws nothing, for widgets with nothing to show.
DrawnSkin draws surfaces in code from a theme's style for each state.
ImageSkin loads an image file and scales it with nine-slice scaling.

Widgets cache the surfaces their skin produces, one per state, and swap
between them as their state changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import assert_never

import pygame as pg
from pygame.typing import Point

from puigame.core.state import State
from puigame.themes.theme import FadeProfile, Theme


@dataclass(frozen=True)
class BlitOffsetImage:
    """A rendered image and where to draw it relative to the widget.

    The field names match the attributes they set on a widget: ``image`` is the
    sprite's image, and ``blit_offset`` is where to draw it.

    Attributes:
        image: The rendered surface. It is larger than the widget when a halo
            or positive swell extends past its edges, and smaller when a
            negative swell shrinks it.
        blit_offset: How far up and to the left of the widget's
            ``rect.topleft`` to draw ``image``, as ``(x, y)`` in pixels.
            Subtract it from ``rect.topleft`` to get the drawing position.
            ``(0, 0)`` when the surface matches the widget's size, and
            negative when the surface is smaller than it.
    """

    image: pg.Surface
    blit_offset: tuple[int, int]


class Skin(ABC):
    """Abstract base class for skins.

    A skin turns a size and a state into a surface and an offset. Subclasses
    implement ``render()``. ``Skin`` itself cannot be created.
    """

    @abstractmethod
    def render(self, size: Point, state: State) -> BlitOffsetImage:
        """Render a surface for a widget of the given size in the given state.

        Every subclass implements this. Widgets call it once per state they can
        be in, and cache the results.

        Args:
            size: Width and height of the widget in pixels.
            state: State to draw, for example ``State.HIGHLIGHTED``.

        Returns:
            A new surface with its blit offset. Without effects, the surface
            is exactly ``size`` and the offset is ``(0, 0)``.
        """


class TransparentSkin(Skin):
    """Skin that renders a fully transparent surface.

    Used for widgets with nothing to show, such as invisible containers. The
    surface is the same in every state.
    """

    def render(self, size: Point, state: State) -> BlitOffsetImage:
        """Return a fully transparent surface of the requested size.

        The surface is the same in every state, so ``state`` is not used, and
        the offset is always ``(0, 0)``.
        """
        surface = pg.Surface(size, pg.SRCALPHA)
        return BlitOffsetImage(surface, (0, 0))


def _clamp_radius(radius: int, size: tuple[int, int]) -> int:
    """Clamp a corner radius to the range a rect of ``size`` can draw.

    The radius is kept between 0 and half the rect's shorter side. As in CSS, a
    radius that would be negative gives square corners, and one larger than
    half the shorter side gives a pill shape, or a circle for a square rect.

    Args:
        radius: The radius worked out for the layer, which can be out of range.
        size: The layer's width and height in pixels.

    Returns:
        The radius to draw the layer with.
    """
    max_radius = min(size[0], size[1]) // 2

    return max(0, min(radius, max_radius))


class DrawnSkin(Skin):
    """Skin that draws its surfaces in code from a theme.

    Each surface is drawn as three filled, rounded rectangles, from largest to
    smallest. Each layer covers the middle of the one before, so no gaps appear
    at rounded corners. Each layer's radius is kept between 0 and half that
    layer's shorter side: a radius that would be larger gives a pill shape, and
    one that would be negative gives square corners, for example a body inside
    a border thicker than the corner radius.

    The three layers, from the outside in:

    - **Halo**: drawn outside the border, in the halo colour. With a fading
      profile, its alpha falls from the halo colour's alpha at the inner edge
      to transparent just past the outer edge.
    - **Border**: the widget's outer edge. Its rect is the widget's size, grown
      or shrunk by the swell on every side, centred on the widget's rect.
    - **Body**: the fill inside the border, inset from the border's outer edge
      by the border thickness.

    Attributes:
        theme: The theme whose style for each state is drawn.
    """

    def __init__(self, theme: Theme) -> None:
        """Create a skin that draws from ``theme``.

        Args:
            theme: The theme to read styles from.
        """
        super().__init__()
        self.theme = theme

    def render(self, size: Point, state: State) -> BlitOffsetImage:
        """Draw the widget's halo, border, and body for a size and state.

        The swell grows (or, if negative, shrinks) the border and body on every
        side. The halo surrounds the border, so the surface is larger than
        ``size`` by the swell and halo on each side. With a fading halo, each
        ring is drawn from the outermost in, with its alpha following the
        style's ``halo_fade_profile``.

        Args:
            size: Width and height of the widget in pixels.
            state: State to draw, which can combine several flags.

        Returns:
            The drawn surface with its blit offset, the swell plus the halo
            thickness on each axis.

        Raises:
            ValueError: If the swell and border thickness would give the body
                a negative size. A body of size 0, where the widget is all
                border, is allowed.
        """
        given_size_x = int(size[0])
        given_size_y = int(size[1])
        style = self.theme.style_for(state)

        # main inner body size and radius, and check for negative size
        body_size = (
            given_size_x + (style.swell_px - style.border_thickness_px) * 2,
            given_size_y + (style.swell_px - style.border_thickness_px) * 2,
        )

        body_corner_radius = _clamp_radius(
            style.corner_radius_px + style.swell_px - style.border_thickness_px,
            body_size,
        )

        if min(body_size) < 0:
            raise ValueError(
                f"body_size cannot be negative, got body_size={body_size} px, "
                f"state={state}, size={size} px, "
                f"border_thickness_px={style.border_thickness_px} px, "
                f"swell_px={style.swell_px} px"
            )

        # border size and radius
        border_size = (
            given_size_x + style.swell_px * 2,
            given_size_y + style.swell_px * 2,
        )

        border_corner_radius = _clamp_radius(
            style.corner_radius_px + style.swell_px, border_size
        )

        # outer surface size, sized for the outer edge of the halo
        surface_size = (
            given_size_x + (style.swell_px + style.halo_thickness_px) * 2,
            given_size_y + (style.swell_px + style.halo_thickness_px) * 2,
        )

        # calculated from border_corner_radius so that negative swell_px
        # does not carry over into halo radius
        surface_corner_radius = _clamp_radius(
            border_corner_radius + style.halo_thickness_px,
            surface_size,
        )

        # create and position rects
        surface = pg.Surface(surface_size, pg.SRCALPHA)
        surface_rect = surface.get_rect()

        body_centered_rect = pg.Rect((0, 0), body_size)
        body_centered_rect.center = surface_rect.center

        border_centered_rect = pg.Rect((0, 0), border_size)
        border_centered_rect.center = surface_rect.center

        # fill shape with halo colour
        # overwritten completely later if thickness = 0
        if style.halo_fade_profile is not FadeProfile.SOLID:
            border_size_x, border_size_y = border_size
            inner_halo_ring_size = (border_size_x + 2, border_size_y + 2)
            inner_halo_ring_corner_radius = border_corner_radius + 1
            inner_halo_ring_rect = pg.Rect((0, 0), inner_halo_ring_size)
            inner_halo_ring_rect.center = surface_rect.center

            for i in reversed(range(style.halo_thickness_px)):
                # interpolates, following halo_fade_profile, between the first
                # halo ring at the given alpha and the first ring outside the
                # halo, which is fully transparent
                # thickness = 1 just makes one line at given transparency
                # draws outmost ring first and then inwards to allow each
                # successive ring to overlap the previous one

                match style.halo_fade_profile:
                    case FadeProfile.LINEAR:
                        halo_ring_alpha = round(
                            style.halo_colour[3] * (1 - (i / style.halo_thickness_px))
                        )
                    case FadeProfile.HARD_QUADRATIC:
                        halo_ring_alpha = round(
                            style.halo_colour[3]
                            * (1 - ((i / style.halo_thickness_px) ** 2))
                        )
                    case FadeProfile.SOFT_QUADRATIC:
                        halo_ring_alpha = round(
                            style.halo_colour[3]
                            * ((1 - (i / style.halo_thickness_px)) ** 2)
                        )
                    case FadeProfile.HARD_CUBIC:
                        halo_ring_alpha = round(
                            style.halo_colour[3]
                            * (1 - ((i / style.halo_thickness_px) ** 3))
                        )
                    case FadeProfile.SOFT_CUBIC:
                        halo_ring_alpha = round(
                            style.halo_colour[3]
                            * ((1 - (i / style.halo_thickness_px)) ** 3)
                        )
                    case _:
                        assert_never(style.halo_fade_profile)

                halo_ring_colour = (*style.halo_colour[:3], halo_ring_alpha)
                halo_ring_rect = inner_halo_ring_rect.inflate(i * 2, i * 2)
                # no clamp needed: each ring is the border grown by 1 + i px on
                # every side, and its radius grows by the same amount from the
                # clamped border radius, so it stays between 0 and half the
                # ring's shorter side
                halo_ring_corner_radius = inner_halo_ring_corner_radius + i

                pg.draw.rect(
                    surface,
                    halo_ring_colour,
                    halo_ring_rect,
                    width=0,
                    border_radius=halo_ring_corner_radius,
                )

        # no halo fade
        else:
            pg.draw.rect(
                surface,
                style.halo_colour,
                surface_rect,
                width=0,
                border_radius=surface_corner_radius,
            )

        # fill inner border shape with border colour
        # completely overwritten by body later if this thickness = 0
        pg.draw.rect(
            surface,
            style.border_colour,
            border_centered_rect,
            width=0,
            border_radius=border_corner_radius,
        )

        # fill inner body shape with body colour
        pg.draw.rect(
            surface,
            style.body_colour,
            body_centered_rect,
            width=0,
            border_radius=body_corner_radius,
        )

        offset = (
            style.swell_px + style.halo_thickness_px,
            style.swell_px + style.halo_thickness_px,
        )

        return BlitOffsetImage(surface, offset)


class ImageSkin(Skin):
    """Skin that uses an image file, scaled with nine-slice scaling."""

    pass
