"""Test lazy-loading utilities"""

import pytest
import numpy as np
import stdatamodels.jwst.datamodels as dm
from stdatamodels.jwst.datamodels.util import lazy_load_attribute, lazy_load_tree
from sys import getsizeof


TESTFILE_ROOT = "jwst_image."
FILT = "GR150R"
DATA = np.zeros((1000, 1000), dtype=np.float32)


@pytest.fixture
def make_and_save_models(tmp_path):
    # Create a new datamodel with a meta attribute
    # and relatively large data array
    model = dm.ImageModel(DATA)
    model.meta.instrument.filter = FILT

    for extension in ["fits", "asdf"]:
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


@pytest.mark.parametrize("extension", ["asdf", "fits"])
def test_lazy_load_tree(make_and_save_models, extension, tmp_path):
    root = TESTFILE_ROOT + extension
    path = str(tmp_path / root)

    # Load the entire meta tree from the file
    tree = lazy_load_tree(path)

    # ensure the tree has attributes that have been set
    assert tree["meta"]["instrument"]["filter"] == FILT

    # ensure the tree has attributes that are in schema but have not been set
    assert tree["meta"]["instrument"]["detector"] is None

    # ensure the tree does not have data attributes
    assert "data" not in tree

    # ensure the memory usage of tree is lower than memory usage of data
    assert getsizeof(tree) < getsizeof(DATA)


def test_lazy_load_bad_inputs(make_and_save_models, tmp_path):
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
