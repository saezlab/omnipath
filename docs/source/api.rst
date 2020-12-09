API
===

Import Omnipath as::

    import omnipath as op

Requests
~~~~~~~~

.. module::omnipath.requests
.. currentmodule:: omnipath

.. autosummary::
    :toctree: api

    requests.Annotations
    requests.Complexes
    requests.Enzsub
    requests.Intercell
    requests.SignedPTMs

Interactions
~~~~~~~~~~~~

.. module::omnipath.interactions
.. currentmodule:: omnipath

.. autosummary::
    :toctree: api

    interactions.AllInteractions
    interactions.Dorothea
    interactions.KinaseExtra
    interactions.LigRecExtra
    interactions.OmniPath
    interactions.PathwayExtra
    interactions.PostTranslational
    interactions.TFmiRNA
    interactions.TFtarget
    interactions.Transcriptional
    interactions.lncRNAmRNA
    interactions.miRNA
    interactions.import_intercell_network

Other
~~~~~

Constants
---------

.. module::omnipath.constants
.. currentmodule:: omnipath

.. autosummary::
    :toctree: api

    constants.InteractionDataset
    constants.License
    constants.Organism

Options
-------

.. module::omnipath
.. currentmodule:: omnipath

.. autosummary::
    :toctree: api

    omnipath.clear_cache
    omnipath.options
