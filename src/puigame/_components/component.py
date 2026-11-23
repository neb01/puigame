"""Component, the protocol for anything a widget renders into its image.

A widget's image is made of layers: its skin at the bottom, then each of its
components in the order the widget was given them. Every layer is rendered
from the widget's size and the style for one of its states, and the results
are combined with ``compose_layers()``.

``Text`` matches this protocol without inheriting from it. Pyright checks
the match wherever a ``Component`` is expected.
"""

from typing import Protocol

from pygame.typing import Point

from puigame._components.placed_image import PlacedImage
from puigame._styling.style import Style


class Component(Protocol):
    """Protocol for parts of a widget that render into its image.

    Any object with matching ``get_preferred_size()`` and ``render()`` methods
    is a component. Components hold no theme: the widget passes in the style
    for each of its states.
    """

    def get_preferred_size(self, style: Style) -> tuple[int, int]:
        """Return the size a widget needs to fit this part in a style.

        The size depends only on the part's content and the style, never on
        the size of the widget it is drawn on. Measuring may render, so it can
        cost as much as ``render()``.

        Args:
            style: Style to measure the part in.

        Returns:
            ``(width, height)`` in pixels, neither below 0. A part that fills
            whatever size it is given, rather than having a size of its own,
            returns ``(0, 0)``.
        """
        ...

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Render this part of a widget for the given size and style.

        Widgets call this once per state they can be in, and cache the results
        until the cache is rebuilt.

        Args:
            size: ``(width, height)`` of the widget's rect, in pixels.
            style: Style for one of the widget's states, as resolved by the
                widget's theme.

        Returns:
            A new surface, never shared with another widget or another call,
            and the position of its top-left corner relative to the widget's
            ``rect.topleft``. The position may be negative, and the surface may
            extend past the rect. A zero-size surface is skipped when layers
            are combined. Library code never draws on the surface after it is
            returned.
        """
        ...
