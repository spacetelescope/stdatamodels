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


class FitsRequiredModel(DataModel):
    """
    Model that includes fits_required attributes.
    """
    schema_url = "http://example.com/schemas/fits_required_model"


class RequiredModel(DataModel):
    """
    Model that includes a required attribute.  Uses JSON Schema's
    built-in 'required' property rather than the custom fits_required.
    """
    schema_url = "http://example.com/schemas/required_model"

