from puigame.core.state import State

# region --- State values -----------------------------------------------------


def test_base_value_has_no_bits_set():
    assert State.BASE.value == 0b0


# endregion
