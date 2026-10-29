"""Theme, the shared rules for drawing every widget in a UI.

A theme holds a base style and the changes each state makes to it. Skins and
text ask the theme for the style of a widget's current state, so every widget
in a UI is drawn consistently.

``DEFAULT_THEME`` is sized for a 640x360 render surface, scaled up to the
window with ``pg.SCALED``.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from types import MappingProxyType

from puigame._layout.anchor import Anchor
from puigame._styling.style import BundledTypeface, FadeProfile, Style, StyleOverride
from puigame._widgets.state import State


@dataclass(frozen=True, kw_only=True)
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

        for flag in self.style_overrides:
            if len(flag) > 1:
                raise ValueError(
                    f"style_overrides cannot use combined flags as a key, got {flag}",
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
                changed_fields = {
                    field: value
                    for field, value in asdict(style_override).items()
                    if value is not None
                }

                result = replace(result, **changed_fields)

        return result


_TRANSPARENT = (0, 0, 0, 0)

_OFF_WHITE = (220, 220, 220, 255)
_LIGHT_GREY = (100, 100, 100, 255)
_MID_GREY = (50, 50, 50, 255)
_DARK_GREY = (35, 35, 35, 255)
_OFF_BLACK = (15, 15, 15, 255)


_MID_GREEN = (0, 200, 0, 255)
_DARK_GREEN = (0, 100, 0, 255)

DEFAULT_THEME = Theme(
    base_style=Style(
        body_colour=_MID_GREY,
        border_colour=_OFF_WHITE,
        border_thickness_px=2,
        corner_radius_px=5,
        halo_colour=_TRANSPARENT,
        halo_fade_profile=FadeProfile.SOLID,
        halo_thickness_px=0,
        swell_px=0,
        text_colour=_MID_GREEN,
        text_typeface=BundledTypeface.NEB0FONT,
        text_font_size=18,
        text_anchor=Anchor.CENTRE,
        text_parent_anchor=Anchor.CENTRE,
        text_margin=(0, 0),
        # centres capitals in NEB0FONT at size 18, whose lines have 6 px of blank
        # space below the capitals and 3 px after the last glyph: half of each,
        # rounded down
        text_offset=(1, 3),
    ),
    style_overrides={
        State.DISABLED: StyleOverride(
            body_colour=_OFF_BLACK,
            border_colour=_LIGHT_GREY,
            text_colour=_DARK_GREEN,
        ),
        State.HIGHLIGHTED: StyleOverride(
            halo_colour=_MID_GREEN,
            halo_fade_profile=FadeProfile.SOFT_QUADRATIC,
            halo_thickness_px=6,
            swell_px=1,
        ),
        State.PRESSED: StyleOverride(
            body_colour=_DARK_GREY,
            swell_px=-1,
            text_offset=(1, 4),  # the base offset, 1 px lower
        ),
    },
)
