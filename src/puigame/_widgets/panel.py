"""Panel, a widget with a skin that gives its children a visible background."""

from pygame.typing import Point

from puigame._components.skin import Skin
from puigame._layout.anchor import Anchor
from puigame._widgets.widget import Widget


class Panel(Widget):
    """Widget with a skin, giving its children a visible background.

    Any widget can hold children, so a Panel differs from a ``Container`` only
    in appearance: its images come from the skin it is given, where a
    Container is invisible. The skin is fixed on creation.
    """

    def __init__(
        self,
        parent: Widget,
        *,
        size: Point,
        skin: Skin,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        consumes_clicks: bool = True,
    ) -> None:
        """Create a panel as the last child of ``parent``.

        Args:
            parent: Widget to anchor against and to be a child of. It cannot be
                changed later.
            size: Width and height in pixels.
            skin: Skin that draws the panel's images. It cannot be changed
                later. For no background, use a ``Container``.
            anchor: Point on this panel used for positioning.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the panel and its children respond to input. A
                disabled panel is drawn in the theme's style for the disabled
                state.
            visible: Whether the panel and its children are drawn.
            consumes_clicks: Whether mouse clicks over the panel stop at it.
                Defaults to ``True``, so clicks on its background reach neither
                the widgets below it nor the game.

        Raises:
            ValueError: If either dimension of ``size`` is negative. The panel
                is not added to ``parent``.
            TypeError: If ``margin`` or ``offset`` is a single number rather
                than an ``(x, y)`` pair. The panel is not added to ``parent``.
        """
        super().__init__(
            parent,
            size=size,
            skin=skin,
            anchor=anchor,
            parent_anchor=parent_anchor,
            margin=margin,
            offset=offset,
            enabled=enabled,
            visible=visible,
            consumes_clicks=consumes_clicks,
        )
