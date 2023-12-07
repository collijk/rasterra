import typing

import numpy as np
from rasterio.crs import CRS as _CRS

RawCRS: typing.TypeAlias = _CRS | str | int | dict

NumpyDtype: typing.TypeAlias = (
    str | np.dtype | typing.Type[str | complex | bool | object]
)
NumpyUFuncMethod: typing.TypeAlias = typing.Literal[
    "reduce", "accumulate", "reduceat", "outer", "at", "__call__"
]
