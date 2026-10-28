"""Shared fixtures and configuration for the puigame test suite."""

import os
from collections.abc import Iterator

import pygame as pg
import pytest

from puigame.core.ui import UI
from puigame.core.ui_root import UIRoot
from puigame.themes.theme import DEFAULT_THEME

# use SDL's dummy drivers so tests run without a screen or sound device (needed
# on CI); SDL reads these when pygame is initialised, not when it is imported,
# so they only need setting before pygame_session runs
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(scope="session", autouse=True)
def pygame_session() -> Iterator[None]:
    """Initialise pygame once for the whole test session and quit it afterwards."""
    pg.init()

    yield

    pg.quit()


@pytest.fixture
def ui_root() -> UIRoot:
    """Return a UIRoot that all test widgets can use as a parent."""
    return UIRoot(size=(300, 200), theme=DEFAULT_THEME)


@pytest.fixture
def ui() -> UI:
    """Return a UI with the default theme, for tests that ignore colours."""
    return UI(size=(300, 200), theme=DEFAULT_THEME)
