from .model_base import JwstDataModel

__all__ = ['AmiOIModel']


class AmiOIModel(JwstDataModel):
    """
    TODO

    Parameters
    __________
    TODO
    """
    schema_url = "http://stsci.edu/schemas/jwst_datamodel/amioi.schema"

    # TODO
    # def get_primary_array_name(self):

    def on_save(self, path=None):
        super().on_save(path)

        # OIFITS requires specific keyword names for some data that already
        # exist in JWST files under different keywords. For existing
        # (and defined) metadata, copy the data to the OIFITS compatible
        # locations

        if self.meta.oi_fits.observer is None:
            if self.meta.program.pi_name is not None:
                self.meta.oi_fits.observer = self.meta.program.pi_name
            else:
                msg = "OIFITS requires meta.oi_fits.observer or meta.program.pi_name"
                raise ValueError(msg)
        if self.meta.oi_fits.object is None:
            if self.meta.target.proposer_name is not None:
                self.meta.oi_fits.object = self.meta.target.proposer_name
            elif self.meta.target.catalog_name is not None:
                self.meta.oi_fits.object = self.meta.target.catalog_name
            else:
                msg = "OIFITS requires meta.oi_fits.object or meta.target.proposer_name or meta.target.catalog_name"
                raise ValueError(msg)

        # TODO what to set for mode?
        if self.meta.oi_fits.instrument_mode is None:
            self.meta.oi_fits.instrument_mode = 'NRM'

        # This file contains OIFITS2 content
        self.meta.oi_fits.content = 'OIFITS2'

        # each OIFITS data table needs specific cross-referencing keywords
        array_name = self.oi_array_meta.arrname
        if array_name is None:
            raise ValueError("oi_array_meta.arrname must be defined")
        self.oi_vis_meta.array_name = array_name
        self.oi_vis2_meta.array_name = array_name
        self.oi_t3_meta.array_name = array_name

        insname = self.meta.instrument.name
        if insname is None:
            raise ValueError("meta.instrument.name must be defined")
        self.oi_wavelength_meta.instrument_name = insname
        self.oi_vis_meta.instrument = insname
        self.oi_vis2_meta.instrument = insname
        self.oi_t3_meta.instrument = insname

        # TODO observation date
        # JWST saves meta.observation.date to DATE-OBS
        # which is the UTC date for the observation start
        # In Table 2 of the OIFITS 2 paper:
        # https://doi.org/10.48550/arXiv.1510.04556
        # However it's unclear is this format is required
        # and if a UTC date is valid.
        # Currently this code leaves the value as-is (expressed
        # as a date only) to avoid complications for other JWST
        # code.
        date_obs = self.meta.observation.date
        if date_obs is None:
            raise ValueError("meta.observation.date must be defined")
        self.oi_vis_meta.date_obs = date_obs
        self.oi_vis2_meta.date_obs = date_obs
        self.oi_t3_meta.date_obs = date_obs

        self.oi_wavelength_meta.revn = 2
        self.oi_array_meta.revn = 2
        self.oi_target_meta.revn = 2
        self.oi_vis_meta.revn = 2
        self.oi_vis2_meta.revn = 2
        self.oi_t3_meta.revn = 2

        # fill in possibly missing OI_ARRAY meta data
        if self.oi_array_meta.frame is None:
            self.oi_array_meta.frame = 'SKY'
        if self.oi_array_meta.x is None:
            self.oi_array_meta.x = 0.0
        if self.oi_array_meta.y is None:
            self.oi_array_meta.y = 0.0
        if self.oi_array_meta.z is None:
            self.oi_array_meta.z = 0.0
