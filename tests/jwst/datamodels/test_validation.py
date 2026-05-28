import contextlib
from datetime import datetime

import numpy as np
import pytest
from asdf.exceptions import ValidationError
from astropy import time
from gwcs.examples import gwcs_2d_shift_scale

from stdatamodels.exceptions import ValidationWarning
from stdatamodels.jwst.datamodels import JwstDataModel


def test_strict_validation_enum():
    with JwstDataModel(strict_validation=True) as dm:
        assert dm.meta.instrument.name is None
        with pytest.raises(ValidationError):
            # FOO is not in the allowed enumerated values
            dm.meta.instrument.name = "FOO"


def test_strict_validation_type():
    with JwstDataModel(strict_validation=True) as dm:
        with pytest.raises(ValidationError):
            # Schema requires a float
            dm.meta.target.ra = "FOO"


def test_strict_validation_date():
    with JwstDataModel(strict_validation=True) as dm:
        time_obj = time.Time(dm.meta.date)
        assert isinstance(time_obj, time.Time)
        date_obj = datetime.strptime(dm.meta.date, "%Y-%m-%dT%H:%M:%S.%f")
        assert isinstance(date_obj, datetime)


@pytest.mark.parametrize(
    "value, error",
    [
        [None, False],
        [1, True],
        [np.array([1, 2, 3]), True],
        [gwcs_2d_shift_scale(), False],
    ],
)
@pytest.mark.parametrize("strict", [True, False])
def test_wcs_validation_on_assignment(value, error, strict):
    if error:
        if strict:
            ctx = pytest.raises(ValidationError)
        else:
            ctx = pytest.warns(ValidationWarning)
    else:
        ctx = contextlib.nullcontext()
    with JwstDataModel(strict_validation=strict) as dm:
        with ctx:
            dm.meta.wcs = value
        if error:
            assert dm.meta.wcs is None
            dm.meta.instance["wcs"] = value
        else:
            assert dm.meta.wcs is value


@pytest.mark.parametrize(
    "value, error",
    [
        [None, False],
        [1, True],
        [np.array([1, 2, 3]), True],
        [gwcs_2d_shift_scale(), False],
    ],
)
@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("ext", ["fits", "asdf"])
def test_wcs_validation_on_save(tmp_path, ext, value, error, strict):
    fn = tmp_path / f"test.{ext}"
    if error:
        ctx = pytest.raises(ValidationError)
        if ext == "asdf":
            pytest.xfail(
                "saving to asdf does not correctly trigger wcs (or other custom) validation"
            )
    else:
        ctx = contextlib.nullcontext()
    with JwstDataModel(strict_validation=strict) as dm:
        dm.meta.instance["wcs"] = value
        with ctx:
            dm.save(fn)
