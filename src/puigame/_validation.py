"""Checks on values that callers pass in: ints, enums, pairs, and sizes.

Each ``validate_...()`` function checks one kind of value completely and is
what other modules call. The ``_is_...()`` and ``_reject_...()`` helpers are
the single checks they are built from.
"""

from collections.abc import Sized
from enum import Enum

from pygame.typing import Point

from puigame._layout.fit_size import FitSize


def _is_int(value: object) -> bool:
    """Return whether a value is an ``int`` but not a ``bool``.

    ``bool`` is a subclass of ``int``, so ``isinstance()`` alone accepts it.

    Args:
        value: The value to check.

    Returns:
        ``True`` if ``value`` is an ``int`` and not a ``bool``.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    """Return whether a value is an ``int`` or ``float`` but not a ``bool``.

    ``bool`` is a subclass of ``int``, so ``pg.Rect``, ``pg.Vector2``, and
    Pyright all accept it as a number without complaint.

    Args:
        value: The value to check.

    Returns:
        ``True`` if ``value`` is an ``int`` or ``float`` and not a ``bool``.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_tuple(value: object) -> bool:
    """Return whether a value is a ``tuple``.

    Args:
        value: The value to check.

    Returns:
        ``True`` if ``value`` is a ``tuple``.
    """
    return isinstance(value, tuple)


def _is_pair(value: object) -> bool:
    """Return whether a value is an indexable sequence of length 2.

    This matches pygame's ``SequenceLike``, which needs ``__len__`` and
    ``__getitem__``, so a ``tuple``, a ``list``, and a ``pg.Vector2`` pass
    but a ``set`` fails. ``Sized`` is checked first, so ``len()`` never
    raises.

    Args:
        value: The value to check.

    Returns:
        ``True`` if ``value`` has a length of 2 and can be indexed.
    """
    return (
        isinstance(value, Sized) and len(value) == 2 and hasattr(value, "__getitem__")
    )


def _is_enum(value: object, enum_class: type[Enum]) -> bool:
    """Return whether a value is a member of an enum.

    Args:
        value: The value to check.
        enum_class: The enum that ``value`` should be a member of.

    Returns:
        ``True`` if ``value`` is a member of ``enum_class``.
    """
    return isinstance(value, enum_class)


def _reject_non_tuple(field_name: str, pair: Point) -> None:
    """Reject a value that is not a ``tuple``.

    Run this before the pair checks, so that a ``list`` or ``pg.Vector2`` is
    refused for not being a ``tuple`` rather than accepted as a pair.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is not a ``tuple``.
    """
    if not _is_tuple(pair):
        raise TypeError(f"{field_name} must be tuple, got {pair!r}")


def _reject_non_pair(field_name: str, pair: FitSize) -> None:
    """Reject a value that is not an ``(x, y)`` pair.

    Run this before the item checks, which index the value.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is not an indexable sequence of length 2, such
            as ``None``, a single number, a ``set``, or a sequence of the
            wrong length.
    """
    if not _is_pair(pair):
        raise TypeError(f"{field_name} must be a sequence of length 2, got {pair!r}")


def _reject_non_number_in_pair(field_name: str, pair: FitSize) -> None:
    """Reject an ``(x, y)`` pair with an item that is not a number.

    A ``bool`` is not a number here. Pyright rejects ``None`` in a ``Point``,
    but code without a type checker can still pass one.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The ``(x, y)`` pair to check.

    Raises:
        TypeError: If either item of ``pair`` is not an ``int`` or ``float``,
            or is a ``bool``.
    """
    if any(not _is_number(item) for item in pair):
        raise TypeError(f"{field_name} items must be numbers, got {pair!r}")


def _reject_non_number_in_fit_size(field_name: str, pair: FitSize) -> None:
    """Reject a fit size with an item that is neither a number nor ``None``.

    A ``bool`` is not a number here. Only a fit size may contain ``None``.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The ``(x, y)`` pair to check.

    Raises:
        TypeError: If either item of ``pair`` is neither ``None`` nor an
            ``int`` or ``float``, or is a ``bool``.
    """
    if any(item is not None and not _is_number(item) for item in pair):
        raise TypeError(f"{field_name} items must be numbers or None, got {pair!r}")


def _reject_negative_in_pair(field_name: str, pair: FitSize) -> None:
    """Reject an ``(x, y)`` size that contains a negative number.

    ``None`` items are skipped, since they fit that axis to the content.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The ``(x, y)`` size to check.

    Raises:
        ValueError: If either item of ``pair`` is a negative number.
    """
    if any(item is not None and item < 0 for item in pair):
        raise ValueError(f"{field_name} items cannot be negative, got {pair!r} px")


def validate_int(field_name: str, value: object) -> None:
    """Check that a value is an ``int``.

    A ``bool`` is not an ``int`` here, although it is a subclass of one.

    Args:
        field_name: Name of the parameter or field, used in the message.
        value: The value to check.

    Raises:
        TypeError: If ``value`` is not an ``int``, or is a ``bool``.
    """
    if not _is_int(value):
        raise TypeError(f"{field_name} must be int, got {value!r}")


def validate_tuple(field_name: str, pair: Point) -> None:
    """Check that a value is an ``(x, y)`` ``tuple`` of numbers.

    For fields of frozen objects, such as a ``Style``, where a ``list`` or
    ``pg.Vector2`` could be changed after the object was made.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is not a ``tuple`` of length 2, or if either of
            its items is not an ``int`` or ``float``, or is a ``bool``.
    """
    _reject_non_tuple(field_name, pair)
    _reject_non_pair(field_name, pair)
    _reject_non_number_in_pair(field_name, pair)


def validate_pair(field_name: str, pair: Point) -> None:
    """Check that a value is an ``(x, y)`` pair of numbers.

    Args:
        field_name: Name of the parameter or field, used in the message.
        pair: The value to check.

    Raises:
        TypeError: If ``pair`` is not an indexable sequence of length 2, or if
            either of its items is not an ``int`` or ``float``, or is a
            ``bool``.
    """
    _reject_non_pair(field_name, pair)
    _reject_non_number_in_pair(field_name, pair)


def validate_size(field_name: str, size: Point) -> None:
    """Check that a value is a size: an ``(x, y)`` pair of non-negative numbers.

    Args:
        field_name: Name of the parameter or field, used in the message.
        size: The value to check.

    Raises:
        TypeError: If ``size`` is not an indexable sequence of length 2, or if
            either of its items is not an ``int`` or ``float``, or is a
            ``bool``.
        ValueError: If either of its items is negative.
    """
    _reject_non_pair(field_name, size)
    _reject_non_number_in_pair(field_name, size)
    _reject_negative_in_pair(field_name, size)


def validate_fit_size(field_name: str, fit_size: FitSize) -> None:
    """Check that a value is a fit size: an ``(x, y)`` pair of sizes.

    Each item is a number, or ``None``, which means that axis fits the
    widget's content.

    Args:
        field_name: Name of the parameter or field, used in the message.
        fit_size: The value to check.

    Raises:
        TypeError: If ``fit_size`` is not an indexable sequence of length 2,
            or if either of its items is neither ``None`` nor an ``int`` or
            ``float``, or is a ``bool``.
        ValueError: If either of its items is negative.
    """
    _reject_non_pair(field_name, fit_size)
    _reject_non_number_in_fit_size(field_name, fit_size)
    _reject_negative_in_pair(field_name, fit_size)


def validate_enum(
    field_name: str,
    value: object,
    expected_enum: type[Enum],
    *,
    allow_none: bool = False,
) -> None:
    """Check that a value is a member of an enum.

    Args:
        field_name: Name of the parameter or field, used in the message.
        value: The value to check.
        expected_enum: The enum that ``value`` should be a member of.
        allow_none: Whether ``None`` is also accepted. Defaults to ``False``.

    Raises:
        TypeError: If ``value`` is not a member of ``expected_enum``, and is
            not ``None`` when ``allow_none`` is ``True``.
    """
    if allow_none and value is None:
        return

    if allow_none:
        valid_types = f"{expected_enum.__name__} or None"
    else:
        valid_types = expected_enum.__name__

    if not _is_enum(value, expected_enum):
        raise TypeError(f"{field_name} must be {valid_types}, got {value!r}")
