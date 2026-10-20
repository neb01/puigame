"""Text, the component that displays text on a widget."""

from functools import cache
from importlib.resources import files
from pathlib import Path

import pygame as pg
from pygame.typing import Point

from puigame.core.anchor import get_pos_from_anchor_match
from puigame.themes.theme import BundledTypeface, Style

from .placed_image import PlacedImage


@cache
def _get_font(
    *,
    typeface: BundledTypeface | Path,
    size: int,
) -> pg.Font:
    """Return a font for a typeface and size, loading it on first use.

    Results are cached by both arguments, so every caller that passes the same
    arguments receives the same font object. Callers must not change the
    returned font, for example by setting ``bold`` or ``align``, since that
    would change it for every other caller too.

    Args:
        typeface: Bundled typeface, or path to a font file supplied by the game.
        size: Font size, in pixels.

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

    return font


class Text:
    """Text drawn on a widget, styled and placed by the widget's style.

    ``Text`` holds only its string. The typeface, font size, colour, and
    placement come from the ``Style`` passed to ``render()``, so the text
    follows the widget's theme and state. It is not a widget: it is not a
    sprite, receives no input, and is drawn into its owner's image.

    The text is placed relative to the widget's rect with the style's anchors,
    margin, and offset, and is not clipped, so it can extend past the rect. It
    is drawn without antialiasing, and the alpha channel of the style's
    ``text_colour`` sets its transparency.

    Each newline starts a new line, using pygame-ce's own multiline rendering:
    lines are left-aligned and spaced by the font's line size. A trailing
    newline, or text that is only a newline or carriage return, is drawn as a
    glyph rather than as an empty line.

    Attributes:
        content: The text to draw. An empty string draws nothing.
    """

    def __init__(self, content: str = "") -> None:
        """Create text with the given content.

        Args:
            content: The text to draw. Defaults to an empty string, which draws
                nothing.
        """
        self.content = content

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Render the text and place it for a widget's size and style.

        Args:
            size: ``(width, height)`` of the widget's rect, in pixels, which the
                text is placed against.
            style: Style for the widget's current state. Sets the text's
                typeface, font size, colour, anchors, margin, and offset.

        Returns:
            The rendered text and its position relative to the widget's
            ``rect.topleft``. Empty text gives a 0x0 image at ``(0, 0)``.

        Raises:
            FileNotFoundError: If the style's typeface's font file does not
                exist.
        """
        if self.content == "":
            surface = pg.Surface((0, 0), pg.SRCALPHA)
            pos = (0, 0)

        else:
            font = _get_font(
                typeface=style.text_typeface,
                size=style.text_font_size,
            )

            surface = font.render(
                self.content,
                antialias=False,
                color=style.text_colour,
            )

            surface.set_alpha(style.text_colour[3])

            pos = get_pos_from_anchor_match(
                child_size=surface.get_size(),
                child_anchor=style.text_anchor,
                parent_size=size,
                parent_anchor=style.text_parent_anchor,
                margin=style.text_margin,
                offset=style.text_offset,
            )

        return PlacedImage(surface, pos)
