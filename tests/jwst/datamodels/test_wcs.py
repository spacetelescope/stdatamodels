import pytest

from stdatamodels.jwst.datamodels import FilteroffsetModel


def test_wcs_ref_models():
    filters = [
        {"name": "F090W", "row_offset": 1, "column_offset": 1},
        {"name": "F070W", "row_offset": 2, "column_offset": 2},
    ]
    with FilteroffsetModel(filters=filters, instrument="NIRCAM", strict_validation=True) as fo:
        assert fo.filters == filters
        with pytest.raises(
            ValueError,
            match="Model.meta is missing values for['description', "
            "'reftype', 'author', 'pedigree','useafter']",
        ):
            fo.validate()

    filters = [
        {"filter": "F090W", "pupil": "GRISMR", "row_offset": 1, "column_offset": 1},
        {"filter": "F070W", "pupil": "GRISMC", "row_offset": 2, "column_offset": 2},
    ]
    with FilteroffsetModel(filters=filters, instrument="NIRCAM", strict_validation=True) as fo:
        assert fo.filters == filters
        fo.meta.description = "Filter offsets"
        fo.meta.reftype = "filteroffset"
        fo.meta.author = "Unknown"
        fo.meta.pedigree = "GROUND"
        fo.meta.useafter = "2019-12-01"

        with pytest.raises(
            ValueError, match="Expected meta.instrument.channel for instrument NIRCAM to be one of "
        ):
            fo.validate()
        fo.meta.instrument.channel = "SHORT"
        fo.meta.instrument.module = "A"
        fo.validate()
