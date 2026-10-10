"""Shared rules for drawing UI elements.

A theme holds a base style and the changes each state makes to it. Skins and
text ask the theme for the style of a widget's current state, so every widget
in a UI is drawn consistently.

``DEFAULT_THEME`` is sized for a 640x360 render surface, scaled up to the
window with ``pg.SCALED``.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from enum import Enum, auto
from types import MappingProxyType

from puigame.core.anchor import Anchor
from puigame.core.state import State

# A colour as (red, green, blue, alpha), each from 0 to 255.
RGBA = tuple[int, int, int, int]


class FadeProfile(Enum):
    """How a halo's alpha changes from its inner edge to its outer edge.

    With ``t`` running from 0 at the halo's inner ring to 1 just past its outer
    edge, each ring's alpha is the halo colour's alpha multiplied by:

    - ``SOLID``: 1. No fade; every ring has the halo colour's alpha.
    - ``LINEAR``: ``1 - t``. An even fade.
    - ``SOFT_QUADRATIC``: ``(1 - t) ** 2``. Fades early, for a soft, glow-like
      edge.
    - ``HARD_QUADRATIC``: ``1 - t ** 2``. Stays strong, then drops near the
      outer edge.
    - ``SOFT_CUBIC``: ``(1 - t) ** 3``. Like ``SOFT_QUADRATIC``, but stronger.
    - ``HARD_CUBIC``: ``1 - t ** 3``. Like ``HARD_QUADRATIC``, but stronger.

    A halo with a thickness of 1 has a single ring, so every profile gives the
    same result.
    """

    SOLID = auto()
    LINEAR = auto()
    SOFT_QUADRATIC = auto()
    HARD_QUADRATIC = auto()
    SOFT_CUBIC = auto()
    HARD_CUBIC = auto()


@dataclass(frozen=True)
class Style:
    """Complete appearance of a widget: every value needed to draw it.

    A theme's base style is a ``Style``, and ``Theme.style_for()`` returns a
    ``Style`` for any combination of state flags. Only the fields that
    ``StyleOverride`` also has can change between states.

    A negative corner radius, border thickness, or halo thickness, or a font
    size of 0 or less, raises ``ValueError`` when the style is created. A
    negative swell is allowed.

    Attributes:
        body_colour: Colour of the body, the fill inside the border, as
            RGBA. The alpha channel controls transparency.
        border_colour: Border colour as RGBA.
        border_thickness_px: Border thickness in pixels, drawn inside the
            widget's edge. 0 means no border.
        corner_radius_px: Corner radius in pixels of the widget's outer edge
            (the border's outer edge) at its normal size. Skins derive every
            layer's radius from it: larger for the halo, smaller for the body,
            and grown or shrunk with the swell, so every layer stays
            concentric. Each layer's radius is kept between 0 and half that
            layer's shorter side, so a radius that would be larger gives a
            pill shape, and one that would be negative gives square corners.
        halo_colour: Halo colour as RGBA.
        halo_fade_profile: How the halo's alpha falls from ``halo_colour``'s
            alpha at its inner edge to transparent just past its outer edge.
            See ``FadeProfile``.
        halo_thickness_px: Halo thickness in pixels, drawn outside the
            widget's edge. 0 means no halo.
        swell_px: How many pixels the widget grows by on each
            side. Negative values shrink it. 0 means no swell.
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
    body_colour: RGBA  # alpha channel controls transparency
    border_colour: RGBA

    # general appearance options (state-agnostic)
    border_thickness_px: int  # 0 for no border
    corner_radius_px: int  # outer edge; halo, border, and body radii derive from it

    # effect options
    halo_colour: RGBA
    halo_fade_profile: FadeProfile
    halo_thickness_px: int  # 0 for no halo
    swell_px: int  # 0 for no swell

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

    def __post_init__(self) -> None:
        """Reject values that cannot be drawn.

        Runs whenever a ``Style`` is created, including each one that
        ``Theme.style_for()`` builds with ``dataclasses.replace()``. The swell
        is not checked, since a negative swell is valid and shrinks the widget.

        Raises:
            ValueError: If ``corner_radius_px``, ``border_thickness_px``, or
                ``halo_thickness_px`` is negative, or if ``text_font_size`` is
                not positive.
        """
        if self.corner_radius_px < 0:
            raise ValueError(
                f"corner_radius_px cannot be negative, got {self.corner_radius_px} px"
            )

        if self.border_thickness_px < 0:
            raise ValueError(
                "border_thickness_px cannot be negative, "
                f"got {self.border_thickness_px} px"
            )

        if self.halo_thickness_px < 0:
            raise ValueError(
                f"halo_thickness_px cannot be negative, got {self.halo_thickness_px} px"
            )

        if self.text_font_size <= 0:
            raise ValueError(
                f"text_font_size must be positive, got {self.text_font_size} px"
            )


@dataclass(frozen=True)
class StyleOverride:
    """Changes that one state makes to a ``Style``.

    Each field matches a field of ``Style``, and only these fields can change
    between states. A field left as ``None`` keeps the value underneath, and
    any other value replaces it. When several states are active, their
    overrides are applied in turn, so a later override wins when two set the
    same field.

    Attributes:
        body_colour: Colour of the body as RGBA, or ``None`` to keep it.
        border_colour: Border colour as RGBA, or ``None`` to keep it.
        halo_colour: Halo colour as RGBA, or ``None`` to keep it.
        halo_fade_profile: How the halo fades towards its outer edge, or
            ``None`` to keep it.
        halo_thickness_px: Halo thickness in pixels, or ``None`` to keep
            it. 0 turns the halo off.
        swell_px: How many pixels the widget grows by on each
            side, or ``None`` to keep it. Negative values shrink it, and 0
            turns the swell off.
        text_colour: Text colour as RGBA, or ``None`` to keep it.
    """

    # general appearance options
    body_colour: RGBA | None = None  # alpha channel controls transparency
    border_colour: RGBA | None = None
    halo_colour: RGBA | None = None
    halo_fade_profile: FadeProfile | None = None
    halo_thickness_px: int | None = None  # 0 for no halo
    swell_px: int | None = None  # 0 for no swell

    # text options
    text_colour: RGBA | None = None

    def __post_init__(self) -> None:
        """Reject values that cannot be drawn, as soon as the override is made.

        Fields left as ``None`` are not checked. The swell is not checked,
        since a negative swell is valid and shrinks the widget.

        Raises:
            ValueError: If ``halo_thickness_px`` is negative.
        """
        if self.halo_thickness_px is not None and self.halo_thickness_px < 0:
            raise ValueError(
                f"halo_thickness_px cannot be negative, got {self.halo_thickness_px} px"
            )


@dataclass(frozen=True)
class Theme:
    """Shared drawing rules for every widget in a UI.

    Overrides combine best when each state changes its own fields: for
    example, highlighting changes the border, checking changes the body, and
    disabling greys out the colours. Overrides that set different fields
    always combine; where two set the same field, the later one in
    ``style_overrides`` wins.

    Attributes:
        base_style: Appearance of a widget when no state flags are set.
        style_overrides: Changes each state makes to ``base_style``, keyed by
            single state flag. ``State.BASE`` cannot be used as a key, because
            it is part of every state and its override would always apply.
            Combined flags, such as ``State.DISABLED | State.HIGHLIGHTED``,
            cannot be used either; a combination of states is styled by
            applying each flag's override in turn. Stored as a read-only copy.
    """

    base_style: Style
    style_overrides: Mapping[State, StyleOverride]

    def __post_init__(self) -> None:
        """Reject invalid keys and store ``style_overrides`` read-only.

        Raises:
            ValueError: If ``style_overrides`` uses ``State.BASE`` or a
                combination of flags as a key.
        """
        if State.BASE in self.style_overrides:
            raise ValueError("style_overrides cannot use State.BASE as a key")

        for state in self.style_overrides:
            if len(state) > 1:
                raise ValueError(
                    f"style_overrides cannot use combined flags as a key, got {state}"
                )

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
        body_colour=(0, 0, 0, 255),
        border_colour=(255, 255, 255, 255),
        border_thickness_px=2,
        corner_radius_px=2,
        halo_colour=(0, 0, 0, 0),
        halo_fade_profile=FadeProfile.SOLID,
        halo_thickness_px=0,
        swell_px=0,
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
            body_colour=(50, 50, 50, 255),
        ),
        State.HIGHLIGHTED: StyleOverride(
            halo_colour=(155, 155, 155, 50),
            halo_fade_profile=FadeProfile.SOFT_QUADRATIC,
            halo_thickness_px=2,
            swell_px=1,
        ),
    },
)
