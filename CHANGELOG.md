# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.2] - 2025-02-26
### Added
- Additions to upgrade to poetry v2

### Fixed
- Relax python requirment to >=3.12

## [0.6.1] - 2024-12-25
### Added
- Support for a no-data color in plotting.

## [0.6.0] - 2024-08-28
### Added
- Added a `resolution` property to RasterArray that returns a tuple of
    (x_resolution, y_resolution).
- Added a general purpose `reproject` method that can change the crs and resolution
    simultaneously.
- Updated `resample`, `resample_to` and `to_crs` to use internal `reproject` method.
- Added a top level merge function to merge rasters in memory.

## [0.5.14] - 2024-06-25
### Fixed
- Removed support for float128, which doesn't work on apple silicon.

## [0.5.13] - 2024-06-24
### Added
- Upgrade numpy to 2.0

## [0.5.12] - 2024-06-24
### Added
- Upgrade geopandas to 1.0

## [0.5.11] - 2024-05-16
### Added
- Allow windowed reads of raster data.
- Add a selection method for extracting values from a raster array by coordinates.

## [0.5.10] - 2024-05-15
### Added
- Accumulate and propagate the no-data mask through operations on RasterArray objects.

## [0.5.9] - 2024-05-10
### Added
- Add **kwargs to raster.to_file, allowing users to specify different drivers, compression,
    tiling, and other options for writing raster files.

## [0.5.8] - 2024-05-10
### Added
- Basic import test

### Fixed
- Typing of flatiter in RasterArray

## [0.5.7] - 2024-05-08
### Fixed
- More patches to the typing system.

## [0.5.6] - 2024-05-07
### Fixed
- Cover all float and int dtypes for RasterArray data.

## [0.5.5] - 2024-05-07
### Added
- Updated dev tools to use ruff instead of black/isort/flake8 and friends
- Fixed a ton of typing and formatting picked up with the new tooling
- Explicitly export the RasterArray class and i/o methods in the `__init__.py` file

## [0.5.4] - 2024-05-07
### Fixed
- Fixed a bug with nodata call into rasterio.warp.resample
- Fixed implementation of x_coordinates and y_coordinates
- Fixed documentation build process

### Added
- Added a __getitem__ method to the RasterArray class
- Added a to_gdf method and backing function to convert raster data to vector data.
- Contributing guide and a better readme

## [0.5.2] - 2023-12-27
### Fixed
- Doc build process

## [0.5.1] - 2023-12-27
### Added
- Fix documentation rendering.

## [0.5.0] - 2023-12-27
### Added
- Read rasters from one or many files
- Basic object-oriented raster object
- Sensible repr and basic plotting functions
- Numpy array interface
- Fixed up the CI for package maintenance, CI, and releases.

[Unreleased]: https://github.com/collijk/rasterra/compare/0.6.2...master
[0.6.2]: https://github.com/collijk/rasterra/compare/0.6.1...0.6.2
[0.6.1]: https://github.com/collijk/rasterra/compare/0.6.0...0.6.1
[0.6.0]: https://github.com/collijk/rasterra/compare/0.5.14...0.6.0
[0.5.14]: https://github.com/collijk/rasterra/compare/0.5.13...0.5.14
[0.5.13]: https://github.com/collijk/rasterra/compare/0.5.12...0.5.13
[0.5.12]: https://github.com/collijk/rasterra/compare/0.5.11...0.5.12
[0.5.11]: https://github.com/collijk/rasterra/compare/0.5.10...0.5.11
[0.5.10]: https://github.com/collijk/rasterra/compare/0.5.9...0.5.10
[0.5.9]: https://github.com/collijk/rasterra/compare/0.5.8...0.5.9
[0.5.8]: https://github.com/collijk/rasterra/compare/0.5.7...0.5.8
[0.5.7]: https://github.com/collijk/rasterra/compare/0.5.6...0.5.7
[0.5.6]: https://github.com/collijk/rasterra/compare/0.5.5...0.5.6
[0.5.5]: https://github.com/collijk/rasterra/compare/0.5.4...0.5.5
[0.5.4]: https://github.com/collijk/rasterra/compare/0.5.2...0.5.4
[0.5.2]: https://github.com/collijk/rasterra/compare/0.5.1...0.5.2
[0.5.1]: https://github.com/collijk/rasterra/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/collijk/rasterra/tree/0.5.0
