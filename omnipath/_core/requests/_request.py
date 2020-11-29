from io import BytesIO
from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
from typing import (
    Any,
    Dict,
    Tuple,
    Union,
    Mapping,
    Callable,
    Iterable,
    Optional,
    Sequence,
)
from operator import itemgetter
from functools import wraps, partial
import logging

from pandas.api.types import is_float_dtype, is_numeric_dtype
import pandas as pd

from omnipath import options
from omnipath.constants import License, Organism
from omnipath._core.query import QueryType
from omnipath._core.utils._docs import d
from omnipath._core.requests._utils import (
    _inject_params,
    _inject_api_method,
    _strip_resource_label,
)
from omnipath.constants._pkg_constants import DEFAULT_FIELD, Key, Format, final
from omnipath._core.downloader._downloader import Downloader


def _error_handler(callback: Callable[[BytesIO], Any]) -> Callable:
    @wraps(callback)
    def wrapper(cls, *args, **kwargs) -> pd.DataFrame:
        res: pd.DataFrame = callback(*args, **kwargs)
        if len(res.columns) == 1 and res.columns == ["Something is not entirely good:"]:
            raise RuntimeError(" ".join(res.iloc[:, 0]))

        return res

    return wrapper


class OmnipathRequestMeta(ABCMeta):  # noqa: D101
    def __new__(cls, clsname, superclasses, attributedict):  # noqa: D102
        for supercls in superclasses:
            for attr in ("__string__", "__logical__", "__categorical__"):
                attributedict[attr] = attributedict.get(attr, frozenset()) | getattr(
                    supercls, attr, frozenset()
                )

        clazz = super().__new__(cls, clsname, superclasses, attributedict)
        _inject_api_method(clazz)

        return clazz


class OmnipathRequestABC(ABC, metaclass=OmnipathRequestMeta):
    """Base class for all :mod:`omnipath` requests."""

    __string__ = frozenset({"uniprot", "genesymbol"})
    __logical__ = frozenset()
    __categorical__ = frozenset()

    _json_reader = _error_handler(partial(pd.read_json, typ="frame"))
    _tsv_reader = _error_handler(
        partial(pd.read_csv, sep="\t", header=0, squeeze=False)
    )
    _query_type: Optional[QueryType] = None

    def __init__(self):
        self._downloader = Downloader(options)

    @classmethod
    @d.dedent
    def resources(cls, **kwargs) -> Tuple[str]:
        """%(query_resources)s"""
        return cls()._resources(**kwargs)

    @classmethod
    @d.dedent
    def params(cls) -> Dict[str, Any]:
        """%(query_params)s"""
        return {q.param: q.valid for q in cls._query_type.value}

    @classmethod
    def _annotations(cls) -> Dict[str, type]:
        """Return the type annotation for the query parameters."""
        return {q.param: q.annotation for q in cls._query_type.value}

    @classmethod
    def _docs(cls) -> Dict[str, Optional[str]]:
        """Return the type annotation for the query parameters."""
        return {q.param: q.doc for q in cls._query_type.value}

    def _get(self, **kwargs) -> pd.DataFrame:
        kwargs = self._modify_params(kwargs)
        kwargs = self._inject_fields(kwargs)
        kwargs, callback = self._convert_params(kwargs)
        kwargs = self._validate_params(kwargs)
        kwargs = self._finalize_params(kwargs)

        res = self._downloader.maybe_download(
            self._query_type.endpoint, params=kwargs, callback=callback, is_final=False
        )

        if self._downloader._options.convert_dtypes:
            res = self._convert_dtypes(res)

        return self._post_process(res)

    def _convert_params(
        self, params: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Callable]:
        organism = params.pop("organism", params.pop("organisms", None))
        if organism is not None:
            organism = Organism(organism)
            try:
                params[self._query_type("organism").param] = organism.code
            except ValueError:
                pass

        # check the requested format
        fmt = params.pop("format", params.pop("formats", None))
        fmt = Format(Format.TSV if fmt is None else fmt)
        if fmt not in (Format.TSV, Format.JSON):
            logging.warning(
                f"Invalid `{Key.FORMAT.s}={fmt.s!r}`. Using `{Key.FORMAT.s}={Format.TSV.s!r}`"
            )
            fmt = Format.TSV
        callback = self._tsv_reader if fmt == Format.TSV else self._json_reader
        try:
            params[self._query_type("format").param] = fmt.s
        except ValueError:
            pass

        # check the license
        license = params.pop(
            "license", params.pop("licenses", self._downloader._options.license)
        )
        if license is not None:
            license = License(license)
            try:
                params[self._query_type("license").param] = license
            except ValueError:
                pass

        if self._downloader._options.password is not None:
            params.setdefault(Key.PASSWORD.s, self._downloader._options.password)

        return params, callback

    def _inject_fields(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            _inject_params(
                params,
                key=self._query_type(Key.FIELDS.value).param,
                value=getattr(DEFAULT_FIELD, self._query_type.name).value,
            )
        except AttributeError:
            # no default field for this query
            pass
        except Exception as e:
            logging.warning(
                f"Unable to inject `{Key.FIELDS.value}` for `{self}`. Reason: `{e}`"
            )

        return params

    def _validate_params(
        self, params: Dict[str, Any]
    ) -> Dict[str, Optional[Union[str, Sequence[str]]]]:
        """For each passed parameter, validate if it has the correct value."""
        res = {}
        for k, v in params.items():
            # first get the validator for the parameter, then validate
            res[self._query_type(k).param] = self._query_type(k)(v)
        return res

    def _finalize_params(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Convert all the parameters to strings."""
        # this is largely redundant
        res = {}
        for k, v in params.items():
            if isinstance(v, str):
                res[k] = v
            elif isinstance(v, bool):
                res[k] = str(int(v))
            elif isinstance(v, (int, float)):
                res[k] = str(v)
            elif isinstance(v, Iterable):
                res[k] = ",".join(sorted(v))
            elif isinstance(v, Enum):
                res[k] = str(v.value)
            elif v is not None:
                logging.warning(f"Unable to process parameter `{k}={v}`. Ignoring")

        return dict(sorted(res.items(), key=itemgetter(0)))

    def _convert_dtypes(self, res: pd.DataFrame, **_) -> pd.DataFrame:
        """Automatically convert dtypes for this type of query."""

        def to_logical(col: pd.Series) -> pd.Series:
            if is_numeric_dtype(col):
                return col > 0
            return col.astype(str).str.lower().isin("y", "t", "yes", "true", "1")

        def handle_logical(df: pd.DataFrame, columns: frozenset) -> None:
            cols = list(frozenset(df.columns) & columns)
            if cols:
                df[cols] = df[cols].apply(to_logical)

        def handle_categorical(df: pd.DataFrame, columns: frozenset) -> None:
            cols = frozenset(df.columns) & columns
            cols = [
                col
                for col, dtype in zip(cols, df[cols].dtypes)
                if not is_float_dtype(dtype)
            ]
            if cols:
                df[cols] = df[cols].astype("category")

        def handle_string(df: pd.DataFrame, columns: frozenset) -> None:
            for col in frozenset(df.columns) & columns:
                mask = pd.isnull(df[col])
                df[col] = df[col].astype(str)
                df.loc[mask, col] = None

        if not isinstance(res, pd.DataFrame):
            raise TypeError(
                f"Expected the result to be of type `pandas.DataFrame`, found `{type(res).__name__}`."
            )

        handle_logical(res, self.__logical__)
        handle_categorical(res, self.__categorical__)
        handle_string(res, self.__string__)

        return res

    def _resources(self, **kwargs) -> Tuple[str]:
        """
        Return available resources for this type of query.

        Parameters
        ----------
        **kwargs
            Keyword arguments used for filtering unwanted resources.

        Returns
        -------
        tuple
            Unique and sorted resources.
        """
        return tuple(
            sorted(
                res
                for res, params in self._downloader.resources.items()
                if self._query_type.endpoint in params.get(Key.QUERIES.s, {})
                and self._resource_filter(
                    params[Key.QUERIES.s][self._query_type.endpoint], **kwargs
                )
            )
        )

    def _modify_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove parameters from this query.

        Parameters
        ----------
        params
            The parameters to filter.

        Returns
        -------
        :class:`dict`
            The filtered parameters.
        """
        return params

    @abstractmethod
    def _post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Post process the result, e.g. by adding extra columns.

        df
            The result from :meth:`get`.

        Returns
        -------
        :class:`pandas.DataFrame`
            The maybe modified result.
        """
        pass

    @abstractmethod
    def _resource_filter(self, data: Mapping[str, Any], **kwargs) -> bool:
        """
        Filter out resources relevant to this query.

        Parameters
        ----------
        data
            Data which is used as a basis for the filtering.
        kwargs
            Additional keyword arguments.

        Returns
        --------
        bool
            `True` if the resource should be included, otherwise `False`.
        """
        pass

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

    def _post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add number of resources and references for each row in the resulting ``df``.

        Parameters
        ----------
        df
            The dataframe containing results.

        Returns
        -------
        :class:`pandas.DataFrame`
            The modified dataframe.
        """
        if "references" in df:
            df["references_stripped"] = _strip_resource_label(df["references"])
            df["n_references"] = _strip_resource_label(
                df["references"], func=lambda row: len(set(row))
            )
        if "sources" in df:
            df["n_sources"] = df["sources"].astype(str).str.split(";").apply(len)
            df["n_primary_sources"] = (
                df["sources"]
                .astype(str)
                .str.split(";")
                .apply(
                    lambda row: len(
                        [r for r in row if "_" not in r]
                        if isinstance(row, Iterable)
                        else 0
                    )
                )
            )

        return df


class OrganismGenesymbolsRemover(CommonPostProcessor, ABC):
    """Class that removes organism and genesymbols keys from the query."""

    def _modify_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params.pop(Key.ORGANISM.s, None)
        params.pop(Key.GENESYMBOLS.s, None)

        return params

    @classmethod
    @d.dedent
    def params(cls) -> Dict[str, Any]:
        """%(query_params)s"""
        params = super().params()
        params.pop(Key.ORGANISM.s, None)
        params.pop(Key.GENESYMBOLS.s, None)

        return params


@final
class Enzsub(CommonPostProcessor):
    """
    Request enzyme-substrate relationships from [OmniPath]_.

    Imports the enzyme-substrate (more exactly, enzyme-PTM) relationships `database <https://omnipathdb.org/enzsub>`__.
    """

    __string__ = frozenset({"enzyme", "substrate"})
    __categorical__ = frozenset({"residue_type", "modification"})

    _query_type = QueryType.ENZSUB
    _final = True

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True


__all__ = [Enzsub]
