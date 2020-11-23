from copy import copy, deepcopy
from pathlib import Path

import pytest

from omnipath import options, clear_cache
from omnipath._core.cache._cache import FileCache, MemoryCache


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
        assert mc.path is None

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
        assert mc["foo"] is sentinel

        mc.clear()

        assert len(mc) == 0


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
