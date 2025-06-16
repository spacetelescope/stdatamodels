# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test jwst.transforms
"""

import asdf
import pytest
from astropy.modeling.models import Identity
import numpy as np
from numpy.testing import assert_allclose

from stdatamodels.jwst.transforms import models


# _RANDOM_SEED = 0x1337

"""
def test_logical():

    with NumpyRNGContext(0x1337):
        compareto = np.random.randn(10)
    with NumpyRNGContext(0x1338):
        val = np.random.randn(10)
    with NumpyRNGContext(0x1339):
        x = np.random.randn(10)
    l = models.Logical('GT', .5, 10)

    res = l(x)
    y = x.copy()
    y[np.greater(x, .5)] = 10
    assert_allclose(res, npres)
    l = models.Logical('lt', compareto, val)
    cond = np.less(x, compareto)
    y = x.copy()
    y[cond] = val[cond]
    assert_allclose(res, npres)
"""


def test_ideal_to_v23_roundtrip():
    """
    Test roundtripping of the transforms.
    """
    v2i = models.V2V3ToIdeal(0.4, 450, 730, 1)
    x, y = 450, 730
    assert_allclose(v2i.inverse(*v2i(x, y)), (x, y))


@pytest.mark.parametrize(
    ("wavelength", "n"), [(1e-6, 1.43079543), (2e-6, 1.42575377), (5e-6, 1.40061966)]
)
def test_refraction_index(wavelength, n):
    """
    Tests the computation of the refraction index.
    True values are from the ESA pipeline.
    Reference values are from the PRISM reference file from CV3.
    """
    temp_sys = 37.06107795068881  # in K
    tref = 35  # in K
    pref = 0  # in atm
    pressure_sys = 0  # in atm
    kcoef = [0.58339748, 0.46085267, 3.8915394]
    lcoef = [0.00252643, 0.010078333, 1200.556]
    tcoef = [-2.66e-05, 0.0, 0.0, 0.0, 0.0, 0.0]
    n_pipeline = models.Snell.compute_refraction_index(
        wavelength, temp_sys, tref, pref, pressure_sys, kcoef, lcoef, tcoef
    )
    assert_allclose(n_pipeline, n)


def test_slit_to_msa_from_ids(tmp_path):
    slits = list(range(5))
    transforms = [Identity(2)] * len(slits)
    slit2msa = models.Slit2Msa(slits, transforms)
    assert slit2msa.slits == slits
    assert slit2msa.slit_ids == slits

    # Inverse is another defined model, with opposite input/output
    assert isinstance(slit2msa.inverse, models.Msa2Slit)
    assert slit2msa.inputs == slit2msa.inverse.outputs
    assert slit2msa.outputs == slit2msa.inverse.inputs

    for i in range(len(slits)):
        # slit name is switched from first input to last output
        assert slit2msa(i, 200, 200) == (200, 200, i)

        # and the opposite on inverse
        assert slit2msa.inverse(200, 200, i) == (i, 200, 200)

    # test roundtrip to file
    tmp_file = tmp_path / "slit2msa.asdf"
    asdf.AsdfFile({"model": slit2msa}).write_to(tmp_file)
    with asdf.open(tmp_file) as af:
        assert af["model"].slits == slits
        assert af["model"].slit_ids == slits


def test_slit_to_msa_from_slits(tmp_path):
    slits = []
    for i in range(3):
        slits.append(models.Slit(i))
    transforms = [Identity(2)] * 3

    slit2msa = models.Slit2Msa(slits, transforms)
    assert slit2msa.slits == slits
    assert slit2msa.slit_ids == list(range(len(slits)))

    # Inverse is another defined model, with opposite input/output
    assert isinstance(slit2msa.inverse, models.Msa2Slit)
    assert slit2msa.inputs == slit2msa.inverse.outputs
    assert slit2msa.outputs == slit2msa.inverse.inputs

    for i in range(len(slits)):
        # slit name is switched from first input to last output
        assert slit2msa(i, 200, 200) == (200, 200, i)

        # and the opposite on inverse
        assert slit2msa.inverse(200, 200, i) == (i, 200, 200)

    # test roundtrip to file
    tmp_file = tmp_path / "slit2msa.asdf"
    asdf.AsdfFile({"model": slit2msa}).write_to(tmp_file)
    with asdf.open(tmp_file) as af:
        assert af["model"].slits == slits
        assert af["model"].slit_ids == list(range(len(slits)))


def test_gwa_to_slit_from_ids(tmp_path):
    slits = list(range(5))
    transforms = [Identity(3)] * len(slits)
    gwa2slit = models.Gwa2Slit(slits, transforms)
    assert gwa2slit.slits == slits
    assert gwa2slit.slit_ids == slits

    # Inverse is another defined model, with opposite input/output
    assert isinstance(gwa2slit.inverse, models.Slit2Gwa)
    assert gwa2slit.inputs == gwa2slit.inverse.outputs
    assert gwa2slit.outputs == gwa2slit.inverse.inputs

    for i in range(len(slits)):
        # slit name is passed through as first input and output
        assert gwa2slit(i, 200, 200, 200) == (i, 200, 200, 200)

        # and the same on inverse
        assert gwa2slit.inverse(i, 200, 200, 200) == (i, 200, 200, 200)

    # test roundtrip to file
    tmp_file = tmp_path / "gwa2slit.asdf"
    asdf.AsdfFile({"model": gwa2slit}).write_to(tmp_file)
    with asdf.open(tmp_file) as af:
        assert af["model"].slits == slits
        assert af["model"].slit_ids == slits


def test_gwa_to_slit_from_slits(tmp_path):
    slits = []
    for i in range(3):
        slits.append(models.Slit(i))
    transforms = [Identity(3)] * 3

    gwa2slit = models.Gwa2Slit(slits, transforms)
    assert gwa2slit.slits == slits
    assert gwa2slit.slit_ids == list(range(len(slits)))

    # Inverse is another defined model, with opposite input/output
    assert isinstance(gwa2slit.inverse, models.Slit2Gwa)
    assert gwa2slit.inputs == gwa2slit.inverse.outputs
    assert gwa2slit.outputs == gwa2slit.inverse.inputs

    for i in range(len(slits)):
        # slit name is passed through as first input and output
        assert gwa2slit(i, 200, 200, 200) == (i, 200, 200, 200)

        # and the same on inverse
        assert gwa2slit.inverse(i, 200, 200, 200) == (i, 200, 200, 200)

    # test roundtrip to file
    tmp_file = tmp_path / "gwa2slit.asdf"
    asdf.AsdfFile({"model": gwa2slit}).write_to(tmp_file)
    with asdf.open(tmp_file) as af:
        assert af["model"].slits == slits
        assert af["model"].slit_ids == list(range(len(slits)))


def test_slit_to_msa_legacy(tmp_path):
    slits = []
    for i in range(3):
        slits.append(models.Slit(i))
    transforms = [Identity(2)] * 3

    with pytest.warns(DeprecationWarning, match='WCS pipeline may be incomplete'):
        slit2msa = models.Slit2MsaLegacy(slits, transforms)

    assert slit2msa.slits == slits
    assert slit2msa.slit_ids == list(range(len(slits)))

    # Legacy model has 2 outputs, no inverse
    assert not slit2msa.has_inverse()
    assert slit2msa.n_outputs == 2

    for i in range(len(slits)):
        # slit name is not propagated to output
        assert slit2msa(i, 200, 200) == (200, 200)

    # test roundtrip to file
    tmp_file = tmp_path / "slit2msa_legacy.asdf"
    asdf.AsdfFile({"model": slit2msa}).write_to(tmp_file)
    with pytest.warns(DeprecationWarning, match='WCS pipeline may be incomplete'):
        with asdf.open(tmp_file) as af:
            assert af["model"].slits == slits
            assert af["model"].slit_ids == list(range(len(slits)))


def _invdisp_interp_old(model, x0, y0, wavelength):
    """
    Legacy interpolation function for NIRCAM backward grism dispersion.

    This function is used to ensure that the new model's output is identical to the
    legacy model's output for the same inputs (to within some tolerance).
    """
    t0 = np.linspace(0.0, 1.0, 40)
    t_re = np.reshape(t0, [len(t0), *map(int, np.ones_like(np.shape(x0)))])
    if len(model) == 2:
        xr = (np.ones_like(t_re) * model[0](x0, y0)) + (t_re * model[1](x0, y0))
    elif len(model) == 3:
        xr = (
            (np.ones_like(t_re) * model[0](x0, y0))
            + (t_re * model[1](x0, y0))
            + (t_re**2 * model[2](x0, y0))
        )
    so = np.argsort(xr, axis=1)
    f = np.zeros_like(wavelength)
    for i, w in enumerate(wavelength):
        f[i] = np.interp(w, np.take_along_axis(xr, so, axis=1)[:, i], t0)
    return f


@pytest.mark.parametrize("n_coeffs", [2, 3])
def test_nircam_backward_grism_dispersion(n_coeffs):
    """Ensure algorithm change works similarly to legacy code."""

    def _mock_coeff(x,y):
        """
        Simulate dependence of the polynomial coefficients on the detector position.

        The output of ldmodel should be a list of coefficients that are each themselves
        a polynomial function of x and y. The output should be scaled to return values
        that are in the range of wavelengths in microns.
        """
        return (x/100)*1e-6

    lmodel = [_mock_coeff]*n_coeffs

    orders = [1,2]
    lmodels = [lmodel] * len(orders)
    xmodels = [Identity(1)] * len(orders)
    ymodels = [Identity(1)] * len(orders)

    sampling = 80
    # imagine we are dispersing a square 5x5 source
    # then x0, y0 are expected to be flattened arrays of the grid
    # such that each (x0[i], y0[i]) corresponds to a unique pixel in the source
    # but x0 or y0 itself can and usually will have repeated values
    x = np.linspace(100, 200, 5)
    y = np.linspace(90, 190, 5)
    x0, y0 = np.meshgrid(x, y, indexing='ij')
    x0 = x0.flatten()
    y0 = y0.flatten()

    wl = np.linspace(1.5e-6, 2.5e-6, 21)  # 2 microns
    model = models.NIRCAMBackwardGrismDispersion(orders, lmodels, xmodels, ymodels)
    t_out = model.invdisp_interp(lmodels[0], x0, y0, wl, sampling=sampling)

    # for this version we need to make x0, y0, wl all have same shape
    t2_out = np.empty_like(t_out)
    for i, this_wl in enumerate(wl):
        wl2 = this_wl * np.ones_like(x0)
        t2 = _invdisp_interp_old(lmodels[0], x0, y0, wl2)
        t2_out[i] = t2

    assert_allclose(t_out, t2_out, atol=1e-3, rtol=0)


def test_nircam_backward_grism_dispersion_single():
    """Smoke test to ensure works on single-valued inputs as well."""
    def _mock_coeff(x,y):
        return (x/100)*1e-6

    lmodel = [_mock_coeff]*2

    orders = np.array([1])
    lmodels = [lmodel] * len(orders)
    xmodels = [Identity(1)] * len(orders)
    ymodels = [Identity(1)] * len(orders)

    # many wavelengths, single x0, y0
    x0 = 150
    y0 = 140
    wl = np.linspace(1.5e-6, 2.5e-6, 21)  # 2 microns
    model = models.NIRCAMBackwardGrismDispersion(orders, lmodels, xmodels, ymodels)
    xi, yi, x, y, order = model.evaluate(x0, y0, wl, orders)
    assert xi.size == wl.size
    assert yi.size == wl.size
    assert x == x0
    assert y == y0
    assert_allclose(order, orders[0])

    # many x0, y0, single wavelength
    x0 = np.linspace(100, 200, 11)
    y0 = np.linspace(90, 190, 11)
    wl = 2e-6  # 2 microns
    model = models.NIRCAMBackwardGrismDispersion(orders, lmodels, xmodels, ymodels)
    xi, yi, x, y, order = model.evaluate(x0, y0, wl, orders)
    assert xi.size == x0.size
    assert yi.size == y0.size
