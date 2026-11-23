"""FitSize, a widget size that can fit either axis, and FitSource.

FitSource says what a widget class fits a ``None`` axis to.
"""

from enum import Enum, auto
from typing import TypeAlias

from pygame.typing import Point

FitSize: TypeAlias = Point | tuple[float | None, float | None]
"""``(width, height)`` in pixels; ``None`` fits that axis to the content.

The content depends on the widget: the text, for a text widget, or the
children, for a panel.
"""


class FitSource(Enum):
    """What a widget class fits a ``None`` axis of its ``size`` to.

    Each widget class sets one as ``_fit_source``. Whether a widget fits an
    axis at all comes from the ``size`` it was given.

    - ``NO_FIT``: nothing, so ``None`` raises ``ValueError``.
    - ``COMPONENTS``: the largest preferred size among the widget's
      components, measured on creation and whenever its content changes.
    - ``CHILDREN``: the widget's children, measured by its ``_measure()`` at
      each layout pass. The axis is 0 until the first pass.
    """

    NO_FIT = auto()
    COMPONENTS = auto()
    CHILDREN = auto()
