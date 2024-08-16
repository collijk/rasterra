from typing import Literal

import affine
import numpy as np
from rasterio import merge as rio_merge

from rasterra._array import RasterArray


def merge(
    rasters: list[RasterArray],
    method: Literal["first", "last", "min", "max", "sum", "count"] = "first",
) -> RasterArray:
    """Merge a list of rasters into a single raster."""
    match_properties = [
        "crs",
        "dtype",
        "no_data_value",
        "x_resolution",
        "y_resolution",
    ]
    for p in match_properties:
        ref_property = getattr(rasters[0], p)
        if not all(getattr(raster, p) == ref_property for raster in rasters):
            msg = f"All rasters must have the same {p}."
            raise ValueError(msg)
    crs = rasters[0].crs
    dtype = rasters[0].dtype
    no_data_value = rasters[0].no_data_value
    x_res, y_res = rasters[0].resolution

    merge_method = rio_merge.MERGE_METHODS[method]

    left, bottom, right, top = zip(*[raster.bounds for raster in rasters], strict=False)
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
