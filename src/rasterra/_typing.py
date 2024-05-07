import os
import typing

import numpy as np
import numpy.typing as npt
from rasterio.crs import CRS as _CRS

FilePath: typing.TypeAlias = str | bytes | os.PathLike[str]

RawCRS: typing.TypeAlias = _CRS | str | int | dict[str, typing.Any]

SupportedDtypes: typing.TypeAlias = np.float64 | np.int_ | np.bool_
RasterData: typing.TypeAlias = npt.NDArray[SupportedDtypes]
RasterMask: typing.TypeAlias = npt.NDArray[np.bool_]
NumpyUFuncMethod: typing.TypeAlias = typing.Literal[
    "__call__",
    "reduce",
    "reduceat",
    "accumulate",
    "outer",
    "inner",
]
