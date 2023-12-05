from os import PathLike
from typing import TypeAlias, Union

import rasterio
from rasterio.merge import merge

from ._array import RasterArray

FilePath: TypeAlias = Union[str, bytes, PathLike]


def load_raster(path: FilePath) -> RasterArray:
    """Read a file and return its content as a string."""
    with rasterio.open(path) as f:
        data = f.read()
        if data.shape[0] == 1:
            return RasterArray(
                data[0],
                transform=f.transform,
                crs=f.crs,
                nodata=f.nodata,
            )
        else:
            raise NotImplementedError("Only single-band rasters are supported.")


def load_mf_raster(paths: list[FilePath]) -> RasterArray:
    """Read a file and return its content as a string."""
    with rasterio.open(paths[0]) as f:
        data = f.read()
        if data.shape[0] == 1:
            merged, transform = merge(paths)
            assert merged.shape[0] == 1
            return RasterArray(
                merged[0],
                transform=transform,
                crs=f.crs,
                nodata=f.nodata,
            )
        else:
            raise NotImplementedError("Only single-band rasters are supported.")
