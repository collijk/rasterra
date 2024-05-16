from collections.abc import Sequence
from typing import Any, TypeAlias

import rasterio
from rasterio.merge import merge
from rasterio.windows import from_bounds
from shapely import Polygon

from rasterra._array import RasterArray
from rasterra._typing import FilePath

Bounds: TypeAlias = (
    tuple[float, float, float, float] | tuple[int, int, int, int] | Polygon
)


def load_raster(
    path: FilePath,
    bounds: Bounds | None = None,
) -> RasterArray:
    """Load a raster from a file."""

    with rasterio.open(path) as f:
        if bounds is not None:
            if isinstance(bounds, Polygon):
                bounds = bounds.bounds
            window = from_bounds(*bounds, transform=f.transform)
            data = f.read(window=window, boundless=True)
            transform = f.window_transform(window)
        else:
            data = f.read()
            transform = f.transform

        if data.shape[0] == 1:
            return RasterArray(
                data[0],
                transform=transform,
                crs=f.crs,
                no_data_value=f.nodata,
            )
        else:
            msg = "Only single-band rasters are supported"
            raise NotImplementedError(msg)


def write_raster(
    raster: RasterArray,
    path: FilePath,
    **kwargs: Any,
) -> None:
    """Write a raster to a file."""
    meta = {
        "driver": "GTiff",
        "height": raster.shape[0],
        "width": raster.shape[1],
        "count": 1,
        "dtype": raster.dtype,
        "crs": raster.crs,
        "transform": raster.transform,
        "nodata": raster.no_data_value,
        **kwargs,
    }

    with rasterio.open(path, "w", **meta) as f:
        f.write(raster.to_numpy(), 1)


def load_mf_raster(paths: Sequence[FilePath]) -> RasterArray:
    """Load multiple files into a single raster."""
    with rasterio.open(paths[0]) as f:
        data = f.read()
        if data.shape[0] == 1:
            merged, transform = merge(paths)
            return RasterArray(
                merged[0],
                transform=transform,
                crs=f.crs,
                no_data_value=f.nodata,
            )
        else:
            msg = "Only single-band rasters are supported."
            raise NotImplementedError(msg)
