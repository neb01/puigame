"""Theme, the shared rules for drawing every widget in a UI.

A theme holds a base style and the changes each state makes to it. Skins and
text ask the theme for the style of a widget's current state, so every widget
in a UI is drawn consistently.

``DEFAULT_THEME`` is sized for a 640x360 render surface, scaled up to the
window with ``pg.SCALED``.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from functools import cache
from types import MappingProxyType

from puigame._layout.anchor import Anchor
from puigame._styling.cursor_image import BundledCursor, CursorImage
from puigame._styling.cursor_role import CursorRole
from puigame._styling.style import (
    BundledTypeface,
    FadeProfile,
    Style,
    StyleOverride,
    TextAlign,
    TextHorizontalExtent,
)
from puigame._widgets.state import State

# order in which _style_for() applies overrides, lowest precedence first, so the
# later of two flags wins a field both set; this tuple decides, not the order
# State declares its members in or the order of style_overrides
_STATE_PRECEDENCE = (
    State.CHECKED,
    State.HIGHLIGHTED,
    State.PRESSED,
    State.EDITING,
    State.DISABLED,
)

_TRANSPARENT = (0, 0, 0, 0)

_OFF_WHITE = (220, 220, 220, 255)
_LIGHT_GREY = (100, 100, 100, 255)
_MID_GREY = (50, 50, 50, 255)
_DARK_GREY = (35, 35, 35, 255)
_OFF_BLACK = (15, 15, 15, 255)

_MID_GREEN = (0, 200, 0, 255)
_DARK_GREEN = (0, 100, 0, 255)


@cache
def _get_default_cursors() -> Mapping[CursorRole, CursorImage]:
    """Return the bundled ``GREEN`` cursor for each role, loaded on first use.

    Cached, so every theme with ``cursors=None`` shares one read-only mapping,
    and the images are neither read nor copied again each frame.

    Returns:
        A read-only mapping from each cursor role to its bundled image.
    """
    return MappingProxyType(
        {
            CursorRole.DEFAULT: CursorImage.bundled(BundledCursor.GREEN_ARROW),
            CursorRole.CLICKABLE: CursorImage.bundled(BundledCursor.GREEN_HAND),
            CursorRole.TEXT: CursorImage.bundled(BundledCursor.GREEN_I_BEAM),
        },
    )


@dataclass(frozen=True, kw_only=True)
class Theme:
    """Shared drawing rules for every widget in a UI.

    Overrides combine best when each state changes its own fields: for
    example, highlighting adds a halo, checking thickens the border, and
    disabling greys out the colours. Overrides that set different fields
    always combine. Where two set the same field, the flag with higher
    precedence wins, whatever order ``style_overrides`` holds them in. From
    lowest to highest, the precedence is ``CHECKED``, ``HIGHLIGHTED``,
    ``PRESSED``, ``EDITING``, then ``DISABLED``, so a disabled widget always
    shows every field its override sets. If checking and disabling both change
    the body colour, for example, a disabled toggle button looks the same
    whether it is checked or not.

    Attributes:
        base_style: Appearance of a widget when no state flags are set.
        style_overrides: Changes each state makes to ``base_style``, keyed by
            single state flag. ``State.BASE`` cannot be used as a key, because
            it is part of every state and its override would always apply.
            Combined flags, such as ``State.HIGHLIGHTED | State.DISABLED``,
            cannot be used either; a combination of states is styled by
            applying each flag's override in turn. Stored as a read-only copy.
        cursors: Image for each cursor role, or ``None`` for puigame's bundled
            ``GREEN`` cursors, which match ``DEFAULT_THEME``. It must map
            ``CursorRole.DEFAULT``; a role it leaves out shows the
            ``DEFAULT`` image. Stored as a read-only copy.
    """

    base_style: Style
    style_overrides: Mapping[State, StyleOverride]
    cursors: Mapping[CursorRole, CursorImage] | None = None

    def __post_init__(self) -> None:
        """Reject invalid keys and values, and store the mappings read-only.

        Raises:
            ValueError: If ``style_overrides`` uses ``State.BASE`` or a
                combination of flags as a key, or if ``cursors`` does not have
                ``CursorRole.DEFAULT`` as a key.
            TypeError: If a value in ``cursors`` is not a ``CursorImage``.
        """
        if State.BASE in self.style_overrides:
            raise ValueError("style_overrides cannot use State.BASE as a key")

        for flag in self.style_overrides:
            if len(flag) > 1:
                raise ValueError(
                    f"style_overrides cannot use combined flags as a key, got {flag!r}",
                )

        # copy, so later changes to the caller's dict don't reach the theme
        object.__setattr__(
            self,
            "style_overrides",
            MappingProxyType(dict(self.style_overrides)),
        )

        if self.cursors is not None:
            for cursor_image in self.cursors.values():
                if not isinstance(cursor_image, CursorImage):
                    raise TypeError(
                        f"cursors values must be CursorImage, got {cursor_image!r}",
                    )

            if CursorRole.DEFAULT not in self.cursors:
                raise ValueError(
                    "cursors must have CursorRole.DEFAULT as a key, "
                    f"got {list(self.cursors)!r}",
                )

            # copy, so later changes to the caller's dict don't reach the theme
            object.__setattr__(
                self,
                "cursors",
                MappingProxyType(dict(self.cursors)),
            )

    def _style_for(self, state: State) -> Style:
        """Return the style for a combination of state flags.

        Starts from ``base_style`` and applies the override for each flag in
        ``state``, from lowest to highest precedence (see ``Theme``). When two
        overrides set the same field, the higher-precedence one wins.

        Args:
            state: The widget's current state, which can combine several flags.

        Returns:
            A complete style for that state. If no flag in ``state`` has an
            override, this is ``base_style`` itself.
        """
        result = self.base_style

        for flag in _STATE_PRECEDENCE:
            if flag in state and flag in self.style_overrides:
                changed_fields = {
                    field: value
                    for field, value in asdict(self.style_overrides[flag]).items()
                    if value is not None
                }

                result = replace(result, **changed_fields)

        return result

    def _cursor_for(self, cursor_role: CursorRole) -> CursorImage:
        """Return the cursor image for a cursor role.

        Uses the bundled ``GREEN`` cursors when ``cursors`` is ``None``, and
        the ``DEFAULT`` image for a role that ``cursors`` leaves out.

        Args:
            cursor_role: Role of the widget that sets the cursor.

        Returns:
            The cursor image to draw.
        """
        if self.cursors is None:
            cursors = _get_default_cursors()
        else:
            cursors = self.cursors

        return cursors.get(cursor_role, cursors[CursorRole.DEFAULT])


DEFAULT_THEME = Theme(
    base_style=Style(
        body_colour=_MID_GREY,
        border_colour=_OFF_WHITE,
        border_thickness=2,
        corner_radius=5,
        halo_colour=_TRANSPARENT,
        halo_fade_profile=FadeProfile.SOLID,
        halo_thickness=0,
        swell=0,
        text_colour=_MID_GREEN,
        text_typeface=BundledTypeface.NEB0FONT,
        text_font_size=18,
        text_anchor=Anchor.CENTRE,
        text_parent_anchor=Anchor.CENTRE,
        text_align=TextAlign.LEFT,
        # Neb0Font's blank space is all after each glyph, so measuring the ink
        # centres it exactly, with no offset
        text_horizontal_extent=TextHorizontalExtent.INK,
        text_margin=(12, 8),
        text_offset=(0, 0),
    ),
    style_overrides={
        State.CHECKED: StyleOverride(border_colour=_MID_GREEN, border_thickness=3),
        State.HIGHLIGHTED: StyleOverride(
            halo_colour=_MID_GREEN,
            halo_fade_profile=FadeProfile.SOFT_QUADRATIC,
            halo_thickness=6,
            swell=1,
        ),
        State.PRESSED: StyleOverride(
            body_colour=_DARK_GREY,
            swell=-1,
            text_offset=(0, 1),  # the base offset, 1 px lower
        ),
        State.DISABLED: StyleOverride(
            body_colour=_OFF_BLACK,
            border_colour=_LIGHT_GREY,
            text_colour=_DARK_GREEN,
        ),
    },
)
