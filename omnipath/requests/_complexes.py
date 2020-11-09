from typing import Any, Mapping

from omnipath.constants import QueryType
from omnipath.requests._request import CommonPostProcessor


class Complexes(CommonPostProcessor):
    """Class capable of requesting information about protein complexes from [OmniPath]_."""

    __string__ = frozenset(
        {
            "name",
            "components",
            "components_genesymbols",
            "stoichiometry",
            "references",
            "identifiers",
        }
    )
    __categorical__ = frozenset({"sources"})

    def __init__(self):
        super().__init__(QueryType.COMPLEXES)

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True


__all__ = [Complexes]
