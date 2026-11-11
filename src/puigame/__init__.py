"""puigame, UI widgets for pygame-ce.

Every public name is imported from ``puigame`` itself, for example
``from puigame import UI, Button``. The subpackages are private, and their
layout may change in any release.
"""

from puigame._components.skin import DrawnSkin, NoSkin
from puigame._layout.anchor import Anchor
from puigame._styling.style import (
    BundledTypeface,
    FadeProfile,
    Style,
    StyleOverride,
    TextAlign,
    TextHorizontalExtent,
)
from puigame._styling.theme import DEFAULT_THEME, Theme
from puigame._ui.ui import UI
from puigame._widgets.button import Button
from puigame._widgets.container import Container
from puigame._widgets.label import Label
from puigame._widgets.panel import Panel
from puigame._widgets.state import State
from puigame._widgets.toggle_button import ToggleButton
from puigame._widgets.toggle_group import ToggleGroup
from puigame._widgets.widget import Widget

__all__ = [
    "DEFAULT_THEME",
    "UI",
    "Anchor",
    "BundledTypeface",
    "Button",
    "Container",
    "DrawnSkin",
    "FadeProfile",
    "Label",
    "NoSkin",
    "Panel",
    "State",
    "Style",
    "StyleOverride",
    "TextAlign",
    "TextHorizontalExtent",
    "Theme",
    "ToggleButton",
    "ToggleGroup",
    "Widget",
]
