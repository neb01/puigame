"""Shared fixtures and configuration for the puigame test suite."""

import os
from collections.abc import Iterator

import pygame as pg
import pytest

from puigame import (
    UI,
    Anchor,
    BundledTypeface,
    FadeProfile,
    Style,
    TextHorizontalExtent,
    Theme,
)
from puigame._ui.ui_root import UIRoot

# use SDL's dummy drivers so tests run without a screen or sound device (needed
# on CI); SDL reads these when pygame is initialised, not when it is imported,
# so they only need setting before pygame_session runs
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

UIROOT_SIZE = (300, 200)

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

ANY_STYLE = Style(
    body_colour=WHITE,
    border_colour=BLACK,
    border_thickness=2,
    corner_radius=2,
    halo_colour=(0, 0, 0, 0),
    halo_fade_profile=FadeProfile.SOLID,
    halo_thickness=0,
    swell=0,
    text_colour=BLACK,
    text_typeface=BundledTypeface.PYGAME_DEFAULT,
    text_font_size=12,
    text_anchor=Anchor.CENTRE,
    text_parent_anchor=Anchor.CENTRE,
    text_horizontal_extent=TextHorizontalExtent.INK,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

ANY_THEME = Theme(base_style=ANY_STYLE, style_overrides={})


@pytest.fixture(scope="session", autouse=True)
def pygame_session() -> Iterator[None]:
    """Initialise pygame once for the whole test session and quit it afterwards."""
    pg.init()

    yield

    pg.quit()


@pytest.fixture
def ui_root() -> UIRoot:
    """Return a UIRoot that all test widgets can use as a parent."""
    return UIRoot(size=UIROOT_SIZE, theme=ANY_THEME)


@pytest.fixture
def ui() -> UI:
    """Return a UI with a placeholder theme, for tests that ignore its look."""
    return UI(size=UIROOT_SIZE, theme=ANY_THEME)
