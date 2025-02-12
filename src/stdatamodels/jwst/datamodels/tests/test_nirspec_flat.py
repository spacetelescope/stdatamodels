"""Tests for nirspec flat field models."""

import numpy as np
import pytest
from stdatamodels.jwst.datamodels import NirspecFlatModel, NirspecQuadFlatModel


@pytest.fixture(scope="module")
def flatmodel():
    rng = np.random.default_rng()
    data = rng.random((100, 100))
    dq = rng.integers(0, 2, (100, 100))
    return NirspecFlatModel(data, dq=dq)


def test_initialize_quad_from_flat(flatmodel):
    """
    Cover a bug where attempting to initialize a quad flat model from a flat model would fail.
    """
    quadmodel = NirspecQuadFlatModel(flatmodel)
    assert isinstance(quadmodel, NirspecQuadFlatModel)
    assert np.allclose(quadmodel.quadrants[0].data, flatmodel.data)
    assert np.allclose(quadmodel.quadrants[0].dq, flatmodel.dq)
