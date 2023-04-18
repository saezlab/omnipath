from typing import Any, Dict, Union, Mapping, Iterable, Optional
import logging

import pandas as pd

from omnipath._misc import dtypes
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
        wide: bool = False,
        **kwargs,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
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

            If `None`, fetch annotations for all available genes or proteins.
        resources
            Load the annotations only from these databases. See :meth:`resources` for available options.
            If `None`, use all available resources.
        force_full_download
            Force the download of the entire annotations dataset. The full size of the data is ~1GB.
            We recommend to retrieve the annotations for a set of proteins or only from a few resources,
            depending on your interest.
        wide
            Pivot the annotations from a long to a wide dataframe format, reconstituting the format
            of the original resource.
        kwargs
            Additional query parameters.

        Returns
        -------
        :class:`pandas.DataFrame`
            A dataframe containing different molecule (protein, complex, gene, miRNA, small molecule) annotations.
            If `wide` is `True` and the result contains more than one resource, a `dict` of dataframes
            will be returned, one for each resource.

        Notes
        -----
        There might be also a few miRNAs and small molecules annotated. A vast majority of protein complex
        annotations are inferred from the annotations of the members: if all members carry the same annotation
        the complex inherits.
        """
        if proteins is None and resources is None and not force_full_download:
            raise ValueError(
                "Please specify `force_full_download=True` in order to download the full dataset."
            )
        res_info = (
            "all resources"
            if resources is None
            else f"the following resources: `{[resources] if isinstance(resources, str) else sorted(set(resources))}`"
        )
        inst = cls()
        inst._wide = wide

        if proteins is not None:
            if isinstance(proteins, str):
                proteins = (proteins,)
            proteins = sorted(set(proteins))

            logging.info(
                f"Downloading annotations for `{len(proteins)}` in `{_MAX_N_PROTS}` chunks from {res_info}"
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

        logging.info(f"Downloading annotations for all proteins from {res_info}")

        return inst._get(proteins=None, resources=resources, **kwargs)

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True

    def _post_process(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if self._wide:
            df = self.pivot_annotations(df)

        return df

    @classmethod
    def pivot_annotations(
        cls,
        df: pd.DataFrame,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Annotations from narrow to wide format

        Converts the annotations from a long to a wide dataframe format,
        reconstituting the format of the original resource.

        Parameters
        ----------
        df
            An annotation dataframe.

        Returns
        -------
        :class:`pandas.DataFrame` or `dict`
            A dataframe of various molecule (protein, complex, gene, miRNA, small molecule) annotations.
            If the data contains more than one resource, a `dict` of dataframes will be returned, one for each
            resource.
        """
        if df.source.nunique() > 1:
            return {
                resource: cls.pivot_annotations(df[df.source == resource])
                for resource in df.source.unique()
            }

        index_cols = ["record_id", "uniprot", "genesymbol", "label"]

        if "entity_type" in df.label.values:
            df = df.drop("entity_type", axis=1)

        else:
            index_cols.append("entity_type")

        return dtypes.auto_dtype(
            df.drop("source", axis=1)
            .set_index(index_cols)
            .unstack("label")
            .droplevel(axis=1, level=0)
            .reset_index()
            .drop("record_id", axis=1)
        )


__all__ = [Annotations]
