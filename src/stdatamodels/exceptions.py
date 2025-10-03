__all__ = ["ValidationWarning", "NoTypeWarning"]


class ValidationWarning(Warning):
    """Warning to raise if a model fails to validate through its schema."""

    pass


class NoTypeWarning(Warning):
    """
    Warning to raise when opening a file that lacks a model type.

    For ASDF files this means the meta.model_type keyword is missing.
    For FITS files this means the DATAMODL keyword is missing from the primary hdulist.
    """

    pass
