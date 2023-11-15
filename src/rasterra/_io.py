from pathlib import Path

import rasterio

from ._array import RasterArray


def read_file(path: str | Path) -> RasterArray:
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
