from typing import Any, Union, Mapping, Iterable, Optional
import logging

import pandas as pd

from omnipath._core.query import QueryType
from omnipath._core.requests._request import OrganismGenesymbolsRemover
from omnipath.constants._pkg_constants import final


@final
class Complexes(OrganismGenesymbolsRemover):
    """Request information about protein complexes from [OmniPath]_."""

    __string__ = frozenset(
        {
            "name",
            "components",
            "components_genesymbols",
            "stoichiometry",
            "references",
            "identifiers",
        }
    )
    __categorical__ = frozenset({"sources"})

    _query_type = QueryType.COMPLEXES

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True

    @classmethod
    def complex_genes(
        cls,
        genes: Union[str, Iterable[str]],
        complexes: Optional[pd.DataFrame] = None,
        total_match: bool = False,
    ) -> pd.DataFrame:
        """
        Get all the molecular complexes for a given ``genes``.

        This function returns all the molecular complexes where an input set of genes participate. User can choose
        to retrieve every complex where any of the input genes participate or just retrieve these complexes where
        all the genes in input set participate together.

        Parameters
        ----------
        genes
            The genes for which complexes will be retrieved (hgnc format).
        complexes
            Complex data from :meth:`get`. If `None`, new request will be made.
        total_match
            If `True`, get only complexes where all the genes participate together, otherwise get complexes
            where any of the genes participate.

        Returns
        -------
        :class:`pandas.DataFrame`
            The filtered ``complexes``.
        """
        if isinstance(genes, str):
            genes = (genes,)
        genes = tuple(set(genes))
        if not len(genes):
            raise ValueError("No genes have been selected.")

        if complexes is None:
            logging.info("Fetching complexes from the server")
            complexes = cls.get()
        if not isinstance(complexes, pd.DataFrame):
            raise TypeError(
                f"Expected `complexes` to be of type `pandas.DataFrame`, found `{type(complexes)}`."
            )

        if complexes.empty:
            logging.warning("Complexes are empty")
            return complexes

        col = "components_genesymbols"
        if col not in complexes:
            raise KeyError(f"Unable to find `{col}` in `{complexes.columns}`.")

        reduction = all if total_match else any

        return complexes.loc[
            complexes[col]
            .str.split("_")
            .apply(lambda needles: reduction(n in genes for n in needles))
        ].reset_index(drop=True)


__all__ = [Complexes]
