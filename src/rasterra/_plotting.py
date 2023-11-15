from typing import Any, Union

import affine
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Colormap
from rasterio.plot import plotting_extent, show_hist


class Plotter:
    def __init__(self, data: np.ndarray, transform: affine.Affine) -> None:
        self._data = data
        self._transform = transform

    def __call__(
        self,
        ax: Union[Axes, None] = None,
        cmap: str | Colormap = "viridis",
        vmin: Union[float, None] = None,
        vmax: Union[float, None] = None,
        nbins: int = 20,
        **kwargs: Any,
    ) -> Axes:
        # Contrast stretching by default
        if vmin is None:
            vmin = np.nanpercentile(self._data, 2)
        if vmax is None:
            vmax = np.nanpercentile(self._data, 98)

        kwargs["extent"] = plotting_extent(self._data, self._transform)

        show_plt = False
        if not ax:
            show_plt = True
            ax = plt.gca()

        ax.imshow(self._data, vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)
        if show_plt:
            plt.show()

        return ax

    def hist(self, *_: Any, **kwargs: Any) -> Axes:
        return show_hist(
            source=self._data,
            **kwargs,
        )
