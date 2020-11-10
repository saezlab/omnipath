import json
from io import BytesIO
from typing import Any, Union, Mapping, Callable, Optional
from hashlib import md5
from functools import lru_cache
from urllib.parse import urljoin

from requests import Request, Session, PreparedRequest
from tqdm.auto import tqdm
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

import pandas as pd

import omnipath as op
from omnipath._options import Options
from omnipath.constants import QueryType, QueryParams
from omnipath.constants._pkg_constants import (
    _Format,
    _OmniPathEndpoint,
    _QueryTypeSummary,
)


class Downloader:
    """
    Class which performs a GET request to the server in order to retrieve some remote resources.

    Also implements other behavior, such as retrying after some status codes.
    """

    def __init__(self):
        self._session = Session()
        self._cacher = op.options.cache

        if op.options.num_retries > 0:
            adapter = HTTPAdapter(
                max_retries=Retry(
                    total=op.options.num_retries,
                    redirect=5,
                    method_whitelist=["HEAD", "GET", "OPTIONS"],
                    status_forcelist=[413, 429, 500, 502, 503, 504],
                    backoff_factor=1,
                )
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

    @property
    def resources(self) -> Mapping[str, Mapping[str, Any]]:
        """Return resources under :attr`omnipath.options.url`."""
        return self.maybe_download(
            urljoin(op.options.url, _OmniPathEndpoint.RESOURCES.value),
            callback=json.load,
        )

    def maybe_download(
        self,
        url: str,
        callback: Callable[[BytesIO], Any],
        params: Optional[Mapping[str, str]] = None,
        cache: bool = True,
        **kwargs,
    ) -> Any:
        """
        Fetch the data from the cache, if present, or download them from the ``url``.

        The key, under which is the download result saved, is the MD5 hash of the ``url``, including the ``params``.

        Parameters
        ----------
        url
            URL that is used to access the remote resources if the data is not found in the cache.
        callback
            Function applied on the downloaded data. Usually, this will return either a :class:`pandas.DataFrame`
            or a :class:`dict`.
        params
            Parameters of the `GET` request.
        cache
            Whether to save the files to the cache or not.
        **kwargs
            Keyword arguments for :class`requests.Request`.

        Returns
        -------
        :class:`typing.Any`
            The result of applying ``callback`` on the maybe downloaded data.
        """
        # TODO: more informative key?
        if callback is not None and not callable(callback):
            raise TypeError(
                f"Expected `callback` to be either `None` or `callable`, "
                f"found `{type(callback).__name__}`."
            )

        req = self._session.prepare_request(
            Request(
                "GET",
                url,
                params=params,
                headers={"User-agent": "omnipathdb-user"},
                **kwargs,
            )
        )
        key = md5(bytes(req.url, encoding="utf-8")).hexdigest()

        if key in self._cacher:
            res = self._cacher[key]
        else:
            res = callback(self._download(req))
            if cache:
                self._cacher[key] = res

        return res

    def _download(self, req: PreparedRequest) -> BytesIO:
        """
        Request the remote resources.

        Parameters
        ----------
        req
            `GET` request to perform.

        Returns
        -------
        :class:`io.BytesIO`
            File-like object containing the data. Usually a json- or csv-like data is present inside.
        """
        handle = BytesIO()

        with self._session.send(req, stream=True, timeout=op.options.timeout) as resp:
            resp.raise_for_status()

            with tqdm(
                unit="B",
                unit_scale=True,
                miniters=1,
                unit_divisor=1024,
                total=len(resp.content),
                disable=not op.options.progress_bar,
            ) as t:
                for chunk in resp.iter_content(chunk_size=op.options.chunk_size):
                    handle.write(chunk)
                    t.update(len(chunk))

                handle.flush()
                handle.seek(0)

        return handle


def _strip_resource_labels(df: pd.DataFrame, inplace: bool = True):
    # TODO
    pass


def _format_url(
    url: str, query: Union[QueryType, _QueryTypeSummary, _OmniPathEndpoint]
) -> str:
    """
    Format the ``url`` according to the ``query``.

    Parameters
    ----------
    url
        URL to format.
    query
        Type of query to be performed.

    Returns
    -------
    str
        The formatted URL.
    """
    if not isinstance(query, (QueryType, _QueryTypeSummary, _OmniPathEndpoint)):
        raise TypeError(
            f"Expected `query` to be either `QueryType`, `_QueryTypeSummary` or `_OmniPathEndpoint` "
            f"found `{type(query).__name__}`."
        )

    return urljoin(url, query.value)


@lru_cache()
def _get_server_version() -> str:
    import re

    def callback(fp: BytesIO) -> str:
        return re.findall(
            r"\d+\.\d+.\d+", fp.getvalue().decode("utf-8"), flags=re.IGNORECASE
        )[0]

    try:
        with Options(
            url=op.options.url,
            password=op.options.password,
            license=op.options.license,
            num_retries=0,
            timeout=0.1,
            cache=None,
            progress_bar=False,
            chunk_size=1024,
        ):
            return Downloader().maybe_download(
                _format_url(op.options.url, _OmniPathEndpoint.ABOUT),
                callback,
                params={QueryParams.FORMAT.value: _Format.TEXT.value},
                cache=False,
            )
    except Exception:
        return "UNKNOWN"
