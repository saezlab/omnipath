from typing import Any, Set, Iterable


def to_set(value: Any) -> Set:
    """Make sure `value` is a set, convert it if necessary.

    Parameters
    ----------
    value
        Any kind of object.

    Returns
    -------
    `Set`
        The `value` itself if it's already a set; a set of single element
        if `value` is a simple type; a set of the elements in `value`
        if `value` is iterable; empty set if `value` is None.

    Raises
    ------
    TypeError
        If `value` is not an iterable and not hashable, or if it's an iterable
        containing non hashable elements.
    """
    if isinstance(value, Set):
        return value

    elif value is None:
        return set()

    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return set(value)

    else:
        return {value}
