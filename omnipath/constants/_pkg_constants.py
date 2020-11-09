from enum import Enum, unique

from omnipath.constants import QueryType


class _DefaultField(Enum):  # noqa: D101
    ENZSUB = ("sources", "references", "curation_effort")
    INTERACTIONS = ("sources", "references", "curation_effort")


@unique
class _OmniPathEndpoint(Enum):
    RESOURCES = "resources"
    DATASETS = "datasets"
    ABOUT = "about"


@unique
class _Format(Enum):
    JSON = "json"
    TABLE = "tab"
    TEXT = "text"
    TSV = "tsv"


@unique
class _QueryTypeSummary(Enum):  # noqa: D101
    INTERCELL = f"{QueryType.INTERCELL.value}_summary"
