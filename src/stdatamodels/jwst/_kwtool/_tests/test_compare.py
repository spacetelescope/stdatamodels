import pytest

from stdatamodels.jwst._kwtool import compare


def test_filter_standard():
    keywords = {
        ("PRIMARY", "PCOUNT"): 1,
        ("PRIMARY", "OBS_ID"): 2,
    }
    result = compare._filter_non_standard(keywords)
    assert ("PRIMARY", "OBS_ID") in result
    assert ("PRIMARY", "PCOUNT") not in result


def test_filter_non_pattern():
    keywords = {
        ("PRIMARY", "P_BAND"): 1,
        ("PRIMARY", "PBAND"): 2,
        ("PRIMARY", "BAND"): 3,
    }
    result = compare._filter_non_pattern(keywords)
    assert ("PRIMARY", "PBAND") in result
    assert ("PRIMARY", "BAND") in result
    assert ("PRIMARY", "P_BAND") not in result


def test_compare_path_no_destination():
    """
    Ignore path differences for keywords that have
    no destination.
    """
    k = [
        {
            "keyword": {
                # no destination
                "title": "foo",
            },
            "path": "a.b.c".split("."),
        }
    ]
    d = [
        {
            "path": "d.e.f".split("."),
        }
    ]
    assert compare._compare_path(k, d) is None


def test_compare_path():
    # make sure k has a destination so the difference isn't ignored
    k = [{"path": "a.b.c".split("."), "keyword": {"destination": "somewhere"}}]
    d = [{"path": "d.e.f".split(".")}]
    assert compare._compare_path(k, d) == {"kwd": {"a.b.c"}, "dmd": {"d.e.f"}}


@pytest.mark.parametrize(
    "kv, dv, expected",
    [
        ("a", "a", None),
        ("a", "z", {"kwd": {"a"}, "dmd": {"z"}}),
        ("z", "a", {"kwd": {"z"}, "dmd": {"a"}}),
        ("a", None, {"kwd": {"a"}, "dmd": {compare._MISSING_VALUE}}),
        (None, "a", {"kwd": {compare._MISSING_VALUE}, "dmd": {"a"}}),
        (None, None, None),
    ],
)
def test_compare_keyword_subitem(kv, dv, expected):
    # if kv/dv is None, don't fill title
    if kv is None:
        k = [{"keyword": {}}]
    else:
        k = [{"keyword": {"title": kv}}]
    if dv is None:
        d = [{"keyword": {}}]
    else:
        d = [{"keyword": {"title": dv}}]
    assert compare._compare_keyword_subitem(k, d, "title") == expected


@pytest.mark.parametrize(
    "ktype, dtype, expected",
    [
        ("string", "string", None),
        ("integer", "string", {"kwd": {"integer"}, "dmd": {"string"}}),
        ("string", "integer", {"kwd": {"string"}, "dmd": {"integer"}}),
        ("float", "number", None),
    ],
)
def test_compare_type(ktype, dtype, expected):
    k = [{"keyword": {"type": ktype}}]
    d = [{"keyword": {"type": dtype}}]
    assert compare._compare_type(k, d) == expected


@pytest.mark.parametrize(
    "kv, dv, expected",
    [
        (["a", "z"], ["z", "a"], None),
        (["a", "z"], ["a"], {"kwd": {"a", "z"}, "dmd": {"a"}}),
        (["a"], ["a", "z"], {"kwd": {"a"}, "dmd": {"a", "z"}}),
    ],
)
def test_compare_enum(kv, dv, expected):
    k = [{"keyword": {"enum": kv}}]
    d = [{"keyword": {"enum": dv}}]
    assert compare._compare_enum(k, d) == expected


@pytest.fixture(scope="module")
def compare_result(fake_kwd_path):
    return compare.compare_keywords(fake_kwd_path)


def test_obs_id(compare_result):
    """
    We constructed a fake keyword dictionary with OBS_IDD
    and the datamodels have OBS_ID. Check this was found.
    """
    in_k, in_d, in_both, def_diff, k_keys, d_keys = compare_result
    assert ("SCI", "OBS_IDD") in in_k
    assert ("PRIMARY", "OBS_ID") in in_d


def test_title(compare_result):
    """
    TITLE should be in both and agree
    """
    in_k, in_d, in_both, def_diff, k_keys, d_keys = compare_result
    key = ("PRIMARY", "TITLE")
    assert key in in_both
    assert key not in def_diff


def test_eng_qual(compare_result):
    """
    ENG_QUAL is in both but the enum differs.

    There are other differences (due to our test setup) but we'll
    ignore these.
    """
    in_k, in_d, in_both, def_diff, k_keys, d_keys = compare_result
    key = ("PRIMARY", "ENG_QUAL")
    assert key in in_both
    assert key in def_diff
    assert "enum" in def_diff[key]
    assert def_diff[key]["enum"] == {
        "dmd": {"OK", "SUSPECT"},
        "kwd": {"OK", "SUSPECT", "NOT_IN_DATAMODEL"},
    }
