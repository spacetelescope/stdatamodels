"""
Various utility functions and data types
"""

import copy
import os

import numpy as np
from numpy.lib.recfunctions import merge_arrays
from astropy.io import fits
import asdf
from asdf import treeutil

try:
    from asdf.treeutil import RemoveNode
except ImportError:
    # Prior to asdf 2.8, None was used to indicate
    # that a node should be removed.
    RemoveNode = None

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def gentle_asarray(a, dtype, allow_extra_columns=False):
    """
    Convert ``a`` to dtype ``dtype`` ignoring case differences in
    dtype field (column) names for structured arrays (tables).

    When name conflicts occur (the cases differ) the name from
    ``dtype`` will be used.

    Parameters
    ----------

    a : np.ndarray
        Array which will be converted to the new dtype.

    dtype : np.dtype
        The dtype of the new array.

    Returns
    -------

    new_array : np.ndarray
        Array converted to the new dtype.
    """
    if isinstance(dtype, np.dtype):
        out_dtype = copy.copy(dtype)
    else:
        out_dtype = np.dtype(dtype)

    if not isinstance(a, np.ndarray):
        try:
            a = np.asarray(a, dtype=out_dtype)
        except Exception:
            raise ValueError("Can't convert {0!s} to ndarray".format(type(a)))
        return a
    in_dtype = a.dtype

    # Non-table array
    if in_dtype.fields is None and out_dtype.fields is None:
        if np.can_cast(in_dtype, out_dtype, 'equiv'):
            return a
        else:
            return _safe_asanyarray(a, out_dtype)

    # one of these dtypes does not have fields
    if in_dtype.fields is None or out_dtype.fields is None:
        return _safe_asanyarray(a, out_dtype)

    # this function should not handle nested structured dtypes
    # as they aren't supported by FITS_rec and not handled well
    # by merge_arrays below (which currently flattens the dtype)
    for dt in (in_dtype, out_dtype):
        for n in dt.names:
            if dt[n].names is not None:
                msg = f"gentle_asarray does not support nested structured dtypes: {dt}"
                raise ValueError(msg)

    # When a FITS file includes a pseudo-unsigned-int column, astropy will return
    # a FITS_rec with an incorrect table dtype.  The following code rebuilds
    # in_dtype from the individual fields, which are correctly labeled with an
    # unsigned int dtype.
    # We can remove this once the issue is resolved in astropy:
    # https://github.com/astropy/astropy/issues/8862
    if isinstance(a, fits.fitsrec.FITS_rec):
        a.dtype = rebuild_fits_rec_dtype(a)
        in_dtype = a.dtype

    if in_dtype == out_dtype:
        return a

    # check if names match (ignoring case)
    in_lower_names = [n.lower() for n in in_dtype.names]
    out_lower_names = [n.lower() for n in out_dtype.names]
    if in_lower_names == out_lower_names:
        in_subdtypes = [in_dtype[n] for n in in_dtype.names]
        out_subdtypes = [out_dtype[n] for n in out_dtype.names]
        if in_subdtypes == out_subdtypes:
            return a.view(dtype=out_dtype)
        else:
            # else, use asanyarray and copy
            return _safe_asanyarray(a, out_dtype)

    # names don't match
    # check if names match but the order is incorrect
    if set(out_lower_names) == set(in_lower_names):
        # all the columns exist but they are in the wrong order
        # reorder the columns, the names might differ in case
        reordered_names = sorted(in_dtype.names, key=lambda n: out_lower_names.index(n.lower()))
        reordered_array = merge_arrays([a[n] for n in reordered_names], flatten=True)
        reordered_subdtypes = [reordered_array.dtype[n] for n in reordered_array.dtype.names]
        out_subdtypes = [out_dtype[n] for n in out_dtype.names]
        if reordered_subdtypes == out_subdtypes:
            return reordered_array.view(out_dtype)
        else:
            return _safe_asanyarray(reordered_array, out_dtype)

    # if extra columns are not allowed or they are (and the required columns are missing)
    # then raise an exception
    if not allow_extra_columns or (not set(out_lower_names).issubset(in_lower_names)):
        # try to match the old error message
        raise ValueError(
            "Column names don't match schema. "
            "Schema has {0}. Data has {1}".format(
                str(set(out_lower_names).difference(set(in_lower_names))),
                str(set(in_lower_names).difference(set(out_lower_names)))))

    # construct new dtype with required columns at start
    # in_dtype vs out_dtype
    # - might have inconsequential (since fitsrec is used) name differences
    # - might have dtype differences (requiring _safe_asanyarray)
    # - in_dtype will have more columns (since we've handled everything else above)
    # if the first set of columns match (by name and dtype) the required dtype, return the array
    n_required = len(out_dtype)
    if in_dtype.descr[:n_required] == out_dtype.descr:
        return a

    # if the names of the first n_required columns match the columns
    if in_lower_names[:n_required] == out_lower_names:
        in_subdtypes = [in_dtype[n] for n in in_dtype.names]
        out_subdtypes = [out_dtype[n] for n in out_dtype.names]
        new_dtype = copy.copy(in_dtype)
        new_dtype.names = tuple(out_dtype.names + in_dtype.names[n_required:])
        if in_subdtypes[:n_required] == out_subdtypes:
            return a.view(dtype=new_dtype)
        else:
            new_dtype = np.dtype(out_dtype.descr + new_dtype.descr[len(out_dtype.descr):])
            return _safe_asanyarray(a, new_dtype)

    # reorder columns so required columns are first
    required_names = [n for n in in_dtype.names if n.lower() in out_lower_names]
    required_names.sort(key=lambda n: out_lower_names.index(n.lower()))
    extra_names = [n for n in in_dtype.names if n.lower() not in out_lower_names]
    names_ordered = tuple(required_names + extra_names)
    reordered_array = merge_arrays([a[n] for n in names_ordered], flatten=True)
    reordered_array.dtype.names = names_ordered

    extra_dtype_descr = [(n, in_dtype[n]) for n in extra_names]
    new_dtype = np.dtype(out_dtype.descr + extra_dtype_descr)

    # check that required columns have the correct dtype
    reordered_subdtypes = [reordered_array.dtype[n] for n in reordered_array.dtype.names]
    out_subdtypes = [out_dtype[n] for n in out_dtype.names]
    if reordered_subdtypes[:n_required] == out_subdtypes:
        return reordered_array.view(new_dtype)
    return _safe_asanyarray(reordered_array, new_dtype)


def _safe_asanyarray(a, dtype):
    if isinstance(a, fits.fitsrec.FITS_rec):
        if any(c.bzero is not None for c in a.columns):
            # Due to an issue in astropy, it's not safe to directly cast
            # a FITS_rec with a pseudo-unsigned column.
            # See https://github.com/astropy/astropy/issues/12112
            result = np.zeros(a.shape, dtype=dtype)
            for old_col, new_col in zip(a.dtype.names, result.dtype.names):
                result[new_col] = a[old_col]
            return result

    result = np.asanyarray(a, dtype=dtype)
    if isinstance(result, fits.fitsrec.FITS_rec) and isinstance(a, fits.fitsrec.FITS_rec):
        for column in result.columns:
            name = column.name
            try:
                matching_column = a.columns[name]
            except KeyError:
                continue
            result.columns[name].unit = matching_column.unit
    return result


def create_history_entry(description, software=None):
    """
    Create a HistoryEntry object.

    Parameters
    ----------
    description : str
        Description of the change.
    software : dict or list of dict
        A description of the software used.  It should not include
        asdf itself, as that is automatically notated in the
        `asdf_library` entry.

        Each dict must have the following keys:

        ``name``: The name of the software
        ``author``: The author or institution that produced the software
        ``homepage``: A URI to the homepage of the software
        ``version``: The version of the software

    Examples
    --------
    >>> soft = {'name': 'jwreftools', 'author': 'STSCI', \
                'homepage': 'https://github.com/spacetelescope/jwreftools', 'version': "0.7"}
    >>> entry = create_history_entry(description="HISTORY of this file", software=soft)

    """
    from asdf.tags.core import Software, HistoryEntry
    import datetime

    if isinstance(software, list):
        software = [Software(x) for x in software]
    elif software is not None:
        software = Software(software)

    dt = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    entry = HistoryEntry({
        'description': description,
        'time': dt
    })

    if software is not None:
        entry['software'] = software
    return entry


def get_envar_as_boolean(name, default=False):
    """Interpret an environmental as a boolean flag

    Truth is any numeric value that is not 0 or
    any of the following case-insensitive strings:

    ('true', 't', 'yes', 'y')

    Parameters
    ----------
    name : str
        The name of the environmental variable to retrieve

    default : bool
        If the environmental variable cannot be accessed, use as the default.
    """
    truths = ('true', 't', 'yes', 'y')
    falses = ('false', 'f', 'no', 'n')
    if name in os.environ:
        value = os.environ[name]
        try:
            value = bool(int(value))
        except ValueError:
            value_lowcase = value.lower()
            if value_lowcase not in truths + falses:
                raise ValueError(f'Cannot convert value "{value}" to boolean unambiguously.')
            return value_lowcase in truths
        return value

    log.debug(f'Environmental "{name}" cannot be found. Using default value of "{default}".')
    return default


def get_model_type(init):
    """
    Fetch the model type string from the underlying file object.

    Parameters
    ----------
    init : asdf.AsdfFile or astropy.io.fits.HDUList

    Returns
    -------
    str or None
    """
    if isinstance(init, asdf.AsdfFile):
        if "meta" in init:
            return init["meta"].get("model_type")
        else:
            return None
    elif isinstance(init, fits.HDUList):
        return init[0].header.get("DATAMODL")
    else:
        raise TypeError(f"Unhandled init type: {init.__class__.__name__}")


def remove_none_from_tree(tree):
    """
    Remove None values from a tree.  Both dictionary keys
    and list indices with None values will be removed.

    Parameters
    ----------
    tree : object
        The root node of the tree.

    Returns
    -------
    object
        Modified tree.
    """

    def _remove_none(node):
        if node is None:
            return RemoveNode
        else:
            return node

    return treeutil.walk_and_modify(tree, _remove_none)


def convert_fitsrec_to_array_in_tree(tree):
    def _convert_fitsrec(node):
        if isinstance(node, fits.FITS_rec):
            return _fits_rec_to_array(node)
        else:
            return node
    return treeutil.walk_and_modify(tree, _convert_fitsrec)


def rebuild_fits_rec_dtype(fits_rec):
    dtype = fits_rec.dtype
    new_dtype = []
    for field_name in dtype.fields:
        table_dtype = dtype[field_name]
        shape = table_dtype.shape
        if shape:
            table_dtype = table_dtype.base
        field_dtype = fits_rec.field(field_name).dtype
        if np.issubdtype(table_dtype, np.signedinteger) and np.issubdtype(field_dtype, np.unsignedinteger):
            new_dtype.append((field_name, field_dtype, shape))
        else:
            new_dtype.append((field_name, table_dtype, shape))
    return np.dtype((np.record, new_dtype))


def _fits_rec_to_array(fits_rec):
    bad_columns = [n for n in fits_rec.dtype.fields if np.issubdtype(fits_rec[n].dtype, np.unsignedinteger)]
    if not len(bad_columns):
        return fits_rec.view(np.ndarray)
    new_dtype = rebuild_fits_rec_dtype(fits_rec)
    arr = np.asarray(fits_rec, new_dtype).copy()
    for name in bad_columns:
        arr[name] = fits_rec[name]
    return arr
