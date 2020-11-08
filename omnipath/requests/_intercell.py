from typing import Any, Tuple, Mapping, Optional, Sequence

from cached_property import cached_property

import pandas as pd

from omnipath._utils import _format_url
from omnipath._options import options
from omnipath.constants import QueryType, QueryParams
from omnipath.requests._request import CommonPostProcessor
from omnipath.constants._pkg_constants import _Format, _QueryTypeSummary


class Intercell(CommonPostProcessor):
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
        return self._downloader.maybe_download(
            _format_url(options.url, _QueryTypeSummary.INTERCELL),
            params={QueryParams.FORMAT.value: _Format.JSON.value},
            callback=self._tsv_reader,
        )

    def _get_metadata(self, col: str) -> Tuple[str]:
        res = self._summary

        if col not in res.columns:
            raise KeyError(f"No column named `{col}` in `{list(res.columns)}`.")

        return tuple(pd.unique(res[col].astype(str)))

    @cached_property
    def categories(self) -> Tuple[str]:
        return self._get_metadata("category")

    @cached_property
    def generic_categories(self):
        return self._get_metadata("parent")

    def filter(self) -> pd.DataFrame:
        raise NotImplementedError()
