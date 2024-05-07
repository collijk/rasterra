# rasterra

[![PyPI](https://img.shields.io/pypi/v/rasterra?style=flat-square)](https://pypi.python.org/pypi/rasterra/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rasterra?style=flat-square)](https://pypi.python.org/pypi/rasterra/)
[![PyPI - License](https://img.shields.io/pypi/l/rasterra?style=flat-square)](https://pypi.python.org/pypi/rasterra/)

---

**Documentation**: [https://collijk.github.io/rasterra](https://collijk.github.io/rasterra)

**Source Code**: [https://github.com/collijk/rasterra](https://github.com/collijk/rasterra)

**PyPI**: [https://pypi.org/project/rasterra/](https://pypi.org/project/rasterra/)

---

An in-memory object-oriented raster manipulation library.

`rasterra` is a library for manipulating raster data in memory. It is designed to be
used in lieu of [`rasterio`](https://rasterio.readthedocs.io/en/latest/) to allow for
easier manipulation of raster data. It is designed to be used in conjunction with
[`geopandas`](https://geopandas.org/) when vector data is also being used.

Currently, `rasterra` is in a very early stage of development. It's primary limitation
at this point is that it only supports single-band raster data. Multi-band support is
planned for the near future.

## Installation

```sh
pip install rasterra
```

## Usage

### File I/O

Reading and writing raster data is done using the `load_raster` and `to_file` functions.

```python
import rasterra as rt

# Read in a raster
raster = rt.load_raster("path/to/raster.tif")

# Write a raster to disk
raster.to_file("path/to/output.tif")

```

A raster can also be read and mosaic'd from multiple files using the `load_mf_raster`
function.

```python
import rasterra as rt

# Read in a multi-file raster
raster = rt.load_mf_raster(["path/to/raster1.tif", "path/to/raster2.tif"])

```

### Raster Manipulation

`rasterra` provides a number of methods for manipulating raster data. These methods
are designed to be used in a method-chaining style, similar to `pandas` and `geopandas`.

```python
import rasterra as rt
import geopandas as gpd

# Read in a raster
raster = rt.load_raster("path/to/raster.tif")
shapes = gpd.read_file("path/to/polygons.shp")


new_raster = (
    raster
    .to_crs(shapes.crs)          # Reproject the raster to the same CRS as the polygons
    .clip(shapes)                # Clip the raster to the bounding box of the polygons
    .mask(shapes, fill_value=0)  # Mask the raster to the polygons, filling in areas outside the polygons with 0
    .resample(0.5, 'sum')        # Downsample the raster half the original resolution,
                                 # computing the area-weighted sum of the contributing pixels
)

```
