from typing import Union, Iterable

import pandas as pd
import numpy as np


TRUE = frozenset(('true', 't', 'yes', 'y'))
FALSE = frozenset(('false', 'f', 'no', 'n'))
BOOL = frozenset().union(TRUE, FALSE)
NA = frozenset((
    'na', 'NA', 'NaN',
    'none', 'None', None,
    pd.NA, pd.NaT, np.NAN, np.nan
))
INT = ('int64', 'uint64')
ALL = INT + ('float64', 'string')


def auto_dtype(
    data: Union[pd.DataFrame, pd.Series, Iterable],
    convert: bool = True,
    categories: bool = True,
    **kwargs,
) -> Union[pd.DataFrame, pd.Series, str, dict]:
    """
    Automatically guesses and optionally converts data types of a dataframe,
    series or other iterable.

    Parameters
    ----------
    data
        A dataframe or an array like object such as :class:`pandas.Series`,
        :class:`numpy.ndarray` or list.
    convert
        Convert the data types to the best fitting types.
    categories
        Use the `category` data type for string variables with a small
        number of values compared to their size.
    **kwargs
        For dataframes, manually set the desired data type of certain
        variables.

    Returns
    -------
    :class:`pandas.DataFrame` or :class:`pandas.Series` or str or list
        If :arg:`convert` is `True`: a dataframe or series with its data
        type(s) converted.
        If :arg:`convert` is `False`: Name of a data type for a single Series
        or iterable, or a dict of data type names by column labels for a
        dataframe.
    """

    method = (
        _auto_dtype_df
            if isinstance(data, pd.DataFrame) else
        _auto_dtype_series
    )

    return method(data, convert = convert, categories = categories, **kwargs)


def _auto_dtype_df(
    data: pd.DataFrame,
    convert: bool = True,
    categories: bool = True,
    **kwargs,
) -> Union[pd.DataFrame, dict]:

    def process_col(col):

        if col in kwargs:

            return (
                data[col].astype(kwargs[col])
                    if convert else
                kwargs[col]
            )

        else:

            return _auto_dtype_series(
                data[col],
                convert = convert,
                categories = categories,
            )


    result = dict(
        (
            col,
            process_col(col)
        )
        for col in data
    )

    return pd.DataFrame(result, index = data.index) if convert else result


def _auto_dtype_series(
    data: pd.Series,
    convert: bool = True,
    categories: bool = True,
    **kwargs,
) -> Union[pd.Series, str]:

    data = pd.Series(data)

    for t in ALL:

        try:

            converted = data.astype(t)

            if t in INT:

                if _has_na(converted):

                    continue

                elif sorted(converted.unique()) == [0, 1]:

                    t = 'bool'
                    converted = converted.astype(t)

            elif t == 'string':

                if not _has_na(converted) and _string_is_bool(converted):

                    t = 'bool'
                    converted = _string_to_bool(converted)

                if converted.nunique() < len(converted) / 4:

                    t = 'category'
                    converted = converted.astype(t)

            return converted if convert else t

        except (OverflowError, ValueError):

            continue

    return data if convert else data.dtype


def _has_na(data: Union[pd.Series, Iterable]) -> bool:
    """
    Checks if any item in the series looks like NA or NaN.
    """

    return any(i in NA for i in data)


def _string_is_bool(data: Union[pd.Series, Iterable]) -> bool:
    """
    Tells if a string or object type series contains only values that we
    recognize as boolean values.
    """

    return pd.Series(s.lower() for s in data).isin(BOOL).all()


def _string_to_bool(data: Union[pd.Series, Iterable]) -> pd.Series:
    """
    Converts a series or iterable to bool type if all elements can be
    recognized as a boolean value.
    """

    if _string_is_bool(data):

        return pd.Series(i.lower() in TRUE for i in data)

    return pd.Series(data)

__all__ = [auto_dtype]
