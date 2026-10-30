"""Style and StyleOverride, the values that say how a widget looks.

A ``Style`` holds every value needed to draw a widget, and a ``StyleOverride``
holds the changes one state makes to it. ``FadeProfile`` and
``BundledTypeface`` are the choices for a style's halo fade and typeface, and
``RGBA`` is the type of its colours.
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from puigame._layout.anchor import Anchor

# a colour as (red, green, blue, alpha), each from 0 to 255
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


class BundledTypeface(Enum):
    """Typefaces bundled with puigame.

    Each member's value is the file name of its font file in puigame's
    ``assets/fonts`` folder, or ``None`` for pygame-ce's built-in font,
    ``freesansbold.ttf``. Games use their own font files by passing a ``Path``
    instead of a member.

    ``NEB0FONT`` is a pixel font drawn on a 6-pixel grid, so it is crisp only at
    font sizes that are multiples of 6; other sizes distort its glyphs. Other
    sizes are not rejected. It covers printable ASCII only, so other characters,
    such as ``£`` or ``é``, need ``PYGAME_DEFAULT`` or a font file of the game's
    own.
    """

    _value_: str | None

    PYGAME_DEFAULT = None
    NEB0FONT = "neb0font.ttf"


@dataclass(frozen=True, kw_only=True)
class Style:
    """Complete appearance of a widget: every value needed to draw it.

    A theme's base style is a ``Style``, and ``Theme.style_for()`` returns a
    ``Style`` for any combination of state flags. Only the fields that
    ``StyleOverride`` also has can change between states.

    A negative corner radius, border thickness, or halo thickness, or a font
    size of 0 or less, raises ``ValueError`` when the style is created. A
    negative swell is allowed. A text margin or offset that is not a tuple, or
    a typeface that is neither a ``BundledTypeface`` nor a ``Path``, raises
    ``TypeError``.

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
        swell_px: How many pixels the widget grows by on each side. Negative
            values shrink it. 0 means no swell.
        text_colour: Text colour as RGBA.
        text_typeface: Typeface used for text: a ``BundledTypeface``, or the
            path to a font file supplied by the game.
        text_font_size: Font size for text, in pixels.
        text_anchor: Point on the text that is aligned to the widget.
        text_parent_anchor: Point on the widget that the text is aligned to.
        text_margin: Distance in pixels that the text is moved from its anchor
            point towards its own centre, as an ``(x, y)`` pair.
        text_offset: Shift in pixels applied to the text after its anchors and
            margin, as an ``(x, y)`` pair, with ``+x`` to the right and ``+y``
            down. Can change between states, for example to move the text
            down 1 pixel when a button is pressed.
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
    text_offset: tuple[int, int]

    # text options (state-agnostic)
    # BundledTypeface.PYGAME_DEFAULT is pygame-ce's built-in font, freesansbold.ttf
    text_typeface: BundledTypeface | Path
    text_font_size: int
    text_anchor: Anchor
    text_parent_anchor: Anchor
    text_margin: tuple[int, int]

    def __post_init__(self) -> None:
        """Reject values that cannot be drawn.

        Runs whenever a ``Style`` is created, including each one that
        ``Theme.style_for()`` builds with ``dataclasses.replace()``. The swell
        is not checked, since a negative swell is valid and shrinks the widget.

        Raises:
            TypeError: If ``text_margin`` or ``text_offset`` is not a tuple, or
                if ``text_typeface`` is neither a ``BundledTypeface`` nor a
                ``Path``.
            ValueError: If ``corner_radius_px``, ``border_thickness_px``, or
                ``halo_thickness_px`` is negative, or if ``text_font_size`` is
                not positive.
        """
        if not isinstance(self.text_margin, tuple):
            raise TypeError(f"text_margin must be a tuple, got {self.text_margin!r}")

        if not isinstance(self.text_offset, tuple):
            raise TypeError(f"text_offset must be a tuple, got {self.text_offset!r}")

        if not isinstance(self.text_typeface, (BundledTypeface, Path)):
            raise TypeError(
                "text_typeface must be a BundledTypeface or Path, "
                f"got {self.text_typeface!r}",
            )

        if self.corner_radius_px < 0:
            raise ValueError(
                f"corner_radius_px cannot be negative, got {self.corner_radius_px} px",
            )

        if self.border_thickness_px < 0:
            raise ValueError(
                "border_thickness_px cannot be negative, "
                f"got {self.border_thickness_px} px",
            )

        if self.halo_thickness_px < 0:
            raise ValueError(
                "halo_thickness_px cannot be negative, "
                f"got {self.halo_thickness_px} px",
            )

        if self.text_font_size <= 0:
            raise ValueError(
                f"text_font_size must be positive, got {self.text_font_size} px",
            )


@dataclass(frozen=True, kw_only=True)
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
        swell_px: How many pixels the widget grows by on each side, or
            ``None`` to keep it. Negative values shrink it, and 0 turns the
            swell off.
        text_colour: Text colour as RGBA, or ``None`` to keep it.
        text_offset: Shift in pixels applied to the text after its anchors and
            margin, as an ``(x, y)`` pair, or ``None`` to keep it.
    """

    # general appearance options
    body_colour: RGBA | None = None  # alpha channel controls transparency
    border_colour: RGBA | None = None

    # effect options
    halo_colour: RGBA | None = None
    halo_fade_profile: FadeProfile | None = None
    halo_thickness_px: int | None = None  # 0 for no halo
    swell_px: int | None = None  # 0 for no swell

    # text options
    text_colour: RGBA | None = None
    text_offset: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        """Reject values that cannot be drawn, as soon as the override is made.

        Fields left as ``None`` are not checked. The swell is not checked,
        since a negative swell is valid and shrinks the widget.

        Raises:
            TypeError: If ``text_offset`` is not a tuple.
            ValueError: If ``halo_thickness_px`` is negative.
        """
        if not (isinstance(self.text_offset, tuple) or self.text_offset is None):
            raise TypeError(
                f"text_offset must be a tuple or None, got {self.text_offset!r}",
            )

        if self.halo_thickness_px is not None and self.halo_thickness_px < 0:
            raise ValueError(
                "halo_thickness_px cannot be negative, "
                f"got {self.halo_thickness_px} px",
            )
