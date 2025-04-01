from .model_base import JwstDataModel
from .image import ImageModel
from .slit import SlitModel, SlitDataModel


__all__ = ["MultiSlitModel"]


class MultiSlitModel(JwstDataModel):
    """
    A data model for multi-slit images.

    This model has a special member `slits` that can be used to
    deal with an entire slit at a time.  It behaves like a list::

        >>> from stdatamodels.jwst.datamodels import SlitModel
        >>> multislit_model = MultiSlitModel()
        >>> multislit_model.slits.append(SlitModel())
        >>> multislit_model[0]
        <SlitModel>

    If ``init`` is a file name or an ``ImageModel`` or a ``SlitModel``instance,
    an empty ``SlitModel`` will be created and assigned to attribute ``slits[0]``,
    and the `data`, ``dq``, ``err``, ``var_rnoise``, and ``var_poisson``
    attributes from the input file or model will be copied to the
    first element of ``slits``.

    Attributes
    ----------
    slits : list of SlitModel
        The slits in the model; see SlitModel for details.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/multislit.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, (SlitModel, ImageModel)):
            super(MultiSlitModel, self).__init__(init=None, **kwargs)
            self.update(init)
            slitdata = SlitDataModel(init)
            self.slits.append(slitdata)
            return

        super(MultiSlitModel, self).__init__(init=init, **kwargs)

    def __getitem__(self, key):
        """
        Return a metadata value using a dotted name or a ``SlitModel``.

        Parameters
        ----------
        key : str or int
            A dotted name identifying a metadata field or a slit number.

        Returns
        -------
        value : any
            The value of the metadata field or the ``SlitModel`` instance.
        """
        if isinstance(key, str) and key.split(".")[0] == "meta":
            res = super(MultiSlitModel, self).__getitem__(key)
            return res
        elif isinstance(key, int):
            # Return an instance of a SlitModel
            # This only executes when the top object level
            # is called: object[1].key not object.slits[key]
            try:
                slit = self.slits[key]  # returns an ObjectNode instance
            except IndexError as err:
                raise (f"Slit {key} doesn't exist") from err
            kwargs = {}
            items = dict(slit.items())
            for key in items:
                if not key.startswith(("meta", "extra_fits")):
                    kwargs[key] = items[key]
            s = SlitModel(**kwargs)
            s.update(self)

            if slit.meta.hasattr("wcs"):
                s.meta.wcs = slit.meta.wcs
            return s
        else:
            raise ValueError(f"Invalid key {key}")
