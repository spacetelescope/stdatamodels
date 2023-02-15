import datetime
from functools import partial
import hashlib
import inspect
import io
import os
from pkg_resources import parse_version
import re
import warnings
import weakref

import numpy as np
from astropy.io import fits
from astropy import time
from astropy.utils.exceptions import AstropyWarning
import asdf
from asdf import resolver
from asdf import schema as asdf_schema
from asdf.tags.core import NDArrayType
from asdf.tags.core import ndarray, HistoryEntry
from asdf import treeutil
from asdf.util import HashableDict
from asdf import tagged
from asdf import generic_io
from jsonschema import validators

from . import properties
from . import schema as mschema
from . import util
from . import validate

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


__all__ = ['to_fits', 'from_fits', 'fits_hdu_name', 'get_hdu', 'is_builtin_fits_keyword']


_ASDF_EXTENSION_NAME = "ASDF"
_FITS_SOURCE_PREFIX = "fits:"
_NDARRAY_TAG = "tag:stsci.edu:asdf/core/ndarray-1.0.0"

_ASDF_GE_2_6 = parse_version(asdf.__version__) >= parse_version('2.6')


_builtin_regexes = [
    '', 'NAXIS[0-9]{0,3}', 'BITPIX', 'XTENSION', 'PCOUNT', 'GCOUNT',
    'EXTEND', 'BSCALE', 'BZERO', 'BLANK', 'DATAMAX', 'DATAMIN',
    'EXTNAME', 'EXTVER', 'EXTLEVEL', 'GROUPS', 'PYTPE[0-9]',
    'PSCAL[0-9]', 'PZERO[0-9]', 'SIMPLE', 'TFIELDS',
    'TBCOL[0-9]{1,3}', 'TFORM[0-9]{1,3}', 'TTYPE[0-9]{1,3}',
    'TUNIT[0-9]{1,3}', 'TSCAL[0-9]{1,3}', 'TZERO[0-9]{1,3}',
    'TNULL[0-9]{1,3}', 'TDISP[0-9]{1,3}', 'HISTORY'
    ]


_builtin_regex = re.compile(
    '|'.join('(^{0}$)'.format(x) for x in _builtin_regexes))


def is_builtin_fits_keyword(key):
    """
    Returns `True` if the given `key` is a built-in FITS keyword, i.e.
    a keyword that is managed by ``astropy.io.fits`` and we wouldn't
    want to propagate through the `_extra_fits` mechanism.
    """
    return _builtin_regex.match(key) is not None


_keyword_indices = [
    ('nnn', 1000, None),
    ('nn', 100, None),
    ('n', 10, None),
    ('s', 27, ' ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    ]

# Key where the FITS hash is stored in the ASDF tree
FITS_HASH_KEY = '_fits_hash'


def _get_indexed_keyword(keyword, i):
    for (sub, max, r) in _keyword_indices:
        if sub in keyword:
            if i >= max:
                raise ValueError(
                    "Too many entries for given keyword '{0}'".format(keyword))
            if r is None:
                val = str(i)
            else:
                val = r[i]
            keyword = keyword.replace(sub, val)

    return keyword


def fits_hdu_name(name):
    """
    Returns a FITS hdu name in the correct form for the current
    version of Python.
    """
    if isinstance(name, bytes):
        return name.decode('ascii')
    return name


def _get_hdu_name(schema):
    hdu_name = schema.get('fits_hdu')
    if hdu_name in (None, 'PRIMARY'):
        hdu_name = 0
    else:
        hdu_name = fits_hdu_name(hdu_name)
    return hdu_name


def _get_hdu_type(hdu_name, schema=None, value=None):
    hdu_type = None
    if hdu_name in (0, 'PRIMARY'):
        hdu_type = fits.PrimaryHDU
    elif schema is not None:
        dtype = ndarray.asdf_datatype_to_numpy_dtype(schema['datatype'])
        if dtype.fields is not None:
            hdu_type = fits.BinTableHDU
    elif value is not None:
        if hasattr(value, 'dtype') and value.dtype.names is not None:
            hdu_type = fits.BinTableHDU
    return hdu_type


def _get_hdu_pair(hdu_name, index=None):
    if index is None:
        pair = hdu_name
    else:
        pair = (hdu_name, index + 1)
    return pair


def get_hdu(hdulist, hdu_name, index=None):
    pair = _get_hdu_pair(hdu_name, index=index)
    try:
        hdu = hdulist[pair]
    except (KeyError, IndexError, AttributeError):
        try:
            if isinstance(pair, str):
                hdu = hdulist[(pair, 1)]
            elif isinstance(pair, tuple) and index == 0:
                hdu = hdulist[pair[0]]
            else:
                raise
        except (KeyError, IndexError, AttributeError):
            raise AttributeError(
                "Property missing because FITS file has no "
                "'{0!r}' HDU".format(
                    pair))

    if index is not None:
        if hdu.header.get('EXTVER', 1) != index + 1:
            raise AttributeError(
                "Property missing because FITS file has no "
                "{0!r} HDU".format(
                    pair))

    return hdu


def _make_hdu(hdulist, hdu_name, index=None, hdu_type=None, value=None):
    if isinstance(value, NDArrayType):
        value = np.asarray(value)

    if hdu_type is None:
        hdu_type = _get_hdu_type(hdu_name, value=value)
        if hdu_type is None:
            hdu_type = fits.ImageHDU

    if hdu_type == fits.PrimaryHDU:
        hdu = hdu_type(value)
    else:
        hdu = hdu_type(value, name=hdu_name)
    if index is not None:
        hdu.ver = index + 1
    hdulist.append(hdu)
    return hdu


def _get_or_make_hdu(hdulist, hdu_name, index=None, hdu_type=None, value=None):
    if isinstance(hdulist, weakref.ReferenceType):
        ref = hdulist()
        result = _get_or_make_hdu(ref, hdu_name, index=index, hdu_type=hdu_type, value=value)
        # While likely not needed (as ref will fall out of scope on
        # return), del ref to remove the reference to the hdulist we
        # resolved from the weakref. weakref is important here as
        # this function is called within a validator which will be
        # cached holding referenced objects in memory.
        # https://github.com/spacetelescope/stdatamodels/pull/109
        del ref
        return result
    try:
        hdu = get_hdu(hdulist, hdu_name, index=index)
    except AttributeError:
        hdu = _make_hdu(hdulist, hdu_name, index=index, hdu_type=hdu_type,
                        value=value)
    else:
        if hdu_type is not None and not isinstance(hdu, hdu_type):
            new_hdu = _make_hdu(hdulist, hdu_name, index=index,
                                hdu_type=hdu_type, value=value)
            for key, val in hdu.header.items():
                if not is_builtin_fits_keyword(key):
                    new_hdu.header[key] = val
            hdulist.remove(hdu)
            hdu = new_hdu
        elif value is not None:
            hdu.data = value
    return hdu


def _assert_non_primary_hdu(hdu_name):
    if hdu_name in (None, 0, 'PRIMARY'):
        raise ValueError(
            "Schema for data property does not specify a non-primary hdu name")


##############################################################################
# WRITER


def _fits_comment_section_handler(fits_context, validator, properties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    title = schema.get('title')
    if title is not None:
        current_comment_stack = fits_context.comment_stack
        current_comment_stack.append(ensure_ascii(title))

    for property, subschema in properties.items():
        if property in instance:
            for error in validator.descend(
                instance[property],
                subschema,
                path=property,
                schema_path=property,
            ):
                yield error

    if title is not None:
        current_comment_stack.pop(-1)


def _fits_element_writer(fits_context, validator, fits_keyword, instance, schema):
    if schema.get('type', 'object') == 'array':
        raise ValueError("'fits_keyword' is not valid with type of 'array'")

    hdu_name = _get_hdu_name(schema)

    hdu = _get_or_make_hdu(fits_context.hdulist, hdu_name, index=fits_context.sequence_index)

    for comment in fits_context.comment_stack:
        hdu.header.append((' ', ''), end=True)
        hdu.header.append((' ', comment), end=True)
        hdu.header.append((' ', ''), end=True)
    fits_context.comment_stack = []

    comment = ensure_ascii(get_short_doc(schema))
    instance = ensure_ascii(instance)

    if fits_keyword in ('COMMENT', 'HISTORY'):
        for item in instance:
            hdu.header[fits_keyword] = ensure_ascii(item)
    elif fits_keyword in hdu.header:
        hdu.header[fits_keyword] = (instance, comment)
    else:
        hdu.header.append((fits_keyword, instance, comment), end=True)


def _fits_array_writer(fits_context, validator, _, instance, schema):
    if instance is None:
        return

    instance = np.asanyarray(instance)

    if not len(instance.shape):
        return

    if 'ndim' in schema:
        ndarray.validate_ndim(validator, schema['ndim'], instance, schema)
    if 'max_ndim' in schema:
        ndarray.validate_max_ndim(validator, schema['max_ndim'], instance, schema)
    if 'dtype' in schema:
        ndarray.validate_dtype(validator, schema['dtype'], instance, schema)

    hdu_name = _get_hdu_name(schema)
    _assert_non_primary_hdu(hdu_name)
    index = fits_context.sequence_index
    if index is None:
        index = 0

    hdu_type = _get_hdu_type(hdu_name, schema=schema, value=instance)
    hdu = _get_or_make_hdu(fits_context.hdulist, hdu_name,
                           index=index, hdu_type=hdu_type)

    hdu.data = instance
    hdu.ver = index + 1


# This is copied from jsonschema._validators and modified to keep track
# of the index of the item we've recursed into.
def _fits_item_recurse(fits_context, validator, items, instance, schema):
    if not validator.is_type(instance, "array"):
        return

    if validator.is_type(items, "object"):
        for index, item in enumerate(instance):
            fits_context.sequence_index = index
            for error in validator.descend(item, items, path=index):
                yield error
    else:
        # We don't do the index trick on "tuple validated" sequences
        for (index, item), subschema in zip(enumerate(instance), items):
            for error in validator.descend(
                item, subschema, path=index, schema_path=index,
            ):
                yield error


def _fits_type(fits_context, validator, items, instance, schema):
    if instance in ('N/A', '#TODO', '', None):
        return
    return validators.Draft4Validator.VALIDATORS["type"](validator, items, instance, schema)


class FitsContext:
    def __init__(self, hdulist):
        self.hdulist = weakref.ref(hdulist)
        self.comment_stack = []
        self.sequence_index = None


def _get_validators(hdulist):
    fits_context = FitsContext(hdulist)

    validators = HashableDict(asdf_schema.YAML_VALIDATORS)

    partial_fits_array_writer = partial(_fits_array_writer, fits_context)

    validators.update({
        'fits_keyword': partial(_fits_element_writer, fits_context),
        'ndim': partial_fits_array_writer,
        'max_ndim': partial_fits_array_writer,
        'datatype': partial_fits_array_writer,
        'items': partial(_fits_item_recurse, fits_context),
        'properties': partial(_fits_comment_section_handler, fits_context),
        'type': partial(_fits_type, fits_context),
    })

    return validators


META_SCHEMA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'metaschema'))


FITS_SCHEMA_URL_MAPPING = resolver.Resolver(
    [
        ('http://stsci.edu/schemas/fits-schema/',
         'file://' + META_SCHEMA_PATH + '/{url_suffix}.yaml')
    ] + resolver.DEFAULT_URL_MAPPING, 'url')


def _save_from_schema(hdulist, tree, schema):
    def datetime_callback(node, json_id):
        if isinstance(node, datetime.datetime):
            node = time.Time(node)

        if isinstance(node, time.Time):
            node = str(time.Time(node, format='iso'))

        return node

    tree = treeutil.walk_and_modify(tree, datetime_callback)

    if _ASDF_GE_2_6:
        kwargs = {"_visit_repeat_nodes": True}
    else:
        kwargs = {}

    validator = asdf_schema.get_validator(
        schema, None, _get_validators(hdulist), FITS_SCHEMA_URL_MAPPING, **kwargs)

    # This actually kicks off the saving
    validator.validate(tree, _schema=schema)

    # Replace arrays in the tree that are identical to HDU arrays
    # with ndarray-1.0.0 tagged objects with special source values
    # that represent links to the surrounding FITS file.
    def ndarray_callback(node, json_id):
        if (isinstance(node, (np.ndarray, NDArrayType))):
            for hdu_index, hdu in enumerate(hdulist):
                if hdu.data is not None and node is hdu.data:
                    return _create_tagged_dict_for_fits_array(hdu, hdu_index)

        return node

    tree = treeutil.walk_and_modify(tree, ndarray_callback)

    return tree


def _create_tagged_dict_for_fits_array(hdu, hdu_index):
     # Views over arrays stored in FITS files have some idiosyncrasies.
     # astropy.io.fits always writes arrays C-contiguous with big-endian
     # byte order, whereas asdf preserves the "contiguousity" and byte order
     # of the base array.
    dtype, byteorder = ndarray.numpy_dtype_to_asdf_datatype(
        hdu.data.dtype,
        include_byteorder=True,
        override_byteorder="big"
    )

    if hdu.name == "":
        source = f"{_FITS_SOURCE_PREFIX}{hdu_index}"
    else:
        source = f"{_FITS_SOURCE_PREFIX}{hdu.name},{hdu.ver}"

    return tagged.TaggedDict(
        data={
            "source": source,
            "shape": list(hdu.data.shape),
            "datatype": dtype,
            "byteorder": byteorder
        },
        tag=_NDARRAY_TAG
    )


def _normalize_arrays(tree):
    """
    Convert arrays in the tree to C-contiguous, since that is
    how they are written to disk by astropy.io.fits and we
    don't want the asdf library to notice the change in memory
    layout and duplicate the array in the embedded ASDF.
    """
    def normalize_array(node, json_id):
        if isinstance(node, np.ndarray):
            # We can't use np.ascontiguousarray because it converts FITS_rec
            # to vanilla np.ndarray, which results in misinterpretation of
            # unsigned int values.
            if not node.flags.c_contiguous:
                node = node.copy()
        return node

    return treeutil.walk_and_modify(tree, normalize_array)


def _save_extra_fits(hdulist, tree):
    # Handle _extra_fits
    for hdu_name, parts in tree.get('extra_fits', {}).items():
        hdu_name = fits_hdu_name(hdu_name)
        if 'data' in parts:
            hdu_type = _get_hdu_type(hdu_name, value=parts['data'])
            hdu = _get_or_make_hdu(hdulist, hdu_name, hdu_type=hdu_type,
                                   value=parts['data'])
        if 'header' in parts:
            hdu = _get_or_make_hdu(hdulist, hdu_name)
            for key, val, comment in parts['header']:
                if is_builtin_fits_keyword(key):
                    continue
                hdu.header.append((key, val, comment), end=True)


def _save_history(hdulist, tree):
    if 'history' not in tree:
        return

    # Support the older way of representing ASDF history entries
    if isinstance(tree['history'], list):
        history = tree['history']
    else:
        history = tree['history'].get('entries', [])

    for i in range(len(history)):
        # There is no guarantee the user has added proper HistoryEntry records
        if not isinstance(history[i], HistoryEntry):
            if isinstance(history[i], dict):
                history[i] = HistoryEntry(history[i])
            else:
                history[i] = HistoryEntry({'description': str(history[i])})
        hdulist[0].header['HISTORY'] = history[i]['description']


def to_fits(tree, schema, hdulist=None):
    """Create hdulist and modified ASDF tree"""
    if hdulist is None:
        hdulist = fits.HDUList()
        hdulist.append(fits.PrimaryHDU())

    tree = _normalize_arrays(tree)
    tree = _save_from_schema(hdulist, tree, schema)
    _save_extra_fits(hdulist, tree)
    _save_history(hdulist, tree)

    # Store the FITS hash in the tree
    tree[FITS_HASH_KEY] = fits_hash(hdulist)

    if _ASDF_EXTENSION_NAME in hdulist:
        del hdulist[_ASDF_EXTENSION_NAME]

    hdulist.append(_create_asdf_hdu(tree))

    return hdulist


def _create_asdf_hdu(tree):
    buffer = io.BytesIO()
    asdf.AsdfFile(tree).write_to(buffer)
    buffer.seek(0)

    data = np.array(buffer.getbuffer(), dtype=np.uint8)[None, :]
    fmt = f"{len(data[0])}B"
    column = fits.Column(array=data, format=fmt, name="ASDF_METADATA")
    return fits.BinTableHDU.from_columns([column], name=_ASDF_EXTENSION_NAME)


##############################################################################
# READER


def _fits_keyword_loader(hdulist, fits_keyword, schema, hdu_index, known_keywords):

    hdu_name = _get_hdu_name(schema)
    try:
        hdu = get_hdu(hdulist, hdu_name, hdu_index)
    except AttributeError:
        return None

    try:
        val = hdu.header[fits_keyword]
    except KeyError:
        return None

    tag = schema.get('tag')
    if tag is not None:
        val = tagged.tag_object(tag, val)

    known_keywords.setdefault(hdu, set()).add(fits_keyword)

    return val


def _fits_array_loader(hdulist, schema, hdu_index, known_datas, context):
    hdu_name = _get_hdu_name(schema)
    _assert_non_primary_hdu(hdu_name)
    try:
        hdu = get_hdu(hdulist, hdu_name, hdu_index)
    except AttributeError:
        return None

    known_datas.add(hdu)
    return from_fits_hdu(hdu, schema, context._cast_fits_arrays)


def _schema_has_fits_hdu(schema):
    has_fits_hdu = [False]

    for node in treeutil.iter_tree(schema):
        if isinstance(node, dict) and 'fits_hdu' in node:
            has_fits_hdu[0] = True

    return has_fits_hdu[0]


def _load_from_schema(hdulist, schema, tree, context, skip_fits_update=False):
    known_keywords = {}
    known_datas = set()

    # Check if there are any table HDU's. If not, this whole process
    # can be skipped.
    if skip_fits_update:
        if not any(isinstance(hdu, fits.BinTableHDU) for hdu in hdulist if hdu.name != 'ASDF'):
            log.debug('Skipping FITS updating completely.')
            return known_keywords, known_datas
        log.debug('Skipping FITS keyword updating except for BinTableHDU and its associated header keywords.')

    # Determine maximum EXTVER that could be used in finding named HDU's.
    # This is needed to constrain the loop over HDU's when resolving arrays.
    max_extver = max(hdu.ver for hdu in hdulist) if len(hdulist) else 0

    def callback(schema, path, combiner, ctx, recurse):
        result = None
        if not skip_fits_update and 'fits_keyword' in schema:
            fits_keyword = schema['fits_keyword']
            result = _fits_keyword_loader(
                hdulist, fits_keyword, schema,
                ctx.get('hdu_index'), known_keywords)

            if result is None and context._validate_on_assignment:
                validate.value_change(path, result, schema, context)
            else:
                if context._validate_on_assignment:
                    if validate.value_change(path, result, schema, context):
                        properties.put_value(path, result, tree)
                else:
                    properties.put_value(path, result, tree)

        elif 'fits_hdu' in schema and (
                'max_ndim' in schema or 'ndim' in schema or 'datatype' in schema):
            result = _fits_array_loader(
                hdulist, schema, ctx.get('hdu_index'), known_datas, context)

            if result is None and context._validate_on_assignment:
                validate.value_change(path, result, schema, context)
            else:
                if context._validate_on_assignment:
                    if validate.value_change(path, result, schema, context):
                        properties.put_value(path, result, tree)
                else:
                    properties.put_value(path, result, tree)

        if schema.get('type') == 'array':
            has_fits_hdu = _schema_has_fits_hdu(schema)
            if has_fits_hdu:
                for i in range(max_extver):
                    recurse(schema['items'],
                            path + [i],
                            combiner,
                            {'hdu_index': i})
                return True

    mschema.walk_schema(schema, callback)
    return known_keywords, known_datas


def _load_extra_fits(hdulist, known_keywords, known_datas, tree):
    # Remove any extra_fits from tree
    if 'extra_fits' in tree:
        del tree['extra_fits']

    # Add header keywords and data not in schema to extra_fits
    for hdu in hdulist:
        # Don't add ASDF hdus to extra_fits for any reason
        if hdu.name != "ASDF":
            known = known_keywords.get(hdu, set())

            cards = []
            for key, val, comment in hdu.header.cards:
                if not (is_builtin_fits_keyword(key) or
                        key in known):
                    cards.append([key, val, comment])

            if len(cards):
                properties.put_value(
                    ['extra_fits', hdu.name, 'header'], cards, tree)

            if hdu not in known_datas:
                if hdu.data is not None:
                    properties.put_value(
                        ['extra_fits', hdu.name, 'data'], hdu.data, tree)


def _load_history(hdulist, tree):
    try:
        hdu = get_hdu(hdulist, 0)
    except AttributeError:
        return

    header = hdu.header
    if 'HISTORY' not in header:
        return

    history = tree['history'] = {'entries': []}

    for entry in header['HISTORY']:
        history['entries'].append(HistoryEntry({'description': entry}))


def from_fits(hdulist, schema, context, skip_fits_update=None, **kwargs):
    """Read model information from a FITS HDU list

    Parameters
    ----------
    hdulist : astropy.io.fits.HDUList
        The FITS HDUList

    schema : dict
        The schema defining the ASDF > FITS_KEYWORD, FITS_HDU mapping.

    context: DataModel
        The `DataModel` to update

    skip_fits_update : bool or None
        When `False`, models opened from FITS files will proceed
        and load the FITS header values into the model.
        When `True` and the FITS file has an ASDF extension, the
        loading/validation of the FITS header will be skipped, loading
        the model only from the ASDF extension.
        When `None`, the value is taken from the environmental SKIP_FITS_UPDATE.
        Otherwise, the default is `False`
    """
    try:
        ff = from_fits_asdf(hdulist, **kwargs)
    except Exception as exc:
        raise exc.__class__("ERROR loading embedded ASDF: " + str(exc)) from exc

    # Determine whether skipping the FITS loading can be done.
    skip_fits_update = _verify_skip_fits_update(
        skip_fits_update, hdulist, ff, context
    )

    known_keywords, known_datas = _load_from_schema(
        hdulist, schema, ff.tree, context, skip_fits_update=skip_fits_update
    )
    if not skip_fits_update:
        _load_extra_fits(hdulist, known_keywords, known_datas, ff.tree)

    _load_history(hdulist, ff.tree)

    return ff


def from_fits_asdf(hdulist,
                   ignore_version_mismatch=True,
                   ignore_unrecognized_tag=False,
                   **kwargs):
    """
    Wrap asdf call to extract optional arguments
    """
    ignore_missing_extensions = kwargs.pop('ignore_missing_extensions')

    try:
        asdf_extension = hdulist[_ASDF_EXTENSION_NAME]
    except (KeyError, IndexError, AttributeError):
        # This means there is no ASDF extension
        return asdf.AsdfFile(
            ignore_version_mismatch=ignore_version_mismatch,
            ignore_unrecognized_tag=ignore_unrecognized_tag,
        )

    generic_file = generic_io.get_file(io.BytesIO(asdf_extension.data), mode="rw")
    # get kwargs supported by asdf, this will not pass along arbitrary kwargs
    akwargs = {
        k: kwargs[k] for k in inspect.getfullargspec(asdf.open).args
        if k[0] != '_' and k in kwargs
    }
    af = asdf.open(
        generic_file,
        ignore_version_mismatch=ignore_version_mismatch,
        ignore_unrecognized_tag=ignore_unrecognized_tag,
        ignore_missing_extensions=ignore_missing_extensions,
        **akwargs
    )
    # map hdulist to blocks here
    _map_hdulist_to_arrays(hdulist, af)
    return af


def _map_hdulist_to_arrays(hdulist, af):
    def callback(node, json_id):
        if (
                isinstance(node, NDArrayType) and
                isinstance(node._source, str) and
                node._source.startswith(_FITS_SOURCE_PREFIX)
                ):
            # read the array data from the hdulist
            source = node._source
            parts = re.match(
                # All printable ASCII characters are allowed in EXTNAME
                "((?P<name>[ -~]+),)?(?P<ver>[0-9]+)",
                source[len(_FITS_SOURCE_PREFIX) :],
            )
            if parts is not None:
                ver = int(parts.group("ver"))
                if parts.group("name"):
                    pair = (parts.group("name"), ver)
                else:
                    pair = ver
            data = hdulist[pair].data
            return data
        return node
    af.tree = treeutil.walk_and_modify(af.tree, callback)


def from_fits_hdu(hdu, schema, cast_arrays=True):
    """
    Read the data from a fits hdu into a numpy ndarray
    """
    data = hdu.data

    if cast_arrays:
        # Save the column listeners for possible restoration
        if hasattr(data, '_coldefs'):
            listeners = data._coldefs._listeners
        else:
            listeners = None

        # Cast array to type mentioned in schema
        data = properties._cast(data, schema)

        # Casting a table loses the column listeners, so restore them
        if listeners is not None:
            data._coldefs._listeners = listeners
    else:
        # Correct the pseudo-unsigned int problem (this normally occurs
        # inside properties._cast, but we still need to do it even
        # when not casting, otherwise arrays from FITS will fail validation).
        if isinstance(data, fits.FITS_rec):
            data.dtype = util.rebuild_fits_rec_dtype(data)

    return data


def _verify_skip_fits_update(skip_fits_update, hdulist, asdf_struct, context):
    """Ensure all conditions for skipping FITS updating are true

    Returns True if either 1) the FITS hash in the asdf structure matches the input
    FITS structure. Or 2) skipping has been explicitly asked for in `skip_fits_update`.

    Parameters
    ----------
    skip_fits_update : bool
        Regardless of FIT hash check, attempt to skip if requested.

    hdulist : astropy.io.fits.HDUList
        The input FITS information

    asdf_struct : asdf.ASDFFile
        The associated ASDF structure

    context : DataModel
        The DataModel being built.

    Returns
    -------
    skip_fits_update : bool
        All conditions are satisfied for skipping FITS updating.
    """
    if skip_fits_update is None:
        skip_fits_update = util.get_envar_as_boolean('SKIP_FITS_UPDATE', None)

    # If skipping has been explicitly disallowed, indicate as such.
    if skip_fits_update is False:
        return False

    # Skipping has either been requested or has been left to be determined automatically.
    # Continue checking conditions necessary for skipping.

    # Need an already existing ASDF. If not, cannot skip.
    if not len(asdf_struct.tree):
        log.debug('No ASDF information found. Cannot skip updating from FITS headers.')
        return False

    # Ensure model types match
    hdulist_model_type = util.get_model_type(hdulist)
    if hdulist_model_type != context.__class__.__name__:
        log.debug(f'Input model type {hdulist_model_type} does not match the'
                  f' requested model {type(context)}.'
                  ' Cannot skip updating from FITS headers.')
        return False

    # Check for FITS hash and compare to current. If equal, automatically skip.
    if asdf_struct.tree.get(FITS_HASH_KEY, None) is not None:
        if asdf_struct.tree[FITS_HASH_KEY] == fits_hash(hdulist):
            log.debug('FITS hash matches. Skipping FITS updating.')
            return True

    # If skip only if explicitly requested.
    return False if skip_fits_update is None else True


def fits_hash(hdulist):
    """Calculate a hash based on all HDU headers

    Uses basic SHA-256 hash to calculate.

    Parameters
    ----------
    hdulist : astropy.fits.HDUList
        The FITS structure.

    Returns
    -------
    fits_hash : str
        The hash of all HDU headers.
    """
    fits_hash = hashlib.sha256()

    # Ignore FITS header warnings, such as "Card is too long".
    # Such issues are inconsequential to hash calculation.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', AstropyWarning)
        fits_hash.update(''.join(
            str(hdu.header)
            for hdu in hdulist
            if hdu.name != 'ASDF').encode()
        )
    return fits_hash.hexdigest()


def get_short_doc(schema):
    title = schema.get('title', None)
    description = schema.get('description', None)
    if description is None:
        description = title or ''
    else:
        if title is not None:
            description = title + '\n\n' + description
    return description.partition('\n')[0]


def ensure_ascii(s):
    # TODO: This function seems to only ever receive
    # string input.  Also it's not checking that the
    # characters in the string fall within the valid
    # range for FITS headers.
    if isinstance(s, bytes):
        s = s.decode('ascii')
    return s
