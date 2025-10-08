# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test jwst.transforms
"""

import asdf
import numpy as np
import pytest
from asdf_astropy.testing.helpers import assert_model_equal
from astropy.modeling.models import Identity, Mapping, Polynomial1D, Polynomial2D
from numpy.testing import assert_allclose

from stdatamodels.jwst.transforms import models


@pytest.mark.parametrize(
    ("beta_zero", "beta_del", "channel", "expected"),
    [
        (-1.77210143797, 0.177210143797, 1, 111),
        (-2.23774549066, 0.279718186333, 2, 209),
        (np.linspace(-10, 10, 5), np.ones((5,)), 1, np.array([111, 106, 101, 96, 91])),
    ],
)
def test_miri_ab2slice(beta_zero, beta_del, channel, expected):
    model = models.MIRI_AB2Slice()
    beta = 0.0
    result = model.evaluate(beta, beta_zero, beta_del, channel)
    assert_allclose(result, expected)


@pytest.mark.parametrize(
    ("alpha_in", "beta_in", "alpha_out", "expected"),
    [
        (np.pi / 8, np.pi / 8, np.pi / 16, 1.113583608571748),
        (
            np.linspace(-np.pi / 8, np.pi / 8, 5),
            np.linspace(0, np.pi / 8, 5),
            np.linspace(-np.pi / 16, np.pi / 16, 5),
            np.array([1.04204409, 0.53019077, 0.19634954, 0.59850526, 1.11358361]),
        ),
    ],
)
def test_refractionindexfromprism(alpha_in, beta_in, alpha_out, expected):
    prism_angle = -16.5  # degrees
    prism_angle_rad = np.deg2rad(prism_angle)

    # unclear why the model requires the prism angle in degrees on init
    # and also requires the prism angle in radians on evaluation
    model = models.RefractionIndexFromPrism(prism_angle)
    n = model.evaluate(alpha_in, beta_in, alpha_out, prism_angle_rad)
    assert_allclose(n, expected)


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (10, 20),
        (np.linspace(10, 20, 5), np.linspace(30, 20, 5)),
    ],
)
def test_nirisssossmodel(x, y):
    spectral_orders = [1, 2]
    # model is unphysical but does have 2 inputs and 3 outputs like NIRISS SOSS would expect
    order_models = [Identity(2) | Mapping((0, 1, 1))] * len(spectral_orders)

    sossmodel = models.NirissSOSSModel(spectral_orders, order_models)
    assert sossmodel.spectral_orders == spectral_orders
    assert isinstance(sossmodel.models, dict)

    xout, yout, yout2 = sossmodel.evaluate(x, y, np.array([1]))
    assert_allclose(xout, x)
    assert_allclose(yout, y)
    assert_allclose(yout2, y)

    with pytest.raises(ValueError, match="Spectral order is not between"):
        sossmodel.evaluate(10, 20, -1)


def test_logical():
    # model where if value is greater than 0.5, it is set to 10
    l = models.Logical("GT", 0.5, 10)

    x = np.linspace(0, 1, 11)
    res = l(x)
    assert_allclose(res, np.where(x > 0.5, 10, x))

    # model where if value is less than 0.5, it is set to 10
    l = models.Logical("LT", 0.5, 10)
    res = l(x)
    assert_allclose(res, np.where(x < 0.5, 10, x))

    # model where if value is equal to 0.5, it is set to 10
    l = models.Logical("EQ", 0.5, 10)
    res = l(x)
    assert_allclose(res, np.where(x == 0.5, 10, x))

    # model where if value is not equal to 0.5, it is set to 10
    l = models.Logical("NE", 0.5, 10)
    res = l(x)
    assert_allclose(res, np.where(x != 0.5, 10, x))

    # test comparing to array
    compareto = x[::-1]
    l = models.Logical("GT", compareto, compareto)
    res = l(x)
    assert_allclose(res, np.where(x > compareto, compareto, x))


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (450, 730),
        (np.linspace(400, 500, 5), np.linspace(700, 800, 5)),
    ],
)
def test_ideal_to_v23_roundtrip(x, y):
    """
    Test roundtripping of the transforms.
    """
    v2i = models.V2V3ToIdeal(0.4, 450, 730, 1)
    assert_allclose(v2i.inverse(*v2i(x, y)), (x, y))


@pytest.mark.parametrize(
    ("wavelength", "n", "xval", "zval"),
    [
        (1e-6, 1.43079543, 0.08197709799990752, 0.9160061062222742),
        (2e-6, 1.42575377, 0.08010546703309275, 0.916171678990564),
        (5e-6, 1.40061966, 0.07075688081985915, 0.9169410532033251),
    ],
)
def test_refraction_index_and_snell(wavelength, n, xval, zval):
    """
    Tests the computation of the refraction index.
    True values are from the ESA pipeline.
    Reference values are from the PRISM reference file from CV3.

    Also test refraction index computation within the Snell model.
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

    # Test Snell's Law model
    angle = 10.0  # prism angle in degrees
    alpha_in = np.pi / 8  # angle of incidence in radians
    beta_in = np.pi / 8  # angle of incidence in radians
    z = 0.0  # z-coordinate, not used in this model
    model = models.Snell(angle, kcoef, lcoef, tcoef, tref, pref, temp_sys, pressure_sys)
    xout, yout, zout = model.evaluate(wavelength, alpha_in, beta_in, z)
    assert np.isclose(xout, xval)
    assert np.isclose(yout, -0.39269908169872414)
    assert np.isclose(zout, zval)


def test_refraction_index_large_delt():
    """
    Test the case where the temperature difference is large.

    If delta T is larger than 20, the refraction index of the air will be recomputed.
    """
    wavelength = 2e-6
    temp_sys = 65.0  # in K
    tref = 35  # in K
    pref = 0  # in atm
    pressure_sys = 0  # in atm
    kcoef = [0.58339748, 0.46085267, 3.8915394]
    lcoef = [0.00252643, 0.010078333, 1200.556]
    tcoef = [-2.66e-05, 0.0, 0.0, 0.0, 0.0, 0.0]
    n_pipeline = models.Snell.compute_refraction_index(
        wavelength, temp_sys, tref, pref, pressure_sys, kcoef, lcoef, tcoef
    )
    assert np.isclose(n_pipeline, 1.4254647475849418)


@pytest.mark.parametrize("temp_sys", [65, 37])
def test_snell_vectorized(temp_sys):
    """Parametrize temp_sys with one large and one small value to test both paths."""
    tref = 35  # in K
    pref = 0  # in atm
    pressure_sys = 0  # in atm
    kcoef = [0.58339748, 0.46085267, 3.8915394]
    lcoef = [0.00252643, 0.010078333, 1200.556]
    tcoef = [-2.66e-05, 0.0, 0.0, 0.0, 0.0, 0.0]
    prism_angle = 10.0  # prism angle in degrees
    model = models.Snell(prism_angle, kcoef, lcoef, tcoef, tref, pref, temp_sys, pressure_sys)

    wavelength = np.linspace(2.0, 3.0, 5) * 1e-6
    alpha_in = np.linspace(np.pi / 16, 3 * np.pi / 16, 5)  # angle of incidence in radians
    beta_in = np.linspace(-np.pi / 8, np.pi / 8, 5)  # angle of incidence in radians
    z = 0.0  # z-coordinate, not used in this model
    xout, yout, zout = model(wavelength, alpha_in, beta_in, z)
    assert xout.shape == yout.shape == zout.shape == (5,)


def test_grating_equation():
    """Test consistency between WavelengthFromGratingEquation and AngleFromGratingEquation."""
    lam = 2.0e-6  # wavelength in meters
    groovedensity = 1000.0  # grooves per meter
    order = 1  # diffraction order
    alpha_in = np.array([np.pi / 8, np.pi / 8])  # angle of incidence in radians
    beta_in = np.array([np.pi / 8, np.pi / 8])  # angle of incidence in radians
    z = np.array([0.0, 0.0])  # z-coordinate, not used in this model

    angle_transform = models.AngleFromGratingEquation(groovedensity, order)
    alpha_out, beta_out, _zout = angle_transform.evaluate(
        lam, alpha_in, beta_in, z, groovedensity, order
    )
    assert_allclose(beta_out, -beta_in)

    wavelength_transform = models.WavelengthFromGratingEquation(groovedensity, order)
    lam_out = wavelength_transform.evaluate(alpha_in, beta_in, alpha_out, groovedensity, order)
    assert_allclose(lam_out, lam)


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (200, 200),
        (np.arange(200, 206), np.arange(201, 207)),
    ],
)
def test_slit_to_msa_from_ids(tmp_path, x, y):
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
        xout, yout, iout = slit2msa(i, x, y)
        assert_allclose(xout, x)
        assert_allclose(yout, y)
        assert iout == i

        # and the opposite on inverse
        iout, xout, yout = slit2msa.inverse(x, y, i)
        assert_allclose(xout, x)
        assert_allclose(yout, y)
        assert iout == i

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


@pytest.mark.parametrize(
    ("x", "y", "z"),
    [
        (200, 200, 200),
        (np.arange(200, 206), np.arange(201, 207), np.arange(202, 208)),
    ],
)
def test_gwa_to_slit_from_ids(tmp_path, x, y, z):
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
        iout, xout, yout, zout = gwa2slit(i, x, y, z)
        assert i == iout
        assert_allclose(xout, x)
        assert_allclose(yout, y)
        assert_allclose(zout, z)

        # and the same on inverse
        iout, xout, yout, zout = gwa2slit.inverse(i, x, y, z)
        assert i == iout
        assert_allclose(xout, x)
        assert_allclose(yout, y)
        assert_allclose(zout, z)

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

    with pytest.warns(DeprecationWarning, match="WCS pipeline may be incomplete"):
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
    with pytest.warns(DeprecationWarning, match="WCS pipeline may be incomplete"):
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

    def _mock_coeff(x, y):
        """
        Simulate dependence of the polynomial coefficients on the detector position.

        The output of ldmodel should be a list of coefficients that are each themselves
        a polynomial function of x and y. The output should be scaled to return values
        that are in the range of wavelengths in microns.
        """
        return (x / 100) * 1e-6

    lmodel = [_mock_coeff] * n_coeffs

    orders = [1, 2]
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
    x0, y0 = np.meshgrid(x, y, indexing="ij")
    x0 = x0.flatten()
    y0 = y0.flatten()

    wl = np.linspace(1.5e-6, 2.5e-6, 21)  # 2 microns
    model = models.NIRCAMBackwardGrismDispersion(
        orders, lmodels, xmodels, ymodels, sampling=sampling
    )
    t_out = model.invdisp_interp(lmodels[0], x0, y0, wl)

    # for this version we need to make x0, y0, wl all have same shape
    t2_out = np.empty_like(t_out)
    for i, this_wl in enumerate(wl):
        wl2 = this_wl * np.ones_like(x0)
        t2 = _invdisp_interp_old(lmodels[0], x0, y0, wl2)
        t2_out[i] = t2

    assert_allclose(t_out, t2_out, atol=1e-3, rtol=0)


def test_nircam_backward_grism_dispersion_single():
    """Smoke test to ensure works on single-valued inputs as well."""

    def _mock_coeff(x, y):
        return (x / 100) * 1e-6

    lmodel = [_mock_coeff] * 2

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


@pytest.mark.parametrize("direction", ["row", "column"])
def test_nircam_grism_roundtrip(direction):
    """
    Do a forward grism transform for NIRCam,
    then inverse, and check that the output is the same as the input.
    """
    # Create mock polynomial models for the grism dispersion
    # make it so the results have same scaling as wavelengths in microns
    mock_l = Polynomial2D(degree=3, c1_0=1e-8)

    # mock x and y models here paramtrize a slightly curved trace
    # causing enough of a shift in the x and y coordinates
    # to ensure that the forward and backward models are not just
    # identity models.
    mock_x = Polynomial2D(degree=2, c0_0=0.1, c1_0=0.01)

    lmodel = [
        mock_l,
    ] * 2
    xmodel = [
        mock_x,
    ] * 3
    ymodel = [
        mock_x,
    ] * 3
    orders = np.array([1])
    lmodels = [lmodel] * len(orders)
    xmodels = [xmodel] * len(orders)
    ymodels = [ymodel] * len(orders)

    # many wavelengths, single x0, y0
    x0 = 150
    y0 = 140
    wl = 2.0e-6

    # now create the appropriate model for the grism[R/C]
    if direction == "row":
        forward = models.NIRCAMForwardRowGrismDispersion(
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
        )
    elif direction == "column":
        forward = models.NIRCAMForwardColumnGrismDispersion(
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
        )
    backward = models.NIRCAMBackwardGrismDispersion(
        orders,
        lmodels=lmodels,
        xmodels=xmodels,
        ymodels=ymodels,
    )

    combined = backward | forward
    xi, yi, wli, ordersi = combined.evaluate(x0, y0, wl, orders)
    assert_allclose(xi, x0)
    assert_allclose(yi, y0)
    assert_allclose(wli, wl)
    assert_allclose(ordersi, orders)


@pytest.mark.parametrize("direction", ["row", "column"])
def test_legacy_nircam_grism_roundtrip(direction):
    """
    Test that the legacy NIRCAM grism dispersion lmodel roundtrips correctly.

    This lmodel has no dependence of the polynomial coefficients on the detector position,
    so the polynomial model is simply a function of t that gives the wavelength.
    """
    mock_l = Polynomial1D(degree=1, c0=0.75, c1=1.55)
    # mock_invl = Polynomial1D(degree=1, c0=-0.48387097, c1=0.64516129)
    mock_x = Polynomial2D(degree=2, c0_0=0.1, c1_0=0.01)
    xmodel = [
        mock_x,
    ] * 3
    ymodel = [
        mock_x,
    ] * 3
    orders = np.array([1])
    lmodels = [mock_l] * len(orders)
    # invlmodels = [mock_invl] * len(orders)
    xmodels = [xmodel] * len(orders)
    ymodels = [ymodel] * len(orders)

    # single x0, y0, wl
    x0 = 150
    y0 = 140
    wl = 2.0

    if direction == "row":
        forward = models.NIRCAMForwardRowGrismDispersion(
            orders, lmodels=lmodels, xmodels=xmodels, ymodels=ymodels, sampling=40
        )
    elif direction == "column":
        forward = models.NIRCAMForwardColumnGrismDispersion(
            orders, lmodels=lmodels, xmodels=xmodels, ymodels=ymodels, sampling=40
        )
    backward = models.NIRCAMBackwardGrismDispersion(
        orders,
        lmodels=lmodels,
        xmodels=xmodels,
        ymodels=ymodels,
    )

    combined = backward | forward
    xi, yi, wli, ordersi = combined.evaluate(x0, y0, wl, orders)
    assert_allclose(xi, x0)
    assert_allclose(yi, y0)
    assert_allclose(wli, wl, rtol=1e-4)
    assert_allclose(ordersi, orders)


def test_nircam_grism_1d_linear():
    """
    Test case where model coeffs do NOT have dependence on x0, y0.

    This is used in the pipeline for at least some versions of dispy.
    """
    mock_l = Polynomial1D(degree=1, c0=0.75, c1=1.55)
    mock_x = Polynomial1D(degree=1, c0=0.1, c1=0.01)
    xmodel = [
        mock_x,
    ] * 1
    ymodel = [
        mock_x,
    ] * 1
    orders = np.array([1])
    lmodels = [mock_l] * len(orders)
    xmodels = [xmodel] * len(orders)
    ymodels = [ymodel] * len(orders)

    forward = models.NIRCAMForwardRowGrismDispersion(
        orders, lmodels=lmodels, xmodels=xmodels, ymodels=ymodels, sampling=40
    )
    backward = models.NIRCAMBackwardGrismDispersion(
        orders,
        lmodels=lmodels,
        xmodels=xmodels,
        ymodels=ymodels,
    )

    combined = backward | forward
    xi, yi, wli, ordersi = combined.evaluate(150, 140, 2.0, orders)
    assert_allclose(xi, 150)
    assert_allclose(yi, 140)
    assert_allclose(wli, 2.0)
    assert_allclose(ordersi, orders)


@pytest.mark.parametrize("direction", ["row", "column"])
def test_niriss_grism_roundtrip(direction):
    """
    Do a forward grism transform for NIRISS where dispersion is in the columnwise direction,
    then inverse, and check that the output is the same as the input.
    """
    # Create mock polynomial models for the grism dispersion
    # much simpler than NIRCam, as it does not depend on the detector position.
    # These coefficients are taken from a real reference file.
    mock_l = Polynomial1D(degree=1, c0=0.75, c1=1.55)
    mock_invl = Polynomial1D(degree=1, c0=-0.48387097, c1=0.64516129)

    # mock x and y models here paramtrize a slightly curved trace
    # causing enough of a shift in the x and y coordinates
    # to ensure that the forward and backward models are not just
    # identity models.
    mock_x = Polynomial2D(degree=2, c0_0=0.1, c1_0=0.01)

    xmodel = [
        mock_x,
    ] * 3
    ymodel = [
        mock_x,
    ] * 3
    orders = np.array([1])
    lmodels = [mock_l] * len(orders)
    invlmodels = [mock_invl] * len(orders)
    xmodels = [xmodel] * len(orders)
    ymodels = [ymodel] * len(orders)

    # single x0, y0, wl
    x0 = 150
    y0 = 140
    wl = 2.0

    # now create the appropriate model for the grism[R/C]
    if direction == "row":
        forward = models.NIRISSForwardRowGrismDispersion(
            orders, lmodels=lmodels, xmodels=xmodels, ymodels=ymodels, sampling=40
        )
    elif direction == "column":
        forward = models.NIRISSForwardColumnGrismDispersion(
            orders, lmodels=lmodels, xmodels=xmodels, ymodels=ymodels, sampling=40
        )
    backward = models.NIRISSBackwardGrismDispersion(
        orders,
        lmodels=invlmodels,
        xmodels=xmodels,
        ymodels=ymodels,
    )

    combined = backward | forward
    xi, yi, wli, ordersi = combined.evaluate(x0, y0, wl, orders)
    assert_allclose(xi, x0)
    assert_allclose(yi, y0)
    assert_allclose(wli, wl, rtol=1e-4)
    assert_allclose(ordersi, orders)


def test_miri_wfss_roundtrip():
    """
    Do a forward wfss transform for MIRI  then inverse, and check that the output is the same as the input.
    """
    # Create mock polynomial models for the dispersion
    # These coefficients are taken from a real reference file.
    mock_l = Polynomial1D(degree=1, c0=3.125, c1=10.893)
    mock_invl = Polynomial1D(degree=1, c0=-0.28688148, c1=0.09180207)

    # mock y models here parametrize a slightly curved trace
    # causing enough of a shift in the x and y coordinates
    # to ensure that the forward and backward models are not just
    # identity models.
    mock_y = Polynomial2D(degree=2, c0_0=0.1, c1_0=0.01)
    ymodel = [
        mock_y,
    ] * 3

    xmodel = [
        mock_y,
    ] * 3

    orders = np.array([1])
    lmodels = [mock_l] * len(orders)

    inv_lmodels = [mock_invl] * len(orders)
    ymodels = [ymodel] * len(orders)
    xmodels = [xmodel] * len(orders)

    # single x0, y0, wl
    x0 = 450.0
    y0 = 450.0
    wl = 6.0

    # now create the appropriate model for the forward
    forward = models.MIRIWFSSForwardDispersion(
        orders, lmodels=lmodels, xmodels=xmodels, ymodels=ymodels
    )

    backward = models.MIRIWFSSBackwardDispersion(
        orders,
        lmodels=inv_lmodels,
        xmodels=xmodels,
        ymodels=ymodels,
    )

    combined = backward | forward
    xi, yi, wli, ordersi = combined.evaluate(x0, y0, wl, orders)
    assert_allclose(xi, x0)
    assert_allclose(yi, y0)
    assert_allclose(wli, wl, rtol=1e-2)
    assert ordersi == orders


def test_miriwfss_backward_dispersion_single(tmp_path):
    """Test the input source location in BackwardDispersion = output x, y values & test converters"""
    lmodels = []
    l0 = 3.125
    l1 = 10.893
    lmodels.append(Polynomial1D(1, c0=l0, c1=l1))

    orders = np.array([1])
    xmodels = []
    x0 = 0.25132305
    x1 = 0.000000
    x2 = 0.0
    x3 = 0.0
    x4 = 0.0
    x5 = 0.0
    cpolx_0 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    cpolx_1 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    cpolx_2 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    cpolx_3 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    xmodels.append((cpolx_0, cpolx_1, cpolx_2, cpolx_3))

    ymodels = []
    y0 = 8.850746809616503
    y1 = 0.00000003
    y2 = 0.0
    y3 = 0.00000018
    y4 = 0.0
    y5 = 0.0
    cpoly_0 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    cpoly_1 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    cpoly_2 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    cpoly_3 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    ymodels.append((cpoly_0, cpoly_1, cpoly_2, cpoly_3))

    # many wavelengths, single x0, y0
    x0 = 150
    y0 = 140
    wl = np.linspace(5.5e-6, 6.5e-6, 21)  #
    model = models.MIRIWFSSBackwardDispersion(orders, lmodels, xmodels, ymodels)

    xi, yi, x, y, order = model.evaluate(x0, y0, wl, orders)
    assert xi.size == wl.size
    assert yi.size == wl.size
    assert x == x0
    assert y == y0
    assert order == 1

    # many x0, y0, single wavelength
    x0 = np.linspace(100, 200, 11)
    y0 = np.linspace(90, 190, 11)
    wl = 6e-6  # 2 microns
    model = models.MIRIWFSSBackwardDispersion(orders, lmodels, xmodels, ymodels)
    xi, yi, x, y, order = model.evaluate(x0, y0, wl, orders)
    assert xi.size == x0.size
    assert yi.size == y0.size

    # test roundtrip to file- test specific values
    tmp_file = tmp_path / "miri_wfss.asdf"
    asdf.AsdfFile({"model": model}).write_to(tmp_file)
    with asdf.open(tmp_file) as af:
        # test the full model
        assert_model_equal(model, af["model"])


def test_miriwfss_forward_dispersion(tmp_path):
    """Test test converters for forward"""
    lmodels = []  # this is the inv_disp values
    l0 = -0.28688148
    l1 = 0.09180207
    lmodels.append(Polynomial1D(1, c0=l0, c1=l1))

    orders = np.array([1])

    xmodels = []
    x0 = 0.25132305
    x1 = 0.000000
    x2 = 0.0
    x3 = 0.0
    x4 = 0.0
    x5 = 0.0
    cpolx_0 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    cpolx_1 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    cpolx_2 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    cpolx_3 = Polynomial2D(2, c0_0=x0, c1_0=x1, c2_0=x2, c0_1=x3, c1_1=x4, c0_2=x5)
    xmodels.append((cpolx_0, cpolx_1, cpolx_2, cpolx_3))

    ymodels = []
    y0 = 8.850746809616503
    y1 = 0.00000003
    y2 = 0.0
    y3 = 0.00000018
    y4 = 0.0
    y5 = 0.0
    cpoly_0 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    cpoly_1 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    cpoly_2 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    ymodels.append((cpoly_0, cpoly_1, cpoly_2))

    x0 = 450
    y0 = 450
    x = 450
    y = 450
    model = models.MIRIWFSSForwardDispersion(orders, lmodels, xmodels, ymodels)
    # test roundtrip to file- test specific values
    tmp_file = tmp_path / "miri_wfss_forward.asdf"
    asdf.AsdfFile({"model": model}).write_to(tmp_file)
    with asdf.open(tmp_file) as af:
        # test the full model
        assert_model_equal(model, af["model"])


@pytest.mark.parametrize("direction", ["row", "column"])
@pytest.mark.parametrize("instrument", ["nircam", "niriss", "miri"])
def test_grism_error_raises(direction, instrument):
    if instrument == "nircam" and direction == "row":
        ForwardModel = models.NIRCAMForwardRowGrismDispersion
    elif instrument == "nircam" and direction == "column":
        ForwardModel = models.NIRCAMForwardColumnGrismDispersion
    elif instrument == "niriss" and direction == "row":
        ForwardModel = models.NIRISSForwardRowGrismDispersion
    elif instrument == "niriss" and direction == "column":
        ForwardModel = models.NIRISSForwardColumnGrismDispersion
    if instrument == "nircam":
        BackwardModel = models.NIRCAMBackwardGrismDispersion
    elif instrument == "niriss":
        BackwardModel = models.NIRISSBackwardGrismDispersion
    elif instrument == "miri":
        ForwardModel = models.MIRIWFSSForwardDispersion
        BackwardModel = models.MIRIWFSSBackwardDispersion

    orders = np.array([1, 2])
    if instrument == "miri":
        orders = np.array([1])
    x0 = 150
    y0 = 140
    wl = 2.0
    forward = ForwardModel(orders)
    backward = BackwardModel(orders)

    # raise for order not in the list
    with pytest.raises(ValueError, match="Specified order is not available"):
        forward.evaluate(x0, y0, x0, y0, np.array([-1]))
    with pytest.raises(ValueError, match="Specified order is not available"):
        backward.evaluate(x0, y0, wl, np.array([-1]))
    # raise for negative wavelength
    with pytest.raises(ValueError, match="Wavelength should be greater than zero"):
        backward.evaluate(x0, y0, -wl, orders)


def test_error_raises_bad_transforms():
    """Test error raises for unsupported transform types."""
    x0 = 150
    y0 = 140
    t = 0.5

    poly1d = Polynomial1D(degree=1, c0=0.75, c1=1.55)
    poly2d = Polynomial2D(degree=2, c0_0=0.1, c1_0=0.01)

    # Not a model or list of models
    with pytest.raises(TypeError, match="Expected a model or list of models, but got"):
        models._evaluate_transform_guess_form("bad_model_type", x=x0, y=y0, t=t)

    # Is a list, but not all models are valid
    with pytest.raises(
        TypeError,
        match="Expected a model or list of models, but got a list containing non-model elements.",
    ):
        models._evaluate_transform_guess_form([poly1d, "bad_model_type"], x=x0, y=y0, t=t)

    # Is a single-element list, but takes in more than one input
    with pytest.raises(
        ValueError, match="Received a transform with an unexpected number of inputs"
    ):
        models._evaluate_transform_guess_form(
            [
                poly2d,
            ],
            x=x0,
            y=y0,
            t=t,
        )

    # Is a multi-element list, but takes in only one input
    with pytest.raises(
        ValueError, match="Received a transform with an unexpected number of inputs"
    ):
        models._evaluate_transform_guess_form(
            [
                poly1d,
            ]
            * 3,
            x=x0,
            y=y0,
            t=t,
        )


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (np.sqrt(2) / 2, np.sqrt(2) / 2),
        (np.linspace(0, np.pi, 5), np.linspace(0, np.pi / 4, 5)),
    ],
)
def test_dircos2unitless_roundtrip(x, y):
    """
    Test DirCos2Unitless transform model.
    """
    tr = models.Unitless2DirCos()
    assert_allclose(tr.inverse(*tr(x, y)), (x, y))


def test_rotation3d_deprecated():
    """
    Test Rotation3D transform model deprecation.
    """
    with pytest.warns(DeprecationWarning, match="Rotation3D is deprecated"):
        models.Rotation3D(angles=(0, 0, 0), axes_order="xyz")


def test_v23tosky_deprecated(tmp_path):
    """
    Test V2V3ToSky transform model deprecation, including deprecation warning
    when attempting to open.
    """
    with pytest.warns(DeprecationWarning, match="V23ToSky is deprecated"):
        model = models.V23ToSky(angles=(0, 0, 0), axes_order="xyz")

    tmp_file = tmp_path / "v23tosky.asdf"
    asdf.AsdfFile({"model": model}).write_to(tmp_file)

    with pytest.warns(DeprecationWarning, match="V23ToSky is deprecated"), asdf.open(tmp_file):
        pass


def test_grismobject_empty_init():
    model = models.GrismObject()
    for att in ["order_bounding", "partial_order"]:
        assert hasattr(model, att)
        assert isinstance(getattr(model, att), dict)
    for att in [
        "sid",
        "sky_centroid",
        "waverange",
        "sky_bbox_ll",
        "sky_bbox_lr",
        "sky_bbox_ur",
        "sky_bbox_ul",
        "xcentroid",
        "ycentroid",
        "is_extended",
        "isophotal_abmag",
    ]:
        assert hasattr(model, att)
        assert getattr(model, att) is None
