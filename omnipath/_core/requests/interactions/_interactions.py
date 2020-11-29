from abc import ABC, abstractmethod
from typing import Any, Set, Dict, Tuple, Union, Mapping, Iterable, Optional, Sequence

import pandas as pd

from omnipath.constants import InteractionDataset
from omnipath._core.query import QueryType
from omnipath._core.utils._docs import d
from omnipath._core.requests._utils import _inject_params
from omnipath._core.requests._request import GraphLike, CommonPostProcessor
from omnipath.constants._pkg_constants import Key, final

Datasets_t = Union[str, InteractionDataset, Sequence[str], Sequence[InteractionDataset]]


def _to_dataset_set(
    datasets, name: str, none_value: Iterable[InteractionDataset]
) -> Set[InteractionDataset]:
    if isinstance(datasets, (str, InteractionDataset)):
        datasets = (datasets,)
    elif datasets is None:
        datasets = none_value

    if not isinstance(datasets, Iterable):
        raise TypeError(
            f"Expected `{name}` to be an `Iterable`, found `{type(datasets).__name__}`."
        )

    return {InteractionDataset(d) for d in datasets}


@d.dedent
class InteractionRequest(CommonPostProcessor, GraphLike, ABC):
    """
    Base class for retrieving interactions from [OmniPath]_.

    Parameters
    ----------
    datasets
        Name of interaction datasets to download. If `None`, download all datasets, after removing the ones in
        ``exclude``. Can be one or more of the following:

            %(interaction_datasets)s

    exclude
        Interaction datasets to exclude. Only used when ``datasets = None``.
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

    _query_type = QueryType.INTERACTIONS

    def __init__(
        self,
        datasets: Optional[Datasets_t] = None,
        exclude: Optional[Datasets_t] = None,
    ):
        super().__init__()

        datasets = _to_dataset_set(datasets, "datasets", set(InteractionDataset))
        exclude = _to_dataset_set(exclude, "exclude", set())
        datasets = datasets - exclude

        if not len(datasets):
            raise ValueError(
                f"After excluding `{len(exclude)}` datasets, none were left."
            )

        self._datasets = datasets

    def _modify_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = super()._modify_params(params)
        params[self._query_type("datasets").param] = self._datasets
        return params

    @classmethod
    @abstractmethod
    def _filter_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        params.pop(cls._query_type(Key.DATASETS.s).param, None)

        return params

    @classmethod
    @d.dedent
    def params(cls) -> Dict[str, Any]:
        """%(query_params)s"""
        params = super().params()
        return cls._filter_params(params)

    @classmethod
    def _get_source_target_cols(cls, data: pd.DataFrame) -> Tuple[str, str]:
        source = "source_genesymbol" if "source_genesymbol" in data else "source"
        target = "target_genesymbol" if "target_genesymbol" in data else "target"

        return source, target

    def _resources(self, **_) -> Tuple[str]:
        return super()._resources(**{Key.DATASETS.s: self._datasets})

    def _resource_filter(
        self,
        data: Mapping[str, Any],
        datasets: Optional[Sequence[InteractionDataset]] = None,
    ) -> bool:
        res = datasets is None or (
            {InteractionDataset(d) for d in data.get(Key.DATASETS.s, {})}
            & {InteractionDataset(d) for d in datasets}
        )

        return res


class CommonParamFilter(InteractionRequest, ABC):
    """Filter which tries to remove some common invalid parameters from many interaction queries."""

    @classmethod
    def _filter_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        params = super()._filter_params(params)

        for key in (
            "dorothea_levels",
            "dorothea_methods",
            "tfregulons_levels",
            "tfregulons_methods",
        ):
            try:
                # catch the ValueError if not a valid key anymore
                params.pop(cls._query_type(key).param)
            except (KeyError, ValueError):
                pass

        return params


@final
class PathwayExtra(CommonParamFilter):
    """
    Request interactions from the `pathway extra` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=pathwayextra>`__ which contains activity flow
    interactions without literature reference.
    """

    def __init__(self):
        super().__init__(InteractionDataset.PATHWAY_EXTRA)


@final
class KinaseExtra(CommonParamFilter):
    """
    Request interactions from the `kinase extra` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=kinaseextra>`__ which contains enzyme-substrate
    interactions without literature reference.

    The enzyme-substrate interactions supported by literature references are part of the
    :class:`omnipath.requests.AllInteractions`.
    """

    def __init__(self):
        super().__init__(InteractionDataset.KINASE_EXTRA)


@final
class LigRecExtra(CommonParamFilter):
    """
    Request interactions from the `ligrec extra` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=ligrecextra>`__ which contains ligand-receptor
    interactions without literature reference.
    """

    def __init__(self):
        super().__init__(InteractionDataset.LIGREC_EXTRA)


@final
class Dorothea(InteractionRequest):
    """
    Request interactions from the `dorothea` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=dorothea>`__ which contains transcription factor
    (TF)-target interactions from `DoRothEA <https://github.com/saezlab/DoRothEA>`__.
    """

    def __init__(self):
        super().__init__(InteractionDataset.DOROTHEA)

    @classmethod
    def _filter_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        params = super()._filter_params(params)
        params.pop(cls._query_type("tfregulons_levels").param, None)
        params.pop(cls._query_type("tfregulons_methods").param, None)

        return params


@final
class TFtarget(InteractionRequest):
    """
    Request interactions from the `TF-target` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=tf_target>`__ which contains transcription
    factor-target protein coding gene interactions.

    Other TF-target datasets in :mod:`omnipath` are :class:`omnipath.interactions.Dorothea` and
    :class:`omnipath.interactions.TFmiRNA` which provides TF-miRNA gene interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.TF_TARGET)

    @classmethod
    def _filter_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        params = super()._filter_params(params)
        params.pop(cls._query_type("dorothea_levels").param, None)
        params.pop(cls._query_type("dorothea_methods").param, None)

        return params


@final
class Transcriptional(InteractionRequest):
    """
    Request all `TF-target` interactions of [OmniPath]_.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=dorothea,tf_target>`__ which contains
    transcription factor-target protein coding gene interactions.
    """

    def __init__(self):
        super().__init__((InteractionDataset.DOROTHEA, InteractionDataset.TF_TARGET))

    @classmethod
    def _filter_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        return super()._filter_params(params)


@final
class miRNA(CommonParamFilter):
    """
    Request interactions from the `miRNA-target` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=mirnatarget>`__. which contains
    miRNA-mRNA interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.MIRNA_TARGET)


@final
class TFmiRNA(CommonParamFilter):
    """
    Request interactions from the `TF-miRNA` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=tf_mirna>`__ which contains transcription
    factor-miRNA gene interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.TF_MIRNA)


@final
class lncRNAmRNA(CommonParamFilter):
    """
    Request interactions from the `lncRNA-mRNA` dataset.

    Imports the `dataset <https://omnipathdb.org/interactions?datasets=lncrna_mrna>`__ which contains
    lncRNA-mRNA interactions.
    """

    def __init__(self):
        super().__init__(InteractionDataset.LNCRNA_MRNA)


@final
class OmniPath(InteractionRequest):
    """
    Request interactions from the `omnipath` dataset.

    Imports the `database <https://omnipathdb.org/interactions>`__, which contains only interactions supported by
    literature references.

    This part of the interaction database was compiled in a similar way as it has been presented in [OmniPath16]_.
    """

    @classmethod
    def _filter_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        return super()._filter_params(params)

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
        super().__init__(InteractionDataset.OMNIPATH)


@final
@d.get_sections(base="all_ints", sections=["Parameters"])
@d.dedent
class AllInteractions(InteractionRequest):
    """
    Request all [OmniPath]_ interaction datasets.

    The available interaction datasets are :class:`omnipath.constants.InteractionDataset`.

    Parameters
    ----------
    include
        Interactions datasets to include from the [OmniPath]_ database. If `None`, include everything.
    exclude
        Interaction datasets to exclude from the [OmniPath]_ database. If `None`, don't exclude anything.
    """

    def __init__(
        self,
        include: Optional[Datasets_t] = None,
        exclude: Optional[Datasets_t] = None,
    ):
        super().__init__(include, exclude=exclude)

    def _inject_fields(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params = super()._inject_fields(params)
        _inject_params(params, key=self._query_type("fields").param, value="type")

        return params

    @classmethod
    def _filter_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        return super()._filter_params(params)

    @classmethod
    @final
    @d.dedent
    def get(
        cls,
        include: Optional[Datasets_t] = None,
        exclude: Optional[Datasets_t] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        %(get.full_desc)s

        The available interaction datasets are :class:`omnipath.constants.InteractionDataset`.

        Parameters
        ----------
        include
            Interactions datasets to include from the [OmniPath]_ database. If `None`, include everything.
        exclude
            Interaction datasets to exclude from the [OmniPath]_ database. If `None`, don't exclude anything.
        %(get.parameters)s

        Returns
        -------
        %(get.returns)s
        """
        return cls(include, exclude=exclude)._get(**kwargs)


__all__ = [
    Dorothea,
    OmniPath,
    TFtarget,
    KinaseExtra,
    LigRecExtra,
    PathwayExtra,
    AllInteractions,
    Transcriptional,
    TFmiRNA,
    miRNA,
    lncRNAmRNA,
]
