from io import BytesIO, StringIO
from urllib.parse import urljoin
import logging

import pytest

import numpy as np
import pandas as pd

from omnipath import options as opt
from omnipath._core.utils._options import Options
from omnipath.constants._pkg_constants import UNKNOWN_SERVER_VERSION, Endpoint
from omnipath._core.downloader._downloader import Downloader, _get_server_version


class TestDownloader:
    def test_options_wrong_type(self):
        with pytest.raises(TypeError):
            Downloader("foobar")

    def test_str_repr(self, options: Options):
        d = Downloader(options)

        assert str(d) == f"<{d.__class__.__name__}[options={options}]>"
        assert repr(d) == f"<{d.__class__.__name__}[options={options}]>"

    def test_initialize_local_options(self, options: Options):
        options.password = "foo"
        options.timeout = 1337
        d = Downloader(options)

        assert d._options is not options
        assert str(d._options) == str(options)
        assert str(d._options) != str(opt)

        options.password = "bar"
        assert d._options.password == "foo"

    def test_initialize_global_options(self):
        d = Downloader()

        assert d._options is not opt
        assert str(d._options) == str(opt)

    def test_resources_cached_values(self, downloader: Downloader, requests_mock):
        data = {"foo": "bar", "42": 1337}
        requests_mock.register_uri(
            "GET", urljoin(downloader._options.url, Endpoint.RESOURCES.s), json=data
        )

        assert downloader.resources == data
        assert requests_mock.called_once

        assert downloader.resources == data
        assert requests_mock.called_once

    def test_resources_no_cached_values(self, downloader: Downloader, requests_mock):
        data = {"foo": "bar", "42": 1337}
        requests_mock.register_uri(
            "GET", urljoin(downloader._options.url, Endpoint.RESOURCES.s), json=data
        )

        assert downloader.resources == data
        assert requests_mock.called_once

        downloader._options.cache.clear()

        assert downloader.resources == data
        assert len(requests_mock.request_history) == 2

    def test_maybe_download_not_callable(self, downloader: Downloader):
        with pytest.raises(TypeError):
            downloader.maybe_download("foo", callback=None)

    def test_maybe_download_wrong_callable(
        self, downloader: Downloader, requests_mock, csv_data: bytes
    ):
        url = urljoin(downloader._options.url, "foobar")
        requests_mock.register_uri("GET", url, content=csv_data)

        with pytest.raises(ValueError, match=r"Expected object or value"):
            downloader.maybe_download(url, callback=pd.read_json)

    def test_maybe_download_passes_params(
        self, downloader: Downloader, requests_mock, csv_data: bytes
    ):
        csv_url = urljoin(downloader._options.url, "foobar/?format=csv")
        csv_df = pd.read_csv(BytesIO(csv_data))
        json_url = urljoin(downloader._options.url, "foobar/?format=json")
        json_handle = StringIO()
        csv_df.to_json(json_handle)

        requests_mock.register_uri("GET", csv_url, content=csv_data)
        requests_mock.register_uri(
            "GET", json_url, content=bytes(json_handle.getvalue(), encoding="utf-8")
        )

        res1 = downloader.maybe_download(csv_url, callback=pd.read_csv)
        res2 = downloader.maybe_download(csv_url, callback=pd.read_csv)

        assert res1 is res2
        assert requests_mock.called_once
        np.testing.assert_array_equal(res1.index, csv_df.index)
        np.testing.assert_array_equal(res1.columns, csv_df.columns)
        np.testing.assert_array_equal(res1.values, csv_df.values)

        res1 = downloader.maybe_download(json_url, callback=pd.read_json)
        res2 = downloader.maybe_download(json_url, callback=pd.read_json)

        assert res1 is res2
        assert len(requests_mock.request_history) == 2
        np.testing.assert_array_equal(res1.index, csv_df.index)
        np.testing.assert_array_equal(res1.columns, csv_df.columns)
        np.testing.assert_array_equal(res1.values, csv_df.values)

    def test_maybe_download_no_cache(
        self, downloader: Downloader, requests_mock, csv_data: bytes
    ):
        url = urljoin(downloader._options.url, "foobar")
        requests_mock.register_uri("GET", url, content=csv_data)

        res1 = downloader.maybe_download(url, callback=pd.read_csv)
        downloader._options.cache.clear()
        res2 = downloader.maybe_download(url, callback=pd.read_csv)

        assert res1 is not res2
        assert len(requests_mock.request_history) == 2
        np.testing.assert_array_equal(res1.index, res2.index)
        np.testing.assert_array_equal(res1.columns, res2.columns)
        np.testing.assert_array_equal(res1.values, res2.values)

    def test_maybe_download_is_not_final(
        self, downloader: Downloader, requests_mock, csv_data: bytes
    ):
        endpoint = "barbaz"
        url = urljoin(downloader._options.url, endpoint)
        requests_mock.register_uri("GET", url, content=csv_data)
        csv_df = pd.read_csv(BytesIO(csv_data))

        res = downloader.maybe_download(endpoint, callback=pd.read_csv, is_final=False)

        assert requests_mock.called_once
        np.testing.assert_array_equal(res.index, csv_df.index)
        np.testing.assert_array_equal(res.columns, csv_df.columns)
        np.testing.assert_array_equal(res.values, csv_df.values)

    def test_get_server_version_not_decodable(
        self, options: Options, requests_mock, caplog
    ):
        url = urljoin(options.url, Endpoint.ABOUT.s)
        options.autoload = True
        requests_mock.register_uri(
            "GET", f"{url}?format=text", content=bytes("foobarbaz", encoding="utf-8")
        )

        with caplog.at_level(logging.DEBUG):
            version = _get_server_version(options)

        assert requests_mock.called_once
        assert (
            "Unable to get server version. Reason: `list index out of range`"
            in caplog.text
        )
        assert version == UNKNOWN_SERVER_VERSION

    def test_get_server_version_no_autoload(
        self, options: Options, requests_mock, caplog
    ):
        url = urljoin(options.url, Endpoint.ABOUT.s)
        options.autoload = False
        requests_mock.register_uri("GET", f"{url}?format=text", text="foobarbaz")

        with caplog.at_level(logging.DEBUG):
            version = _get_server_version(options)

        assert not requests_mock.called_once
        assert (
            "Unable to get server version. Reason: `Autoload is disabled.`"
            in caplog.text
        )
        assert version == UNKNOWN_SERVER_VERSION

    def test_get_server_version(self, options: Options, requests_mock):
        url = urljoin(options.url, Endpoint.ABOUT.s)
        options.autoload = True
        requests_mock.register_uri(
            "GET",
            f"{url}?format=text",
            content=bytes("foo bar baz\nversion: 42.1337.00", encoding="utf-8"),
        )

        version = _get_server_version(options)

        assert requests_mock.called_once
        assert version == "42.1337.00"
