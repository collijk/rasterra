from typing import Any

import affine
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import Colormap, Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable
from rasterio.plot import plotting_extent

from rasterra._typing import RasterData, RasterMask


class Plotter:
    def __init__(
        self,
        data: RasterData,
        data_mask: RasterMask,
        transform: affine.Affine,
    ) -> None:
        self._data = data
        self._mask = data_mask
        self._transform = transform

    def __call__(
        self,
        ax: Axes | None = None,
        cmap: str | Colormap = "viridis",
        vmin: float | None = None,
        vmax: float | None = None,
        under_color: str | None = None,
        norm: Normalize | None = None,
        **kwargs: Any,
    ) -> Axes:
        if (vmin is not None or vmax is not None) and norm is not None:
            msg = "Cannot pass both vmin/vmax and norm."
            raise ValueError(msg)
        if norm is None:
            norm = Normalize(vmin=vmin, vmax=vmax)

        kwargs["extent"] = plotting_extent(self._data, self._transform)

        show_plt = False
        if not ax:
            show_plt = True
            ax = plt.gca()

        _make_image_plot(self._data, self._mask, norm, cmap, under_color, ax, **kwargs)

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
        vmin = norm.vmin if norm.vmin is not None else self._data.min()
        vmax = norm.vmax if norm.vmax is not None else self._data.max()
        mask = (vmin <= self._data) & (self._data <= vmax) & ~self._mask
        data = self._data[mask].flatten()

        result = norm(data)

        fig, axes = plt.subplots(figsize=(15, 15), ncols=2, nrows=2)

        _make_hist_plot(data, nbins, "Raw data", axes[0, 0])
        _make_image_plot(
            data,
            self._mask,
            Normalize(vmin=vmin, vmax=vmax),
            cmap,
            under_color,
            axes[1, 0],
        )

        _make_hist_plot(result, nbins, "Normalized data", axes[0, 1])
        _make_image_plot(result, self._mask, norm, cmap, under_color, axes[1, 1])

        plt.show()


def _make_hist_plot(
    data: RasterData,
    nbins: int,
    title: str,
    ax: Axes,
) -> Axes:
    """Plot a histogram of the data."""
    hist, bins = np.histogram(data, nbins)
    cdf = hist.cumsum()
    cdf = cdf / cdf.max()
    ax.bar(bins[:-1], hist, width=bins[1:] - bins[:-1], color="tab:blue")
    ax.set_ylabel("Frequency", color="tab:blue", fontsize=14)
    ax.set_title(title, fontsize=16)
    ax2 = ax.twinx()
    ax2.plot(bins[:-1], cdf, color="tab:orange")
    ax2.set_ylabel("Cumulative frequency", color="tab:orange", fontsize=14)
    return ax


def _make_image_plot(
    data: RasterData,
    mask: RasterMask,
    norm: Normalize,
    cmap: str | Colormap,
    under_color: str | None,
    ax: Axes,
    **kwargs: Any,
) -> Axes:
    """Plot a histogram of the data."""
    masked = np.ma.masked_array(data, mask=mask)  # type: ignore[no-untyped-call,var-annotated]
    im = ax.imshow(
        masked,
        cmap=cmap,
        norm=norm,
        **kwargs,
    )
    if under_color is not None:
        im.cmap.set_under(under_color)  # type: ignore[union-attr]

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    ax.figure.colorbar(ax.images[0], cax=cax, orientation="vertical")  # type: ignore[union-attr]

    return ax
