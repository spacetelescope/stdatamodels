import datetime
import hashlib
import io
import logging
import re
import warnings
import weakref
from functools import partial

import asdf
import numpy as np
from asdf import generic_io, tagged, treeutil
from asdf import schema as asdf_schema
from asdf.tags.core import HistoryEntry, NDArrayType, ndarray
from asdf.util import HashableDict
from astropy import time
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning

from . import properties, util, validate
from . import schema as mschema

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


__all__ = ["to_fits", "from_fits", "get_hdu", "is_builtin_fits_keyword"]


_ASDF_EXTENSION_NAME = "ASDF"
_FITS_SOURCE_PREFIX = "fits:"
if asdf.versioning.default_version > "1.5.0":
    _NDARRAY_TAG = "tag:stsci.edu:asdf/core/ndarray-1.1.0"
else:
    _NDARRAY_TAG = "tag:stsci.edu:asdf/core/ndarray-1.0.0"

_builtin_regexes = [
    "",
    "NAXIS[0-9]{0,3}",
    "BITPIX",
    "XTENSION",
    "PCOUNT",
    "GCOUNT",
    "EXTEND",
    "BSCALE",
    "BZERO",
    "BLANK",
    "DATAMAX",
    "DATAMIN",
    "EXTNAME",
    "EXTVER",
    "EXTLEVEL",
    "GROUPS",
    "PYTPE[0-9]",
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


_builtin_regex = re.compile("|".join(f"(^{x}$)" for x in _builtin_regexes))


def is_builtin_fits_keyword(key):
    """
    Check if key is a FITS builtin.

    Builtins are those managed by ``astropy.io.fits``, and we don't
    want to propagate those through the `_extra_fits` mechanism.

    Parameters
    ----------
    key : str
        The keyword to check.

    Returns
    -------
    bool
        `True` if the keyword is a built-in FITS keyword.
    """
    return _builtin_regex.match(key) is not None


_keyword_indices = [
    ("nnn", 1000, None),
    ("nn", 100, None),
    ("n", 10, None),
    ("s", 27, " ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
]

# Key where the FITS hash is stored in the ASDF tree
FITS_HASH_KEY = "_fits_hash"


def _get_indexed_keyword(keyword, i):
    for sub, max_value, r in _keyword_indices:
        if sub in keyword:
            if i >= max_value:
                raise ValueError(f"Too many entries for given keyword '{keyword}'")
            if r is None:
                val = str(i)
            else:
                val = r[i]
            keyword = keyword.replace(sub, val)

    return keyword


def _get_hdu_name(schema):
    hdu_name = schema.get("fits_hdu")
    if hdu_name in (None, "PRIMARY"):
        hdu_name = 0
    return hdu_name


def _get_hdu_type(hdu_name, schema=None, value=None):
    hdu_type = None
    if hdu_name in (0, "PRIMARY"):
        hdu_type = fits.PrimaryHDU
    elif schema is not None:
        dtype = ndarray.asdf_datatype_to_numpy_dtype(schema["datatype"])
        if dtype.fields is not None:
            hdu_type = fits.BinTableHDU
    elif value is not None:
        if hasattr(value, "dtype") and value.dtype.names is not None:
            hdu_type = fits.BinTableHDU
    return hdu_type


def _get_hdu_pair(hdu_name, index=None):
    if index is None:
        pair = hdu_name
    else:
        pair = (hdu_name, index + 1)
    return pair


def get_hdu(hdulist, hdu_name, index=None, _cache=None):
    """
    Retrieve an HDU from an hdulist.

    Parameters
    ----------
    hdulist : astropy.io.fits.hdu.hdulist.HDUList
        A FITS HDUList
    hdu_name : str
        The name of the HDU to retrieve
    index : int, optional
        The index of the HDU to retrieve
    _cache : dict, optional
        Cache of HDUs

    Returns
    -------
    hdu : astropy.io.fits.hdu.base._BaseHDU
        The HDU as represented by astropy.io.fits
    """
    pair = _get_hdu_pair(hdu_name, index=index)
    if _cache is not None and pair in _cache:
        return _cache[pair]
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
        except (KeyError, IndexError, AttributeError) as err:
            raise AttributeError(
                f"Property missing because FITS file has no '{pair!r}' HDU"
            ) from err

    if index is not None:
        if hdu.header.get("EXTVER", 1) != index + 1:
            raise AttributeError(f"Property missing because FITS file has no {pair!r} HDU")

    if _cache is not None:
        _cache[pair] = hdu
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
        hdu = _make_hdu(hdulist, hdu_name, index=index, hdu_type=hdu_type, value=value)
    else:
        if hdu_type is not None and not isinstance(hdu, hdu_type):
            new_hdu = _make_hdu(hdulist, hdu_name, index=index, hdu_type=hdu_type, value=value)
            for key, val in hdu.header.items():
                if not is_builtin_fits_keyword(key):
                    new_hdu.header[key] = val
            hdulist.remove(hdu)
            hdu = new_hdu
        elif value is not None:
            hdu.data = value
    return hdu


def _assert_non_primary_hdu(hdu_name):
    if hdu_name in (None, 0, "PRIMARY"):
        raise ValueError("Schema for data property does not specify a non-primary hdu name")


##############################################################################
# WRITER


def _fits_comment_section_handler(fits_context, validator, properties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    title = schema.get("title")
    if title is not None:
        current_comment_stack = fits_context.comment_stack
        current_comment_stack.append(title)

    for prop, subschema in properties.items():
        if prop in instance:
            yield from validator.descend(
                instance[prop],
                subschema,
                path=prop,
                schema_path=prop,
            )

    if title is not None:
        current_comment_stack.pop(-1)


def _fits_element_writer(fits_context, validator, fits_keyword, instance, schema):
    if schema.get("type", "object") == "array":
        raise ValueError("'fits_keyword' is not valid with type of 'array'")

    hdu_name = _get_hdu_name(schema)

    hdu = _get_or_make_hdu(fits_context.hdulist, hdu_name, index=fits_context.sequence_index)

    for comment in fits_context.comment_stack:
        hdu.header.append((" ", ""), end=True)
        hdu.header.append((" ", comment), end=True)
        hdu.header.append((" ", ""), end=True)
    fits_context.comment_stack = []

    comment = _get_short_doc(schema)

    if fits_keyword in ("COMMENT", "HISTORY"):
        for item in instance:
            hdu.header[fits_keyword] = item
    elif fits_keyword in hdu.header:
        hdu.header[fits_keyword] = (instance, comment)
    else:
        hdu.header.append((fits_keyword, instance, comment), end=True)


def _fits_array_writer(fits_context, validator, _, instance, schema):
    if instance is None:
        return

    instance_id = id(instance)

    instance = np.asanyarray(instance)

    if not len(instance.shape):
        return

    if "ndim" in schema:
        yield from ndarray.validate_ndim(validator, schema["ndim"], instance, schema)
    if "max_ndim" in schema:
        yield from ndarray.validate_max_ndim(validator, schema["max_ndim"], instance, schema)
    if "datatype" in schema:
        yield from validate._validate_datatype(validator, schema["datatype"], instance, schema)

    hdu_name = _get_hdu_name(schema)
    _assert_non_primary_hdu(hdu_name)
    index = fits_context.sequence_index
    if index is None:
        index = 0

    hdu_type = _get_hdu_type(hdu_name, schema=schema, value=instance)
    hdu = _get_or_make_hdu(fits_context.hdulist, hdu_name, index=index, hdu_type=hdu_type)

    hdu.data = instance
    if instance_id in fits_context.extension_array_links:
        if fits_context.extension_array_links[instance_id]() is not hdu:
            raise ValueError("Linking one array to multiple hdus is not supported")
    fits_context.extension_array_links[instance_id] = weakref.ref(hdu)
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
        for (index, item), subschema in zip(enumerate(instance), items, strict=False):
            for error in validator.descend(
                item,
                subschema,
                path=index,
                schema_path=index,
            ):
                yield error


def _fits_type(fits_context, validator, items, instance, schema):
    if instance in ("N/A", "#TODO", "", None):
        return

    return asdf_schema.YAML_VALIDATORS["type"](validator, items, instance, schema)


class FitsContext:
    def __init__(self, hdulist):
        self.hdulist = weakref.ref(hdulist)
        self.comment_stack = []
        self.sequence_index = None
        self.extension_array_links = {}


def _get_validators(hdulist):
    fits_context = FitsContext(hdulist)

    validators = HashableDict(asdf_schema.YAML_VALIDATORS)

    partial_fits_array_writer = partial(_fits_array_writer, fits_context)

    validators.update(
        {
            "fits_keyword": partial(_fits_element_writer, fits_context),
            "ndim": partial_fits_array_writer,
            "max_ndim": partial_fits_array_writer,
            "datatype": partial_fits_array_writer,
            "items": partial(_fits_item_recurse, fits_context),
            "properties": partial(_fits_comment_section_handler, fits_context),
            "type": partial(_fits_type, fits_context),
        }
    )

    return validators, fits_context


def _save_from_schema(hdulist, tree, schema):
    def datetime_callback(node):
        if isinstance(node, datetime.datetime):
            node = time.Time(node)

        if isinstance(node, time.Time):
            node = str(time.Time(node, format="iso"))

        return node

    tree = treeutil.walk_and_modify(tree, datetime_callback)

    kwargs = {"_visit_repeat_nodes": True}

    validators, context = _get_validators(hdulist)
    validator = asdf_schema.get_validator(schema, None, validators, **kwargs)

    # This actually kicks off the saving
    validator.validate(tree, _schema=schema)

    # Now link extensions to items in the tree

    def callback(node):
        if id(node) in context.extension_array_links:
            hdu = context.extension_array_links[id(node)]()
            return _create_tagged_dict_for_fits_array(hdu, hdulist.index(hdu))
        elif isinstance(node, (np.ndarray, NDArrayType)):
            # in addition to links generated during validation
            # replace arrays in the tree that are identical to HDU arrays
            # with ndarray-1.0.0 tagged objects with special source values
            # that represent links to the surrounding FITS file.
            # This is important for general ASDF-in-FITS support
            for hdu_index, hdu in enumerate(hdulist):
                if hdu.data is not None and node is hdu.data:
                    return _create_tagged_dict_for_fits_array(hdu, hdu_index)
        return node

    tree = treeutil.walk_and_modify(tree, callback)

    return tree


def _create_tagged_dict_for_fits_array(hdu, hdu_index):
    # Views over arrays stored in FITS files have some idiosyncrasies.
    # astropy.io.fits always writes arrays C-contiguous with big-endian
    # byte order, whereas asdf preserves the "contiguousity" and byte order
    # of the base array.
    dtype, byteorder = ndarray.numpy_dtype_to_asdf_datatype(
        hdu.data.dtype, include_byteorder=True, override_byteorder="big"
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
            "byteorder": byteorder,
        },
        tag=_NDARRAY_TAG,
    )


def _normalize_arrays(tree):
    """
    Convert arrays in the tree to C-contiguous.

    They are written to disk by astropy.io.fits in C-contiguous, and we
    don't want the asdf library to notice the change in memory
    layout and duplicate the array in the embedded ASDF.

    Parameters
    ----------
    tree : dict
        The ASDF tree.

    Returns
    -------
    tree : dict
        The ASDF tree with all arrays converted to C-contiguous.
    """

    def normalize_array(node):
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
    for hdu_name, parts in tree.get("extra_fits", {}).items():
        if "data" in parts:
            hdu_type = _get_hdu_type(hdu_name, value=parts["data"])
            hdu = _get_or_make_hdu(hdulist, hdu_name, hdu_type=hdu_type, value=parts["data"])
            node = _create_tagged_dict_for_fits_array(hdu, hdulist.index(hdu))
            tree["extra_fits"][hdu_name]["data"] = node
        if "header" in parts:
            hdu = _get_or_make_hdu(hdulist, hdu_name)
            for key, val, comment in parts["header"]:
                if is_builtin_fits_keyword(key):
                    continue
                hdu.header.append((key, val, comment), end=True)

    return tree


def _save_history(hdulist, tree):
    if "history" not in tree:
        return

    # Support the older way of representing ASDF history entries
    if isinstance(tree["history"], list):
        history = tree["history"]
    else:
        history = tree["history"].get("entries", [])

    for i in range(len(history)):
        # There is no guarantee the user has added proper HistoryEntry records
        if not isinstance(history[i], HistoryEntry):
            if isinstance(history[i], dict):
                history[i] = HistoryEntry(history[i])
            else:
                history[i] = HistoryEntry({"description": str(history[i])})
        hdulist[0].header["HISTORY"] = history[i]["description"]


def to_fits(tree, schema, hdulist=None):
    """
    Create hdulist and modified ASDF tree.

    Parameters
    ----------
    tree : dict
        The ASDF tree to convert to FITS.
    schema : dict
        The schema for the ASDF tree.
    hdulist : astropy.io.fits.HDUList, optional
        The HDU list to append to. If not provided, a new HDU list will be created.

    Returns
    -------
    hdulist : astropy.io.fits.HDUList
        The HDU list.
    """
    if hdulist is None:
        hdulist = fits.HDUList()
        hdulist.append(fits.PrimaryHDU())

    tree = _normalize_arrays(tree)
    tree = _save_from_schema(hdulist, tree, schema)
    tree = _save_extra_fits(hdulist, tree)
    _save_history(hdulist, tree)

    # Store the FITS hash in the tree
    tree[FITS_HASH_KEY] = fits_hash(hdulist)

    if _ASDF_EXTENSION_NAME in hdulist:
        del hdulist[_ASDF_EXTENSION_NAME]

    hdulist.append(_create_asdf_hdu(tree))

    return hdulist


def _create_asdf_hdu(tree):
    buffer = io.BytesIO()
    # convert all FITS_rec instances to numpy arrays, this is needed as
    # some arrays loaded from the FITS data for old files may not be defined
    # in the current schemas. These will be loaded as FITS_rec instances but
    # not linked back (and safely converted) on write if they are removed
    # from the schema.
    asdf.AsdfFile(util.convert_fitsrec_to_array_in_tree(tree)).write_to(buffer)
    buffer.seek(0)

    data = np.array(buffer.getbuffer(), dtype=np.uint8)[None, :]
    fmt = f"{len(data[0])}B"
    column = fits.Column(array=data, format=fmt, name="ASDF_METADATA")
    return fits.BinTableHDU.from_columns([column], name=_ASDF_EXTENSION_NAME)


##############################################################################
# READER


def _fits_keyword_loader(hdulist, fits_keyword, schema, hdu_index, known_keywords, fits_hdu_cache):
    hdu_name = _get_hdu_name(schema)
    try:
        hdu = get_hdu(hdulist, hdu_name, hdu_index, _cache=fits_hdu_cache)
    except AttributeError:
        return None

    try:
        val = hdu.header[fits_keyword]
    except KeyError:
        return None

    tag = schema.get("tag")
    if tag is not None:
        val = tagged.tag_object(tag, val)

    known_keywords.setdefault(hdu, set()).add(fits_keyword)

    return val


def _fits_array_loader(hdulist, schema, hdu_index, known_datas, fits_hdu_cache):
    hdu_name = _get_hdu_name(schema)
    _assert_non_primary_hdu(hdu_name)
    try:
        hdu = get_hdu(hdulist, hdu_name, hdu_index, _cache=fits_hdu_cache)
    except AttributeError:
        return None

    known_datas.add(hdu)
    return from_fits_hdu(hdu, schema)


def _schema_has_fits_hdu(schema):
    has_fits_hdu = [False]

    for node in treeutil.iter_tree(schema):
        if isinstance(node, dict) and "fits_hdu" in node:
            has_fits_hdu[0] = True

    return has_fits_hdu[0]


def _load_from_schema(
    hdulist, schema, tree, context, skip_fits_update=False, ignore_arrays=False, keep_unknown=True
):
    """
    Read model information from a FITS HDU list.

    Parameters
    ----------
    hdulist : astropy.io.fits.HDUList
        The FITS HDUList from which to read the data.
    schema : dict
        The schema defining the mapping between datamodel and FITS.
    tree : dict
        The ASDF tree to update.
    context : DataModel
        The `DataModel` from which to read context information.
    skip_fits_update : bool, optional
        If True, skip updating the tree based on the FITS HDUList.
    ignore_arrays : bool, optional
        If True, do not read array-type data.
    keep_unknown : bool, optional
        Controls the behavior for keywords that are in the schema but NOT in the input hdulist.
        If True, the output tree contains the keyword, and the corresponding attribute is None.
        If False, the keyword is not present in the output tree.

    Returns
    -------
    known_keywords : dict
        Dictionary of FITS keywords that were found in the HDUList.
    known_datas : set
        Set of HDUs that were found in the HDUList.
    """
    known_keywords = {}
    known_datas = set()

    # Check if there are any table HDU's. If not, this whole process
    # can be skipped.
    if skip_fits_update:
        if not any(isinstance(hdu, fits.BinTableHDU) for hdu in hdulist if hdu.name != "ASDF"):
            log.debug("Skipping FITS updating completely.")
            return known_keywords, known_datas
        log.debug(
            "Skipping FITS keyword updating except for "
            "BinTableHDU and its associated header keywords."
        )

    # Determine maximum EXTVER that could be used in finding named HDU's.
    # This is needed to constrain the loop over HDU's when resolving arrays.
    max_extver = max(hdu.ver for hdu in hdulist) if len(hdulist) else 0

    # hdulist.__getitem__ is surprisingly slow (2 ms per call on my system
    # for a nirspec mos file with ~500 extensions) so we use a cache
    # here to handle repeated accesses. A lru_cache around get_hdu
    # was not used as hdulist is not hashable.
    hdu_cache = {}

    def callback(schema, path, combiner, ctx, recurse):
        result = None
        if not skip_fits_update and "fits_keyword" in schema:
            fits_keyword = schema["fits_keyword"]
            result = _fits_keyword_loader(
                hdulist, fits_keyword, schema, ctx.get("hdu_index"), known_keywords, hdu_cache
            )
            if result is None and not keep_unknown:
                return
            if result is None and context._validate_on_assignment:
                validate.value_change(path, result, schema, context)
            else:
                if context._validate_on_assignment:
                    if validate.value_change(path, result, schema, context):
                        properties.put_value(path, result, tree)
                else:
                    properties.put_value(path, result, tree)

        elif (
            "fits_hdu" in schema
            and ("max_ndim" in schema or "ndim" in schema or "datatype" in schema)
            and not ignore_arrays
        ):
            result = _fits_array_loader(
                hdulist, schema, ctx.get("hdu_index"), known_datas, hdu_cache
            )

            if result is None and context._validate_on_assignment:
                validate.value_change(path, result, schema, context)
            else:
                if context._validate_on_assignment:
                    if validate.value_change(path, result, schema, context):
                        properties.put_value(path, result, tree)
                else:
                    properties.put_value(path, result, tree)

        if schema.get("type") == "array":
            has_fits_hdu = _schema_has_fits_hdu(schema)
            if has_fits_hdu:
                for i in range(max_extver):
                    recurse(schema["items"], path + [i], combiner, {"hdu_index": i})
                return True

    mschema.walk_schema(schema, callback)
    return known_keywords, known_datas


def _load_extra_fits(hdulist, known_keywords, known_datas, tree):
    # Remove any extra_fits from tree
    if "extra_fits" in tree:
        del tree["extra_fits"]

    # Add header keywords and data not in schema to extra_fits
    for hdu in hdulist:
        # Don't add ASDF hdus to extra_fits for any reason
        if hdu.name != "ASDF":
            known = known_keywords.get(hdu, set())

            cards = []
            for key, val, comment in hdu.header.cards:
                if not (is_builtin_fits_keyword(key) or key in known):
                    cards.append([key, val, comment])

            if len(cards):
                properties.put_value(["extra_fits", hdu.name, "header"], cards, tree)

            if hdu not in known_datas:
                if hdu.data is not None:
                    properties.put_value(["extra_fits", hdu.name, "data"], hdu.data, tree)


def _load_history(hdulist, tree):
    try:
        hdu = get_hdu(hdulist, 0)
    except AttributeError:
        return

    header = hdu.header
    if "HISTORY" not in header:
        return

    history = tree["history"] = {"entries": []}

    for entry in header["HISTORY"]:
        history["entries"].append(HistoryEntry({"description": entry}))


def from_fits(
    hdulist, schema, context, ignore_unrecognized_tag=False, ignore_missing_extensions=False
):
    """
    Read model information from a FITS HDU list.

    Parameters
    ----------
    hdulist : astropy.io.fits.HDUList
        The FITS HDUList
    schema : dict
        The schema defining the ASDF > FITS_KEYWORD, FITS_HDU mapping.
    context : DataModel
        The `DataModel` to update
    ignore_unrecognized_tag : bool, optional
        If `True`, ignore unrecognized tags in the ASDF file.
        If `False`, raise an error when an unrecognized tag is found.
    ignore_missing_extensions : bool, optional
        If `True`, ignore missing extensions in the ASDF file.
        If `False`, raise an error when an extension is missing.

    Returns
    -------
    asdf.AsdfFile
        The ASDF file object
    """
    try:
        ff = from_fits_asdf(
            hdulist,
            ignore_missing_extensions=ignore_missing_extensions,
            ignore_unrecognized_tag=ignore_unrecognized_tag,
        )
    except Exception as exc:
        raise exc.__class__("ERROR loading embedded ASDF: " + str(exc)) from exc

    # Determine whether skipping the FITS loading can be done.
    skip_fits_update = _can_skip_fits_update(hdulist, ff, context)

    known_keywords, known_datas = _load_from_schema(
        hdulist, schema, ff.tree, context, skip_fits_update=skip_fits_update
    )
    if not skip_fits_update:
        _load_extra_fits(hdulist, known_keywords, known_datas, ff.tree)

    _load_history(hdulist, ff.tree)

    return ff


def from_fits_asdf(
    hdulist, ignore_unrecognized_tag=False, ignore_missing_extensions=False, **kwargs
):
    """
    Open the ASDF extension from a FITS HDUlist.

    Parameters
    ----------
    hdulist : astropy.io.fits.HDUList
        The FITS HDUList
    ignore_unrecognized_tag : bool
        When `True`, ignore unrecognized tags in the ASDF file.
        When `False`, raise an error when an unrecognized tag is found.
    ignore_missing_extensions : bool
        When `True`, ignore missing extensions in the ASDF file.
        When `False`, raise an error when an extension is missing.
    **kwargs : dict
        Additional keyword arguments to pass to `asdf.open`.
        Usage of kwargs is deprecated and will be removed in a future version.

    Returns
    -------
    asdf.AsdfFile
        The ASDF file object
    """
    try:
        asdf_extension = hdulist[_ASDF_EXTENSION_NAME]
    except (KeyError, IndexError, AttributeError):
        # This means there is no ASDF extension
        return asdf.AsdfFile(
            ignore_unrecognized_tag=ignore_unrecognized_tag,
        )

    generic_file = generic_io.get_file(io.BytesIO(asdf_extension.data), mode="rw")
    af = asdf.open(
        generic_file,
        ignore_unrecognized_tag=ignore_unrecognized_tag,
        ignore_missing_extensions=ignore_missing_extensions,
        **kwargs,
    )
    # map hdulist to blocks here
    _map_hdulist_to_arrays(hdulist, af)
    return af


def _map_hdulist_to_arrays(hdulist, af):
    def callback(node):
        if (
            isinstance(node, NDArrayType)
            and isinstance(node._source, str)
            and node._source.startswith(_FITS_SOURCE_PREFIX)
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

    # don't assign to af.tree to avoid an extra validation
    af._tree = treeutil.walk_and_modify(af.tree, callback)


def from_fits_hdu(hdu, schema):
    """
    Read the data from a FITS HDU into a numpy ndarray.

    Parameters
    ----------
    hdu : astropy.io.fits.hdu.base._BaseHDU
        The FITS HDU
    schema : dict
        The schema for the data

    Returns
    -------
    data : numpy.ndarray
        The data from the FITS HDU
    """
    data = hdu.data

    # Save the column listeners for possible restoration
    if hasattr(data, "_coldefs"):
        listeners = data._coldefs._listeners
    else:
        listeners = None

    # Cast array to type mentioned in schema
    data = properties._cast(data, schema)

    # Casting a table loses the column listeners, so restore them
    if listeners is not None:
        data._coldefs._listeners = listeners

    return data


def _can_skip_fits_update(hdulist, asdf_struct, context):
    """
    Ensure all conditions for skipping FITS updating are true.

    Returns True if either 1) the FITS hash in the asdf structure matches the input
    FITS structure. Or 2) skipping has been explicitly asked for in `skip_fits_update`.

    Parameters
    ----------
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
    # Need an already existing ASDF. If not, cannot skip.
    if not len(asdf_struct.tree):
        log.debug("No ASDF information found. Cannot skip updating from FITS headers.")
        return False

    # Ensure model types match
    hdulist_model_type = util.get_model_type(hdulist)
    if hdulist_model_type != context.__class__.__name__:
        log.debug(
            f"Input model type {hdulist_model_type} does not match the"
            f" requested model {type(context)}."
            " Cannot skip updating from FITS headers."
        )
        return False

    # Check for FITS hash and compare to current. If equal, automatically skip.
    if asdf_struct.tree.get(FITS_HASH_KEY, None) is not None:
        if asdf_struct.tree[FITS_HASH_KEY] == fits_hash(hdulist):
            log.debug("FITS hash matches. Skipping FITS updating.")
            return True

    # If all else fails, run fits_update
    return False


def fits_hash(hdulist):
    """
    Calculate a hash based on all HDU headers.

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
        warnings.simplefilter("ignore", AstropyWarning)
        fits_hash.update("".join(str(hdu.header) for hdu in hdulist if hdu.name != "ASDF").encode())
    return fits_hash.hexdigest()


def _get_short_doc(schema):
    title = schema.get("title", None)
    description = schema.get("description", None)
    if description is None:
        description = title or ""
    else:
        if title is not None:
            description = title + "\n\n" + description
    return description.partition("\n")[0]
