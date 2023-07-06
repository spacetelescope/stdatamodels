from astropy import time
from datetime import datetime
from asdf.exceptions import ValidationError
import pytest

from stdatamodels.jwst.datamodels import JwstDataModel


def test_strict_validation_enum():
    with JwstDataModel(strict_validation=True) as dm:
        assert dm.meta.instrument.name is None
        with pytest.raises(ValidationError):
            # FOO is not in the allowed enumerated values
            dm.meta.instrument.name = 'FOO'


def test_strict_validation_type():
    with JwstDataModel(strict_validation=True) as dm:
        with pytest.raises(ValidationError):
            # Schema requires a float
            dm.meta.target.ra = "FOO"


def test_strict_validation_date():
    with JwstDataModel(strict_validation=True) as dm:
        time_obj = time.Time(dm.meta.date)
        assert isinstance(time_obj, time.Time)
        date_obj = datetime.strptime(dm.meta.date, '%Y-%m-%dT%H:%M:%S.%f')
        assert isinstance(date_obj, datetime)
