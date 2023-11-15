from typing import Union

import numpy as np
from affine import Affine
from rasterio.warp import Resampling, reproject

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

    @crs.setter
    def crs(self, new_crs: CRS_IN_TYPE) -> None:
        if self._crs is not None:
            raise ValueError(
                "Coordinate reference system is already set. Use to_crs() to reproject "
                "to a new coordinate reference system."
            )
        self._crs = new_crs

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

    @property
    def nodata(self) -> Union[int, float, None]:
        """Value representing no data."""
        return self._nodata

    @nodata.setter
    def nodata(self, new_nodata: Union[int, float]) -> None:
        if self._nodata is not None:
            self._data[self._data == self._nodata] = new_nodata
        self._nodata = new_nodata

    @property
    def plot(self) -> Plotter:
        return Plotter(self._data, self.transform)

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
