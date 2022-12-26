|PyPI| |Downloads| |CI| |Docs| |Coverage|

Python client for the OmniPath web service
==========================================

Installation
------------
You can install ``omnipath`` by running::

    pip install omnipath

The OmniPath database
---------------------

OmniPath is a database of:

* Protein-protein, TF target and miRNA-mRNA interactions
* Enzyme-PTM relationships
* Protein complexes
* Annotations of protein function, structure, localization, expression
* Intercellular communication roles of proteins

To learn more about OmniPath, you can visit its `website`_, or read our recent `preprint`_
or our first `paper from 2016`_, especially its `supplementary material`_.

The Python client
-----------------
The data is available through a web service hosted on this `website`_.
This repository hosts a Python package for querying this web service and
downloading data into data frames or dictionaries.


The Python package for OmniPath is pypath, isn't it?
----------------------------------------------------
`pypath`_ is a tool for building the OmniPath databases in a fully customizable way.
We recommend to use pypath if you want to:

* Tailor the database building to your needs
* Include resources not available in the public web service
* Use the rich Python APIs available for the database objects
* Make sure the data from the original sources is the most up-to-date
* Use the methods in ``pypath.inputs`` to download data from resources
* Use the various extra tools in ``pypath.utils``, e.g. for identifier
  translation, homology translation, querying Gene Ontology, working with
  protein sequences, processing BioPAX, etc.

Is there an R client?
---------------------
Yes there is. The R/Bioconductor package ``OmnipathR`` you may find on `GitHub <https://github.com/saezlab/OmnipathR>`_
or in `Bioconductor <http://bioconductor.org/packages/3.12/bioc/html/OmnipathR.html>`_.
The R client currently supports all features of the web service.

Cytoscape
---------
We even have a `Cytoscape plug-in`_.
With the plug-in you are able to load networks into Cytoscape and access
certain (not all) annotations of the proteins.

.. |PyPI| image:: https://img.shields.io/pypi/v/omnipath.svg
    :target: https://pypi.org/project/omnipath
    :alt: PyPI

.. |Downloads| image:: https://pepy.tech/badge/omnipath
    :target: https://pepy.tech/project/omnipath
    :alt: Downloads

.. |CI| image:: https://img.shields.io/github/actions/workflow/status/saezlab/omnipath/ci.yml?branch=master
    :target: https://github.com/saezlab/omnipath/actions?query=workflow:CI
    :alt: CI

.. |Coverage| image:: https://codecov.io/gh/saezlab/omnipath/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/saezlab/omnipath
    :alt: Coverage

.. |Docs|  image:: https://img.shields.io/readthedocs/omnipath
    :target: https://omnipath.readthedocs.io/en/latest
    :alt: Documentation

.. _website : https://omnipathdb.org/
.. _Cytoscape plug-in : https://apps.cytoscape.org/apps/omnipath
.. _pypath : https://github.com/saezlab/pypath
.. _preprint : https://www.biorxiv.org/content/10.1101/2020.08.03.221242v2
.. _paper from 2016 : https://www.nature.com/articles/nmeth.4077
.. _supplementary material : https://static-content.springer.com/esm/art%3A10.1038%2Fnmeth.4077/MediaObjects/41592_2016_BFnmeth4077_MOESM495_ESM.pdf
