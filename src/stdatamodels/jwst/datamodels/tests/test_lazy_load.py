"""Test lazy-loading utilities"""

import pytest
import numpy as np
from sys import getsizeof
from astropy.time import Time
import stdatamodels.jwst.datamodels as dm
from stdatamodels.jwst.datamodels.util import get_metadata


TESTFILE_ROOT = "jwst_image."
FILT = "GR150R"
INPUT_TIME = "2021-01-01 00:00:00.000"
DATA = np.zeros((1000, 1000), dtype=np.float32)


@pytest.fixture
def make_and_save_models(tmp_path):
    """Create a new datamodel with a meta attribute and relatively large data array."""
    model = dm.ImageModel(DATA)
    model.meta.instrument.filter = FILT

    # give this an astropy time to ensure it is cast to string
    model.meta.observation.date = Time(INPUT_TIME, format="iso", scale="utc")

    for extension in ["fits", "asdf"]:
        # Save the datamodel to a file
        root = TESTFILE_ROOT + extension
        path = str(tmp_path / root)
        model.save(path)
        model.close()


@pytest.mark.parametrize("extension", ["fits", "asdf"])
def test_get_metadata(make_and_save_models, extension, tmp_path):
    """Test lazy loading of a single attribute. Data should not be accessible."""
    root = TESTFILE_ROOT + extension
    path = str(tmp_path / root)

    # Load the metadata
    meta = get_metadata(path)

    # Ensure the dict is flat, i.e., none of the vals in keys are themselves dicts
    assert isinstance(meta, dict)
    assert all(not isinstance(v, dict) for v in meta.values())

    # Ensure the metadata has the expected attributes
    # with times re-cast to string
    assert meta["meta.instrument.filter"] == FILT
    assert meta["meta.observation.date"] == INPUT_TIME

    # Ensure attributes in schema but not in model are there but give None
    assert meta["meta.instrument.detector"] is None

    # Ensure the metadata does not have data attributes
    assert "data" not in meta
    assert getsizeof(meta) < getsizeof(DATA)


def test_get_metadata_bad_inputs(make_and_save_models, tmp_path):
    # Create and save a new datamodel with a meta attribute
    shp = (500, 500)
    data = np.zeros(shp, dtype=np.float32)
    model = dm.ImageModel(data=data)
    model.meta.foo = "bar"
    path = str(tmp_path / "jwst_image.fits")
    model.save(path)

    # Cannot use this on an asn file
    with pytest.raises(ValueError):
        get_metadata("asn.json")

    # Cannot use this on a datamodel object
    with pytest.raises(TypeError):
        get_metadata(model)

    # Bad custom model type causes error
    with pytest.raises(ValueError):
        get_metadata(path, model_type="foo")
