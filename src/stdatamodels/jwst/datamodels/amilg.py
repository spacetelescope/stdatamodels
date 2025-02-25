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

    def get_primary_array_name(self):  # noqa: D102
        return "fit_image"
