import warnings
import sys
import traceback

from stdatamodels.exceptions import ValidationWarning

from .reference import ReferenceFileModel


__all__ = ["TsoPhotModel"]


class TsoPhotModel(ReferenceFileModel):
    """A model for a reference file of type "tsophot"."""

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/tsophot.schema"
    reftype = "tsophot"

    def __init__(self, init=None, radii=None, **kwargs):
        """
        Initialize the model.

        Parameters
        ----------
        init : str, tuple, `~astropy.io.fits.HDUList`, ndarray, dict, None, optional
            The data from which to initialize the model. Can be of any type that
            is supported by DataModel.
        radii : list, optional
            List of one or more dictionaries, each with keys 'pupil', 'radius',
            'radius_inner', and 'radius_outer'.
        **kwargs
            Additional keyword arguments passed to ReferenceFileModel.
        """
        super(TsoPhotModel, self).__init__(init=init, **kwargs)
        if radii is not None:
            self.radii = radii

    def on_save(self, path=None):  # noqa: D102
        self.meta.reftype = self.reftype

    def to_fits(self):  # noqa: D102
        raise NotImplementedError("FITS format is not supported for this file.")

    def validate(self):  # noqa: D102
        super(TsoPhotModel, self).validate()
        try:
            assert len(self.radii) > 0
            assert self.meta.instrument.name in ["MIRI", "NIRCAM"]
            assert self.meta.exposure.type in ["MIR_IMAGE", "NRC_TSIMAGE"]
        except AssertionError:
            if self._strict_validation:
                raise
            else:
                tb = sys.exc_info()[-1]
                tb_info = traceback.extract_tb(tb)
                text = tb_info[-1][-1]
                warnings.warn(text, ValidationWarning, stacklevel=2)
