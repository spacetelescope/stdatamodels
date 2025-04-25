from .model_base import JwstDataModel
from .spec import SpecModel, MRSSpecModel, TSOSpecModel


__all__ = ["MultiSpecModel", "MRSMultiSpecModel", "TSOMultiSpecModel"]


class MultiSpecModel(JwstDataModel):
    """
    A data model for multi-spec tables.

    This model has a special member `spec` that can be used to
    deal with an entire spectrum at a time.  It behaves like a list::

       >>> from stdatamodels.jwst.datamodels import SpecModel
       >>> multispec_model = MultiSpecModel()
       >>> multispec_model.spec.append(SpecModel())
       >>> multispec_model.spec[0] # doctest: +SKIP
       <SpecModel>

    If `init` is a `SpecModel` instance, an empty `SpecModel` will be
    created and assigned to attribute `spec[0]`, and the `spec_table`
    attribute from the input `SpecModel` instance will be copied to
    the first element of `spec`.  `SpecModel` objects can be appended
    to the `spec` attribute by using its `append` method.

    Attributes
    ----------
    int_times : numpy table
         table of times for each integration
    spec.items.spec_table : numpy table
         Extracted spectral data table

    Examples
    --------
    >>> output_model = MultiSpecModel()
    >>> spec = SpecModel()  # for the default data type
    >>> for slit in input_model.slits:  # doctest: +SKIP
    ...     slitname = slit.name
    ...     slitmodel = ExtractModel()
    ...     slitmodel.fromJSONFile(extref, slitname)
    ...     column, wavelength, countrate = slitmodel.extract(slit.data)
    ...     otab = np.array(zip(column, wavelength, countrate), dtype=spec.spec_table.dtype)
    ...     spec = datamodels.SpecModel(spec_table=otab)
    ...     output_model.spec.append(spec)
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/multispec.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, SpecModel):
            super(MultiSpecModel, self).__init__(init=None, **kwargs)
            self.spec.append(self.spec.item())
            self.spec[0].spec_table = init.spec_table
            return

        super(MultiSpecModel, self).__init__(init=init, **kwargs)


class MRSMultiSpecModel(JwstDataModel):
    """
    A data model for MIRI MRS multi-spec tables.

    This model has a special member `spec` that can be used to
    deal with an entire spectrum at a time.  It behaves identically
    to `MultiSpecModel`, except that the spectra have additional columns
    for the MIRI MRS mode, containing residual fringe corrected values.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/mrs_multispec.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, MRSSpecModel):
            super(MRSMultiSpecModel, self).__init__(init=None, **kwargs)
            self.spec.append(self.spec.item())
            self.spec[0].spec_table = init.spec_table
            return

        super(MRSMultiSpecModel, self).__init__(init=init, **kwargs)


class TSOMultiSpecModel(JwstDataModel):
    """
    A data model for TSO multi-integration, multi-spectra tables.

    This model has a special member `spec` that is used to contain spectra
    from multiple integrations at a time.  It behaves identically
    to `MultiSpecModel`, except that each row in the spectral
    table corresponds to the full spectrum for a single integration,
    so that all integrations are stored in the same EXTRACT1D
    extension.  For the standard MultiSpecModel, column data is
    one-dimensional for each extension.  For this model, column data is
    two-dimensional.

    In addition, the spectra for this model have additional columns
    to contain the segment number and integration identifying the spectrum
    in each row.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/tso_multispec.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, TSOSpecModel):
            super(TSOMultiSpecModel, self).__init__(init=None, **kwargs)
            self.spec.append(self.spec.item())
            self.spec[0].spec_table = init.spec_table
            return

        super(TSOMultiSpecModel, self).__init__(init=init, **kwargs)
