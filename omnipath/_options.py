import configparser
from copy import copy
from typing import Union, ClassVar, NoReturn, Optional
from pathlib import Path
from urllib.parse import urlparse

import attr

from omnipath._cache import Cache, FileCache, MemoryCache
from omnipath.constants import License


def _is_positive(_instance, attribute: attr.Attribute, value: int) -> NoReturn:
    """Check whether the ``value`` is positive."""
    if value <= 0:
        raise ValueError(
            f"Expected `{attribute.name}` to be positive, found `{value}`."
        )


def _is_non_negative(_instance, attribute: attr.Attribute, value: int) -> NoReturn:
    """Check whether the ``value`` is positive."""
    if value < 0:
        raise ValueError(
            f"Expected `{attribute.name}` to be non-negative, found `{value}`."
        )


def _is_valid_url(_instance, _attribute: attr.Attribute, value: str) -> NoReturn:
    """Check whether the ``value`` forms a valid URL."""
    pr = urlparse(value)

    if not pr.scheme or not pr.netloc:
        raise ValueError(f"Invalid URL `{value}`.")


def _cache_converter(value: Optional[Union[str, Path]]) -> Cache:
    """Convert ``value`` to :class:`omnipath._cache.Cache`."""
    if value is None:
        return DefaultOptions.MEM_CACHE

    return FileCache(value)


class DefaultOptions:  #: noqa: D101
    URL: str = "https://omnipathdb.org"
    LICENSE: License = License.ACADEMIC
    NUM_RETRIES: int = 3
    TIMEOUT: int = 5
    CHUNK_SIZE: int = 8196
    CACHE_DIR: Path = Path.home() / ".cache" / "omnipathdb"
    MEM_CACHE = MemoryCache()
    PROGRESS_BAR: bool = True


@attr.s
class Options:
    """:mod:`omnipath` options."""

    config_path: ClassVar[Path] = Path.home() / ".config" / "omnipathdb.ini"

    url: str = attr.ib(
        default=DefaultOptions.URL,
        validator=[attr.validators.instance_of(str), _is_valid_url],
        on_setattr=attr.setters.validate,
    )
    license: License = attr.ib(
        default=License.ACADEMIC, converter=License, on_setattr=attr.setters.convert
    )
    password: Optional[str] = attr.ib(
        default=None,
        repr=False,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
        on_setattr=attr.setters.validate,
    )

    cache: Cache = attr.ib(
        default=DefaultOptions.CACHE_DIR,
        converter=_cache_converter,
        kw_only=True,
        on_setattr=attr.setters.convert,
    )

    num_retries: int = attr.ib(
        default=DefaultOptions.NUM_RETRIES,
        validator=[attr.validators.instance_of(int), _is_non_negative],
        on_setattr=attr.setters.validate,
    )
    timeout: Union[int, float] = attr.ib(
        default=DefaultOptions.TIMEOUT,
        validator=[attr.validators.instance_of((int, float)), _is_positive],
        on_setattr=attr.setters.validate,
    )
    chunk_size: int = attr.ib(
        default=DefaultOptions.CHUNK_SIZE,
        validator=[attr.validators.instance_of(int), _is_positive],
        on_setattr=attr.setters.validate,
    )

    progress_bar: bool = attr.ib(
        default=True,
        repr=False,
        validator=attr.validators.instance_of(bool),
        on_setattr=attr.setters.validate,
    )

    def _create_config(self):
        config = configparser.ConfigParser()
        # do not save the password
        config[self.url] = {
            "license": self.license.value,
            "cache_dir": str(self.cache.path),
            "num_retries": self.num_retries,
            "timeout": self.timeout,
            "chunk_size": self.chunk_size,
            "progress_bar": self.progress_bar,
        }

        return config

    @classmethod
    def from_config(cls) -> "Options":
        """Return the options from a configuration file."""
        if not cls.config_path.is_file():
            return cls().write()

        section = DefaultOptions.URL

        config = configparser.ConfigParser()
        config.read(cls.config_path)

        cache = config.get(section, "cache_dir", fallback=DefaultOptions.CACHE_DIR)
        if cache == "None":
            cache = None

        return cls(
            url=section,
            license=License(
                config.get(section, "license", fallback=DefaultOptions.LICENSE)
            ),
            num_retries=config.getint(
                section, "num_retries", fallback=DefaultOptions.NUM_RETRIES
            ),
            timeout=config.getint(section, "timeout", fallback=DefaultOptions.TIMEOUT),
            chunk_size=config.getint(
                section, "chunk_size", fallback=DefaultOptions.CHUNK_SIZE
            ),
            progress_bar=config.getint(
                section, "progress_bar", fallback=DefaultOptions.PROGRESS_BAR
            ),
            cache=cache,
        )

    def write(self) -> NoReturn:
        """Write the current options to a configuration file."""
        self.config_path.parent.mkdir(exist_ok=True)

        config = self._create_config()
        with open(self.config_path, "w") as fout:
            config.write(fout)

        return self

    def __enter__(self):
        import omnipath as op

        self._previous_options = copy(op.options)
        op.options = self

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import omnipath as op

        op.options = self._previous_options


__all__ = [Options]
