"""Skins, which turn a size and a style into a widget surface.

A skin draws a widget's appearance for a given size and style. Skins hold no
per-widget data and no theme: the widget looks up the style for each of its
states and passes it in. One skin can therefore serve many widgets, each with
its own size and theme.

Effects such as a halo or a swell can make the surface larger or smaller than
the widget. Each render therefore returns the surface together with a blit
offset that keeps the drawing centred on the widget's rect.

NoSkin renders an empty surface, for widgets with no appearance at all.
TransparentSkin renders a transparent surface, for content with no background.
DrawnSkin draws surfaces in code from the style it is given.
ImageSkin loads an image file and scales it with nine-slice scaling.

Widgets cache what their skin renders as one image per state, and swap
between those images as their state changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import assert_never

import pygame as pg
from pygame.typing import Point

from puigame.themes.theme import FadeProfile, Style


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

    A skin turns a size and a style into a surface and a blit offset. Subclasses
    implement ``render()``, keeping its signature, so any skin can stand in for
    any other. ``Skin`` itself cannot be created.
    """

    @abstractmethod
    def render(self, size: Point, style: Style) -> BlitOffsetImage:
        """Render a surface for a widget of the given size in the given style.

        Every subclass implements this. Widgets call it once per state they can
        be in, passing the theme's style for that state, and cache the results.

        Args:
            size: Width and height of the widget in pixels.
            style: Complete style to draw with, as returned by
                ``Theme.style_for()``.

        Returns:
            A new surface with its blit offset. Without effects, the surface
            is exactly ``size`` and the blit offset is ``(0, 0)``. A skin that draws
            nothing, such as ``NoSkin``, may return an empty surface instead.
        """


class NoSkin(Skin):
    """Skin that renders an empty surface, for widgets with no appearance.

    Used by ``Container`` and ``UIRoot``, which draw nothing, so their images
    cost almost nothing to store or draw. A widget with content but no
    background, such as a bare label, uses ``TransparentSkin`` instead, since
    its content needs a surface of the widget's size to be drawn on.
    """

    def render(self, size: Point, style: Style) -> BlitOffsetImage:
        """Return an empty surface, whatever the size and style.

        Args:
            size: Not used; accepted so the signature matches ``Skin.render()``.
            style: Not used; accepted so the signature matches ``Skin.render()``.

        Returns:
            A new 0x0 surface, with blit offset ``(0, 0)``.
        """
        surface = pg.Surface((0, 0), pg.SRCALPHA)
        blit_offset = (0, 0)

        return BlitOffsetImage(surface, blit_offset)


class TransparentSkin(Skin):
    """Skin that renders a fully transparent surface.

    Used for widgets with content but no background, such as a bare label: the
    content is drawn onto the transparent surface. Widgets that draw nothing at
    all use ``NoSkin`` instead. The surface is the same whatever the style.
    """

    def render(self, size: Point, style: Style) -> BlitOffsetImage:
        """Return a fully transparent surface of the requested size.

        Nothing is drawn, so ``style`` is not used, and the blit offset is
        always ``(0, 0)``.

        Args:
            size: Width and height of the widget in pixels.
            style: Not used; accepted so the signature matches ``Skin.render()``.

        Returns:
            A new transparent surface of exactly ``size``, with blit offset
            ``(0, 0)``.
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
    """Skin that draws its surfaces in code from a style.

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

    The skin holds no data of its own: everything it draws comes from the style
    passed to ``render()``.
    """

    def render(self, size: Point, style: Style) -> BlitOffsetImage:
        """Draw the widget's halo, border, and body for a size and style.

        The swell grows (or, if negative, shrinks) the border and body on every
        side. The halo surrounds the border, so the surface is larger than
        ``size`` by the swell and halo on each side. With a fading halo, each
        ring is drawn from the outermost in, with its alpha following the
        style's ``halo_fade_profile``.

        Args:
            size: Width and height of the widget in pixels.
            style: Complete style to draw with, as returned by
                ``Theme.style_for()``.

        Returns:
            The drawn surface with its blit offset, the swell plus the halo
            thickness on each axis.

        Raises:
            ValueError: If the swell and border thickness would give the body
                a negative size. A body of size 0, where the widget is all
                border, is allowed.
        """
        given_width = int(size[0])
        given_height = int(size[1])

        # main inner body size and radius, and check for negative size
        body_size = (
            given_width + (style.swell_px - style.border_thickness_px) * 2,
            given_height + (style.swell_px - style.border_thickness_px) * 2,
        )

        body_corner_radius = _clamp_radius(
            style.corner_radius_px + style.swell_px - style.border_thickness_px,
            body_size,
        )

        if min(body_size) < 0:
            raise ValueError(
                "border_thickness_px and swell_px cannot combine to make the "
                f"body size negative, got body_size={body_size} px, size={size} px, "
                f"border_thickness_px={style.border_thickness_px} px, "
                f"swell_px={style.swell_px} px"
            )

        # border size and radius
        border_size = (
            given_width + style.swell_px * 2,
            given_height + style.swell_px * 2,
        )

        border_corner_radius = _clamp_radius(
            style.corner_radius_px + style.swell_px, border_size
        )

        # outer surface size, sized for the outer edge of the halo
        surface_size = (
            given_width + (style.swell_px + style.halo_thickness_px) * 2,
            given_height + (style.swell_px + style.halo_thickness_px) * 2,
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

        body_centred_rect = pg.Rect((0, 0), body_size)
        body_centred_rect.center = surface_rect.center

        border_centred_rect = pg.Rect((0, 0), border_size)
        border_centred_rect.center = surface_rect.center

        # fill shape with halo colour
        # overwritten completely later if thickness = 0
        if style.halo_fade_profile is not FadeProfile.SOLID:
            inner_halo_ring_rect = border_centred_rect.inflate(2, 2)
            inner_halo_ring_corner_radius = border_corner_radius + 1

            for i in reversed(range(style.halo_thickness_px)):
                # draws the outermost ring first, then inwards, so each ring
                # overlaps the one drawn before it; a thickness of 1 gives a
                # single ring at the halo's alpha

                # t runs from 0 at the innermost ring to 1 just past the outer
                # edge; each profile's multiplier is defined in FadeProfile
                t = i / style.halo_thickness_px

                match style.halo_fade_profile:
                    case FadeProfile.LINEAR:
                        fade_multiplier = 1 - t

                    case FadeProfile.SOFT_QUADRATIC:
                        fade_multiplier = (1 - t) ** 2

                    case FadeProfile.HARD_QUADRATIC:
                        fade_multiplier = 1 - t**2

                    case FadeProfile.SOFT_CUBIC:
                        fade_multiplier = (1 - t) ** 3

                    case FadeProfile.HARD_CUBIC:
                        fade_multiplier = 1 - t**3

                    case _:
                        assert_never(style.halo_fade_profile)

                halo_ring_alpha = round(style.halo_colour[3] * fade_multiplier)

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

        # solid halo: no fade
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
            border_centred_rect,
            width=0,
            border_radius=border_corner_radius,
        )

        # fill inner body shape with body colour
        pg.draw.rect(
            surface,
            style.body_colour,
            body_centred_rect,
            width=0,
            border_radius=body_corner_radius,
        )

        blit_offset = (
            style.swell_px + style.halo_thickness_px,
            style.swell_px + style.halo_thickness_px,
        )

        return BlitOffsetImage(surface, blit_offset)


class ImageSkin(Skin):
    """Skin that uses an image file, scaled with nine-slice scaling."""

    pass
