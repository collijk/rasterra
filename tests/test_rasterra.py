import numpy as np
from affine import Affine


def test_rasterra() -> None:
    import rasterra as rt

    data = np.arange(100).reshape(10, 10)
    raster = rt.RasterArray(
        data,
        transform=Affine.identity(),
        crs="EPSG:4326",
        no_data_value=-1,
    )
    assert np.all(raster.to_numpy() == data)
