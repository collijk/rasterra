# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/collijk/rasterra/compare/0.5.7...master
[0.5.7]: https://github.com/collijk/rasterra/compare/0.5.6...0.5.7
[0.5.6]: https://github.com/collijk/rasterra/compare/0.5.5...0.5.6
[0.5.5]: https://github.com/collijk/rasterra/compare/0.5.4...0.5.5
[0.5.4]: https://github.com/collijk/rasterra/compare/0.5.2...0.5.4
[0.5.2]: https://github.com/collijk/rasterra/compare/0.5.1...0.5.2
[0.5.1]: https://github.com/collijk/rasterra/compare/0.5.0...0.5.1
[0.5.0]: https://github.com/collijk/rasterra/tree/0.5.0
