import pandas as pd


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

    if "evidences" not in df.columns:

        raise ValueError(
            "The input data frame must contain `evidences` column."
        )

    for key in ("positive", "negative", "directed", "undirected"):

        df[key] = df["evidences"].apply(lambda x: x[key])

    return df
