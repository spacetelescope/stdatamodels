import numpy as np
from astropy.io import fits

import stdatamodels.jwst.datamodels as dm

N_SOURCES = 25
N_WAVELENGTHS = 10


def _make_2d_spectable(base_dtype, metadata_cols, n_sources=N_SOURCES, n_wavelengths=N_WAVELENGTHS):
    """Build a spec_table array with (n_sources, n_wavelengths) shaped spectral columns.

    `base_dtype` is the schema-derived (scalar-only) dtype; `metadata_cols` are the
    columns that stay one-per-source (shape (n_sources,)) instead of being expanded
    to (n_sources, n_wavelengths).
    """
    fields = []
    for name in base_dtype.names:
        subdtype = base_dtype.fields[name][0]
        if name in metadata_cols:
            fields.append((name, subdtype))
        else:
            fields.append((name, subdtype, (n_wavelengths,)))
    return np.zeros((n_sources,), dtype=np.dtype(fields))


def test_legacy_wfss_multispec(tmp_path):
    """Generate WFSSMultiSpecModel without the new contam_flux and contam_surf_bright columns."""
    new_colnames = ["CONTAM_FLUX", "CONTAM_SURF_BRIGHT"]
    metadata_cols = [
        "SOURCE_ID",
        "N_ALONGDISP",
        "SOURCE_TYPE",
        "SOURCE_XPOS",
        "SOURCE_YPOS",
        "SOURCE_RA",
        "SOURCE_DEC",
        "EXTRACT2D_XSTART",
        "EXTRACT2D_YSTART",
        "EXTRACT2D_XSTOP",
        "EXTRACT2D_YSTOP",
    ]

    # Create a np recarray with old-style columns
    default_dtype = dm.WFSSSpecModel().get_dtype("spec_table")
    default_spectable = _make_2d_spectable(default_dtype, metadata_cols)

    # make a WFSSMultiSpecModel with a few extensions
    fname = tmp_path / "wfss_multispec.fits"
    with dm.WFSSMultiSpecModel() as model:
        for _ in range(3):
            model.spec.append(dm.WFSSSpecModel(spec_table=default_spectable.copy()))
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

                    # Create a temporary HDU to extract the correct data and header
                    new_hdu = fits.BinTableHDU.from_columns(new_cols)

                    # Update the existing extension's data and header
                    ext.data = new_hdu.data
                    ext.header.update(new_hdu.header)

        # check that the setup worked: isn't empty but it doesn't contain the contam columns
        for name in new_colnames:
            assert name not in hdulist[1].data.columns.names
        assert "FLUX" in hdulist[1].data.columns.names

        # Now try to instantiate the model from this hdulist
        # and check that the columns have been restored
        with dm.WFSSMultiSpecModel(hdulist) as model:
            for spec in model.spec:
                tab = spec.spec_table
                for name in new_colnames:
                    assert name in tab.columns.names
                    assert tab[name].shape == (N_SOURCES, N_WAVELENGTHS)
                    assert np.all(np.isnan(tab[name]))  # new columns are filled with NaNs


def test_legacy_wfss_combinedspec(tmp_path):
    """Generate WFSSCombinedSpecModel without the new contam_flux and contam_surf_bright columns."""
    new_colnames = ["CONTAM_FLUX", "CONTAM_SURF_BRIGHT"]
    metadata_cols = ["SOURCE_ID", "N_ALONGDISP", "SOURCE_TYPE", "SOURCE_RA", "SOURCE_DEC"]

    # Create a np recarray with old-style columns
    default_dtype = dm.WFSSCombinedSpecModel().get_dtype("spec_table")
    default_spectable = _make_2d_spectable(default_dtype, metadata_cols)

    # make a WFSSCombinedSpecModel with a few extensions
    fname = tmp_path / "wfss_combinedspec.fits"
    with dm.WFSSMultiCombinedSpecModel() as model:
        for _ in range(3):
            model.spec.append(dm.WFSSCombinedSpecModel(spec_table=default_spectable.copy()))
        model.save(fname)

    # Create old-style hdu in astropy fits because datamodel won't allow
    # assignment or save if the table has the wrong number of columns,
    # regardless of any of the validation strictness flags
    with fits.open(fname) as hdulist:
        for ext in hdulist:
            if ext.name == "COMBINE1D":
                # delete two columns from the table
                for name in new_colnames:
                    table_data = ext.data
                    # for both missing attributes, find the schema-defined index in the table
                    # and add a NaN-filled column at that index
                    idx = table_data.dtype.names.index(name)
                    new_cols = fits.ColDefs(ext.columns[:idx]) + fits.ColDefs(
                        ext.columns[idx + 1 :]
                    )

                    # Create a temporary HDU to extract the correct data and header
                    new_hdu = fits.BinTableHDU.from_columns(new_cols)

                    # Update the existing extension's data and header
                    ext.data = new_hdu.data
                    ext.header.update(new_hdu.header)

        # check that the setup worked: isn't empty but it doesn't contain the contam columns
        for name in new_colnames:
            assert name not in hdulist[1].data.columns.names
        assert "FLUX" in hdulist[1].data.columns.names

        # Now try to instantiate the model from this hdulist
        # and check that the columns have been restored
        with dm.WFSSMultiCombinedSpecModel(hdulist) as model:
            for spec in model.spec:
                tab = spec.spec_table
                for name in new_colnames:
                    assert name in tab.columns.names
                    assert tab[name].shape == (N_SOURCES, N_WAVELENGTHS)
                    assert np.all(np.isnan(tab[name]))  # new columns are filled with NaNs
