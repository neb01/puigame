"""Label, a non-interactive widget that displays text."""

from pygame.typing import Point

from puigame.components.skin import NoSkin
from puigame.components.text import Text
from puigame.core.anchor import Anchor
from puigame.core.widget import Widget


def _check_text(value: object) -> None:
    """Check that a label's text is a string.

    Args:
        value: The value given for the text.

    Raises:
        TypeError: If ``value`` is not a string.
    """
    if not isinstance(value, str):
        raise TypeError(f"text must be a string, got {value!r}")


class Label(Widget):
    """Non-interactive widget that displays text, with no background.

    A Label draws one ``Text`` and uses a ``NoSkin``, so its image is the size
    of its text, or 0x0 when the text is empty. For text on a background, place
    a Label in a ``Panel``.

    The text is styled and placed by the theme's style for the label's current
    state, relative to its rect, and is not clipped to the rect.
    """

    def __init__(
        self,
        parent: Widget,
        *,
        size: Point,
        text: str = "",
        anchor: Anchor = Anchor.CENTRE,
        parent_anchor: Anchor | None = None,
        margin: Point = (0, 0),
        offset: Point = (0, 0),
        enabled: bool = True,
        visible: bool = True,
        consumes_clicks: bool = False,
    ) -> None:
        """Create a label as the last child of ``parent``.

        Args:
            parent: Widget to anchor against and to be a child of. It cannot be
                changed later.
            size: Width and height in pixels. The text is placed against this
                rect.
            text: The text to display. Defaults to an empty string, which draws
                nothing.
            anchor: Point on this label used for positioning.
            parent_anchor: Point on the parent that ``anchor`` is matched to.
                Defaults to the same point as ``anchor``.
            margin: ``(x, y)`` space between the matched anchor points, as
                for ``Widget``. Defaults to no margin.
            offset: Shift in screen coordinates (``+x`` right, ``+y`` down),
                applied after the anchor and margin. Defaults to no shift.
            enabled: Whether the label is enabled. A disabled label is drawn in
                the theme's style for the disabled state.
            visible: Whether the label is drawn.
            consumes_clicks: Whether mouse clicks over the label stop at it.
                Defaults to ``False``, so a label on a button does not block
                the button, and HUD text does not block clicks meant for the
                game.

        Raises:
            ValueError: If either dimension of ``size`` is negative. The label
                is not added to ``parent``.
            TypeError: If ``text`` is not a string, or if ``margin`` or
                ``offset`` is a single number rather than an ``(x, y)`` pair.
                The label is not added to ``parent``.
        """
        _check_text(text)
        # Widget.__init__ renders the components, so the text must exist first
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
            consumes_clicks=consumes_clicks,
            components=[self._text],
        )

    @property
    def text(self) -> str:
        """The text the label displays.

        Assigning new text redraws the label's images; assigning the text it
        already has does nothing. Assigning a value that is not a string raises
        ``TypeError`` and leaves the text unchanged.
        """
        return self._text.content

    @text.setter
    def text(self, value: str) -> None:
        _check_text(value)

        if value == self._text.content:
            return

        self._text.content = value
        self._rebuild_image_cache()
