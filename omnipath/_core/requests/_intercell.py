from typing import Any, Tuple, Mapping, Iterable, Optional, Sequence

import pandas as pd

from omnipath._core.query import QueryType
from omnipath._core.query._types import Strseq_t
from omnipath._core.requests._request import OrganismGenesymbolsRemover
from omnipath.constants._pkg_constants import Key, Format, final
from omnipath._core.query._query_validator import _to_string_set


@final
class Intercell(OrganismGenesymbolsRemover):
    """
    Request `intercell` annotations from [OmniPath]_.

    Imports the [OmniPath]_ inter-cellular communication role annotation
    `database <https://omnipathdb.org/intercell>`__.

    It provides information on the roles in inter-cellular signaling, e.g. if a protein is a ligand, a receptor,
    an extracellular matrix (ECM) component, etc.
    """

    __categorical__ = frozenset(
        {"category", "parent", "database", "scope", "aspect", "source", "entity_type"}
    )

    _query_type = QueryType.INTERCELL

    def _resource_filter(
        self,
        data: Mapping[str, Any],
        generic_categories: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> bool:
        return generic_categories is None or _to_string_set(
            data.get(Key.GENERIC_CATEGORIES.s, set())
        ) & _to_string_set(generic_categories)

    @classmethod
    def resources(cls, generic_categories: Strseq_t = None) -> Tuple[str]:
        """
        Return the resources falling into the specified generic categories.

        Parameters
        ----------
        generic_categories
            For valid options, see :paramref:`generic_categories`.

        Returns
        -------
        tuple
            The filtered resources according to ``generic_categories``.
        """
        if generic_categories is None:
            return super().resources()

        if isinstance(generic_categories, str):
            generic_categories = (generic_categories,)
        if not isinstance(generic_categories, (Sequence, Iterable)):
            raise TypeError(
                f"Expected generic categories to be a `str` or an `Iterable`, "
                f"found `{type(generic_categories).__name__}`."
            )

        if not len(generic_categories):
            raise ValueError("No generic categories have been selected.")

        return super().resources(**{Key.GENERIC_CATEGORIES.s: generic_categories})

    @classmethod
    def categories(cls) -> Tuple[str]:
        """Return categories from the `intercell` database."""
        return cls()._get_metadata(Key.CATEGORY.s)

    @classmethod
    def generic_categories(cls) -> Tuple[str]:
        """Return generic categories from the `intercell` database."""
        return cls()._get_metadata(Key.PARENT.s)

    def _get_metadata(self, col: Optional[str]) -> Tuple[str]:
        """Return unique summary data from column ``col``."""
        metadata = self._downloader.maybe_download(
            Key.INTERCELL_SUMMARY.s,
            params={Key.FORMAT.s: Format.JSON.s},
            callback=self._json_reader,
            is_final=False,
        )

        if col not in metadata.columns:
            raise KeyError(f"Column `{col}` not found in `{list(metadata.columns)}`.")

        return tuple(sorted(pd.unique(metadata[col].astype(str))))


__all__ = [Intercell]
