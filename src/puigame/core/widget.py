"""The base Widget class that every puigame widget extends."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar

import pygame as pg
from pygame.typing import Point

from puigame.components.skin import BlitOffsetImage, Skin, TransparentSkin
from puigame.themes.theme import Theme

from .anchor import Anchor
from .state import State


class Widget(pg.sprite.Sprite):
    """Base class for all puigame widgets.

    A Widget is a pygame Sprite that provides:

    - a rect, sized on creation and positioned by its anchors
    - an optional parent to anchor against, and a list of children
    - a skin that draws its surfaces, and an optional theme of its own,
      otherwise inherited from the nearest ancestor that has one
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
        *,
        skin: Skin | None = None,
        own_theme: Theme | None = None,  # None inherits from the nearest ancestor
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
            skin: Skin that draws the widget's surfaces, or ``None`` for a
                transparent widget, which uses a ``TransparentSkin``.
            own_theme: Theme for this widget and the descendants that inherit
                it, or ``None`` to inherit the nearest ancestor's theme.
                Until a theme can be found, the widget's images are not built.
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
            raise ValueError(f"size cannot be negative, got size={size} px")

        super().__init__()

        self._rect = pg.Rect((0, 0), size)

        if skin is None:
            self.skin = TransparentSkin()
        else:
            self.skin = skin

        self._own_theme = own_theme
        self._parent: Widget | None = None
        self._children: list[Widget] = []

        self.anchor = anchor
        if parent_anchor is None:
            self.parent_anchor = self.anchor
        else:
            self.parent_anchor = parent_anchor

        self.margin = margin
        self.offset = offset

        # set initial image_cache, image, blit_offset according to initial flags
        self.enabled = enabled
        self.visible = visible

        self._image_cache: dict[State, BlitOffsetImage] = {}
        self.image: pg.Surface
        self.blit_offset: tuple[int, int]
        self.rebuild_image_cache()  # build cache and set image, blit_offset

        self.set_parent(parent)
        if children is not None:
            for child in children:
                child.set_parent(self)

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
        raise AttributeError(
            "widget's rect cannot be set directly; "
            "position the widget via anchor, parent_anchor, margin, and offset"
        )

    @property
    def parent(self) -> Widget | None:
        """The widget this one is anchored against, or ``None`` if detached.

        The parent can be read, but replacing it directly raises an error.
        Move the widget with ``set_parent()``, which keeps both sides of the
        link in step.
        """
        return self._parent

    @parent.setter
    def parent(self, value: Widget | None) -> None:
        raise AttributeError(
            "widget's parent cannot be set directly; "
            "set the parent via the set_parent() method."
        )

    @property
    def children(self) -> tuple[Widget, ...]:
        """The widget's children, in the order they were added.

        Returned as a tuple, so it cannot be changed directly. Add or remove a
        child with ``child.set_parent()``, which keeps both sides of the link
        in step.
        """
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
                f"offset cannot be a single value, got {value!r}; "
                "offset must instead be a point"
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

    @property
    def own_theme(self) -> Theme | None:
        """The theme set on this widget itself, or ``None`` if it inherits one.

        Setting it to a theme makes this widget, and the descendants that
        inherit from it, draw with that theme. Setting it to ``None`` makes the
        widget inherit the nearest ancestor's theme again. Either way, the
        image caches of the widget and all its descendants are rebuilt, and
        any widget that still has no theme is skipped.
        """
        return self._own_theme

    @own_theme.setter
    def own_theme(self, value: Theme | None) -> None:
        self._own_theme = value

        self.rebuild_image_cache()
        for descendant in self.iter_descendants():
            descendant.rebuild_image_cache()

    @property
    def theme(self) -> Theme:
        """The theme the widget draws with.

        This is ``own_theme`` if it is set, and otherwise the nearest
        ancestor's ``own_theme``.

        Raises:
            RuntimeError: If neither the widget nor any of its ancestors has a
                theme, for example while it is detached.
        """
        theme = self._find_theme()

        if theme is None:
            raise RuntimeError(
                "Widget cannot be built without either its own theme "
                "or an ancestor with a valid theme; "
                f"{self} has no valid theme"
            )

        return theme

    def _find_theme(self) -> Theme | None:
        """Return the theme the widget draws with, or ``None`` if it has none.

        Walks up the chain of parents, returning the first ``own_theme`` that
        is set, starting with this widget's. Unlike ``theme``, does not raise.

        Returns:
            This widget's ``own_theme`` if set, otherwise the nearest
            ancestor's, or ``None`` if no widget in the chain has one.
        """
        if self.own_theme is not None:
            return self.own_theme

        if self.parent is None:
            return None

        return self.parent._find_theme()

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

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Refresh ``image`` from the current state; called once per frame."""
        super().update(*args, **kwargs)

        if self._image_cache:  # don't refresh if image cache not yet built
            self._refresh_current_image_blit_offset()

    def set_parent(self, new_parent: Widget | None) -> None:
        """Move this widget to a new parent, updating both sides of the link.

        Does nothing if ``new_parent`` is already the parent. Otherwise removes
        this widget from the old parent's children, sets ``new_parent`` as its
        parent, and adds it to ``new_parent``'s children. Then rebuilds the
        image caches of this widget and all its descendants, since the theme
        they inherit may have changed.

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
            raise ValueError(f"cannot set {self!r} as its own parent")

        if new_parent is None:  # detach current widget
            if self.parent is not None:
                self.parent._children.remove(self)

            self._parent = None

        else:  # new parent exists: move current widget to new parent
            if new_parent.has_ancestor(self):
                raise ValueError(
                    "cannot set a descendant as its own parent, "
                    f"got self {self!r} and new_parent {new_parent!r}"
                )

            new_parent._children.append(self)

            if self.parent is not None:
                self.parent._children.remove(self)

            self._parent = new_parent

        self.rebuild_image_cache()
        for descendant in self.iter_descendants():
            descendant.rebuild_image_cache()

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
                "pos cannot be a single value, "
                f"got {pos!r}; pos must instead be a point"
            )

        self.anchor = Anchor.TOP_LEFT
        self.parent_anchor = Anchor.TOP_LEFT
        self.margin = pos

    def iter_descendants(self) -> Iterator[Widget]:
        """Yield every widget below this one in the tree, parents first.

        The order is depth-first pre-order: each child is followed by all of its
        own descendants before the next child. The widget itself is not
        included. The tree is read as it is walked, so take a ``list()`` first
        if the walk will move widgets.

        Yields:
            Each descendant, in depth-first pre-order.
        """
        for child in self.children:
            yield child
            yield from child.iter_descendants()

    def rebuild_image_cache(self) -> None:
        """Render every state in ``possible_states`` again and cache the results.

        Each state's surface is cached together with its blit offset, as a
        ``BlitOffsetImage``. Does nothing if the widget has no theme, so a
        detached widget is built once it gains one, either its own or an
        ancestor's.
        """
        if self._find_theme() is not None:
            for state in self.possible_states:
                self._image_cache[state] = self._render_state_image(state)

            self._refresh_current_image_blit_offset()

    def _render_state_image(self, state: State) -> BlitOffsetImage:
        """Return a new surface and its blit offset for ``state``.

        Uses the skin's rendering. Subclasses extend this to draw their content
        on top, adding the blit offset to any position so the content lands on
        the widget's body rather than in a halo margin.
        """
        style = self.theme.style_for(state)
        return self.skin.render(self.rect.size, style)

    def _refresh_current_image_blit_offset(self) -> None:
        """Show the cached image and blit offset for the widget's current state.

        Reads ``current_state`` once and looks up its ``BlitOffsetImage`` in the
        image cache. Called whenever the cache is rebuilt, and each frame by
        ``update()`` so the image follows changes to the widget's and its
        ancestors' flags.

        Raises:
            RuntimeError: If ``current_state`` is not in ``possible_states``,
                which means the class's ``possible_states`` is missing a
                combination its flags can produce.
        """
        state = self.current_state  # cache property method result once

        if state not in self.possible_states:
            raise RuntimeError(
                "current_state is not in possible_states; add it to "
                f"{type(self).__name__}.possible_states, "
                f"got state={state}, possible_states={self.possible_states}"
            )

        blit_offset_image = self._image_cache[state]  # cache lookup once
        self.image = blit_offset_image.image
        self.blit_offset = blit_offset_image.blit_offset
