import pandas as pd

from omnipath._core.utils._orthology import translate_column
from omnipath._core.utils._homologene import download_homologene


class TestHomologene:
    def test_download_homologene(self):
        homologene = download_homologene(9606, 10090)

        expected_shape = (17312, 2)
        actual_shape = homologene.shape

        assert expected_shape == actual_shape

        expected_columns = ["source", "target"]
        actual_columns = homologene.columns

        assert all(expected_columns == actual_columns)


class TestOrthologyConversion:
    def test_complex_genes(self):
        df = pd.DataFrame(
            {
                "symbol": [
                    "CSF2RA_CSF2RB",  # one to many
                    "IFNL3_IFNLR1_IL10RB",  # 3 subunits
                    "HCST_KLRK1",  # one subunit missing
                    "CD8A_CD8B",  # 1 to 1
                    "IL4",  # 1 to 1 simple protein
                ]
            }
        )

        default = translate_column(
            df,
            column="symbol",
            id_type="genesymbol",
            target_organism=10090,
        )
        assert all(default["symbol"] == ["Cd8a_Cd8b1", "Il4"])

        to_many = translate_column(
            df,
            column="symbol",
            id_type="genesymbol",
            target_organism=10090,
            replace=True,
            keep_untranslated=False,
            one_to_many=2,
        )
        expected = {
            "Csf2ra_Csf2rb",
            "Csf2ra_Csf2rb2",
            "Ifnl2_Ifnlr1_Il10rb",
            "Ifnl3_Ifnlr1_Il10rb",
            "Cd8a_Cd8b1",
            "Il4",
        }

        assert to_many.shape == (6, 1)
        assert set(to_many["symbol"]) == expected

        keep_missing = translate_column(
            df,
            column="symbol",
            id_type="genesymbol",
            target_organism=10090,
            replace=False,
            keep_untranslated=True,
            one_to_many=2,
        )
        untranslated = keep_missing["symbol"].isin(["HCST_KLRK1"])
        assert untranslated.any()
        assert keep_missing[untranslated]["orthology_target"].isna().all()
