from typing import Union

import numpy as np
from affine import Affine
from rasterio.warp import Resampling, reproject
from shapely.geometry import MultiPolygon, Polygon

from rasterra._features import raster_geometry_mask
from rasterra._plotting import Plotter

_RESAMPLING_MAP = {data.name: data for data in Resampling}

CRS_IN_TYPE = Union[str, int, dict, None]
CRS_OUT_TYPE = str


class RasterArray:
    def __init__(
        self,
        data: np.ndarray,
        transform: Affine = Affine.identity(),
        crs: CRS_IN_TYPE = None,
        nodata: Union[int, float, None] = None,
    ):
        """
        Initialize a RasterArray.

        Parameters
        ----------
        data
            2D NumPy array representing raster data.
        transform
            Affine transform to georeference the raster.
        crs
            Coordinate reference system.
        nodata
            Value representing no data.

        """
        self._data = data
        self._transform = transform
        self._crs = crs
        self._nodata = nodata

    @property
    def transform(self) -> Affine:
        """Affine transform to georeference the raster."""
        return self._transform

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Bounding box of the raster."""
        return (
            self.transform.c,
            self.transform.f + self.transform.e * self._data.shape[0],
            self.transform.c + self.transform.a * self._data.shape[1],
            self.transform.f,
        )

    @property
    def crs(self) -> str:
        """Coordinate reference system."""
        if self._crs is None:
            raise ValueError("Coordinate reference system is not set.")
        return str(self._crs)

    @property
    def nodata(self) -> Union[int, float, None]:
        """Value representing no data."""
        return self._nodata

    @property
    def no_data_mask(self) -> np.ndarray:
        """Mask representing no data."""
        if self._nodata is None:
            return np.zeros_like(self._data, dtype=bool)
        elif np.isnan(self._nodata):
            return np.isnan(self._data)
        elif np.isinf(self._nodata):
            return np.isinf(self._data)
        else:
            return np.equal(self._data, self._nodata)

    @property
    def nbytes(self) -> int:
        """Number of bytes in the raster."""
        return self._data.nbytes

    def set_crs(self, new_crs: CRS_IN_TYPE) -> "RasterArray":
        if self._crs is not None:
            raise ValueError(
                "Coordinate reference system is already set. Use to_crs() to reproject "
                "to a new coordinate reference system."
            )
        return RasterArray(self._data.copy(), self._transform, new_crs, self._nodata)

    def to_crs(self, new_crs: str, resampling: str = "nearest") -> "RasterArray":
        """Reproject the raster to a new coordinate reference system."""
        if self._crs is None:
            raise ValueError("Coordinate reference system is not set.")
        resampling = _RESAMPLING_MAP[resampling]

        new_data, transform = reproject(
            source=self._data,
            src_transform=self._transform,
            src_crs=self._crs,
            src_nodata=self._nodata,
            dst_crs=new_crs,
            resampling=resampling,
        )
        return RasterArray(new_data[0], transform, new_crs, nodata=self._nodata)

    def set_nodata(self, new_nodata: Union[int, float]) -> "RasterArray":
        new_data = self._data.copy()
        if self._nodata is not None:
            new_data[self.no_data_mask] = new_nodata
        return RasterArray(new_data, self._transform, self._crs, new_nodata)

    def unset_nodata(self) -> "RasterArray":
        """Unset value representing no data."""
        return RasterArray(self._data.copy(), self._transform, self._crs, nodata=None)

    def clip(
        self,
        shapes: list[Union[Polygon, MultiPolygon]],
    ) -> "RasterArray":
        _, transform, window = raster_geometry_mask(
            data_transform=self.transform,
            data_width=self._data.shape[1],
            data_height=self._data.shape[0],
            shapes=shapes,
            crop=True,
        )

        x_start, x_end = window.col_off, window.col_off + window.width
        y_start, y_end = window.row_off, window.row_off + window.height
        new_data = self._data[y_start:y_end, x_start:x_end].copy()
        return RasterArray(new_data, transform, self.crs, nodata=self.nodata)

    def mask(
        self,
        shapes: list[Union[Polygon, MultiPolygon]],
        fill_value: Union[int, float],
        all_touched: bool = False,
        invert: bool = False,
    ) -> "RasterArray":
        shape_mask, *_ = raster_geometry_mask(
            data_transform=self.transform,
            data_width=self._data.shape[1],
            data_height=self._data.shape[0],
            shapes=shapes,
            all_touched=all_touched,
            invert=invert,
        )
        new_data = self._data.copy()
        new_data[shape_mask] = fill_value

        return RasterArray(new_data, self.transform, self.crs, nodata=self.nodata)

    def __repr__(self) -> str:
        out = "RasterArray\n"
        out += "===========\n"
        out += f"dimensions : {self._data.shape[1]}, {self._data.shape[0]} (x, y)\n"
        out += f"resolution : {self.transform.a}, {self.transform.e} (x, y)\n"
        bounds = ", ".join(
            str(s)
            for s in [self.bounds[0], self.bounds[2], self.bounds[1], self.bounds[3]]
        )
        out += f"extent     : {bounds} (xmin, xmax, ymin, ymax)\n"
        out += f"crs        : {self._crs}\n"
        out += f"nodata     : {self._nodata}\n"
        out += f"dtype      : {self._data.dtype}\n"
        return out

    @property
    def plot(self) -> Plotter:
        return Plotter(self._data, self.no_data_mask, self.transform)
