from .model_base import JwstDataModel


__all__ = ['OutlierIFUOutputModel']


class OutlierIFUOutputModel(JwstDataModel):
    """
    A data model for the optional output from outlier_detection_ifu  step.

    In the parameter definitions below, `n` is the number of
    exposures,  `ny` and `nx` are the height and width of the image.

    Parameters
    __________

    diffarr : numpy float32 array (n, ny, nx)
        Minimum difference array for all the data

    minarr : numpy float32 array (ny, nx)
        Final combined minimum difference array

    normarr : numpy float32 array (ny, nx)
        Normalized minarr

    minnorm : numpy float32 array (ny, nx)
        minarr/normarr

    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/outlierifuoutput.schema"
