"""Various utility functions and data types."""

from collections.abc import Sequence
import warnings
from pathlib import Path
import logging
from asdf.tagged import TaggedString

import io
import asdf

import numpy as np
from astropy.io import fits
from stdatamodels import filetype, fits_support
from stdatamodels.model_base import _FileReference
from stdatamodels.exceptions import NoTypeWarning
import stdatamodels.jwst.datamodels as dm


__all__ = ["open", "is_association"]


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def open(init=None, guess=True, **kwargs):  # noqa: A001
    """
    Create a DataModel from a number of different types.

    Parameters
    ----------
    init : shape tuple, file path, astropy.io.fits.HDUList, numpy array, dict, None

        - None: A default data model with no shape

        - shape tuple: Initialize with empty data of the given shape

        - file path: Initialize from the given file (FITS, JSON or ASDF)

        - astropy.io.fits.HDUList: Initialize from the given
          `~astropy.io.fits.HDUList`

        - A numpy array: A new model with the data array initialized
          to what was passed in.

        - dict: The object model tree for the data model

    guess : bool
        Guess as to the model type if the model type is not specifically known from the file.
        If not guess and the model type is not explicit, raise a TypeError.
    **kwargs
        Additional keyword arguments passed to the DataModel constructor.  Some arguments
        are general, others are file format-specific.  Arguments of note are:

        - General

           validate_arrays : bool
             If `True`, arrays will be validated against ndim, max_ndim, and datatype
             validators in the schemas.

    Returns
    -------
    DataModel
        A new model instance.
    """
    from . import model_base

    if "memmap" in kwargs:
        warnings.warn(
            "Memory mapping is no longer supported; memmap is hard-coded to False "
            "and the keyword argument no longer has any effect.",
            DeprecationWarning,
            stacklevel=2,
        )
        kwargs.pop("memmap")

    # Initialize variables used to select model class

    hdulist = {}
    shape = ()
    file_name = None
    file_to_close = None

    # Get special cases for opening a model out of the way
    # all special cases return a model if they match

    if init is None:
        return model_base.JwstDataModel(None, **kwargs)

    elif isinstance(init, model_base.JwstDataModel):
        # Copy the object so it knows not to close here
        return init.__class__(init, **kwargs)

    elif isinstance(init, (str, Path)):
        # If given a string, presume its a file path.

        file_name = Path(init).name
        file_type = filetype.check(init)

        if file_type == "fits":
            hdulist = fits.open(init, memmap=False)
            file_to_close = hdulist

        elif file_type == "asn":
            # Read the file as an association / model container
            try:
                from jwst.datamodels import ModelContainer
            except ImportError as err:
                raise ValueError(
                    "Cannot open an association file without the jwst package installed"
                ) from err

            return ModelContainer(init, **kwargs)

        elif file_type == "asdf":
            asdffile = asdf.open(init, memmap=False)

            # Detect model type, then get defined model, and call it.
            new_class = _class_from_model_type(asdffile)
            if new_class is None:
                # No model class found, so return generic DataModel.
                model = model_base.JwstDataModel(asdffile, **kwargs)
                _handle_missing_model_type(model, file_name)
            else:
                model = new_class(asdffile, **kwargs)

            model._file_references.append(_FileReference(asdffile))

            return model

    elif isinstance(init, tuple):
        for item in init:
            if not isinstance(item, int):
                raise ValueError("shape must be a tuple of ints")  # noqa: TRY004
        shape = init

    elif isinstance(init, np.ndarray):
        shape = init.shape

    elif isinstance(init, fits.HDUList):
        hdulist = init

    elif is_association(init) or isinstance(init, Sequence) and not isinstance(init, bytes):
        try:
            from jwst.datamodels import ModelContainer
        except ImportError as err:
            raise ValueError(
                "Cannot open an association without the jwst package installed"
            ) from err

        return ModelContainer(init, **kwargs)

    else:
        raise TypeError(f"Unsupported type for init argument to open {type(init)}")

    # If we have it, determine the shape from the science hdu
    if hdulist:
        # So we don't need to open the image twice
        init = hdulist
        info = init.fileinfo(0)
        if info is not None:
            file_name = info.get("filename")

        try:
            hdu = hdulist[("SCI", 1)]
        except (KeyError, NameError):
            shape = ()
        else:
            if hasattr(hdu, "shape"):
                shape = hdu.shape
            else:
                shape = ()

    # First try to get the class name from the primary header
    new_class = _class_from_model_type(hdulist)
    has_model_type = new_class is not None
    if not guess and not has_model_type:
        if file_to_close is not None:
            file_to_close.close()
        raise TypeError("Model type is not specifically defined and guessing has been disabled.")

    # Special handling for ramp files for backwards compatibility
    if new_class is None:
        new_class = _class_from_ramp_type(hdulist, shape)

    # Or get the class from the reference file type and other header keywords
    if new_class is None:
        new_class = _class_from_reftype(hdulist, shape)

    # Or Get the class from the shape
    if new_class is None:
        new_class = _class_from_shape(hdulist, shape)

    # Throw an error if these attempts were unsuccessful
    if new_class is None:
        raise TypeError("Can't determine datamodel class from argument to open")

    # Log a message about how the model was opened
    if file_name:
        log.debug(f"Opening {file_name} as {new_class}")
    else:
        log.debug(f"Opening as {new_class}")

    # Actually open the model
    try:
        model = new_class(init, **kwargs)
    except Exception:
        if file_to_close is not None:
            file_to_close.close()
        raise

    # Close the hdulist if we opened it
    if file_to_close is not None:
        # TODO: We need a better solution than messing with DataModel
        # internals.
        model._file_references.append(_FileReference(file_to_close))

    if not has_model_type:
        _handle_missing_model_type(model, file_name)

    return model


def _handle_missing_model_type(model, file_name):
    if file_name:
        class_name = model.__class__.__name__.split(".")[-1]
        warnings.warn(
            f"model_type not found. Opening {file_name} as a {class_name}",
            NoTypeWarning,
            stacklevel=2,
        )
    try:
        delattr(model.meta, "model_type")
    except AttributeError:
        pass


def _class_from_model_type(init):
    """
    Get the model type from the primary header, lookup to get class.

    Parameters
    ----------
    init : AsdfFile or HDUList
        The input metadata

    Returns
    -------
    new_class : str or None
        The class name.
    """
    from . import _defined_models as defined_models

    if init:
        if isinstance(init, fits.hdu.hdulist.HDUList):
            primary = init[0]
            model_type = primary.header.get("DATAMODL")
        elif isinstance(init, asdf.AsdfFile):
            try:
                model_type = init.tree["meta"]["model_type"]
            except KeyError:
                model_type = None

        if model_type is None:
            new_class = None
        else:
            new_class = defined_models.get(model_type)
    else:
        new_class = None

    return new_class


def _class_from_ramp_type(hdulist, shape):
    """
    Check to see if file is ramp file.

    Parameters
    ----------
    hdulist : HDUList
        The HDUList object
    shape : tuple
        The shape of the data

    Returns
    -------
    RampModel
        The model class to use
    """
    if not hdulist:
        new_class = None
    else:
        if len(shape) == 4:
            try:
                hdulist["DQ"]
            except KeyError:
                from . import ramp

                new_class = ramp.RampModel
            else:
                new_class = None
        else:
            new_class = None

    return new_class


def _class_from_reftype(hdulist, shape):
    """
    Get the class name from the reftype and other header keywords.

    Parameters
    ----------
    hdulist : HDUList
        The HDUList object
    shape : tuple
        The shape of the data

    Returns
    -------
    ReferenceDataModel
        The model class to use
    """
    if not hdulist:
        new_class = None

    else:
        primary = hdulist[0]
        reftype = primary.header.get("REFTYPE")
        if reftype is None:
            new_class = None

        else:
            from . import reference

            if len(shape) == 0:
                new_class = reference.ReferenceFileModel
            elif len(shape) == 2:
                new_class = reference.ReferenceImageModel
            elif len(shape) == 3:
                new_class = reference.ReferenceCubeModel
            elif len(shape) == 4:
                new_class = reference.ReferenceQuadModel
            else:
                new_class = None

    return new_class


def _class_from_shape(hdulist, shape):
    """
    Get the class name from the shape.

    Parameters
    ----------
    hdulist : HDUList
        The HDUList object
    shape : tuple
        The shape of the data

    Returns
    -------
    DataModel
        The model class to use
    """
    if len(shape) == 0:
        from . import model_base

        new_class = model_base.JwstDataModel
    elif len(shape) == 4:
        from . import quad

        new_class = quad.QuadModel
    elif len(shape) == 3:
        from . import cube

        new_class = cube.CubeModel
    elif len(shape) == 2:
        try:
            hdulist[("SCI", 2)]
        except (KeyError, NameError):
            # It's an ImageModel
            from . import image

            new_class = image.ImageModel
        else:
            # It's a MultiSlitModel
            from . import multislit

            new_class = multislit.MultiSlitModel
    else:
        new_class = None

    return new_class


def is_association(asn_data):
    """
    Test if an object is an association by checking for required fields.

    Parameters
    ----------
    asn_data : object
        The object to test

    Returns
    -------
    bool
        True if `asn_data` is an association
    """
    if isinstance(asn_data, dict):
        if "asn_id" in asn_data and "asn_pool" in asn_data:
            return True
    return False


def _convert_tagged_strings(tree):
    """Convert TaggedString to string for all values of nested dict."""

    def recurse(tree):
        for key, val in tree.items():
            if key == "wcs":
                # Skip the WCS object because it is recursive
                continue
            if isinstance(val, TaggedString):
                tree[key] = str(val)
            elif isinstance(val, dict):
                recurse(val)

    recurse(tree)


def _to_flat_dict(tree):
    """
    Convert a tree to a flat dictionary.

    Lists are converted to dictionaries with keys equal to their indices as strings.
    For example, a MultiSlitModel with two slits slits will have the attributes::

        "slits.0.name", "slits.1.name", etc.

    Parameters
    ----------
    tree : dict
        The input tree to flatten

    Returns
    -------
    dict
        The flattened dictionary
    """
    flat_dict = {}

    def recurse(subtree, path):
        if isinstance(subtree, dict):
            for key, val in subtree.items():
                if key == "wcs":
                    # Skip the WCS object because it is recursive
                    continue
                current_path = path + [key]
                recurse(val, current_path)
        elif isinstance(subtree, (list, tuple)):
            for i, item in enumerate(subtree):
                indexed_key = f"{path[-1]}.{i}" if path else str(i)
                recurse(item, path[:-1] + [indexed_key])
        else:
            flat_dict[".".join(path)] = subtree

    recurse(tree, [])
    return flat_dict


def _retrieve_schema(model_type):
    """Load schema for the input model type."""  # numpydoc ignore=RT01
    try:
        schema_url = getattr(dm, model_type).schema_url
    except AttributeError:
        raise ValueError(f"Model type {model_type} not found.") from None
    return asdf.schema.load_schema(schema_url, resolve_references=True)


def read_metadata(fname, model_type=None, flatten=True):
    """
    Load a metadata tree from a file without loading the entire datamodel into memory.

    The metadata dictionary will be returned in a flat format by default,
    such that each key is a dot-separated name. For example, the schema element
    `meta.observation.date` will end up in the result as::

        ("meta.observation.date": "2012-04-22T03:22:05.432")

    If `flatten` is set to False, the metadata will be returned as a nested
    dictionary, with the keys being the schema elements.

    For FITS files, the output dictionary contains all metadata attributes
    that are present in the FITS header and mapped to a schema element, as well
    as any extra attributes that are present in the ASDF extension of the FITS file.
    (If a header keyword is not mapped to a schema element, it will not be included.)

    For ASDF files, the output dictionary simply contains the entire ASDF tree.

    WCS objects are not loaded, as they can be recursive and can be large.

    .. warning::

        This function entirely bypasses schema validation. Although validation
        is done when saving a datamodel to file, if a model is modified and then
        saved with something other than datamodels.save (e.g. astropy.fits.writeto),
        the schema will not be validated and invalid data could be loaded here.

    Parameters
    ----------
    fname : str or Path
        Path to a JWSTDataModel file.
    model_type : str, optional
        The model type used to figure out which schema to load. If not provided,
        the model type will be determined from the file's header information
        ("DATAMODL" keyword for FITS files). Has no effect for ASDF input.
    flatten : bool, optional
        If True, the metadata will be returned as a flat dictionary. If False,
        the metadata will be returned as a nested dictionary. Default is True.

    Returns
    -------
    dict
        The metadata tree.
    """
    if not isinstance(fname, (Path, str)):
        raise TypeError("Input must be a file path.")

    ext = filetype.check(str(fname))
    if ext == "fits":
        with fits.open(fname) as hdulist:
            bs = io.BytesIO(hdulist["ASDF"].data.tobytes())
            tree = asdf.util.load_yaml(bs)
            if model_type is None:
                model_type = hdulist[0].header["DATAMODL"]
            schema = _retrieve_schema(model_type)

            # hack to turn off validation without needing an entire datamodel object
            class PlaceholderCtx:
                def __init__(self):
                    self._validate_on_assignment = False

            context = PlaceholderCtx()

            fits_support._load_from_schema(
                hdulist,
                schema,
                tree,
                context,
                skip_fits_update=False,
                ignore_arrays=True,
                keep_unknown=False,
            )

    elif ext == "asdf":
        tree = asdf.util.load_yaml(fname, tagged=True)
        _convert_tagged_strings(tree)

    else:
        raise ValueError(f"File type {ext} not supported. Must be FITS or ASDF.")

    # custom handling of cal_logs object to ensure it ends up as a single string
    _convert_cal_logs_to_string(tree)

    if flatten:
        return _to_flat_dict(tree)
    return tree


def _convert_cal_logs_to_string(tree):
    """
    Convert cal_logs dictionary into a single string.

    Output format looks similar to what was originally printed to the logs,
    e.g. a newline-separated log

    Parameters
    ----------
    tree : dict
        The input tree containing the cal_logs dictionary
    """
    if "cal_logs" not in tree.keys():
        return

    cal_str = ""
    for _key, val in tree["cal_logs"].items():
        if isinstance(val, dict):
            val = "\n".join([f"{k}: {v}" for k, v in val.items()])
        elif isinstance(val, list):
            val = "\n".join([str(v) for v in val])
        cal_str += f"{val}\n"
    tree["cal_logs"] = cal_str
