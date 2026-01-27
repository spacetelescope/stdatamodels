import copy

from astropy.time import Time

from stdatamodels import DataModel as _DataModel
from stdatamodels.dynamicdq import dynamic_mask

from .dqflags import pixel

__all__ = ["DQMixin", "JwstDataModel"]


class JwstDataModel(_DataModel):
    """Base class for JWST data models."""

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/core.schema"

    @property
    def crds_observatory(self):
        """
        Get CRDS observatory code for this model.

        Returns
        -------
        str
            The observatory code.
        """
        return "jwst"

    def get_crds_parameters(self):
        """
        Get parameters used by CRDS to select references for this model.

        Returns
        -------
        dict
            Dictionary of CRDS parameters
        """
        return {
            key: val
            for key, val in self.to_flat_dict(include_arrays=False).items()
            if isinstance(val, (str, int, float, complex, bool))
        }

    def on_init(self, init):
        """
        Run a hook before returning a newly created model instance.

        Parameters
        ----------
        init : object
            First argument to __init__.
        """
        super().on_init(init)

        if not self.meta.hasattr("date"):
            self.meta.date = Time.now().isot

    def on_save(self, init):
        """
        Run a hook before writing a model to a file (FITS or ASDF).

        Parameters
        ----------
        init : str
            The path to the file that we're about to save to.
        """
        super().on_save(init)

        self.meta.date = Time.now().isot

    def update(self, d, only=None, extra_fits=False, cal_logs=True):
        """
        Update this model with the metadata elements from another model.

        Note: The ``update`` method skips a WCS object, if present.

        Parameters
        ----------
        d : `~stdatamodels.jwst.datamodels.JwstDataModel` or dictionary-like object
            The model to copy the metadata elements from. Can also be a
            dictionary or dictionary of dictionaries or lists.
        only : str, list of str, or None
            Update only the named hdu, e.g. ``only='PRIMARY'``. Can either be
            a string or list of hdu names. If None, all hdus will be updated.
        extra_fits : bool
            Update from ``extra_fits`` as well as ``meta``.
        cal_logs : bool
            Update from ``cal_logs`` as well as ``meta``.
        """
        # Get the cal logs first
        if isinstance(d, _DataModel):
            # Get cal logs if present
            if d.hasattr("cal_logs"):
                logs = copy.deepcopy(d.cal_logs._instance)
            else:
                logs = {}
        else:
            # Dictionary-like input: get cal_logs from the updates
            # and remove them before calling the parent method.
            # NOTE: If cal_logs is not removed in the input dictionary,
            # it will cause an inscrutable crash in the parent update.
            # It has non-meta handling for extra_fits only.
            d = copy.deepcopy(d)
            logs = d.pop("cal_logs", {})

        # Update logs if needed
        if cal_logs and logs:
            if not self.hasattr("cal_logs"):
                # Set logs from other model if not present yet
                self.cal_logs = logs
            else:
                # Update the logs dictionary from the other model
                self.cal_logs._instance.update(logs)

        # Call the parent update
        super().update(d, only=only, extra_fits=extra_fits)


class DQMixin(_DataModel):
    """Mixin for models that should have dq array initialized on init."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If data array hasn't been initialized, do not initialize DQ
        if not hasattr(self, self.get_primary_array_name()):
            return

        # Otherwise, ensure DQ array exists
        if not hasattr(self, "dq"):
            self.dq = self.get_default("dq")

        # if dq_def is in the schema, attempt to apply dq flag mapping
        if self.hasattr("dq_def"):
            self.dq = dynamic_mask(self, pixel)

        # do the same handling for err array
        # this is only here to minimize number of downstream failures and
        # should be removed in the future once we can fix downstream patterns
        if not hasattr(self, "err") and "err" in self.schema["properties"]:
            self.err = self.get_default("err")
