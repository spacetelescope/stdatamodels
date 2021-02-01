"""Test model resource management"""
from pathlib import Path

from models import FitsModel


# Test data path
DATA_PATH = Path(__file__).parent / 'data'


def test_context_management(tmp_path):
    """Ensure working across context management"""
    new_model_filename = tmp_path / 'new_model.fits'

    with FitsModel(DATA_PATH / 'fits_model.fits') as model:
        new_model = FitsModel(model)
        assert len(new_model._models_using_resources) == 2

    assert len(new_model._models_using_resources) == 1
    new_model.save(new_model_filename)

    # Success is no exceptions and the file exists
    assert new_model_filename.exists()

    # Close up.
    new_model.close()
    assert len(new_model._models_using_resources) == 0


def test_reinstantiation(tmp_path):
    """Ensure file resources exist after re-instantiation

    After re-instantiating a model that has been constructed
    from a file, the original model should be closeable
    without affecting the underlying file resources for the new
    model.
    """
    new_model_filename = tmp_path / 'new_model.fits'

    model = FitsModel(DATA_PATH / 'fits_model.fits')
    new_model = FitsModel(model)
    assert len(new_model._models_using_resources) == 2

    model.close()
    assert len(new_model._models_using_resources) == 1

    # Success is no exceptions and the file exists
    new_model.save(new_model_filename)
    assert new_model_filename.exists()

    # Close up.
    new_model.close()
    assert len(new_model._models_using_resources) == 0
