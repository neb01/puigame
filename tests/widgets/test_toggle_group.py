import pytest

from mouse_helpers import left_click
from puigame import UI, Anchor, NoSkin, ToggleButton, ToggleGroup, Widget
from puigame._ui.ui_root import UIRoot
from stubs import OnToggleError, on_toggle_error

# region --- Constants --------------------------------------------------------

ANY_SIZE = (9, 10)
ANY_SKIN = NoSkin()

# endregion


# region --- Helpers ----------------------------------------------------------


def interact_via_click(ui: UI, toggle_button: ToggleButton) -> None:
    left_click(ui, pos=(1, 2))


def check_via_checked_button(ui: UI, toggle_button: ToggleButton) -> None:
    assert toggle_button.group is not None
    toggle_button.group.checked_button = toggle_button


def uncheck_via_checked_button(ui: UI, toggle_button: ToggleButton) -> None:
    assert toggle_button.group is not None
    toggle_button.group.checked_button = None


def interact_via_toggle(ui: UI, toggle_button: ToggleButton) -> None:
    toggle_button.toggle()


def check_via_attribute(ui: UI, toggle_button: ToggleButton) -> None:
    toggle_button.checked = True


def uncheck_via_attribute(ui: UI, toggle_button: ToggleButton) -> None:
    toggle_button.checked = False


CHECK_ROUTES = (
    pytest.param(interact_via_click, id="click"),
    pytest.param(check_via_checked_button, id="checked button"),
    pytest.param(interact_via_toggle, id="toggle"),
    pytest.param(check_via_attribute, id="attribute"),
)

CODE_UNCHECK_ROUTES = (
    pytest.param(uncheck_via_checked_button, id="checked button"),
    pytest.param(interact_via_toggle, id="toggle"),
    pytest.param(uncheck_via_attribute, id="attribute"),
)

UNCHECK_ROUTES = (
    pytest.param(interact_via_click, id="click"),
    pytest.param(uncheck_via_checked_button, id="checked button"),
    pytest.param(interact_via_toggle, id="toggle"),
    pytest.param(uncheck_via_attribute, id="attribute"),
)


# endregion


# region --- Construction -----------------------------------------------------


def test_new_group_has_no_buttons():
    toggle_group = ToggleGroup()

    assert toggle_group.buttons == ()


def test_new_group_has_no_checked_button():
    toggle_group = ToggleGroup()

    assert toggle_group.checked_button is None


def test_buttons_lists_buttons_in_joining_order(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button_1 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )
    toggle_button_2 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )
    toggle_button_3 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    assert toggle_group.buttons == (toggle_button_1, toggle_button_2, toggle_button_3)


def test_group_can_have_buttons_with_none_checked(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=False,
    )
    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=False,
    )

    assert toggle_group.checked_button is None


def test_first_button_created_checked_is_checked_button(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    assert toggle_group.checked_button is toggle_button


def test_constructor_with_second_checked_button_raises(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    with pytest.raises(ValueError):
        ToggleButton(
            ui_root,
            size=ANY_SIZE,
            skin=ANY_SKIN,
            group=toggle_group,
            checked=True,
        )

    assert ui_root.children == (toggle_button,)
    assert toggle_group.buttons == (toggle_button,)
    assert toggle_group.checked_button is toggle_button


def test_group_can_have_members_with_different_parents(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button_1 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    parent = Widget(ui_root, size=ANY_SIZE, skin=ANY_SKIN)
    toggle_button_2 = ToggleButton(
        parent,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    assert toggle_group.buttons == (toggle_button_1, toggle_button_2)


# endregion


# region --- Checking ---------------------------------------------------------


@pytest.mark.parametrize("check_function", CHECK_ROUTES)
def test_checking_member_makes_it_checked_button(ui: UI, check_function):
    toggle_group = ToggleGroup()
    ToggleButton(
        ui.root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    toggle_button = ToggleButton(
        ui.root,
        size=(9, 10),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        group=toggle_group,
        checked=False,
    )

    check_function(ui, toggle_button)

    assert toggle_group.checked_button is toggle_button


@pytest.mark.parametrize("check_function", CHECK_ROUTES)
def test_checking_member_unchecks_checked_button(ui: UI, check_function):
    toggle_group = ToggleGroup()
    old_toggle_button = ToggleButton(
        ui.root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    new_toggle_button = ToggleButton(
        ui.root,
        size=(9, 10),
        skin=ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        group=toggle_group,
        checked=False,
    )

    check_function(ui, new_toggle_button)

    assert not old_toggle_button.checked


@pytest.mark.parametrize("check_function", CHECK_ROUTES)
def test_checking_member_calls_old_then_new_on_toggle(ui: UI, check_function):
    on_toggle_calls = []
    toggle_group = ToggleGroup()
    old_toggle_button = ToggleButton(
        ui.root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked, toggle_group.checked_button),
        ),
        group=toggle_group,
        checked=True,
    )

    new_toggle_button = ToggleButton(
        ui.root,
        size=(9, 10),
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked, toggle_group.checked_button),
        ),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        group=toggle_group,
        checked=False,
    )

    check_function(ui, new_toggle_button)

    assert on_toggle_calls == [
        (old_toggle_button, False, new_toggle_button),
        (new_toggle_button, True, new_toggle_button),
    ]


def test_checking_member_with_nothing_checked_calls_only_its_on_toggle(ui_root: UIRoot):
    on_toggle_calls = []
    toggle_group = ToggleGroup()
    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=False,
    )

    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=False,
    )

    toggle_button.checked = True

    assert on_toggle_calls == [(toggle_button, True)]


@pytest.mark.parametrize("check_function", CHECK_ROUTES)
def test_old_on_toggle_raising_skips_new_on_toggle(ui: UI, check_function):
    on_toggle_calls = []
    toggle_group = ToggleGroup()
    ToggleButton(
        ui.root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=on_toggle_error,
        group=toggle_group,
        checked=True,
    )

    toggle_button = ToggleButton(
        ui.root,
        size=(9, 10),
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        group=toggle_group,
        checked=False,
    )

    with pytest.raises(OnToggleError):
        check_function(ui, toggle_button)

    assert on_toggle_calls == []


# endregion


# region --- Unchecking -------------------------------------------------------


@pytest.mark.parametrize("uncheck_function", CODE_UNCHECK_ROUTES)
def test_unchecking_checked_member_by_code_leaves_nothing_checked(
    ui: UI,
    uncheck_function,
):
    toggle_group = ToggleGroup(can_uncheck=False)
    ToggleButton(
        ui.root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=False,
    )

    toggle_button = ToggleButton(
        ui.root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    uncheck_function(ui, toggle_button)

    assert toggle_group.checked_button is None


@pytest.mark.parametrize("uncheck_function", UNCHECK_ROUTES)
def test_unchecking_checked_member_calls_only_that_on_toggle(ui: UI, uncheck_function):
    on_toggle_calls = []
    toggle_group = ToggleGroup(can_uncheck=True)
    ToggleButton(
        ui.root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=False,
    )

    toggle_button = ToggleButton(
        ui.root,
        size=(9, 10),
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        group=toggle_group,
        checked=True,
    )

    uncheck_function(ui, toggle_button)

    assert on_toggle_calls == [(toggle_button, False)]


def test_clicking_checked_member_in_default_group_does_nothing(ui: UI):
    on_toggle_calls = []
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui.root,
        size=(9, 10),
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(0, 0),
        offset=(0, 0),
        enabled=True,
        visible=True,
        hit_testable=True,
        group=toggle_group,
        checked=True,
    )

    left_click(ui, pos=(1, 2))

    assert on_toggle_calls == []
    assert toggle_button.checked


# endregion


# region --- checked_button ---------------------------------------------------


def test_checked_button_setter_with_current_button_does_not_call_on_toggle(
    ui_root: UIRoot,
):
    on_toggle_calls = []
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=True,
    )

    toggle_group.checked_button = toggle_button

    assert on_toggle_calls == []
    assert toggle_button.checked


def test_checked_button_setter_with_none_and_nothing_checked_does_not_call_on_toggle(
    ui_root: UIRoot,
):
    on_toggle_calls = []
    toggle_group = ToggleGroup()
    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=False,
    )

    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=False,
    )

    toggle_group.checked_button = None

    assert on_toggle_calls == []
    assert toggle_group.checked_button is None


@pytest.mark.parametrize(
    "group_factory",
    [ToggleGroup, lambda: None],
    ids=["button in another group", "button with no group"],
)
def test_checked_button_setter_with_non_member_button_raises(
    ui_root: UIRoot,
    group_factory,
):
    toggle_group = ToggleGroup()
    member_toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    non_member_toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=group_factory(),
        checked=False,
    )

    with pytest.raises(ValueError):
        toggle_group.checked_button = non_member_toggle_button

    assert toggle_group.checked_button is member_toggle_button
    assert toggle_group.buttons == (member_toggle_button,)
    assert not non_member_toggle_button.checked


@pytest.mark.parametrize("checked_button", [5, "apple granny"], ids=["int", "str"])
def test_checked_button_setter_with_non_button_raises(ui_root: UIRoot, checked_button):
    toggle_group = ToggleGroup()
    member_toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    with pytest.raises(ValueError):
        toggle_group.checked_button = checked_button

    assert toggle_group.checked_button is member_toggle_button
    assert toggle_group.buttons == (member_toggle_button,)


def test_checked_button_setter_with_killed_member_raises(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=False,
    )

    toggle_button.kill()

    with pytest.raises(ValueError):
        toggle_group.checked_button = toggle_button

    assert toggle_group.checked_button is None
    assert not toggle_button.checked


# endregion


# region --- kill() -----------------------------------------------------------


def test_killing_member_removes_it_from_buttons(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button_1 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )
    toggle_button_2 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )
    toggle_button_3 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    toggle_button_2.kill()

    assert toggle_group.buttons == (toggle_button_1, toggle_button_3)


def test_killing_member_sets_its_group_to_none(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    toggle_button.kill()

    assert toggle_button.group is None


def test_killing_checked_member_does_not_call_on_toggle(ui_root: UIRoot):
    on_toggle_calls = []
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=True,
    )

    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        on_toggle=lambda toggle_button, checked: on_toggle_calls.append(
            (toggle_button, checked),
        ),
        group=toggle_group,
        checked=False,
    )

    toggle_button.kill()

    assert on_toggle_calls == []


def test_killing_checked_member_leaves_nothing_checked(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    checked_toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=True,
    )

    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=False,
    )

    ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
        checked=False,
    )

    checked_toggle_button.kill()

    assert toggle_group.checked_button is None


def test_killing_parent_removes_member_from_buttons(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    parent = Widget(ui_root, size=ANY_SIZE, skin=ANY_SKIN)
    toggle_button_1 = ToggleButton(
        parent,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    toggle_button_2 = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    parent.kill()

    assert toggle_group.buttons == (toggle_button_2,)
    assert toggle_button_1.group is None


def test_killing_member_twice_does_not_raise(ui_root: UIRoot):
    toggle_group = ToggleGroup()
    toggle_button = ToggleButton(
        ui_root,
        size=ANY_SIZE,
        skin=ANY_SKIN,
        group=toggle_group,
    )

    toggle_button.kill()
    toggle_button.kill()


# endregion
