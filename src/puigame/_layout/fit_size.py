"""FitSize, a widget size that can fit either axis to the widget's content."""

from typing import TypeAlias

from pygame.typing import Point

FitSize: TypeAlias = Point | tuple[float | None, float | None]
"""``(width, height)`` in pixels; ``None`` fits that axis to the content."""
