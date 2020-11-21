from abc import ABCMeta
from enum import Enum, EnumMeta
from typing import Set, Tuple, Union, Optional, Sequence, FrozenSet

from inflect import engine

from omnipath.constants._constants import FormatterMeta, ErrorFormatter
from omnipath._core.query._query_validator import (
    EnzsubValidator,
    ComplexesValidator,
    IntercellValidator,
    AnnotationsValidator,
    InteractionsValidator,
)

_engine = engine()


def _get_synonyms(key: str) -> Tuple[str]:
    """
    Create synonyms for ``key``.

    This function creates just 2 synonyms - the singular and plural case of ``key``.

    Parameters
    ----------
    key
        Key for which to create the synonyms.

    Returns
    -------
    :class:`tuple`
        Synonyms for ``key``. User will be able to use these submitting requests.
    """
    if not isinstance(key, str):
        raise TypeError(f"Expected a `str`, found `{type(key)}`.")

    singular = _engine.singular_noun(key)
    singular = singular if isinstance(singular, str) else key

    plural = _engine.plural_noun(singular)
    if not isinstance(plural, str):
        plural = key + "s" if not key.endswith("s") else key

    return tuple(sorted({singular, plural}))


class SynonymizerMeta(EnumMeta, ABCMeta):  # noqa: D101
    def __new__(cls, clsname, superclasses, attributedict):  # noqa: D102
        validator = attributedict.get("__validator__", None)

        if validator is None:
            return super().__new__(cls, clsname, superclasses, attributedict)

        for k in list(validator):
            k = str(k.name)
            for i, synonym in enumerate(_get_synonyms(k.lower())):
                attributedict[f"{k}_{i}"] = synonym

        return super().__new__(cls, clsname, superclasses, attributedict)


class QueryMeta(SynonymizerMeta, FormatterMeta):  # noqa: D101
    pass


class Query(ErrorFormatter, Enum, metaclass=QueryMeta):  # noqa: D101
    @property
    def _query_name(self) -> str:
        """Convert the synonym to an actual query parameter name."""
        return "_".join(self.name.split("_")[:-1])

    @property
    def _delegate(self):
        """Delegate the validation."""
        return getattr(self.__validator__, self._query_name)

    @property
    def param(self) -> str:
        """Get the parameter name as required by the server."""
        return self._query_name.lower()

    @property
    def valid(self) -> Optional[FrozenSet[str]]:
        """Return the set of valid values for :paramref:`param`."""
        return self._delegate.valid

    @property
    def annotation(self) -> type:
        """Return type annotations for :paramref:`param`."""
        return self._delegate.annotation

    @property
    def doc(self) -> Optional[str]:
        """Return the docstring for :paramref:`param`."""
        return self._delegate.doc

    def __call__(
        self, value: Optional[Union[str, Sequence[str]]]
    ) -> Optional[Set[str]]:
        """%(validate)s"""  # noqa: D401
        return self._delegate(value)


class EnzsubQuery(Query):  # noqa: D101
    __validator__ = EnzsubValidator


class InteractionsQuery(Query):  # noqa: D101
    __validator__ = InteractionsValidator


class ComplexesQuery(Query):  # noqa: D101
    __validator__ = ComplexesValidator


class AnnotationsQuery(Query):  # noqa: D101
    __validator__ = AnnotationsValidator


class IntercellQuery(Query):  # noqa: D101
    __validator__ = IntercellValidator


class QueryType(Enum):  # noqa: D101
    ENZSUB = EnzsubQuery
    INTERACTIONS = InteractionsQuery
    COMPLEXES = ComplexesQuery
    ANNOTATIONS = AnnotationsQuery
    INTERCELL = IntercellQuery

    def __call__(
        self, value: Optional[Union[str, Sequence[str]]]
    ) -> Optional[Set[str]]:
        """%(validate)s"""  # noqa: D401
        return self.value(value)

    @property
    def endpoint(self) -> str:
        """Get the API endpoint for this type of query."""
        return self.name.lower()


__all__ = [
    EnzsubQuery,
    InteractionsQuery,
    ComplexesQuery,
    AnnotationsQuery,
    IntercellQuery,
]
