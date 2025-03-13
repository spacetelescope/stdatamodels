"""Test util.load_meta_attribute."""

import pytest
from sys import getsizeof
import numpy as np
import stdatamodels.jwst.datamodels as dm
from stdatamodels.jwst.datamodels.util import load_meta_attribute


@pytest.mark.parametrize("extension", ["fits", "asdf"])
def test_load_meta(extension, tmp_path):
    # Create and save a new datamodel with a meta attribute
    shp = (500, 500)
    data = np.zeros(shp, dtype=np.float32)
    model = dm.ImageModel(data=data)
    model.meta.foo = "bar"
    root = "jwst_image." + extension
    path = str(tmp_path / root)
    model.save(path)

    # Load the meta attribute from the file
    meta_attr_foo = load_meta_attribute(path, "meta.foo")
    meta_attr_foo_list = load_meta_attribute(path, ["meta", "foo"])
    assert meta_attr_foo == "bar"
    assert meta_attr_foo_list == "bar"

    # Ensure meta attributes of data are accessible
    # TODO: these come out differently for ASDF and FITS files
    # data_shape = load_meta_attribute(path, "data.shape")
    # assert shp == tuple(data_shape)

    # Ensure that data itself is not in memory when attempting to access "data"
    data_meta = load_meta_attribute(path, "data")
    assert getsizeof(data_meta) < getsizeof(data)


def test_load_meta_bad_inputs(tmp_path):
    # Create and save a new datamodel with a meta attribute
    shp = (500, 500)
    data = np.zeros(shp, dtype=np.float32)
    model = dm.ImageModel(data=data)
    model.meta.foo = "bar"
    path = str(tmp_path / "jwst_image.fits")
    model.save(path)

    # Cannot use this on a datamodel object
    with pytest.raises(TypeError):
        load_meta_attribute(model, "meta.foo")

    # Cannot use this on a bad attribute data type
    with pytest.raises(TypeError):
        load_meta_attribute(path, 5)

    # Cannot use this on a non-existent attribute
    with pytest.raises(KeyError):
        load_meta_attribute(path, "meta.baz")
