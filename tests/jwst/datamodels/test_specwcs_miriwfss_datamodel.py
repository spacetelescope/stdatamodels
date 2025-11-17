import pytest
from astropy import units as u
from astropy.modeling.models import Polynomial1D, Polynomial2D

from stdatamodels.jwst import datamodels
from stdatamodels.validate import ValidationWarning


def test_miri_wfss_specwcs():
    """Test the MIRI WFSS specwcs data is of the correct form."""
    dispx = []
    dispy = []
    displ = []
    invdispl = []

    l0 = 3.125
    l1 = 10.893
    displ.append(Polynomial1D(1, c0=l0, c1=l1))

    ind0 = -0.28688148
    ind1 = 0.09180207
    invdispl.append(Polynomial1D(1, c0=ind0, c1=ind1))

    y0 = 8.850746809616503
    y1 = 0.00000003
    y2 = 0.0
    y3 = 0.00000018
    y4 = 0.0
    y5 = 0.0
    cpoly_0 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)

    y0 = 281.47469555
    y1 = 0.00000005
    y2 = 0.0
    y3 = 0.00000036
    y4 = 0.0
    y5 = 0.0
    cpoly_1 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)

    y0 = 68.54314495
    y1 = 0.00000002
    y2 = 0.0
    y3 = 0.00000017
    y4 = 0.0
    y5 = 0.0

    cpoly_2 = Polynomial2D(2, c0_0=y0, c1_0=y1, c2_0=y2, c0_1=y3, c1_1=y4, c0_2=y5)
    dispy.append((cpoly_0, cpoly_1, cpoly_2))
    dispx.append((cpoly_0, cpoly_1, cpoly_2))

    model = datamodels.MiriWFSSSpecwcsModel(
        dispx=dispx, dispy=dispy, displ=displ, invdispl=invdispl
    )
    model.meta.description = "MIRI WFSS SPECWCS reference file"
    model.meta.author = "Jane Morrison"
    model.meta.pedigree = "FLIGHT"
    model.meta.useafter = "2022-05-01T00:00:00"

    assert model.meta.instrument.name == "MIRI"
    assert model.meta.instrument.detector == "MIRIMAGE"
    assert model.meta.reftype == "specwcs"

    # no orders is defined and it is required.
    with pytest.warns(ValidationWarning):
        model.validate()

    # now add order
    orders = [1]
    model = datamodels.MiriWFSSSpecwcsModel(
        dispx=dispx, dispy=dispy, displ=displ, invdispl=invdispl, orders=orders
    )
    model.meta.description = "MIRI WFSS SPECWCS reference file"
    model.meta.author = "Jane Morrison"
    model.meta.pedigree = "FLIGHT"
    model.meta.useafter = "2022-05-01T00:00:00"
    model.meta.input_units = u.micron
    model.meta.output_units = u.micron
    model.validate()

    assert model.dispx == dispx
    assert model.dispy == dispy
    assert model.displ == displ
    assert model.invdispl == invdispl
    assert model.meta.exposure.type == "MIR_WFSS"
