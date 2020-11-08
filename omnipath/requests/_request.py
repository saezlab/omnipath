from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Tuple, Mapping, Optional, Sequence
from functools import partial

import pandas as pd
from pandas.api.types import is_float_dtype, is_numeric_dtype

from omnipath._utils import Downloader, _format_url
from omnipath._options import options
from omnipath.constants import Organism, QueryType, QueryParams, InteractionDataset
from omnipath.constants._pkg_constants import _Format, _DefaultField


class OmnipathRequestMeta(ABCMeta):  # noqa: D101
    # TODO: make sure no intersection in __string__, etc.
    pass


class OmnipathRequestABC(ABC, metaclass=OmnipathRequestMeta):
    """Base class for all :mod:`omnipath` requests."""

    __string__ = frozenset({"uniprot", "genesymbol"})
    __logical__ = frozenset()
    __categorical__ = frozenset()

    _json_reader = partial(pd.read_json, type="frame")
    _tsv_reader = partial(pd.read_csv, sep="\t", header=0, squeeze=False)

    def __init__(self, query_type: QueryType):
        self._query_type = QueryType(query_type)
        self._result: Optional[pd.DataFrame] = None
        self._downloader = Downloader()

    def get(
        self,
        organism: Organism = Organism.HUMAN,
        resources: Optional[Sequence[str]] = None,
        genesymbols: bool = True,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Perform a request.

        Parameters
        ----------
        organism
            Organism for which to make the request. Can be one of the following:

                - omnipath.constants.Organism.HUMAN
                - omnipath.constants.Organism.MOUSE
                - omnipath.constants.Organism.RAT
        resources
            Return only results which are contained in any of these databases.
        genesymbols
            Whether to also retrieve the gene symbols.
        **kwargs
            Keyword arguments for the query.

        Returns
        -------
        :class:`pandas.DataFrame`
            The requested data.
        """
        # TODO: improve docs, expose parameters, docrep/inject docs
        organism = Organism(organism)

        if resources is None:
            resources = self.resources(**kwargs)

        params = self._validate_params(
            {
                **kwargs,
                **{
                    QueryParams.GENESYMBOLS.value: "yes" if genesymbols else "no",
                    QueryParams.ORGANISMS.value: organism.value,
                    QueryParams.RESOURCES.value: resources,
                },
            }
        )
        kwargs.setdefault(QueryParams.FORMAT.value, _Format.TSV.value)
        callback = (
            self._json_reader
            if _Format(kwargs[QueryParams.FORMAT.value]) == _Format
            else self._tsv_reader
        )

        url = _format_url(options.url, self._query_type)

        return self._post_process(
            self._downloader.maybe_download(url, params=params, callback=callback),
            **kwargs,
        )

    def _post_process(self, res: pd.DataFrame, **_) -> pd.DataFrame:
        def to_logical(col: pd.Series) -> pd.Series:
            if is_numeric_dtype(col):
                return col > 0
            return col.astype("string").str.lower().isin("y", "t", "yes", "true", "1")

        def handle_logical(df: pd.DataFrame, columns: frozenset):
            cols = list(frozenset(df.columns) & columns)
            if cols:
                df[cols] = df[cols].apply(to_logical)

        def handle_categorical(df: pd.DataFrame, columns: frozenset):
            cols = frozenset(df.columns) & columns
            cols = [
                col
                for col, dtype in zip(cols, df[cols].dtypes)
                if not is_float_dtype(dtype)
            ]
            if cols:
                df[cols] = df[cols].astype("category")

        def handle_string(df: pd.DataFrame, columns: frozenset):
            cols = list(frozenset(df.columns) & columns)
            df[cols] = df[cols].astype("string")

        # TODO: extract the above functions from this scope?

        if not isinstance(res, pd.DataFrame):
            raise TypeError(type(res))

        handle_logical(res, self.__logical__)
        handle_categorical(res, self.__categorical__)
        handle_string(res, self.__string__)

        return res

    def resources(self, **kwargs) -> Tuple[str]:
        """
        Return available resources for this type of query.

        Parameters
        ----------
        **kwargs
            Keyword arguments used for filtering unwanted resources.

        Returns
        -------
        tuple
            Sequence of sorted resources.
        """
        return tuple(
            sorted(
                res
                for res, params in self._downloader.resources().items()
                if self._query_type.value in params["queries"]
                and self._resource_filter(
                    params["queries"][self._query_type.value], **kwargs
                )
            )
        )

    @abstractmethod
    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        pass

    def _validate_params(
        self, params: Optional[Dict[str, Any]], add_defaults: bool = True
    ) -> Dict[str, Any]:
        # TODO: refactor this function
        for name, value in params.items():
            _ = QueryParams(name)
            if isinstance(value, (tuple, list)):
                params[name] = ",".join(value)

        if add_defaults and self._query_type in _DefaultField:
            params[QueryParams.FIELDS.value] = params.get(
                QueryParams.FIELDS.value, set()
            ) | {field.value for field in _DefaultField(self._query_type)}
            if InteractionDataset.DOROTHEA.value in params.get(QueryParams.RESOURCES):
                params[QueryParams.FIELDS.value] |= {QueryParams.DOROTHEA_LEVELS.value}

        if QueryParams.RESOURCES.value in params:
            requested_resources = set(params[QueryParams.RESOURCES.value].split(","))
            unknown_resources = requested_resources - set(self.resources())

            if unknown_resources:
                # TODO: logging
                print("TODO UNK resources:", unknown_resources)

        for opt, val in zip(
            (QueryParams.LICENSE, QueryParams.PASSWORD),
            (options.license.value, options.password),
        ):
            params.setdefault(opt.value, val)

        return {k: v for k, v in params.items() if v is not None}

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}>"

    def __repr__(self) -> str:
        return str(self)


class CommonPostProcessor(OmnipathRequestABC, ABC):
    """
    Class that implements common post-processing steps for :class:`omnipath.requests.Enzsub`, \
    :class:`omnipath.requests.Intercell`, :class:`omnipath.requests.Complexes` and \
    :class`omnipath.interactions.InteractionRequest`.

    This class remove `'genesymbols'` and `'organisms'` from the query parameters, as well as optionally adds
    number of resources and references to the result or removes the resource labels from references (PubMed IDs)
    :class:`omnipath.interactions.InteractionRequest` and :class:`omnipath.requests.Enzsub`.
    """

    def _post_process(
        self,
        res: pd.DataFrame,
        add_counts: bool = True,
        strip_reference_from_resource: bool = False,
        **_,
    ) -> pd.DataFrame:
        res = super()._post_process(res)

        # TODO: finish this
        if strip_reference_from_resource and "references" in res:
            res["references"] = 0
        if add_counts:
            res["n_references"] = 0
            res["n_resources"] = 0

        return res

    def get(
        self,
        resources: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> pd.DataFrame:  # noqa: D102
        # TODO: docrep
        return super().get(
            Organism.HUMAN, resources=resources, genesymbols=False, **kwargs
        )

    def _validate_params(
        self, params: Optional[Dict[str, Any]], add_defaults: bool = True
    ) -> Mapping[str, Any]:
        params = super()._validate_params(params, add_defaults=add_defaults)

        params.pop(QueryParams.GENESYMBOLS.value, None)
        params.pop(QueryParams.ORGANISMS.value, None)

        return params


class Enzsub(CommonPostProcessor):
    """
    Class capable of requesting enzyme-substrate relationships from [OmniPath]_.

    Imports the enzyme-substrate (more exactly, enzyme-PTM) relationship `database <https://omnipathdb.org/enzsub>`__.
    """

    def __init__(self):
        super().__init__(QueryType.ENZSUB)

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True
