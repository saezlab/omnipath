from typing import Any, Dict, Mapping, Optional, Sequence

import pandas as pd

from omnipath.constants import Organism, QueryType, QueryParams
from omnipath.requests._request import OmnipathRequestABC


class Annotations(OmnipathRequestABC):
    """Class capable of requesting annotations from [OmniPath]_."""

    def __init__(self):
        super().__init__(QueryType.ANNOTATIONS)

    def get(
        self,
        proteins: Sequence[str],
        resources: Optional[Sequence[str]] = None,
        genesymbols: bool = True,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Import annotations from [OmniPath]_.

        Retrieves protein annotations about function, localization, expression, structure and other properties of
        proteins from `OmniPath <https://omnipathdb.org/annotations>`__.

        Parameters
        ----------
        proteins
            Genes or proteins for which annotations will be retrieved (UniProt IDs, HGNC Gene Symbols or miRBase IDs).

            It is also possible to download annotations for protein complexes. To do so, write **'COMPLEX:'**
            before the gene symbols of the genes integrating the complex.

            Maximum number of proteins for `1` request is `600`.
        resources
            To get available resources, see :meth:`resources`.
        **kwargs
            Keyword arguments.

        Returns
        -------
        :class:`pandas.DataFrame`
            A dataframe containing different gene/complex annotations.

        Notes
        -----
        There might be also a few miRNAs annotated. A vast majority of protein complex annotations are inferred
        from the annotations of the members: if all members carry the same annotation the complex inherits.
        """
        # TODO: docrep
        # TODO: force_full_download?
        # TODO: wide?
        # TODO: more than 600 proteins?

        if len(proteins) > 600:
            raise ValueError("Please request at most `600` proteins.")

        return super().get(
            Organism.HUMAN,
            proteins=proteins,
            resources=resources,
            genesymbols=genesymbols,
            **kwargs,
        )

    def _validate_params(
        self, params: Optional[Dict[str, Any]], add_defaults: bool = True
    ) -> Dict[str, Any]:
        params = super()._validate_params(params, add_defaults=True)
        params.pop(QueryParams.ORGANISMS.value, None)

        return params

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True


__all__ = [Annotations]
