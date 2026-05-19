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


def test_simple_model_to_fits_not_implemented():
    """
    Test that _SimpleModel subclasses raise NotImplementedError on to_fits(),
    not TypeError (which was the bug before the *args, **kwargs signature fix).
    See https://github.com/spacetelescope/stdatamodels/pull/744
    """
    import tempfile
    import os
    import warnings
    from stdatamodels.jwst.datamodels import DistortionModel

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with DistortionModel(distort_type="test", pupil="TEST", strict_validation=False) as m:
            m.meta.description = "test"
            m.meta.reftype = "distortion"
            m.meta.author = "test"
            m.meta.pedigree = "GROUND"
            m.meta.useafter = "2015-10-01"
            m.meta.instrument.name = "NIRCAM"
            m.validate()

            with tempfile.NamedTemporaryFile(suffix=".fits", delete=False) as f:
                tmp = f.name

            try:
                with pytest.raises(NotImplementedError, match="FITS format is not supported"):
                    m.save(tmp)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
