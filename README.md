# Python client for the OmniPath web service

**This package is in planning stage, without any useful functionality yet.**
Contributions are welcome, please contact us at omnipathdb@gmail.com, open
issues or send pull requests. Otherwise please check out the resources below
and return to us later.

## The OmniPath database

OmniPath is a database of
* Protein-protein, TF target and miRNA-mRNA interactions
* Enzyme-PTM relationships
* Protein complexes
* Annotations of protein function, structure, localization, expression
* Intercellular communication roles of proteins

See more about OmniPath at [its webpage][1], in our [recent preprint][2],
and in our first [paper from 2016][3], especially in its [supplementary
material][4].

## The Python client

The data is available by a web service at https://omnipathdb.org/,
this repository hosts a Python package for querying this web service and
downloading data into data frames or dictionaries.

## The Python package for OmniPath is pypath, isn't it?

``pypath`` (https://github.com/saezlab/pypath) is tool for building the
OmniPath databases in a fully customizable way. We recommend to use pypath
if you want to:

* Tailor the database building to your needs
* Include resources not available in the public web service
* Use the rich Python APIs available for the database objects
* Make sure the data from the original sources is the most up-to-date
* Use the methods in ``pypath.inputs`` to download data from resources
* Use the various extra tools in ``pypath.utils``, e.g. for identifier
  translation, homology translation, querying Gene Ontology, working with
  protein sequences, processing BioPAX, etc.

## Is there an R client?

Yes there is. The R/Bioconductor package ``OmnipathR`` you may find in
[github][5] or in [BiocondictoR][6].
OmnipathR currently supports all features of the web service.

## Cytoscape

We even have a [Cytoscape plug-in][7].
With the plug-in you are able to load networks into Cytoscape and access
certain (not all) annotations of the proteins.

[1] https://omnipathdb.org/
[2] https://www.biorxiv.org/content/10.1101/2020.08.03.221242v2
[3] https://rdcu.be/m53B
[4] https://static-content.springer.com/esm/art%3A10.1038%2Fnmeth.4077/MediaObjects/41592_2016_BFnmeth4077_MOESM495_ESM.pdf
[5] https://github.com/saezlab/OmnipathR
[6] http://bioconductor.org/packages/3.12/bioc/html/OmnipathR.html
[7] https://apps.cytoscape.org/apps/omnipath