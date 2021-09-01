from copy import copy, deepcopy
from typing import Optional
from pathlib import Path

import pytest

from pandas.testing import assert_frame_equal
import pandas as pd

from omnipath import options, clear_cache
from omnipath._core.cache._cache import FileCache, NoopCache, MemoryCache


def test_clear_cache_high_lvl(cache_backup):
    options.cache["foo"] = 42
    assert len(options.cache) == 1
    assert options.cache["foo"] == 42

    clear_cache()

    assert len(options.cache) == 0


class TestMemoryCache:
    def test_str_repr(self):
        mc = MemoryCache()

        assert str(mc) == f"<{mc.__class__.__name__}[size={len(mc)}]>"
        assert repr(mc) == f"<{mc.__class__.__name__}[size={len(mc)}]>"

    def test_path_is_None(self):
        mc = MemoryCache()
        assert mc.path == "memory"

    def test_copy_does_nothing(self):
        mc = MemoryCache()

        assert mc is mc.copy()
        assert mc is copy(mc)

    def test_deepcopy_work(self):
        mc = MemoryCache()

        assert mc is not deepcopy(mc)

    def test_cache_works(self):
        mc = MemoryCache()
        sentinel = object()

        mc["foo"] = sentinel

        assert len(mc) == 1
        assert mc["foo"] is not sentinel  # copy was made

        mc.clear()

        assert len(mc) == 0

    def test_dataframe_modification(self):
        mc = MemoryCache()
        df = pd.DataFrame({"foo": [1, 2], "bar": [3, 4]})

        mc["baz"] = df
        _ = df.pop("foo")

        assert "foo" in mc["baz"]
        assert "bar" in mc["baz"]

    @pytest.mark.parametrize("val", [None, pd.DataFrame()])
    def test_add_empty_value(self, val: Optional[pd.DataFrame]):
        mc = MemoryCache()

        mc["foo"] = val

        assert "foo" not in mc
        assert len(mc) == 0

    def test_returns_copy(self):
        mc = MemoryCache()
        data = pd.DataFrame({"x": [0, 1]})
        mc["foo"] = data

        assert mc["foo"] is not mc["foo"]
        assert_frame_equal(mc["foo"], data)


class TestPickleCache:
    def test_invalid_path(self):
        with pytest.raises(TypeError):
            FileCache(42)

    def test_path(self, tmpdir):
        fc = FileCache(Path(tmpdir))

        assert isinstance(fc.path, Path)
        assert str(fc.path) == str(tmpdir)

    def test_str_repr(self, tmpdir):
        fc = FileCache(Path(tmpdir))

        assert (
            str(fc)
            == f"<{fc.__class__.__name__}[size={len(fc)}, path={str(tmpdir)!r}]>"
        )
        assert (
            repr(fc)
            == f"<{fc.__class__.__name__}[size={len(fc)}, path={str(tmpdir)!r}]>"
        )

    def test_cache_works(self, tmpdir):
        fc = FileCache(Path(tmpdir))
        sentinel = object()

        assert "foo" not in fc
        fc["foo"] = 42
        fc["bar.pickle"] = sentinel

        assert "foo" in fc
        assert "foo.pickle" in fc
        assert fc["bar.pickle"] is not sentinel

    def test_clear_works(self, tmpdir):
        fc = FileCache(Path(tmpdir))
        fc["foo"] = 42
        assert Path(fc.path).exists()

        fc.clear()

        assert len(fc) == 0
        assert not Path(tmpdir).exists()

    @pytest.mark.parametrize("val", [None, pd.DataFrame()])
    def test_add_empty_value(self, tmpdir, val: Optional[pd.DataFrame]):
        fc = FileCache(Path(tmpdir))

        fc["foo"] = val

        assert "foo" not in fc
        assert len(fc) == 0


class TestNoopCache:
    def test_add_value(self):
        nc = NoopCache()
        nc["foo"] = 42

        assert nc.path is None
        assert "foo" not in nc
        assert len(nc) == 0
