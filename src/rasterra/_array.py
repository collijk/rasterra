import numbers
import typing

import geopandas as gpd
import numpy as np
from affine import Affine
from numpy.core.multiarray import flagsobj
from rasterio.crs import CRS
from rasterio.warp import Resampling, reproject
from shapely.geometry import MultiPolygon, Polygon

from rasterra._features import raster_geometry_mask
from rasterra._plotting import Plotter
from rasterra._typing import FilePath, Number, NumpyDtype, NumpyUFuncMethod, RawCRS

_RESAMPLING_MAP = {data.name: data for data in Resampling}

NO_DATA_UNSET = None


class RasterArray(np.lib.mixins.NDArrayOperatorsMixin):
    def __init__(
        self,
        data: np.ndarray,
        transform: Affine = Affine.identity(),
        crs: RawCRS | None = None,
        no_data_value: Number | None = NO_DATA_UNSET,
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
        no_data_value
            Value representing no data.

        """
        self._ndarray = data
        self._transform = transform
        if crs is not None and not isinstance(crs, CRS):
            crs = CRS.from_user_input(crs)
        self._crs: CRS | None = crs
        self._no_data_value = no_data_value

    # ----------------------------------------------------------------
    # Array data

    @property
    def flags(self) -> flagsobj:
        """Flags of the raster."""
        return self._ndarray.flags

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the raster."""
        return self._ndarray.shape

    @property
    def strides(self) -> tuple[int, ...]:
        """Strides of the raster."""
        return self._ndarray.strides

    @property
    def ndim(self) -> int:
        """Number of dimensions of the raster."""
        return 2

    @property
    def data(self) -> memoryview:
        """Python buffer object pooint to the start of the raster's data."""
        return self._ndarray.data

    @property
    def size(self) -> int:
        """Number of elements in the raster."""
        return self._ndarray.size

    @property
    def itemsize(self) -> int:
        """Size of each element in the raster."""
        return self._ndarray.itemsize

    @property
    def nbytes(self) -> int:
        """Number of bytes in the raster."""
        return self._ndarray.nbytes

    @property
    def base(self) -> np.ndarray | None:
        """Base object of the raster."""
        return self._ndarray.base

    @property
    def dtype(self) -> np.dtype:
        """Data type of the raster."""
        return self._ndarray.dtype

    @property
    def T(self) -> typing.NoReturn:  # noqa: N802
        """Transpose of the raster."""
        raise TypeError("Transpose of a raster is not defined.")

    @property
    def real(self) -> "RasterArray":
        """Real part of the raster."""
        return RasterArray(
            self._ndarray.real, self._transform, self._crs, self._no_data_value
        )

    @property
    def imag(self) -> "RasterArray":
        """Imaginary part of the raster."""
        return RasterArray(
            self._ndarray.imag, self._transform, self._crs, self._no_data_value
        )

    @property
    def flat(self) -> np.flatiter:
        """Flat iterator of the raster."""
        return self._ndarray.flat

    @property
    def ctypes(self) -> typing.NoReturn:
        """ctypes object of the raster."""
        raise TypeError("ctypes object of a raster is not defined.")

    # ----------------------------------------------------------------
    # NumPy array interface

    def astype(self, dtype: NumpyDtype) -> "RasterArray":
        """Cast the raster to a new data type."""
        return RasterArray(
            self._ndarray.astype(dtype), self._transform, self._crs, self._no_data_value
        )

    def to_numpy(self) -> np.ndarray:
        """Convert the raster to a NumPy array."""
        return self._ndarray.copy()

    def __array__(self, dtype: NumpyDtype | None = None) -> np.ndarray:
        return np.asarray(self._ndarray, dtype=dtype)

    def __array_ufunc__(
        self,
        ufunc: np.ufunc,
        method: NumpyUFuncMethod,
        *inputs: np.ndarray | Number | "RasterArray",
        **kwargs: typing.Any,
    ) -> typing.Union[tuple["RasterArray", ...], "RasterArray"]:
        out = kwargs.get("out", ())
        for x in inputs + out:
            # Only support operations with instances of _HANDLED_TYPES.
            # Use RasterArray instead of type(self) for isinstance to
            # allow subclasses that don't override __array_ufunc__ to
            # handle RasterArray objects.
            handled_types = (np.ndarray, numbers.Number, RasterArray)
            if not isinstance(x, handled_types):
                return NotImplemented
            if isinstance(x, RasterArray):
                if x._crs != self._crs:
                    raise ValueError("Coordinate reference systems do not match.")
                if not self._no_data_equal(x._no_data_value):
                    raise ValueError("No data values do not match.")
                if x._transform != self._transform:
                    raise ValueError("Affine transforms do not match.")

        # Defer to the implementation of the ufunc on unwrapped values.
        inputs = tuple(x._ndarray if isinstance(x, RasterArray) else x for x in inputs)
        if out:
            kwargs["out"] = tuple(
                x._ndarray if isinstance(x, RasterArray) else x for x in out
            )
        result = getattr(ufunc, method)(*inputs, **kwargs)

        if type(result) is tuple:
            # multiple return values
            return tuple(
                type(self)(x, self._transform, self._crs, self._no_data_value)
                for x in result
            )
        else:
            # one return value
            return type(self)(result, self._transform, self._crs, self._no_data_value)

    # ----------------------------------------------------------------
    # Specialized array methods

    def all(self) -> bool:
        """Return True if all elements evaluate to True."""
        return self._ndarray.all()  # type: ignore[return-value]

    def any(self) -> bool:
        """Return True if any element evaluates to True."""
        return self._ndarray.any()  # type: ignore[return-value]

    # ----------------------------------------------------------------
    # Raster data

    @property
    def transform(self) -> Affine:
        """Affine transform to georeference the raster."""
        return self._transform

    @property
    def x_min(self) -> float:
        """Minimum x coordinate."""
        return self.transform.c

    @property
    def x_max(self) -> float:
        """Maximum x coordinate."""
        return self.x_min + self.x_resolution * self.width

    @property
    def y_min(self) -> float:
        """Minimum y coordinate."""
        return self.y_max + self.y_resolution * self.height

    @property
    def y_max(self) -> float:
        """Maximum y coordinate."""
        return self.transform.f

    @property
    def width(self) -> int:
        """Width of the raster."""
        return self._ndarray.shape[1]

    @property
    def height(self) -> int:
        """Height of the raster."""
        return self._ndarray.shape[0]

    @property
    def x_resolution(self) -> float:
        """Resolution in x direction."""
        return self.transform.a

    @property
    def y_resolution(self) -> float:
        """Resolution in y direction."""
        return self.transform.e

    def x_coordinates(self, center: bool = False) -> np.ndarray:
        """x coordinates of the raster."""
        if center:
            return np.linspace(
                self.x_min + self.x_resolution / 2,
                self.x_max - self.x_resolution / 2,
                self.width,
            )
        else:
            return np.linspace(self.x_min, self.x_max, self.width)

    def y_coordinates(self, center: bool = False) -> np.ndarray:
        """y coordinates of the raster."""
        if center:
            return np.linspace(
                self.y_min + self.y_resolution / 2,
                self.y_max - self.y_resolution / 2,
                self.height,
            )
        else:
            return np.linspace(self.y_min, self.y_max, self.height)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Bounding box of the raster."""
        return self.x_min, self.x_max, self.y_min, self.y_max

    @property
    def crs(self) -> str | None:
        """Coordinate reference system."""
        if isinstance(self._crs, CRS):
            return self._crs.to_string()
        else:
            return self._crs

    def set_crs(self, new_crs: RawCRS) -> "RasterArray":
        if self._crs is not None:
            raise ValueError(
                "Coordinate reference system is already set. Use to_crs() to reproject "
                "to a new coordinate reference system."
            )
        return RasterArray(
            self._ndarray.copy(), self._transform, new_crs, self._no_data_value
        )

    def to_crs(self, new_crs: str, resampling: str = "nearest") -> "RasterArray":
        """Reproject the raster to a new coordinate reference system."""
        if self._crs is None:
            raise ValueError("Coordinate reference system is not set.")
        resampling = _RESAMPLING_MAP[resampling]
        new_crs = CRS.from_user_input(new_crs)

        new_data, transform = reproject(
            source=self._ndarray,
            src_transform=self._transform,
            src_crs=self._crs,
            src_no_data_value=self._no_data_value,
            dst_crs=new_crs,
            resampling=resampling,
        )
        return RasterArray(
            new_data[0], transform, new_crs, no_data_value=self._no_data_value
        )

    @property
    def no_data_value(self) -> Number:
        """Value representing no data."""
        if self._no_data_value is NO_DATA_UNSET:
            raise ValueError("No data value is not set.")
        return self._no_data_value

    def set_no_data_value(self, new_no_data_value: Number) -> "RasterArray":
        new_data = self._ndarray.copy()
        if self._no_data_value is not NO_DATA_UNSET:
            new_data[self.no_data_mask] = new_no_data_value
        return RasterArray(new_data, self._transform, self._crs, new_no_data_value)

    def _no_data_equal(self, other_no_data_value: Number | None) -> bool:
        if self._no_data_value is NO_DATA_UNSET:
            return other_no_data_value is NO_DATA_UNSET
        elif other_no_data_value is NO_DATA_UNSET:
            return False
        elif np.isnan(self._no_data_value):
            return np.isnan(other_no_data_value)
        elif np.isinf(self._no_data_value):
            return np.isinf(other_no_data_value) and np.sign(
                self._no_data_value
            ) == np.sign(other_no_data_value)
        else:
            return self._no_data_value == other_no_data_value

    def unset_no_data_value(self) -> "RasterArray":
        """Unset value representing no data."""
        return RasterArray(
            self._ndarray.copy(), self._transform, self._crs, NO_DATA_UNSET
        )

    @property
    def no_data_mask(self) -> np.ndarray:
        """Mask representing no data."""
        if self._no_data_value is NO_DATA_UNSET:
            return np.zeros_like(self._ndarray, dtype=bool)
        elif np.isnan(self._no_data_value):
            return np.isnan(self._ndarray)
        elif np.isinf(self._no_data_value):
            return np.isinf(self._ndarray)
        else:
            return np.equal(self._ndarray, self._no_data_value)

    def resample(self, scale: float, resampling: str = "nearest") -> "RasterArray":
        """Resample the raster."""
        resampling = _RESAMPLING_MAP[resampling]

        dest_width = int(self.width * scale)
        dest_height = int(self.height * scale)
        destination = np.empty((dest_height, dest_width), dtype=self._ndarray.dtype)

        new_data, transform = reproject(
            source=self._ndarray,
            src_transform=self._transform,
            src_crs=self._crs,
            src_no_data_value=self._no_data_value,
            destination=destination,
            dst_crs=self._crs,
            resampling=resampling,
        )

        return RasterArray(
            new_data, transform, self._crs, no_data_value=self.no_data_value
        )

    def resample_to(
        self, target: "RasterArray", resampling: str = "nearest"
    ) -> "RasterArray":
        """Resample the raster to match the resolution of another raster."""
        resampling = _RESAMPLING_MAP[resampling]

        destination = np.empty_like(target._ndarray, dtype=self._ndarray.dtype)
        new_data, transform = reproject(
            source=self._ndarray,
            src_transform=self._transform,
            src_crs=self._crs,
            src_no_data_value=self._no_data_value,
            destination=destination,
            dst_transform=target.transform,
            dst_crs=target._crs,
            resampling=resampling,
        )
        return RasterArray(
            new_data, transform, target._crs, no_data_value=self.no_data_value
        )

    def _coerce_to_shapely(
        self, shape: Polygon | MultiPolygon | gpd.GeoDataFrame | gpd.GeoSeries
    ) -> Polygon | MultiPolygon:
        if isinstance(shape, (gpd.GeoDataFrame, gpd.GeoSeries)):
            if not shape.crs == self._crs:
                raise ValueError("Coordinate reference systems do not match.")
            return shape.geometry.unary_union
        return shape

    def clip(
        self, shape: Polygon | MultiPolygon | gpd.GeoDataFrame | gpd.GeoSeries
    ) -> "RasterArray":
        """Clip the raster to a shape."""
        shape = self._coerce_to_shapely(shape)
        _, transform, window = raster_geometry_mask(
            data_transform=self.transform,
            data_width=self._ndarray.shape[1],
            data_height=self._ndarray.shape[0],
            shapes=[shape],
            crop=True,
        )

        x_start, x_end = window.col_off, window.col_off + window.width
        y_start, y_end = window.row_off, window.row_off + window.height
        new_data = self._ndarray[y_start:y_end, x_start:x_end].copy()
        return RasterArray(
            new_data, transform, self._crs, no_data_value=self.no_data_value
        )

    def mask(
        self,
        shape: Polygon | MultiPolygon | gpd.GeoDataFrame | gpd.GeoSeries,
        fill_value: Number | None = None,
        all_touched: bool = False,
        invert: bool = False,
    ) -> "RasterArray":
        """Mask the raster with a shape."""
        shape = self._coerce_to_shapely(shape)
        if fill_value is None and self._no_data_value is NO_DATA_UNSET:
            raise ValueError("No fill value is set.")
        elif fill_value is None:
            fill_value = self.no_data_value

        shape_mask, *_ = raster_geometry_mask(
            data_transform=self.transform,
            data_width=self._ndarray.shape[1],
            data_height=self._ndarray.shape[0],
            shapes=[shape],
            all_touched=all_touched,
            invert=invert,
        )
        new_data = self._ndarray.copy()
        new_data[shape_mask] = fill_value

        return RasterArray(
            new_data, self.transform, self._crs, no_data_value=self.no_data_value
        )

    def __repr__(self) -> str:
        out = "RasterArray\n"
        out += "===========\n"
        out += f"dimensions    : {self.width}, {self.height} (x, y)\n"
        out += f"resolution    : {self.transform.a}, {self.transform.e} (x, y)\n"
        bounds = ", ".join(
            str(s) for s in [self.x_min, self.x_max, self.y_min, self.y_max]
        )
        out += f"extent        : {bounds} (xmin, xmax, ymin, ymax)\n"
        out += f"crs           : {self.crs}\n"
        out += f"no_data_value : {self._no_data_value}\n"
        out += f"size          : {self.nbytes / 1024 ** 2:.2f} MB\n"
        out += f"dtype         : {self._ndarray.dtype}\n"
        return out

    def to_file(self, path: FilePath) -> None:
        """Write the raster to a file."""
        from rasterra._io import write_raster

        write_raster(self, path)

    @property
    def plot(self) -> Plotter:
        return Plotter(self._ndarray, self.no_data_mask, self.transform)
