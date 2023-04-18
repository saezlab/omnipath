from typing import Union, Iterable

import numpy as np
import pandas as pd

__all__ = ["auto_dtype"]

TRUE = frozenset(("true", "t", "yes", "y"))
FALSE = frozenset(("false", "f", "no", "n"))
BOOL = frozenset().union(TRUE, FALSE)
NA = frozenset(("na", "NA", "NaN", "none", "None", None, pd.NA, pd.NaT, np.NAN, np.nan))
INT = frozenset(
    ("int64", "uint64", "int32", "uint32", "int16", "uint16", "int8", "uint8")
)
FLT = frozenset(("float64", "float32", "float128"))
NUM = INT | FLT
ALL = ("int64", "uint64", "float64", "string")


def auto_dtype(
    data: Union[pd.DataFrame, pd.Series, Iterable],
    categories: bool = True,
    **kwargs,
) -> Union[pd.DataFrame, pd.Series]:
    """
    Convert to the best dtype

    Guess automatically and convert data types of a dataframe, series or other
    iterable.

    Parameters
    ----------
    data
        A dataframe or an array like object such as :class:`pandas.Series`,
        :class:`numpy.ndarray` or list.
    categories
        Use the `category` data type for string variables with a small
        number of values compared to their size.
    kwargs
        For dataframes, manually set the desired data type of certain
        variables.

    Returns
    -------
    :class:`pandas.DataFrame` or :class:`pandas.Series` or str or list
        A dataframe or series with its data type(s) converted.
    """
    method = _auto_dtype_df if isinstance(data, pd.DataFrame) else _auto_dtype_series

    return method(data, categories=categories, **kwargs)


def _auto_dtype_df(
    data: pd.DataFrame,
    categories: bool = True,
    **kwargs,
) -> pd.DataFrame:
    def process_col(col):
        if col in kwargs:
            return data[col].astype(kwargs[col])

        else:
            return _auto_dtype_series(
                data[col],
                categories=categories,
            )

    result = {col: process_col(col) for col in data}

    return pd.DataFrame(result, index=data.index)


def _auto_dtype_series(
    data: pd.Series,
    categories: bool = True,
    **kwargs,
) -> pd.Series:
    data = pd.Series(data)

    for t in ALL:
        if (str(data.dtype) in INT and t in FLT) or (
            t == "string" and str(data.dtype) != "object"
        ):
            continue

        try:
            converted = data.astype(t)

            if t in FLT:
                if str(data.dtype) in FLT:
                    continue

                elif str(data.dtype) not in FLT:
                    return _auto_dtype_series(converted)

            if t in INT:
                if _has_na(converted) or (
                    str(data.dtype) in FLT and (data != converted).any()
                ):
                    continue

                elif sorted(converted.unique()) == [0, 1]:
                    t = "bool"
                    converted = converted.astype(t)

                elif str(data.dtype) in INT:
                    continue

            elif t == "string":
                if not _has_na(converted) and _string_is_bool(converted):
                    t = "bool"
                    converted = _string_to_bool(converted)

                elif converted.nunique() < len(converted) / 4:
                    t = "category"
                    converted = converted.astype(t)

            return converted

        except (OverflowError, ValueError):
            continue

    return data


def _has_na(data: Union[pd.Series, Iterable]) -> bool:
    """Chec if any item in the series looks like NA or NaN."""
    return pd.Series(data).isin(NA).any()


def _string_is_bool(data: Union[pd.Series, Iterable]) -> bool:
    """
    Contains only bool-like values

    Tell if a string or object type series contains only values that we
    recognize as boolean values.
    """
    return pd.Series(s.lower() for s in data).isin(BOOL).all()


def _string_to_bool(data: Union[pd.Series, Iterable]) -> pd.Series:
    """
    Convert to bool if possible

    Convert a series or iterable to bool type if all elements can be
    recognized as a boolean value.
    """
    if _string_is_bool(data):
        return pd.Series(i.lower() in TRUE for i in data)

    return pd.Series(data)
