import os
import typing

import numpy as np
from rasterio.crs import CRS as _CRS

FilePath: typing.TypeAlias = str | bytes | os.PathLike

Number: typing.TypeAlias = typing.Union[int, float, complex]
RawCRS: typing.TypeAlias = _CRS | str | int | dict

NumpyDtype: typing.TypeAlias = (
    str | np.dtype | typing.Type[str | complex | bool | object]
)
NumpyUFuncMethod: typing.TypeAlias = typing.Literal[
    "__call__",
    "reduce",
    "reduceat",
    "accumulate",
    "outer",
    "inner",
]
