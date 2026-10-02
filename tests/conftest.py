"""Shared fixtures and configuration for the puigame test suite."""

import os
from collections.abc import Iterator

import pytest

# Use SDL's dummy drivers so tests run without a screen or sound device
# (needed on CI). conftest.py loads before any test module imports pygame.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(scope="session", autouse=True)
def pygame_session() -> Iterator[None]:
    """Initialise pygame once for the whole test session and quit it afterwards."""
    import pygame

    pygame.init()

    yield

    pygame.quit()
