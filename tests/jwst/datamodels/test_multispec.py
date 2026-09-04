from astropy.io import fits

from stdatamodels.jwst.datamodels import WFSSMultiSpecModel, WFSSSpecModel


def test_old_wfss_multispec(tmp_path):
    """Generate WFSSMultiSpecModel without the new contam_flux and contam_surf_bright columns."""
    new_colnames = ["CONTAM_FLUX", "CONTAM_SURF_BRIGHT"]

    # Create a np recarray with old-style columns
    default_spectable = WFSSSpecModel().get_default("spec_table")

    # make a WFSSMultiSpecModel with a few extensions
    fname = tmp_path / "wfss_multispec.fits"
    with WFSSMultiSpecModel() as model:
        for i in range(3):
            model.spec.append(WFSSSpecModel())
            model.spec[i].spec_table = default_spectable
        model.save(fname)

    # Create old-style hdu in astropy fits because datamodel won't allow
    # assignment or save if the table has the wrong number of columns,
    # regardless of any of the validation strictness flags
    with fits.open(fname) as hdulist:
        for ext in hdulist:
            if ext.name == "EXTRACT1D":
                # delete two columns from the table
                for name in new_colnames:
                    table_data = ext.data
                    # for both missing attributes, find the schema-defined index in the table
                    # and add a NaN-filled column at that index
                    idx = table_data.dtype.names.index(name)
                    new_cols = fits.ColDefs(ext.columns[:idx]) + fits.ColDefs(
                        ext.columns[idx + 1 :]
                    )

                    # 3. Create a temporary HDU to extract the correct data and header
                    new_hdu = fits.BinTableHDU.from_columns(new_cols)

                    # Update the existing extension's data and header
                    ext.data = new_hdu.data
                    ext.header.update(new_hdu.header)

        # check that the setup worked: isn't empty but it doesn't contain the contam columns
        for name in new_colnames:
            assert name not in hdulist[1].data.columns.names
        assert "FLUX" in hdulist[1].data.columns.names

        # Now try to instantiate a WFSSMultiSpecModel from this hdulist
        # and check that the columns have been restored
        with WFSSMultiSpecModel(hdulist) as model:
            for spec in model.spec:
                tab = spec.spec_table
                for name in new_colnames:
                    assert name in tab.columns.names
