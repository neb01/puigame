"""Checks on ``(x, y)`` pairs and fit sizes that callers pass in."""

from collections.abc import Sized

from pygame.typing import Point

from puigame._layout.fit_size import FitSize


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


def reject_non_pair(field_name: str, pair: FitSize) -> None:
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


def reject_non_number_in_pair(field_name: str, pair: FitSize) -> None:
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


def reject_non_number_in_fit_size(field_name: str, pair: FitSize) -> None:
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
        raise ValueError(f"{field_name} items cannot be negative, got {pair!r} px")


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
    reject_non_pair(field_name, pair)
    reject_non_number_in_pair(field_name, pair)


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
    reject_non_pair(field_name, fit_size)
    reject_non_number_in_fit_size(field_name, fit_size)
    reject_negative_in_pair(field_name, fit_size)
