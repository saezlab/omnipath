from typing import Union, Optional, Sequence

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


Strseq_t = Optional[Union[str, Sequence[str]]]
Organism_t = Literal["human", "mouse", "rat"]
License_t = Literal["academic", "commercial"]
Bool_t = Optional[bool]
Str_t = Optional[str]
Int_t = Optional[int]
None_t = type(None)
