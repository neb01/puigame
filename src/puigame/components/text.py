"""Text, the component that displays text on a widget."""

from functools import cache
from importlib.resources import files
from pathlib import Path

import pygame as pg
from pygame.typing import Point

from puigame.themes.theme import BundledTypeface, Style


@cache
def _get_font(
    *,
    typeface: BundledTypeface | Path,
    size: int,
    bold: bool,
    underlined: bool,
    italic: bool,
) -> pg.Font:
    """Return a font for a typeface and settings, loading it on first use.

    Results are cached by all five arguments, so every caller that passes the
    same arguments receives the same font object. Callers must not change the
    returned font, for example by setting ``bold``, since that would change it
    for every other caller too.

    Args:
        typeface: Bundled typeface, or path to a font file supplied by the game.
        size: Font size, in pixels.
        bold: Whether the font is bold.
        underlined: Whether the font is underlined.
        italic: Whether the font is italic.

    Returns:
        The font, shared with every caller that passes the same arguments.

    Raises:
        FileNotFoundError: If the typeface's font file does not exist.
    """
    if typeface is BundledTypeface.PYGAME_DEFAULT:
        font = pg.Font(None, size)
    elif isinstance(typeface, BundledTypeface):
        # files() returns a Traversable, which pg.Font's type hints do not
        # accept. str() gives its filesystem path, which assumes puigame is
        # installed as files on disk rather than imported from a zip archive.
        filepath = str(files("puigame") / "assets" / "fonts" / typeface.value)
        font = pg.Font(filepath, size)
    else:  # user-defined path
        font = pg.Font(typeface, size)

    font.bold = bold
    font.underline = underlined
    font.italic = italic

    return font


class Text:
    """."""

    def __init__(self, content: str = "") -> None:
        """."""
        self.content = content

    def render(self, size: Point, style: Style) -> pg.Surface:
        """."""
        font = _get_font(
            typeface=style.text_typeface,
            size=style.text_font_size,
            bold=style.text_is_bold,
            underlined=style.text_is_underlined,
            italic=style.text_is_italic,
        )

        return font.render(self.content, antialias=True, color=style.text_colour)
