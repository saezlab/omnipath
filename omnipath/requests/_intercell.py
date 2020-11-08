from typing import Any, Tuple, Mapping, Optional, Sequence

from cached_property import cached_property

import pandas as pd

from omnipath._utils import _format_url
from omnipath._options import options
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

    @cached_property
    def _summary(self) -> pd.DataFrame:
        """Retrieve `intercell` summary data."""
        return self._downloader.maybe_download(
            _format_url(options.url, _QueryTypeSummary.INTERCELL),
            params={QueryParams.FORMAT.value: _Format.JSON.value},
            callback=self._json_reader,
        )

    def _get_metadata(self, col: str) -> Tuple[str]:
        """Return unique summary data from column ``col``."""
        res = self._summary

        if col not in res.columns:
            raise KeyError(f"No column named `{col}` in `{list(res.columns)}`.")

        return tuple(pd.unique(res[col].astype(str)))

    @cached_property
    def categories(self) -> Tuple[str]:
        """Return categories from the `intercell` database of [OmniPath]_."""
        return self._get_metadata("category")

    @cached_property
    def generic_categories(self):
        """Return generic categories from the `intercell` database of [OmniPath]_."""
        return self._get_metadata("parent")

    def filter(self) -> pd.DataFrame:  # noqa: D102
        raise NotImplementedError()
