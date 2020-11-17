from docrep import DocstringProcessor

_general_get = """
Perform the query.

Parameters
----------
kwargs
    Parameters of the request. For more information about available values, see :meth:`params`.

Returns
-------
:class:`pandas.DataFrame`
    The result of this query."""
_interactions_datasets = """
    - :attr:`omnipath.constants.InteractionDataset.OMNIPATH`
    - :attr:`omnipath.constants.InteractionDataset.PATHWAY_EXTRA`
    - :attr:`omnipath.constants.InteractionDataset.KINASE_EXTRA`
    - :attr:`omnipath.constants.InteractionDataset.LIGREC_EXTRA`
    - :attr:`omnipath.constants.InteractionDataset.DOROTHEA`
    - :attr:`omnipath.constants.InteractionDataset.TF_TARGET`
    - :attr:`omnipath.constants.InteractionDataset.TF_MIRNA`
    - :attr:`omnipath.constants.InteractionDataset.TF_REGULONS`
    - :attr:`omnipath.constants.InteractionDataset.MIRNA_TARGET`
    - :attr:`omnipath.constants.InteractionDataset.LNCRNA_MRNA`"""
_validate = """
Validate the ``value`` for the :paramref:`param`.

Parameters
----------
value
    Value to validate.

Returns
-------
    The valid values."""
_query_resources = """
    Return the available resources for this query."""
_query_params = """
    Return the available values for each parameter, if available."""

d = DocstringProcessor(
    general_get=_general_get,
    interaction_datasets=_interactions_datasets,
    validate=_validate,
    query_params=_query_params,
    query_resources=_query_resources,
)
