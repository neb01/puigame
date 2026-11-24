"""Showcase puigame example: a small game running beside a puigame UI.

Two sprites bounce in a panel while buttons pause the game, jostle the main
buttons around a small circle, show and hide or enable and disable them, and
quit. P pauses, J jostles, and Esc quits. A label above the panel counts the
bounces, and another shows every character in Neb0Font.

Run it from the repository root with ``uv run python examples/showcase.py``.
"""

import math

import pygame as pg
from pygame.typing import Point

from puigame import (
    UI,
    Anchor,
    Button,
    Column,
    CrossAxisAlign,
    DrawnSkin,
    Label,
    Panel,
    Row,
    ToggleButton,
    ToggleGroup,
    Widget,
)

FPS_CAP = 60
DT_CAP = 0.1  # seconds; a longer frame is treated as lag, not one big step
FULL_TURN = math.pi * 2  # radians

SCREEN_SIZE = (640, 360)
MAIN_ROW_SPACING = 50

INTRA_CONTENT_SPACING = 15
BUTTON_PANEL_MARGIN = (7, 7)
SHOW_HIDE_BUTTON_SPACING = 5

TITLE_MARGIN = (5, 5)
TITLE_TEXT = "JUMPING\nSTANDARD\nBERNARDS"

TOGGLE_PAUSE = pg.event.custom_type()
PAUSE_TEXT = "PAUSE (P)"
UNPAUSE_TEXT = "UNPAUSE (P)"

JOSTLE_LAP_TIME = 1.2  # seconds
JOSTLE_TOTAL_LAPS = 2
JOSTLE_CENTRE = (6, 0)
JOSTLE_IDLE_TEXT = "JOSTLE (J)"
JOSTLE_ACTIVE_TEXT = "JOSTLING..."

QUIT_TEXT = "QUIT (ESC)"

SHOW_TEXT = "SHOW"
HIDE_TEXT = "HIDE"

# fixed width, wide enough for both texts, so the button doesn't resize when
# its text changes; height fitted
TOGGLE_ENABLE_BUTTON_SIZE = (198, None)
DISABLE_TEXT = "DISABLE BUTTONS"
ENABLE_TEXT = "ENABLE BUTTONS"

BOUNCE_PANEL_SIZE = (80, 250)
MAX_BOUNCES = 999
SQUARE_SIZE = (10, 10)
SQUARE_LAUNCH_VELOCITY = (0, -600)
RED_SQUARE_ACCELERATION = (0, 831)
BLUE_SQUARE_ACCELERATION = (0, 1000)

FONT_SPECIMEN_TEXT = (
    "Neb0Font\n\n"
    " !\"#$%&'()*+,-./\n"
    "0123456789:;<=>?\n"
    "@ABCDEFGHIJKLMNO\n"
    "PQRSTUVWXYZ[\\]^_\n"
    "`abcdefghijklmno\n"
    # U+FFFD isn't in Neb0Font, so it renders as .notdef, the glyph drawn in
    # the sheet's last cell
    "pqrstuvwxyz{|}~\ufffd\n\n"
    "THE QUICK BROWN\n"
    "FOX JUMPS OVER\n"
    "THE LAZY DOG\n\n"
    "the quick brown\n"
    "fox jumps over\n"
    "the lazy dog"
)


class BouncingSquare(pg.sprite.Sprite):
    """Sprite that bounces on a floor, standing in for a game's own sprites.

    Attributes:
        pos: Position of the sprite's bottom centre, in pixels. The rect is
            rounded from it each frame, so motion keeps its fractional part.
        acceleration: Constant acceleration, in pixels per second squared.
        floor_y: The y coordinate of the floor the sprite bounces on.
        launch_velocity: Velocity the sprite is launched with, at the start and
            from the floor, in pixels per second. Negative y is upwards.
        velocity: Current velocity, in pixels per second.
        bounces: Number of times the sprite has bounced off the floor.
    """

    def __init__(
        self,
        *,
        image: pg.Surface,
        start_pos: Point,
        launch_velocity: Point,
        acceleration: Point,
        floor_y: int,
    ) -> None:
        """Place the sprite at its start position and launch it.

        Args:
            image: Image to draw the sprite with.
            start_pos: Starting position of the sprite's bottom centre.
            launch_velocity: Velocity the sprite is launched with, at the start
                and from the floor, in pixels per second. Negative y is
                upwards. Stored as a copy.
            acceleration: Constant acceleration, in pixels per second squared,
                for example gravity. Stored as a copy.
            floor_y: The y coordinate of the floor the sprite bounces on.
        """
        super().__init__()
        self.image = image

        self.rect: pg.Rect = image.get_rect()
        self.pos = pg.Vector2(start_pos)
        self.rect.midbottom = (round(self.pos.x), round(self.pos.y))
        self.acceleration = pg.Vector2(acceleration)

        self.floor_y = floor_y

        self.launch_velocity = pg.Vector2(launch_velocity)
        self.velocity = self.launch_velocity.copy()

        self.bounces = 0

    def update(self, dt: float) -> None:
        """Move the sprite by one frame and bounce it off the floor.

        A bounce launches the sprite at ``launch_velocity`` rather than
        reflecting its velocity, so the height doesn't drift from bounce to
        bounce. Each frame updates the velocity before the position
        (semi-implicit Euler), so the peak is slightly lower at longer frame
        times.

        Args:
            dt: Time since the last frame, in seconds.
        """
        self.velocity += self.acceleration * dt
        self.pos += self.velocity * dt

        if self.pos.y > self.floor_y:
            self.pos.y = self.floor_y
            self.velocity = self.launch_velocity.copy()
            self.bounces += 1

        self.rect.midbottom = (round(self.pos.x), round(self.pos.y))


class JostleAnimation:
    """Animation that circles a widget for a set number of laps.

    The circle passes through the widget's rest position, so a jostle starts and
    ends there without a jump. The button that starts a jostle is disabled and
    shows ``active_text`` while it runs, and shows ``idle_text`` otherwise.

    Attributes:
        button: Button that starts a jostle and shows whether one is running.
        idle_text: Text of ``button`` between jostles.
        active_text: Text of ``button`` during a jostle.
        target: Widget moved around the circle through its ``offset``.
        initial_offset: Offset of ``target`` at rest, restored after each
            jostle.
        angle: Angle travelled in the current jostle, in radians.
        centre: Centre of the circle relative to the rest position, in pixels.
        speed: Angular speed, in radians per second.
        total_laps: Number of laps in each jostle.
        active: Whether a jostle is running.
    """

    def __init__(
        self,
        *,
        button: Button,
        idle_text: str,
        active_text: str,
        target: Widget,
        centre: Point,
        lap_time: float,
        total_laps: int,
    ) -> None:
        """Show the idle text on the button and record the target's rest offset.

        Args:
            button: Button that starts a jostle and shows whether one is
                running.
            idle_text: Text of ``button`` between jostles.
            active_text: Text of ``button`` during a jostle.
            target: Widget moved around the circle through its ``offset``.
            centre: Centre of the circle relative to the target's rest
                position, in pixels. Its length is the radius. Stored as a copy.
            lap_time: Time one lap takes, in seconds.
            total_laps: Number of laps in each jostle.
        """
        self.button = button
        self.idle_text = idle_text
        self.active_text = active_text
        self.button.text = self.idle_text

        self.target = target
        self.initial_offset = self.target.offset.copy()

        self.angle = 0.0  # radians
        self.centre = pg.Vector2(centre)
        self.speed = FULL_TURN / lap_time
        self.total_laps = total_laps

        self.active = False

    def start(self) -> None:
        """Start a jostle, unless one is already running."""
        if not self.active:
            self.active = True
            self.angle = 0.0

            self.button.text = self.active_text
            self.button.enabled = False

    def update(self, dt: float) -> None:
        """Move the target along the circle, and stop after the last lap.

        Does nothing between jostles, so it can be called every frame. Call it
        before ``ui.update()``, so that layout applies the new offset in the
        same frame.

        Args:
            dt: Time since the last frame, in seconds.
        """
        if self.active:
            self.angle += self.speed * dt

            if self.angle > FULL_TURN * self.total_laps:
                self._stop()

            else:
                self.target.offset = (
                    self.initial_offset
                    + self.centre
                    - self.centre.rotate_rad(self.angle)
                )

    def _stop(self) -> None:
        """End the jostle, and return the target and the button to rest."""
        self.active = False

        self.target.offset = self.initial_offset

        self.button.text = self.idle_text
        self.button.enabled = True


def main() -> None:
    """Open a window and run the example until it is closed."""
    pg.init()
    screen = pg.display.set_mode(SCREEN_SIZE, pg.SCALED)
    pg.display.set_caption("puigame showcase demo")

    ui = UI(size=screen.size)

    main_row = Row(
        ui,
        main_axis_spacing=MAIN_ROW_SPACING,
        cross_axis_align=CrossAxisAlign.END,
    )
    button_panel = Panel(main_row, skin=DrawnSkin())
    button_column = Column(
        button_panel,
        main_axis_spacing=INTRA_CONTENT_SPACING,
        margin=BUTTON_PANEL_MARGIN,
    )

    bounce_container = Column(main_row, main_axis_spacing=INTRA_CONTENT_SPACING)
    show_hide_buttons = Row(button_column, main_axis_spacing=SHOW_HIDE_BUTTON_SPACING)
    main_buttons = Column(button_column, main_axis_spacing=INTRA_CONTENT_SPACING)

    Label(ui, text=TITLE_TEXT, anchor=Anchor.TOP_LEFT, margin=TITLE_MARGIN)

    # pause button
    pause_button = Button(
        main_buttons,
        skin=DrawnSkin(),
        text=PAUSE_TEXT,
        on_click=lambda _button: pg.event.post(pg.Event(TOGGLE_PAUSE)),
    )

    # jostle button
    jostle_button = Button(
        main_buttons,
        skin=DrawnSkin(),
        on_click=lambda _button: jostle_animation.start(),
    )

    jostle_animation = JostleAnimation(
        button=jostle_button,
        idle_text=JOSTLE_IDLE_TEXT,
        active_text=JOSTLE_ACTIVE_TEXT,
        target=main_buttons,
        centre=JOSTLE_CENTRE,
        lap_time=JOSTLE_LAP_TIME,
        total_laps=JOSTLE_TOTAL_LAPS,
    )

    # quit button
    Button(
        main_buttons,
        skin=DrawnSkin(),
        text=QUIT_TEXT,
        on_click=lambda _button: pg.event.post(pg.Event(pg.QUIT)),
    )

    show_hide_toggle_group = ToggleGroup()

    # show and hide buttons
    def set_buttons_visible(_button: ToggleButton, checked: bool) -> None:
        """Show the main buttons when the show button becomes checked.

        Args:
            _button: Toggle button that changed. Unused.
            checked: Whether the button is now checked.
        """
        if checked:
            main_buttons.visible = True

    def set_buttons_invisible(_button: ToggleButton, checked: bool) -> None:
        """Hide the main buttons when the hide button becomes checked.

        Args:
            _button: Toggle button that changed. Unused.
            checked: Whether the button is now checked.
        """
        if checked:
            main_buttons.visible = False

    ToggleButton(
        show_hide_buttons,
        skin=DrawnSkin(),
        text=SHOW_TEXT,
        on_toggle=set_buttons_visible,
        group=show_hide_toggle_group,
        checked=True,
    )

    ToggleButton(
        show_hide_buttons,
        skin=DrawnSkin(),
        text=HIDE_TEXT,
        group=show_hide_toggle_group,
        on_toggle=set_buttons_invisible,
    )

    # enable and disable button
    def toggle_buttons_enabled(button: Button) -> None:
        """Enable or disable the main buttons, and relabel this button to match.

        Args:
            button: Button that was clicked.
        """
        if main_buttons.enabled:
            main_buttons.enabled = False
            button.text = ENABLE_TEXT
        else:
            main_buttons.enabled = True
            button.text = DISABLE_TEXT

    Button(
        button_column,
        size=TOGGLE_ENABLE_BUTTON_SIZE,
        skin=DrawnSkin(),
        text=DISABLE_TEXT,
        on_click=toggle_buttons_enabled,
    )

    # bouncing squares

    bounce_count_label = Label(bounce_container)

    bounce_panel = Panel(bounce_container, size=BOUNCE_PANEL_SIZE, skin=DrawnSkin())

    # Neb0Font specimen
    Label(main_row, text=FONT_SPECIMEN_TEXT)

    ui.update()  # lay out the UI, so bounce_panel.rect is current
    floor_y = bounce_panel.rect.bottom - bounce_panel.theme.base_style.border_thickness

    red_surface = pg.Surface(SQUARE_SIZE)
    red_surface.fill("red")
    red_square = BouncingSquare(
        image=red_surface,
        start_pos=(bounce_panel.rect.left + bounce_panel.rect.width / 3, floor_y),
        launch_velocity=SQUARE_LAUNCH_VELOCITY,
        acceleration=RED_SQUARE_ACCELERATION,
        floor_y=floor_y,
    )

    blue_surface = pg.Surface(SQUARE_SIZE)
    blue_surface.fill("blue")
    blue_square = BouncingSquare(
        image=blue_surface,
        start_pos=(bounce_panel.rect.left + bounce_panel.rect.width * 2 / 3, floor_y),
        launch_velocity=SQUARE_LAUNCH_VELOCITY,
        acceleration=BLUE_SQUARE_ACCELERATION,
        floor_y=floor_y,
    )

    squares = pg.sprite.Group(red_square, blue_square)

    clock = pg.time.Clock()
    running = True
    paused = False

    while running:
        dt = min(clock.tick(FPS_CAP) / 1000, DT_CAP)  # dt in seconds

        # handle events
        for event in pg.event.get():
            consumed = ui.handle_event(event)

            if event.type == pg.QUIT:
                running = False

            elif event.type == TOGGLE_PAUSE:
                paused = not paused
                if paused:
                    pause_button.text = UNPAUSE_TEXT
                else:
                    pause_button.text = PAUSE_TEXT

            elif not consumed and event.type == pg.KEYDOWN:
                match event.key:
                    case pg.K_ESCAPE:
                        pg.event.post(pg.Event(pg.QUIT))
                    case pg.K_p:
                        pg.event.post(pg.Event(TOGGLE_PAUSE))
                    case pg.K_j:
                        jostle_animation.start()

        # updates
        if not paused:
            squares.update(dt)

        total_bounces = sum(square.bounces for square in squares)
        bounce_count_label.text = f"{min(total_bounces, MAX_BOUNCES):03}"

        jostle_animation.update(dt)

        ui.update()

        # drawing
        screen.fill("black")
        ui.draw(screen)
        squares.draw(screen)

        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    main()
