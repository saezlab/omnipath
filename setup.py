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
from pathlib import Path

from setuptools import setup, find_packages

try:
    from omnipath import __email__, __author__, __version__, __maintainer__
except ImportError:
    __author__ = "Michal Klein, Dénes Türei"
    __maintainer__ = "Michal Klein, Dénes Türei"
    __email__ = "turei.denes@gmail.com"
    __version__ = "1.0.1"


setup(
    # general
    name="omnipath",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    # version
    version=__version__,
    author=__author__,
    author_email=__email__,
    maintainer=__maintainer__,
    maintainer_email=__email__,
    # description
    description=Path("README.rst").read_text("utf-8").splitlines()[2],
    long_description=Path("README.rst").read_text("utf-8"),
    description_content_type="text/x-rst; charset=UTF-8",
    long_description_content_type="text/x-rst; charset=UTF-8",
    # links
    url="https://omnipathdb.org/",
    download_url="https://github.com/saezlab/omnipath/releases/",
    project_urls={
        "Documentation": "https://omnipath.readthedocs.io/en/latest",
        "Source Code": "https://github.com/saezlab/omnipath",
    },
    license="MIT",
    platforms=["Linux", "Unix", "MacOSX", "Windows"],
    # keywords
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
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Typing :: Typed",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    # package installation
    packages=find_packages(),
    zip_safe=False,
    python_required=">=3.7",
    include_package_data=False,
    # dependency_links = deplinks
    install_requires=list(
        map(
            str.strip,
            Path("requirements.txt").read_text("utf-8").splitlines(),
        )
    ),
    extras_require={
        "tests": [
            "tox>=3.20.1",
        ],
        "docs": [
            line
            for line in (Path("docs") / "requirements.txt")
            .read_text("utf-8")
            .splitlines()
            if not line.startswith("-r")
        ],
        "dev": ["pre-commit>=2.7.1", "bump2version"],
    },
)
