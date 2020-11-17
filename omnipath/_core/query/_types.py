from typing import Union, Literal, Optional, Sequence

# TODO: I don't think 3.6 has Literal

Strseq_t = Optional[Union[str, Sequence[str]]]
Organism_t = Literal["human", "mouse", "rat"]
Bool_t = Optional[bool]
Str_t = Optional[str]
Int_t = Optional[int]
None_t = type(None)
