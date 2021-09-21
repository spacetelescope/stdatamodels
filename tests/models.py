"""
Dummy models for testing.
"""
from stdatamodels import DataModel


class BasicModel(DataModel):
    """
    Model with minimal metadata and a single 2D float32
    data array.
    """
    schema_url = "http://example.com/schemas/basic_model"


class ValidationModel(DataModel):
    """
    Model with various kinds of validated attributes.
    """
    schema_url = "http://example.com/schemas/validation_model"


class RequiredModel(DataModel):
    """
    Model that includes a required attribute.  Uses JSON Schema's
    built-in 'required' property rather than the custom fits_required.
    """
    schema_url = "http://example.com/schemas/required_model"


class AnyOfModel(DataModel):
    """
    Model for which the attribute 'meta.foo' has conflicting
    default values due to use of an anyOf combiner.
    """
    schema_url = "http://example.com/schemas/anyof_model"


class FitsModel(DataModel):
    """
    Model whose schema includes support for writing to FITS
    files.
    """
    schema_url = "http://example.com/schemas/fits_model"


class PureFitsModel(FitsModel):

    def __init__(self, init=None, **kwargs):
        super().__init__(init=init, **kwargs)
        self._no_asdf_extension = True


class TransformModel(DataModel):
    """
    Model with an astropy.modeling model in one of its attributes.
    """
    schema_url = "http://example.com/schemas/transform_model"


class TableModel(DataModel):
    """
    Model that includes a recarray-style table.
    """
    schema_url = "http://example.com/schemas/table_model"


class DeprecatedModel(DataModel):
    """
    Model with a top-level "old_origin" property that has
    moved to "meta.origin", and a "meta.old_data" property that has
    moved to "data".
    """
    schema_url = "http://example.com/schemas/deprecated_model"
