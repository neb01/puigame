"""Shared rules for drawing UI elements.

A theme holds a base style and the changes each state makes to it. Skins and
text ask the theme for the style of a widget's current state, so every widget
in a UI is drawn consistently.

``DEFAULT_THEME`` is sized for a 640x360 render surface, scaled up to the
window with ``pg.SCALED``.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from types import MappingProxyType

from puigame.core.anchor import Anchor
from puigame.core.state import State

# A colour as (red, green, blue, alpha), each from 0 to 255.
RGBA = tuple[int, int, int, int]


@dataclass(frozen=True)
class Style:
    """Complete appearance of a widget: every value needed to draw it.

    A theme's base style is a ``Style``, and ``Theme.style_for()`` returns a
    ``Style`` for any combination of state flags. Only the fields that
    ``StyleOverride`` also has can change between states.

    Attributes:
        background_colour: Fill colour as RGBA. The alpha channel controls
            transparency.
        border_colour: Border colour as RGBA.
        border_width_pixels: Border width in pixels. 0 means no border.
        background_corner_radius_pixels: Corner radius in pixels, used for
            both the background and the border.
        halo_colour: Halo colour as RGBA.
        halo_colour_fade_to_clear: Whether the halo fades to transparent
            towards its outer edge.
        halo_thickness_pixels: Halo thickness in pixels. 0 means no halo.
        swell_increase_pixels: How many pixels the widget grows by. 0 means no
            swell.
        text_colour: Text colour as RGBA.
        text_font_name: Name or path of the font used for text, or ``None``
            for pygame-ce's built-in font.
        text_font_size: Font size for text, in pixels.
        text_anchor: Point on the text that is aligned to the widget.
        text_parent_anchor: Point on the widget that the text is aligned to.
        text_margin: Distance in pixels that the text is moved from its anchor
            point towards its own centre, as an ``(x, y)`` pair.
        text_is_bold: Whether text is bold.
        text_is_underlined: Whether text is underlined.
        text_is_italic: Whether text is italic.
    """

    # general appearance options
    background_colour: RGBA  # alpha channel controls transparency
    border_colour: RGBA

    # general appearance options (state-agnostic)
    border_width_pixels: int  # 0 for no border
    background_corner_radius_pixels: int  # also affects border corners

    # effect options
    halo_colour: RGBA
    halo_colour_fade_to_clear: bool
    halo_thickness_pixels: int  # 0 for no halo
    swell_increase_pixels: int  # 0 for no swell

    # text options
    text_colour: RGBA

    # text options (state-agnostic)
    # None gives pygame-ce's built-in font, freesansbold.ttf
    text_font_name: str | None
    text_font_size: int
    text_anchor: Anchor
    text_parent_anchor: Anchor
    text_margin: tuple[int, int]
    text_is_bold: bool
    text_is_underlined: bool
    text_is_italic: bool


@dataclass(frozen=True)
class StyleOverride:
    """Changes that one state makes to a ``Style``.

    Each field matches a field of ``Style``, and only these fields can change
    between states. A field left as ``None`` keeps the value underneath, and
    any other value replaces it. When several states are active, their
    overrides are applied in turn, so a later override wins when two set the
    same field.

    Attributes:
        background_colour: Fill colour as RGBA, or ``None`` to keep it.
        border_colour: Border colour as RGBA, or ``None`` to keep it.
        halo_colour: Halo colour as RGBA, or ``None`` to keep it.
        halo_colour_fade_to_clear: Whether the halo fades to transparent
            towards its outer edge, or ``None`` to keep it.
        halo_thickness_pixels: Halo thickness in pixels, or ``None`` to keep
            it. 0 turns the halo off.
        swell_increase_pixels: How many pixels the widget grows by, or
            ``None`` to keep it. 0 turns the swell off.
        text_colour: Text colour as RGBA, or ``None`` to keep it.
    """

    # general appearance options
    background_colour: RGBA | None = None  # alpha channel controls transparency
    border_colour: RGBA | None = None
    halo_colour: RGBA | None = None
    halo_colour_fade_to_clear: bool | None = None
    halo_thickness_pixels: int | None = None  # 0 for no halo
    swell_increase_pixels: int | None = None  # 0 for no swell

    # text options
    text_colour: RGBA | None = None


@dataclass(frozen=True)
class Theme:
    """Shared drawing rules for every widget in a UI.

    Attributes:
        base_style: Appearance of a widget when no state flags are set.
        style_overrides: Changes each state makes to ``base_style``, keyed by
            state flag. ``State.BASE`` cannot be used as a key, because it is
            part of every state and its override would always apply. Stored as
            a read-only copy.
    """

    base_style: Style
    style_overrides: Mapping[State, StyleOverride]

    def __post_init__(self) -> None:
        """Reject a ``State.BASE`` key and store ``style_overrides`` read-only.

        Raises:
            ValueError: If ``style_overrides`` uses ``State.BASE`` as a key.
        """
        if State.BASE in self.style_overrides:
            raise ValueError("theme.style_overrides cannot use State.BASE as a key.")

        dict_copy = dict(self.style_overrides)
        read_only_view = MappingProxyType(dict_copy)
        object.__setattr__(self, "style_overrides", read_only_view)

    def style_for(self, state: State) -> Style:
        """Return the style for a combination of state flags.

        Starts from ``base_style`` and applies the override for each flag in
        ``state``, in the order ``style_overrides`` holds them. When two
        overrides set the same field, the later one wins.

        Args:
            state: The widget's current state, which can combine several flags.

        Returns:
            A complete style for that state. If no flag in ``state`` has an
            override, this is ``base_style`` itself.
        """
        result = self.base_style

        for flag, style_override in self.style_overrides.items():
            if flag in state:
                changed_fields: dict[str, object] = {}

                for field, value in asdict(style_override).items():
                    if value is not None:
                        changed_fields[field] = value

                result = replace(result, **changed_fields)

        return result


DEFAULT_THEME = Theme(
    base_style=Style(
        background_colour=(0, 0, 0, 255),
        border_colour=(255, 255, 255, 255),
        border_width_pixels=2,
        background_corner_radius_pixels=2,
        halo_colour=(0, 0, 0, 0),
        halo_colour_fade_to_clear=False,
        halo_thickness_pixels=0,
        swell_increase_pixels=0,
        text_colour=(255, 255, 255, 255),
        text_font_name=None,
        text_font_size=12,
        text_anchor=Anchor.CENTRE,
        text_parent_anchor=Anchor.CENTRE,
        text_margin=(0, 0),
        text_is_bold=False,
        text_is_underlined=False,
        text_is_italic=False,
    ),
    style_overrides={
        State.DISABLED: StyleOverride(
            background_colour=(50, 50, 50, 255),
        ),
        State.HIGHLIGHTED: StyleOverride(
            halo_colour=(155, 155, 155, 50),
            halo_thickness_pixels=2,
            swell_increase_pixels=1,
        ),
    },
)
