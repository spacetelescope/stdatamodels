from datetime import datetime, timedelta

import pytest

from astropy.io import fits
import numpy as np
from numpy.testing import assert_array_equal
from asdf.tags.core import Software, HistoryEntry

from stdatamodels import util


def test_gentle_asarray_array_input():
    inp = np.array([1, 2, 3, 4], dtype=np.int16)
    result = util.gentle_asarray(inp, dtype=np.int16)
    assert result.dtype == np.int16
    assert_array_equal(result, inp)

    result = util.gentle_asarray(inp, dtype=np.int8)
    assert result.dtype == np.int8
    assert_array_equal(result, inp)

    dtype = np.dtype([("col1", np.int16), ("col2", np.float32)])
    result = util.gentle_asarray(inp, dtype=dtype)
    assert result.dtype == dtype
    assert result["col1"].dtype == np.int16
    assert_array_equal(result["col1"], np.array([1, 2, 3, 4], dtype=np.int16))
    assert result["col2"].dtype == np.float32
    assert_array_equal(result["col1"], np.array([1, 2, 3, 4], dtype=np.float32))


def test_gentle_asarray_recarray_input():
    dtype = np.dtype([("col1", np.int16), ("col2", np.float32)])
    inp = np.array([1, 2, 3, 4], dtype=dtype)
    result = util.gentle_asarray(inp, dtype=dtype)
    assert result.dtype == dtype
    assert_array_equal(result, inp)


def test_gentle_asarray_fits_rec_input():
    cols = [fits.Column("col1", format="e", array=np.array([1, 2, 3, 4]))]
    inp = fits.FITS_rec.from_columns(cols)
    out_dtype = np.dtype([("col1", np.float32)])
    result = util.gentle_asarray(inp, dtype=out_dtype)
    assert result.dtype == out_dtype
    assert_array_equal(result, inp)


def test_gentle_asarray_fits_rec_pseudo_unsigned():
    cols = [fits.Column("col1", format="j", array=np.array([1, 2, 3, 4], np.uint32), bzero=2147483648)]
    inp = fits.FITS_rec.from_columns(cols)
    out_dtype = np.dtype([("col1", np.uint32)])
    result = util.gentle_asarray(inp, dtype=out_dtype)
    assert result["col1"].dtype == np.uint32


def test_gentle_asarray_nested_array():
    in_dtype = np.dtype([("col1", np.dtype("2f")), ("col2", np.int16)])
    inp = np.array([1, 2, 3, 4], dtype=in_dtype)
    out_dtype = np.dtype([("col1", np.dtype("2f")), ("col2", np.int8)])
    result = util.gentle_asarray(inp, dtype=out_dtype)
    assert result.dtype == out_dtype
    assert_array_equal(result["col2"], inp["col2"])


def test_gentle_asarray_mismatched_column_names():
    in_dtype = np.dtype([("col1", np.int16), ("col2", np.float32)])
    inp = np.array([1, 2, 3, 4], dtype=in_dtype)
    out_dtype = np.dtype([("col1", np.int16), ("foo", np.float32)])
    with pytest.raises(ValueError):
        util.gentle_asarray(inp, dtype=out_dtype)


def test_gentle_asarray_column_name_case():
    in_dtype = np.dtype([("col1", np.int16), ("col2", np.float32)])
    inp = np.array([1, 2, 3, 4], dtype=in_dtype)
    out_dtype = np.dtype([("COL1", np.int16), ("COL2", np.float32)])
    result = util.gentle_asarray(inp, dtype=out_dtype)
    assert result.dtype == out_dtype
    assert_array_equal(result, inp)


def test_gentle_asarray_scalar_input():
    result = util.gentle_asarray(3.14159, dtype=np.float32)
    assert result.dtype == np.float32
    assert_array_equal(result, np.array([3.14159], dtype=np.float32))


def test_gentle_asarray_invalid_conversion():
    with pytest.raises(ValueError):
        util.gentle_asarray(object(), dtype=np.float32)


def test_get_short_doc():
    assert util.get_short_doc({}) == ""
    assert util.get_short_doc({"title": "Some schema title."}) == "Some schema title."
    assert util.get_short_doc({
        "title": "Some schema title.\nWhoops, another line."
    }) == "Some schema title."
    assert util.get_short_doc({
        "title": "Some schema title.",
        "description": "Some schema description.",
    }) == "Some schema title."
    assert util.get_short_doc({
        "description": "Some schema description.",
    }) == "Some schema description."
    assert util.get_short_doc({
        "description": "Some schema description.\nWhoops, another line.",
    }) == "Some schema description."


def test_ensure_ascii():
    for inp in [b"ABCDEFG", "ABCDEFG"]:
        util.ensure_ascii(inp) == "ABCDEFG"


def test_create_history_entry():
    entry = util.create_history_entry("Once upon a time...")
    assert isinstance(entry, HistoryEntry)
    assert entry["description"] == "Once upon a time..."
    assert entry.get("software") is None
    assert (datetime.utcnow() - entry["time"]) < timedelta(seconds=10)

    software = {"name": "PolarBearSoft", "version": "1.2.3"}
    entry = util.create_history_entry("There was a tie-dyed polar bear...", software)
    assert isinstance(entry["software"], Software)
    assert entry["software"]["name"] == "PolarBearSoft"
    assert entry["software"]["version"] == "1.2.3"

    software = [
        {"name": "PolarBearSoft", "version": "1.2.3"},
        {"name": "BanjoSoft", "version": "4.5.6"},
    ]
    entry = util.create_history_entry("Who loved to strum the banjo.", software)
    assert isinstance(entry["software"], list)
    assert all(isinstance(s, Software) for s in entry["software"])
    assert entry["software"][0]["name"] == "PolarBearSoft"
    assert entry["software"][0]["version"] == "1.2.3"
    assert entry["software"][1]["name"] == "BanjoSoft"
    assert entry["software"][1]["version"] == "4.5.6"


@pytest.mark.parametrize(
    "value,expected_result",
    [
        ("0", False),
        ("false", False),
        ("FALSE", False),
        ("f", False),
        ("no", False),
        ("n", False),
        ("1", True),
        ("-1", True),
        ("198815238", True),
        ("true", True),
        ("TRUE", True),
        ("t", True),
        ("yes", True),
        ("y", True),
    ]
)
def test_get_envar_as_boolean(monkeypatch, value, expected_result):
    monkeypatch.setenv("TEST_VAR", value)
    assert util.get_envar_as_boolean("TEST_VAR") is expected_result

    truths = ('true', 't', 'yes', 'y')
    falses = ('false', 'f', 'no', 'n')


def test_get_envar_as_boolean_default(monkeypatch):
    monkeypatch.delenv("TEST_VAR", raising=False)
    assert util.get_envar_as_boolean("TEST_VAR") is False
    assert util.get_envar_as_boolean("TEST_VAR", default=False) is False
    assert util.get_envar_as_boolean("TEST_VAR", default=True) is True


def test_get_envar_as_boolean_invalid(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "foo")
    with pytest.raises(ValueError):
        assert util.get_envar_as_boolean("TEST_VAR")