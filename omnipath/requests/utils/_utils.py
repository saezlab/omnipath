from typing import Any, Dict, Mapping, Optional

import pandas as pd

from omnipath.requests import Intercell
from omnipath.constants.constants import QueryParams, InteractionDataset
from omnipath.requests.interactions import OmniPath


def _to_dict(mapping: Optional[Mapping[Any, Any]]) -> Dict[Any, Any]:
    return {} if mapping is None else dict(mapping)


def _swap_undirected(df: pd.DataFrame) -> pd.DataFrame:
    if "is_directed" not in df.columns:
        raise KeyError(f"Key `'is_directed'` not found in `{list(df.columns)}`.")

    directed = df.pop("is_directed")

    undirected = df.loc[~directed, :]
    if undirected.empty:
        return df

    undirected_swapped = undirected.copy()
    undirected_swapped[["source", "target"]] = undirected[["target", "source"]]

    if "source_genesymbol" in undirected:
        undirected_swapped[["source_genesymbol", "target_genesymbol"]] = undirected[
            ["target_genesymbol", "source_genesymbol"]
        ]
    if "ncbi_tax_id_source" in undirected.columns:
        undirected_swapped[["ncbi_tax_id_source", "ncbi_tax_id_target"]] = undirected[
            ["ncbi_tax_id_targer", "ncbi_tax_id_source"]
        ]

    return pd.concat(
        [directed, undirected, undirected_swapped], axis=0, ignore_index=True
    )


def import_intercell_network(
    interactions_params: Optional[Mapping[str, Any]] = None,
    transmitter_params: Optional[Mapping[str, Any]] = None,
    receiver_params: Optional[Mapping[str, Any]] = None,
) -> pd.DataFrame:
    """
    TODO.

    Parameters
    ----------
    interactions_params
    transmitter_params
    receiver_params

    Returns
    -------
    :class:`pandas.DataFrame`
        TODO.
    """
    interactions_params = _to_dict(interactions_params)
    transmitter_params = _to_dict(transmitter_params)
    receiver_params = _to_dict(receiver_params)

    interactions_params.setdefault(
        QueryParams.DATASETS.value,
        [
            InteractionDataset.OMNIPATH.value,
            InteractionDataset.PATHWAY_EXTRA.value,
            InteractionDataset.KINASE_EXTRA.value,
            InteractionDataset.LIGREC_EXTRA.value,
        ],
    )
    transmitter_params.setdefault(QueryParams.CAUSALITY.value, "trans")
    transmitter_params.setdefault(QueryParams.SCOPE.value, "generic")
    receiver_params.setdefault(QueryParams.CAUSALITY.value, "rec")
    receiver_params.setdefault(QueryParams.SCOPE.value, "generic")

    interactions = OmniPath().get(**interactions_params)
    interactions = _swap_undirected(interactions)

    ic = Intercell()
    transmitters = ic.get(**transmitter_params)
    receivers = ic.get(**receiver_params)

    # fmt: off
    transmitters = transmitters[~transmitters["parent"].isin(["intracellular_intercellular_related", "intracellular"])]
    transmitters.rename(columns={"source": "category_source"}, inplace=True)
    # this makes it 3x as fast during groupby, since all of these are categories
    # it's mostly because groupby needs observed=True + using string object (numpy) vs "string"
    transmitters[["category", "parent", "database"]] = transmitters[["category", "parent", "database"]].astype(str)

    receivers = receivers[~receivers["parent"].isin(["intracellular_intercellular_related", "intracellular"])]
    receivers.rename(columns={"source": "category_source"}, inplace=True)
    receivers[["category", "parent", "database"]] = receivers[["category", "parent", "database"]].astype(str)

    res = pd.merge(interactions, transmitters, left_on="source", right_on="uniprot", how="inner")
    gb = res.groupby(["category", "parent", "source", "target"], as_index=False,)
    # fmt: on

    res = gb.nth(0).copy()  # much faster than 1st
    res["database"] = gb["database"].apply(";".join)["database"].astype(str)

    res = pd.merge(
        res,
        receivers,
        how="inner",
        left_on="target",
        right_on="uniprot",
        suffixes=["_intercell_source", "_intercell_target"],
    )
    gb = res.groupby(
        [
            "category_intercell_source",
            "parent_intercell_source",
            "source",
            "target",
            "category_intercell_target",
            "parent_intercell_target",
        ],
        as_index=False,
    )

    res = gb.nth(0).copy()
    res["database_intercell_target"] = (
        gb["database_intercell_target"]
        .apply(";".join)["database_intercell_target"]
        .astype(str)
    )

    # retype back as categories
    for suffix in ["_intercell_source", "_intercell_target"]:
        for col in ["category", "parent"]:
            res[f"{col}{suffix}"] = res[f"{col}{suffix}"].astype("category")

    res.reset_index(inplace=True)

    # TODO: maybe also cache this result:
    # from omnipath import options
    # options.cache["foo"] = res

    return res
