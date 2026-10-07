import pygame as pg
import pytest

from puigame.core.anchor import Anchor
from puigame.core.state import State
from puigame.core.widget import Widget

ANY_SIZE = (10, 10)  # arbitrary widget size for consistency


# region --- Fixtures ---------------------------------------------------------


@pytest.fixture
def family():
    """Return <Grandparent : Parent : Child> widgets in that order."""
    grandparent = Widget(ANY_SIZE)
    parent = Widget(ANY_SIZE, parent=grandparent)
    child = Widget(ANY_SIZE, parent=parent)

    return grandparent, parent, child


# endregion


# region --- Construction -----------------------------------------------------


def test_rect_has_given_size_at_origin():
    widget = Widget(ANY_SIZE)

    assert widget.rect.size == ANY_SIZE
    assert widget.rect.topleft == (0, 0)


def test_zero_size_gives_empty_rect():
    widget = Widget((0, 0))

    assert widget.rect.size == (0, 0)


@pytest.mark.parametrize(
    "size",
    [(-1, 0), (0, -1), (-1, -1), (0, -0.01)],
    ids=["negative width", "negative height", "both negative", "negative float"],
)
def test_negative_size_raises(size):
    with pytest.raises(ValueError):
        Widget(size)


@pytest.mark.parametrize(
    ("margin_values", "expected_vector"),
    [
        (1.0, pg.Vector2(1.0, 1.0)),
        ((1.0, 2.0), pg.Vector2(1.0, 2.0)),
        ([2.0, 3.0], pg.Vector2(2.0, 3.0)),
        (pg.Vector2(4.0, 2.0), pg.Vector2(4.0, 2.0)),
    ],
    ids=["single_float", "tuple", "list", "pg.Vector2"],
)
def test_margin_converts_to_vec2_on_correct_axes(margin_values, expected_vector):
    widget = Widget(ANY_SIZE, margin=margin_values)

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
def test_offset_converts_to_vec2_on_correct_axes(offset_values, expected_vector):
    widget = Widget(ANY_SIZE, offset=offset_values)

    assert isinstance(widget.offset, pg.Vector2)
    assert widget.offset == expected_vector


@pytest.mark.parametrize("offset_value", [1, 2.0])
def test_offset_rejects_single_value(offset_value):
    with pytest.raises(TypeError):
        Widget(ANY_SIZE, offset=offset_value)


@pytest.mark.parametrize("anchor", Anchor)
def test_parent_anchor_defaults_to_anchor(anchor):
    widget = Widget(ANY_SIZE, anchor=anchor)

    assert widget.parent_anchor is anchor


# endregion


# region --- rect -------------------------------------------------------------


def test_assigning_to_rect_raises():
    widget = Widget(ANY_SIZE)

    with pytest.raises(AttributeError):
        widget.rect = pg.Rect(1, 1, 1, 1)


def test_rect_can_change_in_place():
    widget = Widget(ANY_SIZE)
    original_rect = widget.rect

    widget.rect.topleft = (1, 1)

    assert widget.rect is original_rect
    assert widget.rect.topleft == (1, 1)

    widget.rect.x += 1

    assert widget.rect is original_rect
    assert widget.rect.topleft == (2, 1)


# endregion


# region --- Tree: normal use -------------------------------------------------


def test_assigning_parent_in_constructor_links_both_ways():
    parent = Widget(ANY_SIZE)
    child_1 = Widget(ANY_SIZE, parent=parent)
    child_2 = Widget(ANY_SIZE, parent=parent)

    assert parent.children == (child_1, child_2)
    for child in (child_1, child_2):
        assert child.parent is parent


def test_assigning_children_in_constructor_links_both_ways():
    child_1 = Widget(ANY_SIZE)
    child_2 = Widget(ANY_SIZE)
    parent = Widget(ANY_SIZE, children=[child_1, child_2])

    assert parent.children == (child_1, child_2)
    assert child_1.parent is parent
    assert child_2.parent is parent


def test_set_parent_moves_between_parents():
    parent_1 = Widget(ANY_SIZE)
    parent_2 = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent_1)

    child.set_parent(parent_2)

    assert child.parent is parent_2
    assert parent_1.children == ()
    assert parent_2.children == (child,)


def test_set_parent_none_detaches():
    parent = Widget(ANY_SIZE)
    child_1 = Widget(ANY_SIZE, parent=parent)
    child_2 = Widget(ANY_SIZE, parent=parent)

    child_1.set_parent(None)

    assert child_1.parent is None
    assert child_2.parent is parent
    assert parent.children == (child_2,)


# endregion


# region --- Tree: safeguards and edge cases ----------------------------------


def test_set_parent_same_parent_retains_order():
    parent = Widget(ANY_SIZE)
    child_1 = Widget(ANY_SIZE, parent=parent)
    child_2 = Widget(ANY_SIZE, parent=parent)

    child_1.set_parent(parent)

    assert parent.children == (child_1, child_2)


def test_detaching_then_reattaching_does_not_duplicate():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.set_parent(None)
    child.set_parent(parent)

    assert parent.children == (child,)


def test_set_parent_none_when_parent_is_already_none_does_nothing():
    child = Widget(ANY_SIZE)

    child.set_parent(None)

    assert child.parent is None


def test_assigning_child_in_constructor_leaves_previous_parent():
    parent_1 = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent_1)
    parent_2 = Widget(ANY_SIZE, children=[child])

    assert child.parent is parent_2
    assert parent_2.children == (child,)
    assert parent_1.children == ()


def test_set_parent_to_self_raises():
    widget = Widget(ANY_SIZE)

    with pytest.raises(ValueError):
        widget.set_parent(widget)

    assert widget.parent is None


def test_set_parent_to_descendant_raises():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    with pytest.raises(ValueError):
        parent.set_parent(child)

    assert child.parent is parent
    assert parent.children == (child,)


def test_moving_up_tree_does_not_raise(family):
    grandparent, _parent, child = family

    child.set_parent(grandparent)


# endregion


# region --- has_ancestor -----------------------------------------------------


def test_has_ancestor_true_for_parent_and_grandparent(family):
    grandparent, parent, child = family

    assert child.has_ancestor(parent)
    assert child.has_ancestor(grandparent)
    assert parent.has_ancestor(grandparent)


def test_has_ancestor_false_for_self_and_unrelated():
    widget_1 = Widget(ANY_SIZE)
    widget_2 = Widget(ANY_SIZE)

    assert not widget_1.has_ancestor(widget_1)  # self
    assert not widget_1.has_ancestor(widget_2)  # unrelated


def test_has_ancestor_false_for_descendant():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    assert not parent.has_ancestor(child)


# endregion


# region --- enabled and enabled_in_tree propagation --------------------------


def test_enabled_in_tree_true_by_default(family):
    grandparent, parent, child = family

    assert child.enabled_in_tree
    assert parent.enabled_in_tree
    assert grandparent.enabled_in_tree


def test_disabling_self_disables_self_in_tree():
    widget = Widget(ANY_SIZE)

    widget.enabled = False

    assert not widget.enabled_in_tree


def test_disabling_child_does_not_affect_parent():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.enabled = False

    assert parent.enabled_in_tree


def test_disabling_parent_disables_child():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    parent.enabled = False

    assert not child.enabled_in_tree


def test_disabling_both_parent_and_child_stays_disabled():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.enabled = False
    parent.enabled = False

    assert not child.enabled_in_tree


def test_disabling_grandparent_disables_child(family):
    grandparent, _parent, child = family

    grandparent.enabled = False

    assert not child.enabled_in_tree


def test_reenabling_parent_enables_child():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    parent.enabled = False
    parent.enabled = True

    assert child.enabled_in_tree


def test_reenabling_parent_does_not_enable_disabled_child():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.enabled = False
    parent.enabled = False
    parent.enabled = True

    assert not child.enabled_in_tree


def test_reenabling_child_does_not_affect_parent():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.enabled = False
    parent.enabled = False
    child.enabled = True

    assert not parent.enabled_in_tree


def test_reenabling_parent_does_not_override_disabled_grandparent(family):
    grandparent, parent, child = family

    grandparent.enabled = False
    parent.enabled = False
    parent.enabled = True

    assert not child.enabled_in_tree


# endregion


# region --- visible and visible_in_tree propagation --------------------------


def test_visible_in_tree_true_by_default(family):
    grandparent, parent, child = family

    assert child.visible_in_tree
    assert parent.visible_in_tree
    assert grandparent.visible_in_tree


def test_hiding_self_hides_self_in_tree():
    widget = Widget(ANY_SIZE)

    widget.visible = False

    assert not widget.visible_in_tree


def test_hiding_child_does_not_affect_parent():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.visible = False

    assert parent.visible_in_tree


def test_hiding_parent_hides_child():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    parent.visible = False

    assert not child.visible_in_tree


def test_hiding_both_parent_and_child_stays_hidden():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.visible = False
    parent.visible = False

    assert not child.visible_in_tree


def test_hiding_grandparent_hides_child(family):
    grandparent, _parent, child = family

    grandparent.visible = False

    assert not child.visible_in_tree


def test_showing_parent_shows_child():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    parent.visible = False
    parent.visible = True

    assert child.visible_in_tree


def test_showing_parent_does_not_show_hidden_child():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.visible = False
    parent.visible = False
    parent.visible = True

    assert not child.visible_in_tree


def test_showing_child_does_not_affect_parent():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    child.visible = False
    parent.visible = False
    child.visible = True

    assert not parent.visible_in_tree


def test_showing_parent_does_not_override_hidden_grandparent(family):
    grandparent, parent, child = family

    grandparent.visible = False
    parent.visible = False
    parent.visible = True

    assert not child.visible_in_tree


# endregion


# region --- current_state ----------------------------------------------------


def test_base_state_is_default():
    widget = Widget(ANY_SIZE)

    assert widget.current_state is State.BASE


def test_disabled_state_when_ancestor_is_disabled():
    parent = Widget(ANY_SIZE)
    child = Widget(ANY_SIZE, parent=parent)

    parent.enabled = False

    assert child.current_state is State.DISABLED


# endregion


# region --- image cache ------------------------------------------------------


def test_image_cache_has_one_surface_per_state():
    widget = Widget(ANY_SIZE)

    # set provides just keys of dictionary
    # set comparison ignores element order
    assert set(widget._image_cache) == set(widget.possible_states)


@pytest.mark.parametrize("state", Widget.possible_states)
def test_every_image_cache_surface_is_same_size_as_rect(state):
    widget = Widget(ANY_SIZE)

    assert widget._image_cache[state].get_size() == widget.rect.size


# endregion


# region --- place_at_pos -----------------------------------------------------


@pytest.mark.parametrize(
    ("pos"),
    [(1.0, 2.0), [2.0, 3.0], pg.Vector2(4.0, 2.0)],
    ids=["tuple", "list", "pg.Vector2"],
)
def test_place_at_pos_sets_anchor_and_margin(pos):
    widget = Widget(ANY_SIZE)

    widget.place_at_pos(pos)

    assert widget.anchor is Anchor.TOP_LEFT
    assert widget.parent_anchor is Anchor.TOP_LEFT
    assert widget.margin == pos


@pytest.mark.parametrize(
    ("pos"),
    [5, 6.1],
    ids=["int", "float"],
)
def test_place_at_pos_with_single_value_raises(pos):
    widget = Widget(ANY_SIZE)

    with pytest.raises(TypeError):
        widget.place_at_pos(pos)

    assert widget.anchor is Anchor.CENTRE
    assert widget.parent_anchor is Anchor.CENTRE
    assert widget.margin == (0, 0)


# endregion
