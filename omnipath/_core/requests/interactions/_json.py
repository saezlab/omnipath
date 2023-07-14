import json

import pandas as pd


def convert_json_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Convert a column of JSON encoded strings to nested Python objects.

    Parameters
    ----------
    df
        An OmniPath interaction data frame.
    col
        Name of a column with JSON encoded strings.

    Returns
    -------
    :class:`pandas.DataFrame`
        The input data frame with the column converted to nested Python
        objects, i.e. lists or dicts. If the column does not exist, the
        data frame is returned unmodified.
    """
    if col in df.columns:
        df[col] = df[col].apply(json.loads)

    return df


def _json_cols_hook(df: pd.DataFrame) -> pd.DataFrame:
    """Handle the JSON columns in post-processing, if there is any."""
    for col in ("extra_attrs", "evidences"):
        df = convert_json_col(df, col)

    return df
