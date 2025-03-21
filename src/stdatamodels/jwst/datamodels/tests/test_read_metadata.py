"""Test utilities for loading metadata without loading entire model."""

import pytest
import numpy as np
from pathlib import Path
from astropy.time import Time
import stdatamodels.jwst.datamodels as dm
from stdatamodels.jwst.datamodels.util import read_metadata


TESTFILE_ROOT = "jwst_image."
FILT = "GR150R"
INPUT_TIME = "2021-01-01 00:00:00.000"


@pytest.fixture
def imagemodel():
    """Create a new datamodel with meta attributes and relatively large data array."""
    data = np.zeros((1000, 1000), dtype=np.float32)
    model = dm.ImageModel(data)
    model.meta.instrument.filter = FILT

    # give this an astropy time to ensure it is cast to string
    model.meta.observation.date = Time(INPUT_TIME, format="iso", scale="utc")
    return model


@pytest.fixture(params=["fits", "asdf"])
def model_path(request, tmp_path, imagemodel):
    """Save the datamodel to an ASDF or FITS file."""
    extension = request.param
    root = TESTFILE_ROOT + extension
    path = str(tmp_path / root)
    imagemodel.save(path)
    imagemodel.close()
    return Path(path)


@pytest.mark.parametrize("is_str", [True, False])
def test_read_metadata(model_path, is_str):
    """Test metadata loading to dict."""
    # Load the metadata. ensure str and path are both ok
    if is_str:
        meta = read_metadata(str(model_path))
    else:
        meta = read_metadata(model_path)

    # Ensure the dict is flat, i.e., none of the vals in keys are themselves dicts
    assert isinstance(meta, dict)
    assert all(not isinstance(v, dict) for v in meta.values())

    # Ensure the metadata has the expected attributes
    # with times re-cast from astropy Time to string (and not asdf.tagged.TaggedString)
    assert isinstance(meta["meta.instrument.filter"], str)
    assert isinstance(meta["meta.observation.date"], str)
    assert meta["meta.instrument.filter"] == FILT
    assert meta["meta.observation.date"] == INPUT_TIME
    assert meta["meta.filename"] == model_path.name

    # Ensure attributes in schema but not in model are not present
    assert "meta.instrument.detector" not in meta.keys()

    # Ensure the metadata does not have data attributes
    assert "data" not in meta


def test_read_metadata_nested(model_path):
    """Test flatten=False mode."""
    meta = read_metadata(model_path, flatten=False)
    assert isinstance(meta, dict)
    assert isinstance(meta["meta"], dict)

    # Ensure the metadata has the expected attributes
    assert meta["meta"]["instrument"]["filter"] == FILT
    assert meta["meta"]["observation"]["date"] == INPUT_TIME


def test_data_never_loaded(model_path, monkeypatch):
    """Test that data is never loaded when reading metadata."""

    def throw_error(self):
        raise Exception()  # noqa: TRY002

    if model_path.suffix == ".asdf":
        import asdf

        monkeypatch.setattr(asdf, "open", throw_error)
        read_metadata(model_path)
    else:
        from astropy.io import fits

        monkeypatch.setattr(fits.ImageHDU, "data", property(throw_error))

        with fits.open(model_path) as hdulist:
            monkeypatch.setattr(fits, "open", lambda *args, **kwargs: hdulist)
            read_metadata(model_path)


def test_error_read_json():
    """Attempting to read_metadata on an asn file should raise an error."""
    with pytest.raises(ValueError):
        read_metadata("asn.json")


def test_error_read_open_model(model_path):
    """Attempting to read_metadata on an open datamodel should raise an error."""
    model = dm.open(model_path)
    with pytest.raises(TypeError):
        read_metadata(model)


def test_error_schema_not_found(model_path):
    """Attempting to read_metadata with an unknown model type should raise an error."""
    with pytest.raises(ValueError):
        read_metadata(model_path, model_type="foo")
