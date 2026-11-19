"""UI, the object a game uses to create and run a set of widgets.

A UI is the top of its widget tree and holds the theme. It lays out the tree,
passes input to it, and draws it, each widget above its parent. A top-level
widget is created with the UI as its parent, and ``handle_event()``,
``update()``, and ``draw()`` run the UI each frame. A screen that shows several
UIs at once, such as a pause menu over a HUD, uses a separate UI for each, with
the game deciding their order.
"""

import math
from collections.abc import Iterator

import pygame as pg
from pygame.typing import Point

from puigame._styling.theme import DEFAULT_THEME, Theme
from puigame._ui.ui_manager import UIManager
from puigame._validation import validate_pair
from puigame._widgets.widget import Widget


class UI:
    """A widget tree, with its layout and drawing, run by the game each frame.

    The UI lays out and draws on a surface of the ``size`` given on creation,
    and its rects are in that surface's pixels. Each frame, the game passes
    each event to ``handle_event()``, then calls ``update()``, then ``draw()``.

    The UI's rect covers the whole surface, so a group of widgets is placed
    under a top-level ``Container`` or ``Panel`` rather than a ``UI`` of its
    own.
    """

    def __init__(
        self,
        *,
        size: Point,
        theme: Theme = DEFAULT_THEME,
    ) -> None:
        """Create a UI with no widgets yet.

        Args:
            size: Width and height of the surface the UI draws on, in pixels.
                For a display opened with ``pg.SCALED``, this is the display's
                own size, not the window's.
            theme: Theme that every widget in the UI draws with.

        Raises:
            TypeError: If ``size`` is a single number rather than an ``(x, y)``
                pair or contains a ``bool``.
            ValueError: If either dimension of ``size`` is negative.
        """
        validate_pair("size", size)
        if min(size[0], size[1]) < 0:
            raise ValueError(f"size cannot be negative, got {size!r} px")

        self._rect = pg.Rect((0, 0), size)
        self._theme = theme
        self._children: list[Widget] = []
        self.offset = (0, 0)

        self._manager = UIManager(ui=self)

    @property
    def rect(self) -> pg.Rect:
        """The area that top-level widgets are placed against.

        It is the size given on creation, in the coordinates of the UI's draw
        surface, at ``(0, 0)`` moved by ``offset``. Layout updates it in place
        each frame. Its size never changes and its position comes from
        ``offset``, so it is read-only.
        """
        return self._rect

    @property
    def children(self) -> tuple[Widget, ...]:
        """The UI's top-level widgets, in the order they were created.

        Returned as a tuple, so it cannot be changed directly.
        """
        return tuple(self._children)

    @property
    def theme(self) -> Theme:
        """The theme that every widget in the UI draws with.

        Set on creation and never changed, so it is read-only.
        """
        return self._theme

    @property
    def offset(self) -> pg.Vector2:
        """The UI's shift as an ``(x, y)`` vector in screen coordinates.

        Moves ``rect``, and every widget with it, with ``+x`` to the right and
        ``+y`` downwards, rounded down on each axis. Assigning any ``(x, y)``
        pair, such as a tuple or another ``Vector2``, stores a copy as a
        ``Vector2``, so it can be changed in place, for example to shake the UI.
        Changes take effect at the next ``update()``. The draw surface does not
        move, so a position off the surface still hits nothing. Starts at
        ``(0, 0)``.

        Assigning a single number, or a pair that contains a ``bool``, raises
        ``TypeError``.
        """
        return self._offset

    @offset.setter
    def offset(self, value: Point) -> None:
        validate_pair("offset", value)
        self._offset = pg.Vector2(value)

    def handle_event(self, event: pg.Event) -> bool:
        """Handle one pygame event and report whether the UI consumed it.

        Pass every event, not only mouse events, before ``update()`` each
        frame. The UI ignores events it has no use for, but needs window events
        such as ``WINDOWLEAVE`` and ``WINDOWFOCUSLOST`` to keep the highlight
        and presses right. It never polls pygame itself, so it sees only the
        events it is given. Event positions must be in the coordinates of the
        UI's draw surface.

        A mouse button down over a hit-testable widget is consumed, and
        so is its matching up, wherever it lands, so a click on a panel never
        reaches the game. A drag that starts outside the UI still reaches the
        game when it is released over a widget. Only the part of a widget that
        lies on the draw surface counts, so a position off the surface hits
        nothing. The mouse wheel is consumed over a hit-testable widget too, so
        scrolling over a panel never reaches the game. Mouse motion and window
        events are never consumed.

        Args:
            event: The event to handle.

        Returns:
            ``True`` if the UI consumed the event, so the game should not handle
            it, otherwise ``False``.
        """
        return self._manager.handle_event(event)

    def update(self) -> None:
        """Lay out the widgets and refresh their images for this frame.

        Call once per frame, after handling events and before ``draw()``.
        Changes made to widgets since the last update, such as a new offset or
        flag, take effect here: the layout pass places every widget against its
        parent, the highlight moves to the widget under the cursor, then each
        widget shows its image for its current state.
        """
        self._place_tree()
        self._manager._update_highlight()
        self._update_tree()

    def draw(self, surface: pg.Surface) -> None:
        """Draw the visible widgets onto ``surface``.

        Each widget is drawn, then its whole subtree, then its next sibling, so
        children appear above their parents and a later sibling's subtree above
        an earlier one's. A hidden widget is skipped along with everything below
        it. Each image is drawn at ``rect.topleft`` moved by its ``image_pos``.
        Drawing changes nothing, so it can run any number of times per update.

        Args:
            surface: Surface to draw on, usually the display surface. It should
                be the size the UI was created with.
        """
        for widget in self._iter_visible_descendants():
            surface.blit(
                widget.image,
                (
                    widget.rect.left + widget.image_pos[0],
                    widget.rect.top + widget.image_pos[1],
                ),
            )

    def _place_tree(self) -> None:
        """Place the UI's rect, then every widget, parents before children.

        This is the layout pass. It runs once per frame, before drawing, so
        that changes to any offset, the UI's included, take effect. Setting an
        offset moves nothing until the pass runs.
        """
        self._place()

        for widget in self._iter_descendants():
            widget._place()

    def _update_tree(self) -> None:
        """Refresh the image of every widget in the UI.

        Each widget shows the cached image and position for its current state.
        This runs once per frame, after the layout pass.
        """
        for widget in self._iter_descendants():
            widget._update()

    def _place(self) -> None:
        """Place the rect at ``(0, 0)`` moved by the offset.

        The UI has no parent to be placed against. The offset is rounded down
        on each axis, as for every widget, so a fractional offset rounds the
        same way everywhere.
        """
        self.rect.topleft = (
            math.floor(self.offset.x),
            math.floor(self.offset.y),
        )

    def _iter_descendants(self) -> Iterator[Widget]:
        """Yield every widget in the UI, parents first.

        The order is depth-first pre-order: each top-level widget followed by
        all of its descendants before the next one. The UI is not a widget, so
        it is not yielded itself. The tree is read as it is walked, so take a
        ``list()`` first if the walk will kill widgets.

        Yields:
            Each widget, in depth-first pre-order.
        """
        for child in self.children:
            yield from child._iter_subtree()

    def _iter_visible_descendants(self) -> Iterator[Widget]:
        """Yield every widget in the UI, skipping hidden subtrees.

        The order is the same depth-first pre-order as ``_iter_descendants()``,
        but a widget that is not ``visible`` is skipped along with everything
        below it, so each widget is checked once. It yields exactly the widgets
        to draw, in drawing order.

        Yields:
            Each visible widget, in depth-first pre-order.
        """
        for child in self.children:
            yield from child._iter_visible_subtree()

    def _before_child_added(self, child: Widget) -> None:
        """Check that ``child`` can join the UI's children.

        ``_add_child()`` calls this just before ``child`` joins. An override
        raises to refuse the child, and must change nothing first, since a
        refused child never joins. The default accepts every child and does
        nothing, so overrides need not call ``super()``.

        Args:
            child: The widget about to join, already set up.
        """

    def _add_child(self, child: Widget) -> None:
        """Add ``child`` as the last of the UI's children, if allowed.

        ``_before_child_added()`` runs first, and if it raises, ``child`` is not
        added. ``child``'s own ``__init__`` calls this once, as the last step of
        its setup.

        Args:
            child: The new widget, whose parent is the UI.
        """
        # called once, from the new child's own __init__
        assert child not in self._children

        self._before_child_added(child)
        self._children.append(child)

    def _remove_child(self, child: Widget) -> None:
        """Remove ``child`` from the UI's children, if it is still there.

        ``child.kill()`` calls this. A child that an earlier ``kill()`` already
        removed is ignored, so ``kill()`` can safely be called more than once.

        Args:
            child: The widget leaving, whose parent is the UI.
        """
        if child in self._children:
            self._children.remove(child)
