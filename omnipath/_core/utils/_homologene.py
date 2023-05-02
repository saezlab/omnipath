import pandas as pd

from omnipath._core.downloader._downloader import Downloader

# NOTE: this downloads homologene data from github
# Either way this is not a great solution, as homologene was last updated in 2014...
RAW_TAXA_URL = (
    "https://raw.githubusercontent.com/oganm/homologene/master/data-raw/taxData.tsv"
)
HOMOLOGENE_URL = (
    "https://raw.githubusercontent.com/oganm/homologene/master/data-raw/homologene2.tsv"
)


def _get_homologene_raw():
    dwnld = Downloader()
    homologene = (
        dwnld.maybe_download(
            HOMOLOGENE_URL,
            callback=pd.read_table,
        )
        .astype(str)
        .rename(
            columns={
                "Gene.Symbol": "genesymbol",
                "Gene.ID": "gene_id",
                "Taxonomy": "ncbi_taxid",
                "HID": "hid",
            }
        )
        .set_index("hid")
    )
    return homologene


def show_homologene():
    """Show the homologene taxa data"""
    dwnld = Downloader()
    return dwnld.maybe_download(RAW_TAXA_URL, callback=pd.read_table)


def download_homologene(source_organism, target_organism, id_type="genesymbol"):
    """
    Download homologene information for a given source and target organism.

    Parameters
    ----------
    source_organism : str
        Source organism name.
    target_organism : str
        Target organism name.
    id_type : str
        Type of ID to use for homology conversion. Can be one of 'genesymbol', 'gene_id'.

    Returns
    -------
    A pandas DataFrame with homologene information.

    """
    homologene = _get_homologene_raw()

    source_df = homologene[(homologene["ncbi_taxid"] == source_organism)][[id_type]]
    target_df = homologene[(homologene["ncbi_taxid"] == target_organism)][[id_type]]

    homologene = pd.merge(
        source_df,
        target_df,
        right_index=True,
        left_index=True,
        suffixes=("_source", "_target"),
        how="inner",
    )
    homologene = homologene.reset_index().rename(
        {f"{id_type}_source": "source", f"{id_type}_target": "target"}, axis=1
    )
    homologene = homologene[["source", "target"]]

    return homologene
