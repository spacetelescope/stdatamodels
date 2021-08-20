"""
Functions that support validation of model changes
"""

import warnings
import jsonschema
from asdf import schema as asdf_schema
from asdf import yamlutil
from asdf.tags.core import ndarray
from asdf.schema import ValidationError, YAML_VALIDATORS
from asdf.util import HashableDict
import numpy as np

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


def _validate_datatype(validator, schema_datatype, instance, schema):
    """
    This extends the ASDF datatype validator to support ndim
    and max_ndim within individual fields of structured arrays,
    and handle the absence of the shape field correctly.

    Additionally, dtypes are required to be equivalent, instead
    of just "safe" to cast.
    """
    if isinstance(instance, list):
        array = ndarray.inline_data_asarray(instance)
        instance_datatype, _ = ndarray.numpy_dtype_to_asdf_datatype(array.dtype)
    elif isinstance(instance, dict):
        if 'datatype' in instance:
            instance_datatype = instance['datatype']
        elif 'data' in instance:
            array = ndarray.inline_data_asarray(instance['data'])
            instance_datatype, _ = ndarray.numpy_dtype_to_asdf_datatype(array.dtype)
        else:
            yield ValidationError("Not an array")
    elif isinstance(instance, (np.ndarray, ndarray.NDArrayType)):
        instance_datatype, _ = ndarray.numpy_dtype_to_asdf_datatype(instance.dtype)
    else:
        yield ValidationError("Not an array")

    schema_dtype = ndarray.asdf_datatype_to_numpy_dtype(schema_datatype)
    instance_dtype = ndarray.asdf_datatype_to_numpy_dtype(instance_datatype)

    if not schema_dtype.fields:
        if instance_dtype.fields:
            yield ValidationError(f"Expected scalar datatype '{schema_datatype}', got '{instance_datatype}'")

        # Using 'equiv' so that we can be flexible on byte order:
        if not np.can_cast(instance_dtype, schema_dtype, 'equiv'):
            yield ValidationError(f"Array datatype '{instance_datatype}' is not compatible with '{schema_datatype}'")
    else:
        if not instance_dtype.fields:
            yield ValidationError(f"Expected structured datatype '{schema_datatype}', got '{instance_datatype}'")

        if len(instance_dtype.fields) != len(schema_dtype.fields):
            yield ValidationError(
                "Mismatch in number of fields: "
                f"Expected {len(schema_datatype)}, got {len(instance_datatype)}"
            )

        for i in range(len(schema_dtype.fields)):
            instance_type = instance_dtype[i]
            instance_ndim = len(instance_type.shape)
            schema_type = schema_dtype[i]
            field_schema = schema_datatype[i]
            instance_name = instance_dtype.names[i]
            schema_name = schema_dtype.names[i]

            if instance_name != schema_name:
                yield ValidationError(
                    f"Wrong name in field {i}: Expected "
                    f"{instance_name}, got {schema_name}"
                )

            if 'ndim' in field_schema and instance_ndim != field_schema['ndim']:
                yield ValidationError(
                    f"Wrong number of dimensions in field {i}: Expected "
                    f"{field_schema['ndim']}, got {instance_ndim}"
                )

            if 'max_ndim' in field_schema and instance_ndim > field_schema['max_ndim']:
                yield ValidationError(
                    f"Wrong number of dimensions in field {i}: Expected "
                    f"maximum of {field_schema['max_ndim']}, got {instance_ndim}"
                )

            if len(schema_type.shape) == 0:
                # If the schema didn't include a shape, then anything goes:
                compare_instance_type = instance_type.base
                compare_schema_type = schema_type.base
            else:
                # If shape is present in the schema, then the array must match:
                compare_instance_type = instance_type
                compare_schema_type = schema_type

            # Using 'equiv' so that we can be flexible on byte order:
            if not np.can_cast(compare_instance_type, compare_schema_type, 'equiv'):
                yield ValidationError(
                    f"Array datatype '{instance_datatype}' is not compatible with '{schema_datatype}' at "
                    f"field {i}"
                )


_VALIDATORS = HashableDict(YAML_VALIDATORS.copy())
_VALIDATORS["datatype"] = _validate_datatype
_VALIDATORS["ndim"] = ndarray.validate_ndim
_VALIDATORS["max_ndim"] = ndarray.validate_max_ndim


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

        if ctx._validate_arrays:
            validators = _VALIDATORS
        else:
            validators = YAML_VALIDATORS

        asdf_schema.validate(value, schema=schema, validators=validators)


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
