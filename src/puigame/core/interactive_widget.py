"""InteractiveWidget, the base class for widgets the user can interact with.

InteractiveWidget extends Widget with the highlight and activation behaviour
that interactive widgets share. Button, Checkbox, and TextBox build on it.

It lives in ``core`` so that the UIManager can recognise interactive widgets
with ``isinstance()`` without importing from ``widgets``.
"""

from collections.abc import Iterable
from typing import ClassVar

from pygame.typing import Point

from puigame._components.component import Component
from puigame._components.skin import Skin
from puigame._layout.anchor import Anchor
from puigame.core.state import State
from puigame.core.widget import Widget


class InteractiveWidget(Widget):
    """Base class for widgets that the mouse can highlight and activate.

    An InteractiveWidget adds ``HIGHLIGHTED`` to the states a widget can be in.
    The ``UIManager`` highlights it while the cursor is over it, and presses
    and activates it with the left mouse button. A disabled widget is never
    highlighted, pressed, or activated, and draws its disabled look instead.
    Subclasses respond to a click by overriding ``_activate()``, and add their
    own states, such as ``PRESSED``.
    """

    _possible_states: ClassVar[tuple[State, ...]] = (
        State.BASE,
        State.DISABLED,
        State.HIGHLIGHTED,
    )

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
        components: Iterable[Component] = (),
    ) -> None:
        """Create an interactive widget as the last child of ``parent``.

        The widget starts neither highlighted nor pressed. The ``UIManager``
        changes both as the mouse moves and clicks.

        Args:
            parent: Widget to anchor against and to be a child of. It cannot be
                changed later.
            size: Width and height in pixels.
            skin: Skin that draws the widget's images.
            anchor: Point on this widget used for positioning. Fixed on
                creation.
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
            enabled: Whether the widget responds to input.
            visible: Whether the widget is drawn.
            consumes_clicks: Whether mouse clicks over the widget stop at it,
                rather than passing to the widgets below it and to the game. A
                hidden widget never stops clicks, but a disabled one still
                does. It can be changed later through ``consumes_clicks``.
                Defaults to ``True``.
            components: Parts drawn above the skin, in the order given, each
                rendered at the widget's size in the theme's style for each
                state. Fixed on creation. Internal: for puigame's own widgets,
                since subclassing ``Widget`` is not yet supported. Defaults to
                no components.

        Raises:
            ValueError: If either dimension of ``size`` is negative. The widget
                is not added to ``parent``.
            TypeError: If ``margin`` or ``offset`` is a single number rather
                than an ``(x, y)`` pair. The widget is not added to ``parent``.
        """
        # set first, since super().__init__() picks the image through _current_state
        self._highlighted = False
        self._pressed = False

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
            components=components,
        )

    @property
    def _current_state(self) -> State:
        """The widget's current State, adding ``HIGHLIGHTED`` while highlighted.

        ``DISABLED`` suppresses ``HIGHLIGHTED``, so a disabled widget never
        looks interactive.
        """
        state = super()._current_state

        if State.DISABLED not in state and self._highlighted:
            state |= State.HIGHLIGHTED

        return state

    def _activate(self) -> None:
        """Respond to a click on the widget.

        The ``UIManager`` calls this when a left press that started on the
        widget is released over it while it is enabled. It does nothing here,
        and subclasses override it.
        """
        pass
