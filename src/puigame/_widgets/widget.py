"""Widget, the base class that every puigame widget extends."""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, ClassVar, Never, NoReturn, assert_never

import pygame as pg
from pygame.typing import Point

from puigame._components.placed_image import PlacedImage, compose_layers
from puigame._components.skin import Skin
from puigame._layout.anchor import Anchor, get_pos_from_anchor_match
from puigame._layout.fit_size import FitSize, FitSource
from puigame._styling.style import Style
from puigame._styling.theme import Theme
from puigame._validation import validate_fit_size, validate_pair
from puigame._widgets.state import State

if TYPE_CHECKING:
    from puigame._components.component import Component
    from puigame._ui.ui import UI


def _resolve_size(
    requested_size: FitSize,
    fit_source: FitSource,
    components: tuple[Component, ...],
    base_style: Style,
) -> tuple[int, int]:
    """Return the size to build a widget's rect from.

    Fixed axes of ``requested_size`` are rounded down to whole pixels. What a
    ``None`` axis becomes depends on ``fit_source``: with ``COMPONENTS``, the
    largest preferred size on that axis among ``components``, measured in
    ``base_style``; with ``CHILDREN``, 0, since the widget has no children
    yet and fits them in ``_measure()`` at each layout pass. The components
    are measured only when an axis is ``None``.

    Args:
        requested_size: Size the widget was given, already validated.
        fit_source: What a ``None`` axis fits to, from the widget's class.
        components: Components to fit the ``None`` axes to, with
            ``COMPONENTS``.
        base_style: Style to measure the components in.

    Returns:
        ``(width, height)`` in whole pixels.

    Raises:
        ValueError: If either axis is ``None`` and ``fit_source`` is
            ``NO_FIT``, or is ``COMPONENTS`` and there are no components.
    """
    width, height = requested_size
    if width is not None and height is not None:
        return (math.floor(width), math.floor(height))

    if width is not None:
        width = math.floor(width)

    if height is not None:
        height = math.floor(height)

    match fit_source:
        case FitSource.NO_FIT:
            raise ValueError(
                "size cannot have None on an axis of a widget that does not fit "
                f"its content, got {requested_size!r}"
            )

        case FitSource.COMPONENTS:
            if not components:
                raise ValueError(
                    "size cannot have None on an axis of a widget with no "
                    f"components to fit to, got {requested_size!r}"
                )

            preferred_sizes = [
                component.get_preferred_size(base_style) for component in components
            ]

            if width is None:
                width = max(preferred_size[0] for preferred_size in preferred_sizes)

            if height is None:
                height = max(preferred_size[1] for preferred_size in preferred_sizes)

        case FitSource.CHILDREN:
            if width is None:
                width = 0

            if height is None:
                height = 0

        case _:
            assert_never(fit_source)

    return (width, height)


class Widget:
    """Base class for all puigame widgets.

    A Widget provides:

    - a rect, sized as given or fitted to its content (its components, or a
      panel's children), and placed against its parent's by its anchors,
      margin, and offset, on creation and by each layout pass
    - a parent to anchor against, fixed on creation, and its children
    - a skin, fixed on creation, that draws its images in the UI's theme
    - ``enabled`` and ``visible`` flags, with ``_in_tree`` versions that take
      its ancestors into account
    - a ``hit_testable`` flag, deciding whether hit-testing can stop on it, so
      that mouse clicks over it stop at it or pass through to whatever is below
    - an image for each state it can be in, rendered on creation, so that
      ``image`` follows its flags
    """

    _possible_states: ClassVar[tuple[State, ...]] = (State.BASE, State.DISABLED)
    _fit_source: ClassVar[FitSource] = FitSource.NO_FIT

    def __init__(
        self,
        parent: Widget | UI,
        *,
        size: FitSize,
        skin: Skin,
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        hit_testable: bool = True,
        components: Iterable[Component] = (),
    ) -> None:
        """Create a widget as the last child of ``parent``.

        The widget's images are built straight away, in the UI's theme, and it
        is placed against its parent.

        Args:
            parent: Widget or ``UI`` to anchor against and to be a child of. A
                widget whose parent is the ``UI`` is a top-level widget. It
                cannot be changed later.
            size: Width and height in pixels. Whether ``None`` is allowed on
                an axis, and what it fits that axis to, depends on the class:
                a widget that fits its components takes the largest preferred
                size among them, measured in the theme's base style; one that
                fits its children starts at 0 and fits them at each layout
                pass; and a plain ``Widget`` fits nothing. Other values are
                rounded down to whole pixels.
            skin: Skin that draws the widget's images.
            anchor: Point on this widget used for positioning. Fixed on
                creation. Defaults to ``Anchor.CENTRE``.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Fixed on creation. Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points.
                Positive values move the widget from its anchor point towards
                its own centre, and negative values move it the other way.
                Ignored on centred axes. Fixed on creation. Defaults to no
                margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. It can be changed later
                through ``offset``. Defaults to no shift.
            enabled: Whether the widget responds to input. Defaults to ``True``.
            visible: Whether the widget is drawn. Defaults to ``True``.
            hit_testable: Whether the mouse can hit the widget, so that clicks
                over it stop at it rather than passing to the widgets below it
                and to the game. A hidden widget is never hit, but a disabled
                one still is. It can be changed later through
                ``hit_testable``. Defaults to ``True``.
            components: Parts drawn above the skin, in the order given, each
                rendered at the widget's size in the theme's style for each
                state, and measured to fit any ``None`` axis of ``size``. Fixed
                on creation. Internal: for puigame's own widgets,
                since subclassing ``Widget`` is not yet supported. Defaults to
                no components.

        Raises:
            TypeError: If ``anchor`` is not an ``Anchor``, if ``parent_anchor``
                is neither an ``Anchor`` nor ``None``, if ``size`` is not an
                ``(x, y)`` pair of numbers or ``None``, or if ``margin`` or
                ``offset`` is not an ``(x, y)`` pair of numbers. The widget is
                not added to ``parent``.
            ValueError: If either dimension of ``size`` is negative, if either
                is ``None`` and the widget's class fits nothing, or fits its
                components and it has none, or if ``parent`` is a box and
                ``anchor``, ``parent_anchor``, or ``margin`` is not its
                default. The widget is not added to ``parent``.
        """
        if not isinstance(anchor, Anchor):
            raise TypeError(f"anchor must be an Anchor, got {anchor!r}")

        if parent_anchor is not None and not isinstance(parent_anchor, Anchor):
            raise TypeError(
                f"parent_anchor must be an Anchor or None, got {parent_anchor!r}",
            )

        self._parent: Widget | UI = parent
        # parents are fixed, so a widget's UI never changes; it is set before
        # the images are built below, since they read its theme
        self._ui: UI
        if isinstance(self._parent, Widget):
            self._ui = self._parent._ui
        else:
            self._ui = self._parent

        self._components = tuple(components)

        validate_fit_size("size", size)
        # copied, so that later changes to the caller's sequence cannot change
        # what a re-fit reads
        self._requested_size = (size[0], size[1])
        size = _resolve_size(
            self._requested_size,
            self._fit_source,
            self._components,
            self.theme.base_style,
        )

        self._rect = pg.Rect((0, 0), size)
        self._skin = skin

        self._children: list[Widget] = []

        self._anchor = anchor
        if parent_anchor is None:
            self._parent_anchor = self._anchor
        else:
            self._parent_anchor = parent_anchor

        validate_pair("margin", margin)
        self._margin = pg.Vector2(margin)

        self.offset = offset

        self.enabled = enabled
        self.visible = visible
        self.hit_testable = hit_testable

        self._placed_image_cache: dict[State, PlacedImage] = {}
        self._placed_image: PlacedImage
        # needs the components above to render, and the flags to pick the image
        # for the current state
        self._rebuild_image_cache()

        self._place()

        # join the parent only once setup has succeeded, so that a widget whose
        # setup raised is never left in the tree
        self._parent._add_child(self)

    def __repr__(self) -> str:
        """Return a representation for debugging."""
        return f"<puigame widget: {type(self).__name__}, {self.rect}>"

    @property
    def rect(self) -> pg.Rect:
        """The widget's rect, in the coordinates of the UI's draw surface.

        It is placed against the parent's rect when the widget is created, and
        updated in place by layout each frame. Assigning to it raises
        ``AttributeError``, since position comes from the anchors, margin, and
        offset.
        """
        return self._rect

    @rect.setter
    def rect(self, value: Never) -> NoReturn:
        raise AttributeError(
            "rect cannot be set directly; "
            "position the widget via anchor, parent_anchor, margin, and offset",
        )

    @property
    def image(self) -> pg.Surface:
        """The widget's current image, drawn at ``image_pos``.

        The image comes from the skin, using the theme's style for the current
        state. Assigning to it raises ``AttributeError``, since it is rendered
        from the widget's skin, theme, and state.
        """
        return self._placed_image.image

    @image.setter
    def image(self, value: Never) -> NoReturn:
        raise AttributeError(
            "image cannot be set directly; "
            "it is derived from the widget's skin, theme, and state",
        )

    @property
    def image_pos(self) -> tuple[int, int]:
        """The position of ``image``'s top-left corner, relative to ``rect.topleft``.

        Add it to ``rect.topleft`` to get the drawing position. Negative on an
        axis where the image starts above or to the left of the rect, for
        example when a halo extends past the widget's edges.
        """
        return self._placed_image.pos

    @property
    def parent(self) -> Widget | UI:
        """The widget or ``UI`` this one is anchored against.

        Set on creation and never changed, so it is read-only.
        """
        return self._parent

    @property
    def skin(self) -> Skin:
        """The skin that draws the widget's images.

        Set on creation and never changed, so it is read-only.
        """
        return self._skin

    @property
    def children(self) -> tuple[Widget, ...]:
        """The widget's children, in the order they were created.

        Returned as a tuple, so it cannot be changed directly.
        """
        return tuple(self._children)

    @property
    def theme(self) -> Theme:
        """The theme the widget draws with, held by its ``UI``."""
        return self._ui.theme

    @property
    def offset(self) -> pg.Vector2:
        """The offset as an ``(x, y)`` vector in screen coordinates.

        Applied after the anchor and margin, with ``+x`` to the right and ``+y``
        downwards. Assigning any ``(x, y)`` pair, such as a tuple or another
        ``Vector2``, stores a copy as a ``Vector2``, so it can be changed in
        place, for example to animate the widget. Changes take effect at the
        next layout pass.

        Assigning anything but an ``(x, y)`` pair of numbers raises
        ``TypeError``.
        """
        return self._offset

    @offset.setter
    def offset(self, value: Point) -> None:
        validate_pair("offset", value)
        self._offset = pg.Vector2(value)

    @property
    def enabled_in_tree(self) -> bool:
        """Whether this widget and all of its ancestors are enabled."""
        if not isinstance(self.parent, Widget):
            return self.enabled

        return self.enabled and self.parent.enabled_in_tree

    @property
    def visible_in_tree(self) -> bool:
        """Whether this widget and all of its ancestors are visible."""
        if not isinstance(self.parent, Widget):
            return self.visible

        return self.visible and self.parent.visible_in_tree

    def kill(self) -> None:
        """Remove the widget and its descendants from the tree.

        The widget leaves its parent's children, and each of its children is
        killed in turn. It can safely be called more than once. A killed widget
        keeps its link to its old parent, but should not be used again.
        """
        self.parent._remove_child(self)

        for child in self.children:
            child.kill()

    def _set_to_resolved_size(self) -> None:
        """Resize the rect to fit the size the widget was created with.

        Each ``None`` axis of the requested size is fitted again to the
        components' current preferred sizes; a fixed axis keeps its size. The
        rect is resized in place, keeping its top-left corner, and the next
        layout pass places it again.
        """
        self._rect.size = _resolve_size(
            self._requested_size,
            self._fit_source,
            self._components,
            self.theme.base_style,
        )

    def _refresh_after_content_change(self) -> None:
        """Re-fit the size and redraw the images after a component changes.

        A widget calls this after changing what one of its components shows,
        such as a label's text. The images are rebuilt after resizing, since
        they are rendered at the rect's size.
        """
        self._set_to_resolved_size()
        self._rebuild_image_cache()

    def _measure(self) -> None:
        """Set the widget's size from its contents, before it is placed.

        ``UI.update()`` calls this for every widget each frame, children before
        parents, so every descendant has already been measured. Boxes and
        panels override it to fit their children. The default does
        nothing, since a fixed size never changes and a widget that fits its
        text measures itself when the text is set, so overrides need not call
        ``super()``.
        """

    def _place(self) -> None:
        """Place the rect where the parent's ``_get_child_pos()`` puts it.

        Most parents place the widget by its own anchors, margin, and offset;
        a box stacks its children. The rect is updated in place, in the
        coordinates of the surface the UI draws on. The parent, a widget or the
        ``UI``, must already be placed, since its rect is read as it is.
        """
        self.rect.topleft = self.parent.rect.topleft
        self.rect.move_ip(self.parent._get_child_pos(self))

    @property
    def _anchored_pos(self) -> tuple[int, int]:
        """The position the anchors, margin, and offset give against the parent.

        Measured from the parent's top-left corner, with ``+x`` to the right
        and ``+y`` down, in whole pixels, rounded down once after the offset is
        added.
        """
        return get_pos_from_anchor_match(
            child_size=self.rect.size,
            child_anchor=self._anchor,
            parent_size=self.parent.rect.size,
            parent_anchor=self._parent_anchor,
            margin=self._margin,
            offset=self.offset,
        )

    def _update(self) -> None:
        """Refresh ``image`` and ``image_pos`` from the current state.

        ``UI.update()`` calls this for every widget each frame, after the layout
        pass.
        """
        self._refresh_current_placed_image()

    def _iter_subtree(self) -> Iterator[Widget]:
        """Yield this widget and every widget below it in the tree, parents first.

        The order is depth-first pre-order: the widget itself, then each child
        followed by all of its own descendants before the next child. The tree
        is read as it is walked, so take a ``list()`` first if the walk will
        kill widgets.

        Yields:
            This widget, then each descendant, in depth-first pre-order.
        """
        yield self

        for child in self.children:
            yield from child._iter_subtree()

    def _iter_visible_subtree(self) -> Iterator[Widget]:
        """Yield this widget and the widgets below it, skipping hidden subtrees.

        The order is the same depth-first pre-order as ``_iter_subtree()``, but
        a widget that is not ``visible`` is skipped along with everything below
        it. Only ``visible`` is read, not ``visible_in_tree``, so the walk
        ignores the starting widget's ancestors and each widget is checked
        once.

        Yields:
            Each visible widget, in depth-first pre-order.
        """
        if not self.visible:
            return

        yield self

        for child in self.children:
            yield from child._iter_visible_subtree()

    def _iter_subtree_post_order(self) -> Iterator[Widget]:
        """Yield every widget below this one, then this widget, children first.

        The order is depth-first post-order: each child's whole subtree in
        turn, then the widget itself, so every widget comes after all of its
        descendants. The tree is read as it is walked, so take a ``list()``
        first if the walk will kill widgets.

        Yields:
            Each descendant, then this widget, in depth-first post-order.
        """
        for child in self.children:
            yield from child._iter_subtree_post_order()

        yield self

    def _rebuild_image_cache(self) -> None:
        """Render every state in ``_possible_states`` and cache the results.

        Each state's image is cached together with its position, as a
        ``PlacedImage``, using the theme's style for that state.
        """
        for state in self._possible_states:
            self._placed_image_cache[state] = self._render_state_placed_image(state)

        self._refresh_current_placed_image()

    def _render_state_placed_image(self, state: State) -> PlacedImage:
        """Return a new image and its position for ``state``.

        Renders the skin, then each component in the order given, all at the
        rect's size in the theme's style for ``state``. The layers are combined
        with ``compose_layers()``, so the skin is at the bottom and the result
        covers every layer. With no components, the result is the skin's.
        """
        style = self.theme._style_for(state)

        skin_layer = self.skin.render(self.rect.size, style)
        component_layers = [
            component.render(self.rect.size, style) for component in self._components
        ]

        return compose_layers([skin_layer, *component_layers])

    def _refresh_current_placed_image(self) -> None:
        """Show the cached image and position for the widget's current state.

        Reads ``_current_state`` once and looks up its ``PlacedImage`` in the
        image cache. Called whenever the cache is rebuilt, and each frame by
        ``_update()`` so the image follows changes to the widget's and its
        ancestors' flags.

        Raises:
            RuntimeError: If ``_current_state`` is not in ``_possible_states``,
                which means the class's ``_possible_states`` is missing a
                combination its flags can produce.
        """
        state = self._current_state  # read the property once

        if state not in self._possible_states:
            raise RuntimeError(
                "_current_state is not in _possible_states, "
                f"got state={state}, _possible_states={self._possible_states}; "
                f"add {state} to {type(self).__name__}._possible_states",
            )

        self._placed_image = self._placed_image_cache[state]

    @property
    def _current_state(self) -> State:
        """The widget's current State, built from its flags.

        Subclasses extend this by calling ``super()._current_state`` and adding
        their own flags.
        """
        state = State.BASE

        if not self.enabled_in_tree:
            state |= State.DISABLED

        return state

    def _get_child_pos(self, child: Widget) -> tuple[int, int]:
        """Return where ``child`` goes, from this widget's top-left corner.

        The default places ``child`` by its own anchors, margin, and offset.
        A widget that arranges its children, such as a box, overrides this.
        ``child._place()`` calls it, including once while ``child`` is being
        created, before it has joined, so an override must handle a child it
        does not hold yet.

        Args:
            child: The widget being placed, whose parent is this widget.

        Returns:
            ``(x, y)`` position of the child's top-left corner, in whole pixels
            from this widget's top-left corner.
        """
        return child._anchored_pos

    def _before_child_added(self, child: Widget) -> None:
        """Check that ``child`` can join this widget's children.

        ``_add_child()`` calls this just before ``child`` joins. An override
        raises to refuse the child, and must change nothing first, since a
        refused child never joins. The default accepts every child and does
        nothing, so overrides need not call ``super()``.

        Args:
            child: The widget about to join, already set up.
        """

    def _add_child(self, child: Widget) -> None:
        """Add ``child`` as the last of this widget's children, if allowed.

        ``_before_child_added()`` runs first, and if it raises, ``child`` is not
        added. ``child``'s own ``__init__`` calls this once, as the last step of
        its setup.

        Args:
            child: The new widget, whose parent is this widget.
        """
        # called once, from the new child's own __init__
        assert child not in self._children

        self._before_child_added(child)
        self._children.append(child)

    def _remove_child(self, child: Widget) -> None:
        """Remove ``child`` from this widget's children, if it is still there.

        ``child.kill()`` calls this. A child that an earlier ``kill()`` already
        removed is ignored, so ``kill()`` can safely be called more than once.

        Args:
            child: The widget leaving, whose parent is this widget.
        """
        if child in self._children:
            self._children.remove(child)
