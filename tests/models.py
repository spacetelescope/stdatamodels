"""Mock models for testing."""

from stdatamodels import DataModel


class BasicModel(DataModel):
    """Model with minimal metadata and a single 2D float32data array."""

    schema_url = "http://example.com/schemas/basic_model"


class ValidationModel(DataModel):
    """Model with various kinds of validated attributes."""

    schema_url = "http://example.com/schemas/validation_model"


class RequiredModel(DataModel):
    """
    Model that includes a required attribute.

    Uses JSON Schema's
    built-in 'required' property rather than the custom fits_required.
    """

    schema_url = "http://example.com/schemas/required_model"


class AnyOfModel(DataModel):
    """Model for which 'meta.foo' has conflicting default values due to use of an anyOf combiner."""

    schema_url = "http://example.com/schemas/anyof_model"


class FitsModel(DataModel):
    """Model whose schema includes support for writing to FITS files."""

    schema_url = "http://example.com/schemas/fits_model"


class PureFitsModel(FitsModel):
    """Model without an asdf extension."""

    def __init__(self, init=None, **kwargs):
        super().__init__(init=init, **kwargs)
        self._no_asdf_extension = True


class TransformModel(DataModel):
    """Model with an astropy.modeling model in one of its attributes."""

    schema_url = "http://example.com/schemas/transform_model"


class TableModel(DataModel):
    """Model that includes a recarray-style table."""

    schema_url = "http://example.com/schemas/table_model"

    def get_primary_array_name(self):  # noqa: D102
        return "table"


class TableModelBad(DataModel):
    """Model that includes a recarray-style table with bad defaults."""

    schema_url = "http://example.com/schemas/table_model_bad_defaults"

    def get_primary_array_name(self):  # noqa: D102
        return "table"
