from puigame.core.state import State


def test_base_value_has_no_bits_set():
    assert State.BASE.value == 0b0
