"""Test utilities for loading metadata without loading entire model."""

import pytest
import numpy as np
from pathlib import Path
from astropy.time import Time
import stdatamodels.jwst.datamodels as dm
from stdatamodels.jwst.datamodels.util import read_metadata, _to_flat_dict
from astropy.io import fits


IMAGEFILE_ROOT = "jwst_image."
MULTISLITFILE_ROOT = "jwst_multislit."
FILT = "GR150R"
INPUT_TIME = "2021-01-01 00:00:00.000"


@pytest.fixture
def recursive_tree():
    """Create a recursive tree to substitute for a WCS object"""

    w = {"inputs": "test"}
    w["outputs"] = w
    return w


@pytest.fixture
def imagemodel(recursive_tree):
    """Create an imagemodel with meta attributes and data array."""
    data = np.zeros((10, 10), dtype=np.float32)
    model = dm.ImageModel(data)
    model.meta.instrument.filter = FILT
    model.meta.wcs = recursive_tree

    model.cal_logs = {
        "assign_wcs": ["baz", "qux"],
        "extract_1d": ["foo", "bar"],
    }

    # give this an astropy time to ensure it is cast to string
    model.meta.observation.date = Time(INPUT_TIME, format="iso", scale="utc")
    return model


@pytest.fixture
def multislitmodel():
    """Create a multislit datamodel with meta attributes and data array."""
    slit0 = dm.SlitModel(np.zeros((10, 10), dtype=np.float32))
    slit0.meta.instrument.filter = FILT
    slit0.name = "slit0"
    slit1 = dm.SlitModel(np.ones((10, 10), dtype=np.float32))
    slit1.name = "slit1"
    model = dm.MultiSlitModel()
    model.slits.append(slit0)
    model.slits.append(slit1)
    model.meta.instrument.filter = FILT

    # give this an astropy time to ensure it is cast to string
    model.meta.observation.date = Time(INPUT_TIME, format="iso", scale="utc")
    return model


@pytest.fixture(params=["fits", "asdf"])
def model_path(request, tmp_path, imagemodel):
    """Save the imagemodel to an ASDF or FITS file."""
    extension = request.param
    root = IMAGEFILE_ROOT + extension
    path = str(tmp_path / root)
    imagemodel.save(path)
    imagemodel.close()
    return Path(path)


@pytest.fixture(params=["fits", "asdf"])
def multislit_path(request, tmp_path, multislitmodel):
    """Save the multislitmodel to an ASDF or FITS file."""
    extension = request.param
    root = MULTISLITFILE_ROOT + extension
    path = str(tmp_path / root)
    multislitmodel.save(path)
    multislitmodel.close()
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

    # Ensure the metadata does not have data or wcs attributes
    assert "data" not in meta
    assert "meta.wcs" not in meta

    # Ensure cal_logs is a single string
    assert isinstance(meta["cal_logs"], str)
    expected_cal_log = "baz\nqux\nfoo\nbar\n"
    assert meta["cal_logs"] == expected_cal_log


def test_read_metadata_nested(model_path):
    """Test flatten=False mode."""
    meta = read_metadata(model_path, flatten=False)
    assert isinstance(meta, dict)
    assert isinstance(meta["meta"], dict)

    # Ensure the metadata has the expected attributes
    assert meta["meta"]["instrument"]["filter"] == FILT
    assert meta["meta"]["observation"]["date"] == INPUT_TIME


def test_read_metadata_multislit(multislit_path):
    """Test metadata loading for multislit model."""
    meta = read_metadata(multislit_path)
    assert isinstance(meta, dict)
    assert all(not isinstance(v, dict) for v in meta.values())

    # Ensure the metadata has the expected attributes
    assert isinstance(meta["meta.instrument.filter"], str)
    assert isinstance(meta["meta.observation.date"], str)
    assert meta["meta.instrument.filter"] == FILT
    assert meta["meta.observation.date"] == INPUT_TIME
    assert meta["meta.filename"] == multislit_path.name

    # Ensure attributes in schema but not in model are not present
    assert "meta.instrument.detector" not in meta.keys()

    # Ensure the slit metadata is also in here
    assert meta["slits.0.name"] == "slit0"
    assert meta["slits.1.name"] == "slit1"


def test_read_metadata_multislit_nested(multislit_path):
    """Test flatten=False mode for multislit model."""
    meta = read_metadata(multislit_path, flatten=False)
    assert isinstance(meta, dict)
    assert isinstance(meta["meta"], dict)
    assert isinstance(meta["slits"], list)

    # Ensure the metadata has the expected attributes
    assert meta["meta"]["instrument"]["filter"] == FILT
    assert meta["meta"]["observation"]["date"] == INPUT_TIME
    assert meta["meta"]["filename"] == multislit_path.name

    # Ensure attributes in schema but not in model are not present
    assert "meta.instrument.detector" not in meta.keys()

    # Ensure the slit metadata is also in here
    assert meta["slits"][0]["name"] == "slit0"
    assert meta["slits"][1]["name"] == "slit1"


@pytest.mark.parametrize("multislit_path", ["fits"], indirect=True)
def test_multislit_fits_update(multislit_path):
    """Ensure a fits_update is done for slit metadata, even though slits is list-like."""
    new_slitname = "foo"
    new_filename = "multislit_modified.fits"
    new_path = multislit_path.with_name(new_filename)
    with fits.open(multislit_path) as hdul:
        hdul[1].header["SLTNAME"] = new_slitname
        hdul.writeto(new_path)
    
    # Load the metadata
    meta = read_metadata(new_path)

    # ensure the slit name is updated
    assert meta["slits.0.name"] == new_slitname


def test_equivalent_to_get_crds_parameters(multislit_path):
    """
    Check that read_metadata returns all attributes that get_crds_parameters does.

    Note that read_metadata output also contains e.g. meta['data'] and meta['slits.0.data'],
    although these are not loaded.
    """
    # Load the metadata
    meta = read_metadata(multislit_path)

    # load the model and get the CRDS parameters
    model = dm.open(multislit_path)
    crds_meta = model.get_crds_parameters()

    # ensure all keys in crds_meta are in meta and have the same values
    for key, val in crds_meta.items():
        assert val == meta[key]


def test_data_never_loaded(model_path, monkeypatch):
    """Test that data is never accessed when reading metadata."""

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
    """
    Attempting to read_metadata with an unknown model type should raise an error.

    This only matters for FITS files.
    """
    if model_path.suffix == ".fits":
        with pytest.raises(ValueError):
            read_metadata(model_path, model_type="foo")


@pytest.mark.parametrize("is_tuple", [True, False])
def test_nested_list_to_flat_dict(is_tuple):
    """Test that nested lists are flattened correctly."""
    # Create a nested list
    if is_tuple:
        nested_list = (
            {"a": 1, "b": (2, 3)},
            {"c": 4, "d": (5, 6)},
        )
    else:
        # Use a list of dictionaries instead
        nested_list = [
            {"a": 1, "b": [2, 3]},
            {"c": 4, "d": [5, 6]},
        ]

    # Flatten the list
    flat_dict = _to_flat_dict(nested_list)

    # Check that the keys are flattened correctly
    assert flat_dict == {
        "0.a": 1,
        "0.b.0": 2,
        "0.b.1": 3,
        "1.c": 4,
        "1.d.0": 5,
        "1.d.1": 6,
    }