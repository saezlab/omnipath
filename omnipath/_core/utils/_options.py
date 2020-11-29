from typing import Union, ClassVar, NoReturn, Optional
from pathlib import Path
from urllib.parse import urlparse
import configparser

import attr

from omnipath.constants import License
from omnipath._core.cache._cache import Cache, FileCache, MemoryCache
from omnipath.constants._pkg_constants import DEFAULT_OPTIONS


def _is_positive(_instance, attribute: attr.Attribute, value: int) -> NoReturn:
    """Check whether the ``value`` is positive."""
    if value <= 0:
        raise ValueError(
            f"Expected `{attribute.name}` to be positive, found `{value}`."
        )


def _is_non_negative(_instance, attribute: attr.Attribute, value: int) -> NoReturn:
    """Check whether the ``value`` is non-negative."""
    if value < 0:
        raise ValueError(
            f"Expected `{attribute.name}` to be non-negative, found `{value}`."
        )


def _is_valid_url(_instance, _attribute: attr.Attribute, value: str) -> NoReturn:
    """Check whether the ``value`` forms a valid URL."""
    pr = urlparse(value)

    if not pr.scheme or not pr.netloc:
        raise ValueError(f"Invalid URL: `{value}`.")


def _cache_converter(value: Optional[Union[str, Path, Cache]]) -> Cache:
    """Convert ``value`` to :class:`omnipath._core.cache.Cache`."""
    if isinstance(value, Cache):
        return value

    if value is None:
        return MemoryCache()

    return FileCache(value)


@attr.s
class Options:
    """
    Class defining various :mod:`omnipath` options.

    Parameters
    ----------
    url
        URL of the web service.
    license
        License to use when fetching the data.
    password
        Password used when performing requests.
    cache
        Type of a cache. If `None`, cache files to memory. If a :class:`str`, persist files into a directory.
    autoload
        Whether to contant the server at ``url`` during import to get the server version and the most up-to-date
        query paramters and their valid options.
    convert_dtypes
        Whether to convert the data types of the resulting :class:`pandas.DataFrame`.
    num_retries
        Number of retries before giving up.
    timeout
        Timout in seconds when awaiting response.
    chunk_size
        Size in bytes in which to read the data.
    progress_bar
        Whether to show the progress bar when downloading data.
    """

    config_path: ClassVar[Path] = Path.home() / ".config" / "omnipathdb.ini"

    url: str = attr.ib(
        default=DEFAULT_OPTIONS.url,
        validator=[attr.validators.instance_of(str), _is_valid_url],
        on_setattr=attr.setters.validate,
    )
    license: License = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of((str, License))),
        converter=(lambda l: None if l is None else License(l)),
        on_setattr=attr.setters.convert,
    )
    password: Optional[str] = attr.ib(
        default=None,
        repr=False,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
        on_setattr=attr.setters.validate,
    )

    cache: Cache = attr.ib(
        default=DEFAULT_OPTIONS.cache_dir,
        converter=_cache_converter,
        kw_only=True,
        on_setattr=attr.setters.convert,
    )
    autoload: bool = attr.ib(
        default=DEFAULT_OPTIONS.autoload,
        validator=attr.validators.instance_of(bool),
        on_setattr=attr.setters.validate,
    )
    convert_dtypes: bool = attr.ib(
        default=DEFAULT_OPTIONS.convert_dtypes,
        validator=attr.validators.instance_of(bool),
        on_setattr=attr.setters.validate,
    )

    num_retries: int = attr.ib(
        default=DEFAULT_OPTIONS.num_retries,
        validator=[attr.validators.instance_of(int), _is_non_negative],
        on_setattr=attr.setters.validate,
    )
    timeout: Union[int, float] = attr.ib(
        default=DEFAULT_OPTIONS.timeout,
        validator=[attr.validators.instance_of((int, float)), _is_positive],
        on_setattr=attr.setters.validate,
    )
    chunk_size: int = attr.ib(
        default=DEFAULT_OPTIONS.chunk_size,
        validator=[attr.validators.instance_of(int), _is_positive],
        on_setattr=attr.setters.validate,
    )

    progress_bar: bool = attr.ib(
        default=True,
        repr=False,
        validator=attr.validators.instance_of(bool),
        on_setattr=attr.setters.validate,
    )

    def _create_config(self, section: Optional[str] = None):
        section = self.url if section is None else section
        _is_valid_url(None, None, section)
        config = configparser.ConfigParser()
        # do not save the password
        config[section] = {
            "license": str(None if self.license is None else self.license.value),
            "cache_dir": str(self.cache.path),
            "autoload": self.autoload,
            "convert_dtypes": self.convert_dtypes,
            "num_retries": self.num_retries,
            "timeout": self.timeout,
            "chunk_size": self.chunk_size,
            "progress_bar": self.progress_bar,
        }

        return config

    @classmethod
    def from_config(cls, section: Optional[str] = None) -> "Options":
        """
        Return the options from a configuration file.

        Parameters
        ----------
        section
            Section of the `.ini` file from which to create the options. It corresponds to the URL of the server.
            If `None`, use default URL.

        Returns
        -------
        :class:`omnipath._cores.utils.Options`
            The options.
        """
        if not cls.config_path.is_file():
            return cls().write()

        config = configparser.ConfigParser(default_section=DEFAULT_OPTIONS.url)
        config.read(cls.config_path)

        section = DEFAULT_OPTIONS.url if section is None else section
        _is_valid_url(None, None, section)
        _ = config.get(section, "cache_dir")

        cache = config.get(section, "cache_dir", fallback=DEFAULT_OPTIONS.cache_dir)
        cache = None if cache == "None" else cache
        license = config.get(section, "license", fallback=DEFAULT_OPTIONS.license)
        license = None if license == "None" else License(license)

        return cls(
            url=section,
            license=license,
            num_retries=config.getint(
                section, "num_retries", fallback=DEFAULT_OPTIONS.num_retries
            ),
            timeout=config.getfloat(
                section, "timeout", fallback=DEFAULT_OPTIONS.timeout
            ),
            chunk_size=config.getint(
                section, "chunk_size", fallback=DEFAULT_OPTIONS.chunk_size
            ),
            progress_bar=config.getboolean(
                section, "progress_bar", fallback=DEFAULT_OPTIONS.progress_bar
            ),
            autoload=config.getboolean(
                section, "autoload", fallback=DEFAULT_OPTIONS.autoload
            ),
            convert_dtypes=config.getboolean(
                section, "convert_dtypes", fallback=DEFAULT_OPTIONS.convert_dtypes
            ),
            cache=cache,
        )

    @classmethod
    def from_options(cls, options: "Options", **kwargs) -> "Options":
        """
        Create new options from previous options.

        Parameters
        ----------
        options
            Options from which to create new ones.
        **kwargs
            Keyword arguments overriding attributes from ``options``.

        Returns
        -------
            The newly created option.
        """
        if not isinstance(options, Options):
            raise TypeError(
                f"Expected `options` to be of type `Options`, found `{type(options)}`."
            )

        kwargs = {k: v for k, v in kwargs.items() if hasattr(options, k)}

        return cls(**{**options.__dict__, **kwargs})

    def write(self, section: Optional[str] = None) -> NoReturn:
        """Write the current options to a configuration file."""
        self.config_path.parent.mkdir(exist_ok=True)

        with open(self.config_path, "w") as fout:
            self._create_config(section).write(fout)

        return self

    def __enter__(self):
        return self.from_options(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


options = Options.from_config()


__all__ = [options, Options]
