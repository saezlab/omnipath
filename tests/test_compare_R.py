from typing import Iterable, Optional

from conftest import RTester
import pytest

import numpy as np
import pandas as pd

from omnipath.constants import License, Organism
import omnipath as op

# in order to minimize server access, the tests are not parametrized
# and the resources are chosen so that minimal data required is transferred
# these tests will also run only on 1 job CI matrix, to further reduce the load
#
# note that these tests don't test whether `<query>.params()` returns the valid values
# this would require different Python interpreter invocation, since by design, during testing
# `omnipath.options.autoload` is disabled


def _assert_dataframes_equal(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    clazz: type = op.requests.Enzsub,
    remove_metadata: Optional[Iterable[str]] = None,
):
    assert isinstance(expected, pd.DataFrame)
    assert isinstance(actual, pd.DataFrame)

    # some small naming discrepancy
    actual.rename(columns={"n_primary_sources": "n_resources"}, inplace=True)
    # these are always present in our case
    if remove_metadata is None:
        remove_metadata = ["n_sources", "references_stripped"]
    for k in remove_metadata:
        if k in actual.columns:
            del actual[k]

    np.testing.assert_array_equal(expected.shape, actual.shape)
    # don't compare index since sometimes, it's not informative + differs across calls from OmnipathR
    col_order = sorted(expected.columns)
    np.testing.assert_array_equal(col_order, sorted(actual.columns))

    expected = clazz()._convert_dtypes(expected)

    # this way, we know which column fails
    for col in col_order:
        e, a = expected[col], actual[col]
        emask = ~(pd.isna(e).values | pd.isnull(a).values)
        amask = ~(pd.isna(e).values | pd.isnull(a).values)

        # print(f"Column `{col}`")
        np.testing.assert_array_equal(emask, amask)
        np.testing.assert_array_equal(e[emask], a[emask])


class TestEnzSub(RTester):
    def test_organism(self):
        organism = Organism.RAT
        expected = self.omnipathr.import_omnipath_enzsub(
            resources="DEPOD", genesymbols=False, organism=organism.code
        )
        actual = op.requests.Enzsub.get(
            resources="DEPOD", genesymbols=False, organism=organism
        )

        _assert_dataframes_equal(expected, actual)

    def test_resources(self):
        expected = self.omnipathr.import_omnipath_enzsub(
            resources="HPRD", genesymbols=True
        )
        actual = op.requests.Enzsub.get(resources="HPRD", genesymbols=True)

        _assert_dataframes_equal(expected, actual)

    def test_fields(self):
        fields = ["isoforms", "ncbi_tax_id"]
        expected = self.omnipathr.import_omnipath_enzsub(
            resources="DEPOD", genesymbols=True, fields=fields
        )
        actual = op.requests.Enzsub.get(
            resources="DEPOD", genesymbols=True, fields=fields
        )

        _assert_dataframes_equal(expected, actual)

    def test_license(self):
        license = License.COMMERCIAL
        expected = self.omnipathr.import_omnipath_enzsub(
            resources="DEPOD", genesymbols=True, license=license.value
        )
        actual = op.requests.Enzsub.get(
            resources="DEPOD", genesymbols=True, license=license
        )

        _assert_dataframes_equal(expected, actual)


class TestIntercell(RTester):
    def test_categories(self):
        expected = sorted(self.omnipathr.get_intercell_categories())
        actual = sorted(op.requests.Intercell.categories())

        np.testing.assert_array_equal(expected, actual)

    def test_generic_categories(self):
        expected = sorted(self.omnipathr.get_intercell_generic_categories())
        actual = sorted(op.requests.Intercell.generic_categories())

        np.testing.assert_array_equal(expected, actual)

    def test_normal_run(self):
        expected = self.omnipathr.import_omnipath_intercell(
            causality="transmitter", scope="specific", entity_types="protein"
        )
        actual = op.requests.Intercell.get(
            causality="transmitter", scope="specific", entity_types="protein"
        )

        _assert_dataframes_equal(expected, actual)


class TestComplexes(RTester):
    def test_complex_genes(self):
        genes = ["ITGB1", "RET"]
        expected = self.omnipathr.import_omnipath_complexes(resources="CellPhoneDB")
        actual = op.requests.Complexes.get(database="CellPhoneDB")

        _assert_dataframes_equal(
            expected,
            actual,
            remove_metadata=[
                "n_sources",
                "n_resources",
                "n_references",
                "references_stripped",
            ],
        )

        expected = self.omnipathr.get_complex_genes(genes, complexes=expected)
        actual = op.requests.Complexes.complex_genes(genes, complexes=actual)

        _assert_dataframes_equal(
            expected,
            actual,
            remove_metadata=[
                "n_sources",
                "n_resources",
                "n_references",
                "references_stripped",
            ],
        )


class TestAnnotations(RTester):
    def test_normal_run(self):
        proteins = ["ITGB1", "RET"]
        expected = self.omnipathr.import_omnipath_annotations(
            proteins=proteins, resources="Phobius", genesymbols=False
        )
        actual = op.requests.Annotations.get(
            proteins=proteins, databases="Phobius", genesymbols=False
        )

        _assert_dataframes_equal(expected, actual)


class TestInteractions(RTester):
    def test_tfregulons_levels(self):
        fields = ["tfregulons_level", "tfregulons_tfbs"]
        expected = self.omnipathr.import_tf_target_interactions(
            resources=["ABS"], fields=fields, genesymbols=False
        )
        actual = op.interactions.TFtarget.get(
            resources=["ABS"], fields=fields, genesymbols=False
        )

        _assert_dataframes_equal(expected, actual)

    def test_dorothea_levels(self):
        fields = ["dorothea_level"]
        expected = self.omnipathr.import_dorothea_interactions(
            resources=["ABS"], dorothea_levels="D", fields=fields, genesymbols=False
        )
        actual = op.interactions.Dorothea.get(
            resources=["ABS"], dorothea_levels="D", fields=fields, genesymbols=False
        )

        _assert_dataframes_equal(expected, actual)

    def test_omnipath(self):
        expected = self.omnipathr.import_omnipath_interactions(
            resources="CA1", genesymbols=False
        )
        actual = op.interactions.OmniPath.get(resource="CA1", genesymbols=False)

        _assert_dataframes_equal(expected, actual)


class TestUtils(RTester):
    @pytest.mark.skip(reason="TODO: different index order, ref. mismatch")
    def test_import_intercell_network(self):
        from rpy2.robjects import ListVector

        interactions_params = {"resources": "CellPhoneDB"}
        transmitter_params = {"categories": "ligand"}
        receiver_params = {"categories": "receptor"}

        expected = self.omnipathr.import_intercell_network(
            interactions_param=ListVector(list(interactions_params.items())),
            transmitter_param=ListVector(list(transmitter_params.items())),
            receiver_param=ListVector(list(receiver_params.items())),
        )
        actual = op.interactions.import_intercell_network(
            interactions_params=interactions_params,
            transmitter_params=transmitter_params,
            receiver_params=receiver_params,
        )

        _assert_dataframes_equal(expected, actual)
