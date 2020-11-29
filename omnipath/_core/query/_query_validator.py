from abc import ABCMeta
from enum import Enum, EnumMeta
from typing import (
    Any,
    Set,
    List,
    Union,
    Mapping,
    Iterable,
    Optional,
    Sequence,
    FrozenSet,
)
from urllib.parse import urljoin
import json
import logging

from omnipath._core.utils._docs import d
from omnipath._core.query._types import (
    Int_t,
    Str_t,
    Bool_t,
    None_t,
    Strseq_t,
    License_t,
    Organism_t,
)
from omnipath._core.utils._options import Options
from omnipath.constants._constants import NoValue
from omnipath.constants._pkg_constants import Key, Format
from omnipath._core.downloader._downloader import Downloader


def _to_string_set(item: Union[Any, Sequence[Any]]) -> Set[str]:
    """
    Convert ``item`` to a `str` set.

    Parameters
    ----------
    item
        Item to convert. If it's not a sequence, it will be made into singleton.

    Returns
    -------
    :class:`set`
        Set of `str`.
    """
    if isinstance(item, (str, Enum)) or not isinstance(item, Iterable):
        item = (item,)
    return set({str(i.value if isinstance(i, Enum) else i) for i in item})


class ServerValidatorMeta(EnumMeta, ABCMeta):  # noqa: D101
    class Validator:
        """
        Class that validates values for some parameter passed to the server.

        Parameters
        ----------
        param
            Name of the parameter we're checking. Only used for informing the user.
        haystack
            Valid values for the ``paramter``. If `None`, no validation will be performed.
        doc
            Doctring specific to the ``param``.
        """

        def __init__(
            self,
            param: str,
            haystack: Optional[Set[str]] = None,
            doc: Optional[str] = None,
        ):
            if isinstance(haystack, str):
                haystack = (haystack,)
            elif haystack is not None and not isinstance(haystack, Iterable):
                raise TypeError(
                    f"Expected `haystack` for `{param}` to be either a "
                    f"`str` or a  `Sequence`, found `{type(haystack)}`."
                )

            self._param = param.lower()
            self._haystack = haystack if haystack is None else frozenset(haystack)
            self._query_doc_ = None if not doc else doc  # doc can also be `()`

        @property
        def haystack(self) -> Optional[FrozenSet[str]]:
            """Return the valid values for this parameter."""
            return self._haystack

        def __call__(self, needle: Optional[Set[str]]) -> Optional[Set[str]]:
            """
            Check whether ``needle`` is a valid value for :paramref:`_param`.

            Parameters
            ----------
            needle
                Needle to check.

            Returns
            -------
                `None` if the ``needle`` was `None`, otherwise the ``needle`` as a `str` set,
                optionally intersected with :paramref:`_haystack` if it is not `None`.

            Raises
            ------
            ValueError
                If :paramref:`_haystack` is not `None` and no valid values were found.
            """
            if needle is None:
                return None
            elif isinstance(needle, bool):
                needle = int(needle)
            elif isinstance(needle, Enum):
                needle = needle.value

            needle = _to_string_set(needle)
            if self.haystack is None:
                logging.debug(
                    f"Unable to perform parameter validation for `{self._param}`, haystack is empty"
                )
                return needle

            res = needle & self.haystack
            if not len(res):
                raise ValueError(
                    f"No valid options found for parameter `{self._param}` in: `{sorted(needle)}`.\n"
                    f"Valid options are: `{sorted(self.haystack)}`."
                )
            elif len(res) < len(needle):
                logging.warning(
                    f"Encountered invalid value(s) for `{self._param}`. "
                    f"Remaining values are `{sorted(res)}`"
                )

            return res

    def __new__(cls, clsname, superclasses, attributedict):  # noqa: D102
        from omnipath import options

        endpoint = attributedict.pop(
            "__endpoint__", clsname.lower().replace("validator", "")
        )
        use_default = True
        old_members = list(attributedict._member_names)
        old_values = cls._remove_old_members(attributedict)

        if endpoint is None:
            if len(old_members):
                raise ValueError(
                    "If `__endpoint__` is `None`, no members must be specified."
                )
        elif options.autoload:
            use_default = False
            with Options.from_options(
                options,
                num_retries=0,
                timeout=0.1,
                cache=None,
                progress_bar=False,
                chunk_size=2048,
            ) as opt:
                try:
                    logging.debug("Attempting to construct classes from the server")
                    res = Downloader(opt).maybe_download(
                        urljoin(urljoin(opt.url, f"{Key.QUERIES.s}/"), endpoint),
                        callback=json.load,
                        params={Key.FORMAT.s: Format.JSON.s},
                    )

                    if len({str(k).upper() for k in res.keys()}) != len(res):
                        raise RuntimeError(
                            f"After upper casing, key will not be unique: `{list(res.keys())}`."
                        )

                    for k, value in res.items():
                        if (
                            isinstance(value, str)
                            and "no such query available" in value
                        ):
                            raise RuntimeError(f"Invalid endpoint: `{endpoint}`.")

                        key = str(k).upper()
                        if value is None:
                            attributedict[key] = cls.Validator(param=k)
                        elif isinstance(value, Sequence):
                            attributedict[key] = cls.Validator(
                                param=k, haystack={str(v) for v in value}
                            )
                        else:
                            attributedict[key] = cls.Validator(param=k)
                except Exception as e:
                    logging.debug(
                        f"Unable to construct classes from the server. Reason: `{e}`"
                    )
                    use_default = True

        if use_default:
            if endpoint is not None:
                logging.debug(
                    f"Using predefined class: `{clsname}`."
                    + (
                        ""
                        if options.autoload
                        else " Consider specifying `omnipath.options.autoload = True`"
                    )
                )

            _ = cls._remove_old_members(attributedict)
            for k, v in zip(old_members, old_values):
                attributedict[k] = cls.Validator(param=k, doc=v)

        return super().__new__(cls, clsname, superclasses, attributedict)

    @classmethod
    def _remove_old_members(cls, attributedict) -> List[Any]:
        vals = []
        for k in list(attributedict._member_names):
            vals.append(attributedict.pop(k, None))
        attributedict._member_names = []

        return vals


class AutoValidator(NoValue):  # noqa: D101
    @property
    def valid(self) -> Optional[Set[str]]:
        """Return the valid values."""
        return self.value.haystack

    @property
    def annotation(self) -> Mapping[str, type]:
        """Return the type annotations."""
        return getattr(self, "__annotations__", {}).get(self.name, Any)

    @property
    def doc(self) -> Optional[str]:
        """Return the docstring."""
        return getattr(self.value, "_query_doc_", None)

    @d.dedent
    def __call__(self, value: Union[str, Sequence[str]]) -> Optional[Set[str]]:
        """%(validate)s"""  # noqa: D401
        return self.value(value)


class QueryValidatorMixin(AutoValidator, metaclass=ServerValidatorMeta):  # noqa: D101
    __endpoint__ = None


class EnzsubValidator(QueryValidatorMixin):  # noqa: D101
    DATABASES: Strseq_t = ()
    ENZYME_SUBSTRATE: Str_t = ()
    ENZYMES: Strseq_t = ()
    FIELDS: Strseq_t = ()
    FORMAT: Str_t = ()
    GENESYMBOLS: Bool_t = ()
    HEADER: Str_t = ()
    LICENSE: License_t = ()
    LIMIT: Int_t = ()
    MODIFICATION: Str_t = ()
    ORGANISMS: Organism_t = ()
    PARTNERS: Strseq_t = ()
    PASSWORD: Str_t = ()
    RESIDUES: Strseq_t = ()
    RESOURCES: Strseq_t = ()
    SUBSTRATES: Strseq_t = ()
    TYPES: Strseq_t = ()


class InteractionsValidator(QueryValidatorMixin):  # noqa: D101
    DATABASES: Strseq_t = ()
    DATASETS: Strseq_t = ()
    DIRECTED: Bool_t = ()
    DOROTHEA_LEVELS: Strseq_t = ()
    DOROTHEA_METHODS: Strseq_t = ()
    ENTITY_TYPES: Strseq_t = ()
    FIELDS: Strseq_t = ()
    FORMAT: Str_t = ()
    GENESYMBOLS: Bool_t = ()
    HEADER: Str_t = ()
    LICENSE: License_t = ()
    LIMIT: Int_t = ()
    ORGANISMS: Organism_t = ()
    PARTNERS: Strseq_t = ()
    PASSWORD: Str_t = ()
    RESOURCES: Strseq_t = ()
    SIGNED: Bool_t = ()
    SOURCE_TARGET: Bool_t = ()
    SOURCES: Strseq_t = ()
    TARGETS: Strseq_t = ()
    TFREGULONS_LEVELS: Strseq_t = ()
    TFREGULONS_METHODS: Strseq_t = ()
    TYPES: Strseq_t = ()


class ComplexesValidator(QueryValidatorMixin):  # noqa: D101
    DATABASES: Strseq_t = ()
    FIELDS: Strseq_t = ()
    FORMAT: Str_t = ()
    HEADER: Str_t = ()
    LICENSE: License_t = ()
    LIMIT: Int_t = ()
    PASSWORD: Str_t = ()
    PROTEINS: Strseq_t = ()
    RESOURCES: Strseq_t = ()


class AnnotationsValidator(QueryValidatorMixin):  # noqa: D101
    DATABASES: Strseq_t = ()
    ENTITY_TYPES: Strseq_t = ()
    FIELDS: Strseq_t = ()
    FORMAT: Str_t = ()
    GENESYMBOLS: Bool_t = ()
    HEADER: Str_t = ()
    LICENSE: License_t = ()
    LIMIT: Int_t = ()
    PASSWORD: Str_t = ()
    PROTEINS: Strseq_t = ()
    RESOURCES: Strseq_t = ()


class IntercellValidator(QueryValidatorMixin):  # noqa: D101
    ASPECT: Str_t = ()
    CATEGORIES: Str_t = ()
    CAUSALITY: Str_t = ()
    DATABASES: Strseq_t = ()
    ENTITY_TYPES: Str_t = ()
    FIELDS: Strseq_t = ()
    FORMAT: Str_t = ()
    HEADER: None_t = ()
    LICENSE: License_t = ()
    LIMIT: Int_t = ()
    PARENT: Str_t = ()
    PASSWORD: Str_t = ()
    PLASMA_MEMBRANE_PERIPHERAL: Bool_t = ()
    PLASMA_MEMBRANE_TRANSMEMBRANE: Bool_t = ()
    PMP: Bool_t = ()
    PMTM: Bool_t = ()
    PROTEINS: Strseq_t = ()
    REC: Bool_t = ()
    RECEIVER: Strseq_t = ()
    RESOURCES: Strseq_t = ()
    SCOPE: Str_t = ()
    SEC: Bool_t = ()
    SECRETED: Bool_t = ()
    SOURCE: Str_t = ()
    TOPOLOGY: Str_t = ()
    TRANS: Bool_t = ()
    TRANSMITTER: Bool_t = ()


__all__ = [
    EnzsubValidator,
    InteractionsValidator,
    ComplexesValidator,
    AnnotationsValidator,
    IntercellValidator,
]
