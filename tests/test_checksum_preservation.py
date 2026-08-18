import numpy as np
from astropy.io import fits

from .models import FitsModel


def test_save_recalculates_existing_checksums(tmp_path):
    """Saving a checksummed FITS model recalculates checksums after modification."""
    source = tmp_path / "checksummed.fits"
    output = tmp_path / "checksummed_updated.fits"
    data = np.arange(4, dtype=np.float32).reshape(2, 2)

    with FitsModel(data=data) as model:
        model.save(source, checksum=True)

    with FitsModel(source) as model:
        model.data[0, 0] = 42
        model.save(output)

    with fits.open(output) as hdulist:
        assert all(hdu.verify_checksum() == 1 for hdu in hdulist)
        assert all(hdu.verify_datasum() == 1 for hdu in hdulist)


def test_save_does_not_add_checksums_when_absent(tmp_path):
    """Saving an unchecked FITS model does not introduce checksum keywords."""
    source = tmp_path / "unchecked.fits"
    output = tmp_path / "unchecked_updated.fits"
    data = np.arange(4, dtype=np.float32).reshape(2, 2)

    with FitsModel(data=data) as model:
        model.save(source)

    with FitsModel(source) as model:
        model.save(output)

    with fits.open(output) as hdulist:
        assert all("CHECKSUM" not in hdu.header for hdu in hdulist)
        assert all("DATASUM" not in hdu.header for hdu in hdulist)
