from typing import Any, Dict, Mapping, Optional

import pandas as pd

from omnipath.constants._constants import InteractionDataset
from omnipath._core.requests._intercell import Intercell
from omnipath._core.requests.interactions._interactions import (
    Datasets_t,
    AllInteractions,
)


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
    include: Datasets_t = (
        InteractionDataset.OMNIPATH,
        InteractionDataset.PATHWAY_EXTRA,
        InteractionDataset.KINASE_EXTRA,
        InteractionDataset.LIGREC_EXTRA,
    ),
    interactions_params: Optional[Mapping[str, Any]] = None,
    transmitter_params: Optional[Mapping[str, Any]] = None,
    receiver_params: Optional[Mapping[str, Any]] = None,
) -> pd.DataFrame:
    """
    Import intercellular network combining intercellular annotations and protein interactions.

    First, it imports a network of protein-protein interactions. Then, it retrieves annotations about the proteins
    intercellular communication roles, once for the transmitter (delivering information from the expressing cell) and
    second, the receiver (receiving signal and relaying it towards the expressing cell) side.

    These 3 queries can be customized by providing parameters which will be passed to
    :meth:`omnipath.interactions.OmniPath.get` for the network and :meth:`omnipath.requests.Intercell`
    for the annotations.

    Finally the 3 :class:`pandas.DataFrame` are combined in a way that the source proteins in each interaction annotated
    by the transmitter, and the target proteins by the receiver categories. If undirected interactions present
    (these are disabled by default) they will be duplicated, i.e. both partners can be both receiver and transmitter.

    Parameters
    ----------
    include
        Interaction datasets to include for :meth:`omnipath.interactions.AllInteractions.get`.
    interactions_params
        Parameters for the :meth:`omnipath.interactions.AllInteractions.get`.
    transmitter_params
        Parameters defining the transmitter side of intercellular connections.
        See :meth:`omnipath.interactions.AllInteractions.params` for available values.
    receiver_params
        Parameters defining the receiver side of intercellular connections.
        See :meth:`omnipath.interactions.AllInteractions.params` for available values.

    Returns
    -------
    :class:`pandas.DataFrame`
        A dataframe containing information about protein-protein interactions and the inter-cellular roles
        of the proteins involved in those interactions.
    """
    interactions_params = _to_dict(interactions_params)
    transmitter_params = _to_dict(transmitter_params)
    receiver_params = _to_dict(receiver_params)

    # TODO: this should be refactored as: QueryType.INTERCELL("scope").param, etc. (also in many other places)
    transmitter_params.setdefault("causality", "trans")
    transmitter_params.setdefault("scope", "generic")
    receiver_params.setdefault("causality", "rec")
    receiver_params.setdefault("scope", "generic")

    interactions = AllInteractions.get(include=include, **interactions_params)
    interactions = _swap_undirected(interactions)

    transmitters = Intercell.get(**transmitter_params)
    receivers = Intercell.get(**receiver_params)

    # fmt: off
    intracell = ['intracellular_intercellular_related', 'intracellular']
    transmitters = transmitters.loc[~transmitters["parent"].isin(intracell), :]
    transmitters.rename(columns={"source": "category_source"}, inplace=True)
    # this makes it 3x as fast during groupby, since all of these are categories
    # it's mostly because groupby needs observed=True + using string object (numpy) vs "string"
    transmitters[["category", "parent", "database"]] = transmitters[["category", "parent", "database"]].astype(str)

    receivers = receivers.loc[~receivers["parent"].isin(intracell), :]
    receivers.rename(columns={"source": "category_source"}, inplace=True)
    receivers[["category", "parent", "database"]] = receivers[["category", "parent", "database"]].astype(str)

    res = pd.merge(interactions, transmitters, left_on="source", right_on="uniprot", how="inner")
    gb = res.groupby(["category", "parent", "source", "target"], as_index=False)
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
    for col in ["category", "parent"]:
        for suffix in ["_intercell_source", "_intercell_target"]:
            res[f"{col}{suffix}"] = res[f"{col}{suffix}"].astype("category")

    return res.reset_index(drop=True)


def get_signed_ptms(
    ptms: Optional[pd.DataFrame] = None, interactions: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Get signs for enzyme-PTM interactions.

    PTM data does not contain sign (activation/inhibition), we generate this information based on the
    interaction network.

    Parameters
    ----------
    ptms
        Data generated by :meth:`omnipath.requests.Enzsub.get`. If `None`, a new request will be performed.
    interactions
        Data generated by :meth:`omnipath.interactions.OmniPath.get`.  If `None`, a new request will be performed.

    Returns
    -------
    :class:`pandas.DataFrame`
        The signed PTMs with columns **'is_inhibition'** and **'is_stimulation'**.
    """
    from omnipath.requests import Enzsub
    from omnipath.interactions import OmniPath

    ptms = Enzsub.get() if ptms is None else ptms
    interactions = OmniPath.get() if interactions is None else interactions

    if not isinstance(ptms, pd.DataFrame):
        raise TypeError(
            f"Expected `ptms` to be of type `pandas.DataFrame`, found `{type(ptms).__name__}`."
        )
    if not isinstance(interactions, pd.DataFrame):
        raise TypeError(
            f"Expected `interactions` to be of type `pandas.DataFrame`, found `{type(ptms).__name__}`."
        )

    return pd.merge(
        ptms,
        interactions[["source", "target", "is_stimulation", "is_inhibition"]],
        left_on=["enzyme", "substrate"],
        right_on=["source", "target"],
        how="left",
    )
