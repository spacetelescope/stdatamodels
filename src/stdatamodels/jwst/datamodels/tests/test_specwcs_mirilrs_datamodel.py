import numpy as np
from stdatamodels.jwst import datamodels


def test_miri_lrs_specwcs():
    """Test the MIRI LRS specwcs data is loaded correctly."""
    xc = np.array([1.0, 2.0, 3.0])
    yc = np.array([4.0, 5.0, 6.0])
    wave = np.array([12.4, 13.4, 14.5])
    x0 = np.array([1.0, 2.0, 3.0])
    x1 = np.array([1, 2, 3])
    x2 = np.array([1, 2, 3])
    x3 = np.array([1, 2, 3])
    y0 = np.array([1, 2, 3])
    y1 = np.array([1, 2, 3])
    y2 = np.array([1, 2, 3])
    y3 = np.array([1, 2, 3])

    d = np.dtype(
        [
            ("x_center", np.float32),
            ("y_center", np.float32),
            ("wavelength", np.float32),
            ("x0", np.float32),
            ("y0", np.float32),
            ("x1", np.float32),
            ("y1", np.float32),
            ("x2", np.float32),
            ("y2", np.float32),
            ("x3", np.float32),
            ("y3", np.float32),
        ]
    )
    wavetable = np.array(
        [
            (xc[0], yc[0], wave[0], x0[0], y0[0], x1[0], y1[0], x2[0], y2[0], x3[0], y3[0]),
            (xc[1], yc[1], wave[1], x0[1], y0[1], x1[1], y1[1], x2[1], y2[1], x3[1], y3[1]),
            (xc[2], yc[2], wave[2], x0[2], y0[2], x1[2], y1[2], x2[2], y2[2], x3[2], y3[2]),
        ],
        dtype=d,
    )

    model = datamodels.MiriLRSSpecwcsModel(x_ref=430, y_ref=400, wavetable=wavetable)
    model.meta.description = "MIRI LRS SPECWCS reference file"
    model.meta.author = "Jane Morrison"
    model.meta.pedigree = "FLIGHT"
    model.meta.useafter = "2022-05-01T00:00:00"
    assert model.meta.instrument.name == "MIRI"
    assert model.meta.instrument.detector == "MIRIMAGE"
    assert model.meta.reftype == "specwcs"
    assert model.meta.x_ref == 430
    assert model.meta.y_ref == 400

    # for slitless case assert the v2/v3 vertices are None if not in the file
    assert model.meta.v2_vert1 is None
    assert model.meta.v2_vert2 is None
    assert model.meta.v2_vert3 is None
    assert model.meta.v2_vert4 is None

    assert model.meta.v3_vert1 is None
    assert model.meta.v3_vert2 is None
    assert model.meta.v3_vert3 is None
    assert model.meta.v3_vert4 is None
    model.validate()
