from pathlib import Path

from omnipath.constants import License, Organism
from omnipath.constants._constants import PrettyEnumMixin


class DEFAULT_FIELD(PrettyEnumMixin):
    """Default values for ``field`` parameter."""

    ENZSUB = ("sources", "references", "curation_effort")
    INTERACTIONS = ("sources", "references", "curation_effort")


class Format(PrettyEnumMixin):
    """Response format types."""

    JSON = "json"
    TABLE = "tab"
    TEXT = "text"
    TSV = "tsv"


class DEFAULT_OPTIONS:
    """Default options for :attr:`omnipath.options`."""

    url: str = "https://omnipathdb.org"
    license: License = License.ACADEMIC
    num_retries: int = 3
    timeout: int = 600
    chunk_size: int = 8196
    cache_dir: Path = Path.home() / ".cache" / "omnipathdb"
    mem_cache = None
    progress_bar: bool = True
    autoload: bool = True
    convert_dtypes: bool = True


class Endpoint(PrettyEnumMixin):
    """Endpoints of :attr:`omnipath.options.url` that are sometimes accessed."""

    RESOURCES = "resources"
    ABOUT = "about"
    INFO = "info"


# TODO: refactor me
class Key(PrettyEnumMixin):  # noqa: D101
    ORGANISM = "organism"
    GENESYMBOLS = "genesymbols"
    FORMAT = "format"
    DATASETS = "datasets"
    LICENSE = "license"
    QUERIES = "queries"

    INTERCELL_SUMMARY = "intercell_summary"
    GENERIC_CATEGORIES = "generic_categories"
    CATEGORY = "category"
    PARENT = "parent"


DEFAULT_ORGANISM = Organism.HUMAN  # default organism to access
DEFAULT_FORMAT = Format.TSV
UNKNOWN_SERVER_VERSION = (
    "UNKNOWN"  # server version to save under __server_version__ if we can't get it
)
