"""Style and StyleOverride, the values that say how a widget looks.

A ``Style`` holds every value needed to draw a widget, and a ``StyleOverride``
holds the changes one state makes to it. ``FadeProfile``,
``TextHorizontalExtent``, and ``BundledTypeface`` are the choices for a
style's halo fade, text placement box, and typeface, and ``RGBA`` is the type
of its colours.
"""

from dataclasses import dataclass
from enum import Enum, auto, unique
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


class TextHorizontalExtent(Enum):
    """How wide a text's placement box is, and where it starts.

    Text is positioned by anchoring its placement box to the widget. The box is
    always the same height: from the top of the first line's capitals to the
    last line's baseline, measured from the font, so text lines up by its
    capitals whatever its characters, and descenders hang below the box. This
    setting chooses only the box's horizontal extent:

    - ``INK``: from the first drawn pixel to the last, across all lines. Spaces
      and the blank space at each end of the text are left out. Suits fonts
      whose blank space is all on one side of each glyph, which then centre
      exactly.
    - ``LOGICAL``: from the start of each line to the end of its last
      character that is not whitespace, using the font's own spacing, as most
      text layout does. Leading spaces count and trailing spaces do not. Text
      in a font with uneven spacing can sit slightly off centre.

    Multi-line text uses its widest line.
    """

    INK = auto()
    LOGICAL = auto()


@unique
class BundledTypeface(Enum):
    """Typefaces bundled with puigame.

    Each member's value is the file name of its font file in puigame's
    ``assets/fonts`` folder, or ``None`` for pygame-ce's built-in font,
    ``freesansbold.ttf``. Games use their own font files by passing a ``Path``
    instead of a member.

    ``NEB0FONT`` is a proportional pixel font with tabular digits, and
    ``NEBMON0FONT`` is its monospace version. Both are drawn on a 6-pixel grid,
    so they are crisp only at font sizes that are multiples of 6; other sizes
    distort their glyphs. Other sizes are not rejected. They cover printable
    ASCII only, so other characters, such as ``£`` or ``é``, need
    ``PYGAME_DEFAULT`` or a font file of the game's own.
    """

    _value_: str | None

    PYGAME_DEFAULT = None
    NEB0FONT = "neb0font.ttf"
    NEBMON0FONT = "nebmon0font.ttf"


@dataclass(frozen=True, kw_only=True)
class Style:
    """Complete appearance of a widget: every value needed to draw it.

    A theme's base style is a ``Style``, and the theme resolves a ``Style``
    for any combination of state flags from it. Only the fields that
    ``StyleOverride`` also has can change between states.

    A negative border thickness, corner radius, or halo thickness, or a font
    size of 0 or less, raises ``ValueError`` when the style is created. A
    negative swell is allowed. A halo fade profile that is not a
    ``FadeProfile``, a text offset that is not a tuple, a typeface that is
    neither a ``BundledTypeface`` nor a ``Path``, a text anchor or parent anchor
    that is not an ``Anchor``, a horizontal extent that is not a
    ``TextHorizontalExtent``, or a text margin that is not a tuple, raises
    ``TypeError``.

    Attributes:
        body_colour: Colour of the body, the fill inside the border, as
            RGBA. The alpha channel controls transparency.
        border_colour: Border colour as RGBA.
        border_thickness: Border thickness in pixels, drawn inside the
            widget's edge. 0 means no border.
        corner_radius: Corner radius in pixels of the widget's outer edge
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
        halo_thickness: Halo thickness in pixels, drawn outside the
            widget's edge. 0 means no halo.
        swell: How many pixels the widget grows by on each side. Negative
            values shrink it. 0 means no swell.
        text_colour: Text colour as RGBA.
        text_offset: Shift in pixels applied to the text after its anchors and
            margin, as an ``(x, y)`` pair, with ``+x`` to the right and ``+y``
            down. Centred text needs no offset to look centred, so this is for
            deliberate nudges, and can change between states, for example to
            move the text down 1 pixel when a button is pressed.
        text_typeface: Typeface used for text: a ``BundledTypeface``, or the
            path to a font file supplied by the game.
        text_font_size: Font size for text, in pixels.
        text_anchor: Point on the text's placement box that is aligned to the
            widget.
        text_parent_anchor: Point on the widget that the text is aligned to.
        text_horizontal_extent: How wide the text's placement box is. See
            ``TextHorizontalExtent``.
        text_margin: Distance in pixels that the text is moved from its anchor
            point towards its own centre, as an ``(x, y)`` pair.
    """

    # general appearance options
    body_colour: RGBA  # alpha channel controls transparency
    border_colour: RGBA

    # general appearance options (state-agnostic)
    border_thickness: int  # 0 for no border
    corner_radius: int  # outer edge; halo, border, and body radii derive from it

    # effect options
    halo_colour: RGBA
    halo_fade_profile: FadeProfile
    halo_thickness: int  # 0 for no halo
    swell: int  # 0 for no swell

    # text options
    text_colour: RGBA
    text_offset: tuple[int, int]

    # text options (state-agnostic)
    # BundledTypeface.PYGAME_DEFAULT is pygame-ce's built-in font, freesansbold.ttf
    text_typeface: BundledTypeface | Path
    text_font_size: int
    text_anchor: Anchor
    text_parent_anchor: Anchor
    text_horizontal_extent: TextHorizontalExtent
    text_margin: tuple[int, int]

    def __post_init__(self) -> None:
        """Reject values that cannot be drawn.

        Runs whenever a ``Style`` is created, including each one that a theme
        builds for a state with ``dataclasses.replace()``. The swell
        is not checked, since a negative swell is valid and shrinks the widget.

        Raises:
            ValueError: If ``border_thickness``, ``corner_radius``, or
                ``halo_thickness`` is negative, or if ``text_font_size`` is
                not positive.
            TypeError: If ``halo_fade_profile`` is not a ``FadeProfile``, if
                ``text_offset`` is not a tuple, if ``text_typeface`` is neither
                a ``BundledTypeface`` nor a ``Path``, if ``text_anchor`` or
                ``text_parent_anchor`` is not an ``Anchor``, if
                ``text_horizontal_extent`` is not a ``TextHorizontalExtent``, or
                if ``text_margin`` is not a tuple.
        """
        if self.border_thickness < 0:
            raise ValueError(
                f"border_thickness cannot be negative, got {self.border_thickness} px",
            )

        if self.corner_radius < 0:
            raise ValueError(
                f"corner_radius cannot be negative, got {self.corner_radius} px",
            )

        if not isinstance(self.halo_fade_profile, FadeProfile):
            raise TypeError(
                "halo_fade_profile must be a FadeProfile, "
                f"got {self.halo_fade_profile!r}",
            )

        if self.halo_thickness < 0:
            raise ValueError(
                f"halo_thickness cannot be negative, got {self.halo_thickness} px",
            )

        if not isinstance(self.text_offset, tuple):
            raise TypeError(f"text_offset must be a tuple, got {self.text_offset!r}")

        if not isinstance(self.text_typeface, (BundledTypeface, Path)):
            raise TypeError(
                "text_typeface must be a BundledTypeface or Path, "
                f"got {self.text_typeface!r}",
            )

        if self.text_font_size <= 0:
            raise ValueError(
                f"text_font_size must be positive, got {self.text_font_size} px",
            )

        if not isinstance(self.text_anchor, Anchor):
            raise TypeError(f"text_anchor must be an Anchor, got {self.text_anchor!r}")

        if not isinstance(self.text_parent_anchor, Anchor):
            raise TypeError(
                "text_parent_anchor must be an Anchor, "
                f"got {self.text_parent_anchor!r}",
            )

        if not isinstance(self.text_horizontal_extent, TextHorizontalExtent):
            raise TypeError(
                "text_horizontal_extent must be a TextHorizontalExtent, "
                f"got {self.text_horizontal_extent!r}",
            )

        if not isinstance(self.text_margin, tuple):
            raise TypeError(f"text_margin must be a tuple, got {self.text_margin!r}")


@dataclass(frozen=True, kw_only=True)
class StyleOverride:
    """Changes that one state makes to a ``Style``.

    Each field matches a field of ``Style``, and only these fields can change
    between states. A field left as ``None`` keeps the value underneath, and
    any other value replaces it. When several states are active, their
    overrides are applied in order of precedence, so the higher-precedence
    state wins when two set the same field (see ``Theme``).

    A negative halo thickness raises ``ValueError`` when the override is
    created. A negative swell is allowed. A halo fade profile that is not a
    ``FadeProfile``, or a text offset that is not a tuple, raises
    ``TypeError``.

    Attributes:
        body_colour: Colour of the body as RGBA, or ``None`` to keep it.
        border_colour: Border colour as RGBA, or ``None`` to keep it.
        halo_colour: Halo colour as RGBA, or ``None`` to keep it.
        halo_fade_profile: How the halo fades towards its outer edge, or
            ``None`` to keep it.
        halo_thickness: Halo thickness in pixels, or ``None`` to keep
            it. 0 turns the halo off.
        swell: How many pixels the widget grows by on each side, or
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
    halo_thickness: int | None = None  # 0 for no halo
    swell: int | None = None  # 0 for no swell

    # text options
    text_colour: RGBA | None = None
    text_offset: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        """Reject values that cannot be drawn, as soon as the override is made.

        Fields left as ``None`` are not checked. The swell is not checked,
        since a negative swell is valid and shrinks the widget.

        Raises:
            TypeError: If ``halo_fade_profile`` is not a ``FadeProfile``, or
                if ``text_offset`` is not a tuple.
            ValueError: If ``halo_thickness`` is negative.
        """
        if self.halo_fade_profile is not None and not isinstance(
            self.halo_fade_profile,
            FadeProfile,
        ):
            raise TypeError(
                "halo_fade_profile must be a FadeProfile or None, "
                f"got {self.halo_fade_profile!r}",
            )

        if self.halo_thickness is not None and self.halo_thickness < 0:
            raise ValueError(
                f"halo_thickness cannot be negative, got {self.halo_thickness} px",
            )

        if self.text_offset is not None and not isinstance(self.text_offset, tuple):
            raise TypeError(
                f"text_offset must be a tuple or None, got {self.text_offset!r}",
            )
