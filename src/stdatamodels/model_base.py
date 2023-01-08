"""
Data model class hierarchy
"""

import copy
import datetime
import os
from pathlib import PurePath
import sys
import warnings

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
from .util import get_envar_as_boolean, remove_none_from_tree
from . import s3_utils

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
    """
    Base class of all of the data models.
    """

    schema_url = None
    """
    The schema URI to validate the model against.  If
    None, only basic validation of required metadata
    properties (filename, model_type) will occur.
    """

    def __init__(self, init=None, schema=None, memmap=False,
                 pass_invalid_values=None, strict_validation=None,
                 validate_on_assignment=None, cast_fits_arrays=True,
                 validate_arrays=False, ignore_missing_extensions=True, **kwargs):
        """
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

        memmap : bool
            Turn memmap of FITS file on or off.  (default: False).  Ignored for
            ASDF files.

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

        cast_fits_arrays : bool
            If `True`, arrays will be cast to the dtype described by the schema
            when read from a FITS file.
            If `False`, arrays will be read without casting.

        validate_arrays : bool
            If `True`, arrays will be validated against ndim, max_ndim, and datatype
            validators in the schemas.

        ignore_missing_extensions : bool
            When `False`, raise warnings when a file is read that
            contains metadata about extensions that are not available.
            Defaults to `True`.

        kwargs : dict
            Additional keyword arguments passed to lower level functions. These arguments
            are generally file format-specific. Arguments of note are:

            - FITS

              skip_fits_update - bool or None
                  `True` to skip updating the ASDF tree from the FITS headers, if possible.
                  If `None`, value will be taken from the environmental SKIP_FITS_UPDATE.
                  Otherwise, the default value is `True`.
        """

        # Override value of validation parameters if not explicitly set.
        if pass_invalid_values is None:
            pass_invalid_values = get_envar_as_boolean("PASS_INVALID_VALUES",
                                                            False)
        self._pass_invalid_values = pass_invalid_values
        if strict_validation is None:
            strict_validation = get_envar_as_boolean("STRICT_VALIDATION",
                                                          False)
        if validate_on_assignment is None:
            validate_on_assignment = get_envar_as_boolean("VALIDATE_ON_ASSIGNMENT",
                                                          True)
        self._strict_validation = strict_validation
        self._ignore_missing_extensions = ignore_missing_extensions
        self._validate_on_assignment = validate_on_assignment
        self._cast_fits_arrays = cast_fits_arrays
        self._validate_arrays = validate_arrays

        kwargs.update({'ignore_missing_extensions': ignore_missing_extensions})

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
        # proper code to intiailize the model
        self._file_references = []
        is_array = False
        is_shape = False
        shape = None

        if init is None:
            asdffile = self.open_asdf(init=None, **kwargs)

        elif isinstance(init, dict):
            asdffile = self.open_asdf(init=init, **kwargs)

        elif isinstance(init, np.ndarray):
            asdffile = self.open_asdf(init=None, **kwargs)

            shape = init.shape
            is_array = True

        elif isinstance(init, tuple):
            for item in init:
                if not isinstance(item, int):
                    raise ValueError("shape must be a tuple of ints")

            shape = init
            is_shape = True
            asdffile = self.open_asdf(init=None, **kwargs)

        elif isinstance(init, DataModel):
            asdffile = None
            self.clone(self, init)
            if not isinstance(init, self.__class__):
                self.validate()
            return

        elif isinstance(init, AsdfFile):
            asdffile = init

        elif isinstance(init, fits.HDUList):
            asdffile = fits_support.from_fits(init, self._schema, self._ctx,
                                              **kwargs)

        elif isinstance(init, (str, bytes, PurePath)):
            if isinstance(init, PurePath):
                init = str(init)
            if isinstance(init, bytes):
                init = init.decode(sys.getfilesystemencoding())
            file_type = filetype.check(init)

            if file_type == "fits":
                if s3_utils.is_s3_uri(init):
                    init_fitsopen = s3_utils.get_object(init)
                    memmap = None
                else:
                    init_fitsopen = init

                hdulist = fits.open(init_fitsopen, memmap=memmap)
                asdffile = fits_support.from_fits(
                    hdulist, self._schema, self._ctx, **kwargs
                )
                self._file_references.append(_FileReference(hdulist))

            elif file_type == "asdf":
                asdffile = self.open_asdf(init=init, **kwargs)

            else:
                # TODO handle json files as well
                raise IOError(
                        "File does not appear to be a FITS or ASDF file.")

        else:
            raise ValueError(
                "Can't initialize datamodel using {0}".format(str(type(init))))

        self._file_references.append(_FileReference(asdffile))

        # Initialize object fields as determined from the code above
        self._shape = shape
        self._instance = asdffile.tree
        self._asdf = asdffile

        # Initalize class dependent hidden fields
        self._no_asdf_extension = False

        # Instantiate the primary array of the image
        if is_array:
            primary_array_name = self.get_primary_array_name()
            if not primary_array_name:
                raise TypeError(
                    "Array passed to DataModel.__init__, but model has "
                    "no primary array in its schema")
            setattr(self, primary_array_name, init)

        # If a shape has been given, initialize the primary array.
        if is_shape:
            primary_array_name = self.get_primary_array_name()
            if not primary_array_name:
                raise TypeError(
                    "Shape passed to DataModel.__init__, but model has "
                    "no primary array in its schema")

            # Initialization occurs when the primary array is first
            # referenced. Do so now.
            getattr(self, primary_array_name)

        # initialize arrays from keyword arguments when they are present

        for attr, value in kwargs.items():
            if value is not None:
                subschema = properties._get_schema_for_property(self._schema,
                                                                attr)
                if 'datatype' in subschema:
                    setattr(self, attr, value)

        # Call hook that sets model properties
        self.on_init(init)

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

        Returns
        -------
        str
        """
        raise NotImplementedError("The base DataModel class cannot be used to select best references")

    def get_crds_parameters(self):
        """
        Get the parameters used by CRDS to select references for this model.

        Returns
        -------
        dict
        """
        raise NotImplementedError("The base DataModel class cannot be used to select best references")

    @property
    def _model_type(self):
        return self.__class__.__name__

    def __repr__(self):
        buf = ['<']
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
        buf.append('>')

        return "".join(buf)

    def __del__(self):
        """Ensure closure of resources when deleted."""
        self.close()

    @property
    def override_handle(self):
        """override_handle identifies in-memory models where a filepath
        would normally be used.
        """
        # Arbitrary choice to look something like crds://
        return "override://" + self.__class__.__name__

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        # This method is called by __del__, which may be invoked
        # even when the model failed to initialize.  Consequently,
        # we can't assume that any attributes have been set.
        if hasattr(self, "_file_references"):
            for file_reference in self._file_references:
                file_reference.decrement()
            # Discard the list in case close is called a second time.
            self._file_references = []

    @staticmethod
    def clone(target, source, deepcopy=False, memo=None):
        if deepcopy:
            instance = copy.deepcopy(source._instance, memo=memo)
            target._asdf = AsdfFile(instance)
            target._instance = instance
        else:
            target._asdf = source._asdf
            target._instance = source._instance
            for file_reference in source._file_references:
                file_reference.increment()
                target._file_references.append(file_reference)

        target._shape = source._shape
        target._ctx = target
        target._no_asdf_extension = source._no_asdf_extension

    def copy(self, memo=None):
        """
        Returns a deep copy of this model.
        """
        result = self.__class__(init=None,
                                pass_invalid_values=self._pass_invalid_values,
                                strict_validation=self._strict_validation)
        self.clone(result, self, deepcopy=True, memo=memo)
        return result

    __copy__ = __deepcopy__ = copy

    def validate(self):
        """
        Re-validate the model instance against its schema
        """
        validate.value_change(str(self), self._instance, self._schema, self)

    def info(self, *args, **kwargs):
        return self._asdf.info(**kwargs)

    def search(self, *args, **kwargs):
        return self._asdf.search(*args, **kwargs)

    try:
        info.__doc__ = AsdfFile.info.__doc__
        search.__doc__ = AsdfFile.search.__doc__
    except AttributeError:
        pass

    def get_primary_array_name(self):
        """
        Returns the name "primary" array for this model, which
        controls the size of other arrays that are implicitly created.
        This is intended to be overridden in the subclasses if the
        primary array's name is not "data".
        """
        if properties._find_property(self._schema, 'data'):
            primary_array_name = 'data'
        else:
            primary_array_name = ''
        return primary_array_name

    def on_init(self, init):
        """
        Hook used to customize model attributes at the end of ``__init__``.

        Parameters
        ----------
        init : object
            First argument to ``__init__``.
        """
        # if the input is from a file, set the filename attribute
        if isinstance(init, str):
            self.meta.filename = os.path.basename(init)
        elif isinstance(init, fits.HDUList):
            info = init.fileinfo(0)
            if info is not None:
                filename = info.get('filename')
                if filename is not None:
                    self.meta.filename = os.path.basename(filename)

        # store the data model type, if not already set
        klass = self.__class__.__name__
        if klass != 'DataModel':
            if not self.meta.hasattr('model_type'):
                self.meta.model_type = klass

    def on_save(self, path=None):
        """
        This is a hook that is called just before saving the file.
        It can be used, for example, to update values in the metadata
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
            self.meta.filename = os.path.basename(path)

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
        path : string or func
            File path to save to.
            If function, it takes one argument with is
            model.meta.filename and returns the full path string.

        dir_path: string
            Directory to save to. If not None, this will override
            any directory information in the `path`

        Returns
        -------
        output_path: str
            The file path the model was saved in.
        """
        if callable(path):
            path_head, path_tail = os.path.split(path(self.meta.filename))
        else:
            path_head, path_tail = os.path.split(path)
        base, ext = os.path.splitext(path_tail)
        if isinstance(ext, bytes):
            ext = ext.decode(sys.getfilesystemencoding())

        if dir_path:
            path_head = dir_path
        output_path = os.path.join(path_head, path_tail)

        # TODO: Support gzip-compressed fits
        if ext == '.fits':
            # TODO: remove 'clobber' check once depreciated fully in astropy
            if 'clobber' not in kwargs:
                kwargs.setdefault('overwrite', True)
            self.to_fits(output_path, *args, **kwargs)
        elif ext == '.asdf':
            self.to_asdf(output_path, *args, **kwargs)
        else:
            raise ValueError("unknown filetype {0}".format(ext))

        return output_path

    @staticmethod
    def open_asdf(init=None,
                  ignore_version_mismatch=True,
                  ignore_unrecognized_tag=False,
                  **kwargs):
        """
        Open an asdf object from a filename or create a new asdf object
        """
        if isinstance(init, str):
            if s3_utils.is_s3_uri(init):
                init = s3_utils.get_object(init)
            asdffile = asdf.open(init,
                                 ignore_version_mismatch=ignore_version_mismatch,
                                 ignore_unrecognized_tag=ignore_unrecognized_tag)

        else:
            asdffile = AsdfFile(init,
                            ignore_version_mismatch=ignore_version_mismatch,
                            ignore_unrecognized_tag=ignore_unrecognized_tag
                            )
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
        schema :
            Same as for `__init__`
        kwargs : dict
            Aadditional arguments passed to lower level functions

        Returns
        -------
        model : `~jwst.datamodels.DataModel` instance
            A data model.
        """
        return cls(init, schema=schema, **kwargs)


    def to_asdf(self, init, *args, **kwargs):
        """
        Write a data model to an ASDF file.

        Parameters
        ----------
        init : file path or file object
        args : tuple, list
            Additional positional arguments passed to `~asdf.AsdfFile.write_to`.
        kwargs : dict
            Any additional keyword arguments are passed along to
            `~asdf.AsdfFile.write_to`.
        """
        self.on_save(init)
        self.validate()
        asdffile = self.open_asdf(self._instance, **kwargs)
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

        kwargs : dict
            Aadditional arguments passed to lower level functions.

        Returns
        -------
        model : `~jwst.datamodels.DataModel`
            A data model.
        """
        return cls(init, schema=schema, **kwargs)

    def to_fits(self, init, *args, **kwargs):
        """
        Write a data model to a FITS file.

        Parameters
        ----------
        init : file path or file object

        args, kwargs
            Any additional arguments are passed along to
            `astropy.io.fits.writeto`.
        """
        self.on_save(init)

        hdulist = fits_support.to_fits(self._instance, self._schema)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='Card is too long')
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
        Extend the model's schema using the given schema, by combining
        it in an "allOf" array.

        Parameters
        ----------
        new_schema : dict
            Schema tree.
        """
        schema = {'allOf': [self._schema, new_schema]}
        self._schema = mschema.merge_property_trees(schema)
        self.validate()
        return self

    def add_schema_entry(self, position, new_schema):
        """
        Extend the model's schema by placing the given new_schema at
        the given dot-separated position in the tree.

        Parameters
        ----------
        position : str
            Dot separated string indicating the position, e.g. ``meta.instrument.name``.
        new_schema : dict
            Schema tree.
        """
        parts = position.split('.')
        schema = new_schema
        for part in parts[::-1]:
            schema = {'type': 'object', 'properties': {part: schema}}
        return self.extend_schema(schema)

    # return_result retained for backward compatibility
    def find_fits_keyword(self, keyword, return_result=True):
        """
        Utility function to find a reference to a FITS keyword in this
        model's schema.  This is intended for interactive use, and not
        for use within library code.

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
        Utility function to search the metadata schema for a
        particular phrase.

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
        """
        from . import schema
        return schema.search_schema(self.schema, substring)

    def __getitem__(self, key):
        """
        Get a metadata value using a dotted name.
        """
        assert isinstance(key, str)
        meta = self
        for part in key.split('.'):
            try:
                meta = getattr(meta, part)
            except AttributeError:
                raise KeyError(repr(key))
        return meta

    def __setitem__(self, key, value):
        """
        Set a metadata value using a dotted name.
        """
        assert isinstance(key, str)
        meta = self
        parts = key.split('.')
        for part in parts[:-1]:
            try:
                part = int(part)
            except ValueError:
                try:
                    meta = getattr(meta, part)
                except AttributeError:
                    raise KeyError(repr(key))
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
        Iterates over all of the schema items in a flat way.

        Each element is a pair (`key`, `value`).  Each `key` is a
        dot-separated name.  For example, the schema element
        `meta.observation.date` will end up in the result as::

            ("meta.observation.date": "2012-04-22T03:22:05.432")
        """
        def recurse(tree, path=[]):
            if isinstance(tree, dict):
                for key, val in tree.items():
                    for x in recurse(val, path + [key]):
                        yield x
            elif isinstance(tree, (list, tuple)):
                for i, val in enumerate(tree):
                    for x in recurse(val, path + [i]):
                        yield x
            elif tree is not None:
                yield ('.'.join(str(x) for x in path), tree)

        for x in recurse(self._instance):
            yield x

    def keys(self):
        """
        Iterates over all of the schema keys in a flat way.

        Each result of the iterator is a `key`.  Each `key` is a
        dot-separated name.  For example, the schema element
        `meta.observation.date` will end up in the result as the
        string `"meta.observation.date"`.
        """
        for key, val in self.items():
            yield key

    def values(self):
        """
        Iterates over all of the schema values in a flat way.
        """
        for key, val in self.items():
            yield val

    def update(self, d, only=None, extra_fits=False):
        """
        Updates this model with the metadata elements from another model.

        Note: The ``update`` method skips a WCS object, if present.

        Parameters
        ----------
        d : `~jwst.datamodels.DataModel` or dictionary-like object
            The model to copy the metadata elements from. Can also be a
            dictionary or dictionary of dictionaries or lists.
        only: str, None
            Update only the named hdu, e.g. ``only='PRIMARY'``. Can either be
            a string or list of hdu names. Default is to update all the hdus.
        extra_fits : boolean
            Update from ``extra_fits``.  Default is False.
        """
        def hdu_keywords_from_data(d, path, hdu_keywords):
            # Walk tree and add paths to keywords to hdu keywords
            if isinstance(d, dict):
                for key, val in d.items():
                    if len(path) > 0 or key != 'extra_fits':
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
            if 'fits_keyword' in subschema:
                fits_hdu = subschema.get('fits_hdu', 'PRIMARY')
                if fits_hdu in hdu_names:
                    ctx.append(path)

        def hdu_names_from_schema(subschema, path, combiner, ctx, recurse):
            # Build a set of hdu names from the schema
            hdu_name = subschema.get('fits_hdu')
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
                if path[0] == 'meta':
                    if path[1] in ('date', 'model_type'):
                        return True
            return False
        # Get the list of hdu names from the model so that updates
        # are limited to those hdus

        if only is not None:
            if isinstance(only, str):
                hdu_names = set([only])
            else:
                hdu_names = set(list(only))
        else:
            hdu_names = set(['PRIMARY'])
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
                path = ['extra_fits', hdu_name, 'header']
                set_hdu_keyword(self._instance, d, path)

        self.validate()

    def to_flat_dict(self, include_arrays=True):
        """
        Returns a dictionary of all of the schema items as a flat dictionary.

        Each dictionary key is a dot-separated name.  For example, the
        schema element `meta.observation.date` will end up in the
        dictionary as::

            { "meta.observation.date": "2012-04-22T03:22:05.432" }

        """
        def convert_val(val):
            if isinstance(val, datetime.datetime):
                return val.isoformat()
            elif isinstance(val, Time):
                return str(val)
            return val

        if include_arrays:
            return dict((key, convert_val(val)) for (key, val) in self.items())
        else:
            return dict((key, convert_val(val)) for (key, val) in self.items()
                        if not isinstance(val, (np.ndarray, NDArrayType)))

    @property
    def schema(self):
        return self._schema

    def get_fileext(self):
        return 'fits'

    @property
    def history(self):
        """
        Get the history as a list of entries
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

    def get_fits_wcs(self, hdu_name='SCI', hdu_ver=1, key=' '):
        """
        Get a `astropy.wcs.WCS` object created from the FITS WCS
        information in the model.

        Note that modifying the returned WCS object will not modify
        the data in this model.  To update the model, use `set_fits_wcs`.

        Parameters
        ----------
        hdu_name : str, optional
            The name of the HDU to get the WCS from.  This must use
            named HDU's, not numerical order HDUs. To get the primary
            HDU, pass ``'PRIMARY'``.

        key : str, optional
            The name of a particular WCS transform to use.  This may
            be either ``' '`` or ``'A'``-``'Z'`` and corresponds to
            the ``"a"`` part of the ``CTYPEia`` cards.  *key* may only
            be provided if *header* is also provided.

        hdu_ver: int, optional
            The extension version. Used when there is more than one
            extension with the same name. The default value, 1,
            is the first.

        Returns
        -------
        wcs : `astropy.wcs.WCS` or `pywcs.WCS` object
            The type will depend on what libraries are installed on
            this system.
        """
        hdulist = fits_support.to_fits(self._instance, self._schema)
        hdu = fits_support.get_hdu(hdulist, hdu_name, index=hdu_ver-1)
        header = hdu.header
        return WCS(header, key=key, relax=True, fix=True)

    def set_fits_wcs(self, wcs, hdu_name='SCI'):
        """
        Sets the FITS WCS information on the model using the given
        `astropy.wcs.WCS` object.

        Note that the "key" of the WCS is stored in the WCS object
        itself, so it can not be set as a parameter to this method.

        Parameters
        ----------
        wcs : `astropy.wcs.WCS` or `pywcs.WCS` object
            The object containing FITS WCS information

        hdu_name : str, optional
            The name of the HDU to set the WCS from.  This must use
            named HDU's, not numerical order HDUs.  To set the primary
            HDU, pass ``'PRIMARY'``.
        """
        header = wcs.to_header()
        if hdu_name == 'PRIMARY':
            hdu = fits.PrimaryHDU(header=header)
        else:
            hdu = fits.ImageHDU(name=hdu_name, header=header)
        hdulist = fits.HDUList([hdu])

        ff = fits_support.from_fits(hdulist, self._schema, self._ctx,
                                    ignore_missing_extensions=self._ignore_missing_extensions)

        self._instance = properties.merge_tree(self._instance, ff.tree)

    # --------------------------------------------------------
    # These two method aliases are here for astropy.registry
    # compatibility and should not be called directly
    # --------------------------------------------------------

    read = __init__

    def write(self, path, *args, **kwargs):
        self.save(path, *args, **kwargs)

    def getarray_noinit(self, attribute):
        """Retrieve array but without initilization

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
    Reference counter for open file pointers managed by
    DataModel.  Once decremented to zero the file will
    be closed.
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
