from io import StringIO
from typing import Iterable, _GenericAlias
from urllib.parse import urljoin
import json
import logging

import pytest

from pandas.api.types import is_object_dtype, is_categorical_dtype
import numpy as np
import pandas as pd

from omnipath import options
from omnipath.requests import Enzsub, Complexes, Intercell, Annotations
from omnipath._core.requests import SignedPTMs
from omnipath._core.query._query import EnzsubQuery
from omnipath._core.requests._utils import _split_unique_join, _strip_resource_label
from omnipath.constants._pkg_constants import Key, Endpoint


class TestEnzsub:
    def test_str_repr(self):
        assert str(Enzsub()) == f"<{Enzsub().__class__.__name__}>"
        assert repr(Enzsub()) == f"<{Enzsub().__class__.__name__}>"

    def test_params_no_org_genesymbol(self):
        params = Enzsub.params()

        assert Key.ORGANISM.value not in params
        assert Key.GENESYMBOLS.value in params

        for k, valid in params.items():
            if isinstance(valid, Iterable):
                np.testing.assert_array_equal(
                    list(set(valid)), list(set(EnzsubQuery(k).valid))
                )
            else:
                assert valid == EnzsubQuery(k).valid

    def test_resources(self, cache_backup, requests_mock, resources: bytes):
        url = urljoin(options.url, Endpoint.RESOURCES.s)
        requests_mock.register_uri("GET", f"{url}?format=json", content=resources)

        res = Enzsub.resources()

        assert res == ("quux",)
        assert requests_mock.called_once

    def test_invalid_params(self):
        with pytest.raises(ValueError, match=r"Invalid value `foo` for `EnzsubQuery`."):
            Enzsub.get(foo="bar")

    def test_invalid_license(self):
        with pytest.raises(ValueError, match=r"Invalid value `bar` for `License`."):
            Enzsub.get(license="bar")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match=r"Invalid value `bar` for `Format`."):
            Enzsub.get(format="bar")

    def test_valid_params(self, cache_backup, requests_mock, tsv_data: bytes, caplog):
        url = urljoin(options.url, Enzsub._query_type.endpoint)
        df = pd.read_csv(StringIO(tsv_data.decode("utf-8")), sep="\t")
        requests_mock.register_uri(
            "GET",
            f"{url}?fields=curation_effort%2Creferences%2Csources&format=tsv&license=academic",
            content=tsv_data,
        )

        with caplog.at_level(logging.WARNING):
            res = Enzsub.get(license="academic", format="text")

        assert f"Invalid `{Key.FORMAT.s}='text'`" in caplog.text
        np.testing.assert_array_equal(res.index, df.index)
        np.testing.assert_array_equal(res.columns, df.columns)
        np.testing.assert_array_equal(res.values, df.values)
        assert requests_mock.called_once

    def test_annotations(self):
        assert set(Enzsub._annotations().keys()) == {e.param for e in EnzsubQuery}
        assert all(
            isinstance(a, (_GenericAlias, type)) for a in Enzsub._annotations().values()
        )

    def test_docs(self):
        assert set(Enzsub._docs().keys()) == {e.param for e in EnzsubQuery}
        assert all(d is None for d in Enzsub._docs().values())

    def test_invalid_organism(self, cache_backup, requests_mock, tsv_data: bytes):
        url = urljoin(options.url, Enzsub._query_type.endpoint)
        requests_mock.register_uri(
            "GET",
            f"{url}?fields=curation_effort%2Creferences%2Csources&format=tsv",
            content=tsv_data,
        )
        with pytest.raises(
            ValueError,
            match=r"Invalid value `foobarbaz` for `Organism`. Valid options are:",
        ):
            Enzsub.get(organism="foobarbaz")

        assert not requests_mock.called_once

    def test_genesymbols_dont_matter(
        self, cache_backup, requests_mock, tsv_data: bytes
    ):
        url = urljoin(options.url, Enzsub._query_type.endpoint)
        requests_mock.register_uri(
            "GET",
            f"{url}?fields=curation_effort%2Creferences%2Csources&format=tsv",
            content=tsv_data,
        )
        _ = Enzsub.get(genesymbol=True)

        assert requests_mock.called_once

    def test_field_injection(self, cache_backup, requests_mock, tsv_data: bytes):
        url = urljoin(options.url, Enzsub._query_type.endpoint)
        requests_mock.register_uri(
            "GET",
            f"{url}?fields=Alpha%2Cbeta%2Ccuration_effort%2Creferences%2Csources&format=tsv",
            content=tsv_data,
        )
        _ = Enzsub.get(fields=("beta", "Alpha", "Alpha"))

        assert requests_mock.called_once

    def test_no_dtype_conversion(self, cache_backup, requests_mock, tsv_data: bytes):
        url = urljoin(options.url, Enzsub._query_type.endpoint)
        options.convert_dtypes = False

        requests_mock.register_uri(
            "GET",
            f"{url}?fields=curation_effort%2Creferences%2Csources&format=tsv",
            content=tsv_data,
        )

        res = Enzsub.get()
        assert is_object_dtype(res["modification"])

        options.convert_dtypes = True

        res = Enzsub.get()
        assert is_categorical_dtype(res["modification"])
        assert requests_mock.called_once


class TestIntercell:
    def test_resources_wrong_type(self):
        with pytest.raises(TypeError):
            Intercell.resources(42)

    def test_resources_no_generic_resources(self):
        with pytest.raises(
            ValueError, match=r"No generic categories have been selected."
        ):
            Intercell.resources([])

    def test_resources_no_generic(self, cache_backup, requests_mock, resources: bytes):
        url = urljoin(options.url, Endpoint.RESOURCES.s)
        requests_mock.register_uri("GET", f"{url}?format=json", content=resources)

        res = Intercell.resources()

        assert res == ("bar", "baz", "foo")
        assert requests_mock.called_once

    def test_resources_generic(self, cache_backup, requests_mock, resources: bytes):
        url = urljoin(options.url, Endpoint.RESOURCES.s)
        requests_mock.register_uri("GET", f"{url}?format=json", content=resources)

        res = Intercell.resources(generic_categories=["42"])
        assert res == ("bar", "foo")

        res = Intercell.resources(generic_categories="24")
        assert res == ("baz",)

        res = Intercell.resources(generic_categories="foobarbaz")
        assert res == ()
        assert requests_mock.called_once  # caching

    def test_categories(self, cache_backup, requests_mock, intercell_data: bytes):
        url = urljoin(options.url, Key.INTERCELL_SUMMARY.s)
        data = json.loads(intercell_data)
        requests_mock.register_uri("GET", f"{url}?format=json", content=intercell_data)

        res = Intercell.categories()

        assert res == tuple(sorted(set(map(str, data[Key.CATEGORY.s]))))
        assert requests_mock.called_once

    def test_generic_categories(
        self, cache_backup, requests_mock, intercell_data: bytes
    ):
        url = urljoin(options.url, Key.INTERCELL_SUMMARY.s)
        data = json.loads(intercell_data)
        requests_mock.register_uri("GET", f"{url}?format=json", content=intercell_data)

        res = Intercell.generic_categories()

        assert res == tuple(sorted(set(map(str, data[Key.PARENT.s]))))
        assert requests_mock.called_once

    def test_password_from_options(
        self, cache_backup, requests_mock, intercell_data: bytes
    ):
        old_pwd = options.password
        options.password = "foobar"

        url = urljoin(options.url, Intercell._query_type.endpoint)
        requests_mock.register_uri(
            "GET",
            f"{url}?format=tsv&password=foobar",
            content=intercell_data,
        )

        _ = Intercell.get()
        options.password = old_pwd

        assert requests_mock.called_once

    def test_password_from_function_call(
        self, cache_backup, requests_mock, intercell_data: bytes
    ):
        old_pwd = options.password
        options.password = "foobar"

        url = urljoin(options.url, Intercell._query_type.endpoint)
        requests_mock.register_uri(
            "GET",
            f"{url}?format=tsv&password=bazquux",
            content=intercell_data,
        )

        _ = Intercell.get(password="bazquux")
        options.password = old_pwd

        assert requests_mock.called_once


class TestComplex:
    def test_complex_genes_wrong_dtype(self):
        with pytest.raises(TypeError):
            Complexes.complex_genes("foo", complexes=42)

    def test_comples_genes_empty_complexes(self, caplog):
        df = pd.DataFrame()
        with caplog.at_level(logging.WARNING):
            res = Complexes.complex_genes("foo", complexes=df)

        assert res is df
        assert "Complexes are empty" in caplog.text

    def test_complex_genes_no_column(self):
        with pytest.raises(KeyError):
            Complexes.complex_genes("foo", complexes=pd.DataFrame({"foo": range(10)}))

    def test_complex_genes_no_genes(self):
        with pytest.raises(ValueError, match=r"No genes have been selected."):
            Complexes.complex_genes([], complexes=None)

    def test_complex_genes_complexes_not_specified(
        self, cache_backup, requests_mock, tsv_data: bytes
    ):
        url = urljoin(options.url, Complexes._query_type.endpoint)
        df = pd.read_csv(StringIO(tsv_data.decode("utf-8")), sep="\t")
        requests_mock.register_uri("GET", f"{url}?format=tsv", content=tsv_data)

        res = Complexes.complex_genes("fooo")

        np.testing.assert_array_equal(res.columns, df.columns)
        assert res.empty

    def test_complexes_complexes_specified(self, complexes: pd.DataFrame):
        res = Complexes.complex_genes("foo", complexes=complexes, total_match=False)

        assert isinstance(res, pd.DataFrame)
        assert res.shape == (2, 2)
        assert set(res.columns) == {"components_genesymbols", "dummy"}
        assert all(
            any(v in "foo" for v in vs.split("_"))
            for vs in res["components_genesymbols"]
        )

    def test_complexes_total_match(self, complexes: pd.DataFrame):
        res = Complexes.complex_genes(
            ["bar", "baz"], complexes=complexes, total_match=True
        )

        assert res.shape == (1, 2)
        assert all(
            all(v in ("bar", "baz") for v in vs.split("_"))
            for vs in res["components_genesymbols"]
        )

    def test_complexes_no_total_match(self, complexes: pd.DataFrame):
        res = Complexes.complex_genes(
            ["bar", "baz", "bar"], complexes=complexes, total_match=False
        )

        assert res.shape == (3, 2)
        assert all(
            any(v in ("bar", "baz") for v in vs.split("_"))
            for vs in res["components_genesymbols"]
        )


class TestAnnotations:
    def test_too_many_proteins_requested(self):
        with pytest.raises(ValueError, match=r"Cannot download annotations for"):
            Annotations.get([f"foo_{i}" for i in range(601)])

    def test_params(self):
        params = Annotations.params()
        assert Key.ORGANISM.value not in params

    def test_genesymbols_matter(self, cache_backup, requests_mock, tsv_data: bytes):
        url = urljoin(options.url, Annotations._query_type.endpoint)
        requests_mock.register_uri(
            "GET", f"{url}?proteins=bar&genesymbols=1&format=tsv", content=tsv_data
        )
        df = pd.read_csv(StringIO(tsv_data.decode("utf-8")), sep="\t")

        res = Annotations.get(["bar"], genesymbols=True)

        np.testing.assert_array_equal(res.index, df.index)
        np.testing.assert_array_equal(res.columns, df.columns)
        np.testing.assert_array_equal(res.values, df.values)

    def test_invalid_organism_does_not_matter(
        self, cache_backup, requests_mock, tsv_data: bytes
    ):
        url = urljoin(options.url, Annotations._query_type.endpoint)
        requests_mock.register_uri(
            "GET", f"{url}?proteins=foo&format=tsv", content=tsv_data
        )
        df = pd.read_csv(StringIO(tsv_data.decode("utf-8")), sep="\t")

        res = Annotations.get(["foo", "foo"], organism="foobarbaz")

        np.testing.assert_array_equal(res.index, df.index)
        np.testing.assert_array_equal(res.columns, df.columns)
        np.testing.assert_array_equal(res.values, df.values)


class TestSignedPTMs:
    def test_get_signed_ptms_wrong_ptms_type(self):
        with pytest.raises(TypeError, match=r"Expected `ptms`"):
            SignedPTMs.get(42, pd.DataFrame())

    def test_get_signed_ptms_wrong_interactions_type(self):
        with pytest.raises(TypeError, match=r"Expected `interactions`"):
            SignedPTMs.get(pd.DataFrame(), 42)

    def test_get_signed_ptms(self):
        ptms = pd.DataFrame(
            {"enzyme": ["alpha", "beta", "gamma"], "substrate": [0, 1, 0], "foo": 42}
        )
        interactions = pd.DataFrame(
            {
                "source": ["gamma", "beta", "delta"],
                "target": [0, 0, 1],
                "is_stimulation": True,
                "is_inhibition": False,
                "bar": 1337,
            }
        )
        expected = pd.merge(
            ptms,
            interactions[["source", "target", "is_stimulation", "is_inhibition"]],
            left_on=["enzyme", "substrate"],
            right_on=["source", "target"],
            how="left",
        )

        res = SignedPTMs.get(ptms, interactions)

        np.testing.assert_array_equal(res.index, expected.index)
        np.testing.assert_array_equal(res.columns, expected.columns)

        np.testing.assert_array_equal(pd.isnull(res), pd.isnull(expected))
        np.testing.assert_array_equal(
            res.values[~pd.isnull(res)], expected.values[~pd.isnull(expected)]
        )

    def test_graph_not_a_dataframe(self):
        with pytest.raises(
            TypeError, match=r"Expected `data` to be of type `pandas.DataFrame`,"
        ):
            SignedPTMs.graph(42)

    def test_graph_source_target(self):
        ptms = pd.DataFrame(
            {
                "enzyme": ["alpha", "beta", "gamma"],
                "substrate": [0, 1, 0],
                "foo": 42,
                "enzyme_genesymbol": "bar",
                "substrate_genesymbol": "baz",
            }
        )
        src, tgt = SignedPTMs._get_source_target_cols(ptms)

        assert src == "enzyme_genesymbol"
        assert tgt == "substrate_genesymbol"

        src, tgt = SignedPTMs._get_source_target_cols(
            ptms[ptms.columns.difference(["enzyme_genesymbol", "substrate_genesymbol"])]
        )

        assert src == "enzyme"
        assert tgt == "substrate"

    def test_graph(self):
        import networkx as nx

        ptms = pd.DataFrame(
            {
                "enzyme": ["alpha", "beta", "gamma"],
                "substrate": [0, 1, 0],
                "foo": 42,
                "references": "bar;baz",
            }
        )
        interactions = pd.DataFrame(
            {
                "source": ["gamma", "beta", "delta"],
                "target": [0, 0, 1],
                "is_stimulation": True,
                "is_inhibition": False,
                "bar": 1337,
            }
        )
        expected = pd.merge(
            ptms,
            interactions[["source", "target", "is_stimulation", "is_inhibition"]],
            left_on=["enzyme", "substrate"],
            right_on=["source", "target"],
            how="left",
        )

        G = SignedPTMs.graph(expected)

        assert isinstance(G, nx.DiGraph)
        assert G.is_directed()
        assert len(G) == 5
        for _, _, attr in G.edges(data=True):
            assert attr["foo"] == 42
            assert attr["references"] == ["bar", "baz"]


class TestUtils:
    def test_split_unique_join_no_func(self, string_series: pd.Series):
        res = _split_unique_join(string_series)

        np.testing.assert_array_equal(
            res, pd.Series(["foo:123", "bar:45;baz", None, "bar:67;baz:67", "foo"])
        )

    def test_split_unique_join_func(self, string_series: pd.Series):
        res = _split_unique_join(string_series, func=len)

        np.testing.assert_array_equal(res, pd.Series([1, 2, None, 2, 3], dtype=object))

    def test_strip_resource_label_no_func(self, string_series: pd.Series):
        res = _strip_resource_label(string_series, func=None)

        np.testing.assert_array_equal(
            res, pd.Series(["123", "45;baz", None, "67", "foo"])
        )

    def test_strip_resource_label_func(self):
        res = _strip_resource_label(
            pd.Series(["abc:123;bcd:123", "aaa:123", "a:1;b:2;c:3"]),
            func=lambda row: len(set(row)),
        )

        np.testing.assert_array_equal(res, pd.Series([1, 1, 3]))
