import omnipath.requests as requests
import omnipath.constants as constants
import omnipath.requests.utils as utils
import omnipath.requests.interactions as interactions
from omnipath._cache import clear_cache
from omnipath._utils import _get_server_version
from omnipath._options import Options

options = Options.from_config()
__server_version__ = _get_server_version()

del Options
del _get_server_version
