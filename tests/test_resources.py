"""Test model resource management"""
import gc

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal
import psutil

from models import FitsModel


@pytest.mark.parametrize("extension", ["asdf", "fits"])
def test_context_management(extension, tmp_path):
    """Ensure working across context management"""
    original_path = tmp_path / f"original.{extension}"
    new_path = tmp_path / f"new.{extension}"

    process = psutil.Process()
    base_count = len(process.open_files())

    array = np.random.uniform(size=(1024, 1024))

    with FitsModel() as model:
        model.data = array
        model.save(original_path)

    # No files left open by creating and saving a model:
    assert len(process.open_files()) == base_count

    with FitsModel(original_path) as model:
        # Count should be higher due to opening the file:
        model_count = len(process.open_files())
        assert model_count > base_count

        new_model = FitsModel(model)

    # No files should be closed yet because new_model still
    # needs the resources:
    assert len(process.open_files()) == model_count

    new_model.save(new_path)
    new_model.close()

    # Back to the original state:
    assert len(process.open_files()) == base_count

    # Confirm that the array was written accurately:
    with FitsModel(new_path) as model:
        assert_array_almost_equal(model.data, array)


@pytest.mark.parametrize("extension", ["asdf", "fits"])
def test_close(extension, tmp_path):
    """Ensure file resources exist after re-instantiation
    After re-instantiating a model that has been constructed
    from a file, the original model should be closeable
    without affecting the underlying file resources for the new
    model.
    """
    original_path = tmp_path / f"original.{extension}"
    new_path = tmp_path / f"new.{extension}"

    process = psutil.Process()
    base_count = len(process.open_files())

    array = np.random.uniform(size=(1024, 1024))

    model = FitsModel()
    model.data = array
    model.save(original_path)
    model.close()

    # No files left open by creating and saving a model:
    assert len(process.open_files()) == base_count

    model = FitsModel(original_path)
    # Count should be higher due to opening the file:
    model_count = len(process.open_files())
    assert model_count > base_count

    new_model = FitsModel(model)
    model.close()

    # No files should be closed yet because new_model still
    # needs the resources:
    assert len(process.open_files()) == model_count

    new_model.save(new_path)
    new_model.close()

    # Back to the original state:
    assert len(process.open_files()) == base_count

    # Confirm that the array was written accurately:
    model = FitsModel(new_path)
    assert_array_almost_equal(model.data, array)
    model.close()


@pytest.mark.parametrize("extension", ["asdf", "fits"])
def test_multiple_close(extension, tmp_path):
    """
    Confirm that multiple calls to close() on the same
    model does not prematurely close the file.
    """
    file_path = tmp_path / f"test.{extension}"

    process = psutil.Process()
    base_count = len(process.open_files())

    array = np.random.uniform(size=(1024, 1024))

    model = FitsModel()
    model.data = array
    model.save(file_path)
    model.close()

    # No files left open by creating and saving a model:
    assert len(process.open_files()) == base_count

    model = FitsModel(file_path)
    # Count should be higher due to opening the file:
    model_count = len(process.open_files())
    assert model_count > base_count

    new_model = FitsModel(model)
    model.close()

    # No files should be closed yet because new_model still
    # needs the resources:
    assert len(process.open_files()) == model_count

    # Close the original model a second time:
    model.close()

    # Still no files closed:
    assert len(process.open_files()) == model_count

    new_model.close()

    # Back to the original state:
    assert len(process.open_files()) == base_count


@pytest.mark.parametrize("extension", ["asdf", "fits"])
def test_delete(extension, tmp_path):
    """Deleting the model should also not close files
    until the last model has been deleted."""
    original_path = tmp_path / f"original.{extension}"
    new_path = tmp_path / f"new.{extension}"

    process = psutil.Process()
    base_count = len(process.open_files())

    array = np.random.uniform(size=(1024, 1024))

    model = FitsModel()
    model.data = array
    model.save(original_path)
    del model
    gc.collect()

    # No files left open by creating and saving a model:
    assert len(process.open_files()) == base_count

    model = FitsModel(original_path)
    # Count should be higher due to opening the file:
    model_count = len(process.open_files())
    assert model_count > base_count

    new_model = FitsModel(model)
    del model
    gc.collect()

    # No files should be closed yet because new_model still
    # needs the resources:
    assert len(process.open_files()) == model_count

    new_model.save(new_path)
    del new_model
    gc.collect()

    # Back to the original state:
    assert len(process.open_files()) == base_count

    # Confirm that the array was written accurately:
    model = FitsModel(new_path)
    assert_array_almost_equal(model.data, array)
    del model
    gc.collect()
