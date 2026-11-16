"""Checks on ``(x, y)`` pairs that callers pass in."""

from pygame.typing import Point


def reject_bool_in_pair(field_name: str, pair: Point) -> None:
    """Reject an ``(x, y)`` pair that contains a ``bool``.

    ``bool`` is a subclass of ``int``, so ``pg.Rect``, ``pg.Vector2``, and
    Pyright all accept it in a pair without complaint.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The ``(x, y)`` pair to check.

    Raises:
        TypeError: If either item of ``pair`` is a ``bool``.
    """
    if isinstance(pair[0], bool) or isinstance(pair[1], bool):
        raise TypeError(f"{field_name} cannot contain a bool, got {pair!r}")


def reject_single_value(field_name: str, pair: Point) -> None:
    """Reject a single number given where an ``(x, y)`` pair is expected.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is a single ``int`` or ``float``, including a
            ``bool``.
    """
    if isinstance(pair, (int, float)):
        raise TypeError(f"{field_name} cannot be a single value, got {pair!r}")


def validate_pair(field_name: str, pair: Point) -> None:
    """Check that a value is an ``(x, y)`` pair with no ``bool`` items.

    The single-value check runs first, since indexing a single number would
    raise Python's own ``TypeError`` before the ``bool`` check could.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is a single number, or if either of its items
            is a ``bool``.
    """
    reject_single_value(field_name, pair)
    reject_bool_in_pair(field_name, pair)
