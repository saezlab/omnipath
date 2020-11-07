from typing import Union, Optional
from urllib.parse import urlparse

from dataclass_property import dataclass, field_property

from omnipath.constants import License

# TODO:
# - add more docstirngs from OmnipathR
# - maybe remove dataclass_property


@dataclass(repr=True, unsafe_hash=False, frozen=False)
class Options:
    """
    These options describe the default settings for :mod:`omnipath` so you do not need to pass these parameters \
    at each function call.

    Currently the only option useful for the public web service at
    `omnipathdb.org <https://omnipathdb.org/>`__ is :paramref:`license`.
    """

    @field_property(default="https://omnipathdb.org/")
    def url(self) -> str:  # noqa: D102
        return self._url

    @url.setter
    def url(self, url: str):
        if not isinstance(url, str):
            raise TypeError(f"Expected a `str`, found `{type(url).__name__}`.")

        pr = urlparse(url)
        if not pr.scheme or not pr.netloc:
            raise ValueError(f"Invalid URL: `{url!r}`.")

        self._url = url

    @field_property(default=License.ACADEMIC)
    def license(self) -> License:  # noqa: D102
        return self._license

    @license.setter
    def license(self, license: Union[License, str]):
        self._license = License(license)

    password: Optional[str] = None
    print_urls: bool = False


__all__ = [Options]
