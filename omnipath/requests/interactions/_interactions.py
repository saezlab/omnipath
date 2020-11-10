import json
from abc import ABC
from typing import Any, Dict, Tuple, Union, Mapping, Optional, Sequence
from urllib.parse import urljoin

import pandas as pd

import omnipath as op
from omnipath.constants import (
    QueryType,
    QueryParams,
    DorotheaLevels,
    InteractionDataset,
)
from omnipath.requests._request import CommonPostProcessor
from omnipath.constants._pkg_constants import _Format


class InteractionRequest(CommonPostProcessor, ABC):
    """
    Class capable of retrieve interactions from [OmniPath]_.

    Parameters
    ----------
    datasets
        Name of interaction datasets to download. If `None`, download all datasets, after removing the ones in
        ``exclude``. Can be either one or a sequence of the following:

            - omnipath.constants.InteractionDataset.OMNIPATH
            - omnipath.constants.InteractionDataset.PATHWAY_EXTRA
            - omnipath.constants.InteractionDataset.KINASE_EXTRA
            - omnipath.constants.InteractionDataset.LIGREC_EXTRA
            - omnipath.constants.InteractionDataset.DOROTHEA
            - omnipath.constants.InteractionDataset.TF_TARGET
            - omnipath.constants.InteractionDataset.TF_MIRNA
            - omnipath.constants.InteractionDataset.TF_REGULONS ?
            - omnipath.constants.InteractionDataset.MIRNA_TARGET ?
            - omnipath.constants.InteractionDataset.LNCRNA_MRNA
    exclude
        Interaction datasets to exclude. Only used when ``datasets=None``.
    """

    # TODO: inject docs (docrep)
    # TODO: check with omnipathR (esp. the ones marked with ?)

    def __init__(
        self,
        datasets: Optional[Union[InteractionDataset, Sequence[InteractionDataset]]],
        exclude: Optional[Sequence[InteractionDataset]] = None,
    ):
        super().__init__(QueryType.INTERACTIONS)

        if datasets is None:
            if exclude is None:
                exclude = set()

            url = urljoin(
                urljoin(op.options.url, QueryType.QUERIES.value) + "/",
                self._query_type.value,
            )
            params = {QueryParams.FORMAT.value: _Format.JSON.value}

            datasets = self._downloader.maybe_download(
                url, params=params, callback=json.load
            )["datasets"]
            datasets = tuple(set(datasets) - set(exclude))

        if isinstance(datasets, InteractionDataset):
            datasets = (datasets,)
        elif not isinstance(datasets, Sequence):
            raise TypeError(
                f"Expected `datasets` to be a `Sequence`, found `{type(datasets).__name__}`."
            )

        if not len(datasets):
            # TODO: nicer message if exclude
            raise ValueError("No datasets have been selected.")

        self._datasets = set(datasets)

    def resources(self, **_) -> Tuple[str]:
        """Return resources for this type of query."""
        return super().resources(datasets=self._datasets)

    def _resource_filter(
        self,
        data: Mapping[str, Any],
        datasets: Optional[Sequence[InteractionDataset]] = None,
    ) -> bool:
        # TODO: docs
        res = datasets is None or (
            {InteractionDataset(d) for d in data["datasets"]}
            & {InteractionDataset(d) for d in datasets}
        )

        return res


class PathwayExtra(InteractionRequest):
    """
    Class capable of requesting interactions from the `pathway extra` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=pathwayextra>`__ which contains activity flow
    interactions without literature reference.
    """

    def __init__(self):
        super().__init__(InteractionDataset.PATHWAY_EXTRA)


class KinaseExtra(InteractionRequest):
    """
    Class capable of requesting interactions from the `kinase extra` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=kinaseextra>`__ which contains enzyme-substrate
    interactions without literature reference.

    The enzyme-substrate interactions supported by literature references are part of the
    :class:`omnipath.requests.AllInteractions`.
    """

    def __init__(self):
        super().__init__(InteractionDataset.KINASE_EXTRA)


class LigRecExtra(InteractionRequest):
    """
    Class capable of requesting interactions from the `ligrec extra` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=ligrecextra>`__ which contains ligand-receptor
    interactions without literature reference.
    """

    def __init__(self):
        super().__init__(InteractionDataset.LIGREC_EXTRA)


class Dorothea(InteractionRequest):
    """
    Class capable of requesting interactions from the `dorothea` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=dorothea>`__ which contains transcription factor
    (TF)-target interactions from `DoRothEA <https://github.com/saezlab/DoRothEA>`__.
    """

    __string__ = frozenset({"source", "target", "dip_url"})
    __logical__ = frozenset(
        {
            "is_directed",
            "is_stimulation",
            "is_inhibition",
            "consensus_direction",
            "consensus_stimulation",
            "consensus_inhibition",
        }
    )

    def __init__(self):
        super().__init__(InteractionDataset.DOROTHEA)

    def _validate_params(
        self, params: Optional[Dict[str, Any]], add_defaults: bool = True
    ) -> Mapping[str, Any]:
        params = super()._validate_params(params, add_defaults=add_defaults)

        dkey = QueryParams.DOROTHEA_LEVELS.value
        if params.get(dkey, None) is not None:
            requested_levels = set(params[dkey].split(","))
            unexpected_levels = requested_levels - {
                level.value for level in DorotheaLevels
            }

            # TODO: logging
            if len(unexpected_levels):
                print("UNEXPECTED DOROTHEALEVEL:", unexpected_levels)

        return params

    def get(
        self,
        resources: Optional[Sequence[str]] = None,
        levels: Optional[Sequence[Union[DorotheaLevels, str]]] = (
            DorotheaLevels.A,
            DorotheaLevels.B,
        ),
        **kwargs,
    ) -> pd.DataFrame:
        """TODO: docrep."""
        if levels is not None:
            kwargs[QueryParams.DOROTHEA_LEVELS.value] = [
                DorotheaLevels(level).value for level in levels
            ]

        return super().get(resources, **kwargs)


class TFtarget(InteractionRequest):
    """
    Class capable of requesting interactions from the `TF-target` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=tf_target>`__ which contains transcription
    factor-target protein coding gene interactions.

    Other TF-target datasets in :mod:`omnipath` are :class:`omnipath.interactions.Dorothea` and
    :class:`omnipath.interactions.TFmiRNA` which provides TF-miRNA gene interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.TF_TARGET)


# TODO: remove?
class Transcriptional(InteractionRequest):
    """
    Class capable of requesting all `TF-target` interactions of [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=tf_target,dorothea>`__ which contains
    transcription factor-target protein coding gene interactions.
    """

    # TODO: needs to be checked
    def __init__(self):
        super().__init__((InteractionDataset.DOROTHEA, InteractionDataset.TF_TARGET))


class miRNA(InteractionRequest):
    """
    Class capable of requesting interactions from the `miRNA-target` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=mirnatarget>`__. which contains
    miRNA-mRNA interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.MIRNA_TARGET)


class TFmiRNA(InteractionRequest):
    """
    Class capable of requesting interactions from the `TF-miRNA` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=tf_mirna>`__ which contains transcription
    factor-miRNA gene interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.TF_MIRNA)


class lncRNAmRNA(InteractionRequest):
    """
    Class capable of requesting interactions from the `lncRNA-mRNA` dataset from [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=lncrna_mrna>`__ which contains
    lncRNA-mRNA interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.LNCRNA_MRNA)


class OmniPath(InteractionRequest):
    """
    Class capable of requesting interactions from the `omnipath` dataset from [OmniPath]_.

    Imports the `database <https://omnipathdb.org/interactions>`__, which contains only interactions supported by
    literature references.

    This part of the interaction database was compiled in a similar way as it has been presented in [OmniPath2016]_.

    References
    ----------
    .. [OmniPath2016] Türei, D., Korcsmáros, T. & Saez-Rodriguez, J.,
        *OmniPath: guidelines and gateway for literature-curated signaling pathway resources.*,
        `Nat Methods 13, 966–967 (2016). <https://doi.org/10.1038/nmeth.4077>`
    """

    def __init__(self):
        super().__init__(InteractionDataset.OMNIPATH)


class AllInteractions(InteractionRequest):
    """
    Class capable of requesting all [OmniPath]_ interaction datasets.

    Parameters
    ----------
    exclude
        Interaction datasets to exclude from the [OmniPath]_ database.
    """

    def __init__(
        self,
        exclude: Optional[Sequence[InteractionDataset]] = None,
    ):
        super().__init__(None, exclude=exclude)

    def get(
        self,
        resources: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """TODO: docrep."""
        kwargs.setdefault(QueryParams.FIELDS.value, ["type"])
        return super().get(resources, **kwargs)


__all__ = [
    Dorothea,
    OmniPath,
    TFtarget,
    KinaseExtra,
    LigRecExtra,
    PathwayExtra,
    AllInteractions,
    Transcriptional,
    miRNA,
    lncRNAmRNA,
]
