from io import StringIO
from abc import ABC
from copy import deepcopy
from shutil import copy
from typing import Optional
from inspect import isclass
from pathlib import Path
from collections import defaultdict
from urllib.parse import urljoin
import json
import pickle
import logging

import pytest
import requests

import numpy as np
import pandas as pd

from omnipath.constants import InteractionDataset
from omnipath._core.cache._cache import MemoryCache
from omnipath._core.query._query import QueryType
from omnipath._core.utils._options import Options
from omnipath.constants._pkg_constants import DEFAULT_OPTIONS, Key, Endpoint
from omnipath._core.downloader._downloader import Downloader
import omnipath as op


def pytest_addoption(parser):
    parser.addoption(
        "--test-server",
        dest="test_server",
        action="store_true",
        help="Whether to also test the server connection.",
    )


@pytest.fixture(scope="function")
def options() -> "Options":
    opt = Options.from_config()
    opt.cache = None
    opt.progress_bar = False
    return opt


@pytest.fixture(scope="function")
def config_backup(tmpdir):
    copy(Options.config_path, tmpdir / "config.ini")
    yield
    copy(tmpdir / "config.ini", Options.config_path)


@pytest.fixture(scope="function")
def cache_backup():
    import omnipath as op

    cache = deepcopy(op.options.cache)
    pb = op.options.progress_bar
    op.options.cache = MemoryCache()
    op.options.progress_bar = False
    yield
    op.options.cache = cache
    op.options.progress_bar = pb


@pytest.fixture(scope="class")
def server_url():
    import omnipath as op

    cache = deepcopy(op.options.cache)
    pb = op.options.progress_bar
    url = op.options.url
    cd = op.options.convert_dtypes

    op.options.cache = MemoryCache()
    op.options.progress_bar = False
    op.options.url = DEFAULT_OPTIONS.url
    op.options.convert_dtypes = True
    yield
    op.options.cache = cache
    op.options.progress_bar = pb
    op.options.url = url
    op.options.convert_dtypes = cd


@pytest.fixture(scope="function")
def downloader(options) -> "Downloader":
    return Downloader(options)


@pytest.fixture(scope="session")
def csv_data() -> bytes:
    str_handle = StringIO()
    pd.DataFrame({"foo": range(5), "bar": "baz", "quux": 42}).to_csv(str_handle)

    return bytes(str_handle.getvalue(), encoding="utf-8")


@pytest.fixture(scope="session")
def tsv_data() -> bytes:
    str_handle = StringIO()
    pd.DataFrame(
        {
            "foo": range(5),
            "components_genesymbols": "foo",
            "quux": 42,
            "modification": "bar",
        }
    ).to_csv(str_handle, sep="\t")

    return bytes(str_handle.getvalue(), encoding="utf-8")


@pytest.fixture(scope="session")
def intercell_data() -> bytes:
    data = {}
    data[Key.PARENT.s] = [42, 1337, 24, 42]
    data[Key.CATEGORY.s] = ["foo", "bar", "bar", "foo"]

    return bytes(json.dumps(data), encoding="utf-8")


@pytest.fixture(scope="session")
def resources() -> bytes:
    data = defaultdict(dict)
    data["foo"][Key.QUERIES.s] = {
        QueryType.INTERCELL.endpoint: {Key.GENERIC_CATEGORIES.s: ["42"]}
    }
    data["bar"][Key.QUERIES.s] = {
        QueryType.INTERCELL.endpoint: {Key.GENERIC_CATEGORIES.s: ["42", "13"]}
    }
    data["baz"][Key.QUERIES.s] = {
        QueryType.INTERCELL.endpoint: {Key.GENERIC_CATEGORIES.s: ["24"]}
    }
    data["quux"][Key.QUERIES.s] = {
        QueryType.ENZSUB.endpoint: {Key.GENERIC_CATEGORIES.s: ["24"]}
    }

    return bytes(json.dumps(data), encoding="utf-8")


@pytest.fixture(scope="session")
def interaction_resources() -> bytes:
    data = defaultdict(dict)
    for i, d in enumerate(InteractionDataset):
        data[f"d_{i}"][Key.QUERIES.s] = {
            QueryType.INTERACTIONS.endpoint: {Key.DATASETS.s: [d.value]}
        }

    return bytes(json.dumps(data), encoding="utf-8")


@pytest.fixture(scope="session")
def complexes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "components_genesymbols": [
                "foo",
                "bar_baz_quux",
                "baz_bar",
                "bar_quux_foo",
            ],
            "dummy": 42,
        }
    )


@pytest.fixture(scope="session")
def interactions_data() -> bytes:
    str_handle = StringIO()
    with open(Path("tests") / "_data" / "interactions.pickle", "rb") as fin:
        data: pd.DataFrame = pickle.load(fin)

    data.to_csv(str_handle, sep="\t", index=False)

    return bytes(str_handle.getvalue(), encoding="utf-8")


@pytest.fixture(scope="session")
def transmitters_data() -> bytes:
    str_handle = StringIO()
    with open(Path("tests") / "_data" / "transmitters.pickle", "rb") as fin:
        data: pd.DataFrame = pickle.load(fin)

    data.to_csv(str_handle, sep="\t", index=False)

    return bytes(str_handle.getvalue(), encoding="utf-8")


@pytest.fixture(scope="session")
def receivers_data() -> bytes:
    str_handle = StringIO()
    with open(Path("tests") / "_data" / "receivers.pickle", "rb") as fin:
        data: pd.DataFrame = pickle.load(fin)

    data.to_csv(str_handle, sep="\t", index=False)

    return bytes(str_handle.getvalue(), encoding="utf-8")


@pytest.fixture(scope="session")
def import_intercell_result() -> pd.DataFrame:
    with open(Path("tests") / "_data" / "import_intercell_result.pickle", "rb") as fin:
        return pickle.load(fin)


@pytest.fixture(scope="session")
def string_series() -> pd.Series:
    return pd.Series(["foo:123", "bar:45;baz", None, "baz:67;bar:67", "foo;foo;foo"])


def _can_import_omnipathR() -> Optional["rpy2.robjects.packages.Package"]:  # noqa: F821
    try:
        from packaging import version
        from rpy2.robjects.packages import PackageNotInstalledError, importr
        import rpy2

        try:
            from importlib_metadata import version as get_version
        except ImportError:
            # >=Python3.8
            from importlib.metadata import version as get_version

        try:
            assert version.parse(get_version(rpy2.__name__)) >= version.parse("3.3.0")
            mod = importr("OmnipathR")
            logging.error("Succesfully loaded `OmnipathR`")
            return mod
        except (PackageNotInstalledError, AssertionError) as err:
            logging.error(f"Unable to import `OmnipathR`. Reason: `{err}`.")

    except ImportError as err:
        logging.error(f"Unable to import `rpy2`. Reason: `{err}`.")

    return None


@pytest.fixture(scope="session")
def omnipathr(request):
    url = urljoin(DEFAULT_OPTIONS.url, Endpoint.ABOUT.s)

    if not request.config.getoption("test_server", default=False, skip=True):
        logging.error("Testing using the server is disabled.")
        return None
    try:
        resp = requests.get(url)
        status_code = resp.status_code
    except Exception as e:
        logging.error(f"Unable to contact the server at `{url}`. Reason: `{e}`")
        return None

    if status_code != 200:
        logging.error(
            f"Unable to contact the server at `{url}`. Status code: `{status_code}`"
        )
        return None

    return _can_import_omnipathR()


@pytest.fixture(autouse=True, scope="class")
def _inject_omnipath(request, omnipathr, server_url):
    if isclass(request.cls) and issubclass(request.cls, RTester):
        if omnipathr is None:
            pytest.skip("Unable to import `OmnipathR`.")
        from rpy2.robjects import pandas2ri

        # at this point, we know rpy2 can be imported, thanks to the `omnipathr` fixture
        # do not change the activation order
        pandas2ri.activate()
        request.cls.omnipathr = omnipathr


class RTester(ABC):
    def test_resources(self):
        expected = sorted(self.omnipathr.get_intercell_resources())
        actual = sorted(op.requests.Intercell.resources())

        np.testing.assert_array_equal(expected, actual)
