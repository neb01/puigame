"""Row and Column, invisible widgets that stack their children in a line.

``Axis`` names the two axes of a surface, so ``LinearArrangement`` can work
along either.
"""

from __future__ import annotations

import math
from enum import IntEnum, unique
from typing import TYPE_CHECKING, ClassVar, TypeVar, assert_never

import pygame as pg
from pygame.typing import Point

from puigame._components.skin import NoSkin
from puigame._layout.anchor import Anchor
from puigame._layout.cross_axis_align import CrossAxisAlign
from puigame._layout.fit_size import FitSource
from puigame._validation import validate_enum, validate_int
from puigame._widgets.widget import Widget

if TYPE_CHECKING:
    from puigame._ui.ui import UI

_Number = TypeVar("_Number", int, float)


@unique
class Axis(IntEnum):
    """The two axes of a surface, as indices into an ``(x, y)`` pair.

    An ``IntEnum``, so a member indexes a size or position directly:
    ``rect.size[Axis.VERTICAL]`` is the height.
    """

    HORIZONTAL = 0
    VERTICAL = 1

    @property
    def cross(self) -> Axis:
        """The axis at right angles to this one."""
        match self:
            case Axis.HORIZONTAL:
                return Axis.VERTICAL

            case Axis.VERTICAL:
                return Axis.HORIZONTAL

            case _:
                assert_never(self)


def _to_xy_order(
    main_axis: Axis,
    main_axis_value: _Number,
    cross_axis_value: _Number,
) -> tuple[_Number, _Number]:
    """Return a main-axis value and a cross-axis value in ``(x, y)`` order.

    Args:
        main_axis: Axis that ``main_axis_value`` lies along.
        main_axis_value: Value along ``main_axis``.
        cross_axis_value: Value along the axis at right angles to
            ``main_axis``.

    Returns:
        ``(x, y)`` pair holding the two values, of the type they were given.
    """
    match main_axis:
        case Axis.HORIZONTAL:
            return (main_axis_value, cross_axis_value)

        case Axis.VERTICAL:
            return (cross_axis_value, main_axis_value)

        case _:
            assert_never(main_axis)


class LinearArrangement(Widget):
    """Base for widgets that stack their children in a column or a row.

    A row or column sizes itself to fit its visible children. Along its main
    axis it lays them end to end, with its ``main_axis_spacing`` between each
    pair of neighbours; across it, it is the size of the largest child. A
    negative spacing overlaps neighbours, with each child drawn over the one
    before it, as in a hand of cards. However large the overlap, the row or
    column encloses its children, shifting them inside if it must. Hidden
    children take no space. Children narrower than the row or column, across
    its main axis, are placed by its ``cross_axis_align``.

    Children are placed in the order they were created, from the start of the
    main axis, or from its end with ``main_axis_reversed``. Either way, they
    are drawn and hit in the order they were created, so a later child is on
    top of an earlier one.

    A row or column places its children, so each child's ``anchor``,
    ``parent_anchor``, and ``margin`` must keep their defaults. A child's
    ``offset`` still applies, after it has been placed. The size and the
    children's positions are worked out by the layout pass, so they are up to
    date after the next ``UI.update()``.

    Like a ``Container``, a row or column has no appearance and does not block
    clicks by default. This class is not used directly: use ``Row`` or
    ``Column``.
    """

    _fit_source = FitSource.CHILDREN
    _main_axis: ClassVar[Axis]

    def __init__(
        self,
        parent: Widget | UI,
        *,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        hit_testable: bool = False,
        main_axis_spacing: int = 0,
        main_axis_reversed: bool = False,
        cross_axis_align: CrossAxisAlign = CrossAxisAlign.CENTRE,
    ) -> None:
        """Create a row or column as the last child of ``parent``.

        It starts at 0x0 and takes its size from its children at the next
        layout pass.

        Args:
            parent: Widget or ``UI`` to anchor against and to be a child of. It
                cannot be changed later.
            anchor: Point on this widget used for positioning. Defaults to
                ``Anchor.CENTRE``.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether this widget and its children respond to input.
                Defaults to ``True``.
            visible: Whether this widget's children are drawn. Defaults to
                ``True``.
            hit_testable: Whether the mouse can hit this widget, so that clicks
                over it, including in the gaps between its children, stop at
                it. Defaults to ``False``, so clicks on its empty space reach
                the widgets below it and the game.
            main_axis_spacing: Space in pixels between neighbouring children
                along the main axis, with none before the first child or after
                the last. A negative value overlaps them. Fixed on creation.
                Defaults to 0.
            main_axis_reversed: Whether children are placed from the end of
                the main axis instead of its start: right to left in a row,
                bottom to top in a column. They are still drawn and hit in
                the order they were created. Fixed on creation. Defaults to
                ``False``.
            cross_axis_align: Where children narrower than this widget sit,
                across its main axis (see ``CrossAxisAlign``). Fixed on
                creation. Defaults to ``CrossAxisAlign.CENTRE``.

        Raises:
            TypeError: If ``anchor`` is not an ``Anchor``, if ``parent_anchor``
                is neither an ``Anchor`` nor ``None``, if ``margin`` or
                ``offset`` is not an ``(x, y)`` pair of numbers, if
                ``main_axis_spacing`` is not an ``int`` (a ``bool`` is
                refused), or if ``cross_axis_align`` is not a
                ``CrossAxisAlign``. The widget is not added to ``parent``.
            ValueError: If ``parent`` is a row or column and ``anchor``,
                ``parent_anchor``, or ``margin`` is not its default. The widget
                is not added to ``parent``.
        """
        validate_int("main_axis_spacing", main_axis_spacing)
        self._main_axis_spacing = main_axis_spacing

        self._main_axis_reversed = main_axis_reversed

        validate_enum("cross_axis_align", cross_axis_align, CrossAxisAlign)
        self._cross_axis_align = cross_axis_align

        self._child_positions: dict[Widget, pg.Vector2] = {}

        super().__init__(
            parent,
            size=(None, None),
            skin=NoSkin(),
            anchor=anchor,
            parent_anchor=parent_anchor,
            margin=margin,
            offset=offset,
            enabled=enabled,
            visible=visible,
            hit_testable=hit_testable,
        )

    def _measure(self) -> None:
        """Size to the visible children and work out where each goes.

        Along the main axis, the children are laid end to end in placement
        order (reversed with ``main_axis_reversed``), with
        ``main_axis_spacing`` between each pair of neighbours. The size runs
        from the lowest start to the highest end, so it encloses the children
        however much they overlap, and every slot is shifted so the lowest
        start is 0. Across the main axis, the size is the largest child's. With
        no visible children the size is 0x0. The layout pass measures the
        children first, so their sizes are current.

        Each visible child's slot, its position from this widget's top-left
        corner before its offset, is kept for ``_get_child_pos()``.
        """
        self._child_positions = {}

        visible_children = [child for child in self._children if child.visible]
        if not visible_children:
            self.rect.size = (0, 0)
            return

        if self._main_axis_reversed:
            visible_children.reverse()

        main_axis = self._main_axis
        cross_axis = main_axis.cross

        main_axis_pos = 0
        child_rect_extents = {}
        for child in visible_children:
            child_rect_end = main_axis_pos + child.rect.size[main_axis]
            child_rect_extents[child] = (main_axis_pos, child_rect_end)
            main_axis_pos = child_rect_end + self._main_axis_spacing

        lowest_start = min(start for start, _end in child_rect_extents.values())
        highest_end = max(end for _start, end in child_rect_extents.values())

        main_axis_size = highest_end - lowest_start
        cross_axis_size = max(
            child.rect.size[cross_axis] for child in child_rect_extents
        )

        self.rect.size = _to_xy_order(
            main_axis,
            main_axis_size,
            cross_axis_size,
        )

        for child, (start, _end) in child_rect_extents.items():
            match self._cross_axis_align:
                case CrossAxisAlign.START:
                    cross_axis_pos = 0

                case CrossAxisAlign.CENTRE:
                    cross_axis_pos = (cross_axis_size - child.rect.size[cross_axis]) / 2

                case CrossAxisAlign.END:
                    cross_axis_pos = cross_axis_size - child.rect.size[cross_axis]

                case _:
                    assert_never(self._cross_axis_align)

            # unrounded, so _get_child_pos() rounds once, after the offset
            self._child_positions[child] = pg.Vector2(
                _to_xy_order(main_axis, start - lowest_start, cross_axis_pos),
            )

    def _get_child_pos(self, child: Widget) -> tuple[int, int]:
        """Return where ``child`` goes, from this widget's top-left corner.

        A visible child goes in the slot the last layout pass worked out for
        it. A child with no slot, because it is hidden or has joined since the
        last layout pass (including while it is being created), goes at this
        widget's top-left corner. Either way, the child's offset is then added
        and the result rounded down once.

        Args:
            child: The widget being placed, whose parent is this one.

        Returns:
            ``(x, y)`` position of the child's top-left corner, in whole pixels
            from this widget's top-left corner.
        """
        pos = self._child_positions.get(child, (0, 0)) + pg.Vector2(child.offset)

        return (math.floor(pos.x), math.floor(pos.y))

    def _before_child_added(self, child: Widget) -> None:
        """Refuse a child whose placement arguments this widget would ignore.

        Args:
            child: The widget about to join, already set up.

        Raises:
            ValueError: If ``child``'s ``anchor`` or ``parent_anchor`` is not
                ``Anchor.CENTRE``, or its ``margin`` is not ``(0, 0)``.
        """
        if child._anchor != Anchor.CENTRE:
            raise ValueError(
                f"anchor must be Anchor.CENTRE in a {type(self).__name__}, "
                f"got {child._anchor!r}; it places its children",
            )
        if child._parent_anchor != Anchor.CENTRE:
            raise ValueError(
                "parent_anchor must be None or Anchor.CENTRE in a "
                f"{type(self).__name__}, got {child._parent_anchor!r}; "
                "it places its children",
            )
        if child._margin != (0, 0):
            raise ValueError(
                f"margin must be (0, 0) in a {type(self).__name__}, got "
                f"({child._margin.x:g}, {child._margin.y:g}); it places its children",
            )


class Row(LinearArrangement):
    """Invisible widget that stacks its children in a row, left to right.

    With ``main_axis_reversed``, it stacks them right to left. Its main axis
    is horizontal, so ``CrossAxisAlign.START`` aligns its children's tops and
    ``CrossAxisAlign.END`` their bottoms. See ``LinearArrangement`` for how it
    sizes itself and places its children.
    """

    _main_axis = Axis.HORIZONTAL


class Column(LinearArrangement):
    """Invisible widget that stacks its children in a column, top to bottom.

    With ``main_axis_reversed``, it stacks them bottom to top. Its main axis
    is vertical, so ``CrossAxisAlign.START`` aligns its children's left edges
    and ``CrossAxisAlign.END`` their right edges. See ``LinearArrangement``
    for how it sizes itself and places its children.
    """

    _main_axis = Axis.VERTICAL
