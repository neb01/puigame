from dataclasses import replace
from typing import ClassVar

import pygame as pg
import pytest
from pygame.typing import Point

from puigame.components.skin import BlitOffsetImage, Skin, TransparentSkin
from puigame.core.anchor import Anchor
from puigame.core.state import State
from puigame.core.ui_root import UIRoot
from puigame.core.widget import Widget
from puigame.themes.theme import DEFAULT_THEME, RGBA, Style, StyleOverride, Theme

# region --- Constants --------------------------------------------------------

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)

ANY_SIZE = (10, 10)
ANY_POINT = (3, 5)
ANY_SKIN = TransparentSkin()

# endregion


# region --- Fixtures ---------------------------------------------------------


@pytest.fixture
def widget(ui_root: UIRoot) -> Widget:
    """Return a widget under ``ui_root`` with ``ANY_SIZE`` and ``ANY_SKIN``."""
    return Widget(ui_root, ANY_SIZE, ANY_SKIN)


@pytest.fixture
def parent_and_child(ui_root: UIRoot) -> tuple[Widget, Widget]:
    """Return a widget under ``ui_root`` and its child, in that order."""
    parent = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    child = Widget(parent, ANY_SIZE, ANY_SKIN)

    return parent, child


@pytest.fixture
def family(ui_root: UIRoot) -> tuple[Widget, Widget, Widget]:
    """Return a widget under ``ui_root``, its child, and its grandchild, in order."""
    grandparent = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    parent = Widget(grandparent, ANY_SIZE, ANY_SKIN)
    child = Widget(parent, ANY_SIZE, ANY_SKIN)

    return grandparent, parent, child


# endregion


# region --- Construction -----------------------------------------------------


def test_rect_has_given_size(ui_root: UIRoot):
    widget = Widget(ui_root, (10, 20), ANY_SKIN)

    assert widget.rect.size == (10, 20)


def test_zero_size_gives_empty_rect(ui_root: UIRoot):
    widget = Widget(ui_root, (0, 0), ANY_SKIN)

    assert widget.rect.size == (0, 0)


@pytest.mark.parametrize(
    "size",
    [(-1, 0), (0, -1), (-1, -1), (0, -0.01)],
    ids=["negative width", "negative height", "both negative", "negative float"],
)
def test_negative_size_raises(ui_root: UIRoot, size):
    with pytest.raises(ValueError):
        Widget(ui_root, size, ANY_SKIN)

    assert ui_root.children == ()


@pytest.mark.parametrize(
    ("margin_values", "expected_vector"),
    [
        (1.0, pg.Vector2(1.0, 1.0)),
        ((1.0, 2.0), pg.Vector2(1.0, 2.0)),
        ([2.0, 3.0], pg.Vector2(2.0, 3.0)),
        (pg.Vector2(4.0, 2.0), pg.Vector2(4.0, 2.0)),
    ],
    ids=["single float", "tuple", "list", "pg.Vector2"],
)
def test_margin_converts_to_vec2_on_correct_axes(
    ui_root: UIRoot,
    margin_values,
    expected_vector,
):
    widget = Widget(ui_root, ANY_SIZE, ANY_SKIN, margin=margin_values)

    assert isinstance(widget.margin, pg.Vector2)
    assert widget.margin == expected_vector


@pytest.mark.parametrize(
    ("offset_values", "expected_vector"),
    [
        ((1.0, 2.0), pg.Vector2(1.0, 2.0)),
        ([2.0, 3.0], pg.Vector2(2.0, 3.0)),
        (pg.Vector2(4.0, 2.0), pg.Vector2(4.0, 2.0)),
    ],
    ids=["tuple", "list", "pg.Vector2"],
)
def test_offset_converts_to_vec2_on_correct_axes(
    ui_root: UIRoot,
    offset_values,
    expected_vector,
):
    widget = Widget(ui_root, ANY_SIZE, ANY_SKIN, offset=offset_values)

    assert isinstance(widget.offset, pg.Vector2)
    assert widget.offset == expected_vector


@pytest.mark.parametrize("offset_value", [1, 2.0], ids=["int", "float"])
def test_setting_offset_to_single_value_raises(ui_root: UIRoot, offset_value):
    with pytest.raises(TypeError):
        Widget(ui_root, ANY_SIZE, ANY_SKIN, offset=offset_value)


@pytest.mark.parametrize("anchor", Anchor)
def test_parent_anchor_defaults_to_anchor(ui_root: UIRoot, anchor):
    widget = Widget(ui_root, ANY_SIZE, ANY_SKIN, anchor=anchor)

    assert widget.parent_anchor is anchor


# endregion


# region --- rect -------------------------------------------------------------


def test_assigning_to_rect_raises(widget: Widget):
    with pytest.raises(AttributeError):
        widget.rect = pg.Rect(1, 1, 1, 1)


def test_rect_can_change_in_place(widget: Widget):
    original_rect = widget.rect

    widget.rect.topleft = (1, 1)

    assert widget.rect is original_rect
    assert widget.rect.topleft == (1, 1)

    widget.rect.x += 1

    assert widget.rect is original_rect
    assert widget.rect.topleft == (2, 1)


# endregion


# region --- Tree: normal use -------------------------------------------------


def test_parent_child_relationship_is_assigned_both_ways_in_new_widgets(
    ui_root: UIRoot,
):
    child_1 = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    child_2 = Widget(ui_root, ANY_SIZE, ANY_SKIN)

    assert ui_root.children == (child_1, child_2)
    for child in (child_1, child_2):
        assert child.parent is ui_root


def test_child_and_grandchild_return_root_theme():
    theme = Theme(replace(DEFAULT_THEME.base_style, body_colour=BLUE), {})
    ui_root = UIRoot(ANY_SIZE, ANY_POINT, theme)

    child = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    grandchild = Widget(child, ANY_SIZE, ANY_SKIN)

    assert child.theme is theme
    assert grandchild.theme is theme


# endregion


# region --- Tree: read-only parent and children ------------------------------


def test_assigning_to_parent_raises(ui_root: UIRoot):
    widget_1 = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_2 = Widget(ui_root, ANY_SIZE, ANY_SKIN)

    with pytest.raises(AttributeError):
        widget_2.parent = widget_1  # pyright: ignore[reportAttributeAccessIssue]

    assert ui_root.children == (widget_1, widget_2)
    assert widget_1.children == ()
    assert widget_2.parent is ui_root


def test_assigning_to_children_raises(ui_root: UIRoot):
    widget_1 = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_2 = Widget(ui_root, ANY_SIZE, ANY_SKIN)

    with pytest.raises(AttributeError):
        widget_1.children = (widget_2,)  # pyright: ignore[reportAttributeAccessIssue]

    assert ui_root.children == (widget_1, widget_2)
    assert widget_1.children == ()
    assert widget_2.parent is ui_root


# endregion


# region --- kill -------------------------------------------------------------


def test_killing_parent_also_kills_children(ui_root: UIRoot):
    parent = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    child_1 = Widget(parent, ANY_SIZE, ANY_SKIN)
    child_2 = Widget(parent, ANY_SIZE, ANY_SKIN)
    child_3 = Widget(parent, ANY_SIZE, ANY_SKIN)

    parent_group = pg.sprite.Group(parent)
    child_group = pg.sprite.Group(child_1, child_2, child_3)
    joint_group = pg.sprite.Group(parent, child_1, child_2, child_3)

    parent.kill()

    assert parent_group.sprites() == []
    assert child_group.sprites() == []
    assert joint_group.sprites() == []

    assert not parent.alive()
    assert not child_1.alive()
    assert not child_2.alive()
    assert not child_3.alive()


def test_killing_child_causes_it_to_leave_parents_children(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    child.kill()

    assert parent.children == ()


def test_killing_middle_sibling_does_not_affect_order(ui_root: UIRoot):
    widget_1 = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_2 = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_3 = Widget(ui_root, ANY_SIZE, ANY_SKIN)

    assert ui_root.children == (widget_1, widget_2, widget_3)

    widget_2.kill()

    assert ui_root.children == (widget_1, widget_3)


def test_killing_widget_twice_does_not_raise(widget: Widget):
    widget.kill()
    widget.kill()


def test_killing_parent_then_child_explicitly_does_not_raise(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    parent.kill()
    child.kill()


# endregion


# region --- iter_descendants -------------------------------------------------


def test_iter_descendants_multiple_levels_order(ui_root: UIRoot):
    widget_a = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_a1 = Widget(widget_a, ANY_SIZE, ANY_SKIN)
    widget_a2 = Widget(widget_a, ANY_SIZE, ANY_SKIN)

    widget_b = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_b1 = Widget(widget_b, ANY_SIZE, ANY_SKIN)

    assert list(ui_root.iter_descendants()) == [
        widget_a,
        widget_a1,
        widget_a2,
        widget_b,
        widget_b1,
    ]


# endregion


# region --- enabled and enabled_in_tree propagation --------------------------


def test_enabled_in_tree_true_by_default(family: tuple[Widget, Widget, Widget]):
    grandparent, parent, child = family

    assert child.enabled_in_tree
    assert parent.enabled_in_tree
    assert grandparent.enabled_in_tree


def test_disabling_self_disables_self_in_tree(widget: Widget):
    widget.enabled = False

    assert not widget.enabled_in_tree


def test_disabling_child_does_not_affect_parent(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    child.enabled = False

    assert parent.enabled_in_tree


def test_disabling_parent_disables_child(parent_and_child: tuple[Widget, Widget]):
    parent, child = parent_and_child

    parent.enabled = False

    assert not child.enabled_in_tree


def test_disabling_both_parent_and_child_stays_disabled(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    child.enabled = False
    parent.enabled = False

    assert not child.enabled_in_tree


def test_disabling_grandparent_disables_child(family: tuple[Widget, Widget, Widget]):
    grandparent, _parent, child = family

    grandparent.enabled = False

    assert not child.enabled_in_tree


def test_reenabling_parent_enables_child(parent_and_child: tuple[Widget, Widget]):
    parent, child = parent_and_child

    parent.enabled = False
    parent.enabled = True

    assert child.enabled_in_tree


def test_reenabling_parent_does_not_enable_disabled_child(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    child.enabled = False
    parent.enabled = False
    parent.enabled = True

    assert not child.enabled_in_tree


def test_reenabling_child_does_not_affect_parent(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    child.enabled = False
    parent.enabled = False
    child.enabled = True

    assert not parent.enabled_in_tree


def test_reenabling_parent_does_not_override_disabled_grandparent(
    family: tuple[Widget, Widget, Widget],
):
    grandparent, parent, child = family

    grandparent.enabled = False
    parent.enabled = False
    parent.enabled = True

    assert not child.enabled_in_tree


# endregion


# region --- visible and visible_in_tree propagation --------------------------


def test_visible_in_tree_true_by_default(family: tuple[Widget, Widget, Widget]):
    grandparent, parent, child = family

    assert child.visible_in_tree
    assert parent.visible_in_tree
    assert grandparent.visible_in_tree


def test_hiding_self_hides_self_in_tree(widget: Widget):
    widget.visible = False

    assert not widget.visible_in_tree


def test_hiding_child_does_not_affect_parent(parent_and_child: tuple[Widget, Widget]):
    parent, child = parent_and_child

    child.visible = False

    assert parent.visible_in_tree


def test_hiding_parent_hides_child(parent_and_child: tuple[Widget, Widget]):
    parent, child = parent_and_child

    parent.visible = False

    assert not child.visible_in_tree


def test_hiding_both_parent_and_child_stays_hidden(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    child.visible = False
    parent.visible = False

    assert not child.visible_in_tree


def test_hiding_grandparent_hides_child(family: tuple[Widget, Widget, Widget]):
    grandparent, _parent, child = family

    grandparent.visible = False

    assert not child.visible_in_tree


def test_showing_parent_shows_child(parent_and_child: tuple[Widget, Widget]):
    parent, child = parent_and_child

    parent.visible = False
    parent.visible = True

    assert child.visible_in_tree


def test_showing_parent_does_not_show_hidden_child(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    child.visible = False
    parent.visible = False
    parent.visible = True

    assert not child.visible_in_tree


def test_showing_child_does_not_affect_parent(parent_and_child: tuple[Widget, Widget]):
    parent, child = parent_and_child

    child.visible = False
    parent.visible = False
    child.visible = True

    assert not parent.visible_in_tree


def test_showing_parent_does_not_override_hidden_grandparent(
    family: tuple[Widget, Widget, Widget],
):
    grandparent, parent, child = family

    grandparent.visible = False
    parent.visible = False
    parent.visible = True

    assert not child.visible_in_tree


# endregion


# region --- current_state ----------------------------------------------------


def test_base_state_is_default(widget: Widget):
    assert widget.current_state is State.BASE


def test_disabled_state_when_ancestor_is_disabled(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child

    parent.enabled = False

    assert child.current_state is State.DISABLED


# endregion


# region --- update and blit_offset -------------------------------------------


def test_update_with_state_not_in_possible_states_raises(ui_root: UIRoot):
    class WidgetWithoutDisabledState(Widget):
        # override possible_states to be just State.BASE
        possible_states: ClassVar[tuple[State, ...]] = (State.BASE,)

    widget = WidgetWithoutDisabledState(ui_root, ANY_SIZE, ANY_SKIN)
    widget.enabled = False

    with pytest.raises(RuntimeError):
        widget.update()


def test_blit_offset_from_skin_is_set_in_widget(ui_root: UIRoot):
    # stub required to generate an asymmetric blit_offset
    class AsymmetricOffsetSkin(Skin):
        def render(self, size: Point, style: Style) -> BlitOffsetImage:
            return BlitOffsetImage(pg.Surface(size, pg.SRCALPHA), (3, 5))

    widget = Widget(ui_root, ANY_SIZE, AsymmetricOffsetSkin())

    assert widget.blit_offset == (3, 5)


# endregion


# region --- image cache ------------------------------------------------------


def test_image_cache_has_one_image_per_state(widget: Widget):
    # set provides just keys of dictionary
    # set comparison ignores element order
    assert set(widget._image_cache) == set(widget.possible_states)


@pytest.mark.parametrize("state", Widget.possible_states)
def test_every_transparent_image_cache_image_is_same_size_as_rect(
    ui_root: UIRoot, state
):
    widget = Widget(ui_root, (10, 20), TransparentSkin())

    assert widget._image_cache[state].image.get_size() == widget.rect.size


def test_disabling_parent_changes_child_image_after_update(
    parent_and_child: tuple[Widget, Widget],
):
    parent, child = parent_and_child
    enabled_child_image = child.image

    parent.enabled = False
    child.update()

    assert child.image is not enabled_child_image


def test_image_cache_reuses_object(widget: Widget):
    original_base_image = widget.image

    widget.enabled = False
    widget.update()
    widget.enabled = True
    widget.update()

    assert widget.image is original_base_image


def test_new_skin_only_shows_after_rebuild_image_cache(ui_root: UIRoot):
    # stub that draws a single colour, so two skins can be told apart
    class ColourSkin(Skin):
        def __init__(self, colour: RGBA) -> None:
            super().__init__()
            self.colour = colour

        def render(self, size: Point, style: Style) -> BlitOffsetImage:
            surface = pg.Surface(size, pg.SRCALPHA)
            surface.fill(self.colour)

            return BlitOffsetImage(surface, (0, 0))

    widget = Widget(ui_root, ANY_SIZE, ColourSkin(RED))
    assert widget.image.get_at((0, 0)) == RED

    widget.skin = ColourSkin(BLUE)
    assert widget.image.get_at((0, 0)) == RED  # image_cache not yet rebuilt

    widget.rebuild_image_cache()
    assert widget.image.get_at((0, 0)) == BLUE


def test_theme_receives_style_for_each_possible_state():
    # stub that records every style it is given
    class RecordingSkin(Skin):
        def __init__(self) -> None:
            super().__init__()
            self.received_styles: list[Style] = []

        def render(self, size: Point, style: Style) -> BlitOffsetImage:
            self.received_styles.append(style)

            return BlitOffsetImage(pg.Surface(size, pg.SRCALPHA), (0, 0))

    base_style = replace(DEFAULT_THEME.base_style, body_colour=BLUE)
    theme = Theme(
        base_style,
        {State.DISABLED: StyleOverride(body_colour=RED)},
    )

    ui_root = UIRoot(ANY_SIZE, ANY_POINT, theme)
    skin = RecordingSkin()
    Widget(ui_root, ANY_SIZE, skin)

    expected_base_style = base_style
    expected_override_style = replace(base_style, body_colour=RED)

    assert set(skin.received_styles) == {
        expected_base_style,
        expected_override_style,
    }

    assert len(skin.received_styles) == 2


# endregion


# region --- place_at_pos -----------------------------------------------------


@pytest.mark.parametrize(
    "pos",
    [(1.0, 2.0), [2.0, 3.0], pg.Vector2(4.0, 2.0)],
    ids=["tuple", "list", "pg.Vector2"],
)
def test_place_at_pos_sets_anchor_and_margin(widget: Widget, pos):
    widget.place_at_pos(pos)

    assert widget.anchor is Anchor.TOP_LEFT
    assert widget.parent_anchor is Anchor.TOP_LEFT
    assert widget.margin == pos


@pytest.mark.parametrize(
    "pos",
    [5, 6.1],
    ids=["int", "float"],
)
def test_place_at_pos_with_single_value_raises(ui_root: UIRoot, pos):
    widget = Widget(
        ui_root,
        ANY_SIZE,
        ANY_SKIN,
        anchor=Anchor.TOP_RIGHT,
        parent_anchor=Anchor.BOTTOM_LEFT,
        margin=(3, 4),
    )
    with pytest.raises(TypeError):
        widget.place_at_pos(pos)

    assert widget.anchor is Anchor.TOP_RIGHT
    assert widget.parent_anchor is Anchor.BOTTOM_LEFT
    assert widget.margin == (3, 4)


# endregion
