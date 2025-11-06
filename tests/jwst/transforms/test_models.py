# Licensed under a 3-clause BSD style license - see LICENSE.rst
import warnings

import asdf
import numpy as np
import pytest
from asdf_astropy.testing.helpers import assert_model_roundtrip
from astropy.modeling import CompoundModel
from astropy.modeling.models import Const1D, Rotation2D, Shift
from gwcs.spectroscopy import AnglesFromGratingEquation3D
from gwcs.spectroscopy import WavelengthFromGratingEquation as WavelengthGWCS
from numpy.testing import assert_allclose

from stdatamodels.jwst.transforms.models import (
    AngleFromGratingEquation,
    DirCos2Unitless,
    Gwa2Slit,
    Logical,
    NirissSOSSModel,
    Rotation3DToGWA,
    Slit,
    Snell,
    Unitless2DirCos,
    WavelengthFromGratingEquation,
)

m1 = Shift(1) & Shift(2) | Rotation2D(3.1)
m2 = Shift(2) & Shift(2) | Rotation2D(23.1)


test_models = [
    DirCos2Unitless(),
    Unitless2DirCos(),
    Rotation3DToGWA(angles=[12.1, 1.3, 0.5, 3.4], axes_order="xyzx"),
    Logical("GT", 5, 10),
    Logical("LT", np.ones((10,)) * 5, np.arange(10)),
    Snell(
        angle=-16.5,
        kcoef=[0.583, 0.462, 3.891],
        lcoef=[0.002526, 0.01, 1200.556],
        tcoef=[-2.66e-05, 0.0, 0.0, 0.0, 0.0, 0.0],
        tref=35,
        pref=0,
        temperature=35,
        pressure=0,
    ),
]


@pytest.mark.parametrize(("model"), test_models)
def test_model_roundtrip(tmpdir, model, version=None):
    assert_model_roundtrip(model, tmpdir)


def test_anglefromgratingequation_replace(tmpdir, version=None):
    """Ensure that replacement of deprecated AngleFromGratingEquation with gwcs equivalent works."""

    # Create the deprecated model
    groove_density = 20000.0
    order = -1
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        deprecated_model = AngleFromGratingEquation(groove_density, order)

    # Test serialization
    path = str(tmpdir / "anglefromgrating.asdf")
    with asdf.AsdfFile({"model": deprecated_model}) as af:
        af.write_to(path)

    # Test deserialization - should convert to gwcs model and raise UserWarning
    with pytest.warns(UserWarning, match="deprecated stdatamodels GratingEquation"):
        with asdf.open(path) as af:
            loaded_model = af["model"]

    assert isinstance(loaded_model, CompoundModel)
    assert isinstance(loaded_model[4], AnglesFromGratingEquation3D)

    # Test that the models produce equivalent results
    lam = 2.0e-6
    alpha_in = np.array([0.1, 0.2])
    beta_in = np.array([0.05, 0.1])
    z = np.array([0.9, 0.95])

    # Evaluate both models in identical ways
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        alpha_out_old, beta_out_old, z_out_old = deprecated_model(lam, alpha_in, beta_in, z)
    alpha_out_new, beta_out_new, z_out_new = loaded_model(lam, alpha_in, beta_in, z)

    # Results should be equivalent
    assert_allclose(alpha_out_new, alpha_out_old, rtol=1e-10)
    assert_allclose(beta_out_new, beta_out_old, rtol=1e-10)
    assert_allclose(z_out_new, z_out_old, rtol=1e-10)


def test_wavelengthfromgratingequation_replace(tmpdir, version=None):
    """Ensure that replacement of deprecated WavelengthFromGratingEquation with gwcs equivalent works."""
    # Create the deprecated model
    groove_density = 25000.0
    order = 2

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        deprecated_model = WavelengthFromGratingEquation(groove_density, order)

    # Test serialization
    path = str(tmpdir / "wavelengthfromgrating.asdf")
    with asdf.AsdfFile({"model": deprecated_model}) as af:
        af.write_to(path)

    # Test deserialization - should convert to gwcs model and raise UserWarning
    with pytest.warns(UserWarning, match="deprecated stdatamodels GratingEquation"):
        with asdf.open(path) as af:
            loaded_model = af["model"]
    assert isinstance(loaded_model, CompoundModel)
    assert isinstance(loaded_model[1], WavelengthGWCS)

    # Test that the models produce equivalent results
    alpha_in = np.array([0.1, 0.2])
    beta_in = np.array([0.05, 0.1])
    alpha_out = np.array([0.15, 0.25])

    # Evaluate both models in identical ways
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        lam_old = deprecated_model(alpha_in, beta_in, alpha_out)
    lam_new = loaded_model(alpha_in, beta_in, alpha_out)

    # Results should be equivalent
    assert_allclose(lam_new, lam_old, rtol=1e-10)


def test_gwa_to_slit(tmpdir):
    transforms = [m1, m2]
    s0 = Slit("s0", 1, 2, 3, 4, 5, 6, 7, 8)
    s1 = Slit("s1", 10, 20, 30, 40, 50, 60, 70, 80)
    slits = [s0, s1]
    m = Gwa2Slit(slits, transforms)
    assert_model_roundtrip(m, tmpdir)

    slits = [1, 2]
    m = Gwa2Slit(slits, transforms)
    assert_model_roundtrip(m, tmpdir)


def test_niriss_soss(tmpdir):
    """Regression test for bugs discussed in issue #7401"""
    spectral_orders = [1, 2, 3]
    models = [
        Const1D(1.0) & Const1D(2.0) & Const1D(3.0),
        Const1D(4.0) & Const1D(5.0) & Const1D(6.0),
        Const1D(7.0) & Const1D(8.0) & Const1D(9.0),
    ]

    soss_model = NirissSOSSModel(spectral_orders, models)

    # Check that no warning is issued when serializing
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert_model_roundtrip(soss_model, tmpdir)

    # Check tag is the latest version
    path = str(tmpdir / "test.asdf")
    with asdf.AsdfFile({"model": soss_model}) as af:
        af.write_to(path)

    tagged_tree = asdf.util.load_yaml(path, tagged=True)
    assert "tag:stsci.edu:jwst_pipeline/niriss_soss" in tagged_tree["model"]._tag


def test_niriss_soss_legacy(test_data_path):
    data = test_data_path / "niriss_soss.asdf"

    # confirm that the file contains the legacy tag
    tagged_tree = asdf.util.load_yaml(data, tagged=True)
    assert tagged_tree["model"]._tag == "tag:stsci.edu:jwst_pipeline/niriss-soss-0.7.0"

    # test that it opens with the legacy tag
    with asdf.open(data) as af:
        model = af["model"]
        assert model.spectral_orders == [1, 2, 3]
        assert (model.models[1].parameters == (1.0, 2.0, 3.0)).all()
        assert (model.models[2].parameters == (4.0, 5.0, 6.0)).all()
        assert (model.models[3].parameters == (7.0, 8.0, 9.0)).all()
