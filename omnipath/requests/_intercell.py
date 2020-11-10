from typing import Any, Tuple, Union, Mapping, Optional, Sequence

import pandas as pd

import omnipath as op
from omnipath._utils import _format_url
from omnipath.constants import QueryType, QueryParams
from omnipath.requests._request import CommonPostProcessor
from omnipath.constants._pkg_constants import _Format, _QueryTypeSummary


class Intercell(CommonPostProcessor):
    """
    Class capable of requesting `intercell` annotations from [OmniPath]_.

    Imports the [OmniPath]_ inter-cellular communication role annotation `database <https://omnipathdb.org/intercell>`.

    It provides information on the roles in inter-cellular signaling, e.g. if a protein is a ligand, a receptor,
    an extracellular matrix (ECM) component, etc.
    """

    __categorical__ = frozenset(
        {"category", "parent", "database", "scope", "aspect", "source", "entity_type"}
    )

    def __init__(self):
        super().__init__(QueryType.INTERCELL)

    def _resource_filter(
        self,
        data: Mapping[str, Any],
        generic_categories: Optional[Sequence[str]] = None,
        **kwargs,
    ) -> bool:
        return generic_categories is None or set(
            data.get("generic_categories", set())
        ) & set(generic_categories)

    def resources(
        self, generic_categories: Optional[Union[str, Sequence[str]]] = None
    ) -> Tuple[str]:
        """Return resources for this type of query."""
        if generic_categories is None:
            return super().resources(generic_categories=None)

        if isinstance(generic_categories, str):
            generic_categories = (generic_categories,)
        if not isinstance(generic_categories, Sequence):
            raise TypeError(
                f"Expected `generic_categories` to be a `Sequence`, "
                f"found `{type(generic_categories).__name__}`."
            )

        if not len(generic_categories):
            raise ValueError("No generic categories have been selected.")

        return super().resources(generic_categories=generic_categories)

    @property
    def categories(self) -> Tuple[str]:
        """Return categories from the `intercell` database from [OmniPath]_."""
        return self._get_metadata("category")

    @property
    def generic_categories(self) -> Tuple[str]:
        """Return generic categories from the `intercell` database from [OmniPath]_."""
        return self._get_metadata("parent")

    def _get_metadata(self, col: Optional[str]) -> Tuple[str]:
        """Return unique summary data from column ``col``."""
        metadata = self._downloader.maybe_download(
            _format_url(op.options.url, _QueryTypeSummary.INTERCELL),
            params={QueryParams.FORMAT.value: _Format.JSON.value},
            callback=self._json_reader,
        )

        if col not in metadata.columns:
            raise KeyError(f"Column `{col}` not found in `{list(metadata.columns)}`.")

        return tuple(sorted(pd.unique(metadata[col].astype(str))))


__all__ = [Intercell]
