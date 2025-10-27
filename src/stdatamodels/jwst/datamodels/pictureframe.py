from .reference import ReferenceFileModel

__all__ = ["PictureFrameModel"]


class PictureFrameModel(ReferenceFileModel):
    """
    A data model for 2D thermal picture frame reference files.

    Attributes
    ----------
    data : numpy float32 array
        Picture frame slope data.
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/pictureframe.schema"

    def __init__(self, init=None, **kwargs):
        super(PictureFrameModel, self).__init__(init=init, **kwargs)
