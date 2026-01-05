from .reference import ReferenceFileModel

__all__ = ["RSCDModel"]


class RSCDModel(ReferenceFileModel):
    """
    A data model for the RSCD reference file.

    Attributes
    ----------
    rscd_group_skip_table : numpy table
        Reference table for RSCD correction baseline correction
        A table with 4 columns that set the number of groups to skip for each
        subarray and readpatt
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/rscd.schema"
