import numpy as np
from astropy.io import fits
from numpy.lib.recfunctions import merge_arrays

from .model_base import JwstDataModel
from .spec import MRSSpecModel, SpecModel, TSOSpecModel, WFSSSpecModel

__all__ = ["MRSMultiSpecModel", "MultiSpecModel", "TSOMultiSpecModel", "WFSSMultiSpecModel"]


class MultiSpecModel(JwstDataModel):
    """
    A data model for multi-spec tables.

    This model has a special member ``spec`` that can be used to
    deal with an entire spectrum at a time.  It behaves like a list::

       >>> from stdatamodels.jwst.datamodels import SpecModel
       >>> multispec_model = MultiSpecModel()
       >>> multispec_model.spec.append(SpecModel())
       >>> multispec_model.spec[0] # doctest: +SKIP
       <SpecModel>

    If ``init`` is a `~stdatamodels.jwst.datamodels.SpecModel` instance,
    an empty `~stdatamodels.jwst.datamodels.SpecModel` will be
    created and assigned to attribute ``spec[0]``, and the ``spec_table``
    attribute from the input `~stdatamodels.jwst.datamodels.SpecModel`
    instance will be copied to the first element of ``spec``.
    `~stdatamodels.jwst.datamodels.SpecModel` objects can be appended
    to the ``spec`` attribute by using its ``append`` method.

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

    This model has a special member ``spec`` that can be used to
    deal with an entire spectrum at a time.  It behaves identically
    to `~stdatamodels.jwst.datamodels.MultiSpecModel`,
    except that the spectra have additional columns
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

    This model has a special member ``spec`` that is used to contain spectra
    from multiple integrations at a time.  It behaves identically
    to `~stdatamodels.jwst.datamodels.MultiSpecModel`, except that each row in the spectral
    table corresponds to the full spectrum for a single integration,
    so that all integrations are stored in the same EXTRACT1D
    extension.  For the standard MultiSpecModel, column data is
    one-dimensional for each extension.  For this model, column data is
    two-dimensional.

    In addition, the spectra for this model have extra columns
    to contain the segment number and integration identifying the spectrum
    in each row, as well as the time tags for the integration.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/tso_multispec.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, TSOSpecModel):
            super(TSOMultiSpecModel, self).__init__(init=None, **kwargs)
            self.spec.append(self.spec.item())
            self.spec[0].spec_table = init.spec_table
            return

        super(TSOMultiSpecModel, self).__init__(init=init, **kwargs)


class WFSSMultiSpecModel(JwstDataModel):
    """
    A data model for a collection of spectra from multiple exposures and/or spectral orders.

    Attributes
    ----------
    spec : list of `~stdatamodels.jwst.datamodels.WFSSSpecModel`
        A list of WFSSSpecModel objects, each containing the
        spectra from a single exposure.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/wfss_multispec.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, WFSSSpecModel):
            # If init is a WFSSSpecModel, convert it to a list
            init = [init]
        super().__init__(init=init, **kwargs)

    def _migrate_hdulist(self, hdulist):
        """Handle old-style files lacking contam estimate table columns."""  # numpydoc ignore: RT01
        for ext in hdulist:
            if ext.name == "EXTRACT1D" and isinstance(ext, fits.BinTableHDU):
                table_data = ext.data.view(np.recarray)
                # for both missing attributes, find the schema-defined table index and datatype
                expected = self.schema["properties"]["spec"]["items"]["properties"]["spec_table"][
                    "datatype"
                ]
                expected_names = [col["name"] for col in expected]
                names = ["CONTAM_FLUX", "CONTAM_SURF_BRIGHT"]
                for name in names:
                    if name not in table_data.dtype.names:
                        # Make the new column and fill it with NaN
                        idx = expected_names.index(name)
                        if table_data.dtype["FLUX"].shape:
                            dtype = [(name, "f4", table_data.dtype["FLUX"].shape)]
                        else:
                            dtype = [(name, "f4")]
                        new_column = np.full(table_data.shape[0], np.nan, dtype=dtype)

                        # Insert new column into the correct position in the table data
                        before_names = [
                            field
                            for field in expected_names[:idx]
                            if field in table_data.dtype.names
                        ]
                        after_names = [
                            field
                            for field in expected_names[idx + 1 :]
                            if field in table_data.dtype.names
                        ]
                        arrays_to_merge = (
                            table_data[before_names],
                            new_column,
                            table_data[after_names],
                        )

                        # Merge them and cast the flat fields back into a recarray
                        table_data = merge_arrays(arrays_to_merge, flatten=True, asrecarray=True)
                ext.data = table_data

        return hdulist
