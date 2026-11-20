"""Checks on ``(x, y)`` pairs and fit sizes that callers pass in."""

from pygame.typing import Point

from puigame._layout.fit_size import FitSize


def reject_single_value(field_name: str, pair: FitSize) -> None:
    """Reject a single value given where an ``(x, y)`` pair is expected.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is ``None`` or a single ``int`` or ``float``,
            including a ``bool``.
    """
    if pair is None or isinstance(pair, (int, float)):
        raise TypeError(f"{field_name} cannot be a single value, got {pair!r}")


def reject_bool_in_pair(field_name: str, pair: FitSize) -> None:
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


def reject_none_in_pair(field_name: str, pair: FitSize) -> None:
    """Reject an ``(x, y)`` pair that contains ``None``.

    Only a fit size may contain ``None``. Pyright rejects ``None`` in a
    ``Point``, but code without a type checker can still pass one.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The ``(x, y)`` pair to check.

    Raises:
        TypeError: If either item of ``pair`` is ``None``.
    """
    if pair[0] is None or pair[1] is None:
        raise TypeError(f"{field_name} cannot contain None, got {pair!r}")


def reject_negative_in_pair(field_name: str, pair: FitSize) -> None:
    """Reject an ``(x, y)`` size that contains a negative number.

    ``None`` items are skipped, since they fit that axis to the content.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The ``(x, y)`` size to check.

    Raises:
        ValueError: If either item of ``pair`` is a negative number.
    """
    if any(item is not None and item < 0 for item in pair):
        raise ValueError(f"{field_name} cannot be negative, got {pair!r} px")


def validate_fit_size(field_name: str, fit_size: FitSize) -> None:
    """Check that a value is an ``(x, y)`` pair whose items may be ``None``.

    ``None`` is allowed in either item, and means that axis fits the
    widget's content. The single-value check runs first, since indexing a
    single number or ``None`` would raise Python's own ``TypeError`` before
    the item checks could.

    Args:
        field_name: Name of the parameter or field, used in the message.
        fit_size: The value to check.

    Raises:
        TypeError: If ``fit_size`` is ``None`` or a single number, or if
            either of its items is a ``bool``.
        ValueError: If either of its items is negative.
    """
    reject_single_value(field_name, fit_size)
    reject_bool_in_pair(field_name, fit_size)
    reject_negative_in_pair(field_name, fit_size)


def validate_pair(field_name: str, pair: Point) -> None:
    """Check that a value is an ``(x, y)`` pair of numbers, none a ``bool``.

    The single-value check runs first, since indexing a single number or
    ``None`` would raise Python's own ``TypeError`` before the item checks
    could.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is ``None`` or a single number, or if either of
            its items is a ``bool`` or ``None``.
    """
    reject_single_value(field_name, pair)
    reject_bool_in_pair(field_name, pair)
    reject_none_in_pair(field_name, pair)
