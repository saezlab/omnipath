from abc import ABC, ABCMeta
from enum import Enum, EnumMeta, unique
from typing import Any, Callable
from functools import wraps

from enum_tools import document_enum
import enum_tools.documentation as documentation

documentation.INTERACTIVE = True


def _pretty_raise_enum(cls: EnumMeta, fun: Callable) -> Callable:
    @wraps(fun)
    def wrapper(*args, **kwargs) -> Enum:
        try:
            return fun(*args, **kwargs)
        except ValueError as e:
            _cls, value, *_ = args
            e.args = (cls._format(value),)
            raise e

    if not issubclass(cls, ErrorFormatter):
        raise TypeError(f"Class `{cls}` must be subtype of `ErrorFormatter`.")
    elif not len(cls.__members__):
        # empty enum, for class hierarchy
        return fun

    return wrapper


class NoValue(Enum):
    """Enumeration which hides its :paramref:`value`."""

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self.name}>"


class ErrorFormatter(ABC):  # noqa: D101
    __error_format__ = "Invalid value `{}` for `{}`. Valid options are: `{}`."

    @classmethod
    def _format(cls, value: Any) -> str:
        """Format the error message for invalid ``value``."""
        return cls.__error_format__.format(
            value, cls.__name__, [m.value for m in cls.__members__.values()]
        )


class FormatterMeta(EnumMeta, ABCMeta):  # noqa: D101
    def __call__(cls, *args, **kw):  # noqa: D102
        if getattr(cls, "__error_format__", None) is None:
            raise TypeError(
                f"Can't instantiate class `{cls.__name__}` "
                f"without `__error_format__` class attribute."
            )
        return super().__call__(*args, **kw)

    def __new__(cls, clsname, superclasses, attributedict):  # noqa: D102
        res = super().__new__(cls, clsname, superclasses, attributedict)
        res.__new__ = _pretty_raise_enum(res, res.__new__)
        return res


class PrettyEnumMixin(ErrorFormatter, NoValue, metaclass=FormatterMeta):
    """Enum mixin that that pretty prints when user uses invalid value."""

    @property
    def s(self) -> str:
        """Return the :paramref:`value` as :class:`str`."""
        return str(self.value)


@unique
@document_enum
class License(PrettyEnumMixin):
    """License types."""

    ACADEMIC = "academic"  # doc: Academic license.
    COMMERCIAL = "commercial"  # doc: Commercial license.
    NON_PROFIT = "non_profit"  # doc: Non-profit license.
    FOR_PROFIT = "for_profit"  # doc: For-profit license.
    IGNORE = "ignore"  # doc: Ignore the license type.


@unique
class InteractionDataset(PrettyEnumMixin):
    """Available interaction datasets in [OmniPath]_."""

    DOROTHEA = "dorothea"
    KINASE_EXTRA = "kinaseextra"
    LIGREC_EXTRA = "ligrecextra"
    LNCRNA_MRNA = "lncrna_mrna"
    MIRNA_TARGET = "mirnatarget"
    OMNIPATH = "omnipath"
    PATHWAY_EXTRA = "pathwayextra"
    TF_MIRNA = "tf_mirna"
    TF_REGULONS = "tfregulons"
    TF_TARGET = "tf_target"


@unique
@document_enum
class Organism(PrettyEnumMixin):
    """Organism types."""

    HUMAN = "human"  # doc: NCIB taxonomy id: 9606.
    MOUSE = "mouse"  # doc: NCIB taxonomy id: 10090.
    RAT = "rat"  # doc: NCIB taxonomy id: 10116.

    def __new__(cls, value: str):  # noqa: D102
        obj = object.__new__(cls)
        obj._code = {"human": 9606, "rat": 10116, "mouse": 10090}[value]
        return obj

    @property
    def code(self) -> int:
        """Return the code of this organism."""
        return self._code


__all__ = [
    License,
    Organism,
    InteractionDataset,
]
