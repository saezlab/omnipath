from typing import Any, Dict, Mapping, Optional, Sequence

import pandas as pd

from omnipath.constants import Organism, QueryType, QueryParams
from omnipath.requests._request import OmnipathRequestABC


class Annotations(OmnipathRequestABC):
    def __init__(self):
        super().__init__(QueryType.ANNOTATIONS)

    def get(
        self,
        proteins: Sequence[str],
        resources: Optional[Sequence[str]] = None,
        genesymbols: bool = True,
        **kwargs,
    ) -> pd.DataFrame:
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
