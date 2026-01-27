from stdatamodels.jwst.datamodels.model_base import DQMixin, JwstDataModel

__all__ = ["GuiderCalModel", "GuiderRawModel"]


class GuiderRawModel(JwstDataModel, DQMixin):
    """
    A data model for Guide Star pipeline raw data files.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    err : numpy float32 array
         Error array
    dq : numpy uint32 array
         Data quality array
    planned_star_table : numpy table
         Planned reference star table
    flight_star_table : numpy table
         Flight reference star table
    pointing_table : numpy table
         Pointing table
    centroid_table : numpy table
         Centroid packet table
    track_sub_table : numpy table
         Track subarray data table
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/guider_raw.schema"


class GuiderCalModel(JwstDataModel, DQMixin):
    """
    A data model for Guide Star pipeline calibrated files.

    Attributes
    ----------
    data : numpy float32 array
         The science data
    err : numpy float32 array
         Error array
    dq : numpy uint32 array
         Data quality array
    planned_star_table : numpy table
         Planned reference star table
    flight_star_table : numpy table
         Flight reference star table
    pointing_table : numpy table
         Pointing table
    centroid_table : numpy table
         Centroid packet table
    track_sub_table : numpy table
         Track subarray data table
    """

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/guider_cal.schema"
