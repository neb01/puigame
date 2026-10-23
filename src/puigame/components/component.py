"""Component, the protocol for anything a widget renders into its image.

A widget's image is made of layers: its skin at the bottom, then each of its
components in the order the widget was given them. Every layer is rendered
from the widget's size and the style for one of its states, and the results
are combined with ``compose_layers()``.

Skins and ``Text`` match this protocol without inheriting from it. Pyright
checks the match wherever a ``Component`` is expected.
"""

from typing import Protocol

from pygame.typing import Point

from puigame.components.placed_image import PlacedImage
from puigame.themes.style import Style


class Component(Protocol):
    """Protocol for parts of a widget that render into its image.

    Any object with a matching ``render()`` method is a component. Components
    hold no theme: the widget passes in the style for each of its states.
    """

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Render this part of a widget for the given size and style.

        Widgets call this once per state they can be in, and cache the results
        until the cache is rebuilt.

        Args:
            size: ``(width, height)`` of the widget's rect, in pixels.
            style: Style for one of the widget's states, as returned by
                ``Theme.style_for()``.

        Returns:
            A new surface, never shared with another widget or another call,
            and the position of its top-left corner relative to the widget's
            ``rect.topleft``. The position may be negative, and the surface may
            extend past the rect. A zero-size surface is skipped when layers
            are combined. Library code never draws on the surface after it is
            returned.
        """
        ...
