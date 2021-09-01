from abc import ABC, abstractmethod
from copy import copy
from shutil import rmtree
from typing import Any, Union, Optional
from pathlib import Path
import os
import pickle

import pandas as pd


def _is_empty(data: Optional[pd.DataFrame]) -> bool:
    return data is None or (isinstance(data, pd.DataFrame) and not len(data))


class Cache(ABC):
    """
    Abstract class which defines the caching interface.

    Empty values (`None` or an empty :class:`pandas.DataFrame`) will not be saved in the cache.
    """

    @abstractmethod
    def __getitem__(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def __setitem__(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def clear(self) -> None:  # noqa: D102
        pass

    @property
    @abstractmethod
    def path(self) -> Optional[Union[str, Path]]:  # noqa: D102
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __repr__(self) -> str:
        return str(self)


class FileCache(Cache):
    """
    Cache which persists the data into :mod:`pickle` files.

    Parameters
    ----------
    path
        Path to a directory where the files will be stored.
    """

    _suffix = ".pickle"

    def __init__(self, path: Union[str, Path]):
        if not isinstance(path, (str, Path)):
            raise TypeError(
                f"Expected `path` to be either `str` or `pathlib.Path`, "
                f"found `{type(path).__name__}`."
            )
        if not str(path):
            raise ValueError("Empty cache path.")

        self._cache_dir = Path(path)

    def __contains__(self, key: str) -> bool:
        if not key.endswith(self._suffix):
            key += self._suffix

        return (self._cache_dir / key).is_file()

    def __setitem__(self, key: str, value: Any) -> None:
        if _is_empty(value):
            return
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        fname = str(key)
        if not fname.endswith(self._suffix):
            fname += self._suffix

        with open(self._cache_dir / fname, "wb") as fout:
            pickle.dump(value, fout)

    def __getitem__(self, key: str) -> Any:
        if not key.endswith(self._suffix):
            key += self._suffix

        if not (self._cache_dir / key).is_file():
            raise KeyError(self._cache_dir / key)

        with open(self._cache_dir / key, "rb") as fin:
            return pickle.load(fin)

    def __len__(self) -> int:
        return (
            len([f for f in os.listdir(self.path) if str(f).endswith(self._suffix)])
            if self.path.is_dir()
            else 0
        )

    @property
    def path(self) -> Path:
        """Return the directory where the cache files are stored."""
        return self._cache_dir

    def clear(self) -> None:
        """Remove all files and the directory under :attr:`path`."""
        if self._cache_dir.is_dir():
            rmtree(self._cache_dir)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}[size={len(self)}, path={str(self.path)!r}]>"


class MemoryCache(dict, Cache):
    """
    Cache which persists the data into the memory.

    Objects stored in the cache are copied using :func:`copy.copy``.
    """

    @property
    def path(self) -> Optional[str]:
        """Return `'memory'`."""
        return "memory"

    def __setitem__(self, key: str, value: Any) -> None:
        if _is_empty(value):
            return
        # the value is usually a dataframe (copy for safety)
        return super().__setitem__(key, copy(value))

    def __getitem__(self, key: str) -> Any:
        return copy(super().__getitem__(key))

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}[size={len(self)}]>"

    def __repr__(self) -> str:
        return str(self)

    def __copy__(self) -> "MemoryCache":
        return self

    def copy(self) -> "MemoryCache":
        """Return self."""
        return self


class NoopCache(MemoryCache):
    """Cache which doesn't save anything."""

    @property
    def path(self) -> Optional[str]:
        """Return `None`."""
        return None

    def __setitem__(self, key: str, value: Any) -> None:
        pass

    def __str__(self):
        return f"<{self.__class__.__name__}>"


def clear_cache() -> None:
    """Remove all cached data from :attr:`omnipath.options.cache`."""
    from omnipath import options

    options.cache.clear()


__all__ = [clear_cache]
