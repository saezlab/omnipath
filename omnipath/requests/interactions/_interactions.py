import json
from typing import Any, Dict, Tuple, Union, Mapping, Optional, Sequence
from urllib.parse import urljoin

import pandas as pd

from omnipath._options import options
from omnipath.constants import (
    QueryType,
    QueryParams,
    DorotheaLevels,
    InteractionDataset,
)
from omnipath.requests._request import CommonPostProcessor
from omnipath.constants._pkg_constants import _Format


class InteractionRequest(CommonPostProcessor):
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
                urljoin(options.url, QueryType.QUERIES.value) + "/",
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
            raise TypeError()

        if not len(datasets):
            raise ValueError()

        self._datasets = set(datasets)

    # TODO: abstract away to all Q types
    def resources(self, **kwargs) -> Tuple[str]:
        return super().resources(datasets=self._datasets, **kwargs)

    def _resource_filter(
        self,
        data: Mapping[str, Any],
        datasets: Optional[Sequence[InteractionDataset]] = None,
    ) -> bool:
        res = datasets is None or (
            {InteractionDataset(d) for d in data["datasets"]}
            & {InteractionDataset(d) for d in datasets}
        )

        return res


class PathwayExtra(InteractionRequest):
    def __init__(self):
        super().__init__(InteractionDataset.PATHWAY_EXTRA)


class KinaseExtra(InteractionRequest):
    def __init__(self):
        super().__init__(InteractionDataset.KINASE_EXTRA)


class LigRecExtra(InteractionRequest):
    def __init__(self):
        super().__init__(InteractionDataset.LIGREC_EXTRA)


class Dorothea(InteractionRequest):
    def __init__(self):
        super().__init__(InteractionDataset.DOROTHEA)

    def _validate_params(
        self, params: Optional[Dict[str, Any]], add_defaults: bool = True
    ) -> Mapping[str, Any]:
        params = super()._validate_params(params, add_defaults=add_defaults)

        if QueryParams.DOROTHEA_LEVELS.value in params:
            requested_levels = set(params[QueryParams.DOROTHEA_LEVELS.value])
            unexpected_levels = requested_levels - {
                level.values for level in DorotheaLevels
            }

            # TODO:
            if len(unexpected_levels):
                print("UNEXPECTED DOROTHEALEVEL:", unexpected_levels)

        return params


class TFregulons(InteractionRequest):
    def __init__(self):
        super().__init__(InteractionDataset.TF_TARGET)


class miRNA(InteractionRequest):
    def __init__(self):
        super().__init__(InteractionDataset.MIRNA_TARGET)


class lncRNAmRNA(InteractionRequest):
    def __init__(self):
        super().__init__(InteractionDataset.LNCRNA_MRNA)


class Transcriptional(InteractionRequest):
    # TODO: needs to be checked
    def __init__(self):
        super().__init__((InteractionDataset.DOROTHEA, InteractionDataset.TF_TARGET))


class Omnipath(InteractionRequest):
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
        kwargs.setdefault(QueryParams.FIELDS.value, ["type"])
        return super().get(resources, **kwargs)


__all__ = [
    PathwayExtra,
    KinaseExtra,
    LigRecExtra,
    Dorothea,
    TFregulons,
    miRNA,
    lncRNAmRNA,
    Transcriptional,
    Omnipath,
]
# import_transcriptional_interactions
