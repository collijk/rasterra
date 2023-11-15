from pathlib import Path

import rasterio

from ._array import RasterArray


def read_file(path: str | Path) -> RasterArray:
    """Read a file and return its content as a string."""
    with rasterio.open(path) as f:
        return RasterArray(
            f.read(),
            transform=f.transform,
            crs=f.crs,
            nodata=f.nodata,
        )
