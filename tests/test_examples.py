import runpy
from collections.abc import Iterator
from pathlib import Path

import pygame as pg
import pytest

# region --- Constants --------------------------------------------------------

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
EXAMPLE_PATHS = sorted(EXAMPLES_DIR.glob("*.py"))

# endregion


# region --- Helpers ----------------------------------------------------------


def single_quit_then_fail() -> Iterator[list[pg.Event]]:
    """Yield one batch holding a QUIT event, then fail if asked for another.

    Stands in for ``pg.event.get()``, so an example sees the window close on its
    first frame. A second call means the example started another frame instead
    of exiting, which would otherwise hang the test.

    Yields:
        A list holding a single ``QUIT`` event.

    Raises:
        AssertionError: If a second batch is requested.
    """
    yield [pg.Event(pg.QUIT)]
    raise AssertionError("second frame should not be reached")


# endregion


# region --- Running examples -------------------------------------------------


@pytest.mark.parametrize(
    "example_path",
    EXAMPLE_PATHS,
    ids=[path.stem for path in EXAMPLE_PATHS],
)
def test_example_runs_one_frame_and_exits(
    monkeypatch: pytest.MonkeyPatch,
    example_path,
):
    quit_batches = single_quit_then_fail()
    monkeypatch.setattr(pg.event, "get", lambda: next(quit_batches))

    monkeypatch.setattr(pg, "quit", lambda: None)

    runpy.run_path(str(example_path), run_name="__main__")


# endregion
