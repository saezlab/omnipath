from typing import Any, Dict, Union, Mapping, Iterable, Optional
import logging

import pandas as pd

from omnipath._core.query import QueryType
from omnipath._core.utils._docs import d
from omnipath._core.requests._request import OmnipathRequestABC
from omnipath.constants._pkg_constants import Key, final

_MAX_N_PROTS = 600


@final
class Annotations(OmnipathRequestABC):
    """Request annotations from [OmniPath]_."""

    __string__ = frozenset({"source", "value"})
    __categorical__ = frozenset({"entity_type", "label", "source"})

    _query_type = QueryType.ANNOTATIONS

    def _modify_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        params.pop(Key.ORGANISM.value, None)

        return params

    @classmethod
    @d.dedent
    def params(cls) -> Dict[str, Any]:
        """%(query_params)s"""
        params = super().params()
        params.pop(Key.ORGANISM.value, None)

        return params

    @classmethod
    def get(
        cls,
        proteins: Optional[Union[str, Iterable[str]]] = None,
        resources: Optional[Union[str, Iterable[str]]] = None,
        force_full_download: bool = False,
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

            In order to download annotations for proteins complexes, write **'COMPLEX:'** before the gene symbols of
            the genes integrating the complex.
        resources
            Load the annotations only from these databases. See :meth:`resources` for available options.
        force_full_download
            Force the download of the entire annotations dataset. The full size of the data is ~1GB.
            We recommend to retrieve the annotations for a set of proteins or only from a few resources,
            depending on your interest.
        kwargs
            Additional query parameters.

        Returns
        -------
        :class:`pandas.DataFrame`
            A dataframe containing different gene/complex annotations.

        Notes
        -----
        There might be also a few miRNAs annotated. A vast majority of protein complex annotations are inferred
        from the annotations of the members: if all members carry the same annotation the complex inherits.
        """
        if proteins is None and resources is None and not force_full_download:
            raise ValueError(
                "Please specify `force_full_download=True` in order to download the full dataset."
            )
        inst = cls()

        if proteins is not None:
            if isinstance(proteins, str):
                proteins = (proteins,)
            proteins = sorted(set(proteins))

            logging.info(
                f"Downloading annotations for `{len(proteins)}` in `{_MAX_N_PROTS}` chunks"
            )

            return pd.concat(
                [
                    inst._get(
                        proteins=proteins[i * _MAX_N_PROTS : (i + 1) * _MAX_N_PROTS],
                        resources=resources,
                        **kwargs,
                    )
                    for i in range((len(proteins) // _MAX_N_PROTS) + 1)
                    if len(proteins[i * _MAX_N_PROTS : (i + 1) * _MAX_N_PROTS])
                ]
            )

        logging.info(
            f"Downloading annotations for all proteins from the following resources: `{list(set(resources))}`"
        )

        return inst._get(proteins=None, resources=resources, **kwargs)

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True

    def _post_process(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        return df


__all__ = [Annotations]
