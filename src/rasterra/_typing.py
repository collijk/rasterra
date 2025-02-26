import os
import typing

import numpy as np
import numpy.typing as npt
from rasterio.crs import CRS as _CRS

type FilePath = str | bytes | os.PathLike[str]

type RawCRS = _CRS | str | int | dict[str, typing.Any]

DataDtypes = (
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
type SupportedDtypes = int | bool | float | DataDtypes
type RasterData = npt.NDArray[DataDtypes]
type RasterMask = npt.NDArray[np.bool_]
type NumpyUFuncMethod = typing.Literal[
    "__call__",
    "reduce",
    "reduceat",
    "accumulate",
    "outer",
    "at",
]
