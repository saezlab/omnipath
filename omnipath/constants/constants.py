from enum import Enum, unique


@unique
class License(Enum):  # noqa: D101
    COMMERCIAL = "commercial"
    ACADEMIC = "academic"


@unique
class QueryType(Enum):  # noqa: D101
    ENZSUB = "enzsub"
    INTERACTIONS = "interactions"
    COMPLEXES = "complexes"
    ANNOTATIONS = "annotations"
    INTERCELL = "intercell"
    QUERIES = "queries"
    # INFO = "info"


@unique
class QueryParams(Enum):  # noqa: D101
    GENESYMBOLS = "genesymbols"
    RESOURCES = "resources"
    DATASETS = "datasets"
    ORGANISMS = "organisms"
    DOROTHEA_LEVELS = "dorothea_levels"
    DOROTHEA_METHODS = "dorothea_methods"
    SOURCE_TARGET = "source_target"
    FIELDS = "fields"
    FORMAT = "format"
    DIRECTED = "directed"
    SIGNED = "signed"
    ENZYMES = "enzymes"
    SUBSTRATES = "substrates"
    PARTNERS = "partners"
    PROTEINS = "proteins"
    ENTITY_TYPES = "entity_types"
    SOURCES = "sources"
    TARGETS = "targets"
    RESIDUES = "residues"
    MODIFICATION = "modification"
    SCOPE = "scope"
    ASPECT = "aspect"
    SOURCE = "source"
    CATEGORIES = "categories"
    PARENT = "parent"
    TRANSMITTER = "transmitter"
    RECEIVER = "receiver"
    SECRETED = "secreted"
    PLASMA_MEMBRANE_TRANSMEMBRANE = "plasma_membrane_transmembrane"
    PLASMA_MEMBRANE_PERIPHERAL = "plasma_membrane_peripheral"
    TOPOLOGY = "topology"
    CAUSALITY = "causality"
    LICENSE = "license"
    PASSWORD = "password"


@unique
class InteractionDataset(Enum):  # noqa: D101
    OMNIPATH = "omnipath"
    PATHWAY_EXTRA = "pathwayextra"
    KINASE_EXTRA = "kinaseextra"
    LIGREC_EXTRA = "ligrecextra"
    DOROTHEA = "dorothea"
    TF_TARGET = "tf_target"
    TF_MIRNA = "tf_mirna"  # ?
    TF_REGULONS = "tfregulons"
    MIRNA_TARGET = "mirnatarget"
    LNCRNA_MRNA = "lncrna_mrna"


@unique
class DorotheaLevels(Enum):  # noqa: D101
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# TODO: what about E


# TODO: is this needed?
@unique
class TFtargetLevels(Enum):  # noqa: D101
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


@unique
class Organism(Enum):  # noqa: D101
    HUMAN = 9606
    RAT = 10116
    MOUSE = 10090


__all__ = [
    License,
    Organism,
    QueryType,
    QueryParams,
    DorotheaLevels,
    TFtargetLevels,
    InteractionDataset,
]
