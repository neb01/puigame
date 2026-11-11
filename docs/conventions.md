# puigame conventions

The rules the code, tests, and docs follow, each with its reason. Tools enforce what they can (see [Enforced by tools](#enforced-by-tools)); the rest is kept by review. When a rule changes, change it here in the same pull request.

## Contents

- [Enforced by tools](#enforced-by-tools)
- [Naming](#naming)
- [Code](#code)
- [Errors and validation](#errors-and-validation)
- [Docstrings and comments](#docstrings-and-comments)
- [Tests](#tests)
- [Commits and pull requests](#commits-and-pull-requests)

## Enforced by tools

- **Ruff** checks and formats everything; the selected rules are in `pyproject.toml` (`B`, `COM812`, `D` with the Google convention, `E`, `F`, `I`, `N`, `RET`, `RUF`, `SIM`, `TID`, `UP`, `W`). Lines are at most 88 characters. Relative imports are banned.
- **Pyright** type-checks `src/`, `tests/`, and `examples/` in CI.
- **pre-commit** runs the housekeeping hooks, Ruff, and pyproject-fmt on every commit. Pyright and pytest run only in CI.

Anything a tool already enforces is not repeated below.

## Naming

- **State flags** are adjectives: `enabled`, `visible`, `highlightable`, `checked`; `State` members likewise (`HIGHLIGHTED`, `PRESSED`, `EDITING`).
- **Tree-aware values** end in `_in_tree`: `enabled_in_tree`, `visible_in_tree`. They are calculated on demand, never stored.
- **Permissions** start with `can_` (`can_uncheck`); **possession** starts with `has_` (`has_text`, `has_children`).
- **Methods** are verbs: `show()`, `hide()`, `toggle()`. Values that read and write like attributes, such as `Label.text`, are properties instead.
- **Classes** use `CapWords` with capitalised acronyms (`UIManager`). Public names avoid abbreviations, except where they follow pygame's own names (`pos`, as in `event.pos`). English spelling is used (`CENTRE`, `colour`).
- **Modules** are named after their main class in `lowercase_with_underscores`: `UIManager` lives in `ui_manager.py`.
- **No unit suffixes.** Fields and parameters carry no `_px`; the docstring says "in pixels". This follows pygame (`width`, `border_radius`).
- **Empty images** are "zero size" in names (`zero_size`, `test_…_zero_size_image`) and "0x0" in prose.
- **Locals** say what they hold now, not what they were: `pressed_widget`, not `erstwhile_pressed_widget`.

## Code

- **Imports**: `from typing import X`, never `typing.X`.
- **Keyword-only parameters** wherever two parameters share a type a caller could swap (sizes, positions, margins, offsets). Short, unambiguous signatures such as `render(size, style)` and `PlacedImage(image, pos)` stay positional. Cached private functions take keyword-only arguments.
- **No parameters that do nothing.** A parameter is added when something uses it (YAGNI): removing one later breaks callers, adding an optional one does not.
- **Unfinished features live on branches**, not as stubs in the package: everything under `src/puigame/` ships in the wheel.
- **Name a value only when the name adds meaning** or splits a long expression. A local that is only returned or passed straight on is inlined; a comment explains a non-obvious step better than a name that repeats the call.
- **Blank line before `return`**, except when its block is one simple statement plus the `return`. A compound statement (`if`, `for`, `match`) before a `return` always gets one. Guard clauses return early instead of using `else` after `return`.
- **Empty bodies**: a docstring alone, with no `pass`. `pass` only where there is no docstring, and `...` for stubs. Never `return None` in a function annotated `-> None`.
- **Membership constants** are module-level `frozenset`s (`_WHEEL_BUTTONS`), not tuples or lists repeated inline.
- **`State` order**: members, and the flags in a combination, are listed in `State` declaration order (`HIGHLIGHTED | PRESSED`) in code, tests, and docs. The exceptions are `_STATE_PRECEDENCE`, which is in precedence order, and tests that list them out of order on purpose, to show that order makes no difference.
- **Enums** with explicit values are `@unique`; enums built with `auto()` cannot collide and do not need it.
- **Attributes** follow whether a value can change after creation. A fixed value is private, behind a read-only property where callers need it (`skin`, `parent`, `group`) and with none where they do not (`_anchor`, `_can_uncheck`). A value that changes with no logic is a plain public attribute (`enabled`, `visible`). A value whose change needs logic is a property with a setter (`checked`, `text`).
- **Internal access**: a class reads its own private attributes, and reads other classes' state through their public properties. It writes another class's private state only where the public route would do the wrong thing, or to keep a two-way link in one place (`ToggleGroup` sets and clears each member's `_group`).
- **Asserts** in the package state internal invariants only, never checks on a caller's input, which raise real exceptions (see Errors and validation), since `python -O` strips asserts. Each has a comment above it saying why the invariant holds (`# all widgets have a parent apart from UIRoot, which overrides kill()`). An assert also narrows types for Pyright.
- **One way to do each thing.** When two APIs would do the same job, only one ships. A second can be added later without breaking anyone; removing one cannot.
- **Read-only properties** rely on Python's default `AttributeError` when there is no setter. Only `rect` and `image` have custom raising setters, because `Sprite` users habitually assign them; those setters are typed `value: Never` and return `NoReturn`, so Pyright flags any assignment.
- **Exhaustive `match`** over an enum ends with `case _: assert_never(value)`, so Pyright reports any member that is not handled.
- **`None` checks** use `is None` and `is not None`, never truthiness, so valid falsy values such as `0` or `""` are never replaced. Optional arguments default to `None`, never to a mutable object.
- **Multi-line text** is a single `str` with `\n`.
- **pygame-ce** is required, so its APIs are used freely: `surface.size`, not `surface.get_size()`.

## Errors and validation

- **Validate where a mistake is plausible and would fail far from its cause**, not every possible misuse.
- **Checks run in field declaration order**, and tests mirror that order. Optional values are checked as `x is not None and not isinstance(x, T)`.
- **Messages** start lowercase, name the exact parameter or field, and have no final full stop. Requirements use "must" and prohibitions use "cannot" (never "must not", which is easy to misread). The bad value follows ", got", shown with `!r`: `"style_overrides cannot use combined flags as a key, got <State.CHECKED|PRESSED: 5>"`. Numbers followed by a unit are the exception, since their `str` and `repr` match: `"border_thickness cannot be negative, got -2 px"`. Several values are written `name=value`, a second clause follows a semicolon, and class names appear as written.
- **Split messages** break after a space, so each line but the last ends with a space and the next starts with a word.

## Docstrings and comments

- **Google style**: `Args`, `Returns`, and `Raises` sections. Summary lines are imperative for functions and methods ("Return the style for…"), and noun phrases for properties ("The widget's rect…").
- **English spelling** and the **Oxford comma** in lists of three or more, in docstrings and all documentation.
- **`Raises`** lists exception types in the order of the first check that raises each.
- **Sizes**: render methods document `size` as "``(width, height)`` of the widget's rect, in pixels"; widget constructors say "Width and height in pixels".
- **Setters have no docstring**: the getter's docstring documents the property, including what assigning does.
- **Comments** start lowercase, have no final full stop, and explain why rather than what. Tests use comments, not docstrings.

## Tests

### Layout of a test module

- **Regions** (`# region --- Name ---…` / `# endregion`) group the module: Constants, Stubs, Helpers, Fixtures, then the tests. Region names are code names as written, with `()` on methods (`update()`, `kill()`), and sentence case otherwise; validation tests sit under "Validation" (or "Validation: <name>" where a module has several).
- **Constants** come in this order, as blank-line-separated groups:
  1. named constants the tests deliberately depend on (`NEBMON0FONT_PATH`, `WIDGET_SIZE`, `UIROOT_SIZE`)
  2. plain placeholders, `ANY_*` (`ANY_SIZE`, `ANY_POS`, `ANY_SKIN`, `ANY_STRING`)
  3. colours, in RGB channel order then neutrals: `RED, GREEN, BLUE, BLACK, WHITE`
  4. role colours in `State` declaration order: `BASE_COLOUR, HIGHLIGHTED_COLOUR, PRESSED_COLOUR, DISABLED_COLOUR`
  5. styles (`ANY_STYLE`)
  6. themes: deliberate ones (`STATE_COLOUR_THEME`) before `ANY_THEME`

  One blank line follows the region header, separates the groups, and precedes `# endregion`. Unused constants are removed.
- **Constants are defined in every module that uses them**, never imported from another test module or from `conftest.py`, which is for fixtures. A shared name has the same value everywhere (`ANY_SIZE = (9, 10)`), except `ANY_STRING`, which is deliberately different in every module.

### What a test sets

- **DAMP over DRY**: a test sets every input its assertion depends on, even when a placeholder already holds the right value. Duplication is accepted for readability.
- **Pinned styles**: tests build on an explicit `ANY_STYLE` literal (every `Style` field written out), via `replace(ANY_STYLE, …)`, and a placeholder theme `ANY_THEME = Theme(base_style=ANY_STYLE, style_overrides={})`. `DEFAULT_THEME` appears only where the default look itself is under test. A test that reads text pixels sets every text field that affects what it reads: always the typeface (the test copy of NebMon0Font) and size, `text_align` for multi-line text, and the anchors, margin, offset, and `text_horizontal_extent` only where it reads a position on the widget.
- **Interaction flags**: a test that presses, clicks, or highlights a widget sets `enabled`, `visible`, and `hit_testable`, since hit-testing and activation depend on all three; a look test (one that reads a widget's state-dependent look) sets `enabled`. Flags an assertion does not depend on stay at their defaults.
- **Look tests** read colours that are all distinct, base colours included, so a pixel read from the wrong region or a field applied in the wrong state fails. A module with look tests defines a `STATE_COLOUR_THEME` that gives each state its own colour and builds its UI with a `state_colour_ui` fixture. A stub skin that shows two style fields draws them in fixed regions, independent of other style fields.
- **One act per test**: a behaviour that differs by starting value (checked or unchecked, say) is one test parametrised over the starting value, not a sequence of changes in one test. Parameter lists are literal, with no guards or filtering inside the test.
- **Mouse helpers**: left presses, releases, and clicks, plus mouse motion, go through the shared `left_press()`, `left_release()`, `left_click()`, and `move_mouse()` helpers in `tests/mouse_helpers.py`, which take `pos` as a keyword. The press and release helpers return whether the UI consumed the event, so a test asserts on the call (`assert left_press(ui, pos=(1, 2))`) or calls it bare when only the effect matters. Other buttons, other events, and parametrised event types are built inline, so the difference stands out. The helpers never call `update()`, so a test shows where each frame falls.
- **Frames**: a test calls `update()` before reading a widget's `image`, even where the image is already right at creation, since which image a widget shows before its first frame is an internal detail. Such a test uses a `UI` (the `ui` fixture or one built in the test), since a bare `UIRoot` has no public `update()`. A change and the `update()` that applies it stay together with no blank line between them; setup is separated from the first `update()` by a blank line.
- **Literal expected values**, never the production formula. Different x and y values everywhere (`(9, 10)`, not `(10, 10)`), so a swapped axis fails.
- **Test through the public API**, importing public names from `puigame`; internal names come from their private modules. The deliberate white-box exceptions are the font-cache tests, the `Theme._style_for()` tests, which pin the override precedence order directly, and the `DEFAULT_THEME` test that `CHECKED` changes the style in every state a toggle button can be in. Where there is no public attribute, observe the effect (`ui_root.children == (widget,)`, `widget.rect.topleft`).
- **Expected values match the actual type** (an int tuple for a rect position, a `pg.Vector2` for `offset`). Number types are only varied where the code branches on them.
- **Images**: sizes are checked with `.size`. Shapes are compared with `pg.mask.from_surface(s, 0)` and the three-way overlap check; pixel tests use literal coordinates.
- **Stubs** use asymmetric values so wiring mistakes show. Rules every skin must follow are contract tests parametrised over factories.

### Names and parametrisation

- **Test names** describe behaviour. Raising tests on construction are `test_constructor_with_<bad input>_raises`; types in names are lowercase and in value order, joined as `int_str_or_none`. Group names stand in for three or more fields sharing a rule. Unqualified "button" and "click" mean the left button; only the right is named.
- **Value order** in parametrisations: `bool`, `int`, `float`, then `str`, `bytes`, then containers (`tuple`, `list`, `pg.Vector2`), then `None` last. Enum members come before standard-library types, in declaration order; field-name lists are in declaration order; numbers ascend.
- **Parameter names** are the name of the argument the value is passed to (`button`, `margin`), prefixed only where that name would shadow a built-in (`event_type`). Expected values are `expected_<name>`. `value` is used only alongside `field_name`, for parametrisations over fields, which need no `ids`; stacked parametrisations put `field_name` on top.
- **`ids`** are lowercase prose naming the case; code names as written; enum members as lowercase words (`"left button"`, `"pg.Vector2 of ints"`). A parametrisation whose only parameter is an enum member needs no `ids`, since pytest names each case after the member (`[TextAlign.LEFT]`).
- **Variable names** are the class name in snake_case (`toggle_button`, `toggle_group`), including callback parameters (`lambda toggle_button, checked: …`). Where a test has several of one class, the role goes in front (`old_toggle_button`, `new_toggle_button`); numbers are used only where position is the point (`toggle_button_1` in a joining-order test).
- **Event variables** are named after the pygame event type (`mouse_button_down_event`), as the `UIManager` handlers are. Their attributes are passed in pygame's order, `pos` before `button`.

### Pairing and order

- **Every raising test has a can-take partner** showing that valid input works; the can-take test comes first, straight before its raising test. Where `Style` and `StyleOverride` share a rule, the `Style` pair comes before the `StyleOverride` pair.
- **Join or split**: cases share one parametrised test when they follow the same rule with the same valid and invalid values; otherwise they are split.
- **Raising tests check the exception type only** (no `match=`), and keep raising and non-raising cases in separate tests. A constructor raising test also asserts that the widget was not attached (`ui_root.children == ()`).
- **One representative wrong value per plausible mistake**, including `None` for every non-optional field.
- **Assertions** put the actual value first: `assert actual == expected`. A fixed bool expectation is a bare `assert x` or `assert not x`; a parametrised one uses `is` (`assert result is consumed`), since `==` would accept `1` for `True`.
- **Wrong-type tests** that pass a value Pyright rejects use a narrow ignore on that line, naming the rule (`# pyright: ignore[reportArgumentType]`). A one-case parametrisation, `cast()`, or an `Any` variable would hide the intent.
- **Field-name parametrisations on `StyleOverride`** build the override with `replace(StyleOverride(), **{field_name: value})`, since Pyright checks `StyleOverride(**{...})` against every keyword parameter.
- **Assignment tests** for read-only properties share one shape: the `widget` fixture and one assignment of a plausible value inside `pytest.raises(AttributeError)`, with a Pyright ignore.
- **Bugs** get a test that fails first.

## Commits and pull requests

- **Conventional Commits** for commit messages and pull request titles (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`); a `!` marks a breaking change (`refactor!: drop the _px suffix…`). Breaking changes are allowed between 0.x releases.
- **One logical change per commit**, committed as soon as it is done, with its updated tests, so every commit passes.
- **One concern per pull request.** Unrelated fixes go in their own small `fix:` pull request from `main`. Pull requests merge with merge commits, and branches are deleted on merge.
