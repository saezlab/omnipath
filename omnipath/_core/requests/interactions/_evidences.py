from typing import List, Tuple, Union, Callable, Iterable, Optional

import pandas as pd

from omnipath._misc.utils import to_set
from omnipath._core.requests._utils import (
    _count_resources,
    _count_references,
    _strip_resource_label_df,
)

EVIDENCES_KEYS = ("positive", "negative", "directed", "undirected")


def _must_have_evidences(df: pd.DataFrame) -> None:
    """Raise an error if the input data frame does not contain evidences."""
    if "evidences" not in df.columns:
        raise ValueError("The input data frame must contain `evidences` column.")


def unnest_evidences(df: pd.DataFrame, col: str = "evidences") -> pd.DataFrame:
    """
    Create new columns of evidences by direction and effect sign.

    Plucks evidence lists of each direction and effect sign into separate,
    new columns. This will yield four new columns: "positive", "negative",
    "directed" and "undirected", each containing lists of dicts of evidences.

    Parameters
    ----------
    df
        An OmniPath interaction data frame with "evidences" column.
    col
        Name of the column containing the nested evidences.

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
    for key in ("positive", "negative", "directed", "undirected"):
        df[key] = df[col].apply(lambda x: x[key])  # noqa: B023

    return df


def filter_evidences(
    df: pd.DataFrame,
    datasets: Optional[Union[str, Iterable[str]]] = None,
    resources: Optional[Union[str, Iterable[str]]] = None,
    col: str = "evidences",
    target_col: Optional[str] = None,
) -> pd.DataFrame:
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
                ev
                for ev in evs
                if (
                    (not datasets or ev["dataset"] in datasets)
                    and (not resources or ev["resource"] in resources)
                )
            ]

        else:
            return evs

    df[target_col] = df[col].apply(the_filter)

    return df


def from_evidences(
    df: pd.DataFrame,
    col: str = "evidences",
) -> pd.DataFrame:
    """
    Recreate interaction records from an evidences column.

    Parameters
    ----------
    df
        An OmniPath interaction data frame.
    col:
        Name of the column containing the evidences.

    Returns
    -------
    :class:`pandas.DataFrame`
        The input data frame with its standard columns reconstructed based
        on the evidences in `col`. The records with no evidences from the
        specified datasets and resources will be removed.
    """
    evs_df = pd.DataFrame({"evidences": df[col]})
    evs_df = unnest_evidences(evs_df)
    evs_df["ce_positive"] = _curation_effort_from(evs_df, columns="positive")
    evs_df["ce_negative"] = _curation_effort_from(evs_df, columns="negative")
    evs_df["ce_directed"] = _curation_effort_from(evs_df, columns="directed")

    df["is_directed"] = evs_df["directed"].apply(bool)
    df["is_stimulation"] = evs_df["positive"].apply(bool)
    df["is_inhibition"] = evs_df["negative"].apply(bool)
    df["curation_effort"] = _curation_effort_from(evs_df)
    df["sources"] = _resources_from(evs_df)
    df["references"] = _references_from(evs_df)
    df["consensus_stimulation"] = evs_df["ce_positive"] >= evs_df["ce_negative"]
    df["consensus_inhibition"] = evs_df["ce_positive"] <= evs_df["ce_negative"]

    # recompile the consensus_direction
    opposite_direction = pd.DataFrame(
        {
            "source": df["source"],
            "target": df["target"],
            "ce_directed_opp": evs_df["ce_directed"],
        }
    )
    df["ce_directed"] = evs_df["ce_directed"]
    df = df.merge(
        opposite_direction,
        on=["source", "target"],
        how="left",
        sort=False,
    )
    df["consensus_direction"] = (
        pd.isnull(df["ce_directed_opp"]) | df["ce_directed"] >= df["ce_directed_opp"]
    )
    df.drop(columns=["ce_directed", "ce_directed_opp"], inplace=True)

    _count_resources(df)
    _count_references(df)
    _strip_resource_label_df(df, col="references")

    # drop records which remained without evidences
    df = df[df.sources.apply(bool)]

    return df


def _ensure_unnested(
    df: pd.DataFrame,
    columns: Union[str, Iterable[str]] = EVIDENCES_KEYS,
) -> Tuple[pd.DataFrame, Tuple[str]]:
    """
    Unnest a nested evidences column in a single column data frame.

    Used only in some specific contexts within this module, all are helper
    functions of `from_evidences`.

    Returns
    -------
        A tuple of the input data frame and a tuple of column names. If the
        data frame does not consist of a single nested evidences columns it
        will be still subsetted to the specified columns.
    """
    columns = list(to_set(columns))
    evs_df = df[columns]

    if (
        evs_df.shape[1] == 1
        and isinstance(evs_df.iloc[0, 0], dict)
        and not set(EVIDENCES_KEYS) - set(evs_df.iloc[0, 0].keys())
    ):
        evs_df = unnest_evidences(evs_df, col=evs_df.columns[0])
        columns = EVIDENCES_KEYS

    evs_df = evs_df[columns]

    return evs_df, columns


def _from(
    df: pd.DataFrame,
    func: Callable,
    columns: Union[str, Iterable[str]] = EVIDENCES_KEYS,
) -> List[Union[int, str]]:
    """Compile a new column by applying a function on evidences."""
    evs_df, columns = _ensure_unnested(df, columns)

    return [
        func(ev for evs in rec for ev in evs)
        for rec in evs_df[columns].itertuples(index=False)
    ]


def _curation_effort_from(
    df: pd.DataFrame,
    columns: Union[str, Iterable[str]] = EVIDENCES_KEYS,
) -> List[int]:
    """Curation effort from one or more evidences columns."""
    return _from(
        df=df,
        func=lambda evs: sum(len(ev["references"]) + 1 for ev in evs),
        columns=columns,
    )


def _resources_from(
    df: pd.DataFrame,
    columns: Union[str, Iterable[str]] = EVIDENCES_KEYS,
) -> List[str]:
    """Resources from one or more evidences columns."""

    def extract_resources(evs: tuple) -> str:
        return ";".join(
            sorted(
                {
                    f"{ev['resource']}{'_' if ev['via'] else ''}{ev['via'] or ''}"
                    for ev in evs
                }
            )
        )

    return _from(df=df, func=extract_resources, columns=columns)


def _references_from(
    df: pd.DataFrame,
    columns: Union[str, Iterable[str]] = EVIDENCES_KEYS,
    prefix: bool = True,
) -> List[str]:
    """Get references from one or more evidences columns."""

    def extract_references(evs: tuple) -> str:
        return ";".join(
            sorted(
                {
                    f"{ev['resource'] + ':' if prefix else ''}{ref}"
                    for ev in evs
                    for ref in ev["references"]
                }
            )
        )

    return _from(df=df, func=extract_references, columns=columns)


def only_from(
    df: pd.DataFrame,
    datasets: Optional[Union[str, Iterable[str]]] = None,
    resources: Optional[Union[str, Iterable[str]]] = None,
):
    """
    Restrict interactions to the specified datasets and resources.

    The OmniPath interactions database fully integrates all attributes from all
    resources for each interaction. This comes with the advantage that
    interaction data frames are ready for use in most of the applications;
    however, it makes it impossible to know which of the resources and
    references support the direction or effect sign of the interaction. This
    information can be recovered from the "evidences" column. The "evidences"
    column preserves all the details about interaction provenances. In cases
    when you want to use a faithful copy of a certain resource or dataset, this
    function will help you do so. Still, in most of the applications the best
    is to use the interaction data as it is returned by the web service.

    Parameters
    ----------
    df
        An OmniPath interaction data frame with "evidences" column.
    datasets
        A list of dataset names. If None, all datasets will be included.
    resources
        A list of resource names. If None, all resources will be included.

    Returns
    -------
        The input data frame with the standard columns reconstructed from the
        evidences supported by the datasets and resources provided. The
        records with no evidences from the specified datasets or resources
        will be removed.
    """
    tmp_col = "evidences_filtered_tmp"

    _must_have_evidences(df)

    df = filter_evidences(df, datasets, resources, target_col=tmp_col)
    df = from_evidences(df, tmp_col)
    df = df.drop(columns=tmp_col)

    return df
