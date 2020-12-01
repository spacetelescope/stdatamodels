"""
Functions that support validation of model changes
"""

import warnings
import jsonschema
from asdf import schema as asdf_schema
from asdf import yamlutil

from .util import remove_none_from_tree


class ValidationWarning(Warning):
    pass


def value_change(path, value, schema, ctx):
    """
    Validate a change in value against a schema.
    Trap error and return a flag.
    """
    try:
        _check_value(value, schema, ctx)
        update = True

    except jsonschema.ValidationError as error:
        update = False
        errmsg = _error_message(path, error)
        if ctx._pass_invalid_values:
            update = True
        if ctx._strict_validation:
            raise jsonschema.ValidationError(errmsg)
        else:
            warnings.warn(errmsg, ValidationWarning)
    return update


def _check_value(value, schema, ctx):
    """
    Perform the actual validation.
    """
    # Do not validate None values.  These are regarded as missing in DataModel,
    # and will eventually be stripped out when the model is saved to FITS or ASDF.
    if value is not None:
        # There may also be Nones hiding within the value.  Do this before
        # converting to tagged tree, so that we don't have to descend unnecessarily
        # into nodes for custom types.
        value = remove_none_from_tree(value)
        value = yamlutil.custom_tree_to_tagged_tree(value, ctx._asdf)
        # The YAML_VALIDATORS dictionary excludes the ASDF ndarray validators
        # (datatype, shape, ndim, max_ndim), which we can't use here because
        # they don't fully support recarray columns whose elements are arrays.
        # Currently ndarray validation is handled in properties._cast instead.
        asdf_schema.validate(value, schema=schema, validators=asdf_schema.YAML_VALIDATORS)


def _error_message(path, error):
    """
    Add the path to the attribute as context for a validation error
    """
    if isinstance(path, list):
        spath = [str(p) for p in path]
        name = '.'.join(spath)
    else:
        name = str(path)

    error = str(error)
    if len(error) > 2000:
        error = error[0:1996] + " ..."
    errfmt = "While validating {} the following error occurred:\n{}"
    errmsg = errfmt.format(name, error)
    return errmsg
