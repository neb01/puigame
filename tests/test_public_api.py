import pytest

import puigame

# region --- Constants --------------------------------------------------------

PUBLIC_NAMES = [
    "DEFAULT_DT",
    "DEFAULT_THEME",
    "UI",
    "Anchor",
    "BundledTypeface",
    "Button",
    "Container",
    "DrawnSkin",
    "FadeProfile",
    "Label",
    "NoSkin",
    "Panel",
    "State",
    "Style",
    "StyleOverride",
    "Theme",
    "Widget",
]

# endregion


# region --- Public names -----------------------------------------------------


def test_all_lists_exactly_public_names():
    assert set(puigame.__all__) == set(PUBLIC_NAMES)


def test_no_duplicates_in_puigame_all():
    assert len(puigame.__all__) == len(set(puigame.__all__))


@pytest.mark.parametrize("attribute_name", PUBLIC_NAMES)
def test_public_name_is_importable(attribute_name):
    assert hasattr(puigame, attribute_name)


# endregion
