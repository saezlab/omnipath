from io import BytesIO
from copy import copy
from typing import Any, Mapping, Callable, Optional
from hashlib import md5
from urllib.parse import urljoin
import json
import logging

from requests import Request, Session, PreparedRequest
from tqdm.auto import tqdm
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

from omnipath._core.utils._options import Options
from omnipath.constants._pkg_constants import (
    UNKNOWN_SERVER_VERSION,
    Key,
    Format,
    Endpoint,
)


class Downloader:
    """
    Class which performs a GET request to the server in order to retrieve some remote resources.

    Also implements other behavior, such as retrying after some status codes.

    Parameters
    ----------
    opts
        Options. If `None`, :attr:`omnipath.options` are used.
    """

    def __init__(self, opts: Optional[Options] = None):
        if opts is None:
            from omnipath import options as opts

        if not isinstance(opts, Options):
            raise TypeError(
                f"Expected `opts` to be of type `Options`, found {type(opts).__name__}."
            )

        self._session = Session()
        self._options = copy(opts)  # this does not copy MemoryCache

        if self._options.num_retries > 0:
            adapter = HTTPAdapter(
                max_retries=Retry(
                    total=self._options.num_retries,
                    redirect=5,
                    allowed_methods=["HEAD", "GET", "OPTIONS"],
                    status_forcelist=[413, 429, 500, 502, 503, 504],
                    backoff_factor=1,
                )
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

        logging.debug(f"Initialized `{self}`")

    @property
    def resources(self) -> Mapping[str, Mapping[str, Any]]:
        """Return the resources."""
        logging.debug("Fetching resources")
        return self.maybe_download(
            Endpoint.RESOURCES.s,
            params={Key.FORMAT.s: Format.JSON.s},
            callback=json.load,
            is_final=False,
        )

    def maybe_download(
        self,
        url: str,
        callback: Callable[[BytesIO], Any],
        params: Optional[Mapping[str, str]] = None,
        cache: bool = True,
        is_final: bool = True,
        **_,
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
        is_final
            Whether ``url`` is final or should be prefixed with :paramref:`_options.url`.

        Returns
        -------
        :class:`typing.Any`
            The result of applying ``callback`` on the maybe downloaded data.
        """
        if not callable(callback):
            raise TypeError(
                f"Expected `callback` to be `callable`, found `{type(callback).__name__}`."
            )

        if not is_final:
            url = urljoin(self._options.url, url)

        req = self._session.prepare_request(
            Request(
                "GET",
                url,
                params=params,
                headers={"User-agent": "omnipathdb-user"},
            )
        )
        key = md5(bytes(req.url, encoding="utf-8")).hexdigest()

        if key in self._options.cache:
            logging.debug(f"Found data in cache `{self._options.cache}[{key!r}]`")
            res = self._options.cache[key]
        else:
            res = callback(self._download(req))
            if cache:
                logging.debug(f"Caching result to `{self._options.cache}[{key!r}]`")
                self._options.cache[key] = res
            else:
                logging.debug("Not caching the results")

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
        logging.info(f"Downloading data from `{req.url}`")

        handle = BytesIO()
        with self._session.send(
            req, stream=True, timeout=self._options.timeout
        ) as resp:
            resp.raise_for_status()
            total = resp.headers.get("content-length", None)

            with tqdm(
                unit="B",
                unit_scale=True,
                miniters=1,
                unit_divisor=1024,
                total=total if total is None else int(total),
                disable=not self._options.progress_bar,
            ) as t:
                for chunk in resp.iter_content(chunk_size=self._options.chunk_size):
                    t.update(len(chunk))
                    handle.write(chunk)

                handle.flush()
                handle.seek(0)

        return handle

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}[options={self._options}]>"

    def __repr__(self) -> str:
        return str(self)


def _get_server_version(options: Options) -> str:
    """Try and get the server version."""
    import re

    def callback(fp: BytesIO) -> str:
        """Parse the version."""
        return re.findall(
            r"\d+\.\d+.\d+", fp.getvalue().decode("utf-8"), flags=re.IGNORECASE
        )[0]

    try:
        if not options.autoload:
            raise ValueError("Autoload is disabled.")

        with Options.from_options(
            options,
            num_retries=0,
            timeout=0.1,
            cache=None,
            progress_bar=False,
            chunk_size=1024,
        ) as opt:
            return Downloader(opt).maybe_download(
                Endpoint.ABOUT.s,
                callback,
                params={Key.FORMAT.s: Format.TEXT.s},
                cache=False,
                is_final=False,
            )
    except Exception as e:
        logging.debug(f"Unable to get server version. Reason: `{e}`")

        return UNKNOWN_SERVER_VERSION
