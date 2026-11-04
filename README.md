# puigame

<!-- GIF of examples/showcase.py goes here -->

UI widgets for [pygame-ce](https://pyga.me/): buttons, labels, and panels, placed by anchors and styled by themes.

> **Status:** pre-alpha, ahead of the first release. The API may change in any 0.x release.

## Install

```powershell
pip install puigame
```

puigame needs Python 3.11+ and pygame-ce 2.5.8+. It uses pygame-ce, not pygame, and the two cannot be installed together.

## Quick start

A window with one button, which quits ([`examples/minimal.py`](examples/minimal.py)):

```python
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
```

For more, see [`examples/custom_theme.py`](examples/custom_theme.py) and [`examples/showcase.py`](examples/showcase.py).

## Running a UI

Each frame, the game passes every event to `ui.handle_event()`, then calls `ui.update(dt)`, then `ui.draw(surface)`, in that order. Pass every event, not only mouse events: the UI needs window events such as `WINDOWLEAVE` to keep highlights and presses right, and it never polls pygame itself.

`handle_event()` returns whether the UI consumed the event. A click on a button or panel is consumed, so the game can ignore it:

```python
for event in pg.event.get():
    consumed = ui.handle_event(event)

    if event.type == pg.QUIT:
        running = False

    elif not consumed and event.type == pg.MOUSEBUTTONDOWN:
        ...  # a click on the game world, not on the UI
```

Mouse motion, wheel, and window events are never consumed.

For a display opened with `pg.SCALED`, create the UI with the display's own size, `screen.get_size()`, not the window's.

## Widgets

- `Button`: a clickable widget with text.
- `Label`: text.
- `Panel`: a background for its children, which by default stops clicks reaching the widgets and game below it.
- `Container`: an invisible widget that groups and places its children.

Each widget is created with its parent, `ui.root` for a top-level widget, and placed against it: `anchor` is the point on the widget, `parent_anchor` the point on the parent it is matched to (the same point by default), and `margin` and `offset` move it from there. To place a group of widgets together, create them under a `Container` (or a `Panel`, for a background) that is itself under `ui.root`; a `UI` always covers its whole surface. Buttons and panels take a skin: `DrawnSkin()` draws them in the theme's style, and `NoSkin()` draws nothing.

## Responding to clicks

A button's `on_click` is called with the button, from inside `handle_event()`. To keep game logic in the game loop, post an event and handle it there:

```python
TOGGLE_PAUSE = pg.event.custom_type()

Button(
    ui.root,
    size=(96, 30),
    skin=DrawnSkin(),
    text="PAUSE",
    on_click=lambda _button: pg.event.post(pg.Event(TOGGLE_PAUSE)),
)
```

A key binding can then post the same event, so the button and the key share one handler.

## Themes

A theme is a base style plus, for each state, the fields that state changes. The simplest way to make one is to copy the default base style with `dataclasses.replace()`, then write an override for each state that should look different:

```python
from dataclasses import replace

from puigame import DEFAULT_THEME, UI, State, StyleOverride, Theme

theme = Theme(
    base_style=replace(DEFAULT_THEME.base_style, body_colour=(150, 0, 0, 255)),
    style_overrides={
        State.HIGHLIGHTED: StyleOverride(
            halo_colour=(255, 165, 0, 255),
            halo_thickness_px=6,
        ),
        State.PRESSED: StyleOverride(
            body_colour=(50, 0, 0, 255),
            text_offset=(0, 1),
        ),
    },
)

ui = UI(size=screen.get_size(), theme=theme)
```

An override lists only the fields that differ, and the rest come from the base style. `style_overrides` replaces the default theme's overrides rather than adding to them, so a state left out, such as `DISABLED` above, looks the same as the base style. [`examples/custom_theme.py`](examples/custom_theme.py) restyles the default theme this way, with overrides for the disabled, highlighted, and pressed states.

When several states apply at once, their overrides are applied in a fixed order, lowest precedence first: `CHECKED`, `HIGHLIGHTED`, `PRESSED`, `EDITING`, `DISABLED`. If two states set the same field, the later one wins, whatever order `style_overrides` lists them in.

Themes are frozen, and a UI's theme is set when it is created.

### Text placement

Text is centred on its capitals. It is placed by a box that runs from the top of the first line's capitals to the last line's baseline, measured from the font, so text looks centred in any font and at any size with no offset, and descenders hang below the box.

`text_horizontal_extent` chooses how wide that box is:

- `TextHorizontalExtent.INK`: from the first drawn pixel to the last. This suits pixel fonts like Neb0Font, whose spacing is all on one side of each glyph, and is what the default theme uses.
- `TextHorizontalExtent.LOGICAL`: the font's own spacing, as in most text layout. Leading spaces count, and trailing spaces do not.

`text_offset` is for deliberate nudges, such as moving pressed text down 1 pixel.

## Limitations in v0.1

- **Neb0Font and NebMon0Font cover printable ASCII only.** Other characters, such as `£` or `é`, are drawn as a placeholder box; use `BundledTypeface.PYGAME_DEFAULT` or a font file of your own for them. Both are pixel fonts, crisp only at sizes that are multiples of 6: Neb0Font (`NEB0FONT`) is proportional with tabular digits, and NebMon0Font (`NEBMON0FONT`) is its monospace version.
- **Multi-line text is left-aligned.**
- **Subclassing widgets is not supported.** Compose them instead.
- **The first click on an unfocused window is dropped.** By default, SDL uses the click that focuses a window and does not pass it on, so the first click after switching to the game does not reach a button. To pass it on, set the hint before creating the window: `os.environ["SDL_MOUSE_FOCUS_CLICKTHROUGH"] = "1"`. puigame leaves this choice to the game. This is untested on Windows.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setting up, running the checks, and commit messages.

## Authorship

All code in puigame is written by hand. Documentation, including this README, the `docs/` folder, and the docstrings in the code, is first drafted with AI assistance and then checked by hand.

## License

[MIT](LICENSE)
