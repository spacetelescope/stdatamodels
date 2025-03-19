"""Test lazy-loading utilities"""

import pytest
import numpy as np
import stdatamodels.jwst.datamodels as dm
from stdatamodels.jwst.datamodels.util import lazy_load_attribute


TESTFILE_ROOT = "jwst_image."
FILT = "GR150R"


@pytest.fixture
def make_and_save_models(tmp_path):
    for extension in ["fits", "asdf"]:
        # Create a new datamodel with a meta attribute
        shp = (10, 10)
        data = np.zeros(shp, dtype=np.float32)
        model = dm.ImageModel(data=data)
        model.meta.instrument.filter = FILT

        # Save the datamodel to a file
        root = TESTFILE_ROOT + extension
        path = str(tmp_path / root)
        model.save(path)
        model.close()


@pytest.mark.parametrize("extension", ["fits", "asdf"])
def test_lazy_load_attribute(make_and_save_models, extension, tmp_path):
    root = TESTFILE_ROOT + extension
    path = str(tmp_path / root)

    # Load the meta attribute from the file
    meta_attr_foo = lazy_load_attribute(path, "meta.instrument.filter")
    meta_attr_foo_list = lazy_load_attribute(path, ["meta", "instrument", "filter"])
    assert meta_attr_foo == FILT
    assert meta_attr_foo_list == FILT

    # Ensure data is not accessible
    with pytest.raises(KeyError):
        lazy_load_attribute(path, "data")


def test_load_meta_bad_inputs(make_and_save_models, tmp_path):
    # Create and save a new datamodel with a meta attribute
    shp = (500, 500)
    data = np.zeros(shp, dtype=np.float32)
    model = dm.ImageModel(data=data)
    model.meta.foo = "bar"
    path = str(tmp_path / "jwst_image.fits")
    model.save(path)

    # Cannot use this on a bad filename
    with pytest.raises(ValueError):
        lazy_load_attribute("fake.asn", "meta.foo")

    # Cannot use this on a datamodel object
    with pytest.raises(TypeError):
        lazy_load_attribute(model, "meta.foo")

    # Cannot use this on a bad attribute data type
    with pytest.raises(TypeError):
        lazy_load_attribute(path, 5)

    # Cannot use this on a non-existent attribute
    with pytest.raises(KeyError):
        lazy_load_attribute(path, "meta.baz")
