import os
import typing

import numpy as np
import numpy.typing as npt
from rasterio.crs import CRS as _CRS

FilePath: typing.TypeAlias = str | bytes | os.PathLike[str]

RawCRS: typing.TypeAlias = _CRS | str | int | dict[str, typing.Any]

DataDtypes: typing.TypeAlias = (
    np.bool_
    | np.int8
    | np.int16
    | np.int32
    | np.int64
    | np.uint8
    | np.uint16
    | np.uint32
    | np.uint64
    | np.intp
    | np.uintp
    | np.float16
    | np.float32
    | np.float64
)
SupportedDtypes: typing.TypeAlias = int | bool | float | DataDtypes
RasterData: typing.TypeAlias = npt.NDArray[DataDtypes]
RasterMask: typing.TypeAlias = npt.NDArray[np.bool_]
NumpyUFuncMethod: typing.TypeAlias = typing.Literal[
    "__call__",
    "reduce",
    "reduceat",
    "accumulate",
    "outer",
    "at",
]
