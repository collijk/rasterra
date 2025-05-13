from collections.abc import Sequence
from typing import Any

import rasterio
from rasterio.merge import merge
from rasterio.windows import from_bounds
from shapely import Polygon

from rasterra._array import RasterArray
from rasterra._typing import FilePath

type Bounds = tuple[float, float, float, float] | tuple[int, int, int, int] | Polygon


def get_raster_metadata(path: FilePath) -> dict[str, Any]:
    """Get metadata from a raster file without loading the data.

    Returns:
        dict: Dictionary containing raster metadata including:
            - driver: The raster driver (e.g., 'GTiff')
            - height: Number of rows
            - width: Number of columns
            - count: Number of bands
            - dtype: Data type
            - crs: Coordinate reference system
            - transform: Affine transformation matrix
            - nodata: No data value
            - bounds: Spatial bounds (left, bottom, right, top)
            - res: Pixel resolution (x_res, y_res)
            - tags: Dataset tags/metadata
            - units: Units of measurement (if specified)
            - descriptions: Band descriptions
            - scales: Band scale factors
            - offsets: Band offset values
            - colormap: Color interpretation for each band
            - block_shapes: Block shapes for each band
            - compression: Compression type if any
            - interleaving: Pixel/band interleaving type
            - is_tiled: Whether the raster is tiled
            - name: Dataset name/identifier
            - profile: Full raster profile with all metadata
            - statistics: Per-band statistics (min, max, mean, std)
            - nodatavals: No data values for each band
            - indexes: Band indexes
            - overviews: Number of overview levels for each band
            - mask_flags: Mask flags for each band
            - meta: Additional metadata dictionary
            - rpcs: Rational polynomial coefficients if available
            - gcps: Ground control points if available
            - subdatasets: List of subdatasets if present
            - photometric: Color interpretation type
            - is_masked: Whether the dataset has a mask
            - band_descriptions: Tuple of band names/descriptions
            - dtypes: Data types for each band
            - sharing: Whether dataset arrays share memory
            - dataset_mask: Dataset-wide mask flags
            - transform_method: Method used for coordinate transforms
            - width_height: (width, height) tuple
    """
    with rasterio.open(path) as f:
        return {
            "driver": f.driver,
            "height": f.height,
            "width": f.width,
            "count": f.count,
            "crs": f.crs,
            "dtypes": f.dtypes,
            "transform": f.transform,
            "nodata": f.nodata,
            "bounds": f.bounds,
            "res": f.res,
            "tags": f.tags(),
            "units": f.units,
            "descriptions": f.descriptions,
            "scales": f.scales,
            "offsets": f.offsets,
            "block_shapes": f.block_shapes,
            "compression": f.compression.value if f.compression else None,
            "interleaving": f.interleaving.value if f.interleaving else None,
            "is_tiled": f.is_tiled,
            "name": f.name,
            "statistics": f.stats(),
            "nodatavals": f.nodatavals,
            "indexes": f.indexes,
            "overviews": [f.overviews(i) for i in range(1, f.count + 1)]
            if f.count > 0
            else None,
            "mask_flags": f._mask_flags,  # noqa: SLF001
            "rpcs": f.rpcs,
            "gcps": f.gcps,
            "subdatasets": f.subdatasets,
            "photometric": f.photometric,
            "band_descriptions": f.descriptions,
        }


def load_raster(
    path: FilePath,
    bounds: Bounds | None = None,
    band: int | None = None,
) -> RasterArray:
    """Load a raster from a file.

    Parameters
    ----------
    path : FilePath
        Path to the raster file
    bounds : Bounds | None, optional
        Bounds to load, by default None
    band : int | None, optional
        Band number to load (1-based indexing). If None, verifies single-band raster.
    """
    with rasterio.open(path) as f:
        if band is None and f.count > 1:
            msg = (
                f"Raster has {f.count} bands. Specify which band to "
                "load using the 'band' argument"
            )
            raise ValueError(msg)

        band_to_read = 1 if band is None else band

        if bounds is not None:
            if isinstance(bounds, Polygon):
                bounds = bounds.bounds
            window = from_bounds(*bounds, transform=f.transform)
            data = f.read(band_to_read, window=window, boundless=True)
            transform = f.window_transform(window)
        else:
            data = f.read(band_to_read)
            transform = f.transform

        return RasterArray(
            data,
            transform=transform,
            crs=f.crs,
            no_data_value=f.nodata,
        )


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


def load_mf_raster(paths: Sequence[FilePath], band: int | None = None) -> RasterArray:
    """Load multiple files into a single raster.

    Parameters
    ----------
    paths : Sequence[FilePath]
        Paths to the raster files to merge
    band : int | None, optional
        Band number to load (1-based indexing). If None, verifies single-band raster.
    """
    # Verify all files have compatible metadata
    with rasterio.open(paths[0]) as f:
        ref_crs = f.crs
        ref_dtype = f.dtypes[0]
        ref_nodata = f.nodata
        ref_count = f.count

        if band is None and ref_count > 1:
            msg = (
                f"First raster has {ref_count} bands. Specify which band to "
                "load using the 'band' argument"
            )
            raise ValueError(msg)

    # Check all other files match
    for path in paths[1:]:
        with rasterio.open(path) as f:
            p = str(path)
            if f.crs != ref_crs:
                msg = f"CRS mismatch: {p} has CRS {f.crs}, expected {ref_crs}"
                raise ValueError(msg)
            if f.dtypes[0] != ref_dtype:
                msg = (
                    f"Dtype mismatch: {p} has dtype {f.dtypes[0]}, expected {ref_dtype}"
                )
                raise ValueError(msg)
            if f.nodata != ref_nodata:
                msg = (
                    f"NoData mismatch: {p} has nodata {f.nodata}, expected {ref_nodata}"
                )
                raise ValueError(msg)
            if f.count != ref_count:
                msg = (
                    f"Band count mismatch: {p} has {f.count} bands, "
                    f"expected {ref_count}"
                )
                raise ValueError(msg)

    band_to_read = 1 if band is None else band
    merged, transform = merge(paths, indexes=[band_to_read])

    return RasterArray(
        merged[0],
        transform=transform,
        crs=ref_crs,
        no_data_value=ref_nodata,
    )
