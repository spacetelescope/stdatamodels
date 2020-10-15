"""
Functions that support validation of model changes
"""

import warnings
import jsonschema
from asdf import schema as asdf_schema
from asdf import yamlutil


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
    if value is None:
        if schema.get('fits_required'):
            name = schema.get("fits_keyword") or schema.get("fits_hdu")
            raise jsonschema.ValidationError("%s is a required value"
                                              % name)
    else:
        value = yamlutil.custom_tree_to_tagged_tree(value, ctx._asdf)
        asdf_schema.validate(value, schema=schema)


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
