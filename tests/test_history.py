import datetime

import asdf
import numpy as np
import pytest
from asdf.tags.core import HistoryEntry
from astropy.io import fits
from astropy.time import Time

from stdatamodels import DataModel


@pytest.mark.filterwarnings("ignore:The history attribute is deprecated:DeprecationWarning")
def test_historylist_methods():
    m = DataModel()
    h1 = m.history

    info = "First entry"
    h1.append(info)
    assert h1 == info, "Append new history entry"

    h2 = m.history
    assert h2 == info, "Two history lists point to the same object"

    assert len(h1) == 1, "Length of a history list"

    entry = h1[0]
    assert entry["description"] == info, "Get history list item"

    info += " for real"
    h1[0] = info
    assert h1 == info, "Set history list item"

    del h1[0]
    assert len(h1) == 0, "Delete history list item"

    info = ("First entry", "Second_entry", "Third entry")
    h1.extend(info)
    assert len(h1) == 3, "Length of extended history list"
    assert h1 == info, "Contents of extended history list"

    for entry, item in zip(h1, info, strict=False):
        assert entry["description"] == item, "Iterate over history list"

    h1.clear()
    assert len(h1) == 0, "Clear history list"


@pytest.mark.filterwarnings("ignore:The history attribute is deprecated:DeprecationWarning")
def test_history_from_model_to_fits(tmp_path):
    tmpfits = str(tmp_path / "tmp.fits")
    m = DataModel()
    m.history = [
        HistoryEntry(
            {"description": "First entry", "time": Time(datetime.datetime.now().isoformat())}
        )
    ]
    m.history.append(
        HistoryEntry(
            {"description": "Second entry", "time": Time(datetime.datetime.now().isoformat())}
        )
    )
    m.save(tmpfits)

    with fits.open(tmpfits, memmap=False) as hdulist:
        assert list(hdulist[0].header["HISTORY"]) == ["First entry", "Second entry"]

    tmpfits2 = str(tmp_path / "tmp2.fits")
    with DataModel(tmpfits) as m2:
        m2 = DataModel()
        m2.update(m)
        m2.history = m.history

        assert m2.history == [{"description": "First entry"}, {"description": "Second entry"}]

        m2.save(tmpfits2)

    with fits.open(tmpfits2, memmap=False) as hdulist:
        assert list(hdulist[0].header["HISTORY"]) == ["First entry", "Second entry"]


@pytest.mark.filterwarnings("ignore:The history attribute is deprecated:DeprecationWarning")
def test_history_from_fits(tmp_path):
    tmpfits = str(tmp_path / "tmp.fits")
    header = fits.Header()
    header["HISTORY"] = "First entry"
    header["HISTORY"] = "Second entry"
    fits.writeto(tmpfits, np.array([]), header, overwrite=True)

    tmpfits2 = str(tmp_path / "tmp2.fits")
    with DataModel(tmpfits) as m:
        assert m.history == [{"description": "First entry"}, {"description": "Second entry"}]

        del m.history[0]
        m.history.append(HistoryEntry({"description": "Third entry"}))
        assert m.history == [{"description": "Second entry"}, {"description": "Third entry"}]
        m.save(tmpfits2)

    with DataModel(tmpfits2) as m:
        assert m.history == [{"description": "Second entry"}, {"description": "Third entry"}]


def test_history_get_deprecation():
    m = DataModel()
    with pytest.warns(DeprecationWarning, match="The history attribute is deprecated"):
        m.history


def test_history_set_deprecation():
    m = DataModel()
    with pytest.warns(DeprecationWarning, match="The history attribute is deprecated"):
        m.history = []


@pytest.mark.parametrize("filename", ["test.asdf", "test.fits"])
def test_add_history_entry(tmp_path, filename):
    msgs = ["foo", "bar"]
    path = tmp_path / filename
    m = DataModel()
    for msg in msgs:
        m.add_history_entry(msg)
    m.save(path)

    if "asdf" in filename:
        with asdf.open(path, lazy_load=False) as af:
            written_msgs = [entry["description"] for entry in af["history"]["entries"]]
    else:
        with fits.open(path, memmap=False) as ff:
            written_msgs = [
                card.value for card in ff["PRIMARY"].header.cards if card.keyword == "HISTORY"
            ]

    assert set(msgs) == set(written_msgs)
