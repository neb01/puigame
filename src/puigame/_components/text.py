"""Text, the component that displays text on a widget."""

from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import assert_never

import pygame as pg
from pygame.typing import Point

from puigame._components.placed_image import PlacedImage
from puigame._layout.anchor import get_pos_from_anchor_match
from puigame._styling.style import (
    BundledTypeface,
    Style,
    TextAlign,
    TextHorizontalExtent,
)


@cache
def _get_font(
    *,
    typeface: BundledTypeface | Path,
    size: int,
    text_align: TextAlign,
) -> pg.Font:
    """Return a font for a typeface, size, and alignment, loading it on first use.

    Results are cached by all three arguments, so every caller that passes the
    same arguments receives the same font object. The alignment is set once,
    when the font is created. Callers must not change the returned font, for
    example by setting ``bold`` or ``align``, since that would change it for
    every other caller too.

    Args:
        typeface: Bundled typeface, or path to a font file supplied by the game.
        size: Font size, in pixels.
        text_align: How the lines of multi-line text line up with each other.

    Returns:
        The font, shared with every caller that passes the same arguments.

    Raises:
        FileNotFoundError: If the typeface's font file does not exist.
    """
    if typeface is BundledTypeface.PYGAME_DEFAULT:
        font = pg.Font(None, size)

    elif isinstance(typeface, BundledTypeface):
        # files() returns a Traversable, which pg.Font's type hints do not accept;
        # str() gives its filesystem path, which assumes puigame is installed
        # as files on disk rather than imported from a zip archive
        filepath = str(files("puigame") / "assets" / "fonts" / typeface.value)
        font = pg.Font(filepath, size)

    else:  # user-defined path
        font = pg.Font(typeface, size)

    match text_align:
        case TextAlign.LEFT:
            font.align = pg.FONT_LEFT

        case TextAlign.CENTRE:
            font.align = pg.FONT_CENTER

        case TextAlign.RIGHT:
            font.align = pg.FONT_RIGHT

        case _:
            assert_never(text_align)

    return font


@cache
def _get_cap_height(*, font: pg.Font) -> int:
    """Return a font's cap height, the height of ``H`` above the baseline.

    Results are cached by font object, so they stay correct only while the
    font is unchanged. Fonts from ``_get_font()`` are never changed.

    Args:
        font: Font to measure.

    Returns:
        Distance in pixels from the baseline to the top of ``H``, or the
        font's ascent if pygame-ce cannot measure ``H``.
    """
    h_metrics = font.metrics("H")

    # pygame-ce's types allow None for a glyph it cannot measure,
    # but a font without H usually reports its .notdef glyph's metrics instead,
    # so this may never run
    if h_metrics[0] is None:
        return font.get_ascent()

    _minx, _maxx, _miny, maxy, _advance = h_metrics[0]

    return maxy


class Text:
    r"""Text drawn on a widget, styled and placed by the widget's style.

    ``Text`` holds only its string. The typeface, font size, colour, and
    placement come from the ``Style`` passed to ``render()``, so the text
    follows the widget's theme and state. It is not a widget: it is not in the
    tree, receives no input, and is drawn into its owner's image.

    The text is placed by its placement box, which is anchored to the widget's
    rect with the style's anchors, margin, and offset. The box runs from the
    top of the first line's capitals to the last line's baseline, so centred
    text is centred on its capitals, and descenders hang below the box. Its
    width depends on the style's ``text_horizontal_extent`` (see
    ``TextHorizontalExtent``). The text is not clipped, so it can extend past
    the rect. It is drawn without antialiasing, and the alpha channel of the
    style's ``text_colour`` sets its transparency.

    Each newline starts a new line, using pygame-ce's own multiline rendering:
    lines are aligned by the style's ``text_align`` (see ``TextAlign``) and
    spaced by the font's line size. Trailing whitespace on each line is not
    drawn (see ``stripped_content``), so it does not affect alignment or the
    placement box, and text that is only whitespace draws nothing. The last
    newline in the text is drawn as a blank space at the end of its line
    rather than starting an empty line, so ``"A\n"`` is one line and
    ``"A\n\n"`` is two. Empty lines count towards the placement box.
    """

    def __init__(self, content: str = "") -> None:
        """Create text with the given content.

        Args:
            content: The text to draw. Defaults to an empty string, which draws
                nothing.

        Raises:
            TypeError: If ``content`` is not a string.
        """
        self.content = content

    @property
    def content(self) -> str:
        """The text to draw.

        An empty string draws nothing. Assigning a value that is not a string
        raises ``TypeError`` and leaves the content unchanged. ``Text`` keeps
        no reference to its owner, so assigning does not redraw anything: the
        owner rebuilds its images after changing the content.
        """
        return self._content

    @content.setter
    def content(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"content must be a string, got {value!r}")

        self._content = value

    @property
    def stripped_content(self) -> str:
        """The content as drawn, with trailing whitespace removed from each line.

        Leading whitespace and newlines are kept, so a final newline is still
        drawn as a blank space at the end of its line. Whitespace is anything
        ``str.rstrip()`` removes, including tabs and non-breaking spaces. A
        line that is only whitespace becomes empty, but its newline is kept.
        Content with nothing to draw, made only of whitespace and newlines,
        gives an empty string, so it draws nothing rather than blank lines.
        """
        if self.content.strip() == "":
            return ""

        return "\n".join(line.rstrip() for line in self.content.split("\n"))

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Render the text and place it for a widget's size and style.

        Args:
            size: ``(width, height)`` of the widget's rect, in pixels, which the
                text is placed against.
            style: Style for the widget's current state. Sets the text's
                typeface, font size, colour, anchors, alignment, horizontal
                extent, margin, and offset.

        Returns:
            The rendered text and its position relative to the widget's
            ``rect.topleft``. Empty text, or text that is only whitespace,
            gives a 0x0 image at ``(0, 0)``.

        Raises:
            FileNotFoundError: If the style's typeface's font file does not
                exist.
        """
        if self.stripped_content == "":
            return PlacedImage.zero_size()

        font = _get_font(
            typeface=style.text_typeface,
            size=style.text_font_size,
            text_align=style.text_align,
        )

        surface = font.render(
            self.stripped_content,
            antialias=False,
            color=style.text_colour,
        )

        surface.set_alpha(style.text_colour[3])

        # the placement box's width, and its left edge inside the surface
        match style.text_horizontal_extent:
            case TextHorizontalExtent.LOGICAL:
                text_lines = self.stripped_content.split("\n")
                placement_box_width = max(
                    font.size(text_line)[0] for text_line in text_lines
                )
                pos_x_correction = 0

            case TextHorizontalExtent.INK:
                ink_rect = surface.get_bounding_rect()
                placement_box_width = ink_rect.width
                pos_x_correction = ink_rect.left

            case _:
                assert_never(style.text_horizontal_extent)

        # the placement box's height, from the first line's cap top to the
        # last line's baseline; lines are counted from the surface, since
        # pygame-ce draws a final newline as a blank glyph, not a new line
        text_line_height = font.get_linesize()
        num_lines = surface.get_height() // text_line_height
        cap_height = _get_cap_height(font=font)
        placement_box_height = cap_height + (num_lines - 1) * text_line_height

        placement_box_pos = get_pos_from_anchor_match(
            child_size=(placement_box_width, placement_box_height),
            child_anchor=style.text_anchor,
            parent_size=size,
            parent_anchor=style.text_parent_anchor,
            margin=style.text_margin,
            offset=style.text_offset,
        )

        # move the surface so that the placement box, which starts inside
        # it, lands where it was anchored
        pos = (
            placement_box_pos[0] - pos_x_correction,
            placement_box_pos[1] - (font.get_ascent() - cap_height),
        )

        return PlacedImage(surface, pos)
