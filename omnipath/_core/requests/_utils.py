from types import MethodType
from typing import *  # noqa: F401 F403 (because of the argspec factory)
from typing import Any, Dict, Union, Callable, Iterable, Optional
from inspect import Parameter, unwrap, isabstract
import inspect

import wrapt
import typing_extensions  # noqa: F401

import pandas as pd

from omnipath._core.utils._docs import d


@d.get_full_description(base="get")
@d.get_sections(base="get", sections=["Parameters", "Returns"])
def _get_helper(cls: type, **kwargs) -> pd.DataFrame:
    """
    Perform a request to the [OmniPath]_ web service.

    Parameters
    ----------
    kwargs
        Additional query parameters.

    Returns
    -------
    :class:`pandas.DataFrame`
        The result which depends the type of the request and the supplied parameters.
    """
    return cls()._get(**kwargs)


def _inject_api_method(
    clazz: type,
) -> None:
    """
    Create a decorator which does nothing except for modifying the function signature in the docstring.

    The function to be decorated must be a class method and is allowed only to have positional arguments,
    and variable keyword arguments (**kwargs).

    The resulting decorated function will containing only the positional arguments (including original type annotations)
    and possibly keyword only arguments. In this example signature might def fn(foo, bar, *, baz, quux),
    `baz` and `quux` are the keyword only arguments.

    Parameters
    ----------
    clazz
        The class for which to create the query. Must not be abstract.

    Returns
    -------
    :class:`callable`
        The decorator as described above.
    """

    def argspec_factory(orig_fn: Callable) -> Callable:
        orig_params = inspect.signature(orig_fn).parameters
        # maintain the original signature if the subclass has overriden the method
        # this will lose the docstring of the original function
        parameters = {
            k: v
            for k, v in orig_params.items()
            if k != "cls"
            and v.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        }
        annotations = {
            k: v for k, v in clazz._annotations().items() if k not in parameters
        }

        sig = inspect.signature(lambda _: _)
        sig = sig.replace(
            parameters=[Parameter("cls", kind=Parameter.POSITIONAL_ONLY)]
            + list(parameters.values())
            + [
                Parameter(k, kind=Parameter.KEYWORD_ONLY, annotation=a)
                for k, a in sorted(annotations.items())
            ]
            + [Parameter("kwargs", kind=Parameter.VAR_KEYWORD)]
        )
        # modify locals() for argspec factory
        import omnipath  # noqa: F401

        NoneType, pandas = type(None), pd

        exec(
            f"def adapter{sig}: pass".replace(" /,", ""),
            globals(),
            locals(),
        )
        return locals()["adapter"]

    if not isinstance(clazz, type):
        raise TypeError(
            f"Expected `clazz` to be a type, found `{type(clazz).__name__}`."
        )

    if isabstract(clazz):
        return

    @wrapt.decorator(adapter=wrapt.adapter_factory(argspec_factory))
    def wrapper(wrapped, _instance, args, kwargs):
        return wrapped(*args, **kwargs)

    if hasattr(clazz, "get") and not hasattr(clazz.get, "__wrapped__"):
        # overriding in subclass
        clazz.get = wrapper(unwrap(clazz.get))
        return

    clazz.get = wrapper(MethodType(_get_helper, clazz))


def _inject_params(
    params: Dict[str, Any], key: str, value: Optional[Union[str, Iterable[str]]]
) -> None:
    if value is None:
        return
    value = {value} if isinstance(value, str) else set(value)

    old_value = params.pop(key, None)
    if old_value is None:
        params[key] = value
        return

    old_value = {old_value} if isinstance(old_value, str) else set(old_value)

    params[key] = value | old_value


def _split_unique_join(data: pd.Series, func: Optional[Callable] = None) -> pd.Series:
    mask = ~pd.isnull(data.astype("string"))
    data = data[mask]
    data = data.str.split(";")

    if func is None:
        data = data.apply(
            lambda row: ";".join(sorted(set(map(str, row))))
            if isinstance(row, Iterable)
            else row
        )
    else:
        data = data.apply(func)

    res = pd.Series([None] * len(mask))
    res.loc[mask] = data

    return res


def _strip_resource_label(
    data: pd.Series, func: Optional[Callable] = None
) -> pd.Series:
    return _split_unique_join(
        _split_unique_join(data.str.replace(r"[-\w]*:?(\d+)", r"\1")), func=func
    )
