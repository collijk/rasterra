import math

import numpy as np
from affine import Affine
from rasterio.features import bounds, rasterize
from rasterio.windows import Window
from shapely.geometry import MultiPolygon, Polygon


def _geometry_window(
    data_transform: Affine,
    data_width: int,
    data_height: int,
    shapes: list[Polygon | MultiPolygon],
    pad_x: float = 0.0,
    pad_y: float = 0.0,
) -> Window:
    all_bounds = [bounds(shape, transform=~data_transform) for shape in shapes]

    cols = [
        x
        for (left, bottom, right, top) in all_bounds
        for x in (left - pad_x, right + pad_x, right + pad_x, left - pad_x)
    ]
    rows = [
        y
        for (left, bottom, right, top) in all_bounds
        for y in (top - pad_y, top - pad_y, bottom + pad_y, bottom + pad_y)
    ]

    row_start, row_stop = int(math.floor(min(rows))), int(math.ceil(max(rows)))
    col_start, col_stop = int(math.floor(min(cols))), int(math.ceil(max(cols)))

    window = Window(
        col_off=col_start,
        row_off=row_start,
        width=max(col_stop - col_start, 0),
        height=max(row_stop - row_start, 0),
    )

    # Make sure that window overlaps raster
    raster_window = Window(0, 0, data_width, data_height)
    window = window.intersection(raster_window)

    return window


def _window_transform(
    window: Window,
    transform: Affine,
) -> Affine:
    x, y = transform * (window.col_off or 0.0, window.row_off or 0.0)
    return Affine.translation(x - transform.c, y - transform.f) * transform


def raster_geometry_mask(
    data_transform: Affine,
    data_width: int,
    data_height: int,
    shapes: list[Polygon | MultiPolygon],
    all_touched: bool = False,
    invert: bool = False,
    crop: bool = False,
    pad_x: float = 0.0,
    pad_y: float = 0.0,
) -> tuple[np.ndarray, Affine, Window]:
    if crop and invert:
        raise ValueError("crop and invert cannot both be True.")

    window = _geometry_window(
        data_transform,
        data_width,
        data_height,
        shapes,
        pad_x=pad_x,
        pad_y=pad_y,
    )

    if crop:
        transform = _window_transform(window, data_transform)
        out_shape = (int(window.height), int(window.width))
    else:
        window = None
        transform = data_transform
        out_shape = (data_height, data_width)

    fill_value, mask_value = (0, 1) if invert else (1, 0)

    mask = rasterize(
        shapes,
        out_shape=out_shape,
        transform=transform,
        all_touched=all_touched,
        fill=fill_value,
        default_value=mask_value,
    ).astype(bool)

    return mask, transform, window
