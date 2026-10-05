# puigame architecture

This document records the design of puigame v0.1: what the library does, how it is structured, and the decisions behind it. Later pull requests implement it piece by piece; when a decision changes, this document is updated in the same pull request.

## Goals and scope

- **UI widgets for pygame-ce**: widgets, anchoring, skins, themes, event dispatch, and keyboard navigation.
- **Framework-agnostic**: no event bus, scenes, or game loop inside the library. The game owns the window and the loop; puigame receives events, updates, and draws.
- **Passive API plus callbacks**: puigame exposes methods and accepts callables. The game, or a game framework built on top, does the wiring.

Out of scope: event buses, scene management, game key bindings, and game-specific widgets (health bars, minimaps, and so on). These belong in games or in a separate framework package.

## Integration

A game uses puigame through one object, the `UIManager`:

```python
ui = puigame.UIManager()
ui.add(puigame.Button(..., text="Back", on_click=go_back))

while running:
    for event in pygame.event.get():
        if ui.handle_event(event):  # True = consumed by the UI
            continue
        ...  # the game handles everything else
    ui.update(dt)
    screen.fill(BACKGROUND)
    draw_game(screen)
    ui.draw(screen)  # UI drawn on top
```

In an event-bus framework, a scene owns a `UIManager` like any other manager: the scene subscribes `ui.handle_event` to the bus, calls `ui.update` and `ui.draw` each frame, and passes callbacks that publish to the bus. puigame never imports the framework.

### Timing

`update(dt)` takes the time since the last frame in **seconds**, as a `float`. puigame measures all durations in seconds (for example a text caret blinking every `0.5` seconds), so the UI runs at the same real-world speed at any frame rate.

`dt` defaults to `DEFAULT_DT = 1 / 60`, which suits games running at a fixed 60 fps. Games running at other or variable frame rates pass the real elapsed time:

```python
dt = clock.tick(fps) / 1000  # Clock.tick() returns milliseconds
ui.update(dt)
```

The default is stated in the `update()` docstring, so it appears in editor tooltips, and in the user documentation.

## Class hierarchy

The hierarchy is shallow and describes **behaviour** only. Appearance (skins) and content (text) are added by composition.

```
Widget            pygame Sprite: rect, anchor, children, flags, skin, state-surface cache
├── Container     invisible group of children (no skin)
├── Panel         Container behaviour with a skin, so it has a background
├── Label         + Text component, non-interactive
├── Button        + press and release, on_click; optional Text
│   └── Checkbox  + checked, can_untoggle, optional CheckboxGroup
└── TextBox       + editable Text, editing mode (a direct Widget subclass: no PRESSED state)

CheckboxGroup     helper: mutual exclusion between checkboxes (radio behaviour)
WidgetGroup       LayeredUpdates subclass that draws the widget tree
UIManager         owns the theme and the root group; routes input, tracks the highlight
```

- **Every widget can hold children.** The tree lives on `Widget` itself, so any widget can parent another (for example a tooltip that is a child of its button). `Container` and `Panel` are thin classes that exist to make intent clear.
- Complex widgets are built by **composing** simpler ones (a slider is a container holding a track and a handle button), not by deepening the hierarchy.

### Widgets are pygame Sprites

Every widget is a `pygame.sprite.Sprite` with an `image` and a `rect`, so widgets work with sprite groups and fit games that organise objects into groups. pygame's sprite system is part of pygame itself, so this does not tie puigame to any game framework.

## Widget tree and flags

### Parents and children

Every widget stores a reference to its `parent` (or `None`) and a list of references to its children.

- A widget with no parent is **top-level**: the `UIManager` positions it against its own area, which defaults to the whole screen.
- A parent, children, or both can be passed when a widget is created.
- `set_parent()` is the single place where the link changes, so both sides always agree. Passing children on creation calls `set_parent()` on each child.

`set_parent(new_parent)`:

1. Does nothing if `new_parent` is already the parent.
2. Removes this widget from the old parent's children, if there was one.
3. Sets `new_parent` as this widget's parent.
4. Adds this widget to `new_parent`'s children.

Passing `None` detaches the widget and makes it top-level.

### Flags

Each widget has its **own** flags, which parents never overwrite, and a tree-aware version of each:

| Own flag | Taking parents into account |
|---|---|
| `visible` | `visible_in_tree` |
| `enabled` | `enabled_in_tree` |
| `highlightable` | `highlightable_in_tree` |

- The `_in_tree` values are **calculated on demand**, never stored: a widget is visible in the tree only if it and every widget above it are visible (the same for enabled).
- `highlightable_in_tree` is true only if the widget's own `highlightable` is true **and** it is `visible_in_tree` and `enabled_in_tree`. `highlightable` defaults to `False` on `Widget` and `True` on `Button`, `Checkbox`, and `TextBox`.
- Hiding a parent changes only its own flag; its children's `_in_tree` values change automatically. A child hidden individually stays hidden when its parent is shown again.
- Widgets that are not `visible_in_tree` are not drawn; widgets that are not `enabled_in_tree` ignore input.

## Components

Components are objects a widget **holds** as attributes, rather than classes it inherits from. This avoids multiple inheritance and lets one widget hold several of the same kind (for example a title and a subtitle).

| Component | Held by | Job |
|---|---|---|
| **`Skin`** | Every `Widget` (optional; `None` means transparent) | Renders the widget's background surface for a given size and `State` |
| **`Text`** | `Label`, `Button`, `TextBox` (one or more per widget) | Holds the string, font, and colour; is positioned within its owner by an anchor and margin; renders onto the owner's image; notifies the owner when it changes |

A `Text` component is **not** a child widget: it is not a Sprite, receives no input, and is drawn into its owner's image rather than on its own.

### Skins

A skin turns a size and a state into a surface, following the rules in the theme. Widgets are given a skin when they are created and do not know which kind they have. One skin can serve many widgets.

- **`DrawnSkin`**: built in code from theme values: per-state fill, border, and text colours, border width, corner radius, and padding. Works with no art at all and draws cleanly at any size.
- **`ImageSkin`**: one image per state, scaled with **nine-slice** so corners stay crisp at any size. A `pixel_art` option switches to nearest-neighbour scaling to keep hard pixel edges. Accepts a `pygame.Surface` or a path.
- Custom skins can implement the same interface.

Scaling behaviour is a per-skin option, not a global setting.

## Themes

A `Theme` holds the shared rules skins and text read: colours, fonts, text sizes, corner radius, border widths, and per-state adjustments (for example disabled is dimmer, highlighted is lighter or has a halo).

- The theme lives on the **`UIManager`**, so every widget it manages draws consistently.
- puigame ships a default theme that uses the bundled default art and fonts.

## Anchors

Positions are set with a nine-point `Anchor` (`CENTRE`, `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_RIGHT`, `MID_LEFT`, `MID_RIGHT`, `MID_TOP`, `MID_BOTTOM`) plus a margin.

- A widget is anchored relative to its **parent's rect**; moving or resizing the parent repositions its children. Top-level widgets are anchored to the `UIManager`'s area, which defaults to the whole screen.
- A `Text` component is anchored relative to its **owner widget's rect**.

### Anchor points

Each anchor names a point on a rect:

![The nine anchor points of a rect](images/anchors.svg)

### Matching anchors

Placement aligns a point on the widget with a point on its parent:

- `anchor`: the point **on the widget**.
- `parent_anchor`: the point **on the parent**. Optional; defaults to the same as `anchor`.

With the same anchor on both, the widget sits **inside** its parent (for example, bottom-right corner to bottom-right corner). With different anchors, it can sit **outside** or alongside it (for example, a tooltip that is a child of a button, with its `MID_TOP` matched to the button's `MID_BOTTOM`, sits directly below the button whatever either widget's size).

![Placing a widget with the same or different anchors](images/anchor_matching.svg)

### Margins

`margin` is either a single number or an `(x, y)` pair. A single number `m` is shorthand for `(m, m)`.

The margin is measured **inwards from the widget's own anchor point**: positive values push the widget towards its own centre side of the anchor, negative values push it the other way.

![How margins offset widgets inwards from each anchor](images/margins.svg)

| Anchor | Margin used |
|---|---|
| Corners (`TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_RIGHT`) | `x` horizontally and `y` vertically, both inwards |
| `MID_LEFT`, `MID_RIGHT` | `x` only |
| `MID_TOP`, `MID_BOTTOM` | `y` only |
| `CENTRE` | Ignored |

Examples:

- `anchor=BOTTOM_RIGHT, margin=10` places the widget 10 px left of and 10 px above its parent's bottom-right corner.
- `anchor=TOP_LEFT, margin=(20, 8)` places it 20 px in from the left and 8 px down from the top.
- `anchor=MID_TOP, parent_anchor=MID_BOTTOM, margin=(0, 4)` places it directly below its parent with a 4 px gap.
- Negative margins push outwards, for example a badge overlapping the corner of a button.

In short: a positive margin always creates space between the matched points; a negative margin creates overlap. Changing anchors never requires flipping signs.

### Offset

`offset` is an optional `(x, y)` nudge in **screen coordinates** (pygame's convention: `+x` is right, `+y` is down), applied after the anchor and margin. It works on every anchor, including centred axes, where margins have no inward direction:

- `anchor=CENTRE, offset=(0, -20)` places a widget 20 px above the centre of its parent.
- `anchor=MID_BOTTOM, margin=12, offset=(20, 0)` places it 12 px up from the bottom edge, then 20 px right of centre.

The two parameters keep one meaning each: `margin` is space relative to the anchors, `offset` is a plain screen-space shift.

Both are stored as `pygame.Vector2`, whatever form they are given in, so layout can use them in calculations directly. They are properties: assigning a new value converts it, while changing the stored vector in place (for example `widget.offset.y -= 2` to animate a slide) works as expected.

## State

A widget's visual state is a `State`, an `enum.Flag`:

```python
class State(Flag):
    BASE = 0
    DISABLED = auto()
    HIGHLIGHTED = auto()
    PRESSED = auto()
    CHECKED = auto()
    EDITING = auto()
```

Each member is one bit, so a combination such as `State.HIGHLIGHTED | State.PRESSED` is a single `State` value. Combinations are hashable and are used directly as cache keys. `BASE` has no bits set: it is the empty combination.

### Current state

`current_state` is a property built by composing flags with `|=`. Each class adds its own flags on top of its parent's:

- `Widget` starts from `BASE` and adds `DISABLED` when not `enabled_in_tree`.
- `Button` calls `super().current_state` and, unless `DISABLED` is set, adds `HIGHLIGHTED` and `PRESSED`.
- `Checkbox` adds `CHECKED` when `checked` is true.
- `TextBox` adds `HIGHLIGHTED` and `EDITING`.

`DISABLED` suppresses `HIGHLIGHTED` and `PRESSED`: a disabled widget never looks interactive.

### Valid states

Not every combination can occur, so each class lists the combinations it can be in **explicitly**, in a class-level `possible_states` tuple, annotated as a `ClassVar`. The cache renders exactly these.

| Class | `possible_states` |
|---|---|
| `Widget`, `Container`, `Panel`, `Label` | `BASE`, `DISABLED` |
| `Button` | `BASE`, `HIGHLIGHTED`, `HIGHLIGHTED \| PRESSED`, `DISABLED` |
| `Checkbox` | Button's four, each with and without `CHECKED` (eight) |
| `TextBox` | `BASE`, `HIGHLIGHTED`, `HIGHLIGHTED \| EDITING`, `DISABLED` |

## Rendering and caching

Each widget builds its image in layers:

1. The skin renders the widget's rect for a state.
2. Content (`Text` components, check marks, and so on) is drawn on top.
3. The result is stored in the widget's cache, a `dict[State, Surface]`.

Caching rules:

- **Per widget, per state**: one surface for every combination in the class's `possible_states`.
- **Eager**: all states are rendered when the widget is created. Lazy rendering (on first use) is a later optimisation.
- **State changes swap `image`** from the cache, with no drawing. Each frame, `update()` reads `current_state` and looks up its surface, so `image` always matches the widget's flags and its parents' flags.
- **Invalidation**: the cache is cleared and rebuilt whenever text, size, skin, or theme changes. These values are changed only through setters, which handle the rebuild.

Because rendering happens at creation, widgets must be created after `pygame.init()`. Converting surfaces for display (`convert_alpha()`) also requires a display window to exist.

## Drawing: WidgetGroup

`WidgetGroup` subclasses pygame's `LayeredUpdates`:

- **Layers follow the tree**: children draw above their parents. Layers are corrected when widgets are added, moved in the tree, or reordered, so layering can change while the game runs.
- **Hidden widgets are skipped**: widgets that are not `visible_in_tree` are not drawn.

The `UIManager` owns the root `WidgetGroup`. Games that keep their own sprite groups can still add widgets to them, since widgets are ordinary sprites.

## Input

```
pygame event → UIManager.handle_event
   ├─ mouse    → hit-test topmost first → the first widget that handles it stops it
   ├─ keyboard → the editing TextBox, or highlight navigation and activation
   └─ unused   → returns False → the game handles it
```

### Hit-testing

Widgets are hit-tested against their `rect` by default. A widget can opt into a **mask** (built from its current image) so that non-rectangular widgets, such as round buttons, respond only where they are drawn.

### Highlight

Mouse hover and keyboard focus are **one concept**, the highlight, shown with `HIGHLIGHTED`. The `UIManager` tracks a single highlighted widget.

- **Mouse**: moving the mouse highlights the topmost `highlightable_in_tree` widget under the cursor. Moving onto empty space clears the highlight.
- **Keyboard**: Tab and the arrow keys move the highlight between `highlightable_in_tree` widgets. The `UIManager` switches to keyboard mode and hides the cursor.
- **Switching back**: in keyboard mode, hover is ignored, because the hidden cursor still has a position. The first real mouse movement switches back to mouse mode, shows the cursor, and highlights whatever is under it.

### Pressing

- **Clicks fire on release**, and only if the cursor is over the widget on release.
- Pressing shows `HIGHLIGHTED | PRESSED`. Dragging off while held shows `BASE`; dragging back on while still held returns to `HIGHLIGHTED | PRESSED`. The widget remembers that the press started on it.
- A press that starts elsewhere and is dragged onto a widget does not press or activate it.
- **Keyboard activation** follows the same rule: Enter or Space down on the highlighted widget shows `HIGHLIGHTED | PRESSED`, and key up fires.
- **Mouse-button enable map**: each button chooses which mouse buttons (left, middle, right, scroll) it responds to.

### Editing text

- Clicking a `TextBox`, or pressing Enter while it is highlighted, starts editing. The text at that moment is kept so editing can be cancelled.
- While editing, the `TextBox` **keeps the highlight** regardless of mouse movement, and the arrow keys move the text caret instead of the highlight.
- **Enter** confirms the text. **Escape** cancels and restores the original text.
- **Clicking elsewhere** ends editing and keeps the text. That click does nothing else.

### Cursor

The `UIManager` hides and shows the mouse cursor as the input mode changes. A game that manages the cursor itself passes `manage_cursor=False`. Since `pygame.mouse.set_visible` affects the whole window, this is an option rather than something puigame always does.

## Callbacks

Callbacks are plain callables passed to widgets and receive the widget as their first argument, so one handler can serve several widgets. The exact names and signatures for `Button`, `Checkbox`, `CheckboxGroup`, and `TextBox` are still open (see [Open questions](#open-questions)).

## Positions and types

- **`pygame.Rect` internally**, for pixel-exact positioning.
- Constructors take a **size**, not a position or rect. Position always comes from layout (parent, anchors, margin, and offset), so a widget sits at `(0, 0)` until it has a parent or is added to the `UIManager`. Absolute placement is `anchor=TOP_LEFT, margin=(x, y)`.
- Smooth movement, if needed, keeps a precise `pygame.Vector2` and rounds it into the `Rect`.
- pygame types use pygame-ce's `pygame.typing` aliases. puigame defines its own `Protocol` classes only for its own concepts.

## Assets

- Bundled assets live in `assets/images/` (default skin art, nine-slice-ready) and `assets/fonts/`, all MIT-compatible.
- They are loaded with `importlib.resources`, so they are found wherever the package is installed.
- Fonts are cached, since rendering text is the most expensive step.
- Loading failures raise exceptions (for example `FileNotFoundError`) and never exit the program.
- Game-side concerns stay in games: asset folder conventions, resource paths, and PyInstaller handling. Games bundled with PyInstaller need puigame's data files included in their build.

## Naming conventions

- **State flags** are adjectives: `visible`, `enabled`, `highlightable`, `checked`; `State` members likewise (`HIGHLIGHTED`, `PRESSED`, `EDITING`).
- **Tree-aware values** end in `_in_tree`: `visible_in_tree`, `enabled_in_tree`, `highlightable_in_tree`. They are calculated on demand, never stored.
- **Permissions** start with `can_`: `can_untoggle`.
- **Possession** starts with `has_`: `has_text`, `has_children`.
- **Methods** are verbs: `show()`, `hide()`, `toggle()`, `set_text()`.
- **Classes** use `CapWords` with capitalised acronyms (`UIManager`); public names avoid abbreviations; British spelling is used (`CENTRE`, `colour`).
- **Docstrings and documentation** use British spelling and the Oxford comma in lists of three or more.
- **Modules** are named after their main class in `lowercase_with_underscores`: `UIManager` lives in `ui_manager.py`, `WidgetGroup` in `widget_group.py`.

## Package layout

```
src/puigame/
├── __init__.py          public API re-exports
├── py.typed
├── assets/
│   ├── fonts/
│   └── images/
├── components/          objects widgets hold
│   ├── skin.py          Skin, DrawnSkin, ImageSkin (nine-slice)
│   └── text.py          Text and the font cache
├── core/
│   ├── anchor.py        Anchor
│   ├── state.py         State
│   ├── widget.py        Widget, DEFAULT_DT
│   ├── widget_group.py  WidgetGroup
│   └── ui_manager.py    UIManager
├── themes/
│   └── theme.py         Theme and the default theme
└── widgets/
    ├── container.py
    ├── panel.py
    ├── label.py
    ├── button.py
    ├── checkbox.py      Checkbox and CheckboxGroup
    └── textbox.py
```

Every subpackage has an `__init__.py`. Tests mirror this layout under `tests/`.

### Dependencies

Each layer imports only from the layers above it:

1. `core/anchor`, `core/state`
2. `themes/theme`
3. `components/skin`, `components/text`
4. `core/widget`
5. `core/widget_group`
6. `widgets/*`
7. `core/ui_manager`

`UIManager` needs only `Widget` and `WidgetGroup`, not the concrete widgets, so nothing in `core` imports from `widgets`. This prevents circular imports and makes it clear where new code belongs.

## v0.1 scope

**Included:** `Anchor`, `State`, `Widget`, `WidgetGroup`, `UIManager`, `Theme`, `Text`, `DrawnSkin`, `ImageSkin` with default art, `Container`, `Panel`, `Label`, `Button`, `Checkbox` with `CheckboxGroup`, and `TextBox`.

**Later:** lazy caching, an `Image` widget, sliders and progress bars (as compound widgets), dropdowns, scroll and list views, row and column layouts, and a shared skin cache.

## Build order

Each step is one branch and pull request, with tests:

1. `docs/architecture`: this document
2. `chore/package-structure`: subpackages, `__init__.py` files and module stubs
3. `feat/anchor-state`: `Anchor` and `State`
4. `feat/theme-drawn-skin`: `Theme`, `Skin`, and `DrawnSkin`
5. `feat/text`: `Text` component and font cache
6. `feat/widget-base`: `Widget`, with the tree, flags, positioning, and state cache (replaces the `hello()` placeholder)
7. `feat/widget-group`: `WidgetGroup`
8. `feat/container-panel-label`: `Container`, `Panel`, and `Label`
9. `feat/ui-manager`: `UIManager` input routing, highlight, keyboard mode, and cursor management
10. `feat/button`: `Button`
11. `feat/checkbox`: `Checkbox` and `CheckboxGroup`
12. `feat/textbox`: `TextBox`
13. `feat/image-skin`: `ImageSkin`, nine-slice scaling, pixel-art option, and default art

## Open questions

- **Callbacks**: names and signatures for each widget, whether programmatic changes (for example `checkbox.checked = True`) notify, and whether Escape on a `TextBox` has its own callback.
