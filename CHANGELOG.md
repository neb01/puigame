# Changelog

All notable changes to puigame are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Before 1.0.0, any minor release may break the API.

## [Unreleased]

## [0.3.0] - 2026-11-23

### Added

- `VBox` and `HBox`, invisible widgets that stack their children in a column or a row and size themselves to fit them, with the theme's `box_gap` between neighbours. Hidden children take no space. `align`, a `BoxAlign` (`START`, `CENTRE`, or `END`), places children narrower than the box. A box places its children, so a child's `anchor`, `parent_anchor`, and `margin` must keep their defaults, and other values raise `ValueError`; its `offset` still applies. Sizes and positions are worked out by `ui.update()`.
- Fit-to-text sizing. `Label`, `Button`, and `ToggleButton` accept `None` on either axis of `size`, which fits that axis to their text: the text's box, from the top of its capitals to its baseline, plus `text_margin` on each side, in the theme's base style. Their `size` now defaults to `(None, None)`, so it can be left out. Assigning `text` fits the `None` axes again; the new size applies at once, and the new position at the next `ui.update()`. Empty text counts as one line high and 0 wide. A `Container` has nothing to fit to, so `None` in its `size` raises `ValueError`.
- `FitSize`, the type of a size that can fit its content, for annotations.
- A `Panel` can fit its children. `None` on either axis of its `size` sizes that axis to its visible children whose `anchor` is the same as their `parent_anchor`: the largest child's size plus its margin on each side, floored at 0, or 0 with no such children. Children anchored elsewhere, such as one hanging off the panel's side, are not counted. The size is worked out by `ui.update()`, so a fitted axis is 0 until the first update.

### Changed

- **Breaking:** `Style` now requires `box_gap`, the space in pixels between neighbouring children of a `VBox` or `HBox`. `DEFAULT_THEME` uses 3. A negative gap raises `ValueError`.
- **Breaking:** `DEFAULT_THEME`'s `text_margin` is `(12, 8)`, not `(0, 0)`, so text fitted to its button keeps clear of the border in every state. Text in widgets of a fixed size looks the same, since the default `text_anchor` is `CENTRE` and a margin does not move centred text. A theme built from `DEFAULT_THEME.base_style` with a different `text_anchor` now places its text 12 pixels in from the side and 8 from the top or bottom; set `text_margin=(0, 0)` to keep the old placement.
- `DrawnSkin` draws a widget of any size, flooring each layer's size at 0. A border thicker than half the widget leaves no body, so the widget is all border, and a swell that shrinks a layer past 0 leaves nothing of it to draw. `render()` raised `ValueError` when the body would have had a negative size.

### Fixed

- The bundled fonts' underline and strikethrough positions follow the OpenType specification, which places each line by its top edge: the underline fills the descender row, and the strikethrough the middle row of the x-height. The underline was half a pixel low, and the strikethrough had no position. puigame draws neither, so this affects only programs that use the font files directly.
- An `(x, y)` pair that is not two numbers raises `TypeError` with a message naming the parameter. This covers a widget's or UI's `size`, `margin`, and `offset`, `Style.text_margin` and `Style.text_offset`, and `StyleOverride.text_offset`, and catches a pair of the wrong length, a `set`, and items that are not numbers, such as `None` in a `margin`. Widgets and the UI raised `IndexError`, pygame's `TypeError` or `ValueError`, or a `TypeError` from a comparison; a style accepted most of these, and pygame raised `ValueError` when a widget drew text in that style.

## [0.2.1] - 2026-11-18

### Fixed

- The bundled fonts load when puigame is imported from a zip archive, such as an app made with `zipapp`. They were opened by a path that does not exist inside an archive.

## [0.2.0] - 2026-11-18

### Added

- `ToggleButton`, a button that switches between checked and unchecked when clicked. It calls `on_toggle` with the button and its new value on every change, from a click, from `toggle()`, or from assigning `checked`. While checked, it adds `State.CHECKED` on top of its other states, including disabled.
- `ToggleGroup`, which keeps at most one of its toggle buttons checked, as radio buttons do. A button joins a group by passing it as `group` when it is created, and leaves it when it is killed. Checking a button in the group, by a click or from code, unchecks the one that was checked. By default a click cannot uncheck the checked button; `can_uncheck=True` allows it, and code always can. `checked_button` reads or sets the group's checked button, `buttons` lists its buttons, and `ToggleButton.group` gives a button's group.
- `StyleOverride.border_thickness`, so the border thickness can change between states.
- `DEFAULT_THEME` styles `State.CHECKED` with a thicker green border, which stays visible while a toggle button is highlighted, pressed, or disabled.
- Line alignment for multi-line text, set with `Style.text_align` and chosen with `TextAlign`: `LEFT`, `CENTRE`, or `RIGHT`. The anchors still place the whole block of text; alignment places each line within it.

### Changed

- **Breaking:** `consumes_clicks` is renamed `hit_testable`, as a constructor argument and as an attribute of every widget. The flag decides whether hit-testing can stop on a widget, so it also decides whether the widget can be highlighted or pressed, not only whether clicks stop at it.
- **Breaking:** `Style` now requires `text_align`.
- **Breaking:** the mouse wheel is consumed over hit-testable widgets, as clicks are, so scrolling over a panel no longer reaches the game. Both `MOUSEWHEEL` and the wheel's button 4 and 5 events are consumed. Mouse motion and window events still are not.
- **Breaking:** an `(x, y)` pair that contains a `bool` raises `TypeError`: a widget's `size`, `margin`, and `offset`, the `UI`'s `size`, `Style.text_offset` and `text_margin`, and `StyleOverride.text_offset`. pygame reads `True` as 1, so a mistyped flag there was silently accepted.
- **Breaking:** `UIRoot` and `ui.root` are removed, and a top-level widget is created with the `UI` itself as its parent: `Button(ui, ...)` rather than `Button(ui.root, ...)`. A top-level widget's `parent` is now the `UI`, so `parent` is never `None`. The `UI` gains what games used from the root: `rect`, `offset` (to move the whole UI, for example to shake it), `children`, and `theme`. The `UI` is not a widget, so it has no `kill()`, `image`, or flags.
- Trailing whitespace at the end of each line is no longer drawn, so it no longer widens the text's image or moves aligned lines. Text made only of whitespace and newlines now gives a 0x0 image, as empty text does.

## [0.1.0] - 2026-11-06

### Added

- `UI`, which runs a tree of widgets covering one surface. Each frame, the game passes it every event with `handle_event()`, which returns whether the UI consumed the event, then calls `update()` and `draw()`.
- `Button`, with an `on_click` callback and a pressed look; `Label`; `Panel`, a background that stops clicks reaching the widgets and game below it; and `Container`, which groups and places its children.
- Placement against the parent with `Anchor`: a widget's `anchor`, its parent's `parent_anchor`, `margin`, and `offset`.
- Mouse highlight, presses, and left clicks, hit-tested against the draw surface. Clicks on buttons and panels are consumed; mouse motion, wheel, and window events are not.
- Skins: `DrawnSkin`, which draws a widget in its theme's style, including a halo shaped by a `FadeProfile`, and `NoSkin`, which draws nothing.
- Themes: `Theme`, a base `Style` plus a `StyleOverride` for each `State`, applied in a fixed precedence order; and `DEFAULT_THEME`.
- Text placed by its capitals: from the first line's cap height to the last line's baseline, with `TextHorizontalExtent` choosing whether its width comes from the ink or the font's advances.
- Two bundled pixel fonts, chosen with `BundledTypeface`: Neb0Font, proportional and kerned with tabular digits, and NebMon0Font, its monospace version. Both cover printable ASCII.
- Inline type hints (`py.typed`).
- Examples: `minimal.py`, `custom_theme.py`, and `showcase.py`.

[Unreleased]: https://github.com/neb01/puigame/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/neb01/puigame/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/neb01/puigame/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/neb01/puigame/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/neb01/puigame/releases/tag/v0.1.0
