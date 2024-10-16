import re

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
    return {k: v for k, v in keyword_dictionary.items() if not _is_standard(k[1])}


def compare_keywords(kwd_path):
    # the keyword dictionary contains standard FITS keywords
    # remove them as they're mostly not defined in the datamodel schemas
    datamodel_keywords = _filter_non_standard(dmd.load())
    kwd_keywords = _filter_non_standard(kwd.load(kwd_path))

    # get keys to compare
    kwd_keys = set(kwd_keywords.keys())
    datamodel_keys = set(datamodel_keywords.keys())

    # compare keys
    in_kwd = kwd_keys - datamodel_keys
    in_datamodels = datamodel_keys - kwd_keys
    return in_kwd, in_datamodels, kwd_keywords, datamodel_keywords
