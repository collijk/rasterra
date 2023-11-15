from typing import Any

import affine
import numpy as np
from matplotlib.axes import Axes
from rasterio.plot import show, show_hist


class Plotter:
    def __init__(self, data: np.ndarray, transform: affine.Affine) -> None:
        self._data = data
        self._transform = transform

    def __call__(self, *_: Any, **kwargs: Any) -> Axes:
        return show(
            source=self._data,
            with_bounds=True,
            transform=self._transform,
            **kwargs,
        )

    def hist(self, *_: Any, **kwargs: Any) -> Axes:
        return show_hist(
            source=self._data,
            **kwargs,
        )
