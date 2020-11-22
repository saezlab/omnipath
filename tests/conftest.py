from io import StringIO
from copy import deepcopy
from shutil import copy
from pathlib import Path
from collections import defaultdict
import json
import pickle

import pytest

import pandas as pd

from omnipath.constants import InteractionDataset
from omnipath._core.cache._cache import MemoryCache
from omnipath._core.query._query import QueryType
from omnipath._core.utils._options import Options
from omnipath.constants._pkg_constants import Key
from omnipath._core.downloader._downloader import Downloader


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
