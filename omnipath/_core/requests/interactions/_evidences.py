from typing import Iterable, Optional, Union

import pandas as pd

from omnipath._misc.utils import to_set


def _must_have_evidences(df: pd.DataFrame) -> None:
    """
    Raises an error if the input data frame does not contain evidences.
    """

    if "evidences" not in df.columns:

        raise ValueError(
            "The input data frame must contain `evidences` column."
        )


def unnest_evidences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create new columns of evidences by direction and effect sign.

    Plucks evidence lists of each direction and effect sign into separate,
    new columns. This will yield four new columns: "positive", "negative",
    "directed" and "undirected", each containing lists of dicts of evidences.

    Parameters
    ----------
    df
        An OmniPath interaction data frame with "evidences" column.

    Returns
    -------
    :class:`pandas.DataFrame`
        The input data frame with new columns "positive", "negative",
        "directed" and "undirected" each containing lists of dicts of
        evidences.

    Raises
    ------
    ValueError
        If the input data frame does not contain "evidences" column.
    """

    _must_have_evidences(df)

    for key in ("positive", "negative", "directed", "undirected"):

        df[key] = df["evidences"].apply(lambda x: x[key])

    return df


def filter_evidences(
        df: pd.DataFrame,
        datasets: Optional[Union[str, Iterable[str]]] = None,
        resources: Optional[Union[str, Iterable[str]]] = None,
        col: str = "evidences",
        target_col: Optional[str] = None,
    ):
    """
    Filter evidences by dataset and resource.

    Parameters
    ----------
    df
        An OmniPath interaction data frame with "evidences" column.
    datasets
        A list of dataset names. If None, all datasets will be included.
    resources
        A list of resource names. If None, all resources will be included.
    col
        Name of the column containing the evidences.
    target_col
        Column to output the filtered evidences to. By default `col` is
        to be overwritten.

    Returns
    -------
    :class:`pandas.DataFrame`
        The input data frame with the evidences filtered, with a new column
        depending on the `target_col` parameter.
    """

    target_col = target_col or col
    datasets = to_set(datasets)
    resources = to_set(resources)

    def the_filter(evs):

        if isinstance(evs, dict):

            return {k: the_filter(v) for k, v in evs.items()}

        elif isinstance(evs, list):

            return [
                ev for ev in evs
                if (
                    (not datasets or ev["dataset"] in datasets) and
                    (not resources or ev["resource"] in resources)
                )
            ]

        else:

            return evs


    df[target_col] = df[col].apply(the_filter)

    return df
