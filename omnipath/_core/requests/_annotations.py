from typing import Any, Dict, Mapping

import pandas as pd

from omnipath._core.query import QueryType
from omnipath._core.utils._docs import d
from omnipath._core.requests._request import OmnipathRequestABC
from omnipath.constants._pkg_constants import Key, final


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
        # fmt: off
        if not any(
            kw in kwargs
            for kw in ("proteins", "resources", "databases")
        ):

            raise ValueError(
                "Downloading the entire annotations database is not allowed "
                "due to its huge size (>1GB). Please query a set of proteins "
                "or a few resources, depending on your interest."
            )
        # fmt: on

        if "proteins" in kwargs:

            proteins = kwargs["proteins"]
            if isinstance(proteins, str):
                proteins = (proteins,)
            proteins = tuple(set(proteins))

            if len(proteins) > 600:
                # fmt: off
                raise ValueError(
                    "Cannot download annotations for "
                    "more than `600` proteins yet."
                )
                # fmt: on

            kwargs["proteins"] = proteins

        return cls()._get(**kwargs)

    def _resource_filter(self, data: Mapping[str, Any], **_) -> bool:
        return True

    def _post_process(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        return df


__all__ = [Annotations]
