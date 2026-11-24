"""Panel, a widget with a skin that gives its children a visible background."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pygame.typing import Point

from puigame._components.skin import Skin
from puigame._layout.anchor import Anchor
from puigame._layout.fit_size import FitSize, FitSource
from puigame._widgets.widget import Widget

if TYPE_CHECKING:
    from puigame._ui.ui import UI


class Panel(Widget):
    """Widget with a skin, giving its children a visible background.

    Any widget can hold children; a Panel gives them a background, drawn by
    the skin it is given, which is fixed on creation. A ``Container`` is an
    invisible Panel.

    A Panel can also fit its children: ``None`` on an axis of its ``size``
    sizes that axis to them at each ``ui.update()``.
    """

    _fit_source = FitSource.CHILDREN

    def __init__(
        self,
        parent: Widget | UI,
        *,
        size: FitSize = (None, None),
        skin: Skin,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        hit_testable: bool = True,
    ) -> None:
        """Create a panel as the last child of ``parent``.

        Args:
            parent: Widget or ``UI`` to anchor against and to be a child of. It
                cannot be changed later.
            size: Width and height in pixels. ``None`` on an axis fits that
                axis to the panel's visible children whose ``anchor`` is the
                same as their ``parent_anchor``: the largest of their sizes
                plus their margin on each side, floored at 0, or 0 with no
                such children. Children anchored elsewhere, such as one
                hanging off the panel's side, are not counted. The axis is 0
                until the first ``ui.update()``, which fits it, and each
                update fits it again. Other values are rounded down to whole
                pixels. Defaults to ``(None, None)``, which fits both axes.
            skin: Skin that draws the panel's images. It cannot be changed
                later. For no background, use a ``Container``.
            anchor: Point on this panel used for positioning. Defaults to
                ``Anchor.CENTRE``.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the panel and its children respond to input. A
                disabled panel is drawn in the theme's style for the disabled
                state. Defaults to ``True``.
            visible: Whether the panel and its children are drawn. Defaults to
                ``True``.
            hit_testable: Whether the mouse can hit the panel, so that clicks
                over it stop at it. Defaults to ``True``, so clicks on its
                background reach neither the widgets below it nor the game.

        Raises:
            TypeError: If ``anchor`` is not an ``Anchor``, if ``parent_anchor``
                is neither an ``Anchor`` nor ``None``, or if ``size``,
                ``margin``, or ``offset`` is not an ``(x, y)`` pair of numbers.
                The panel is not added to ``parent``.
            ValueError: If either dimension of ``size`` is negative, or if
                ``parent`` is a box and ``anchor``, ``parent_anchor``, or
                ``margin`` is not its default. The panel is not added to
                ``parent``.
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
            hit_testable=hit_testable,
        )

    def _measure(self) -> None:
        """Fit each ``None`` axis of the requested size to the children.

        A child is counted if it is visible and its ``anchor`` is the same as
        its ``parent_anchor``, so that a child placed against an edge or
        corner it does not share, such as one hanging off the side, cannot
        grow the panel. Each counted child takes its size plus its margin on
        each side, floored at 0, since a negative margin lets a child overlap
        the panel's edge. A fixed axis keeps its size. The layout pass
        measures the children first, so their sizes are current.

        The images are rebuilt only when the size changes, since this runs
        every frame.
        """
        width, height = self._requested_size

        if width is not None and height is not None:
            return

        relevant_child_sizes = [
            (
                max(0, child.rect.width + child._margin[0] * 2),
                max(0, child.rect.height + child._margin[1] * 2),
            )
            for child in self.children
            if child.visible and child._anchor == child._parent_anchor
        ]

        if width is None:
            width = math.floor(
                max(
                    (child_size[0] for child_size in relevant_child_sizes),
                    default=0,
                )
            )
        else:
            width = self._rect.width

        if height is None:
            height = math.floor(
                max(
                    (child_size[1] for child_size in relevant_child_sizes),
                    default=0,
                )
            )
        else:
            height = self._rect.height

        if self._rect.size != (width, height):
            self._rect.size = (width, height)
            self._rebuild_image_cache()
