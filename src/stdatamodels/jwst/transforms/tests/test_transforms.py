# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Test jwst.transforms
"""

import asdf
import numpy as np
import pytest
from astropy.modeling.models import Identity, Mapping, Polynomial1D, Polynomial2D
from numpy.testing import assert_allclose

from stdatamodels.jwst.transforms import models


@pytest.mark.parametrize(
    ("beta_zero", "beta_del", "channel", "expected"),
    [
        (-1.77210143797, 0.177210143797, 1, 111),
        (-2.23774549066, 0.279718186333, 2, 209),
    ],
)
def test_miri_ab2slice(beta_zero, beta_del, channel, expected):
    model = models.MIRI_AB2Slice()
    beta = 0.0
    result = model.evaluate(beta, beta_zero, beta_del, channel)
    assert result == expected


def test_refractionindexfromprism():
    prism_angle = -16.5  # degrees
    prism_angle_rad = np.deg2rad(prism_angle)
    alpha_in = np.pi / 8  # angle of incidence in radians
    beta_in = np.pi / 8  # angle of incidence in radians
    alpha_out = np.pi / 16  # angle of refraction in radians

    # unclear why the model requires the prism angle in degrees on init
    # and also requires the prism angle in radians on evaluation
    model = models.RefractionIndexFromPrism(prism_angle)
    n = model.evaluate(alpha_in, beta_in, alpha_out, prism_angle_rad)
    assert np.isclose(n, 1.113583608571748)


def test_nirisssossmodel():
    spectral_orders = [1, 2]
    # model is unphysical but does have 2 inputs and 3 outputs like NIRISS SOSS would expect
    order_models = [Identity(2) | Mapping((0, 1, 1))] * len(spectral_orders)

    sossmodel = models.NirissSOSSModel(spectral_orders, order_models)
    assert sossmodel.spectral_orders == spectral_orders
    assert isinstance(sossmodel.models, dict)

    xout, yout, yout2 = sossmodel.evaluate(10, 20, np.array([1]))
    assert xout == 10
    assert yout == 20
    assert yout2 == 20

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


def test_ideal_to_v23_roundtrip():
    """
    Test roundtripping of the transforms.
    """
    v2i = models.V2V3ToIdeal(0.4, 450, 730, 1)
    x, y = 450, 730
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
    np.testing.assert_allclose(beta_out, -beta_in)

    wavelength_transform = models.WavelengthFromGratingEquation(groovedensity, order)
    lam_out = wavelength_transform.evaluate(alpha_in, beta_in, alpha_out, groovedensity, order)
    np.testing.assert_allclose(lam_out, lam)


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
    np.testing.assert_allclose(xi, x0)
    np.testing.assert_allclose(yi, y0)
    np.testing.assert_allclose(wli, wl)
    np.testing.assert_allclose(ordersi, orders)


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
    np.testing.assert_allclose(xi, x0)
    np.testing.assert_allclose(yi, y0)
    np.testing.assert_allclose(wli, wl, rtol=1e-4)
    np.testing.assert_allclose(ordersi, orders)


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
    np.testing.assert_allclose(xi, 150)
    np.testing.assert_allclose(yi, 140)
    np.testing.assert_allclose(wli, 2.0)
    np.testing.assert_allclose(ordersi, orders)


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
    np.testing.assert_allclose(xi, x0)
    np.testing.assert_allclose(yi, y0)
    np.testing.assert_allclose(wli, wl, rtol=1e-4)
    np.testing.assert_allclose(ordersi, orders)


@pytest.mark.parametrize("direction", ["row", "column"])
@pytest.mark.parametrize("instrument", ["nircam", "niriss"])
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

    orders = np.array([1, 2])
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


def test_v23tosky():
    """
    Test V2V3ToSky transform model.

    This is currently unused by JWST - skip adding tests for now, as it may get removed.
    """
    pass


def test_dircos2unitless_roundtrip():
    """
    Test DirCos2Unitless transform model.
    """
    tr = models.Unitless2DirCos()
    x, y = np.sqrt(2) / 2, np.sqrt(2) / 2
    assert_allclose(tr.inverse(*tr(x, y)), (x, y))
