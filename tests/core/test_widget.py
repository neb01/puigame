from dataclasses import replace
from typing import ClassVar

import pygame as pg
import pytest
from pygame.typing import Point

from puigame.components.placed_image import PlacedImage
from puigame.components.skin import NoSkin, Skin
from puigame.core.anchor import Anchor
from puigame.core.state import State
from puigame.core.ui_root import UIRoot
from puigame.core.widget import Widget
from puigame.themes.theme import DEFAULT_THEME, Style, StyleOverride, Theme
from stubs import FixedLayer

# region --- Constants --------------------------------------------------------

RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
WHITE = (255, 255, 255, 255)

ANY_SIZE = (10, 10)
ANY_SKIN = NoSkin()

# endregion


# region --- Stubs ------------------------------------------------------------


class RecordingLayer(Skin):
    """Skin or component that records every size and style it is given."""

    def __init__(self) -> None:
        """Set up empty lists of received sizes and styles."""
        super().__init__()

        self.received_sizes: list[Point] = []
        self.received_styles: list[Style] = []

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Record ``size`` and ``style``, and return a transparent image."""
        self.received_sizes.append(size)
        self.received_styles.append(style)

        return PlacedImage(
            pg.Surface(size, pg.SRCALPHA),
            (0, 0),
        )


class BodyColourLayer(Skin):
    """Skin or component that fills its whole size with the style's body colour.

    Unlike ``FixedLayer``, it reads the style, so its image shows which state's
    style it was given.
    """

    def render(self, size: Point, style: Style) -> PlacedImage:
        """Return a new surface of ``size``, filled with the body colour, at (0, 0)."""
        image = pg.Surface(size, pg.SRCALPHA)
        image.fill(style.body_colour)

        return PlacedImage(image, (0, 0))


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


@pytest.mark.parametrize("margin_value", [1, 2.0], ids=["int", "float"])
def test_setting_margin_to_single_value_raises(ui_root: UIRoot, margin_value):
    with pytest.raises(TypeError):
        Widget(ui_root, ANY_SIZE, ANY_SKIN, margin=margin_value)


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


# region --- Layout -----------------------------------------------------------


def test_rect_is_placed_against_parent_from_anchors_margin_and_offset():
    ui_root = UIRoot(ANY_SIZE, DEFAULT_THEME)

    parent = Widget(
        ui_root,
        (10, 20),
        ANY_SKIN,
        anchor=Anchor.TOP_LEFT,
        parent_anchor=Anchor.TOP_LEFT,
        margin=(4, 6),
    )

    child = Widget(
        parent,
        (5, 6),
        ANY_SKIN,
        anchor=Anchor.BOTTOM_LEFT,
        parent_anchor=Anchor.BOTTOM_RIGHT,
        margin=(1, 2),
        offset=(3, 4),
    )

    assert child.rect.topleft == (18, 22)


def test_parent_anchor_defaults_to_anchor():
    ui_root = UIRoot((10, 12), DEFAULT_THEME)
    widget = Widget(ui_root, (5, 10), ANY_SKIN, anchor=Anchor.BOTTOM_RIGHT)

    assert widget.rect.topleft == (5, 2)


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
    ui_root = UIRoot(ANY_SIZE, theme)

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


# region --- _iter_descendants ------------------------------------------------


def test_iter_descendants_multiple_levels_order(ui_root: UIRoot):
    widget_a = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_a1 = Widget(widget_a, ANY_SIZE, ANY_SKIN)
    widget_a2 = Widget(widget_a, ANY_SIZE, ANY_SKIN)

    widget_b = Widget(ui_root, ANY_SIZE, ANY_SKIN)
    widget_b1 = Widget(widget_b, ANY_SIZE, ANY_SKIN)

    # white-box: nothing public walks the tree yet
    assert list(ui_root._iter_descendants()) == [
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


# region --- State images -----------------------------------------------------


def test_image_shows_base_style_by_default():
    base_style = replace(DEFAULT_THEME.base_style, body_colour=BLUE)
    theme = Theme(
        base_style,
        {State.DISABLED: StyleOverride(body_colour=RED)},
    )

    ui_root = UIRoot(ANY_SIZE, theme)

    widget = Widget(ui_root, (12, 10), BodyColourLayer())

    assert widget.image.get_at((4, 5)) == BLUE


def test_image_shows_disabled_style_when_ancestor_is_disabled():
    base_style = replace(DEFAULT_THEME.base_style, body_colour=BLUE)
    theme = Theme(
        base_style,
        {State.DISABLED: StyleOverride(body_colour=RED)},
    )

    ui_root = UIRoot(ANY_SIZE, theme)
    parent = Widget(ui_root, ANY_SIZE, BodyColourLayer())
    child = Widget(parent, (10, 12), BodyColourLayer())

    parent.enabled = False
    child.update()

    assert child.image.get_at((3, 5)) == RED


# endregion


# region --- update and image_pos ---------------------------------------------


def test_update_with_state_not_in_possible_states_raises(ui_root: UIRoot):
    class WidgetWithoutDisabledState(Widget):
        # white-box: drops DISABLED, which only puigame's own widgets can do,
        # so disabling the widget gives a state with no cached image
        _possible_states: ClassVar[tuple[State, ...]] = (State.BASE,)

    widget = WidgetWithoutDisabledState(ui_root, ANY_SIZE, ANY_SKIN)
    widget.enabled = False

    with pytest.raises(RuntimeError):
        widget.update()


def test_assigning_to_image_raises(widget: Widget):
    with pytest.raises(AttributeError):
        widget.image = pg.Surface(ANY_SIZE)


def test_assigning_to_skin_raises(widget: Widget):
    with pytest.raises(AttributeError):
        widget.skin = ANY_SKIN


# endregion


# region --- image cache ------------------------------------------------------


def test_image_cache_has_one_image_per_state(widget: Widget):
    # white-box: the cache has no public view
    # set provides just keys of dictionary
    # set comparison ignores element order
    assert set(widget._placed_image_cache) == set(widget._possible_states)


def test_state_change_swaps_to_different_image(widget: Widget):
    enabled_image = widget.image

    widget.enabled = False
    widget.update()

    assert widget.image is not enabled_image


def test_image_cache_reuses_object(widget: Widget):
    original_base_image = widget.image

    widget.enabled = False
    widget.update()
    widget.enabled = True
    widget.update()

    assert widget.image is original_base_image


def test_theme_receives_style_for_each_possible_state():
    base_style = replace(DEFAULT_THEME.base_style, body_colour=BLUE)
    theme = Theme(
        base_style,
        {State.DISABLED: StyleOverride(body_colour=RED)},
    )

    ui_root = UIRoot(ANY_SIZE, theme)
    skin = RecordingLayer()
    Widget(ui_root, ANY_SIZE, skin)

    expected_base_style = base_style
    expected_override_style = replace(base_style, body_colour=RED)

    assert set(skin.received_styles) == {
        expected_base_style,
        expected_override_style,
    }

    assert len(skin.received_styles) == 2


# endregion


# region --- Skin and components ----------------------------------------------


def test_image_without_components_gives_skin_image(ui_root: UIRoot):
    widget = Widget(
        ui_root,
        (10, 12),
        FixedLayer(size=(5, 6), colour=BLUE, pos=(-3, 10)),
        components=[],
    )

    assert widget.image.size == (5, 6)
    assert widget.image_pos == (-3, 10)
    assert widget.image.get_at((0, 0)) == BLUE


def test_image_draws_components_over_skin_in_given_order(ui_root: UIRoot):
    widget = Widget(
        ui_root,
        ANY_SIZE,
        FixedLayer(size=(9, 10), colour=WHITE, pos=(1, 0)),
        components=[
            FixedLayer(size=(5, 6), colour=RED, pos=(2, 3)),
            FixedLayer(size=(7, 8), colour=BLUE, pos=(4, 5)),
        ],
    )

    assert widget.image.get_at((0, 0)) == WHITE
    assert widget.image.get_at((1, 3)) == RED
    assert widget.image.get_at((3, 5)) == BLUE


def test_image_covers_all_layers(ui_root: UIRoot):
    widget = Widget(
        ui_root,
        ANY_SIZE,
        FixedLayer(size=(10, 12), colour=WHITE, pos=(0, 0)),
        components=[
            FixedLayer(size=(5, 5), colour=RED, pos=(-3, 2)),
            FixedLayer(size=(20, 3), colour=BLUE, pos=(4, -1)),
        ],
    )

    assert widget.image.size == (27, 13)
    assert widget.image_pos == (-3, -1)


def test_components_receive_rect_size_and_style_for_each_possible_state():
    ui_root = UIRoot(
        ANY_SIZE,
        theme=Theme(
            DEFAULT_THEME.base_style,
            {State.DISABLED: StyleOverride(body_colour=RED)},
        ),
    )
    recording_layer = RecordingLayer()

    Widget(
        ui_root,
        (10, 12),
        ANY_SKIN,
        components=[recording_layer],
    )

    assert set(recording_layer.received_styles) == {
        DEFAULT_THEME.base_style,
        replace(DEFAULT_THEME.base_style, body_colour=RED),
    }
    assert len(recording_layer.received_styles) == 2
    assert recording_layer.received_sizes == [(10, 12), (10, 12)]


def test_image_keeps_components_given_as_generator(ui_root: UIRoot):
    single_use_components = (
        layer for layer in [FixedLayer(size=(5, 6), colour=RED, pos=(-3, 2))]
    )
    widget = Widget(
        ui_root,
        ANY_SIZE,
        ANY_SKIN,
        components=single_use_components,
    )

    # white-box: nothing public renders a plain Widget again
    widget._rebuild_image_cache()

    assert widget.image.size == (5, 6)
    assert widget.image_pos == (-3, 2)
    assert widget.image.get_at((1, 1)) == RED


# endregion
