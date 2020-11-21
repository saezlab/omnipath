from typing import _GenericAlias
from collections import defaultdict

import pytest

from omnipath._core.query._query import (
    Query,
    QueryType,
    EnzsubQuery,
    ComplexesQuery,
    IntercellQuery,
    AnnotationsQuery,
    InteractionsQuery,
    _get_synonyms,
)
from omnipath._core.query._query_validator import (
    EnzsubValidator,
    ComplexesValidator,
    IntercellValidator,
    AnnotationsValidator,
    InteractionsValidator,
    _to_string_set,
)


class TestUtils:
    def test_get_synonyms_wrong_type(self):
        with pytest.raises(TypeError):
            _get_synonyms(42)

    def test_get_synonyms_from_s2p(self):
        res = _get_synonyms("cat")

        assert len(res) == 2
        assert res == ("cat", "cats")

    def test_get_synonyms_from_p2s(self):
        res = _get_synonyms("dogs")

        assert len(res) == 2
        assert res == ("dog", "dogs")

    def test_to_string_set_string(self):
        assert {"foo"} == _to_string_set("foo")

    def test_to_string_set_int(self):
        assert {"42"} == _to_string_set(42)

    def test_to_string_set_sequence(self):
        assert {"foo", "42"} == _to_string_set(["foo", 42])


class TestValidator:
    @pytest.mark.parametrize(
        "validator",
        [
            EnzsubValidator,
            InteractionsValidator,
            ComplexesValidator,
            AnnotationsValidator,
            IntercellValidator,
        ],
    )
    def test_validator_no_server_access(self, validator):
        for value in list(validator):
            v = validator(value)

            assert v.valid is None
            assert v.doc is None

            assert v(None) is None
            assert v("foo") == {"foo"}
            assert v(42) == {"42"}
            assert v(True) == {"1"}
            assert v(False) == {"0"}
            assert v(["foo", "foo"]) == {"foo"}
            assert v(["foo", 42]) == {"foo", "42"}
            assert v({"foo", "bar", "baz"}) == {"foo", "bar", "baz"}

            assert issubclass(type(v.annotation), (_GenericAlias, type))


class TestQuery:
    @pytest.mark.parametrize(
        "query,validator",
        zip(
            [
                EnzsubQuery,
                InteractionsQuery,
                ComplexesQuery,
                AnnotationsQuery,
                IntercellQuery,
            ],
            [
                EnzsubValidator,
                InteractionsValidator,
                ComplexesValidator,
                AnnotationsValidator,
                IntercellValidator,
            ],
        ),
    )
    def test_query_correct_validator(self, query, validator):
        assert query.__validator__ == validator

    def test_query_endpoint(self):
        for q in list(QueryType):
            q = QueryType(q)

            assert issubclass(q.value, Query)
            assert q.endpoint == q.name.lower()

    @pytest.mark.parametrize(
        "query,validator",
        zip(
            [
                EnzsubQuery,
                InteractionsQuery,
                ComplexesQuery,
                AnnotationsQuery,
                IntercellQuery,
            ],
            [
                EnzsubValidator,
                InteractionsValidator,
                ComplexesValidator,
                AnnotationsValidator,
                IntercellValidator,
            ],
        ),
    )
    def test_query_delegation(self, query, validator, mocker):
        call_spy = mocker.spy(validator, "__call__")

        qdb = query("databases")
        _ = qdb("foo")

        call_spy.assert_called_once_with(
            getattr(qdb.__validator__, qdb._query_name), "foo"
        )
        assert call_spy.spy_return == {"foo"}
        assert qdb.doc is None

        for attr in ("valid", "annotation", "doc"):
            m = mocker.patch.object(
                validator, attr, new_callable=mocker.PropertyMock, return_value="foo"
            )
            assert getattr(qdb, attr) == "foo"

            m.assert_called_once()

    @pytest.mark.parametrize(
        "query",
        [
            EnzsubQuery,
            InteractionsQuery,
            ComplexesQuery,
            AnnotationsQuery,
            IntercellQuery,
        ],
    )
    def test_query_synonym(self, query):
        mapper = defaultdict(list)
        for v in list(query):
            name = "_".join(v.name.split("_")[:-1])
            mapper[name].append(v.value)

        for vs in mapper.values():
            assert len(vs) == 2
            assert len({query(v).param for v in vs})
