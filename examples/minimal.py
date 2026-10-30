"""Minimal puigame example: a window with one button, which quits.

Run it from the repository root with ``uv run python examples/minimal.py``.
"""

import pygame as pg

from puigame import UI, Button, DrawnSkin


def main() -> None:
    """Open a window and run the example until it is closed."""
    pg.init()
    screen = pg.display.set_mode((640, 360), pg.SCALED)
    pg.display.set_caption("puigame minimal demo")

    ui = UI(size=screen.get_size())

    Button(
        ui.root,
        size=(64, 30),
        skin=DrawnSkin(),
        text="QUIT",
        on_click=lambda _button: pg.event.post(pg.Event(pg.QUIT)),
    )

    clock = pg.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000  # seconds since the last frame

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            ui.handle_event(event)

        ui.update(dt)

        screen.fill("black")
        ui.draw(screen)
        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    main()
