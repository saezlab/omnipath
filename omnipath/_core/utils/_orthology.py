from itertools import product

import numpy as np
import pandas as pd

from omnipath._core.utils._homologene import download_homologene

CPLEX_PREFIX = "COMPLEX:"


# Replace list elements with dictionary values
def _replace_subunits(lst, my_dict, one_to_many):
    result = []
    for x in lst:
        if x in my_dict:
            value = my_dict[x]

            if not isinstance(value, list):
                value = [value]

            if len(value) > one_to_many:
                result.append(np.nan)
            else:
                result.append(value)
        else:
            result.append(np.nan)
    return result


def _generate_orthologs(data, column, map_dict, one_to_many):
    df = data[[column]].drop_duplicates().set_index(column)
    data[column] = data[column].replace(CPLEX_PREFIX, "", regex=True)

    df["subunits"] = df.index.str.split("_")
    df["subunits"] = df["subunits"].apply(
        _replace_subunits,
        args=(
            map_dict,
            one_to_many,
        ),
    )
    df = df["subunits"].explode().reset_index()

    grouped = (
        df.groupby(column).filter(lambda x: x["subunits"].notna().all()).groupby(column)
    )

    # Generate all possible subunit combinations within each group
    complexes = []
    for name, group in grouped:
        if group["subunits"].isnull().all():
            continue
        subunit_lists = [list(x) for x in group["subunits"]]
        complex_combinations = list(product(*subunit_lists))
        for complex in complex_combinations:
            complexes.append((name, "_".join(complex)))

    # Create output DataFrame
    col_names = ["orthology_source", "orthology_target"]
    result = pd.DataFrame(complexes, columns=col_names).set_index("orthology_source")

    return result


def translate_column(
    data,
    column,
    id_type,
    target_organism,
    replace=True,
    keep_untranslated=False,
    source_organism=9606,
    one_to_many=1,
):
    """
    Generate orthologs for a given column in a DataFrame.

    Parameters
    ----------
    data : pandas.DataFrame
        Input DataFrame.
    column : str
        Column name to translate.
    id_type : str
        Type of ID to use for homology conversion. Can be one of 'genesymbol', 'gene_id'.
    target_organism : int
        NCBI Taxonomy ID of the target organism.
    replace : bool, optional
        Whether to replace the original column with the translated values. Default is True.
    keep_untranslated : bool, optional
        Whether to keep the original column in the output DataFrame. Default is False. Ignored if `replace` is True.
    source_organism : int
        NCBI Taxonomy ID of the source organism. Default is 9606 (human).
    one_to_many : int, optional
        Maximum number of orthologs allowed per gene. Default is 1.

    Returns
    -------
    Resulting DataFrame with translated column.

    """
    if not isinstance(one_to_many, int):
        raise ValueError("`one_to_many` should be a positive integer!")

    id_types = ["genesymbol", "gene_id"]
    if id_type not in id_types:
        raise ValueError(f"`id_type` should be one of: {id_types}")

    # get orthologs
    source_organism, target_organism = str(source_organism), str(target_organism)
    map_df = download_homologene(source_organism, target_organism, id_type).set_index(
        "source"
    )
    map_dict = map_df.groupby(level=0)["target"].apply(list).to_dict()
    map_data = _generate_orthologs(data, column, map_dict, one_to_many)

    # join orthologs
    data = (
        data.set_index(column)
        .merge(map_data, left_index=True, right_index=True, how="left")
        .reset_index(names=column)
    )

    # replace orthologs
    if replace:
        data[column] = data["orthology_target"]
        data = data.drop(columns=["orthology_target"])

    elif keep_untranslated:
        data[column] = data.apply(
            lambda x: (
                x["orthology_target"]
                if not pd.isnull(x["orthology_target"])
                else x[column]
            ),
            axis=1,
        )

    data = data.dropna(subset=[column])
    return data
