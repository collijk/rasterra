from typing import Literal

import affine
import numpy as np
from rasterio import merge as rio_merge

from rasterra._array import RasterArray


def validate_property(
    rasters: list[RasterArray],
    property_name: str,
    *,
    is_nan: bool = False,
) -> None:
    ref_property = getattr(rasters[0], property_name)

    def _property_matches(r: RasterArray) -> bool:
        return bool(
            (is_nan and np.isnan(getattr(r, property_name)))
            or getattr(r, property_name) == ref_property
        )  # fmt: skip

    if not all(_property_matches(raster) for raster in rasters):
        msg = f"All rasters must have the same {property_name}."
        raise ValueError(msg)


def merge(
    rasters: list[RasterArray],
    method: Literal["first", "last", "min", "max", "sum", "count"] = "first",
) -> RasterArray:
    """Merge a list of rasters into a single raster."""
    validate_property(rasters, "crs")
    crs = rasters[0].crs
    validate_property(rasters, "dtype")
    dtype = rasters[0].dtype
    no_data_isnan = np.issubdtype(dtype, np.floating) and np.isnan(
        rasters[0].no_data_value
    )
    validate_property(rasters, "no_data_value", is_nan=no_data_isnan)
    no_data_value = rasters[0].no_data_value
    validate_property(rasters, "resolution")
    x_res, y_res = rasters[0].resolution
    y_res = -y_res  # rasterio uses negative y resolution

    merge_method = rio_merge.MERGE_METHODS[method]

    left, right, bottom, top = zip(*[raster.bounds for raster in rasters], strict=False)
    dst_w, dst_s, dst_e, dst_n = min(left), min(bottom), max(right), max(top)

    output_width = int(round((dst_e - dst_w) / x_res))
    output_height = int(round((dst_n - dst_s) / y_res))

    dest = no_data_value * np.ones((output_height, output_width), dtype=dtype)
    for raster in rasters:
        # Find the row and column offset of the input raster
        row_off = int(round((dst_n - raster.y_max) / y_res))
        col_off = int(round((raster.x_min - dst_w) / x_res))
        window = (
            slice(row_off, row_off + raster.height),
            slice(col_off, col_off + raster.width),
        )
        dest_region = dest[window]
        if np.isnan(no_data_value):
            dest_mask = np.isnan(dest_region)
        elif np.issubdtype(dtype, np.floating):
            dest_mask = np.isclose(dest_region, no_data_value)
        else:
            dest_mask = dest_region == no_data_value

        source_mask = raster.no_data_mask
        merge_method(dest_region, raster.to_numpy(), dest_mask, source_mask)

    dest_transform = affine.Affine(
        a=x_res,
        b=0,
        c=dst_w,
        d=0,
        e=-y_res,
        f=dst_n,
    )
    return RasterArray(
        dest,
        transform=dest_transform,
        crs=crs,
        no_data_value=no_data_value,
    )
