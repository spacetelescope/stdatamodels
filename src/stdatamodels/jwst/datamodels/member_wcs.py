from astropy import wcs

from .reference import ReferenceFileModel

__all__ = ["MemberWcsModel", "MemberWcsSingleModel"]


class MemberWcsModel():
    """
    A data model for storing WCS objects from a list of image models.

    This model is meant to store all WCS objects from input images used to generate
    a mosaic during image resampling.  It behaves like a list::

       >>> from stdatamodels.jwst.datamodels import MemberWcsModel
       >>> memberwcs_model = MemberWcsModel()
       >>> memberwcs_model.member_wcs.append(MemberWcsSingleModel())
       >>> memberwcs_model.member_wcs[0] # doctest: +SKIP
       <MemberWcsSingleModel>

    If `init` is a `MemberWcsSingleModel` instance, an empty `MemberWcsSingleModel`
    will be created and assigned to attribute `member_wcs[0]`.
    `SpecProfileSingleModel` objects can be appended to the `member_wcs` attribute
    by using its `append` method.

    Attributes
    ----------
    member_wcs.items.wcs : ~`gwcs.wcs.WCS` object
         Imaging WCS object.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/member_wcs.schema"

    def __init__(self, init=None, **kwargs):
        if isinstance(init, MemberWcsSingleModel):
            self.member_wcs.append(self.profile.item())
            self.member_wcs[0].filename = init.filename
            self.member_wcs[0].wcs = init.wcs

        super(SpecProfileModel, self).__init__(init=init, **kwargs)


class MemberWcsSingleModel():
    """
    A simple data model to store a filename and associated imaging WCS object.

    Attributes
    ----------
    filename : string
         The mosaic member filename.
    wcs : ~`gwcs.wcs.WCS` object
        The member's image WCS object.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/member_wcs_single.schema"
