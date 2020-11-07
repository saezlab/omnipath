#  This file is part of the `omnipath` python module
#
#  Copyright
#  2020
#  Heidelberg University
#
#  File author(s): Dénes Türei (turei.denes@gmail.com)
#
#  Distributed under the MIT (expat) License.
#  See accompanying file LICENSE or copy at
#      https://opensource.org/licenses/MIT
#
#  Website: http://omnipathdb.org/
#

__revision__ = "$Id$"

from setuptools import setup, find_packages

__version__ = "0.0.1"


def _read_requirements():

    with open("requirements.txt") as fp:

        requirements = [
            name.strip() for name in fp if name and not name.startswith("-")
        ]

    return requirements


setup(
    name="omnipath",
    version=__version__,
    maintainer="Dénes Türei",
    maintainer_email="turei.denes@gmail.com",
    author="Dénes Türei",
    author_email="turei.denes@gmail.com",
    description_content_type="text/x-rst; charset=UTF-8",
    keywords=sorted(
        {
            "protein",
            "mRNA",
            "miRNA",
            "DNA",
            "signaling",
            "SignaLink",
            "SIGNOR",
            "InnateDB",
            "IntAct",
            "Reactome",
            "MPPI",
            "NCI-PID",
            "DIP",
            "MatrixDB",
            "PANTHER",
            "PhosphoSite",
            "PhosphoPoint",
            "DEPOD",
            "SPIKE",
            "KEGG",
            "Autophagy",
            "ARN",
            "NRF2ome",
            "Guide to Pharmacology",
            "UniProt",
            "BioPAX",
            "Ensembl",
            "Surfaceome",
            "Exocarta",
            "Vesiclepedia",
            "Matrisome",
            "Human Protein Atlas",
            "Compleat",
            "CORUM",
            "ComplexPortal",
            "BioGRID",
            "STRING",
            "ICELLNET",
            "Cell Surface Protein Atlas",
            "COSMIC",
            "Cancer Gene Census",
            "IntOGen",
            "TopDB",
            "iTALK",
            "Human Plasma Membrane Receptome",
            "EMBRACE",
            "ELM",
            "phospho.ELM",
            "CancerSEA",
            "ComPPI",
            "CellPhoneDB",
            "DGIdb",
            "DisGeNet",
            "PAZAR",
            "ORegAnno",
            "TRED",
            "DoRothEA",
            "TRRD",
            "CPAD",
            "regulation",
            "phosphorylation",
            "kinase",
            "phosphatase",
            "dephosphorylation",
            "directed graph",
            "annotations",
            "cancer",
            "complexes",
            "intercellular communication",
            "HGNC",
            "GPCRdb",
            "MSigDB",
            "GSEA",
            "Phobius",
            "Phosphatome",
            "NetPath",
            "gene",
            "gene symbol",
            "mouse",
            "rat",
            "HomoloGene",
            "integrin",
            "adhesion",
            "receptor",
            "ligand",
            "transporter",
            "ion channel",
            "disease",
            "activity flow",
            "transcription",
            "PPI",
            "subcellular localization",
            "pathway",
            "signaling pathway",
        }
    ),
    # description = 'Molecular signaling prior knowledge in Python',
    license="GPLv3",
    platforms=["Linux", "Unix", "MacOSX", "Windows"],
    url="https://omnipathdb.org/",
    download_url="https://github.com/saezlab/omnipath/releases/",
    project_url=("Git repo", "https://github.com/saezlab/omnipath"),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    # package installation
    packages=list(set(find_packages() + ["omnipath"])),
    include_package_data=True,
    # dependency_links = deplinks
    install_requires=_read_requirements(),
    extras_require={
        "tests": [
            "tox>=3.20.1",
        ],
        "docs": [
            "sphinx>=3.3.0",
        ],
        "dev": [
            "pre-commit>=2.7.1",
        ],
    },
)
