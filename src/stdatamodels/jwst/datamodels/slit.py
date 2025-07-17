from .model_base import JwstDataModel


__all__ = ["SlitModel", "SlitDataModel"]


class SlitDataModel(JwstDataModel):
    """
    A data model for 2D slit images.

    Attributes
    ----------
    data : numpy float32 array
        The science data
    dq : numpy uint32 array
        Data quality array
    err : numpy float32 array
        Error array
    var_poisson : numpy float32 array
        variance due to poisson noise
    var_rnoise : numpy float32 array
        variance due to read noise
    var_flat : numpy float32 array
        variance due to flat
    wavelength : numpy float32 array
        Wavelength array, corrected for zero-point
    barshadow : numpy float32 array
        Bar shadow correction
    flatfield_point : numpy float32 array
        flatfield array for point source
    flatfield_uniform : numpy float32 array
        flatfield array for uniform source
    pathloss_point : numpy float32 array
        pathloss array for point source
    pathloss_uniform : numpy float32 array
        pathloss array for uniform source
    photom_point : numpy float32 array
        photom array for point source
    photom_uniform : numpy float32 array
        photom array for uniform source
    area : numpy float32 array
        Pixel area map array
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/slitdata.schema"

    def __init__(self, init=None, **kwargs):
        """
        Handle kwargs in a custom way.

        This allows MultiSlitModel.__getitem__ to create SlitModel objects from ObjectNode.
        """
        super(SlitDataModel, self).__init__(init=init, **kwargs)
        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])


class SlitModel(JwstDataModel):
    """
    A data model for 2D images.

    Attributes
    ----------
    data : numpy float32 array
        The science data
    dq : numpy uint32 array
        Data quality array
    err : numpy float32 array
        Error array
    var_poisson : numpy float32 array
        Variance due to poisson noise
    var_rnoise : numpy float32 array
        Variance due to read noise
    var_flat : numpy float32 array
        Variance due to flat
    wavelength : numpy float32 array
        Wavelength array, corrected for zero-point
    barshadow : numpy float32 array
        Bar shadow correction
    flatfield_point : numpy float32 array
        Flatfield array for point source
    flatfield_uniform : numpy float32 array
        Flatfield array for uniform source
    pathloss_point : numpy float32 array
        Pathloss array for point source
    pathloss_uniform : numpy float32 array
        Pathloss array for uniform source
    photom_point : numpy float32 array
        Photom array for point source
    photom_uniform : numpy float32 array
        Photom array for uniform source
    area : numpy float32 array
        Pixel area map array
    int_times : numpy table
        Table of times for each integration
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/slit.schema"

    def __init__(self, init=None, **kwargs):
        """
        Handle kwargs in a custom way.

        This allows MultiSlitModel.__getitem__ to create SlitModel objects from ObjectNode.
        """
        super(SlitModel, self).__init__(init=init, **kwargs)
        if kwargs:
            for key in kwargs:
                setattr(self, key, kwargs[key])
