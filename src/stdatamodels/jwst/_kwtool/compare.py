import re

import stdatamodels.jwst.datamodels as dm
from stdatamodels.schema import walk_schema

from . import dmd, kwd

# Initialize the standard in regex pattern
_fits_standard_regex = re.compile(
    "|".join(
        f"(^{x}$)"
        for x in [
            "",
            "NAXIS[0-9]{0,3}",
            "BITPIX",
            "XTENSION",
            "PCOUNT",
            "GCOUNT",
            "EXTEND",
            "BSCALE",
            "BUNIT",
            "BZERO",
            "BLANK",
            "DATAMAX",
            "DATAMIN",
            "EXTNAME",
            "EXTVER",
            "EXTLEVEL",
            "GROUPS",
            "PTYPE[0-9]",
            "PSCAL[0-9]",
            "PZERO[0-9]",
            "SIMPLE",
            "TFIELDS",
            "TBCOL[0-9]{1,3}",
            "TFORM[0-9]{1,3}",
            "TTYPE[0-9]{1,3}",
            "TUNIT[0-9]{1,3}",
            "TSCAL[0-9]{1,3}",
            "TZERO[0-9]{1,3}",
            "TNULL[0-9]{1,3}",
            "TDISP[0-9]{1,3}",
            "HISTORY",
        ]
    )
)

_MISSING_VALUE = "MISSING_VALUE"

_DEFAULT_SKIP_MODELS = {
    dm.ReferenceFileModel,  # ignore reference file models
}

# There are some expected differences. One example is an old enum
# value might be supported in the schemas but not in the keyword dictionary
# since new files should only get new enum values.
# These differences are represented in a dict of:
#   key: (HDU, KEYWORD)
#   value: dict of
#     key: difference type (enum, title, path, etc)
#     value: dict of
#       key: name of collection to modify (dmd or kwd)
#       value: dict of
#         key: set operation (difference, union, etc)
#         value: set to pass to the operation
_DEFAULT_EXPECTED_DIFFS = {
    ("PRIMARY", "ENGQLPTG"): {
        "enum": {
            "dmd": {
                "difference": {"CALCULATED_FULL", "CALCULATED_FULLVA"},
            },
        },
    },
    ("PRIMARY", "PATTTYPE"): {
        "enum": {
            "dmd": {
                "difference": {"SUBARRAY-DITHER", "N/A", "FULL-TIGHT", "ANY"},
            },
        },
    },
    ("PRIMARY", "CATEGORY"): {
        "enum": {
            "dmd": {
                "union": {"AR", "CAL", "COM", "DD", "ENG", "GO", "GTO", "NASA", "SURVEY"},
                "difference": {_MISSING_VALUE},
            },
        },
    },
    ("PRIMARY", "FOCUSPOS"): {
        "type": {
            "dmd": {
                "union": {"integer"},
            },
        },
    },
    ("PRIMARY", "MRSPRCHN"): {
        "enum": {
            "dmd": {
                "difference": {"ALL"},
            },
        },
    },
}


def _is_standard(keyword):
    return _fits_standard_regex.match(keyword) is not None


def _filter_non_standard(keyword_dictionary):
    # Remove keywords that are already defined by the FITS standard.
    return {k: v for k, v in keyword_dictionary.items() if not _is_standard(k[1])}


def _filter_non_pattern(d):
    # Remove all P_XXX keywords. These are used in reference
    # files to aid in generating rmaps for CRDS and are not needed
    # in the keyword dictionary.
    return {k: v for k, v in d.items() if not k[1].startswith("P_")}


def _compare_path(k, d):
    paths = {}
    for c, n in [(k, "kwd"), (d, "dmd")]:
        paths[n] = {".".join(i["path"]) for i in c}
    if paths["kwd"] == paths["dmd"]:
        return None

    # Ignore paths that are nested under "items" in the
    # datamodel schemas as these can't be matched to specific
    # keywords
    for i in d:
        if "items" in i["path"]:
            return None

    # Paths differences are only a problem for the keywords
    # that have an archive destination
    for i in k:
        if i["keyword"].get("destination"):
            # since there is a destination, report the difference
            return paths
    return None


def _compare_keyword_subitem(k, d, key):
    # This can pass if both are missing since the final set comparison will
    # be {_MISSING_VALUE} == {_MISSING_VALUE}.
    items = {}
    for c, n in [(k, "kwd"), (d, "dmd")]:
        items[n] = {i["keyword"].get(key, _MISSING_VALUE) for i in c}
    if items["kwd"] == items["dmd"]:
        return None
    return items


def _compare_type(k, d):
    # "type" in the keyword dictionary has different possible
    # values that don't match standard jsonschema types so
    # map them here.
    _k_to_d_map = {
        "float": "number",
        "integer": "integer",
        "string": "string",
        "boolean": "boolean",
    }
    diff = _compare_keyword_subitem(k, d, "type")
    if not diff:
        return
    k_values = diff["kwd"]
    d_values = diff["dmd"]
    mapped_k_values = set()
    for kv in k_values:
        if kv not in _k_to_d_map:
            raise ValueError(f"Unknown keyword dictionary type: {kv}")
        mapped_k_values.add(_k_to_d_map[kv])
    if mapped_k_values == d_values:
        return None
    return {"kwd": mapped_k_values, "dmd": d_values}


def _compare_enum(k, d):
    # enums in the keyword dictionary are lists of items
    k_values = set()
    for i in k:
        if "enum" in i["keyword"]:
            enum = i["keyword"]["enum"]
            if not isinstance(enum, list):
                # PRIDTPTS has an empty list as an enum, this is probably a bug
                # in the keyword dictionary
                if enum:
                    raise ValueError(f"keyword dictionary contains a non-list enum: {enum}")
            k_values.update(enum)
        else:
            # If one scope has an enum and one doesn't this will make
            # an enum that contains some values and a _MISSING_VALUE
            # it's not clear if we want that in the comparison but we
            # add one here to at least detect the comparison.
            # The same as the note below.
            k_values.add(_MISSING_VALUE)

    # enums in the datamodel schema can:
    # - nested under a schema combiner
    # - enums are lists or regexes
    d_values = set()
    for i in d:
        keyword_definition = i["keyword"]

        # an "enum" might be nested in this subschema so let's walk the schema
        def _get_enums(ss, path, combiner, ctx, r):
            if isinstance(ss, dict) and "enum" in ss:
                enum = ss["enum"]
                if not isinstance(enum, list):
                    raise ValueError(f"datamodel contains a non-list enum: {enum}")
                ctx.update(enum)

        enum_values = set()
        walk_schema(keyword_definition, _get_enums, enum_values)
        if enum_values:
            d_values.update(enum_values)
        else:
            # See note about MISSING_VALUE above
            d_values.add(_MISSING_VALUE)

    # If this is a bool the keyword dictionary may
    # define T/F (this is inconsistent).
    # This is not needed for the datamodel schemas so
    # if only _MISSING_VALUE was found, overwrite it to {T, F}
    for i in k:
        if i["keyword"].get("type") == "boolean":
            if d_values == {_MISSING_VALUE}:
                d_values = set()
            d_values |= {"T", "F"}
            if k_values == {_MISSING_VALUE}:
                k_values = set()
            k_values |= {"T", "F"}

    if k_values == d_values:
        return None
    return {"kwd": k_values, "dmd": d_values}


def _compare_fits_hdu(k, d):
    # the fits hdu where the keyword is located
    diff = _compare_keyword_subitem(k, d, "fits_hdu")
    if not diff:
        return
    k_value = diff["kwd"]
    d_value = diff["dmd"]
    if k_value == d_value:
        return None
    return {"kwd": k_value, "dmd": d_value}


def _compare_definitions(k, d):
    # compare the keyword definitions in the keyword dictionary (k)
    # and datamodels (d)
    # each is a list of definitions since each high level structure
    # has organization that will lead to many definitions for a single keyword
    # The things to compare are:
    # - paths: these should match
    # - title: these should match
    # - enum: these should match (after combination, might not exist)
    diff = {}
    if subdiff := _compare_path(k, d):
        diff["path"] = subdiff
    for key in ("title",):
        if subdiff := _compare_keyword_subitem(k, d, key):
            diff[key] = subdiff
    if subdiff := _compare_type(k, d):
        diff["type"] = subdiff
    if subdiff := _compare_enum(k, d):
        diff["enum"] = subdiff
    return diff


def _is_expected(kw, diff, expected_diffs):
    if kw not in expected_diffs:
        return False
    expected = expected_diffs[kw]
    for expected_key, sub_expected in expected.items():
        if expected_key == "notes":
            continue
        if expected_key not in diff:
            continue
        sub_diff = diff[expected_key]
        for collection_key in ("dmd", "kwd"):
            if collection_key not in sub_expected:
                continue
            try:
                for op, other_set in sub_expected[collection_key].items():
                    sub_diff[collection_key] = getattr(sub_diff[collection_key], op)(other_set)
            except AttributeError:
                sub_diff[collection_key] = sub_expected[collection_key]
        if sub_diff["dmd"] == sub_diff["kwd"]:
            del diff[expected_key]
    # if we have no differences left then all was expected
    if not diff:
        return True
    return False


def _clean_set(the_set, keys_to_remove):
    for k in keys_to_remove:
        the_set.discard(k)
    return the_set


def _pretty_print_it(d, indent=1):
    res = ""
    for k, v in d.items():
        res += "\t" * indent + repr(k)
        if isinstance(v, dict):
            res += ": { \n"
            res += _pretty_print_it(v, indent + 1)
            res += "\t" * (indent + 1) + "}, \n"
        elif isinstance(v, list):
            res += ": [ \n"
            for list_item in v:
                res += "\t" * (indent + 2) + repr(list_item) + ", \n"
            res += "\t" * (indent + 1) + "], \n"
        else:
            res += ": \n"
            res += "\t" * (indent + 1) + repr(v) + ", \n"
    return res


def print_dict_to_file(dict_name, the_dict, the_file):
    with open(the_file, "w") as f:
        f.write(dict_name + " = { \n")
        f.write(_pretty_print_it(the_dict))
        f.write("} \n")


def _mk_txt_table(dict_name, the_dict):
    file_name = dict_name + "_table.txt"
    okified, notes = "No", ""
    with open(file_name, "w") as f:
        line = "{:<12} {:<25} {:<60} {:<8} {:<30}".format(
            "Keyword", "HDU", "Title", "Okified", "Notes"
        )
        f.write(line + "\n")
        # print the dashed lines under the headers
        lengths = [12, 25, 60, 8, 30]
        dashed_lines = []
        for l in lengths:
            dl = "-"
            for _ in range(l - 2):
                dl += "-"
            dashed_lines.append(dl)
        line = (
            f"{dashed_lines[0]:<12} {dashed_lines[1]:<25} {dashed_lines[2]:<60} "
            f"{dashed_lines[3]:<8} {dashed_lines[4]:<30}"
        )
        f.write(line + "\n")
        for tpl, item in the_dict.items():
            fits_hdu, keyword = tpl
            title = None
            for d in item:
                for k, v in d.items():
                    if k == "keyword":
                        if "title" in v:
                            title = v["title"]
                            line = f"{keyword:<12} {fits_hdu:<25} {title:<60} {okified:<5} {notes:<100}"
                            f.write(line + "\n")
                            break
                    # only print the keyword once
                    if title:
                        break


def _print_final_keywords(dict_name, in_kord, the_dict):
    final_keywords = {}
    for tpl in in_kord:
        final_keywords[tpl] = the_dict[tpl]
    if final_keywords:
        file_name = dict_name + ".py"
        print_dict_to_file(dict_name, final_keywords, file_name)
        _mk_txt_table(dict_name, final_keywords)


def compare_keywords(kwd_path, skip_models=None, expected_diffs=None):
    if skip_models is None:
        skip_models = _DEFAULT_SKIP_MODELS
    if expected_diffs is None:
        expected_diffs = _DEFAULT_EXPECTED_DIFFS
    # the keyword dictionary contains standard FITS keywords
    # remove them as they're mostly not defined in the datamodel schemas
    datamodel_keywords = _filter_non_pattern(_filter_non_standard(dmd.load(skip_models)))
    kwd_keywords = _filter_non_standard(kwd.load(kwd_path))

    # get keys to compare
    kwd_keys = set(kwd_keywords.keys())
    datamodel_keys = set(datamodel_keywords.keys())

    # compare keys
    in_kwd = kwd_keys - datamodel_keys
    in_datamodels = datamodel_keys - kwd_keys

    # find keywords that are in both and check if they match
    in_both = kwd_keys & datamodel_keys

    definitions_diff = {}
    for kw in in_both:
        k = kwd_keywords[kw]
        d = datamodel_keywords[kw]

        # compare keyword definitions
        if diff := _compare_definitions(k, d):
            # only report unexpected differences
            if not _is_expected(kw, diff, expected_diffs):
                definitions_diff[kw] = diff

    # double check that the keyword is indeed missing
    # look up keyword dictionary keys in datamodels
    to_remove_in_kwd = []
    for tplk in in_kwd:
        for tpld in datamodel_keys:
            if tplk[1] == tpld[1]:
                to_remove_in_kwd.append(tplk)
                if tplk not in in_both:
                    in_both.add(tplk)
                    definitions_diff[tplk] = _compare_fits_hdu(
                        kwd_keywords[tplk], datamodel_keywords[tpld]
                    )
    _clean_set(in_kwd, to_remove_in_kwd)
    _print_final_keywords("final_kwd_keywords", in_kwd, kwd_keywords)
    # look up datamodels keys in keyword dictionary
    to_remove_in_dmd = []
    for tpld in in_datamodels:
        for tplk in kwd_keys:
            if tplk[1] == tpld[1]:
                to_remove_in_dmd.append(tpld)
                # but don't add it twice
                if tplk not in definitions_diff:
                    if tplk not in in_both:
                        in_both.add(tplk)
                        definitions_diff[tplk] = _compare_fits_hdu(
                            kwd_keywords[tplk], datamodel_keywords[tpld]
                        )
    _clean_set(in_datamodels, to_remove_in_dmd)
    _print_final_keywords("final_datamodel_keywords", in_datamodels, datamodel_keywords)

    return in_kwd, in_datamodels, in_both, definitions_diff, kwd_keywords, datamodel_keywords
