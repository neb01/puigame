"""Label, a non-interactive widget that displays text."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame.typing import Point

from puigame._components.skin import NoSkin
from puigame._components.text import Text
from puigame._layout.anchor import Anchor
from puigame._layout.fit_size import FitSize, FitSource
from puigame._widgets.widget import Widget

if TYPE_CHECKING:
    from puigame._ui.ui import UI


class Label(Widget):
    """Non-interactive widget that displays text, with no background.

    A Label draws one ``Text`` and uses a ``NoSkin``, so its image is the size
    of its text, or 0x0 when the text is empty. For text on a background, place
    a Label in a ``Panel``.

    The text is styled and placed by the theme's style for the label's current
    state, relative to its rect, and is not clipped to the rect.
    """

    _fit_source = FitSource.COMPONENTS

    def __init__(
        self,
        parent: Widget | UI,
        *,
        size: FitSize = (None, None),
        text: str = "",
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        hit_testable: bool = False,
    ) -> None:
        """Create a label as the last child of ``parent``.

        Args:
            parent: Widget or ``UI`` to anchor against and to be a child of. It
                cannot be changed later.
            size: Width and height in pixels. ``None`` on an axis fits that
                axis to the text, measured in the theme's base style: the
                text's placement box, from cap top to baseline, plus
                ``text_margin`` on each side. Empty text's box is one line
                high and 0 wide. Other values are rounded down to whole
                pixels. The text is placed against this rect, so
                ``text_anchor`` has no visible effect on a fitted axis.
                Defaults to ``(None, None)``, which fits both axes.
            text: The text to display. Defaults to an empty string, which draws
                nothing.
            anchor: Point on this label used for positioning. Defaults to
                ``Anchor.CENTRE``.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the label is enabled. A disabled label is drawn in
                the theme's style for the disabled state. Defaults to ``True``.
            visible: Whether the label is drawn. Defaults to ``True``.
            hit_testable: Whether the mouse can hit the label, so that clicks
                over it stop at it. Defaults to ``False``, so a label on a
                button does not block the button, and HUD text does not block
                clicks meant for the game.

        Raises:
            TypeError: If ``text`` is not a string, if ``anchor`` is not an
                ``Anchor``, if ``parent_anchor`` is neither an ``Anchor`` nor
                ``None``, if ``size`` is not an ``(x, y)`` pair of numbers or
                ``None``, or if ``margin`` or ``offset`` is not an ``(x, y)``
                pair of numbers. The label is not added to ``parent``.
            ValueError: If either dimension of ``size`` is negative, or if
                ``parent`` is a row or column and ``anchor``, ``parent_anchor``,
                or ``margin`` is not its default. The label is not added to
                ``parent``.
        """
        # Widget.__init__() renders the components, so the text must exist first
        self._text = Text(text)

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
            components=[self._text],
        )

    @property
    def text(self) -> str:
        """The text the label displays.

        Assigning new text fits each axis of ``size`` given as ``None`` to it
        again and redraws the label's images. The rect's size changes at once,
        and its position at the next ``UI.update()``. Assigning the text it
        already has does nothing. Assigning a value that is not a string raises
        ``TypeError`` and leaves the text unchanged.
        """
        return self._text.content

    @text.setter
    def text(self, value: str) -> None:
        if value == self._text.content:
            return

        self._text.content = value
        self._refresh_after_content_change()
