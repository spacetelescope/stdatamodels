from .model_base import JwstDataModel


__all__ = ['AmiLgFitModel']


class AmiLgFitModel(JwstDataModel):
    """
    A data model for AMI LG analysis results.

    Parameters
    ----------

    centered_image : numpy float32 array
        Centered image
    norm_centered_image : numpy float32 array
        Centered image normalized by data peak
    fit_image : numpy float32 array
        Fitted image
    norm_fit_image : numpy float32 array
        Fitted image normalized by data peak
    resid_image : numpy float32 array
        Residual image
    norm_resid_image : numpy float32 array
        Residual image normalized by data peak
    solns_table : numpy table
        Solutions table
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/amilgfitmodel.schema"

    def get_primary_array_name(self):
        """
        Returns the name "primary" array for this model, which
        controls the size of other arrays that are implicitly created.
        This is intended to be overridden in the subclasses if the
        primary array's name is not "data".
        """
        return 'fit_image'
