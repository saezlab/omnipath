from enum import Enum


class License(Enum):  # noqa: D101
    COMMERCIAL = "commercial"
    ACADEMIC = "academic"


class Synonym(Enum):  # noqa: D101
    PTMS = "enzsub"
    ENZSUB = PTMS
    COMPLEX = "complexes"


class PrettyMessage(Enum):  # noqa: D101
    ENZSUB = "enzyme-substrate relationships"
    INTERACTIONS = "interactions"
    COMPLEXES = "protein complexes"
    ANNOTATIONS = "annotation records"
    INTERCELL = "intercellular communication role records"


class DefaultField(Enum):  # noqa: D101
    ENZSUB = ("sources", "references", "curation_effort")
    INTERACTIONS = ENZSUB


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


class QuerySynonym(Enum):  # noqa: D101
    ORGANISM = QueryParams.ORGANISMS
    RESOURCE = QueryParams.RESOURCES
    DATABASE = RESOURCE
    DATABASES = RESOURCE
    DOROTHEA_LEVEL = QueryParams.DOROTHEA_LEVELS
    TFREGULONS_LEVELS = DOROTHEA_LEVEL
    TFREGULONS_LEVEL = DOROTHEA_LEVEL
    GENESYMBOL = QueryParams.GENESYMBOLS
    FIELD = QueryParams.FIELDS
    DATASET = QueryParams.DATASETS
    # DIRECTED = QueryParams.DIRECTED
    ENTITY_TYPE = QueryParams.ENTITY_TYPES


__all__ = [License, Synonym, PrettyMessage, DefaultField, QueryParams, QuerySynonym]
