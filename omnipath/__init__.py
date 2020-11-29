from omnipath._core.cache import clear_cache
from omnipath._core.utils import options  # from_first in isort is important here
from omnipath._core.downloader._downloader import _get_server_version
import omnipath.requests as requests
import omnipath.constants as constants
import omnipath.interactions as interactions

__author__ = ", ".join(["Michal Klein", "Dénes Türei"])
__maintainer__ = ", ".join(["Michal Klein", "Dénes Türei"])
__version__ = "1.0.1"
__email__ = "turei.denes@gmail.com"

try:
    from importlib_metadata import version  # Python < 3.8
except ImportError:
    from importlib.metadata import version  # Python = 3.8

from packaging.version import parse

__full_version__ = parse(version(__name__))
__full_version__ = (
    f"{__version__}+{__full_version__.local}" if __full_version__.local else __version__
)
__server_version__ = _get_server_version(options)

del parse, version, _get_server_version
