"""Widget, the base class that every puigame widget extends."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar

import pygame as pg
from pygame.typing import Point

from puigame.components.skin import BlitOffsetImage, Skin
from puigame.themes.theme import Theme

from .anchor import Anchor
from .state import State

if TYPE_CHECKING:
    from .ui_root import UIRoot


class Widget(pg.sprite.Sprite):
    """Base class for all puigame widgets.

    A Widget is a pygame Sprite that provides:

    - a rect, sized on creation and positioned by its anchors
    - a parent to anchor against, fixed on creation, and its children
    - a skin that draws its images, in the theme held by the tree's
      ``UIRoot``
    - ``enabled`` and ``visible`` flags, with ``_in_tree`` versions that take
      its ancestors into account
    - its current State, and the States it can be in
    """

    possible_states: ClassVar[tuple[State, ...]] = (State.BASE, State.DISABLED)

    _margin: pg.Vector2
    _offset: pg.Vector2

    def __init__(
        self,
        parent: Widget,
        size: Point,
        skin: Skin,
        *,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
    ) -> None:
        """Create a widget as the last child of ``parent``.

        The widget's images are built straight away, in the theme of the tree's
        ``UIRoot``.

        Args:
            parent: Widget to anchor against and to be a child of. It cannot be
                changed later.
            size: Width and height in pixels.
            skin: Skin that draws the widget's images.
            anchor: Point on this widget used for positioning.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points.
                Positive values move the widget from its anchor point towards
                its own centre, and negative values move it the other way.
                Ignored on centred axes. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the widget responds to input.
            visible: Whether the widget is drawn.

        Raises:
            ValueError: If either dimension of ``size`` is negative. The widget
                is not added to ``parent``.
            TypeError: If ``margin`` or ``offset`` is a single number rather
                than an ``(x, y)`` pair. The widget is not added to ``parent``.
        """
        self._parent: Widget | None = parent
        # parents are fixed, so a widget's root never changes
        self._root: UIRoot = self._parent._root

        self._setup(
            size,
            skin,
            anchor=anchor,
            parent_anchor=parent_anchor,
            margin=margin,
            offset=offset,
            enabled=enabled,
            visible=visible,
        )

        # join the parent only once setup has succeeded, so that a widget whose
        # setup raised is never left in the tree
        self._parent._children.append(self)

    def _setup(
        self,
        size: Point,
        skin: Skin,
        *,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
    ) -> None:
        """Set up everything that ``Widget`` and ``UIRoot`` share.

        ``Widget.__init__()`` calls this after linking the widget to its parent,
        and ``UIRoot.__init__()``, which has no parent, after setting up the
        root and its theme. Either way, the theme must be reachable before this
        runs, since the images are built at the end. The arguments are the same
        as ``Widget.__init__()``'s.

        Raises:
            ValueError: If either dimension of ``size`` is negative.
            TypeError: If ``margin`` or ``offset`` is a single number rather
                than an ``(x, y)`` pair.
        """
        if min(size[0], size[1]) < 0:
            raise ValueError(f"size cannot be negative, got {size} px")

        super().__init__()
        self._rect = pg.Rect((0, 0), size)
        self.skin = skin

        self._children: list[Widget] = []

        self.anchor = anchor
        if parent_anchor is None:
            self.parent_anchor = self.anchor
        else:
            self.parent_anchor = parent_anchor

        self.margin = margin
        self.offset = offset

        self.enabled = enabled
        self.visible = visible

        self._image_cache: dict[State, BlitOffsetImage] = {}
        self.image: pg.Surface
        self.blit_offset: tuple[int, int]
        # needs the flags above, since it picks the image for the current state
        self.rebuild_image_cache()

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
            "rect cannot be set directly; "
            "position the widget via anchor, parent_anchor, margin, and offset"
        )

    @property
    def parent(self) -> Widget | None:
        """The widget this one is anchored against, or ``None`` for a ``UIRoot``.

        Set on creation and never changed, so it is read-only.
        """
        return self._parent

    @property
    def children(self) -> tuple[Widget, ...]:
        """The widget's children, in the order they were created.

        Returned as a tuple, so it cannot be changed directly.
        """
        return tuple(self._children)

    @property
    def theme(self) -> Theme:
        """The theme the widget draws with, held by the tree's ``UIRoot``."""
        return self._root.theme

    @property
    def margin(self) -> pg.Vector2:
        """The margin as an ``(x, y)`` vector.

        Assigning any ``(x, y)`` pair, such as a tuple or another ``Vector2``,
        stores a copy as a ``Vector2``, so it can be changed in place.
        Assigning a single number raises ``TypeError``.
        """
        return self._margin

    @margin.setter
    def margin(self, value: Point) -> None:
        if isinstance(value, (int, float)):
            raise TypeError(
                f"margin cannot be a single value, got {value!r}; "
                "margin must be an (x, y) pair"
            )

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
                "offset must be an (x, y) pair"
            )
        self._offset = pg.Vector2(value)

    @property
    def enabled_in_tree(self) -> bool:
        """Whether this widget and all of its ancestors are enabled."""
        if self.parent is None:
            return self.enabled
        else:
            return self.enabled and self.parent.enabled_in_tree

    @property
    def visible_in_tree(self) -> bool:
        """Whether this widget and all of its ancestors are visible."""
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

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Refresh ``image`` and ``blit_offset`` from the current state each frame."""
        super().update(*args, **kwargs)

        self._refresh_current_image_blit_offset()

    def kill(self) -> None:
        """Remove the widget and its descendants from the tree and all groups.

        Extends ``Sprite.kill()``: the widget leaves its parent's children, each
        of its children is killed in turn, and every one of them leaves all its
        sprite groups. Like ``Sprite.kill()``, it can safely be called more than
        once. A killed widget keeps its link to its old parent, but should not
        be used again.
        """
        # all widgets have a parent apart from UIRoot, which overrides kill()
        assert self.parent is not None

        if self in self.parent._children:  # skip if an earlier kill() removed it
            self.parent._children.remove(self)

        for child in self.children:
            child.kill()

        super().kill()

    def place_at_pos(self, pos: Point) -> None:
        """Place the widget's top-left corner at ``pos``.

        Shorthand for absolute placement: sets ``anchor`` and ``parent_anchor``
        to ``Anchor.TOP_LEFT`` and ``margin`` to ``pos``. The position is
        relative to the parent's top-left corner, which for a top-level widget
        (one created with ``ui.root`` as its parent) is the top-left of the UI's
        area. Layout still runs as normal, so the widget moves with its parent.

        Args:
            pos: ``(x, y)`` position of the widget's top-left corner, in pixels
                from the parent's top-left corner.

        Raises:
            TypeError: If ``pos`` is a single number rather than an ``(x, y)``
                pair. The widget is left unchanged.
        """
        if isinstance(pos, (int, float)):
            raise TypeError(
                f"pos cannot be a single value, got {pos!r}; pos must be an (x, y) pair"
            )

        self.anchor = Anchor.TOP_LEFT
        self.parent_anchor = Anchor.TOP_LEFT
        self.margin = pos

    def iter_descendants(self) -> Iterator[Widget]:
        """Yield every widget below this one in the tree, parents first.

        The order is depth-first pre-order: each child is followed by all of its
        own descendants before the next child. The widget itself is not
        included. The tree is read as it is walked, so take a ``list()`` first
        if the walk will kill widgets.

        Yields:
            Each descendant, in depth-first pre-order.
        """
        for child in self.children:
            yield child
            yield from child.iter_descendants()

    def rebuild_image_cache(self) -> None:
        """Render every state in ``possible_states`` and cache the results.

        Each state's image is cached together with its blit offset, as a
        ``BlitOffsetImage``, using the theme's style for that state.
        """
        for state in self.possible_states:
            self._image_cache[state] = self._render_state_image(state)

        self._refresh_current_image_blit_offset()

    def _render_state_image(self, state: State) -> BlitOffsetImage:
        """Return a new image and its blit offset for ``state``.

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
        state = self.current_state  # read the property once

        if state not in self.possible_states:
            raise RuntimeError(
                "current_state is not in possible_states, "
                f"got state={state}, possible_states={self.possible_states}; "
                f"add {state} to {type(self).__name__}.possible_states"
            )

        blit_offset_image = self._image_cache[state]  # look up once
        self.image = blit_offset_image.image
        self.blit_offset = blit_offset_image.blit_offset
