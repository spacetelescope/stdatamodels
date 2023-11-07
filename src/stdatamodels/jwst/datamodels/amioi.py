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

    def get_primary_array_name(self):
        # for the example file OI_T3 is the largest array
        return 't3'

    def _map_oifits_keywords(self):
        # OIFITS requires specific keyword names for some data that already
        # exist in JWST files under different keywords. For existing
        # (and defined) metadata, copy the data to the OIFITS compatible
        # locations

        self.meta.oifits.derived.observer = self.meta.program.pi_name
        self.meta.oifits.derived.object = self.meta.target.proposer_name or self.meta.target.catalog_name

        # This file contains OIFITS2 content
        self.meta.oifits.derived.content = 'OIFITS2'

        # each OIFITS data table needs specific cross-referencing keywords
        array_name = self.meta.oifits.array_name
        self.meta.oifits.derived.t3.array_name = array_name
        self.meta.oifits.derived.vis.array_name = array_name
        self.meta.oifits.derived.vis2.array_name = array_name

        insname = self.meta.instrument.name
        self.meta.oifits.derived.wavelength.instrument_name = insname
        self.meta.oifits.derived.t3.instrument_name = insname
        self.meta.oifits.derived.vis.instrument_name = insname
        self.meta.oifits.derived.vis2.instrument_name = insname

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
        self.meta.oifits.derived.t3.date_obs = date_obs
        self.meta.oifits.derived.vis.date_obs = date_obs
        self.meta.oifits.derived.vis2.date_obs = date_obs

        self.meta.oifits.derived.array.revn = 2
        self.meta.oifits.derived.target.revn = 2
        self.meta.oifits.derived.t3.revn = 2
        self.meta.oifits.derived.vis.revn = 2
        self.meta.oifits.derived.vis2.revn = 2
        self.meta.oifits.derived.wavelength.revn = 2

        # fill in possibly missing OI_ARRAY meta data
        if self.meta.oifits.derived.array.frame is None:
            self.meta.oifits.derived.array.frame = 'SKY'
        if self.meta.oifits.derived.array.x is None:
            self.meta.oifits.derived.array.x = 0.0
        if self.meta.oifits.derived.array.y is None:
            self.meta.oifits.derived.array.y = 0.0
        if self.meta.oifits.derived.array.z is None:
            self.meta.oifits.derived.array.z = 0.0

    def on_save(self, path=None):
        super().on_save(path)
        self._map_oifits_keywords()

    def validate(self):
        # map the JWST to OIFITS keywords prior to validate
        self._map_oifits_keywords()
        super().validate()
