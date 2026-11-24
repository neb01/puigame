"""Container, an invisible widget that holds and positions children."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame.typing import Point

from puigame._components.skin import NoSkin
from puigame._layout.anchor import Anchor
from puigame._layout.fit_size import FitSize
from puigame._widgets.panel import Panel
from puigame._widgets.widget import Widget

if TYPE_CHECKING:
    from puigame._ui.ui import UI


class Container(Panel):
    """Invisible panel that holds and positions children.

    A Container is a ``Panel`` with a ``NoSkin``, so its image is 0x0 and
    costs almost nothing to draw, and by default clicks pass through it. For
    a group of children with a background, use a ``Panel``.

    A Container can fit its children: ``None`` on an axis of its ``size``
    sizes that axis to them at each ``ui.update()``.
    """

    def __init__(
        self,
        parent: Widget | UI,
        *,
        size: FitSize = (None, None),
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        hit_testable: bool = False,
    ) -> None:
        """Create a container as the last child of ``parent``.

        Args:
            parent: Widget or ``UI`` to anchor against and to be a child of. It
                cannot be changed later.
            size: Width and height in pixels, or ``None`` on an axis to fit
                that axis to the container's children, as for ``Panel``.
                Defaults to ``(None, None)``, which fits both axes.
            anchor: Point on this container used for positioning. Defaults to
                ``Anchor.CENTRE``.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the container and its children respond to input.
                Defaults to ``True``.
            visible: Whether the container's children are drawn. Defaults to
                ``True``.
            hit_testable: Whether the mouse can hit the container, so that
                clicks over it stop at it. Defaults to ``False``, so clicks on
                its empty space reach the widgets below it and the game.

        Raises:
            TypeError: If ``anchor`` is not an ``Anchor``, if ``parent_anchor``
                is neither an ``Anchor`` nor ``None``, or if ``size``,
                ``margin``, or ``offset`` is not an ``(x, y)`` pair of numbers.
                The container is not added to ``parent``.
            ValueError: If either dimension of ``size`` is negative, or if
                ``parent`` is a box and ``anchor``, ``parent_anchor``, or
                ``margin`` is not its default. The container is not added to
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
            hit_testable=hit_testable,
        )
