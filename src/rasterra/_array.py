import numbers
import typing

import geopandas as gpd
import numpy as np
import numpy.typing as npt
from affine import Affine
from numpy.core.multiarray import flagsobj
from rasterio.crs import CRS
from rasterio.warp import Resampling, reproject
from shapely.geometry import MultiPolygon, Polygon

from rasterra._features import raster_geometry_mask, to_gdf
from rasterra._plotting import Plotter
from rasterra._typing import (
    DataDtypes,
    FilePath,
    NumpyUFuncMethod,
    RasterData,
    RasterMask,
    RawCRS,
    SupportedDtypes,
)

_RESAMPLING_MAP = {data.name: data for data in Resampling}

NO_DATA_UNSET = None

_IDENTITY_TRANSFORM: Affine = Affine.identity()


class RasterArray(np.lib.mixins.NDArrayOperatorsMixin):
    def __init__(
        self,
        data: RasterData,
        transform: Affine = _IDENTITY_TRANSFORM,
        crs: RawCRS | None = None,
        no_data_value: SupportedDtypes | None = NO_DATA_UNSET,
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
        return self._ndarray.shape  # type: ignore[no-any-return]

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
    def base(self) -> RasterData | None:
        """Base object of the raster."""
        return self._ndarray.base

    @property
    def dtype(self) -> np.dtype[DataDtypes]:
        """Data type of the raster."""
        return self._ndarray.dtype

    @property
    def T(self) -> typing.NoReturn:  # noqa: N802
        """Transpose of the raster."""
        msg = "Transpose of a raster is not defined."
        raise TypeError(msg)

    @property
    def real(self) -> typing.NoReturn:
        """Real part of the raster."""
        msg = "Complex raster data is not supported."
        raise NotImplementedError(msg)

    @property
    def imag(self) -> typing.NoReturn:
        """Imaginary part of the raster."""
        msg = "Complex raster data is not supported."
        raise NotImplementedError(msg)

    @property
    def flat(self) -> np.flatiter:  # type: ignore[type-arg]
        """Flat iterator of the raster."""
        return self._ndarray.flat

    @property
    def ctypes(self) -> typing.NoReturn:
        """ctypes object of the raster."""
        msg = "ctypes object of a raster is not defined."
        raise TypeError(msg)

    def __getitem__(self, item: int | slice | tuple[int, int] | tuple[slice, slice]):  # type: ignore[no-untyped-def]
        def _process_item(_item: int | slice) -> int | slice:
            if isinstance(_item, int):
                return _item
            elif isinstance(_item, slice):
                if _item.step is not None:
                    msg = "Slicing with a step is not supported."
                    raise ValueError(msg)
                return _item.start or 0
            else:
                msg = "Invalid index type"
                raise TypeError(msg)

        new_data = self._ndarray[item]
        if not isinstance(new_data, np.ndarray):
            return new_data

        if isinstance(item, tuple):
            if len(item) != 2:  # noqa: PLR2004
                msg = "Invalid number of indices"
                raise ValueError(msg)
            y_item, x_item = item

            yi = _process_item(y_item)
            xi = _process_item(x_item)
        else:
            yi = _process_item(item)
            xi = 0

        new_transform = Affine(
            self._transform.a,
            self._transform.b,
            self._transform.c + xi * self._transform.a,
            self._transform.d,
            self._transform.e,
            self._transform.f + yi * self._transform.e,
        )

        return RasterArray(new_data, new_transform, self._crs, self._no_data_value)

    # ----------------------------------------------------------------
    # NumPy array interface

    def astype(self, dtype: type[DataDtypes]) -> "RasterArray":
        """Cast the raster to a new data type."""
        return RasterArray(
            self._ndarray.astype(dtype), self._transform, self._crs, self._no_data_value
        )

    def to_numpy(self) -> RasterData:
        """Convert the raster to a NumPy array."""
        return self._ndarray.copy()

    def __array__(self, dtype: type[DataDtypes] | None = None) -> RasterData:
        return np.asarray(self._ndarray, dtype=dtype)

    def __array_ufunc__(  # noqa: C901
        self,
        ufunc: np.ufunc,
        method: NumpyUFuncMethod,
        *inputs: typing.Union[RasterData, SupportedDtypes, "RasterArray"],
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
                if x._crs != self._crs:  # noqa: SLF001
                    msg = "Coordinate reference systems do not match."
                    raise ValueError(msg)
                if not self._no_data_equal(x._no_data_value):  # noqa: SLF001
                    msg = "No data values do not match."
                    raise ValueError(msg)
                if x._transform != self._transform:  # noqa: SLF001
                    msg = "Affine transforms do not match."
                    raise ValueError(msg)

        # Propagate the no_data_value to the output array.
        no_data_mask = self.no_data_mask
        for x in inputs:
            if isinstance(x, RasterArray):
                no_data_mask |= x.no_data_mask

        # Defer to the implementation of the ufunc on unwrapped values.
        inputs = tuple(x._ndarray if isinstance(x, RasterArray) else x for x in inputs)  # noqa: SLF001
        if out:
            kwargs["out"] = tuple(
                x._ndarray if isinstance(x, RasterArray) else x  # noqa: SLF001
                for x in out
            )
        result = getattr(ufunc, method)(*inputs, **kwargs)
        result[no_data_mask] = self._no_data_value

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
        return self.transform.c  # type: ignore[no-any-return]

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
        return self.transform.f  # type: ignore[no-any-return]

    @property
    def width(self) -> int:
        """Width of the raster."""
        return self._ndarray.shape[1]  # type: ignore[no-any-return]

    @property
    def height(self) -> int:
        """Height of the raster."""
        return self._ndarray.shape[0]  # type: ignore[no-any-return]

    @property
    def x_resolution(self) -> float:
        """Resolution in x direction."""
        return self.transform.a  # type: ignore[no-any-return]

    @property
    def y_resolution(self) -> float:
        """Resolution in y direction."""
        return self.transform.e  # type: ignore[no-any-return]

    @property
    def resolution(self) -> tuple[float, float]:
        """Resolution in x and y directions."""
        return self.x_resolution, self.y_resolution

    def x_coordinates(self, *, center: bool = False) -> npt.NDArray[np.float64]:
        """x coordinates of the raster."""
        if center:
            return np.linspace(
                self.x_min + self.x_resolution / 2,
                self.x_max - self.x_resolution / 2,
                self.width,
            )
        else:
            return np.linspace(
                self.x_min,
                self.x_max - self.x_resolution,
                self.width,
            )

    def y_coordinates(self, *, center: bool = False) -> npt.NDArray[np.float64]:
        """y coordinates of the raster."""
        if center:
            return np.linspace(
                self.y_min - self.y_resolution / 2,
                self.y_max + self.y_resolution / 2,
                self.height,
            )
        else:
            return np.linspace(
                self.y_min - self.y_resolution,
                self.y_max,
                self.height,
            )

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """Bounding box of the raster."""
        return self.x_min, self.x_max, self.y_min, self.y_max

    @property
    def crs(self) -> str | None:
        """Coordinate reference system."""
        if isinstance(self._crs, CRS):
            return self._crs.to_string()  # type: ignore[no-any-return]
        else:
            return self._crs

    def set_crs(self, new_crs: RawCRS) -> "RasterArray":
        if self._crs is not None:
            msg = (
                "Coordinate reference system is already set. Use to_crs() to reproject "
                "to a new coordinate reference system."
            )
            raise ValueError(msg)
        return RasterArray(
            self._ndarray.copy(), self._transform, new_crs, self._no_data_value
        )

    def to_crs(self, new_crs: str, resampling: str = "nearest") -> "RasterArray":
        """Reproject the raster to a new coordinate reference system."""
        if self._crs is None:
            msg = "Coordinate reference system is not set."
            raise ValueError(msg)
        return self.reproject(
            dst_crs=new_crs,
            resampling=resampling,
        )

    @property
    def no_data_value(self) -> SupportedDtypes:
        """Value representing no data."""
        if self._no_data_value is NO_DATA_UNSET:
            msg = "No data value is not set."
            raise ValueError(msg)
        return self._no_data_value

    def set_no_data_value(self, new_no_data_value: SupportedDtypes) -> "RasterArray":
        new_data = self._ndarray.copy()
        if self._no_data_value is not NO_DATA_UNSET:
            new_data[self.no_data_mask] = new_no_data_value
        return RasterArray(new_data, self._transform, self._crs, new_no_data_value)

    def _no_data_equal(self, other_no_data_value: SupportedDtypes | None) -> bool:
        if self._no_data_value is NO_DATA_UNSET:
            return other_no_data_value is NO_DATA_UNSET
        elif other_no_data_value is NO_DATA_UNSET:
            return False
        elif np.isnan(self._no_data_value):
            return np.isnan(other_no_data_value)  # type: ignore[no-any-return]
        elif np.isinf(self._no_data_value):
            other_inf = np.isinf(other_no_data_value)
            sign_match = np.sign(self._no_data_value) == np.sign(other_no_data_value)
            return other_inf and sign_match  # type: ignore[no-any-return]
        else:
            return self._no_data_value == other_no_data_value

    def unset_no_data_value(self) -> "RasterArray":
        """Unset value representing no data."""
        return RasterArray(
            self._ndarray.copy(), self._transform, self._crs, NO_DATA_UNSET
        )

    @property
    def no_data_mask(self) -> RasterMask:
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
        dest_width = int(self.width * scale)
        dest_height = int(self.height * scale)
        destination = np.empty((dest_height, dest_width), dtype=self._ndarray.dtype)
        return self.reproject(
            destination=destination,
            dst_crs=self._crs,
            resampling=resampling,
        )

    def resample_to(
        self, target: "RasterArray", resampling: str = "nearest"
    ) -> "RasterArray":
        """Resample the raster to match the resolution of another raster."""
        destination = np.empty_like(target._ndarray, dtype=self._ndarray.dtype)  # noqa: SLF001
        return self.reproject(
            destination=destination,
            dst_transform=target.transform,
            dst_crs=target._crs,  # noqa: SLF001
            resampling=resampling,
        )

    def reproject(
        self,
        destination: RasterData | None = None,
        dst_transform: Affine | None = None,
        dst_resolution: float | tuple[float, float] | None = None,
        dst_crs: RawCRS | None = None,
        resampling: str = "nearest",
    ) -> "RasterArray":
        """Reproject the raster to match the resolution of another raster."""
        resampling = _RESAMPLING_MAP[resampling]

        dst_crs = self._crs if dst_crs is None else CRS.from_user_input(dst_crs)
        new_data, transform = reproject(
            source=self._ndarray,
            src_transform=self._transform,
            src_crs=self._crs,
            src_nodata=self._no_data_value,
            destination=destination,
            dst_transform=dst_transform,
            dst_resolution=dst_resolution,
            dst_crs=dst_crs,
            resampling=resampling,
        )
        if len(new_data.shape) == 3:  # noqa: PLR2004
            # Some operations assume and prepend a channel dimension
            new_data = new_data[0]
        return RasterArray(
            new_data,
            transform,
            dst_crs,
            self.no_data_value,
        )

    def _coerce_to_shapely(
        self, shape: Polygon | MultiPolygon | gpd.GeoDataFrame | gpd.GeoSeries
    ) -> Polygon | MultiPolygon:
        if isinstance(shape, (gpd.GeoDataFrame, gpd.GeoSeries)):
            if shape.crs != self._crs:
                msg = "Coordinate reference systems do not match."
                raise ValueError(msg)
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
        *,
        fill_value: SupportedDtypes | None = None,
        all_touched: bool = False,
        invert: bool = False,
    ) -> "RasterArray":
        """Mask the raster with a shape."""
        shape = self._coerce_to_shapely(shape)
        if fill_value is None and self._no_data_value is NO_DATA_UNSET:
            msg = "No fill value is set."
            raise ValueError(msg)

        if fill_value is None:
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

    def select(
        self,
        x_coordinates: npt.NDArray[np.float64],
        y_coordinates: npt.NDArray[np.float64],
        method: str = "nearest",
    ) -> npt.NDArray[DataDtypes]:
        """Select values at specific coordinates."""
        if x_coordinates.size != y_coordinates.size:
            msg = "x and y coordinates must have the same size."
            raise ValueError(msg)

        if method == "nearest":
            x_indices = np.clip(
                np.searchsorted(self.x_coordinates(), x_coordinates),
                0,
                self.width - 1,
            )
            y_indices = np.searchsorted(
                self.y_coordinates(), y_coordinates, side="right"
            )
            # Flip y indices to match raster coordinatesok
            y_indices = np.clip(
                self.height - y_indices,
                0,
                self.height - 1,
            )

            return self._ndarray[y_indices, x_indices].copy()
        else:
            msg = "Only 'nearest' method is supported."
            raise NotImplementedError(msg)

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

    def to_file(self, path: FilePath, **kwargs: typing.Any) -> None:
        """Write the raster to a file."""
        from rasterra._io import write_raster

        write_raster(self, path, **kwargs)

    def to_gdf(self) -> gpd.GeoDataFrame:
        return to_gdf(self)

    @property
    def plot(self) -> Plotter:
        return Plotter(self._ndarray, self.no_data_mask, self.transform)
