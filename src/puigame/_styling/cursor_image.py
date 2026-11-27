"""CursorImage, an image drawn as the mouse cursor, with its hotspot."""

import io
from enum import Enum, unique
from functools import cache
from importlib.resources import files
from typing import Self

import pygame as pg
from pygame.typing import Point

from puigame._floor_pair import floor_pair
from puigame._validation import validate_enum, validate_pair

_ARROW_HOTSPOT = (0, 0)
_CROSSHAIR_HOTSPOT = (4, 4)
_HAND_HOTSPOT = (3, 0)
_I_BEAM_HOTSPOT = (4, 7)


@unique
class BundledCursor(Enum):
    """Cursor images bundled with puigame.

    Each member is named ``<SET>_<SHAPE>``. The ``DARK``, ``GREEN``, and
    ``LIGHT`` sets each have an arrow, a crosshair, a hand, and an I-beam, all
    16 by 16 pixels. Each member's value is the file name of its image in
    puigame's ``assets/cursors`` folder and its hotspot. Pass a member to
    ``CursorImage.bundled()`` to get a cursor image.
    """

    _value_: tuple[str, tuple[int, int]]

    DARK_ARROW = ("dark_arrow.png", _ARROW_HOTSPOT)
    DARK_CROSSHAIR = ("dark_crosshair.png", _CROSSHAIR_HOTSPOT)
    DARK_HAND = ("dark_hand.png", _HAND_HOTSPOT)
    DARK_I_BEAM = ("dark_i_beam.png", _I_BEAM_HOTSPOT)
    GREEN_ARROW = ("green_arrow.png", _ARROW_HOTSPOT)
    GREEN_CROSSHAIR = ("green_crosshair.png", _CROSSHAIR_HOTSPOT)
    GREEN_HAND = ("green_hand.png", _HAND_HOTSPOT)
    GREEN_I_BEAM = ("green_i_beam.png", _I_BEAM_HOTSPOT)
    LIGHT_ARROW = ("light_arrow.png", _ARROW_HOTSPOT)
    LIGHT_CROSSHAIR = ("light_crosshair.png", _CROSSHAIR_HOTSPOT)
    LIGHT_HAND = ("light_hand.png", _HAND_HOTSPOT)
    LIGHT_I_BEAM = ("light_i_beam.png", _I_BEAM_HOTSPOT)

    def __init__(self, file_name: str, hotspot: tuple[int, int]) -> None:
        self._file_name = file_name
        self._hotspot = hotspot


@cache
def _get_bundled_cursor_surface(*, bundled_cursor: BundledCursor) -> pg.Surface:
    """Return a bundled cursor's image, loaded on first use and then cached.

    ``bundled_cursor`` is keyword-only, since ``functools.cache`` keys a
    positional call and a keyword call separately.

    Args:
        bundled_cursor: The cursor whose image to load.

    Returns:
        The cursor's image. The same surface is returned on every call, so
        callers must copy it rather than draw on it.
    """
    # read the image's bytes rather than its path, since a bundled file has
    # no path when puigame is imported from a zip archive; the file name
    # tells pygame the image's format
    bundled_cursor_bytes = (
        files("puigame") / "assets" / "cursors" / bundled_cursor._file_name
    ).read_bytes()

    return pg.image.load(io.BytesIO(bundled_cursor_bytes), bundled_cursor._file_name)


class CursorImage:
    """An image drawn as the mouse cursor, with the pixel that is its point.

    A UI draws the image with its hotspot at the mouse position. The image is
    copied on creation, so drawing on the original later does not change the
    cursor.
    """

    def __init__(
        self,
        image: pg.Surface,
        hotspot: Point,
    ) -> None:
        """Create a cursor image from a copy of ``image``.

        Args:
            image: Image to draw as the cursor. A copy is stored.
            hotspot: ``(x, y)`` of the pixel in ``image`` that is the cursor's
                point, which is drawn at the mouse position. It may lie
                outside the image. A fractional value is rounded down to the
                pixel it lies in, and it is stored as a tuple of ints.

        Raises:
            TypeError: If ``hotspot`` is not an indexable sequence of length 2,
                or if either of its items is not an ``int`` or ``float``, or is
                a ``bool``.
        """
        self._image = image.copy()

        validate_pair("hotspot", hotspot)
        self._hotspot = floor_pair(hotspot)

    @property
    def image(self) -> pg.Surface:
        """Image drawn as the cursor, a copy of the one given on creation."""
        return self._image

    @property
    def hotspot(self) -> tuple[int, int]:
        """``(x, y)`` of the pixel in ``image`` drawn at the mouse position."""
        return self._hotspot

    @classmethod
    def bundled(cls, bundled_cursor: BundledCursor) -> Self:
        """Create a cursor image from one of puigame's bundled cursors.

        Each call returns a new cursor image with its own copy of the image.

        Args:
            bundled_cursor: The bundled cursor to use.

        Returns:
            A cursor image with the bundled cursor's image and hotspot.

        Raises:
            TypeError: If ``bundled_cursor`` is not a ``BundledCursor``.
        """
        validate_enum("bundled_cursor", bundled_cursor, BundledCursor)
        return cls(
            image=_get_bundled_cursor_surface(bundled_cursor=bundled_cursor),
            hotspot=bundled_cursor._hotspot,
        )
