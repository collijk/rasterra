from typing import Any, Union

import affine
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Colormap, Normalize
from rasterio.plot import plotting_extent, show_hist
from mpl_toolkits.axes_grid1 import make_axes_locatable


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
        under_color: str | None = None,
        norm: Normalize | None = None,
        **kwargs: Any,
    ) -> Axes:
        if (vmin is not None or vmax is not None) and norm is not None:
            raise ValueError("Cannot pass both vmin/vmax and norm.")
        if norm is None:
            norm = Normalize(vmin=vmin, vmax=vmax)

        kwargs["extent"] = plotting_extent(self._data, self._transform)

        show_plt = False
        if not ax:
            show_plt = True
            ax = plt.gca()

        im = ax.imshow(self._data, norm=norm, cmap=cmap, **kwargs)
        if under_color is not None:
            im.cmap.set_under(under_color)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)
        ax.figure.colorbar(ax.images[0], cax=cax, orientation='vertical')

        if show_plt:
            plt.show()

        return ax

    def test_normalization(
        self,
        norm: Normalize,
        nbins: int = 50,
        cmap: str | Colormap = "viridis",
        under_color: str | None = None,
    ) -> None:
        """Test a normalization of the data for plotting."""
        vmin = norm.vmin
        vmax = norm.vmax
        mask = (vmin <= self._data) & (self._data <= vmax)
        data = self._data[mask].flatten()

        result = norm(data)

        fig, axes = plt.subplots(figsize=(15, 15), ncols=2, nrows=2)

        _make_hist_plot(data, nbins, 'Raw data', axes[0, 0])
        _make_image_plot(data, Normalize(vmin=vmin, vmax=vmax), cmap, under_color, axes[1, 0])

        _make_hist_plot(result, nbins, 'Normalized data', axes[0, 1])
        _make_image_plot(result, norm, cmap, under_color, axes[1, 1])

        plt.show()


def _make_hist_plot(
    data: np.ndarray,
    nbins: int,
    title: str,
    ax: Axes,
) -> Axes:
    """Plot a histogram of the data."""
    hist, bins = np.histogram(data, nbins)
    cdf = hist.cumsum()
    cdf = cdf / cdf.max()
    ax.bar(bins[:-1], hist, width=bins[1:] - bins[:-1], color='tab:blue')
    ax.set_ylabel('Frequency', color='tab:blue', fontsize=14)
    ax.set_title(title, fontsize=16)
    ax2 = ax.twinx()
    ax2.plot(bins[:-1], cdf, color='tab:orange')
    ax2.set_ylabel('Cumulative frequency', color='tab:orange', fontsize=14)
    return ax


def _make_image_plot(
    data: np.ndarray,
    norm: Normalize,
    cmap: str | Colormap,
    under_color: str | None,
    ax: Axes,
    **kwargs: Any,
) -> Axes:
    """Plot a histogram of the data."""
    im = ax.imshow(data, cmap=cmap, norm=norm, **kwargs)
    if under_color is not None:
        im.cmap.set_under(under_color)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    ax.figure.colorbar(ax.images[0], cax=cax, orientation='vertical')

    return ax
