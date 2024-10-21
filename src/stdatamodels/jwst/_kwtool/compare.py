import re

from stdatamodels.schema import walk_schema

from . import dmd
from . import kwd


# Initialize the standard in regex pattern
_fits_standard_regex = re.compile('|'.join('(^{0}$)'.format(x) for x in [
    '', 'NAXIS[0-9]{0,3}', 'BITPIX', 'XTENSION', 'PCOUNT', 'GCOUNT',
    'EXTEND', 'BSCALE', 'BUNIT', 'BZERO', 'BLANK', 'DATAMAX', 'DATAMIN',
    'EXTNAME', 'EXTVER', 'EXTLEVEL', 'GROUPS', 'PTYPE[0-9]',
    'PSCAL[0-9]', 'PZERO[0-9]', 'SIMPLE', 'TFIELDS',
    'TBCOL[0-9]{1,3}', 'TFORM[0-9]{1,3}', 'TTYPE[0-9]{1,3}',
    'TUNIT[0-9]{1,3}', 'TSCAL[0-9]{1,3}', 'TZERO[0-9]{1,3}',
    'TNULL[0-9]{1,3}', 'TDISP[0-9]{1,3}', 'HISTORY'
]))


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
    for c, n in [(k, 'kwd'), (d, 'dmd')]:
        paths[n] = set(('.'.join(i['path']) for i in c))
    if paths['kwd'] == paths['dmd']:
        return None
    # the paths differ this is only a problem for keywords
    # that have an archive destination TODO document this
    for i in k:
        if i['keyword'].get('destination'):
            # since there is a destination, report the differenc
            return paths
    return None


class _MissingValue:
    def __repr__(self):
        return "MISSING VALUE"


_MISSING_VALUE = _MissingValue()


def _compare_keyword_subitem(k, d, key):
    # This can pass if both are missing since the final set comparison will
    # be {_MISSING_VALUE} == {_MISSING_VALUE}.
    items = {}
    for c, n in [(k, 'kwd'), (d, 'dmd')]:
        items[n] = set((i['keyword'].get(key, _MISSING_VALUE) for i in c))
    if items['kwd'] == items['dmd']:
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
    k_values = diff['kwd']
    d_values = diff['dmd']
    mapped_k_values = set()
    for kv in k_values:
        if kv not in _k_to_d_map:
            raise ValueError(f"Unknown keyword dictionary type: {kv}")
        mapped_k_values.add(_k_to_d_map[kv])
    if mapped_k_values == d_values:
        return None
    return {'kwd': mapped_k_values, 'dmd': d_values}


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
            # TODO I'm not sure _MISSING_VALUE makes sense here
            # if one scope has an enum and one doesn't this will make
            # an enum that contains some values and a _MISSING_VALUE
            # it's not clear if we want that in the comparison
            k_values.add(_MISSING_VALUE)

    # enums in the datamodel schema can:
    # - nested under a schema combiner
    # - enums are lists or regexes
    d_values = set()
    for i in d:
        keyword_definition = i["keyword"]

        # an "enum" might be nested in this subschema so let's walk the schema
        def _get_enums(ss, path, combiner, ctx, r):
            if isinstance(ss, dict) and 'enum' in ss:
                enum = ss["enum"]
                if not isinstance(enum, list):
                    raise ValueError(f"datamodel contains a non-list enum: {enum}")
                ctx.update(enum)

        enum_values = set()
        walk_schema(keyword_definition, _get_enums, enum_values)
        if enum_values:
            d_values.update(enum_values)
        else:
            # TODO same as above
            d_values.add(_MISSING_VALUE)

    if k_values == d_values:
        return None
    return {'kwd': k_values, 'dmd': d_values}


def _compare_definitions(k, d):
    # compare the keyword definitions in the keyword dictionary (k)
    # and dataodels (d)
    # each is a list of definitions since each high level structure
    # has orgnization that will lead to many definitions for a single keyword
    # The things to compare are:
    # - paths: these should match
    # - title: these should match (TODO required? might not exist)
    # - description: these should match (TODO required? might not exist)
    # - enum: these should match (after combination, might not exist)
    diff = {}
    if subdiff := _compare_path(k, d):
        diff['path'] = subdiff
    #for key in ('title', 'description'):
    for key in ('title', ):
        if subdiff := _compare_keyword_subitem(k, d, key):
            diff[key] = subdiff
    if subdiff := _compare_type(k, d):
        diff['type'] = subdiff
    if subdiff := _compare_enum(k, d):
        diff['enum'] = subdiff
    return diff


def compare_keywords(kwd_path):
    # the keyword dictionary contains standard FITS keywords
    # remove them as they're mostly not defined in the datamodel schemas
    datamodel_keywords = _filter_non_pattern(_filter_non_standard(dmd.load()))
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
            definitions_diff[kw] = diff

    return in_kwd, in_datamodels, in_both, definitions_diff, kwd_keywords, datamodel_keywords
