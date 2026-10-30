"""Custom-theme puigame example: the default theme restyled.

Builds a theme from a tweaked copy of the default base style and new
overrides for the disabled, highlighted, and pressed states. A titled panel
sits above a button that quits, beside a disabled button, so every state can
be seen. Esc also quits.

Run it from the repository root with ``uv run python examples/custom_theme.py``.
"""

from dataclasses import replace

import pygame as pg

from puigame import (
    DEFAULT_THEME,
    UI,
    Anchor,
    Button,
    Container,
    DrawnSkin,
    FadeProfile,
    Label,
    Panel,
    State,
    StyleOverride,
    Theme,
)

FPS_CAP = 60
DT_CAP = 0.1  # seconds; a longer frame is treated as lag, not one big step

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 360
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

EDGE_MARGIN = 36
MARGIN = (EDGE_MARGIN, EDGE_MARGIN)

HALF_CONTAINER_SIZE = (SCREEN_WIDTH // 2, SCREEN_HEIGHT)

WIDGET_WIDTH = 192

LABEL_HEIGHT = 72
LABEL_SIZE = (WIDGET_WIDTH, LABEL_HEIGHT)
PANEL_SIZE = LABEL_SIZE

BUTTON_HEIGHT = 36
BUTTON_SIZE = (WIDGET_WIDTH, BUTTON_HEIGHT)

ORANGE = (255, 165, 0, 255)
MID_ORANGE = (200, 110, 0, 255)
DARK_ORANGE = (130, 70, 0, 255)
MID_RED = (150, 0, 0, 255)
DARK_RED = (50, 0, 0, 255)

CUSTOM_THEME = Theme(
    base_style=replace(
        DEFAULT_THEME.base_style,
        body_colour=MID_RED,
        border_thickness_px=0,
        corner_radius_px=20,  # over half the button height: a pill, as in CSS
        text_colour=MID_ORANGE,
        text_font_size=24,
        # centres capitals in Neb0Font at size 24, whose lines have 8 px of blank
        # space below the capitals and 4 px after the last glyph: half of each,
        # rounded down
        text_offset=(2, 4),
    ),
    style_overrides={
        State.DISABLED: StyleOverride(
            body_colour=DARK_RED,
            text_colour=DARK_ORANGE,
        ),
        State.HIGHLIGHTED: StyleOverride(
            halo_colour=ORANGE,
            halo_fade_profile=FadeProfile.HARD_QUADRATIC,
            halo_thickness_px=10,
        ),
        State.PRESSED: StyleOverride(
            body_colour=DARK_RED,
            swell_px=-1,
            text_offset=(2, 5),  # the base offset, 1 px lower
        ),
    },
)


def main() -> None:
    """Open a window and run the example until it is closed."""
    pg.init()
    screen = pg.display.set_mode(SCREEN_SIZE, pg.SCALED)
    pg.display.set_caption("puigame custom theme demo")

    ui = UI(size=screen.get_size(), theme=CUSTOM_THEME)

    # containers
    left_half_container = Container(
        ui.root,
        size=HALF_CONTAINER_SIZE,
        anchor=Anchor.MID_LEFT,
    )

    right_half_container = Container(
        ui.root,
        size=HALF_CONTAINER_SIZE,
        anchor=Anchor.MID_RIGHT,
    )

    # title
    title_panel = Panel(
        left_half_container,
        size=PANEL_SIZE,
        skin=DrawnSkin(),
        anchor=Anchor.MID_TOP,
        margin=MARGIN,
    )

    Label(
        title_panel,
        size=LABEL_SIZE,
        text="CUSTOM\nTHEME",
    )

    # quit button
    Button(
        left_half_container,
        size=BUTTON_SIZE,
        skin=DrawnSkin(),
        text="QUIT",
        on_click=lambda _button: pg.event.post(pg.Event(pg.QUIT)),
    )

    # disabled button
    Button(
        right_half_container,
        size=BUTTON_SIZE,
        skin=DrawnSkin(),
        text="DISABLED",
        enabled=False,
    )

    clock = pg.time.Clock()
    running = True

    while running:
        dt = min(clock.tick(FPS_CAP) / 1000, DT_CAP)  # dt in seconds

        # handle events
        for event in pg.event.get():
            consumed = ui.handle_event(event)

            if event.type == pg.QUIT:
                running = False

            elif not consumed and event.type == pg.KEYDOWN:
                match event.key:
                    case pg.K_ESCAPE:
                        pg.event.post(pg.Event(pg.QUIT))

        ui.update(dt)

        # drawing
        screen.fill(MID_ORANGE)
        ui.draw(screen)

        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    main()
