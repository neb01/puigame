from dataclasses import fields, replace
from pathlib import Path

import pygame as pg
import pytest

from puigame.core.anchor import Anchor
from puigame.themes.style import BundledTypeface, FadeProfile, Style, StyleOverride

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
    text_margin=(0, 0),
    text_offset=(0, 0),
)

# endregion


# region --- Style and StyleOverride validation -------------------------------


@pytest.mark.parametrize("swell_px", [-5, 0, 5])
def test_style_swell_px_can_take_any_int(swell_px):
    style = replace(ANY_STYLE, swell_px=swell_px)

    assert style.swell_px == swell_px


@pytest.mark.parametrize("swell_px", [-5, 0, 5])
def test_style_override_swell_px_can_take_any_int(swell_px):
    style_override = StyleOverride(swell_px=swell_px)

    assert style_override.swell_px == swell_px


@pytest.mark.parametrize(
    "field_name",
    ["corner_radius_px", "border_thickness_px", "halo_thickness_px"],
)
def test_style_negative_radius_or_thicknesses_raise(field_name):
    with pytest.raises(ValueError):
        replace(ANY_STYLE, **{field_name: -5})


def test_style_override_negative_halo_thickness_raises():
    with pytest.raises(ValueError):
        StyleOverride(halo_thickness_px=-5)


@pytest.mark.parametrize(
    "field_name",
    ["corner_radius_px", "border_thickness_px", "halo_thickness_px"],
)
def test_style_radius_or_thicknesses_can_be_zero(field_name):
    style = replace(ANY_STYLE, **{field_name: 0})

    assert getattr(style, field_name) == 0


def test_style_override_halo_thickness_can_be_zero():
    style_override = StyleOverride(halo_thickness_px=0)

    assert style_override.halo_thickness_px == 0


@pytest.mark.parametrize("text_font_size", [0, -5])
def test_style_non_positive_font_size_raises(text_font_size):
    with pytest.raises(ValueError):
        replace(ANY_STYLE, text_font_size=text_font_size)


@pytest.mark.parametrize("field_name", ["text_margin", "text_offset"])
@pytest.mark.parametrize(
    "value",
    [1, 3.5, [2, 3], pg.Vector2(4, 5)],
    ids=["int", "float", "list", "pg Vector2"],
)
def test_style_non_tuple_margin_or_offset_raises(field_name, value):
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
def test_style_margin_or_offset_can_take_tuple_of_int(field_name, value):
    style = replace(ANY_STYLE, **{field_name: value})

    assert getattr(style, field_name) == value


@pytest.mark.parametrize(
    "value",
    [1, 3.5, [2, 3], pg.Vector2(4, 5)],
    ids=["int", "float", "list", "pg Vector2"],
)
def test_style_override_non_tuple_offset_raises(value):
    with pytest.raises(TypeError):
        StyleOverride(text_offset=value)


@pytest.mark.parametrize(
    "value",
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
def test_style_override_text_offset_can_take_tuple_of_int_or_None(value):
    style_override = StyleOverride(text_offset=value)

    assert style_override.text_offset == value


def test_style_str_text_typeface_raises():
    with pytest.raises(TypeError):
        replace(ANY_STYLE, text_typeface=ANY_STRING)


@pytest.mark.parametrize(
    "value",
    [
        *BundledTypeface,
        pytest.param(ANY_PATH, id="Path"),
    ],
)
def test_style_text_typeface_can_take_bundled_font_or_path(value):
    style = replace(ANY_STYLE, text_typeface=value)

    assert style.text_typeface == value


# endregion


# region --- Structure --------------------------------------------------------


def test_style_override_fields_are_subset_of_style():
    style_field_names = {field.name for field in fields(Style)}
    style_override_field_names = {field.name for field in fields(StyleOverride)}

    assert style_override_field_names - style_field_names == set()


# endregion
