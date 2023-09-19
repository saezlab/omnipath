from typing import List, Union, Literal, Optional
from functools import partial
import re
import logging
import warnings

import requests

import pandas as pd

from omnipath._core.utils import _options as opt
from omnipath._core.downloader._downloader import Downloader


def static_tables() -> pd.DataFrame:
    """
    List the static tables available from OmniPath

    Returns
    -------
    A data frame with metadata about the static tables.
    """
    refile = re.compile(
        r'<a href="[^"]+">([^<]+)</a>'
        r"\s+(\d{2}-\w+-\d{4}) (\d{2}:\d{2})"
        r"\s+(\d+)[\r\n]*"
    )

    req = requests.get(opt.options.static_url, stream=True)

    result = pd.DataFrame(
        [
            refile.match(line.decode("utf-8")).groups()
            for line in req.raw.readlines()[5:-2]
        ],
        columns=["name", "date", "time", "size"],
    )

    result["url"] = [f"{opt.options.static_url}/{name}" for name in result.name]

    result = pd.concat(
        [
            result,
            result.name.str.extract(
                r"(?P<query>[\w]+)_"
                r"(?P<resource>\w+)_"
                r"(?P<organism>\d+)\.tsv\.gz",
                expand=True,
            ),
        ],
        axis=1,
    )

    return result


def static_table(
    query: Literal["annotations", "interactions"],
    resource: str,
    organism: Union[int, str],
    strict_evidences: bool = True,
    dorothea_levels: Optional[List[Literal["A", "B", "C", "D"]]] = None,
    wide: bool = True,
) -> pd.DataFrame:
    """
    Download a static table from OmniPath.

    A few resources and datasets are available also as plain TSV files and
    can be accessed without TLS. The purpose of these tables is to make the
    most often used OmniPath data available on computers with configuration
    issues. These tables are not the recommended way to access OmniPath
    data, and a warning is issued each time they are accessed.

    Parameters
    ----------
    query
        A query type such as "annotations" or "interactions".
    resource
        Name of the resource or dataset, such as
        "CollecTRI" or "PROGENy".
    organism
        NCBI Taxonomy of the organism: 9606 for human,
        10090 for mouse and 10116 for rat.
    strict_evidences
        Restrict the evidences to the queried
        datasets and resources. If set to False, the directions and effect signs
        and references might be based on other datasets and resources.
    wide
        Convert the annotation table to wide format, which
        corresponds more or less to the original resource. If the data comes
        from more than one resource a list of wide tables will be returned.
        See examples at ``pivot_annotations``.
    dorothea_levels
        A list of confidence levels in case the accessed resource is DoRothEA.
        In dorothea, every TF-target interaction has a confidence score
        ranging from A to E, being A the most reliable interactions.
        By default here we take A, B and C level interactions
        (``["A", "B", "C"]``).
        It is to note that E interactions are not available in OmniPath.

    Returns
    -------
    A data frame with the requested resource.
    """
    msg = (
        f"Accessing `{resource}` as a static table. This is not the "
        "recommended way to access OmniPath data; it is only a backup "
        "plan for situations when our server or your computer is "
        "experiencing issues."
    )
    logging.warning(msg)
    warnings.warn(msg)  # noqa: B028

    organism = str(organism)
    query_l = query.lower()
    resource_l = resource.lower()
    resources = () if resource_l in ("collectri", "dorothea") else (resource,)
    datasets = () if resources else (resource_l,)

    if query_l == "annotations":
        from omnipath._core.requests._annotations import Annotations as req_cls

    elif query_l == "interactions":
        from omnipath._core.requests.interactions._interactions import (
            AllInteractions as req_cls,
        )
        from omnipath._core.requests.interactions._interactions import (
            InteractionDataset,
        )

    s = static_tables()

    s = s[
        (s["query"] == query_l)
        & (s.resource.str.lower() == resource_l)
        & (s.organism == organism)
    ].reset_index()

    if s.shape[0] == 0:
        msg = (
            f"No static table is available for query `{query}`, resource "
            f"`{resource}` and organism `{organism}`. For a list of the "
            "available tables see `static_tables()`."
        )
        logging.error(msg)
        raise ValueError(msg)

    url = s.url[0]
    logging.debug(f"Downloading static table from `{url}`.")
    downloader = Downloader()
    callback = partial(
        pd.read_csv,
        sep="\t",
        header=0,
        low_memory=False,
        compression="gzip",
    )
    result = downloader.maybe_download(url, callback=callback, is_final=True)
    logging.debug(f"Ready downloading static table from `{url}`.")
    omnipath_req = req_cls()
    omnipath_req._last_param = {
        "original": {"strict_evidences": strict_evidences},
        "final": {"resources": resources, "datasets": datasets},
    }
    omnipath_req._wide = wide
    omnipath_req._datasets = {InteractionDataset(d) for d in datasets}
    logging.debug("Static table: converting dtypes.")
    result = omnipath_req._convert_dtypes(result)
    logging.debug("Static table: post-pocessing.")
    result = omnipath_req._post_process(result)

    if resource_l == "dorothea":
        logging.debug("Static table: filtering for DoRothEA confidence levels.")
        dorothea_levels = set(dorothea_levels)
        result = result[result.dorothea_level.isin(dorothea_levels)]

    return result
