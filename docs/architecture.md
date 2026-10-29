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
- [Drawing](#drawing)
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

- **`ui.root`**: a `UIRoot`, the widget at the top of the UI's tree. It covers the surface the UI draws on, at `(0, 0)` moved by its `offset`, instead of anchoring to a parent; it has no parent itself, and holds the UI's theme. A UI that covers only part of the surface is a top-level `Container` anchored inside the root, and changing the root's `offset` moves the whole UI, for example to shake it. Every widget in the UI is its child, directly or further down the tree.
- **A manager**: a private `UIManager` that handles the UI's input: which events the UI consumes, the highlight, and presses (see [Input](#input)). It has no public API of its own yet, so it is not exposed as an attribute.

`UI` passes the calls through, so a game uses `ui.root` and the `UI`'s own methods. Every widget is created with its parent as the first argument, so a widget at the top level of a UI is created with `ui.root` as its parent.

```python
ui = puigame.UI(size=(640, 360))
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

The game passes **every** event to `handle_event()`, not only mouse events: the UI ignores what it has no use for, but needs window events such as `WINDOWLEAVE` and `WINDOWFOCUSLOST` to keep the highlight and presses right. puigame never calls `pygame.event.get()` or `pygame.mouse.get_pos()`, so it sees only the events it is given.

`UI`'s `size` is the size of the surface it draws on, and its rects and event positions are in that surface's pixels. A game that draws at a low resolution and scales up to the window, as pixel-art games do, opens its display with `pg.display.set_mode(size, pg.SCALED)`: pygame scales the display to the window and maps mouse positions back to the display's own pixels, so puigame needs no scaling setting. A game that scales by hand converts event positions before passing events in. puigame never opens or changes the display itself.

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
- **Each UI has its own highlight and presses.** Once keyboard navigation arrives, each will also have its own settings: a HUD would typically turn keyboard navigation off, while a pause menu keeps it on.
- **Only one UI should manage the cursor** at a time, once cursor management arrives, since the cursor belongs to the whole window. The others would be created with `manage_cursor=False` (see [Cursor](#cursor)).

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
Widget                  rect, anchor, fixed parent, children, flags, skin, per-state image cache
├── UIRoot              top of a UI's tree: covers the draw surface, holds the theme, has no parent
├── Container           invisible group of children (NoSkin)
├── Panel               group of children with a background (skin given on creation)
├── Label               + Text component and text property, no background (NoSkin), non-interactive
└── InteractiveWidget   + the highlight and activation behaviour interactive widgets share
    ├── Button          + Text component, pressed look, on_click
    │   └── Checkbox    + checked, can_untoggle, optional CheckboxGroup
    └── TextBox         + editable Text, editing mode (no PRESSED state)

CheckboxGroup           helper: mutual exclusion between checkboxes (radio behaviour)
UI                      composes root (a UIRoot, which holds the theme) and manager; draws the tree
UIManager               handles one UI's input: consumes events, tracks the highlight and presses
```

- **`InteractiveWidget` is a base class beside `Widget`**, so the `UIManager` can find interactive widgets with `isinstance()` without importing the concrete widgets. Non-interactive widgets (`Container`, `Panel`, and `Label`) have no highlight concept at all.
- **Every widget can hold children.** The tree lives on `Widget` itself, so any widget can parent another (for example a tooltip that is a child of its button). `Container` and `Panel` are thin classes that exist to make intent clear, and differ only in appearance: a `Container` is invisible, and a `Panel` is drawn by the skin it is given. `Panel` extends `Widget`, not `Container`, since a `Container` promises to be invisible.
- Complex widgets are built by **composing** simpler ones (a slider is a container holding a track and a handle button), not by deepening the hierarchy.

### Widgets are not pygame Sprites

A widget has an `image` and a `rect`, like a pygame `Sprite`, but does not extend `Sprite`. A sprite group draws each `image` at its `rect`, in the order the group holds its sprites, including hidden ones. None of that is right for widgets: an image is offset from the rect by `image_pos`, the draw order follows the tree, and hidden subtrees are skipped (see [Drawing](#drawing)). Being a `Sprite` would invite games to draw widgets the one way that silently goes wrong.

Games can still check collisions against a widget's `rect`, with `Rect` methods such as `colliderect()` or with `pygame.sprite.collide_rect()`, which accepts any object with a `rect`.

## Widget tree and flags

### Parents and children

Every widget except a `UIRoot` is created with its `parent` as the first argument, and keeps that parent for its whole life: widgets cannot be moved to a new parent. This keeps the tree simple, and guarantees that every widget can reach its UI's theme from the moment it is created. Construction is therefore top-down: a parent exists before its children.

- `parent` and `children` are read-only. `children` returns a tuple of the widget's children in the order they were created, so it cannot be appended to or replaced.
- A new widget joins its parent's children only once the rest of its setup has succeeded, so a widget whose creation raised is never left in the tree.
- A widget at the top level of a UI is created with `ui.root` as its parent. Every widget in a UI therefore has a parent, except the root itself.
- Each widget keeps a reference to the `UIRoot` at the top of its tree, copied from its parent. Parents never change, so neither does the root, and the reference cannot go out of date.
- To move a widget, kill it and create a new one under the new parent. Moving widgets directly is a later feature.

`kill()` removes a widget for good: the widget leaves its parent's children, and each of its children is killed in turn. It can safely be called more than once. A killed widget keeps its link to its old parent, but should not be used again. `UIRoot.kill()` raises `TypeError`: to remove a whole UI, the game drops every reference to it.

`UIRoot` is created differently from other widgets, since it has no parent. It sets up its root reference and its theme itself, then runs the setup that every widget shares, without calling `Widget.__init__()`.

### Flags

Each widget has its **own** flags, which parents never overwrite, and a tree-aware version of each:

| Own flag | Taking ancestors into account |
|---|---|
| `enabled` | `enabled_in_tree` |
| `visible` | `visible_in_tree` |

- The `_in_tree` values are **calculated on demand**, never stored: a widget is visible in the tree only if it and every widget above it are visible (the same for enabled).
- `consumes_clicks` is a flag with no `_in_tree` version, since it is not inherited: it decides only whether hit-testing can stop on this widget. See [Hit-testing](#hit-testing).
- With keyboard navigation, `InteractiveWidget` will add another pair: `highlightable` (default `True`) and `highlightable_in_tree`, which is true only if the widget's own `highlightable` is true **and** it is `visible_in_tree` and `enabled_in_tree`. Setting `highlightable=False` will let keyboard navigation skip an interactive widget, for example a button that should only respond to the mouse. See [Keyboard navigation](#keyboard-navigation).
- Hiding a parent changes only its own flag; its children's `_in_tree` values change automatically. A child hidden individually stays hidden when its parent is shown again.
- Widgets that are not `visible_in_tree` are not drawn, and are skipped by hit-testing; widgets that are not `enabled_in_tree` ignore input, but still block clicks to whatever is below them.

## Components

Components are objects a widget **holds** as attributes, rather than classes it inherits from. This avoids multiple inheritance and lets one widget hold several of the same kind (for example a title and a subtitle).

| Component | Held by | Job |
|---|---|---|
| **`Skin`** | Every `Widget` (required; `Container` and `UIRoot` use `NoSkin`) | Renders the widget's background surface for a given size and `Style` (see [Skins](#skins)) |
| **`Text`** | Widgets that display text, such as `Label`, `Button`, and `TextBox` (as many as the widget needs; widgets without text hold none) | Holds the string; is styled and positioned by the owner's `Style` (see [Text](#text)); renders onto the owner's image; keeps no reference to its owner, so the owner rebuilds its images when it changes the text |

A `Text` component is **not** a child widget: it is not in the tree, receives no input, and is drawn into its owner's image rather than on its own.

### Skins

A skin turns a size and a style into a surface. Skins hold no per-widget data and no theme: the widget looks up the `Style` for each of its states in its theme and passes it in. Widgets are given a skin when they are created, keep it for life, and do not know which kind they have. One skin can serve many widgets.

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

- A widget is anchored relative to its **parent's rect**; moving or resizing the parent repositions its children. A top-level widget is created with `ui.root` as its parent, so it is anchored to the surface the UI draws on.
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

There is no separate positioning system for absolute placement. `anchor=Anchor.TOP_LEFT, margin=(x, y)` places the widget's top-left corner at `(x, y)` from its parent's top-left corner (from the top-left of the draw surface, for a top-level widget), and the widget still moves with its parent.

### Offset

`offset` is an optional `(x, y)` nudge in **screen coordinates** (pygame's convention: `+x` is right, `+y` is down), applied after the anchor and margin. It works on every anchor, including centred axes, where margins have no inward direction:

- `anchor=CENTRE, offset=(0, -20)` places a widget 20 px above the centre of its parent.
- `anchor=MID_BOTTOM, margin=(0, 12), offset=(20, 0)` places it 12 px up from the bottom edge, then 20 px right of centre.

The two parameters keep one meaning each: `margin` is space relative to the anchors, `offset` is a plain screen-space shift.

`margin` and `offset` both require an `(x, y)` pair, and a single number raises `TypeError`. This keeps every position-like value in one shape, matching pygame-ce, where positions and sizes are always pairs. For `offset` in particular, an equal shift on both axes is a diagonal move and rarely intended.

Both are stored as `pygame.Vector2`, whatever form they are given in, so layout can use them in calculations directly.

The anchors and margin are fixed on creation and private: they are given to the constructor and seen only through where the widget is placed. `offset` is the one placement value that can change, so it is how widgets move, for example to animate them. It is a property: assigning a new value converts it, while changing the stored vector in place (for example `widget.offset.y -= 2` to animate a slide) works as expected. Changing anchors after creation may be added later, without breaking existing code.

### Layout pass

Layout runs once per frame, before drawing, as a single pass down the tree from the root: the root is placed first, then every widget below it, parents before children, so each widget is placed against its parent's up-to-date rect. Each widget is also placed once when it is created.

Rects are in the coordinates of the surface the UI draws on, which is the screen only when the UI draws straight onto the display surface. Setting a value, such as an offset, only stores it; the next pass applies it. Positions are rounded down once, after the anchors, margin, and offset are combined, so a fractional offset rounds the same way on every widget, the root included.

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
| `HIGHLIGHTED` | The mouse is over the widget (see [Highlight](#highlight)), or, once keyboard navigation arrives, it has selected the widget. Pressing adds `PRESSED` on top |
| `PRESSED` | A press, by mouse button or by Enter or Space, is in progress on the widget |
| `CHECKED` | A `Checkbox` is checked |
| `EDITING` | A `TextBox` is receiving typed text |

Each member is one bit, so a combination such as `State.HIGHLIGHTED | State.PRESSED` is a single `State` value. Combinations are hashable and are used directly as cache keys. `BASE` has no bits set: it is the empty combination.

### Current state

`_current_state` is a private property built by composing flags with `|=`. It is private, like `_possible_states` below, while subclassing `Widget` is unsupported. Each class adds its own flags on top of its parent's:

- `Widget` starts from `BASE` and adds `DISABLED` when not `enabled_in_tree`.
- `InteractiveWidget` calls `super()._current_state` and, unless `DISABLED` is set, adds `HIGHLIGHTED`.
- `Button` adds `PRESSED` only on top of `HIGHLIGHTED`, while a press is held over it. It therefore inherits the suppression by `DISABLED`, and dragging off mid-press shows `BASE`.
- `Checkbox` adds `CHECKED` when `checked` is true.
- `TextBox` adds `EDITING`.

`DISABLED` suppresses `HIGHLIGHTED` and `PRESSED`: a disabled widget never looks interactive.

### Valid states

Not every combination can occur, so each class lists the combinations it can be in **explicitly**, in a private class-level `_possible_states` tuple, annotated as a `ClassVar`. The cache renders exactly these.

| Class | `_possible_states` |
|---|---|
| `Widget`, `Container`, `Panel`, `Label` | `BASE`, `DISABLED` |
| `Button` | `BASE`, `DISABLED`, `HIGHLIGHTED`, `HIGHLIGHTED \| PRESSED` |
| `Checkbox` | Button's four, each with and without `CHECKED` (eight) |
| `TextBox` | `BASE`, `HIGHLIGHTED`, `HIGHLIGHTED \| EDITING`, `DISABLED` |

## Rendering and caching

Each widget builds its image in layers:

1. The skin renders the widget's background for a state, returning the image and its position as a `PlacedImage`.
2. Content (`Text` components, check marks, and so on) renders its own `PlacedImage`, also positioned relative to the widget's `rect.topleft`.
3. `compose_layers()` (in `_components/placed_image`) combines the layers into one `PlacedImage`, in the order given, with the skin first, so the first layer is at the bottom. Layers with zero width or height are skipped. The surface covers the union of the remaining layers' rects, and its position is the union's top-left. Each layer is drawn onto it at the layer's position minus the union's top-left, so content lands on the body rather than in a halo margin. If no layer has a size, including when there are none, the result is a new 0x0 image at `(0, 0)`; if exactly one does, that layer is returned unchanged.
4. The result is stored in the widget's cache, a `dict[State, PlacedImage]`. The image and its position are kept together, since they are made together and drawing needs both.

Caching rules:

- **Per widget, per state**: one image for every combination in the class's [`_possible_states`](#valid-states).
- **Eager**: all states are rendered when the widget is created. Lazy rendering (on first use) is a later optimisation.
- **State changes swap the current `PlacedImage`** from the cache, with no drawing. Each frame, `ui.update()` reads `_current_state` and looks up its entry, so `image` and `image_pos` always match the widget's flags and its ancestors' flags. Both are read-only properties: `image` comes from the skin, theme, and state, so assigning it raises `AttributeError`, as assigning `rect` does.
- **Invalidation**: the private `_rebuild_image_cache()` renders every state again. `Label.text`'s setter calls it when the text changes, and a size setter, when added, will too. The skin is fixed on creation and the theme for the life of the UI, so neither makes the cache out of date.

Because rendering happens at creation, widgets must be created after `pygame.init()`. Converting surfaces for display (`convert_alpha()`) also requires a display window to exist.

## Drawing

### Each frame

`ui.update(dt)` changes state and `ui.draw(surface)` only renders it, so drawing can run any number of times, or be skipped, without changing anything. `update()` runs:

1. **Time-based steps**, using `dt`, such as animations and the caret blink. None exist yet; when the first arrives, it becomes its own walk here, before layout, since it may change offsets or state, and a change made after layout would be drawn a frame late.
2. **The layout pass** (see [Layout pass](#layout-pass)).
3. **The highlight**: the `UIManager` highlights the widget under the last known cursor position (see [Highlight](#highlight)). It runs after layout, so the highlight follows widgets that moved, were hidden, or were disabled under a still cursor.
4. **Image refresh**: each widget picks its `image` and `image_pos` for its current state.

Events are handled before `update()`, so they are hit-tested against the rects placed in the previous frame, which are where the widgets were drawn.

### Tree order

The `UI` draws its tree directly, with no sprite group:

- **Tree order**: widgets are drawn in depth-first pre-order: each widget, then its whole subtree, then its next sibling. Children draw above their parents, and one sibling's subtree never interleaves with another's. The order comes from the tree, so it changes as soon as the tree does.
- **Offset images**: each image is drawn at `rect.topleft + image_pos`, so halos and swell can extend past the rect without moving it.
- **Hidden subtrees are skipped**: a widget that is not `visible` is not drawn, and nor is anything below it.

Hit-testing uses the reverse of this order, so the widget drawn on top is the first to be offered input.

## Input

```
pygame event → ui.handle_event → UIManager
   ├─ mouse button down → hit-test topmost first → consumed if a widget is hit
   ├─ mouse button up   → consumed if its down was
   ├─ motion and window → position stored for the highlight; not consumed
   └─ anything else     → returns False → the game handles it
```

The game passes every event to `ui.handle_event()`, which returns `True` if the UI consumed it. Only the mouse is handled so far; keyboard input comes later (see [Keyboard navigation](#keyboard-navigation)).

### Hit-testing

- Widgets are hit-tested against their `rect`. As with pygame's `Rect.collidepoint()`, the right and bottom edges are outside it. Halos and text that extend past the rect do not count.
- The walk goes in reverse drawing order (see [Tree order](#tree-order)), so the widget drawn on top is found first. Hidden subtrees are skipped. Disabled widgets still count, so a disabled panel still blocks what is below it.
- Each widget has a `consumes_clicks` flag, which decides whether the walk can stop on it. It belongs to the widget alone and is not inherited. It defaults to `True`, since blocking by default is the safer mistake, and is `False` for `Container`, `Label`, and `UIRoot`: a `Label` on a `Button` must not block the button, HUD text should not block clicks meant for the game, and clicks on empty space reach the game.
- Mask hit-testing, so that non-rectangular widgets respond only where they are drawn, is not in v0.1.

### Consuming

- A button down is consumed when the hit-test finds a widget, whichever button it is, and the UI records that button as down.
- A button up is consumed **exactly when its down was**, wherever it lands. A drag in the game world that is released over a panel still reaches the game, and a click on a panel never leaks its release to the game.
- Wheel buttons are never consumed, even over a blocking widget, until a scrollable widget needs them.
- Mouse motion and window events are never consumed.
- A down for a button that is already recorded as down means its up was lost, for example because the game stopped passing events to this UI mid-press, so the stale record is dropped before the new down is handled.

### Highlight

- The `UIManager` tracks a single highlighted widget, shown with `HIGHLIGHTED`. Only an enabled `InteractiveWidget` can be highlighted: non-interactive widgets have no highlight concept.
- Events only store the cursor position: motion, down, and up events store `event.pos`, and `WINDOWLEAVE` forgets it. The highlight is recomputed from that position once per frame, in `update()` (see [Each frame](#each-frame)), not when events arrive.
- The highlighted widget is the hit-test result, if that is an enabled `InteractiveWidget`. Otherwise nothing is highlighted, so a panel covering a button keeps it from highlighting.

### Pressing

- Only the left mouse button presses and activates widgets. A left down on an enabled `InteractiveWidget` starts a press, and the widget remembers that the press started on it.
- **Clicks fire on release**, and only if the release is over the pressed widget and it is still enabled. The press is cleared before the widget is activated, since activation may change the tree.
- During a press, no other widget is highlighted, as with native mouse capture. Dragging off the pressed widget shows `BASE`; dragging back on while still held shows `HIGHLIGHTED | PRESSED`. Releasing off it does nothing.
- A press that starts elsewhere and is dragged onto a widget does not press or activate it.
- A widget killed mid-press can no longer be hit, so its release cannot activate it, and no liveness flag is needed.
- A left down while a press is still recorded ends the old press, since its release was lost. Losing window focus (`WINDOWFOCUSLOST`) also ends any press, since another window may receive the release.
- Widgets respond through private hooks such as `_activate()`, not by handling raw events themselves.

### Keyboard navigation

Not built yet. Mouse hover and keyboard focus will be **one concept**, the highlight:

- **Keyboard**: Tab and the arrow keys move the highlight between `highlightable_in_tree` widgets. The `UIManager` switches to keyboard mode and hides the cursor.
- **Switching back**: in keyboard mode, hover is ignored, because the hidden cursor still has a position. The first real mouse movement switches back to mouse mode, shows the cursor, and highlights whatever is under it.
- **Turning keyboard navigation off**: a scene that uses the keyboard for something else (typically a game screen, as opposed to a menu or options screen) creates its `UI` with `keyboard_navigation=False`. Tab, the arrow keys, Enter, and Space then pass through to the game, and only the mouse highlights and activates widgets. A `TextBox` being edited still receives typing.
- **Keyboard activation** follows the same rule as clicks: Enter or Space down on the highlighted widget shows `HIGHLIGHTED | PRESSED`, and key up fires.

Also later: a **mouse-button enable map**, so that each button chooses which mouse buttons it responds to, and routing wheel events to the nearest scrollable ancestor.

### Editing text

- Clicking a `TextBox`, or pressing Enter while it is highlighted, starts editing. The text at that moment is kept so editing can be cancelled.
- While editing, the `TextBox` **keeps the highlight** regardless of mouse movement, and the arrow keys move the text caret instead of the highlight.
- **Enter** confirms the text. **Escape** cancels and restores the original text.
- **Clicking elsewhere** ends editing and keeps the text. That click does nothing else.

### Cursor

Not built yet, since it is only needed for keyboard navigation. The `UIManager` will hide and show the mouse cursor as the input mode changes. A game that manages the cursor itself will create its `UI` with `manage_cursor=False`. When several UIs are shown at once (see [Layering](#layering)), only one should manage the cursor. Since `pygame.mouse.set_visible` affects the whole window, this is an option rather than something puigame always does.

## Callbacks

Callbacks are plain callables passed to widgets on creation. Each receives the widget as its first argument, so one callback can serve several widgets. puigame calls callbacks rather than posting pygame events: a callback is typed and needs no custom event types, and a game that wants an event posts one from a one-line callback.

### Button

- **Signature:** `on_click: Callable[[Button], object] | None = None`. The return type is `object` rather than `None`, so any callable that takes the button fits, such as `list.append`; the return value is ignored. `None` does nothing on a click.
- **Fixed on creation:** it is stored privately, with no public attribute, so it cannot be read or replaced later.
- **Validated on creation:** a value that is neither `None` nor callable raises `TypeError` before the button is added to its parent. `on_click=handler()`, where `handler` returns `None`, still passes; Pyright catches it for typed callers.
- **Called synchronously** from inside `ui.handle_event()`, on the release that completes a click (see [Pressing](#pressing)). Changes it makes to the widget tree, such as killing or disabling the button, show from the next `update()`. A coroutine function would never run its body, since the coroutine it returns is ignored.
- **Exceptions propagate** to the caller of `handle_event()`. puigame does not catch them, since that would hide bugs in the game.

### Later

- `Checkbox` will inherit `on_click` from `Button` and add a separate `on_toggle(checkbox, checked)` callback for a change of state, following Qt's split between `clicked` and `toggled`.
- The callbacks for `CheckboxGroup` and `TextBox` are still open (see [Open questions](#open-questions)).

## Positions and types

- **`pygame.Rect` internally**, for pixel-exact positioning.
- Constructors take a **size**, not a position or rect. Position always comes from layout (parent, anchors, margin, and offset): a widget is placed when it is created, and again by each layout pass. For absolute placement, see [Absolute placement](#absolute-placement).
- Smooth movement, if needed, keeps a precise `pygame.Vector2` and rounds it into the `Rect`.
- pygame types use pygame-ce's `pygame.typing` aliases. puigame defines its own `Protocol` classes only for its own concepts.

## Assets

- Bundled assets live in `assets/fonts/` and, once `ImageSkin` arrives, `assets/images/` (default skin art, nine-slice-ready), all MIT-compatible.
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
- **Modules** are named after their main class in `lowercase_with_underscores`: `UIManager` lives in `ui_manager.py`, `UIRoot` in `ui_root.py`.
- **Error messages** start lowercase, name the exact parameter or field, and have no final full stop. Requirements use "must" and prohibitions use "cannot" (never "must not", which is easy to misread). The bad value follows ", got": `"border_thickness_px cannot be negative, got -2 px"`. Several values are written `name=value` with no spaces around `=`, units are separated by a space (`2 px`), and a second clause follows a semicolon. When a message is split across several string literals, each break comes after a space, so the space ends one line and the next line starts with a word.
- **Exhaustive `match` statements** over an enum end with `case _: assert_never(value)`, so Pyright reports any member that is not handled.
- **`None` checks** use `is None` and `is not None`, never truthiness (`x or default`), so valid falsy values such as `0` or `""` are never replaced by a default. Optional arguments default to `None`, never to a mutable object such as a list, and the real default is created inside the function.

## Package layout

```
src/puigame/
├── _components/               objects widgets hold
│   ├── __init__.py
│   ├── component.py           Component
│   ├── placed_image.py        PlacedImage, compose_layers
│   ├── skin.py                Skin, NoSkin, DrawnSkin, ImageSkin
│   └── text.py                Text and the font cache
├── _layout/                   anchors and placement
│   ├── __init__.py
│   └── anchor.py              Anchor, get_pos_from_anchor_match
├── _styling/                  styles and themes
│   ├── __init__.py
│   ├── style.py               Style, StyleOverride, FadeProfile, BundledTypeface, RGBA
│   └── theme.py               Theme, DEFAULT_THEME
├── _ui/                       running a widget tree
│   ├── __init__.py
│   ├── ui.py                  UI, DEFAULT_DT
│   ├── ui_manager.py          UIManager
│   └── ui_root.py             UIRoot
├── _widgets/                  base classes, states, and concrete widgets
│   ├── __init__.py
│   ├── button.py              Button
│   ├── container.py           Container
│   ├── interactive_widget.py  InteractiveWidget
│   ├── label.py               Label
│   ├── panel.py               Panel
│   ├── state.py               State
│   └── widget.py              Widget
├── assets/
│   └── fonts/
├── __init__.py                public API: re-exports and __all__
└── py.typed
```

The tree follows VS Code's Explorer order with `explorer.sortOrderLexicographicOptions` set to `unicode`: folders first, then files, sorted by character code (so `_widgets/` comes before `assets/`, and `ui.py` before `ui_manager.py`). Tests mirror this layout under `tests/`, with folder names that drop the leading underscore (`tests/widgets/`).

- **Subpackages are private.** The leading underscore marks everything below `puigame` as internal, so modules can move between releases without breaking games. Each subpackage's `__init__.py` holds only a docstring and imports nothing, so importing one module never pulls in the rest of its package.
- **Base classes live with the concrete widgets.** `Widget`, `InteractiveWidget`, and `State` are in `_widgets`, as Qt and Kivy keep their base widget classes with the widgets.
- **`_layout` is a package ahead of need**, so row, column, and grid layouts have a home when they arrive.
- **`_styling`**, not `themes` (a plural suggests a collection of themes) or `appearance` (which this document uses for skins).
- Unfinished widgets live on branches and are not in the tree until they are built.

### Public API

The public API is exactly the names in `puigame.__all__`, and every public name is imported from `puigame` itself (`from puigame import UI, Button`). Nothing inside the package imports from `puigame`, and tests import public names the same way games do.

| Group | Names |
| --- | --- |
| Running a UI | `UI`, `DEFAULT_DT` |
| Widgets | `Widget`, `Container`, `Panel`, `Label`, `Button` |
| Placement | `Anchor` |
| States | `State` |
| Looks | `Theme`, `DEFAULT_THEME`, `Style`, `StyleOverride`, `FadeProfile`, `BundledTypeface`, `NoSkin`, `DrawnSkin` |

- **Narrow first.** A name can be made public later without breaking anyone, but not made private again. Everything else stays internal: `UIRoot`, `UIManager`, `InteractiveWidget`, `Skin`, `ImageSkin`, `Component`, `Text`, `PlacedImage`, `compose_layers`, `get_pos_from_anchor_match`, and `RGBA`.
- **Themes are the way to change the look in v0.1.** A theme can be built from public names alone; the practical route is `dataclasses.replace(DEFAULT_THEME.base_style, ...)` plus a few `StyleOverride`s. Custom skins (`Skin` and `PlacedImage` made public) are planned for the release after v0.1.
- **`Widget` is public for annotations**, for example a function that takes any parent. Subclassing it is not supported in v0.1.
- **`RGBA` stays internal.** It is an alias for `tuple[int, int, int, int]`, so colour tuples type-check without it, and keeping it private leaves room to accept `pg.Color` later.
- Positions use `Point` from `pygame.typing`, not a puigame type.

### Dependencies

Each layer imports only from the layers above it:

1. `_components/placed_image`, `_layout/anchor`, `_widgets/state`
2. `_styling/style`
3. `_styling/theme`, `_components/component`, `_components/skin`, `_components/text`
4. `_widgets/widget`
5. `_widgets/interactive_widget`, `_ui/ui_root`
6. `_widgets/button`, `_widgets/container`, `_widgets/label`, `_widgets/panel`
7. `_ui/ui_manager`
8. `_ui/ui`

`_widgets` and `_styling` import from each other at package level (`Widget` reads a `Theme`, and a `Theme` is keyed by `State`), but no module imports one that imports it back. `_widgets/widget` imports `UIRoot` from `_ui` for type checking only. `UIManager` and `UI` need only `Widget`, `InteractiveWidget`, and `UIRoot`, not the concrete widgets, so nothing in `_ui` imports them. This prevents circular imports and makes it clear where new code belongs.

## v0.1 scope

**Public classes:** `UI`, `Widget`, `Container`, `Panel`, `Label`, `Button`, `Anchor`, `State`, `Theme` with a default theme, `Style`, `StyleOverride`, `NoSkin`, and `DrawnSkin` (see [Public API](#public-api) for the full list of names).

**Internal classes:** `UIRoot`, `UIManager`, `InteractiveWidget`, `Skin`, `Component`, `Text`, and `PlacedImage`.

**Features:**

- The widget tree, with fixed parents, `kill()`, and the `_in_tree` flags
- Layout every frame from anchors, margin, and offset
- Eager per-state image caching
- A mouse highlight, designed to be shared with keyboard navigation later
- Left-click press-and-release activation with mouse capture
- Bundled fonts, loaded with `importlib.resources`

**Later:** `Checkbox` with `CheckboxGroup`, `TextBox` with text editing, keyboard navigation, cursor management, a mouse-button enable map, `ImageSkin` with default art, mask hit-testing, lazy caching, per-widget themes, moving widgets to a new parent, an `Image` widget, sliders and progress bars (as compound widgets), dropdowns, scroll and list views, row and column layouts, a shared skin cache, and a non-linear (eased) halo fade.

## Build order

Each step is one branch and pull request, with tests:

1. `docs/architecture`: this document
2. `chore/package-structure`: subpackages, `__init__.py` files, and module stubs
3. `feat/widget-base`: `Anchor`, `State`, the abstract `Skin` with `TransparentSkin`, and a first pass at `Widget`, with the tree, flags, and state cache (replaces the `hello()` placeholder)
4. `feat/theme-drawn-skin`: `Theme` and `DrawnSkin`
5. `feat/widget-tree`: fixed parents, `kill()`, `UIRoot`, `NoSkin`, and `Container`
6. `feat/text`: `Text` component and font cache
7. `feat/layout`: positioning from anchors, margin, and offset
8. `refactor/drop-sprite`: widgets stop being pygame Sprites, and `WidgetGroup` is dropped in favour of drawing the tree from `UI`
9. `feat/panel-label`: `Panel` and `Label`
10. `feat/ui`: `InteractiveWidget`, `UIManager`, and `UI`: drawing, input routing, and the mouse highlight
11. `feat/button`: `Button`

## Open questions

- **Callbacks**: names and signatures for `CheckboxGroup` and `TextBox`, whether programmatic changes (for example `checkbox.checked = True`) notify, and whether Escape on a `TextBox` has its own callback.
- **Combining style overrides**: overrides are currently absolute, so when two active states set the same field the later one in `style_overrides` wins, and combined keys such as `State.DISABLED | State.HIGHLIGHTED` are rejected. Possible next steps, decided once a real widget needs them (most likely `Checkbox`):
  - **Relative overrides**: colour fields that multiply the value underneath (a tint, or a lighten or darken factor) as well as replacing it, so effects such as hover and checked combine on the same field. Integer fields would add, and enum fields such as `halo_fade_profile` would still replace. `StyleOverride` would need a way to mark each value as absolute or relative.
  - **Two passes**: apply absolute values first, so the most specific wins, then relative values on top. Multiplication gives the same result in any order, so relative values would no longer depend on dict order.
  - **Combined keys**: allowed only if stacking and relative overrides cannot express a look. Overrides would apply in order of specificity (fewer flags first, then dict order), worked out once when the theme is created and stored privately, so `style_overrides` stays as given. A relative value in a combined key is an extra adjustment for the combination; an absolute value replaces whatever came before.
  - **Where it lives**: change `Theme` itself if the new rules replace the old ones; use a subclass, or a strategy object the theme holds, only if both sets of rules are needed side by side.
