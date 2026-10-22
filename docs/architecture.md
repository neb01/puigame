# puigame architecture

This document records the design of puigame v0.1: what the library does, how it is structured, and the decisions behind it. Later pull requests implement it piece by piece; when a decision changes, this document is updated in the same pull request.

All puigame code is written by hand. This document, like the rest of the documentation (including the docstrings in the code), was first drafted with AI assistance and then checked by hand.

## Contents

- [Goals and scope](#goals-and-scope)
- [Integration](#integration)
- [Class hierarchy](#class-hierarchy)
- [Widget tree and flags](#widget-tree-and-flags)
- [Components](#components)
- [Themes](#themes)
- [Anchors](#anchors)
- [State](#state)
- [Rendering and caching](#rendering-and-caching)
- [Drawing: WidgetGroup](#drawing-widgetgroup)
- [Input](#input)
- [Callbacks](#callbacks)
- [Positions and types](#positions-and-types)
- [Assets](#assets)
- [Naming and code conventions](#naming-and-code-conventions)
- [Package layout](#package-layout)
- [v0.1 scope](#v01-scope)
- [Build order](#build-order)
- [Open questions](#open-questions)

## Goals and scope

- **UI widgets for pygame-ce**: widgets, anchoring, skins, themes, event dispatch, and keyboard navigation.
- **Framework-agnostic**: no event bus, scenes, or game loop inside the library. The game owns the window and the loop; puigame receives events, updates, and draws.
- **Passive API plus callbacks**: puigame exposes methods and accepts callables. The game, or a game framework built on top, does the wiring.

Out of scope: event buses, scene management, game key bindings, and game-specific widgets (health bars, minimaps, and so on). These belong in games or in a separate framework package.

## Integration

A game uses puigame through a `UI` object. Each `UI` combines two parts:

- **`ui.root`**: a `UIRoot`, the widget at the top of the UI's tree. It fills the UI's area (the whole screen by default) instead of anchoring to a parent, has no parent itself, and holds the UI's theme. Every widget in the UI is its child, directly or further down the tree.
- **`ui.manager`**: a `UIManager` that runs the UI: input routing, the highlight, press capture, and the cursor (see [Input](#input)).

`UI` passes the common calls through, so a game rarely needs either part directly. Every widget is created with its parent as the first argument, so a widget at the top level of a UI is created with `ui.root` as its parent.

```python
ui = puigame.UI()
puigame.Button(ui.root, ..., text="Back", on_click=go_back)

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

In an event-bus framework, a scene owns a `UI` like any other manager: the scene subscribes `ui.handle_event` to the bus, calls `ui.update` and `ui.draw` each frame, and passes callbacks that publish to the bus. puigame never imports the framework.

### Layering

A screen that shows several UIs at once, such as a pause menu over a HUD, uses a separate `UI` for each. puigame does not coordinate them; the game decides the order:

```python
for event in pygame.event.get():
    if pause_ui.handle_event(event):  # top layer first
        continue
    if not paused and hud.handle_event(event):
        continue
    ...  # the game handles the rest

hud.draw(screen)
pause_ui.draw(screen)  # drawn last, so on top
```

- **Input** goes to the top UI first and stops at the first one that consumes it. A modal menu is the game not passing events to the UIs below.
- **Drawing** goes from the bottom UI to the top.
- **Each UI has its own highlight and settings**: a HUD typically turns keyboard navigation off, while a pause menu keeps it on.
- **Only one UI should manage the cursor** at a time, since the cursor belongs to the whole window. The others are created with `manage_cursor=False` (see [Cursor](#cursor)).

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
Widget                  pygame Sprite: rect, anchor, fixed parent, children, flags, skin, per-state image cache
├── UIRoot              top of a UI's tree: fills the UI's area, holds the theme, has no parent
├── Container           invisible group of children (NoSkin)
├── Panel               Container behaviour with a skin, so it has a background
├── Label               + Text component and text property, no background (NoSkin), non-interactive
└── InteractiveWidget   + highlightable, plus the highlight and activation behaviour interactive widgets share
    ├── Button          + press and release, on_click; optional Text
    │   └── Checkbox    + checked, can_untoggle, optional CheckboxGroup
    └── TextBox         + editable Text, editing mode (no PRESSED state)

CheckboxGroup           helper: mutual exclusion between checkboxes (radio behaviour)
WidgetGroup             LayeredUpdates subclass that draws the widget tree
UI                      composes root (a UIRoot, which holds the theme) and manager; owns the root group
UIManager               runs one UI: routes input, tracks the highlight and presses, manages the cursor
```

- **`InteractiveWidget` lives in `core`**, so the `UIManager` can find interactive widgets with `isinstance()` without importing from `widgets`. Non-interactive widgets (`Container`, `Panel`, and `Label`) have no highlight concept at all.
- **Every widget can hold children.** The tree lives on `Widget` itself, so any widget can parent another (for example a tooltip that is a child of its button). `Container` and `Panel` are thin classes that exist to make intent clear.
- Complex widgets are built by **composing** simpler ones (a slider is a container holding a track and a handle button), not by deepening the hierarchy.

### Widgets are pygame Sprites

Every widget is a `pygame.sprite.Sprite` with an `image` and a `rect`, so widgets work with sprite groups and fit games that organise objects into groups. pygame's sprite system is part of pygame itself, so this does not tie puigame to any game framework.

## Widget tree and flags

### Parents and children

Every widget except a `UIRoot` is created with its `parent` as the first argument, and keeps that parent for its whole life: widgets cannot be moved to a new parent. This keeps the tree simple, and guarantees that every widget can reach its UI's theme from the moment it is created. Construction is therefore top-down: a parent exists before its children.

- `parent` and `children` are read-only. `children` returns a tuple of the widget's children in the order they were created, so it cannot be appended to or replaced.
- A new widget joins its parent's children only once the rest of its setup has succeeded, so a widget whose creation raised is never left in the tree.
- A widget at the top level of a UI is created with `ui.root` as its parent. Every widget in a UI therefore has a parent, except the root itself.
- Each widget keeps a reference to the `UIRoot` at the top of its tree, copied from its parent. Parents never change, so neither does the root, and the reference cannot go out of date.
- To move a widget, kill it and create a new one under the new parent. Moving widgets directly is a later feature.

`kill()` removes a widget for good. It extends pygame's `Sprite.kill()`: the widget leaves its parent's children, each of its children is killed in turn, and every one of them leaves all its sprite groups. Like `Sprite.kill()`, it can safely be called more than once. A killed widget keeps its link to its old parent, but should not be used again. `UIRoot.kill()` raises `TypeError`: to remove a whole UI, the game drops every reference to it.

`UIRoot` is created differently from other widgets, since it has no parent. It sets up its root reference and its theme itself, then runs the setup that every widget shares, without calling `Widget.__init__()`.

### Flags

Each widget has its **own** flags, which parents never overwrite, and a tree-aware version of each:

| Own flag | Taking ancestors into account |
|---|---|
| `enabled` | `enabled_in_tree` |
| `visible` | `visible_in_tree` |

- The `_in_tree` values are **calculated on demand**, never stored: a widget is visible in the tree only if it and every widget above it are visible (the same for enabled).
- `InteractiveWidget` adds a third pair: `highlightable` (default `True`) and `highlightable_in_tree`, which is true only if the widget's own `highlightable` is true **and** it is `visible_in_tree` and `enabled_in_tree`. Setting `highlightable=False` lets an interactive widget be skipped by highlighting, for example a button that should only respond to the mouse. See [Highlight](#highlight).
- Hiding a parent changes only its own flag; its children's `_in_tree` values change automatically. A child hidden individually stays hidden when its parent is shown again.
- Widgets that are not `visible_in_tree` are not drawn; widgets that are not `enabled_in_tree` ignore input.

## Components

Components are objects a widget **holds** as attributes, rather than classes it inherits from. This avoids multiple inheritance and lets one widget hold several of the same kind (for example a title and a subtitle).

| Component | Held by | Job |
|---|---|---|
| **`Skin`** | Every `Widget` (required; `Container` and `UIRoot` use `NoSkin`) | Renders the widget's background surface for a given size and `Style` (see [Skins](#skins)) |
| **`Text`** | Widgets that display text, such as `Label`, `Button`, and `TextBox` (as many as the widget needs; widgets without text hold none) | Holds the string; is styled and positioned by the owner's `Style` (see [Text](#text)); renders onto the owner's image; keeps no reference to its owner, so the owner rebuilds its images when it changes the text |

A `Text` component is **not** a child widget: it is not a Sprite, receives no input, and is drawn into its owner's image rather than on its own.

### Skins

A skin turns a size and a style into a surface. Skins hold no per-widget data and no theme: the widget looks up the `Style` for each of its states in its theme and passes it in. Widgets are given a skin when they are created and do not know which kind they have. One skin can serve many widgets.

`Skin` is an abstract base class: it defines `render(size, style)` and cannot be created itself. Every skin takes the same parameters, so any skin can stand in for any other; a skin that ignores the style, such as `NoSkin`, still accepts it. Every skin's `render()` returns a `PlacedImage`: a **new** surface, as `image`, never shared with another widget, together with the position of its top-left corner relative to the widget's `rect.topleft`, as `pos`.

- Without effects, the surface is exactly the requested size and its position is `(0, 0)`.
- A halo or a positive swell makes the surface **larger** than the widget, and a negative swell makes it smaller. The position is `-(swell + halo)` on each axis, so the drawing stays centred on the widget's rect: negative (up and to the left of `rect.topleft`) when the surface is larger, and positive when it is smaller.
- The widget's `rect` stays the size it was given, so effects are purely visual: hit-testing ignores the halo.

![Drawing a skin surface at rect.topleft plus pos](images/skin_offset.svg)

- **`NoSkin`**: a 0x0 surface, whatever the size and style. For widgets with no appearance at all, such as `Container` and `UIRoot`, so their images cost almost nothing to store or draw, and for widgets with content but no background, such as a bare label, whose image is then the size of its content. It is public, so any widget can go without a background, such as a clear button; its hitbox is still its `rect`. A widget with `NoSkin` shows changes of state only through its components' styles, such as text colour and text offset. `Label` always uses it: for text on a background, place a `Label` in a `Panel`. A 0x0 surface is the one exception to the size rules above.
- **`DrawnSkin`**: built in code from the theme's style for each state: body and border colours, border thickness, corner radius, halo, and swell. Works with no art at all and draws cleanly at any size. See [DrawnSkin layers](#drawnskin-layers).
- **`ImageSkin`**: one image per state, scaled with **nine-slice** so corners stay crisp at any size. A `pixel_art` option switches to nearest-neighbour scaling to keep hard pixel edges. Accepts a `pygame.Surface` or a path.
- Custom skins subclass `Skin` and implement `render()`.

Scaling behaviour is a per-skin option, not a global setting.

### Text

`Text` holds only its string. Its typeface, font size, colour, and placement come from the `Style` the widget passes to `render(size, style)`, so it follows the widget's theme and state. `render()` returns a `PlacedImage`: the rendered surface, as `image`, and the position of its top-left corner relative to the widget's `rect.topleft`, as `pos`. `pos` is signed and is added to `rect.topleft`.

- Text is placed relative to the widget's **rect**, not the skin's image or body, using the style's `text_anchor`, `text_parent_anchor`, `text_margin`, and `text_offset` in the same way as widgets are placed (see [Anchors](#anchors)).
- `text_offset` can change between states, for example to move the text down 1 pixel when a button is pressed. `text_margin` stays the same in every state.
- Text is **not clipped**: it can extend past the rect, for example to hang a label beside a widget. Hit-testing still uses the rect.
- Empty text renders a 0x0 image at `(0, 0)`.
- Text is drawn **without antialiasing**, which keeps pixel fonts crisp. The alpha channel of `text_colour` sets the text's transparency; pygame-ce's `Font.render()` ignores it, so `Text` applies it to the rendered surface.
- **Multiline** text uses pygame-ce's own rendering: each newline starts a new line, and lines are left-aligned and spaced by the font's line size. A trailing newline, or text that is only a newline or carriage return, is drawn as a glyph. A fuller multiline design, such as alignment and wrapping, is deferred.
- Bold, italic, and underline are not supported.
- Neb0Font is a pixel font drawn on a 6-pixel grid, so it is crisp only at font sizes that are multiples of 6.

#### DrawnSkin layers

`DrawnSkin` works with four rects, all centred on the same point:

- **Widget rect**: the widget's `rect`, at the size it was given. Layout and hit-testing use this one.
- **Border rect**: the widget's outer edge. It is the widget rect grown by the swell on every side, or shrunk by a negative swell.
- **Body rect**: the fill inside the border. It is the border rect shrunk by the border thickness on every side.
- **Surface rect**: the whole rendered surface. It is the border rect grown by the halo thickness on every side.

It draws three filled, rounded rectangles from largest to smallest: the halo (filling the surface rect), the border (filling the border rect), and the body (filling the body rect). Each layer covers the middle of the one before, so no gaps appear at rounded corners. The style's `corner_radius_px` is the radius of the border rect at the widget's normal size. The halo's radius is larger by the halo thickness and the body's smaller by the border thickness, and all three grow or shrink with the swell, so the layers stay concentric. Each layer's radius is kept between 0 and half that layer's shorter side, as in CSS: a radius that would be larger gives a pill shape, and one that would be negative, such as the body's inside a border thicker than the corner radius, gives square corners.

![DrawnSkin layers for each combination of border and swell](images/skin_layers.svg)

- A **fading halo** is drawn as one ring per pixel of thickness, from the outermost in. Each ring's alpha follows the style's `FadeProfile`: `SOLID`, `LINEAR`, or a soft or hard quadratic or cubic curve.
- If the swell and border would give the body a **negative** size, `render()` raises `ValueError`, since the values contradict each other. A body of size 0 (a widget that is all border) is allowed.

## Themes

A `Theme` holds the shared rules skins and text read. It is made of two parts:

- **`base_style`**: a `Style`, which holds every value needed to draw a widget: body and border colours, border thickness, corner radius, halo colour, thickness, and fade profile, swell, and text settings.
- **`style_overrides`**: a mapping from state flags to `StyleOverride`s. Each override sets only the fields that state changes and leaves the rest as `None`. Only fields that `StyleOverride` has can change between states; the others, such as the font, stay the same in every state.

`theme.style_for(state)` returns a complete `Style` for any combination of flags. It starts from `base_style` and applies the override for each flag in the state, in the order the mapping holds them, so a later override wins when two set the same field. Skins and text use this one `Style` and do not need to know how the theme is organised.

- Themes are **immutable**: `Theme`, `Style`, and `StyleOverride` are frozen dataclasses, and `style_overrides` is stored as a read-only copy. Cached images therefore never go out of date because a theme changed. A variation is made with `dataclasses.replace()`.
- `State.BASE` cannot be a key in `style_overrides`, because it is part of every state and its override would always apply. Combined flags, such as `State.DISABLED | State.HIGHLIGHTED`, cannot be keys either: a combination of states is styled by applying each flag's override in turn. Both raise `ValueError` when the theme is created.
- Overrides combine best when each state changes its own fields: for example, highlighting changes the border, checking changes the body, and disabling greys out the colours. Overrides that set different fields always combine; where two set the same field, the order of `style_overrides` decides which wins.
- Styles reject values that cannot be drawn: a negative corner radius, border thickness, or halo thickness, or a font size of 0 or less, raises `ValueError` as soon as the `Style` or `StyleOverride` is created. A negative swell is allowed, since it shrinks the widget. A text margin or offset that is not a tuple, or a typeface that is neither a `BundledTypeface` nor a `Path`, raises `TypeError`. Whether a negative swell leaves room for the body depends on the widget's size, so `DrawnSkin` checks that when it renders.
- Text is drawn in a **typeface**: a `BundledTypeface` member for a font shipped with puigame, or a `pathlib.Path` to a font file supplied by the game. Each member's value is the name of its file in `assets/fonts/`, and `PYGAME_DEFAULT` (value `None`) is pygame-ce's built-in font. Using two types keeps bundled fonts and game files apart, so nothing has to guess what a value means. Games cannot add members to `BundledTypeface`; a game that wants names for its own fonts defines them on its side, for example as `Path` constants.
- The theme lives on the UI's **`UIRoot`**, and every widget reaches it through the root of its tree, so every widget in a UI draws consistently. It is set when the UI is created and does not change.
- puigame ships a default theme, `DEFAULT_THEME`. It is sized for a **640x360** render surface scaled up with `pg.SCALED`, which suits pixel-art games, and uses pygame-ce's built-in font (`BundledTypeface.PYGAME_DEFAULT`).
- **Later:** individual widgets, or whole subtrees, could have a different theme from the UI's. An earlier attempt, with themes inherited down the tree, is kept at the tag `archive/per-widget-themes`.

## Anchors

Positions are set with a nine-point `Anchor` (`CENTRE`, `TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_RIGHT`, `MID_LEFT`, `MID_RIGHT`, `MID_TOP`, `MID_BOTTOM`) plus a margin.

- A widget is anchored relative to its **parent's rect**; moving or resizing the parent repositions its children. A top-level widget is created with `ui.root` as its parent, so it is anchored to the UI's area (the whole screen by default).
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

`margin` is an `(x, y)` pair. A single number raises `TypeError` (see [Offset](#offset)).

The margin's direction comes from the **widget's own anchor**: a positive margin moves the widget from its anchor point towards its own centre, and a negative margin moves it the other way. The parent's anchor plays no part in the direction.

Margins therefore never use pygame's screen-coordinate signs (`+x` right, `+y` down). The same positive value means "towards the widget's centre" at every anchor, so changing anchors never requires flipping signs. [Offset](#offset) is the one value that does use screen coordinates.

With the same anchor on the widget and its parent, a positive margin moves the widget inwards:

![How positive margins move widgets from each anchor](images/margins.svg)

| Anchor | Margin used |
|---|---|
| Corners (`TOP_LEFT`, `TOP_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_RIGHT`) | `x` horizontally and `y` vertically, both towards the widget's centre |
| `MID_LEFT`, `MID_RIGHT` | `x` only |
| `MID_TOP`, `MID_BOTTOM` | `y` only |
| `CENTRE` | Ignored |

Examples:

- `anchor=BOTTOM_RIGHT, margin=(10, 10)` places the widget 10 px left of and 10 px above its parent's bottom-right corner.
- `anchor=TOP_LEFT, margin=(20, 8)` places it 20 px in from the left and 8 px down from the top.
- `anchor=MID_TOP, parent_anchor=MID_BOTTOM, margin=(0, 4)` places it directly below its parent with a 4 px gap.
- `anchor=TOP_RIGHT, margin=(-8, -8)` moves the widget 8 px up and 8 px right of its parent's top-right corner, so it overlaps the corner, like a notification badge.
- `anchor=TOP_LEFT, parent_anchor=BOTTOM_RIGHT, margin=(4, 4)` places the widget just outside its parent's bottom-right corner, with a 4 px gap. Here a positive margin moves the widget away from its parent, because the direction comes from the widget's own anchor.
- With the same anchors, `margin=(-8, -8)` moves the widget's top-left corner 8 px back inside its parent's corner, so it overlaps the corner from inside.

![Positive and negative margins, with the same and different anchors](images/margin_signs.svg)

In short: a positive margin always creates space between the matched points, and a negative margin moves them past each other. Whether that space is inside or outside the parent depends on the anchors, not on the sign.

### Placement in three steps

Every placement follows the same three steps:

1. **Match the anchor points**: move the widget so its `anchor` point sits on its parent's `parent_anchor` point.
2. **Apply the margin**: move the widget by the margin, in the direction from its own anchor point towards its own centre. The parent's anchor plays no part.
3. **Apply the offset**: move the widget by the offset, in screen coordinates.

For example, with `anchor=TOP_LEFT` and `parent_anchor=BOTTOM_LEFT`, step 1 hangs the widget below its parent's bottom-left corner. Its centre is to the right of and below its top-left corner, so a positive margin moves it right and down: further below the parent, but also inwards from the parent's left edge.

![Placing a widget in three steps: anchors, margin, offset](images/anchor_steps.svg)

### Absolute placement

`widget.place_at_pos((x, y))` places the widget's top-left corner at `(x, y)` relative to its parent's top-left corner (screen coordinates, for a top-level widget in a full-screen `UI`). It is shorthand that sets `anchor` and `parent_anchor` to `TOP_LEFT` and `margin` to `(x, y)`, not a separate positioning system: layout still runs as normal, and changing the parent's position moves the widget with it. A single number raises `TypeError`, since a position needs both coordinates; the check happens before anything changes, so a rejected call leaves the widget as it was.

### Offset

`offset` is an optional `(x, y)` nudge in **screen coordinates** (pygame's convention: `+x` is right, `+y` is down), applied after the anchor and margin. It works on every anchor, including centred axes, where margins have no inward direction:

- `anchor=CENTRE, offset=(0, -20)` places a widget 20 px above the centre of its parent.
- `anchor=MID_BOTTOM, margin=(0, 12), offset=(20, 0)` places it 12 px up from the bottom edge, then 20 px right of centre.

The two parameters keep one meaning each: `margin` is space relative to the anchors, `offset` is a plain screen-space shift.

`margin` and `offset` both require an `(x, y)` pair, and a single number raises `TypeError`. This keeps every position-like value in one shape, matching pygame-ce, where positions and sizes are always pairs. For `offset` in particular, an equal shift on both axes is a diagonal move and rarely intended.

Both are stored as `pygame.Vector2`, whatever form they are given in, so layout can use them in calculations directly. They are properties: assigning a new value converts it, while changing the stored vector in place (for example `widget.offset.y -= 2` to animate a slide) works as expected.

## State

A widget's state is a `State`, an `enum.Flag`. It is derived from the widget's flags and from interaction, so it describes behaviour as well as appearance, and it selects the widget's cached image (see [Rendering and caching](#rendering-and-caching)):

```python
class State(Flag):
    BASE = 0
    DISABLED = auto()
    HIGHLIGHTED = auto()
    PRESSED = auto()
    CHECKED = auto()
    EDITING = auto()
```

| Member | Meaning |
|---|---|
| `BASE` | No flags set: the widget's ordinary state |
| `DISABLED` | The widget is not `enabled_in_tree`: it ignores input and draws its disabled look |
| `HIGHLIGHTED` | The mouse is over the widget, or keyboard navigation has selected it (see [Highlight](#highlight)). Pressing adds `PRESSED` on top |
| `PRESSED` | A press, by mouse button or by Enter or Space, is in progress on the widget |
| `CHECKED` | A `Checkbox` is checked |
| `EDITING` | A `TextBox` is receiving typed text |

Each member is one bit, so a combination such as `State.HIGHLIGHTED | State.PRESSED` is a single `State` value. Combinations are hashable and are used directly as cache keys. `BASE` has no bits set: it is the empty combination.

### Current state

`current_state` is a property built by composing flags with `|=`. Each class adds its own flags on top of its parent's:

- `Widget` starts from `BASE` and adds `DISABLED` when not `enabled_in_tree`.
- `InteractiveWidget` calls `super().current_state` and, unless `DISABLED` is set, adds `HIGHLIGHTED`.
- `Button` adds `PRESSED`, again only when not `DISABLED`.
- `Checkbox` adds `CHECKED` when `checked` is true.
- `TextBox` adds `EDITING`.

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

1. The skin renders the widget's background for a state, returning the image and its position as a `PlacedImage`.
2. Content (`Text` components, check marks, and so on) renders its own `PlacedImage`, also positioned relative to the widget's `rect.topleft`.
3. `compose_layers()` (in `components/placed_image`) combines the layers into one `PlacedImage`, in the order given, with the skin first, so the first layer is at the bottom. Layers with zero width or height are skipped. The surface covers the union of the remaining layers' rects, and its position is the union's top-left. Each layer is drawn onto it at the layer's position minus the union's top-left, so content lands on the body rather than in a halo margin. If no layer has a size, including when there are none, the result is a new 0x0 image at `(0, 0)`; if exactly one does, that layer is returned unchanged.
4. The result is stored in the widget's cache, a `dict[State, PlacedImage]`. The image and its position are kept together, since they are made together and drawing needs both.

Caching rules:

- **Per widget, per state**: one image for every combination in the class's [`possible_states`](#valid-states).
- **Eager**: all states are rendered when the widget is created. Lazy rendering (on first use) is a later optimisation.
- **State changes swap the current `PlacedImage`** from the cache, with no drawing. Each frame, `update()` reads `current_state` and looks up its entry, so `image` and `image_pos` always match the widget's flags and its ancestors' flags. Both are read-only properties: `image` comes from the skin, theme, and state, so assigning it raises `AttributeError`, as assigning `rect` does.
- **Invalidation**: `rebuild_image_cache()` renders every state again. `Label.text`'s setter calls it when the text changes, and a size setter, when added, will too. Assigning a new `skin` does not, so `rebuild_image_cache()` is called afterwards. The theme is fixed for the life of the UI, so it never makes the cache out of date.

Because rendering happens at creation, widgets must be created after `pygame.init()`. Converting surfaces for display (`convert_alpha()`) also requires a display window to exist.

## Drawing: WidgetGroup

`WidgetGroup` subclasses pygame's `LayeredUpdates`:

- **Layers follow the tree**: children draw above their parents. Layers are corrected whenever the tree changes, so layering can change while the game runs.
- **Hidden widgets are skipped**: widgets that are not `visible_in_tree` are not drawn.

The `UI` owns the root `WidgetGroup`. Games that keep their own sprite groups can still add widgets to them, since widgets are ordinary sprites.

## Input

```
pygame event → ui.handle_event → UIManager
   ├─ mouse    → hit-test topmost first → the first widget that handles it stops it
   ├─ keyboard → the editing TextBox, or highlight navigation and activation
   └─ unused   → returns False → the game handles it
```

### Hit-testing

Widgets are hit-tested against their `rect` by default. A widget can opt into a **mask** (built from its current image) so that non-rectangular widgets, such as round buttons, respond only where they are drawn.

### Highlight

Mouse hover and keyboard focus are **one concept**, the highlight, shown with `HIGHLIGHTED`. A widget is highlighted when the mouse is over it or keyboard navigation has selected it, before any press. The `UIManager` tracks a single highlighted widget.

- **Mouse**: moving the mouse highlights the topmost `highlightable_in_tree` widget under the cursor. Moving onto empty space clears the highlight.
- **Keyboard**: Tab and the arrow keys move the highlight between `highlightable_in_tree` widgets. The `UIManager` switches to keyboard mode and hides the cursor.
- **Switching back**: in keyboard mode, hover is ignored, because the hidden cursor still has a position. The first real mouse movement switches back to mouse mode, shows the cursor, and highlights whatever is under it.
- **Turning keyboard navigation off**: a scene that uses the keyboard for something else (typically a game screen, as opposed to a menu or options screen) creates its `UI` with `keyboard_navigation=False`. Tab, the arrow keys, Enter, and Space then pass through to the game, and only the mouse highlights and activates widgets. A `TextBox` being edited still receives typing.

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

The `UIManager` hides and shows the mouse cursor as the input mode changes. A game that manages the cursor itself creates its `UI` with `manage_cursor=False`. When several UIs are shown at once (see [Layering](#layering)), only one should manage the cursor. Since `pygame.mouse.set_visible` affects the whole window, this is an option rather than something puigame always does.

## Callbacks

Callbacks are plain callables passed to widgets and receive the widget as their first argument, so one handler can serve several widgets. The exact names and signatures for `Button`, `Checkbox`, `CheckboxGroup`, and `TextBox` are still open (see [Open questions](#open-questions)).

## Positions and types

- **`pygame.Rect` internally**, for pixel-exact positioning.
- Constructors take a **size**, not a position or rect. Position always comes from layout (parent, anchors, margin, and offset), so a widget's rect sits at `(0, 0)` until layout first runs. Absolute placement uses [`place_at_pos()`](#absolute-placement).
- Smooth movement, if needed, keeps a precise `pygame.Vector2` and rounds it into the `Rect`.
- pygame types use pygame-ce's `pygame.typing` aliases. puigame defines its own `Protocol` classes only for its own concepts.

## Assets

- Bundled assets live in `assets/images/` (default skin art, nine-slice-ready) and `assets/fonts/`, all MIT-compatible.
- They are loaded with `importlib.resources`, so they are found wherever the package is installed.
- Loaded fonts are cached by typeface and size, since loading a font file is slow. All text with the same typeface and size shares one `pg.Font`, which is never changed after it is created, including attributes such as `bold` and `align`.
- Loading failures raise exceptions (for example `FileNotFoundError`) and never exit the program.
- Game-side concerns stay in games: asset folder conventions, resource paths, and PyInstaller handling. Games bundled with PyInstaller need puigame's data files included in their build.

## Naming and code conventions

- **State flags** are adjectives: `enabled`, `visible`, `highlightable`, `checked`; `State` members likewise (`HIGHLIGHTED`, `PRESSED`, `EDITING`).
- **Tree-aware values** end in `_in_tree`: `enabled_in_tree`, `visible_in_tree`, `highlightable_in_tree`. They are calculated on demand, never stored.
- **Permissions** start with `can_`: `can_untoggle`.
- **Possession** starts with `has_`: `has_text`, `has_children`.
- **Methods** are verbs: `show()`, `hide()`, `toggle()`. Values that read and write like attributes, such as `Label.text`, are properties instead.
- **Classes** use `CapWords` with capitalised acronyms (`UIManager`); public names avoid abbreviations, except where they follow pygame's own names (`pos`, as in `event.pos` and `mouse.get_pos()`); English spelling is used (`CENTRE`, `colour`).
- **Docstrings and documentation** use English spelling and the Oxford comma in lists of three or more.
- **Modules** are named after their main class in `lowercase_with_underscores`: `UIManager` lives in `ui_manager.py`, `WidgetGroup` in `widget_group.py`.
- **Error messages** start lowercase, name the exact parameter or field, and have no final full stop. Requirements use "must" and prohibitions use "cannot" (never "must not", which is easy to misread). The bad value follows ", got": `"border_thickness_px cannot be negative, got -2 px"`. Several values are written `name=value` with no spaces around `=`, units are separated by a space (`2 px`), and a second clause follows a semicolon. When a message is split across several string literals, each break comes after a space, so the space ends one line and the next line starts with a word.
- **Exhaustive `match` statements** over an enum end with `case _: assert_never(value)`, so Pyright reports any member that is not handled.
- **`None` checks** use `is None` and `is not None`, never truthiness (`x or default`), so valid falsy values such as `0` or `""` are never replaced by a default. Optional arguments default to `None`, never to a mutable object such as a list, and the real default is created inside the function.

## Package layout

```
src/puigame/
├── assets/
│   ├── fonts/
│   └── images/
├── components/                objects widgets hold
│   ├── __init__.py
│   ├── component.py           Component
│   ├── placed_image.py        PlacedImage
│   ├── skin.py                Skin, NoSkin, DrawnSkin, ImageSkin
│   └── text.py                Text and the font cache
├── core/
│   ├── __init__.py
│   ├── anchor.py              Anchor
│   ├── interactive_widget.py  InteractiveWidget
│   ├── state.py               State
│   ├── ui.py                  UI
│   ├── ui_manager.py          UIManager
│   ├── ui_root.py             UIRoot
│   ├── widget.py              Widget, DEFAULT_DT
│   └── widget_group.py        WidgetGroup
├── themes/
│   ├── __init__.py
│   └── theme.py               Theme and the default theme
├── widgets/
│   ├── __init__.py
│   ├── button.py
│   ├── checkbox.py            Checkbox and CheckboxGroup
│   ├── container.py
│   ├── label.py
│   ├── panel.py
│   └── textbox.py
├── __init__.py                public API re-exports
└── py.typed
```

The tree follows VS Code's Explorer order with `explorer.sortOrderLexicographicOptions` set to `unicode`: folders first, then files, sorted by character code (so `ui.py` comes before `ui_manager.py`). Tests mirror this layout under `tests/`.

### Dependencies

Each layer imports only from the layers above it:

1. `components/placed_image`, `core/anchor`, `core/state`
2. `themes/theme`
3. `components/skin`, `components/text`
4. `core/widget`
5. `core/interactive_widget`, `core/ui_root`, `core/widget_group`
6. `widgets/*`
7. `core/ui_manager`
8. `core/ui`

`UIManager` and `UI` need only `Widget`, `InteractiveWidget`, `UIRoot`, and `WidgetGroup`, not the concrete widgets, so nothing in `core` imports from `widgets`. This prevents circular imports and makes it clear where new code belongs.

## v0.1 scope

**Classes:** `Anchor`, `State`, `Widget`, `InteractiveWidget`, `UIRoot`, `WidgetGroup`, `UIManager`, `UI`, `Theme` with a default theme, `Text`, `NoSkin`, `DrawnSkin`, `ImageSkin` with default art, `Container`, `Panel`, `Label`, `Button`, `Checkbox` with `CheckboxGroup`, and `TextBox`.

**Features:**

- The widget tree, with fixed parents, `kill()`, and the `_in_tree` flags
- Layout every frame from anchors, margin, and offset, plus `place_at_pos()`
- Eager per-state image caching
- A single highlight shared by mouse and keyboard, with keyboard navigation that can be turned off
- Press-and-release activation with mouse capture, and a mouse-button enable map
- Text editing in `TextBox`
- Cursor management, with an opt-out
- Optional mask hit-testing
- Bundled default art and fonts, loaded with `importlib.resources`

**Later:** lazy caching, per-widget themes, moving widgets to a new parent, an `Image` widget, sliders and progress bars (as compound widgets), dropdowns, scroll and list views, row and column layouts, a shared skin cache, and a non-linear (eased) halo fade.

## Build order

Each step is one branch and pull request, with tests:

1. `docs/architecture`: this document
2. `chore/package-structure`: subpackages, `__init__.py` files, and module stubs
3. `feat/widget-base`: `Anchor`, `State`, the abstract `Skin` with `TransparentSkin`, and a first pass at `Widget`, with the tree, flags, and state cache (replaces the `hello()` placeholder)
4. `feat/theme-drawn-skin`: `Theme` and `DrawnSkin`
5. `feat/widget-tree`: fixed parents, `kill()`, `UIRoot`, `NoSkin`, and `Container`
6. `feat/text`: `Text` component and font cache
7. `feat/layout`: positioning from anchors, margin, and offset, plus `place_at_pos()`
8. `feat/widget-group`: `WidgetGroup`
9. `feat/panel-label`: `Panel` and `Label`
10. `feat/ui`: `InteractiveWidget`, `UIManager`, and `UI`: input routing, highlight, keyboard mode, and cursor management
11. `feat/button`: `Button`
12. `feat/checkbox`: `Checkbox` and `CheckboxGroup`
13. `feat/textbox`: `TextBox`
14. `feat/image-skin`: `ImageSkin`, nine-slice scaling, pixel-art option, and default art

## Open questions

- **Callbacks**: names and signatures for each widget, whether programmatic changes (for example `checkbox.checked = True`) notify, and whether Escape on a `TextBox` has its own callback.
- **Combining style overrides**: overrides are currently absolute, so when two active states set the same field the later one in `style_overrides` wins, and combined keys such as `State.DISABLED | State.HIGHLIGHTED` are rejected. Possible next steps, decided once a real widget needs them (most likely `Checkbox`):
  - **Relative overrides**: colour fields that multiply the value underneath (a tint, or a lighten or darken factor) as well as replacing it, so effects such as hover and checked combine on the same field. Integer fields would add, and enum fields such as `halo_fade_profile` would still replace. `StyleOverride` would need a way to mark each value as absolute or relative.
  - **Two passes**: apply absolute values first, so the most specific wins, then relative values on top. Multiplication gives the same result in any order, so relative values would no longer depend on dict order.
  - **Combined keys**: allowed only if stacking and relative overrides cannot express a look. Overrides would apply in order of specificity (fewer flags first, then dict order), worked out once when the theme is created and stored privately, so `style_overrides` stays as given. A relative value in a combined key is an extra adjustment for the combination; an absolute value replaces whatever came before.
  - **Where it lives**: change `Theme` itself if the new rules replace the old ones; use a subclass, or a strategy object the theme holds, only if both sets of rules are needed side by side.
