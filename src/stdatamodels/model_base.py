"""Data model class hierarchy."""

import copy
import datetime
import os
from pathlib import Path, PurePath
import sys
import warnings
import functools

import numpy as np

from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS

import asdf
from asdf.tags.core import NDArrayType
from asdf import AsdfFile
from asdf import schema as asdf_schema

from . import filetype
from . import fits_support
from . import properties
from . import schema as mschema
from . import validate
from .util import convert_fitsrec_to_array_in_tree, get_envar_as_boolean, remove_none_from_tree

from .history import HistoryList


# This minimal schema creates metadata fields that
# are accessed to be available by the core DataModel code.
_DEFAULT_SCHEMA = {
    "properties": {
        "meta": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                },
                "model_type": {
                    "type": "string",
                },
            },
        },
    },
}


class DataModel(properties.ObjectNode):
    """Base class of all of the data models."""

    schema_url = None
    """
    The schema URI to validate the model against.  If
    None, only basic validation of required metadata
    properties (filename, model_type) will occur.
    """

    def __init__(
        self,
        init=None,
        schema=None,
        pass_invalid_values=None,
        strict_validation=None,
        validate_on_assignment=None,
        validate_arrays=False,
        ignore_missing_extensions=True,
        **kwargs,
    ):
        """
        Initialize a data model.

        Parameters
        ----------
        init : str, tuple, `~astropy.io.fits.HDUList`, ndarray, dict, None

            - None : Create a default data model with no shape.

            - tuple : Shape of the data array.
              Initialize with empty data array with shape specified by the.

            - file path: Initialize from the given file (FITS or ASDF)

            - readable file object: Initialize from the given file
              object

            - `~astropy.io.fits.HDUList` : Initialize from the given
              `~astropy.io.fits.HDUList`.

            - A numpy array: Used to initialize the data array

            - dict: The object model tree for the data model

        schema : dict, str (optional)
            Tree of objects representing a JSON schema, or string naming a schema.
            The schema to use to understand the elements on the model.
            If not provided, the schema associated with this class
            will be used.

        pass_invalid_values : bool or None
            If `True`, values that do not validate the schema
            will be added to the metadata. If `False`, they will be set to `None`.
            If `None`, value will be taken from the environmental PASS_INVALID_VALUES.
            Otherwise the default value is `False`.

        strict_validation : bool or None
            If `True`, schema validation errors will generate
            an exception. If `False`, they will generate a warning.
            If `None`, value will be taken from the environmental STRICT_VALIDATION.
            Otherwise, the default value is `False`.

        validate_on_assignment : bool or None
            Defaults to 'None'.
            If `None`, value will be taken from the environmental VALIDATE_ON_ASSIGNMENT,
            defaulting to 'True' if  no environment variable is set.
            If 'True', attribute assignments are validated at the time of assignment.
            Validation errors generate warnings and values will be set to `None`.
            If 'False', schema validation occurs only once at the time of write.
            Validation errors generate warnings.

        validate_arrays : bool
            If `True`, arrays will be validated against ndim, max_ndim, and datatype
            validators in the schemas.

        ignore_missing_extensions : bool
            When `False`, raise warnings when a file is read that
            contains metadata about extensions that are not available.
            Defaults to `True`.

        **kwargs
            Additional keyword arguments passed to lower level functions. These arguments
            are generally file format-specific.
        """
        if "memmap" in kwargs:
            warnings.warn(
                "Memory mapping is no longer supported; memmap is hard-coded to False "
                "and the keyword argument no longer has any effect.",
                DeprecationWarning,
                stacklevel=2,
            )
            kwargs.pop("memmap")

        # Override value of validation parameters if not explicitly set.
        if pass_invalid_values is None:
            pass_invalid_values = get_envar_as_boolean("PASS_INVALID_VALUES", False)
        self._pass_invalid_values = pass_invalid_values
        if strict_validation is None:
            strict_validation = get_envar_as_boolean("STRICT_VALIDATION", False)
        if validate_on_assignment is None:
            validate_on_assignment = get_envar_as_boolean("VALIDATE_ON_ASSIGNMENT", True)
        self._strict_validation = strict_validation
        self._ignore_missing_extensions = ignore_missing_extensions
        self._validate_on_assignment = validate_on_assignment
        self._validate_arrays = validate_arrays

        kwargs.update({"ignore_missing_extensions": ignore_missing_extensions})

        # Load the schema files
        if schema is None:
            if self.schema_url is None:
                schema = _DEFAULT_SCHEMA
            else:
                # Create an AsdfFile so we can use its resolver for loading schemas
                schema = asdf_schema.load_schema(self.schema_url, resolve_references=True)

        self._schema = mschema.merge_property_trees(schema)

        # Provide the object as context to other classes and functions
        self._parent = None

        # Initialize with an empty AsdfFile instance as this is needed for
        # reading in FITS files where validate._check_value() gets called, and
        # ctx needs to have an _asdf attribute.
        self._asdf = AsdfFile()

        # Determine what kind of input we have (init) and execute the
        # proper code to initialize the model
        self._file_references = []
        is_array = False
        is_shape = False
        shape = None

        if init is None:
            asdffile = AsdfFile(
                ignore_unrecognized_tag=kwargs.get("ignore_unrecognized_tag", False)
            )

        elif isinstance(init, dict):
            asdffile = AsdfFile(
                ignore_unrecognized_tag=kwargs.get("ignore_unrecognized_tag", False)
            )
            # Don't pass init to AsdfFile as that triggers an extra validation
            # this can updated to AsdfFile(init, ...) when asdf 4.0 is the
            # minimum version.
            asdffile._tree = init

        elif isinstance(init, np.ndarray):
            asdffile = AsdfFile(
                ignore_unrecognized_tag=kwargs.get("ignore_unrecognized_tag", False)
            )

            shape = init.shape
            is_array = True

        elif isinstance(init, tuple):
            for item in init:
                if not isinstance(item, int):
                    raise ValueError("shape must be a tuple of ints")  # noqa: TRY004

            shape = init
            is_shape = True
            asdffile = AsdfFile(
                ignore_unrecognized_tag=kwargs.get("ignore_unrecognized_tag", False)
            )

        elif isinstance(init, DataModel):
            asdffile = None
            self.clone(self, init)
            if not isinstance(init, self.__class__):
                current_validate_arrays = self._validate_arrays
                self._validate_arrays = True
                self.validate()
                self._validate_arrays = current_validate_arrays
            return

        elif isinstance(init, AsdfFile):
            asdffile = init

        elif isinstance(init, fits.HDUList):
            init = self._migrate_hdulist(init)
            asdffile = fits_support.from_fits(init, self._schema, self._ctx, **kwargs)

        elif isinstance(init, (str, PurePath)):
            file_type = filetype.check(init)

            if file_type == "fits":
                hdulist = fits.open(init, memmap=False)
                self._file_references.append(_FileReference(hdulist))
                hdulist = self._migrate_hdulist(hdulist)
                asdffile = fits_support.from_fits(hdulist, self._schema, self._ctx, **kwargs)

            elif file_type == "asdf":
                asdffile = asdf.open(init, memmap=False, **kwargs)
                self._file_references.append(_FileReference(asdffile))
            else:
                # TODO handle json files as well
                raise OSError("File does not appear to be a FITS or ASDF file.")

        else:
            raise TypeError(f"Can't initialize datamodel using {str(type(init))}")

        # Initialize object fields as determined from the code above
        self._shape = shape
        self._instance = asdffile.tree
        self._asdf = asdffile

        # Initialize class dependent hidden fields
        self._no_asdf_extension = False

        # Instantiate the primary array of the image
        if is_array:
            primary_array_name = self.get_primary_array_name()
            if not primary_array_name:
                raise TypeError(
                    "Array passed to DataModel.__init__, but model "
                    "has no primary array in its schema"
                )
            setattr(self, primary_array_name, init)

        # If a shape has been given, initialize the primary array.
        if is_shape:
            primary_array_name = self.get_primary_array_name()
            if not primary_array_name:
                raise TypeError(
                    "Shape passed to DataModel.__init__, but model "
                    "has no primary array in its schema"
                )

            # Initialization occurs when the primary array is first
            # referenced. Do so now.
            getattr(self, primary_array_name)

        # initialize arrays from keyword arguments when they are present

        for attr, value in kwargs.items():
            if value is not None:
                subschema = properties._get_schema_for_property(self._schema, attr)
                if "datatype" in subschema:
                    setattr(self, attr, value)

        # Call hook that sets model properties
        self.on_init(init)

    def _migrate_hdulist(self, hdulist):
        """
        Migrate a hdulist for an old (incompatible) format to a new format.

        For example, say you have a file with a table that is missing a
        column that is now required. This method can be used to add the
        missing column to the old file.

        This method is only called when a datamodel is constructed using a
        HDUList or a string (not when the DataModel is cloned or created
        from an existing DataModel).

        The migration occurs prior to loading the ASDF extension.

        Parameters
        ----------
        hdulist : HDUList
            The opened hdulist that this method should possibly migrate.

        Returns
        -------
        migrated_hdulist : HDUList
            The migrated/updated hdulist (this can be identical to the
            input hdulist if no migration is needed).
        """
        return hdulist

    @property
    def _ctx(self):
        # self._ctx is a property to avoid reference cycle that would be
        # created if we set self._ctx = self
        # a reference cycle would make DataModel difficult to garbage
        # collect and could reopen the memory leak issues fixed in
        # https://github.com/spacetelescope/stdatamodels/pull/109
        return self

    @property
    def crds_observatory(self):
        """
        Get the CRDS observatory code for this model.

        Raises
        ------
        NotImplementedError
            Subclasses should override this method to return a str.
        """
        raise NotImplementedError(
            "The base DataModel class cannot be used to select best references"
        )

    def get_crds_parameters(self):
        """
        Get the parameters used by CRDS to select references for this model.

        Raises
        ------
        NotImplementedError
            Subclasses should override this method to return a dict.
        """
        raise NotImplementedError(
            "The base DataModel class cannot be used to select best references"
        )

    @property
    def _model_type(self):
        return self.__class__.__name__

    def __repr__(self):
        buf = ["<"]
        buf.append(self._model_type)

        if self.shape:
            buf.append(str(self.shape))

        try:
            filename = self.meta.filename
        except AttributeError:
            filename = None
        if filename:
            buf.append(" from ")
            buf.append(filename)
        buf.append(">")

        return "".join(buf)

    def __del__(self):
        """Ensure closure of resources when deleted."""
        self.close()

    @property
    def override_handle(self):
        """
        Identify in-memory models where a filepath would normally be used.

        Returns
        -------
        str
            A string that can be used to identify the model as an in-memory model.
        """
        # Arbitrary choice to look something like crds://
        return "override://" + self.__class__.__name__

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close all file references."""
        # This method is called by __del__, which may be invoked
        # even when the model failed to initialize.  Consequently,
        # we can't assume that any attributes have been set.
        if hasattr(self, "_file_references"):
            for file_reference in self._file_references:
                file_reference.decrement()
            # Discard the list in case close is called a second time.
            self._file_references.clear()

    @staticmethod
    def clone(target, source, deepcopy=False, memo=None):
        """
        Clone the contents of one model into another.

        Parameters
        ----------
        target : DataModel
            The model to clone into.
        source : DataModel
            The model to clone from.
        deepcopy : bool, optional
            If `True`, perform a deep copy of the source model.
            If `False`, perform a shallow copy.
        memo : dict, optional
            A dictionary to use as a memoization table for deep copy.
        """
        if deepcopy:
            instance = copy.deepcopy(source._instance, memo=memo)
            target._asdf = AsdfFile()
            # assign to private '_tree' to avoid validation caused
            # by either using AsdfFile(instance) or target._asdf = tree
            target._asdf._tree = instance
            target._instance = instance
        else:
            target._asdf = source._asdf
            target._instance = source._instance
            for file_reference in source._file_references:
                file_reference.increment()
                target._file_references.append(file_reference)

        target._shape = source._shape
        target._no_asdf_extension = source._no_asdf_extension

    def copy(self, memo=None):
        """
        Return a deep copy of this model.

        Parameters
        ----------
        memo : dict, optional
            A dictionary to use as a memoization table for deep copy.
        """
        result = self.__class__(
            init=None,
            pass_invalid_values=self._pass_invalid_values,
            strict_validation=self._strict_validation,
        )
        self.clone(result, self, deepcopy=True, memo=memo)
        return result

    __copy__ = __deepcopy__ = copy

    def validate(self):
        """Validate the model instance against its schema."""
        validate.value_change(str(self), self._instance, self._schema, self)

    @functools.wraps(asdf.AsdfFile.info)
    def info(self, *args, **kwargs):  # noqa: D102
        return self._asdf.info(**kwargs)

    @functools.wraps(asdf.AsdfFile.search)
    def search(self, *args, **kwargs):  # noqa: D102
        return self._asdf.search(*args, **kwargs)

    try:
        info.__doc__ = AsdfFile.info.__doc__
        search.__doc__ = AsdfFile.search.__doc__
    except AttributeError:
        pass

    def get_primary_array_name(self):
        """
        Retrieve the name of the "primary" array for this model.

        The primary array controls the size of other arrays that are implicitly created.
        If the schema has the "data" property, then this method returns "data".
        Otherwise, it returns an empty string.
        This is intended to be overridden in the subclasses if the
        primary array's name is not "data".

        Returns
        -------
        primary_array_name : str
            The name of the primary array.
        """
        if properties._find_property(self._schema, "data"):
            primary_array_name = "data"
        else:
            primary_array_name = ""
        return primary_array_name

    def on_init(self, init):
        """
        Customize model attributes at the end of ``__init__``.

        Parameters
        ----------
        init : object
            First argument to ``__init__``.
        """
        # if the input is from a file, set the filename attribute
        if isinstance(init, str):
            self.meta.filename = Path(init).name
        elif isinstance(init, fits.HDUList):
            info = init.fileinfo(0)
            if info is not None:
                filename = info.get("filename")
                if filename is not None:
                    self.meta.filename = Path(filename).name

        # store the data model type, if not already set
        klass = self.__class__.__name__
        if klass != "DataModel":
            if not self.meta.hasattr("model_type"):
                self.meta.model_type = klass

    def on_save(self, path=None):
        """
        Modify the model just before saving to disk.

        This hook can be used, for example, to update values in the metadata
        that are based on the content of the data.

        Override it in the subclass to make it do something, but don't
        forget to "chain up" to the base class, since it does things
        there, too.

        Parameters
        ----------
        path : str
            The path to the file that we're about to save to.
        """
        if isinstance(path, str):
            self.meta.filename = Path(path).name

        # Enforce model_type to be the actual type of model being saved.
        self.meta.model_type = self._model_type

        # DataModel considers None to be equivalent to missing node, but
        # asdf 2.8+ writes None as null values, so we need to remove
        # Nones before proceeding with the save.
        self._instance = remove_none_from_tree(self._instance)

    def save(self, path, dir_path=None, *args, **kwargs):
        """
        Save to either a FITS or ASDF file, depending on the path.

        Parameters
        ----------
        path : str or func
            File path to save to.
            If function, it takes one argument with is
            model.meta.filename and returns the full path string.
        dir_path : str
            Directory to save to. If not None, this will override
            any directory information in the `path`

        Returns
        -------
        output_path : str
            The file path the model was saved in.
        """
        if callable(path):
            path_head, path_tail = os.path.split(path(self.meta.filename))
        else:
            path_head, path_tail = os.path.split(path)
        ext = Path(path_tail).suffix
        if isinstance(ext, bytes):
            ext = ext.decode(sys.getfilesystemencoding())

        if dir_path:
            path_head = dir_path
        output_path = os.path.join(path_head, path_tail)  # noqa: PTH118

        # TODO: Support gzip-compressed FITS
        if ext == ".fits":
            # TODO: remove 'clobber' check once depreciated fully in astropy
            if "clobber" not in kwargs:
                kwargs.setdefault("overwrite", True)
            self.to_fits(output_path, *args, **kwargs)
        elif ext == ".asdf":
            self.to_asdf(output_path, *args, **kwargs)
        else:
            raise ValueError(f"unknown filetype {ext}")

        return output_path

    @staticmethod
    def open_asdf(init=None, ignore_unrecognized_tag=False, **kwargs):
        """
        Open an ASDF object from a filename or create a new ASDF object.

        Parameters
        ----------
        init : str, file object, `~asdf.AsdfFile`, dict
            - str : file path: initialize from the given file
            - readable file object: Initialize from the given file object
            - `~asdf.AsdfFile` : Initialize from the given`~asdf.AsdfFile`.
            - dict : Initialize from the given dictionary.
        ignore_unrecognized_tag : bool
            If `True`, ignore tags that are not recognized.
        **kwargs
            Additional arguments passed to asdf.open.

        Returns
        -------
        asdffile : `~asdf.AsdfFile`
            An ASDF file object.
        """
        warnings.warn(
            "open_asdf is deprecated, use asdf.open instead.", DeprecationWarning, stacklevel=2
        )

        if isinstance(init, str):
            asdffile = asdf.open(init, ignore_unrecognized_tag=ignore_unrecognized_tag, **kwargs)

        elif isinstance(init, dict):
            asdffile = AsdfFile(None, ignore_unrecognized_tag=ignore_unrecognized_tag)
            asdffile._tree = init
        else:
            asdffile = AsdfFile(init, ignore_unrecognized_tag=ignore_unrecognized_tag)
        return asdffile

    @classmethod
    def from_asdf(cls, init, schema=None, **kwargs):
        """
        Load a data model from an ASDF file.

        Parameters
        ----------
        init : str, file object, `~asdf.AsdfFile`
            - str : file path: initialize from the given file
            - readable file object: Initialize from the given file object
            - `~asdf.AsdfFile` : Initialize from the given`~asdf.AsdfFile`.
        schema : dict
            Same as for `__init__`
        **kwargs
            Aadditional arguments passed to lower level functions

        Returns
        -------
        model : `~jwst.datamodels.DataModel` instance
            A data model.
        """
        warnings.warn(
            "from_asdf is deprecated, use DataModel.__init__ instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls(init, schema=schema, **kwargs)

    def to_asdf(self, init, *args, **kwargs):
        """
        Write a data model to an ASDF file.

        Parameters
        ----------
        init : file path or file object
            The file to write to.
        *args
            Additional positional arguments passed to `~asdf.AsdfFile.write_to`.
        **kwargs
            Any additional keyword arguments are passed along to
            `~asdf.AsdfFile.write_to`.
        """
        self.on_save(init)
        self.validate()  # required to trigger ValidationWarning
        tree = convert_fitsrec_to_array_in_tree(self._instance)
        # Don't AsdfFile(tree) as this will cause a second validation of the tree
        # instead open an empty tree, then assign to the hidden '_tree'
        # This can be updated when asdf 4.0 is the minimum version.
        asdffile = AsdfFile()
        asdffile._tree = tree
        asdffile.write_to(init, *args, **kwargs)

    @classmethod
    def from_fits(cls, init, schema=None, **kwargs):
        """
        Load a model from a FITS file.

        Parameters
        ----------
        init : file path, file object, astropy.io.fits.HDUList
            - file path: Initialize from the given file
            - readable file object: Initialize from the given file object
            - astropy.io.fits.HDUList: Initialize from the given
              `~astropy.io.fits.HDUList`.
        schema : dict, str
            Same as for `__init__`
        **kwargs
            Aadditional arguments passed to lower level functions.

        Returns
        -------
        model : `~jwst.datamodels.DataModel`
            A data model.
        """
        warnings.warn(
            "from_fits is deprecated, use DataModel.__init__ instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cls(init, schema=schema, **kwargs)

    def to_fits(self, init, *args, **kwargs):
        """
        Write a data model to a FITS file.

        Parameters
        ----------
        init : file path or file object
            The file to write to.
        *args
            Additional positional arguments passed to `astropy.io.fits.writeto`.
        **kwargs
            Additional keyword arguments passed to `astropy.io.fits.writeto`.
        """
        self.on_save(init)

        hdulist = fits_support.to_fits(self._instance, self._schema)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Card is too long")
            if self._no_asdf_extension:
                # For some old files that were written out before the
                # _no_asdf_extension existed, these will have an ASDF
                # extension, which may get passed along through extra_fits.
                # Avoid this.
                if "ASDF" in hdulist:
                    del hdulist["ASDF"]
            hdulist.writeto(init, *args, **kwargs)

    @property
    def shape(self):
        """Return the shape of the primary array."""
        if self._shape is None:
            primary_array_name = self.get_primary_array_name()
            if primary_array_name and self.hasattr(primary_array_name):
                primary_array = getattr(self, primary_array_name)
                self._shape = primary_array.shape
        return self._shape

    def __setattr__(self, attr, value):
        if attr in frozenset(("shape", "history", "_extra_fits", "schema")):
            object.__setattr__(self, attr, value)
        else:
            properties.ObjectNode.__setattr__(self, attr, value)

    def extend_schema(self, new_schema):
        """
        Extend the model's schema using the given schema, by combining it in an "allOf" array.

        Parameters
        ----------
        new_schema : dict
            Schema tree.

        Returns
        -------
        self : DataModel
            The datamodel with its schema updated.
        """
        schema = {"allOf": [self._schema, new_schema]}
        self._schema = mschema.merge_property_trees(schema)
        self.validate()
        return self

    def add_schema_entry(self, position, new_schema):
        """
        Extend the model's schema.

        Place the given ``new_schema`` at the given dot-separated position in the tree.

        Parameters
        ----------
        position : str
            Dot separated string indicating the position, e.g. ``meta.instrument.name``.
        new_schema : dict
            Schema tree.

        Returns
        -------
        self : DataModel
            The datamodel with the schema entry added.
        """
        parts = position.split(".")
        schema = new_schema
        for part in parts[::-1]:
            schema = {"type": "object", "properties": {part: schema}}
        return self.extend_schema(schema)

    # return_result retained for backward compatibility
    def find_fits_keyword(self, keyword, return_result=True):
        """
        Find a reference to a FITS keyword in this model's schema.

        This is intended for interactive use, and not for use within library code.

        Parameters
        ----------
        keyword : str
            A FITS keyword name.

        Returns
        -------
        locations : list of str
            If `return_result` is `True`, a list of the locations in
            the schema where this FITS keyword is used.  Each element
            is a dot-separated path.
        """
        from . import schema

        return schema.find_fits_keyword(self.schema, keyword)

    def search_schema(self, substring):
        """
        Search the metadata schema for a particular phrase.

        This is intended for interactive use, and not for use within
        library code.

        The searching is case insensitive.

        Parameters
        ----------
        substring : str
            The substring to search for.

        Returns
        -------
        locations : list of tuples
            The locations within the schema where the element is found.
        """
        from . import schema

        return schema.search_schema(self.schema, substring)

    def __getitem__(self, key):  # numpydoc ignore=RT01
        """Get a metadata value using a dotted name."""
        assert isinstance(key, str)
        meta = self
        for part in key.split("."):
            try:
                meta = getattr(meta, part)
            except AttributeError as err:
                raise KeyError(repr(key)) from err
        return meta

    def __setitem__(self, key, value):
        """Set a metadata value using a dotted name."""
        assert isinstance(key, str)
        meta = self
        parts = key.split(".")
        for part in parts[:-1]:
            try:
                part = int(part)
            except ValueError:
                try:
                    meta = getattr(meta, part)
                except AttributeError as err:
                    raise KeyError(repr(key)) from err
            else:
                meta = meta[part]

        part = parts[-1]
        try:
            part = int(part)
        except ValueError:
            setattr(meta, part, value)
        else:
            meta[part] = value

    def items(self):
        """
        Iterate over all of the datamodel contents in a flat way.

        Each element is a pair (`key`, `value`).  Each `key` is a
        dot-separated name.  For example, the schema element
        `meta.observation.date` will end up in the result as::

            ("meta.observation.date": "2012-04-22T03:22:05.432")
        """

        def recurse(tree, path=None):
            if path is None:
                path = []
            if isinstance(tree, dict):
                for key, val in tree.items():
                    for x in recurse(val, path + [key]):
                        yield x
            elif isinstance(tree, (list, tuple)):
                for i, val in enumerate(tree):
                    for x in recurse(val, path + [i]):
                        yield x
            elif tree is not None:
                yield (".".join(str(x) for x in path), tree)

        yield from recurse(self._instance)

    def keys(self):
        """
        Iterate over all of the datamodel contents in a flat way.

        Yields
        ------
        key : str
            The key of the schema element. Each `key` is a
            dot-separated name.  For example, the schema element
            `meta.observation.date` will end up in the result as the
            string `"meta.observation.date"`.
        """
        for key, _ in self.items():
            yield key

    def values(self):
        """
        Iterate over all of the datamodel contents in a flat way.

        Yields
        ------
        value : object
            The value of the schema element.
        """
        for _, val in self.items():
            yield val

    def update(self, d, only=None, extra_fits=False):
        """
        Update this model with the metadata elements from another model.

        Note: The ``update`` method skips a WCS object, if present.

        Parameters
        ----------
        d : `~jwst.datamodels.DataModel` or dictionary-like object
            The model to copy the metadata elements from. Can also be a
            dictionary or dictionary of dictionaries or lists.
        only : str, None
            Update only the named hdu, e.g. ``only='PRIMARY'``. Can either be
            a string or list of hdu names. Default is to update all the hdus.
        extra_fits : bool
            Update from ``extra_fits``.  Default is False.
        """

        def hdu_keywords_from_data(d, path, hdu_keywords):
            # Walk tree and add paths to keywords to hdu keywords
            if isinstance(d, dict):
                for key, val in d.items():
                    if len(path) > 0 or key != "extra_fits":
                        hdu_keywords_from_data(val, path + [key], hdu_keywords)
            elif isinstance(d, list):
                for key, val in enumerate(d):
                    hdu_keywords_from_data(val, path + [key], hdu_keywords)
            elif isinstance(d, np.ndarray):
                # skip data arrays
                pass
            else:
                hdu_keywords.append(path)

        def hdu_keywords_from_schema(subschema, path, combiner, ctx, recurse):
            # Add path to keyword to hdu_keywords if in list of hdu names
            if "fits_keyword" in subschema:
                fits_hdu = subschema.get("fits_hdu", "PRIMARY")
                if fits_hdu in hdu_names:
                    ctx.append(path)

        def hdu_names_from_schema(subschema, path, combiner, ctx, recurse):
            # Build a set of hdu names from the schema
            hdu_name = subschema.get("fits_hdu")
            if hdu_name:
                hdu_names.add(hdu_name)

        def included(cursor, part):
            # Test if part is in the cursor
            if isinstance(part, int):
                return part >= 0 and part < len(cursor)
            else:
                return part in cursor

        def set_hdu_keyword(this_cursor, that_cursor, path):
            # Copy an element pointed to by path from that to this
            part = path.pop(0)
            if not included(that_cursor, part):
                return
            if len(path) == 0:
                this_cursor[part] = copy.deepcopy(that_cursor[part])
            else:
                that_cursor = that_cursor[part]
                if not included(this_cursor, part):
                    if isinstance(path[0], int):
                        if isinstance(part, int):
                            this_cursor.append([])
                        else:
                            this_cursor[part] = []
                    else:
                        if isinstance(part, int):
                            this_cursor.append({})
                        elif isinstance(that_cursor, list):
                            this_cursor[part] = []
                        else:
                            this_cursor[part] = {}
                this_cursor = this_cursor[part]
                set_hdu_keyword(this_cursor, that_cursor, path)

        def protected_keyword(path):
            # Some keywords are protected and
            # should not be copied frpm the other image
            if len(path) == 2:
                if path[0] == "meta":
                    if path[1] in ("date", "model_type"):
                        return True
            return False

        # Get the list of hdu names from the model so that updates
        # are limited to those hdus

        if only is not None:
            if isinstance(only, str):
                hdu_names = {only}
            else:
                hdu_names = set(only)
        else:
            hdu_names = {"PRIMARY"}
            mschema.walk_schema(self._schema, hdu_names_from_schema, hdu_names)

        # Get the paths to all the keywords that will be updated from

        hdu_keywords = []
        if isinstance(d, DataModel):
            schema = d._schema
            d = d._instance
            mschema.walk_schema(schema, hdu_keywords_from_schema, hdu_keywords)
        else:
            path = []
            hdu_keywords_from_data(d, path, hdu_keywords)

        # Perform the updates to the keywords mentioned in the schema
        for path in hdu_keywords:
            if not protected_keyword(path):
                set_hdu_keyword(self._instance, d, path)

        # Update from extra_fits as well, if indicated
        if extra_fits:
            for hdu_name in hdu_names:
                path = ["extra_fits", hdu_name, "header"]
                set_hdu_keyword(self._instance, d, path)

        self.validate()

    def to_flat_dict(self, include_arrays=True):
        """
        Return a dictionary of all of the datamodel contents as a flat dictionary.

        Each dictionary key is a dot-separated name.  For example, the
        schema element `meta.observation.date` will end up in the
        dictionary as::

            {"meta.observation.date": "2012-04-22T03:22:05.432"}

        Parameters
        ----------
        include_arrays : bool
            If `True`, include arrays in the output.  If `False`, exclude
            arrays.  Default is `True`.

        Returns
        -------
        flat_dict : dict
            A dictionary of all of the datamodel contents as a flat dictionary.
        """

        def convert_val(val):
            if isinstance(val, datetime.datetime):
                return val.isoformat()
            elif isinstance(val, Time):
                return str(val)
            return val

        if include_arrays:
            return {key: convert_val(val) for (key, val) in self.items()}
        else:
            return {
                key: convert_val(val)
                for (key, val) in self.items()
                if not isinstance(val, (np.ndarray, NDArrayType))
            }

    @property
    def schema(self):
        """
        Retrieve the schema for this model.

        Returns
        -------
        dict
            The datamodel schema.
        """
        return self._schema

    @property
    def history(self):
        """
        Get the history as a list of entries.

        Returns
        -------
        history : `HistoryList`
            A list of history entries.
        """
        return HistoryList(self._asdf)

    @history.setter
    def history(self, values):
        """
        Set a history entry.

        Parameters
        ----------
        values : list
            For FITS files this should be a list of strings.
            For ASDF files use a list of ``HistoryEntry`` object. It can be created
            with `~jwst.datamodels.util.create_history_entry`.
        """
        entries = self.history
        entries.clear()
        entries.extend(values)

    def get_fits_wcs(self, hdu_name="SCI", hdu_ver=1, key=" "):
        """
        Get a `astropy.wcs.WCS` object created from the FITS WCS information in the model.

        Note that modifying the returned WCS object will not modify
        the data in this model.  To update the model, use `set_fits_wcs`.

        This method is deprecated and will be removed in a future version.
        To get the SIP approximation, call ``to_fits_sip()`` on the
        model.meta.wcs attribute.

        Parameters
        ----------
        hdu_name : str, optional
            The name of the HDU to get the WCS from.  This must use
            named HDU's, not numerical order HDUs. To get the primary
            HDU, pass ``'PRIMARY'``.
        hdu_ver : int, optional
            The extension version. Used when there is more than one
            extension with the same name. The default value, 1,
            is the first.
        key : str, optional
            The name of a particular WCS transform to use.  This may
            be either ``' '`` or ``'A'``-``'Z'`` and corresponds to
            the ``"a"`` part of the ``CTYPEia`` cards.  *key* may only
            be provided if *header* is also provided.

        Returns
        -------
        wcs : `astropy.wcs.WCS` or `pywcs.WCS` object
            The type will depend on what libraries are installed on
            this system.
        """
        warnings.warn(
            "get_fits_wcs is deprecated. To get the SIP approximation, "
            "call ``to_fits_sip()`` on the model.meta.wcs attribute.",
            DeprecationWarning,
            stacklevel=2,
        )
        hdulist = fits_support.to_fits(self._instance, self._schema)
        hdu = fits_support.get_hdu(hdulist, hdu_name, index=hdu_ver - 1)
        header = hdu.header
        return WCS(header, key=key, relax=True, fix=True)

    def set_fits_wcs(self, wcs, hdu_name="SCI"):
        """
        Set the FITS WCS information on the model using the given `astropy.wcs.WCS` object.

        Note that the "key" of the WCS is stored in the WCS object
        itself, so it can not be set as a parameter to this method.

        This method is deprecated and will be removed in a future version.
        The WCS should only be modified by setting model.meta.wcs

        Parameters
        ----------
        wcs : `astropy.wcs.WCS` or `pywcs.WCS` object
            The object containing FITS WCS information
        hdu_name : str, optional
            The name of the HDU to set the WCS from.  This must use
            named HDU's, not numerical order HDUs.  To set the primary
            HDU, pass ``'PRIMARY'``.
        """
        warnings.warn(
            "set_fits_wcs is deprecated and will be removed in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        header = wcs.to_header()
        if hdu_name == "PRIMARY":
            hdu = fits.PrimaryHDU(header=header)
        else:
            hdu = fits.ImageHDU(name=hdu_name, header=header)
        hdulist = fits.HDUList([hdu])

        ff = fits_support.from_fits(
            hdulist,
            self._schema,
            self._ctx,
            ignore_missing_extensions=self._ignore_missing_extensions,
        )

        self._instance = properties.merge_tree(self._instance, ff.tree)

    def read(self, *args, **kwargs):
        """
        Read the model from a file.

        This method is only defined for compatibility with astropy.registry
        and should not be called directly.  Use `__init__` instead.
        This method is deprecated and will be removed in a future version.

        Parameters
        ----------
        *args, **kwargs : tuple, dict
            Additional arguments passed to the model init function.

        Returns
        -------
        model : `~jwst.datamodels.DataModel`
            A data model.
        """
        warnings.warn("read is deprecated, use __init__ instead.", DeprecationWarning, stacklevel=2)
        return self.__init__(*args, **kwargs)

    def write(self, path, *args, **kwargs):
        """
        Write the model to a file.

        This method is only defined for compatibility with astropy.registry
        and should not be called directly.  Use `save` instead.
        This method is deprecated and will be removed in a future version.

        Parameters
        ----------
        path : str
            The path to the file to write to.
        *args, **kwargs : tuple, dict
            Additional arguments passed to the model save function.
        """
        warnings.warn("write is deprecated, use save instead.", DeprecationWarning, stacklevel=2)
        self.save(path, *args, **kwargs)

    def getarray_noinit(self, attribute):
        """
        Retrieve array but without initialization.

        Arrays initialize when directly referenced if they had
        not previously been initialized. This circumvents the
        initialization and instead raises `AttributeError`.

        Parameters
        ----------
        attribute : str
            The attribute to retrieve.

        Returns
        -------
        value : object
           The value of the attribute.

        Raises
        ------
        AttributeError
            If the attribute does not exist.
        """
        if attribute in self.instance:
            return getattr(self, attribute)
        raise AttributeError(f'{self} has no attribute "{attribute}"')


class _FileReference:
    """
    Reference counter for open file pointers managed by DataModel.

    Once decremented to zero the file will be closed.
    """

    def __init__(self, file):
        self._file = file
        self._count = 1

    def increment(self):
        self._count += 1

    def decrement(self):
        if self._count <= 0:
            return

        self._count -= 1
        if self._count <= 0:
            self._file.close()
            self._file = None
