from urllib.parse import urljoin, quote_plus
import json

import pytest

import numpy as np
import pandas as pd

from omnipath import options
from omnipath.constants import Organism, InteractionDataset
from omnipath._core.requests import Intercell
from omnipath.constants._pkg_constants import Key, Endpoint
from omnipath._core.requests.interactions._utils import import_intercell_network
from omnipath._core.requests.interactions._interactions import (
    TFmiRNA,
    Dorothea,
    OmniPath,
    TFtarget,
    KinaseExtra,
    LigRecExtra,
    PathwayExtra,
    AllInteractions,
    Transcriptional,
    miRNA,
    lncRNAmRNA,
)


class TestInteractions:
    def test_all_excluded_excluded(self):
        with pytest.raises(
            ValueError, match=r"After excluding `\d+` datasets, none were left."
        ):
            AllInteractions.get(exclude=list(InteractionDataset))

    def test_invalid_excluded_datasets(self):
        with pytest.raises(
            ValueError, match=r"Invalid value `foo` for `InteractionDataset`."
        ):
            AllInteractions.get(exclude="foo")

    def test_graph_source_target(self):
        interaction = pd.DataFrame(
            {
                "source": ["alpha", "beta", "gamma"],
                "target": [0, 1, 0],
                "source_genesymbol": "bar",
                "target_genesymbol": "baz",
            }
        )
        src, tgt = AllInteractions._get_source_target_cols(interaction)

        assert src == "source_genesymbol"
        assert tgt == "target_genesymbol"

        src, tgt = AllInteractions._get_source_target_cols(
            interaction[
                interaction.columns.difference(
                    ["source_genesymbol", "target_genesymbol"]
                )
            ]
        )

        assert src == "source"
        assert tgt == "target"

    @pytest.mark.parametrize(
        "interaction",
        [
            PathwayExtra,
            KinaseExtra,
            LigRecExtra,
            miRNA,
            TFmiRNA,
            lncRNAmRNA,
            Dorothea,
            TFtarget,
            OmniPath,
        ],
    )
    def test_resources(
        self, cache_backup, interaction, interaction_resources: bytes, requests_mock
    ):
        url = urljoin(options.url, Endpoint.RESOURCES.s)
        data = json.loads(interaction_resources)
        requests_mock.register_uri(
            "GET", f"{url}?format=json", content=interaction_resources
        )

        resources = interaction.resources()
        for resource in resources:
            assert {
                InteractionDataset(d)
                for d in data[resource][Key.QUERIES.s][
                    interaction._query_type.endpoint
                ][Key.DATASETS.s]
            } & interaction()._datasets
        assert requests_mock.called_once

    def test_invalid_organism(self):
        with pytest.raises(
            ValueError, match=r"Invalid value `foo` for `Organism`. Valid options are:"
        ):
            AllInteractions.get(**{Key.ORGANISM.s: "foo"})

    @pytest.mark.parametrize("organisms", list(Organism))
    def test_valid_organism(
        self, cache_backup, organisms, requests_mock, interaction_resources
    ):
        url = urljoin(options.url, AllInteractions._query_type.endpoint)
        datasets = quote_plus(",".join(sorted(d.value for d in InteractionDataset)))
        requests_mock.register_uri(
            "GET",
            f"{url}?datasets={datasets}&fields=curation_effort%2Creferences%2Csources%2Ctype&"
            f"format=tsv&organisms={organisms.code}",
            content=interaction_resources,
        )

        AllInteractions.get(organism=organisms, format="tsv")
        AllInteractions.get(organisms=organisms.value, format="tsv")
        assert requests_mock.called_once

    def test_dorothea_params(self):
        params = Dorothea.params()

        assert "dorothea_levels" in params
        assert "dorothea_methods" in params
        assert "tfregulons_levels" not in params
        assert "tfregulons_methods" not in params
        assert Key.DATASETS.s not in params

    def test_tftarget_params(self):
        params = TFtarget.params()

        assert "dorothea_levels" not in params
        assert "dorothea_methods" not in params
        assert "tfregulons_levels" in params
        assert "tfregulons_methods" in params
        assert Key.DATASETS.s not in params

    @pytest.mark.parametrize(
        "interaction", [OmniPath, Transcriptional, AllInteractions]
    )
    def test_transcriptional_params(self, interaction):
        params = interaction.params()

        assert "dorothea_levels" in params
        assert "dorothea_methods" in params
        assert "tfregulons_levels" in params
        assert "tfregulons_methods" in params
        assert Key.DATASETS.s not in params

    @pytest.mark.parametrize(
        "interaction",
        [PathwayExtra, KinaseExtra, LigRecExtra, miRNA, TFmiRNA, lncRNAmRNA],
    )
    def test_rest_params(self, interaction):
        params = interaction.params()

        assert "dorothea_levels" not in params
        assert "dorothea_methods" not in params
        assert "tfregulons_levels" not in params
        assert "tfregulons_methods" not in params
        assert Key.DATASETS.s not in params


class TestUtils:
    def test_import_intercell_network(
        self,
        cache_backup,
        requests_mock,
        interactions_data: bytes,
        transmitters_data: bytes,
        receivers_data: bytes,
        import_intercell_result: pd.DataFrame,
    ):
        interactions_url = urljoin(options.url, AllInteractions._query_type.endpoint)
        intercell_url = urljoin(options.url, Intercell._query_type.endpoint)

        # interactions
        requests_mock.register_uri(
            "GET",
            f"{interactions_url}?datasets=omnipath&dorothea_levels=A&fields=curation_effort%2C"
            f"references%2Csources%2Ctype&format=tsv",
            content=interactions_data,
        )
        # transmitter
        requests_mock.register_uri(
            "GET",
            f"{intercell_url}?categories=ligand&causality=trans&format=tsv&scope=generic",
            content=transmitters_data,
        )
        # receiver
        requests_mock.register_uri(
            "GET",
            f"{intercell_url}?categories=receptor&causality=rec&format=tsv&scope=generic",
            content=receivers_data,
        )

        res = import_intercell_network(
            include=InteractionDataset.OMNIPATH,
            transmitter_params={"categories": "ligand"},
            interactions_params={"dorothea_levels": "A"},
            receiver_params={"categories": "receptor"},
        )

        assert isinstance(res, pd.DataFrame)
        np.testing.assert_array_equal(res.shape, import_intercell_result.shape)

        np.testing.assert_array_equal(res.index, import_intercell_result.index)
        np.testing.assert_array_equal(res.columns, import_intercell_result.columns)
        np.testing.assert_array_equal(res.dtypes, import_intercell_result.dtypes)
        np.testing.assert_array_equal(
            pd.isnull(res), pd.isnull(import_intercell_result)
        )
        np.testing.assert_array_equal(
            res.values[~pd.isnull(res)],
            import_intercell_result.values[~pd.isnull(import_intercell_result)],
        )
        assert len(requests_mock.request_history) == 3
