from typing import Any, Optional, Union

import numpy as np
from affine import Affine
from rasterio.warp import Resampling, calculate_default_transform, reproject

_RESAMPLING_MAP = {data.name: data for data in Resampling}


class RasterArray:
    def __init__(
        self,
        data: np.ndarray,
        transform: Affine = Affine.identity(),
        crs: Optional[Any] = None,
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
        return self._crs

    @crs.setter
    def crs(self, new_crs: str) -> None:
        if self._crs is not None:
            raise ValueError(
                "Coordinate reference system is already set. Use to_crs() to reproject "
                "to a new coordinate reference system."
            )
        self._crs = new_crs

    @property
    def nodata(self) -> Union[int, float, None]:
        """Value representing no data."""
        return self._nodata

    @nodata.setter
    def nodata(self, new_nodata: Union[int, float]) -> None:
        if self._nodata is not None:
            self._data[self._data == self._nodata] = new_nodata
        self._nodata = new_nodata

    def to_crs(
        self,
        new_crs: str,
        resampling_method: Union[str, Resampling] = "nearest",
    ) -> "RasterArray":
        """
        Reproject the raster to a new coordinate reference system.

        Parameters
        ----------
        new_crs
            The target coordinate reference system.
        resampling_method
            Resampling method to use during CRS transformation.

        Returns
        -------
        RasterArray
            A new RasterArray with update coordinate reference system.
        """
        if isinstance(resampling_method, str):
            resampling_method = _RESAMPLING_MAP[resampling_method]

        out, out_transform = reproject(
            source=self._data,
            src_transform=self.transform,
            src_crs=self.crs,
            dst_crs=new_crs,
            resampling=resampling_method,
        )

        return RasterArray(out[0], out_transform, new_crs, self.nodata)

    def resample(
        self,
        scale_factor: float,
        resampling_method: Union[str, Resampling] = "nearest",
    ) -> "RasterArray":
        """Resample the raster data to a higher or lower resolution.

        Parameters
        ----------
        scale_factor
            Factor to scale the raster data. Use a scale factor > 1 to increase
            the resolution (upsample) and a scale factor < 1 to decrease the
            resolution (downsample).
        resampling_method
            Resampling method to use during CRS transformation.

        Returns
        -------
        RasterArray
            A new RasterArray with resampled data.
        """
        if isinstance(resampling_method, str):
            resampling_method = _RESAMPLING_MAP[resampling_method]

        new_width = int(self._data.shape[1] / scale_factor)
        new_height = int(self._data.shape[0] / scale_factor)
        new_transform = self.transform * self.transform.scale(
            (self._data.shape[1] / new_width),
            (self._data.shape[0] / new_height),
        )

        out, out_transform = reproject(
            source=self._data,
            src_transform=self.transform,
            src_crs=self.crs,
            dst_transform=new_transform,
            dst_crs=self.crs,
            resampling=resampling_method,
        )

        return RasterArray(out[0], out_transform, self.crs, self.nodata)

    def clip(self, bounds: tuple[float, float, float, float]) -> "RasterArray":
        """
        Clip the raster to a bounding box.

        Parameters
        ----------
        bounds
            Tuple specifying (left, bottom, right, top).

        Returns
        -------
        RasterArray
            A new RasterArray with clipped data.
        """

        left, bottom, right, top = bounds
        left, bottom = self.transform * (left, bottom)
        right, top = self.transform * (right, top)

        window = self._data.window(left, bottom, right, top)
        out = self._data.read(window=window, masked=True)

        new_transform = calculate_default_transform(
            src_crs=self.crs,
            dst_crs=self.crs,
            width=out.shape[2],
            height=out.shape[1],
            left=left,
            bottom=bottom,
            right=right,
            top=top,
        )

        return RasterArray(out[0], new_transform, self.crs, self.nodata)
