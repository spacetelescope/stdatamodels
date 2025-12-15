import warnings

from .model_base import JwstDataModel

__all__ = ["AmiLgModel"]


class AmiLgModel(JwstDataModel):
    """
    A data model for AMI LG analysis results.

    Attributes
    ----------
    fit_image : numpy float32 array
         Fitted image
    resid_image : numpy float32 array
         Residual image
    closure_amp_table : numpy table
         Closure amplitudes table
    closure_phase_table : numpy table
         Closure phases table
    fringe_amp_table : numpy table
         Fringe amplitudes table
    fringe_phase_table : numpy table
         Fringe phases table
    pupil_phase_table : numpy table
         Pupil phases table
    solns_table : numpy table
         Solutions table
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/amilg.schema"

    def __init__(self, init=None, **kwargs):
        warnings.warn(
            "AmiLgModel is deprecated and will be removed in a future version. "
            "Please use AmiLgFitModel instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(init=init, **kwargs)

    def get_primary_array_name(self):  # noqa: D102
        return "fit_image"
