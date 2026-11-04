from dataclasses import fields, replace
from pathlib import Path

import pygame as pg
import pytest

from puigame import (
    Anchor,
    BundledTypeface,
    FadeProfile,
    Style,
    StyleOverride,
    TextHorizontalExtent,
)

# region --- Constants --------------------------------------------------------

ANY_STRING = "snath is the specific word for the handle of a scythe"
ANY_PATH = Path("fonts/any_font.ttf")

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

ANY_STYLE = Style(
    body_colour=WHITE,
    border_colour=BLACK,
    border_thickness_px=2,
    corner_radius_px=2,
    halo_colour=(0, 0, 0, 0),
    halo_fade_profile=FadeProfile.SOLID,
    halo_thickness_px=0,
    swell_px=0,
    text_colour=BLACK,
    text_typeface=BundledTypeface.PYGAME_DEFAULT,
    text_font_size=12,
    text_anchor=Anchor.CENTRE,
    text_parent_anchor=Anchor.CENTRE,
    text_horizontal_extent=TextHorizontalExtent.INK,
    text_margin=(0, 0),
    text_offset=(0, 0),
)

# endregion


# region --- Style and StyleOverride validation -------------------------------


@pytest.mark.parametrize(
    "field_name",
    ["border_thickness_px", "corner_radius_px", "halo_thickness_px"],
)
def test_style_negative_thickness_or_radius_raises(field_name):
    with pytest.raises(ValueError):
        replace(ANY_STYLE, **{field_name: -5})


def test_style_override_negative_halo_thickness_px_raises():
    with pytest.raises(ValueError):
        StyleOverride(halo_thickness_px=-5)


@pytest.mark.parametrize(
    "field_name",
    ["border_thickness_px", "corner_radius_px", "halo_thickness_px"],
)
def test_style_thickness_or_radius_can_be_zero(field_name):
    style = replace(ANY_STYLE, **{field_name: 0})

    assert getattr(style, field_name) == 0


def test_style_override_halo_thickness_px_can_be_zero():
    style_override = StyleOverride(halo_thickness_px=0)

    assert style_override.halo_thickness_px == 0


@pytest.mark.parametrize(
    "halo_fade_profile",
    [1, "linear", None],
    ids=["int", "str", "None"],
)
def test_style_int_str_or_none_halo_fade_profile_raises(halo_fade_profile):
    with pytest.raises(TypeError):
        replace(ANY_STYLE, halo_fade_profile=halo_fade_profile)


@pytest.mark.parametrize("halo_fade_profile", [*FadeProfile])
def test_style_halo_fade_profile_can_take_any_member(halo_fade_profile):
    style = replace(ANY_STYLE, halo_fade_profile=halo_fade_profile)

    assert style.halo_fade_profile == halo_fade_profile


@pytest.mark.parametrize(
    "halo_fade_profile",
    [1, "linear"],
    ids=["int", "str"],
)
def test_style_override_int_or_str_halo_fade_profile_raises(halo_fade_profile):
    with pytest.raises(TypeError):
        StyleOverride(halo_fade_profile=halo_fade_profile)


@pytest.mark.parametrize(
    "halo_fade_profile",
    [*FadeProfile, pytest.param(None, id="None")],
)
def test_style_override_halo_fade_profile_can_take_any_member_or_none(
    halo_fade_profile,
):
    style_override = StyleOverride(halo_fade_profile=halo_fade_profile)

    assert style_override.halo_fade_profile == halo_fade_profile


@pytest.mark.parametrize("swell_px", [-5, 0, 5])
def test_style_swell_px_can_take_any_int(swell_px):
    style = replace(ANY_STYLE, swell_px=swell_px)

    assert style.swell_px == swell_px


@pytest.mark.parametrize("swell_px", [-5, 0, 5])
def test_style_override_swell_px_can_take_any_int(swell_px):
    style_override = StyleOverride(swell_px=swell_px)

    assert style_override.swell_px == swell_px


@pytest.mark.parametrize("field_name", ["text_margin", "text_offset"])
@pytest.mark.parametrize(
    "value",
    [1, 3.5, [2, 3], pg.Vector2(4, 5)],
    ids=["int", "float", "list", "pg.Vector2"],
)
def test_style_non_tuple_text_margin_or_text_offset_raises(field_name, value):
    with pytest.raises(TypeError):
        replace(ANY_STYLE, **{field_name: value})


@pytest.mark.parametrize("field_name", ["text_margin", "text_offset"])
@pytest.mark.parametrize(
    "value",
    [
        (0, 0),
        (-1, -4),
        (2, 5),
        (-3, 4),
    ],
    ids=[
        "zero",
        "both negative",
        "both positive",
        "one negative, one positive",
    ],
)
def test_style_text_margin_or_text_offset_can_take_tuple_of_int(field_name, value):
    style = replace(ANY_STYLE, **{field_name: value})

    assert getattr(style, field_name) == value


@pytest.mark.parametrize(
    "text_offset",
    [1, 3.5, [2, 3], pg.Vector2(4, 5)],
    ids=["int", "float", "list", "pg.Vector2"],
)
def test_style_override_non_tuple_text_offset_raises(text_offset):
    with pytest.raises(TypeError):
        StyleOverride(text_offset=text_offset)


@pytest.mark.parametrize(
    "text_offset",
    [
        (0, 0),
        (-1, -4),
        (2, 5),
        (-3, 4),
        None,
    ],
    ids=[
        "zero",
        "both negative",
        "both positive",
        "one negative, one positive",
        "None",
    ],
)
def test_style_override_text_offset_can_take_tuple_of_int_or_none(text_offset):
    style_override = StyleOverride(text_offset=text_offset)

    assert style_override.text_offset == text_offset


def test_style_str_text_typeface_raises():
    with pytest.raises(TypeError):
        replace(ANY_STYLE, text_typeface=ANY_STRING)


@pytest.mark.parametrize(
    "text_typeface",
    [
        *BundledTypeface,
        pytest.param(ANY_PATH, id="Path"),
    ],
)
def test_style_text_typeface_can_take_bundled_typeface_or_path(text_typeface):
    style = replace(ANY_STYLE, text_typeface=text_typeface)

    assert style.text_typeface == text_typeface


@pytest.mark.parametrize("text_font_size", [-5, 0])
def test_style_non_positive_text_font_size_raises(text_font_size):
    with pytest.raises(ValueError):
        replace(ANY_STYLE, text_font_size=text_font_size)


def test_style_text_font_size_can_take_any_positive_int():
    style = replace(ANY_STYLE, text_font_size=24)

    assert style.text_font_size == 24


@pytest.mark.parametrize("field_name", ["text_anchor", "text_parent_anchor"])
@pytest.mark.parametrize(
    "value",
    ["centre", (0.5, 0.5), None],
    ids=["str", "tuple", "None"],
)
def test_style_str_tuple_or_none_text_anchor_or_text_parent_anchor_raises(
    field_name,
    value,
):
    with pytest.raises(TypeError):
        replace(ANY_STYLE, **{field_name: value})


@pytest.mark.parametrize("field_name", ["text_anchor", "text_parent_anchor"])
@pytest.mark.parametrize("value", [*Anchor])
def test_style_text_anchor_or_text_parent_anchor_can_take_any_member(field_name, value):
    style = replace(ANY_STYLE, **{field_name: value})

    assert getattr(style, field_name) == value


@pytest.mark.parametrize(
    "text_horizontal_extent",
    [False, ANY_STRING],
    ids=["bool", "str"],
)
def test_style_bool_or_str_text_horizontal_extent_raises(text_horizontal_extent):
    with pytest.raises(TypeError):
        replace(ANY_STYLE, text_horizontal_extent=text_horizontal_extent)


@pytest.mark.parametrize("text_horizontal_extent", [*TextHorizontalExtent])
def test_style_text_horizontal_extent_can_take_any_member(text_horizontal_extent):
    style = replace(ANY_STYLE, text_horizontal_extent=text_horizontal_extent)

    assert style.text_horizontal_extent == text_horizontal_extent


# endregion


# region --- Structure --------------------------------------------------------


def test_style_override_fields_are_subset_of_style():
    style_field_names = {field.name for field in fields(Style)}
    style_override_field_names = {field.name for field in fields(StyleOverride)}

    assert style_override_field_names - style_field_names == set()


# endregion
