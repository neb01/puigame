"""The base Widget class that every puigame widget extends."""

from __future__ import annotations

from typing import ClassVar

import pygame as pg
from pygame.typing import Point

from puigame.components.skin import Skin

from .anchor import Anchor
from .state import State


class Widget(pg.sprite.Sprite):
    """Base class for all puigame widgets.

    A Widget is a pygame Sprite that provides:

    - a rect, sized on creation and positioned by its anchors
    - an optional parent to anchor against, and a list of children
    - a skin that draws its surfaces
    - ``visible`` and ``enabled`` flags, with ``_in_tree`` versions that take
      its parents into account
    - its current State, and the States it can be in
    """

    possible_states: ClassVar[tuple[State, ...]] = (State.BASE, State.DISABLED)

    _margin: pg.Vector2
    _offset: pg.Vector2

    def __init__(
        self,
        size: Point,  # using Point not tuple[int, int] to follow Pygame convention
        skin: Skin | None = None,
        parent: Widget | None = None,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,  # defaults to same as anchor
        margin: float | Point = 0,  # single number denotes same x and y margin
        offset: Point = (0, 0),  # screen space: +x is right >, +y is down v
        children: list[Widget] | None = None,
        enabled: bool = True,
        visible: bool = True,
    ) -> None:
        """Create a widget.

        Args:
            size: Width and height in pixels.
            skin: Skin that draws the widget's surfaces, or None for a
                transparent widget.
            parent: Widget to anchor against, or None for no parent yet.
                Widgets added to a UI become children of its root widget.
            anchor: Point on this widget used for positioning.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: Space between the matched anchor points. Positive values
                move the widget from its anchor point towards its own centre,
                and negative values move it the other way. A single number
                applies to both axes; an ``(x, y)`` pair sets each axis.
                Ignored on centred axes.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            children: Widgets to attach as children, in order. Each one is
                moved here with its ``set_parent()``, leaving any previous
                parent.
            enabled: Whether the widget responds to input.
            visible: Whether the widget is drawn.
        """
        given_width, given_height = size
        if given_width < 0 or given_height < 0:
            raise ValueError(
                "size cannot be negative. "
                f"Given width = {given_width} and height = {given_height}"
            )

        super().__init__()

        self.skin = skin
        self._rect = pg.Rect((0, 0), size)
        self._image_cache: dict[State, pg.Surface] = {}
        self.rebuild_image_cache()

        self.parent: Widget | None = None
        self.set_parent(parent)
        self._children: list[Widget] = []
        for child in children or []:
            child.set_parent(self)

        self.anchor = anchor
        self.parent_anchor = parent_anchor or self.anchor
        self.margin = margin
        self.offset = offset

        self.enabled = enabled
        self.visible = visible

    def __repr__(self) -> str:
        """Return a representation for debugging."""
        return f"<puigame widget: {type(self).__name__}, {self.rect}>"

    @property
    def rect(self) -> pg.Rect:
        """The widget's rect, positioned by layout.

        The rect can be read and is updated in place by layout each frame.
        Replacing it raises an error, since position comes from the anchors,
        margin, and offset.
        """
        return self._rect

    @rect.setter
    def rect(self, value: pg.Rect | pg.FRect | None) -> None:
        raise AttributeError("Widget's rect is set by layout, not set directly.")

    @property
    def children(self) -> tuple[Widget, ...]:
        """."""
        return tuple(self._children)

    @property
    def margin(self) -> pg.Vector2:
        """The margin as an ``(x, y)`` vector.

        Assigning a single number sets both axes; assigning an ``(x, y)`` pair
        sets each axis. Either is stored as a ``Vector2``.
        """
        return self._margin

    @margin.setter
    def margin(self, value: float | Point) -> None:
        self._margin = pg.Vector2(value)

    @property
    def offset(self) -> pg.Vector2:
        """The offset as an ``(x, y)`` vector in screen coordinates.

        Applied after the anchor and margin, with ``+x`` to the right and ``+y``
        downwards. Assigning any ``(x, y)`` pair, such as a tuple or another
        ``Vector2``, stores a copy as a ``Vector2``, so it can be changed in
        place, for example to animate the widget.
        """
        return self._offset

    @offset.setter
    def offset(self, value: Point) -> None:
        if isinstance(value, (int, float)):
            raise TypeError(
                "A single value (int/float) was provided to offset."
                " Offset requires a Point."
            )
        self._offset = pg.Vector2(value)

    @property
    def enabled_in_tree(self) -> bool:
        """Whether this widget and all of its parents are enabled."""
        if self.parent is None:
            return self.enabled
        else:
            return self.enabled and self.parent.enabled_in_tree

    @property
    def visible_in_tree(self) -> bool:
        """Whether this widget and all of its parents are visible."""
        if self.parent is None:
            return self.visible
        else:
            return self.visible and self.parent.visible_in_tree

    @property
    def current_state(self) -> State:
        """The widget's current State, built from its flags.

        Subclasses extend this by calling ``super().current_state`` and adding
        their own flags.
        """
        state = State.BASE

        if not self.enabled_in_tree:
            state |= State.DISABLED

        return state

    def has_ancestor(self, potential_ancestor: Widget) -> bool:
        """Return whether ``potential_ancestor`` is above this widget in the tree.

        Walks up the chain of parents, recursively, looking for
        ``potential_ancestor``. The widget itself does not count as its own
        ancestor.

        Args:
            potential_ancestor: Widget to look for among this widget's parents.

        Returns:
            True if ``potential_ancestor`` is this widget's parent, its parent's
            parent, and so on; False otherwise.
        """
        if self.parent is None:
            return False

        if self.parent is potential_ancestor:
            return True

        return self.parent.has_ancestor(potential_ancestor)

    def set_parent(self, new_parent: Widget | None) -> None:
        """Move this widget to a new parent, updating both sides of the link.

        Does nothing if ``new_parent`` is already the parent. Otherwise removes
        this widget from the old parent's children, sets ``new_parent`` as its
        parent, and adds it to ``new_parent``'s children.

        Args:
            new_parent: Widget to become the parent, or None to detach this
                widget from the tree.

        Raises:
            ValueError: If ``new_parent`` is this widget or one of its
                descendants, which would create a loop in the tree.
        """
        if new_parent is self.parent:
            return

        if new_parent is self:
            raise ValueError(f"{self!r} attempted to set itself as its own parent.")

        if new_parent is None:  # detach current widget
            if self.parent is not None:
                self.parent._children.remove(self)

            self.parent = None

        else:  # new parent exists: move current widget to new parent
            if new_parent.has_ancestor(self):
                raise ValueError(
                    f"{self!r} attempted to set "
                    f"a descendant ({new_parent!r}) as its parent."
                )

            new_parent._children.append(self)

            if self.parent is not None:
                self.parent._children.remove(self)

            self.parent = new_parent

    def rebuild_image_cache(self) -> None:
        """Render every state in ``possible_states`` again and cache the results."""
        for state in self.possible_states:
            self._image_cache[state] = self._render_state_image(state)

    def place_at_pos(self, pos: Point) -> None:
        """Place the widget's top-left corner at ``pos``.

        Shorthand for absolute placement: sets ``anchor`` and ``parent_anchor``
        to ``Anchor.TOP_LEFT`` and ``margin`` to ``pos``. The position is
        relative to the parent's top-left corner, which for a widget added
        directly to a UI is the top-left of the UI's area. Layout still runs as
        normal, so the widget moves with its parent.

        Args:
            pos: ``(x, y)`` position of the widget's top-left corner, in pixels
                from the parent's top-left corner.

        Raises:
            TypeError: If ``pos`` is a single number rather than an ``(x, y)``
                pair. The widget is left unchanged.
        """
        if isinstance(pos, (int, float)):
            raise TypeError(
                "A single value (int/float) was provided to place_at_pos()."
                " place_at_pos() requires a Point."
            )

        self.anchor = Anchor.TOP_LEFT
        self.parent_anchor = Anchor.TOP_LEFT
        self.margin = pos

    def _render_state_image(self, state: State) -> pg.Surface:
        """Return a new surface for ``state``.

        Uses the skin's rendering, or a transparent surface if there is no skin.
        Subclasses extend this to draw their content on top.
        """
        if self.skin is None:
            return pg.surface.Surface(self.rect.size, pg.SRCALPHA)

        else:
            return self.skin.render(self.rect.size, state)
