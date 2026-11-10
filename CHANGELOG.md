# Changelog

All notable changes to puigame are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Before 1.0.0, any minor release may break the API.

## [Unreleased]

### Added

- `ToggleButton`, a button that switches between checked and unchecked when clicked. It calls `on_toggle` with the button and its new value on every change, from a click, from `toggle()`, or from assigning `checked`. While checked, it adds `State.CHECKED` on top of its other states, including disabled.
- `StyleOverride.border_thickness`, so the border thickness can change between states.
- `DEFAULT_THEME` styles `State.CHECKED` with a thicker green border, which stays visible while a toggle button is highlighted, pressed, or disabled.
- Line alignment for multi-line text, set with `Style.text_align` and chosen with `TextAlign`: `LEFT`, `CENTRE`, or `RIGHT`. The anchors still place the whole block of text; alignment places each line within it.

### Changed

- **Breaking:** `Style` now requires `text_align`.
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

[Unreleased]: https://github.com/neb01/puigame/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/neb01/puigame/releases/tag/v0.1.0
