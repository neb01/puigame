"""Container, an invisible widget that holds and positions children."""

from pygame.typing import Point

from puigame.components.skin import NoSkin
from puigame.core.anchor import Anchor
from puigame.core.widget import Widget


class Container(Widget):
    """Invisible widget that holds and positions children.

    A Container has no appearance: it uses a ``NoSkin``, so its image is 0x0
    and costs almost nothing to draw. For a group of children with a
    background, use a ``Panel``.
    """

    def __init__(
        self,
        parent: Widget,
        *,
        size: Point,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        consumes_clicks: bool = False,
    ) -> None:
        """Create a container as the last child of ``parent``.

        Args:
            parent: Widget to anchor against and to be a child of. It cannot be
                changed later.
            size: Width and height in pixels.
            anchor: Point on this container used for positioning.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the container and its children respond to input.
            visible: Whether the container's children are drawn.
            consumes_clicks: Whether mouse clicks over the container stop at
                it. Defaults to ``False``, so clicks on its empty space reach
                the widgets below it and the game.

        Raises:
            ValueError: If either dimension of ``size`` is negative. The
                container is not added to ``parent``.
            TypeError: If ``margin`` or ``offset`` is a single number rather
                than an ``(x, y)`` pair. The container is not added to
                ``parent``.
        """
        super().__init__(
            parent,
            size=size,
            skin=NoSkin(),
            anchor=anchor,
            parent_anchor=parent_anchor,
            margin=margin,
            offset=offset,
            enabled=enabled,
            visible=visible,
            consumes_clicks=consumes_clicks,
        )
