"""Dictionary of all reviewed and accepted expected differences between stdatamodels and jwstkw."""

# There are some expected differences. One example is an old enum
# value might be supported in the schemas but not in the keyword dictionary
# since new files should only get new enum values.
# These differences are represented in a dict of:
#   key: (HDU, KEYWORD)
#   value: dict of
#     key: difference type (enum, title, path, etc)
#     value: dict of
#       key: name of collection to modify (dmd or kwd)
#       value: dict of
#         key: set operation (difference, union, etc)
#         value: set to pass to the operation
#   notes: string

okifeid_expected_diffs = {
    ("PRIMARY", "ENGQLPTG"): {
        "enum": {
            "dmd": {
                "difference": {"CALCULATED_FULL", "CALCULATED_FULLVA"},
            },
        },
        "notes": """JP-2663: Old values no longer needed in KWD. Will keep in 
                datamodels schemas for backwards compatibility with old
                test suites. No fix needed.""",
    },
    ("PRIMARY", "PATTTYPE"): {
        "enum": {
            "dmd": {
                "difference": {"SUBARRAY-DITHER", "N/A", "FULL-TIGHT", "ANY"},
            },
        },
        "notes": """JP-3711: Old values no longer needed in KWD. Will keep in
                datamodels schemas for backwards compatibility with old
                test suites. No fix needed.""",
    },
    ("PRIMARY", "CATEGORY"): {
        "enum": {
            "dmd": {
                "union": {"AR", "CAL", "COM", "DD", "ENG", "GO", "GTO", "NASA", "SURVEY"},
                "difference": {"MISSING_VALUE"},
            },
        },
        "notes": """No fix needed.""",
    },
    ("PRIMARY", "FOCUSPOS"): {
        "type": {
            "dmd": {
                "union": {"integer"},
            },
        },
        "notes": """Minor type difference. No fix needed.""",
    },
    ("PRIMARY", "MRSPRCHN"): {
        "enum": {
            "dmd": {
                "difference": {"ALL"},
            },
        },
        "notes": """Minor enum difference. No fix needed.""",
    },
    ("EXTRACT1D", "S_REGION"): {
        "title": {
            "dmd": {"Footprint of direct image(s) matched to grism observations"},
            "kwd": {"Spatial extent of grism observations' footprint"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ KEYWORD", "CONVTHRS"): {
        "title": {
            "dmd": {"[pixels] col/row convergence change threshold"},
            "kwd": {"col/row convergence change threshold (pixels)"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ KEYWORD", "FITROFFS"): {
        "title": {
            "dmd": {"[arcsec] roll offset from the least squares fit"},
            "kwd": {"roll offset (arcsec) from the least squares fit"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "FITXSIGM"): {
        "title": {
            "kwd": {"sigma value (arcsec) for the X offset value"},
            "dmd": {"[arcsec] sigma value for the X offset value"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "FITYSIGM"): {
        "title": {
            "kwd": {"sigma value (arcsec) for the Y offset value"},
            "dmd": {"[arcsec] sigma value for the Y offset value"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "IDEAL_X"): {
        "title": {
            "kwd": {"target x ideal coord. (arcsec) at start of TA"},
            "dmd": {"[arcsec] target x ideal coord. at start of TA"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "IDEAL_Y"): {
        "title": {
            "kwd": {"target y ideal coord. (arcsec) at start of TA"},
            "dmd": {"[arcsec] target y ideal coord. at start of TA"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "IDL_ROLL"): {
        "title": {
            "kwd": {"TA start targ roll angle in Idl coord (arcsec)"},
            "dmd": {"[arcsec] TA start targ roll angle in Idl coord"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "OFFSTMAG"): {
        "title": {
            "kwd": {"least squares fit offset magnitude (arcsec)"},
            "dmd": {"[arcsec] least squares fit offset magnitude"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "SAM_ROLL"): {
        "title": {
            "kwd": {"calc. small angle maneuver roll comp (arcsec)"},
            "dmd": {"[arcsec] calc. small angle maneuver roll comp"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "SAM_X"): {
        "title": {
            "kwd": {"calculated small angle maneuver x comp (arcsec)"},
            "dmd": {"[arcsec] calculated small angle maneuver x comp"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "SAM_Y"): {
        "title": {
            "kwd": {"calculated small angle maneuver y comp (arcsec)"},
            "dmd": {"[arcsec] calculated small angle maneuver y comp"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "V2HFOFFS"): {
        "title": {
            "kwd": {"MSA V2 half-facet offset (arcsec)"},
            "dmd": {"[arcsec] MSA V2 half-facet offset"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "V2MSACTR"): {
        "title": {
            "kwd": {"center of MSA in V2 (arcsec)"},
            "dmd": {"[arcsec] center of MSA in V2"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("MSA_TARG_ACQ", "V3MSACTR"): {
        "title": {
            "kwd": {"center of MSA in V3 (arcsec)"},
            "dmd": {"[arcsec] center of MSA in V3"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("OI_T3", "OI_REVN"): {
        "title": {
            "kwd": {"Revision number of the table definition"},
            "dmd": {"Revision number"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("OI_TARGET", "OI_REVN"): {
        "title": {
            "kwd": {"Revision number of the table definition"},
            "dmd": {"Revision number"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("OI_ARRAY", "OI_REVN"): {
        "title": {
            "kwd": {"Revision number of the table definition"},
            "dmd": {"Revision number"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("OI_VIS2", "OI_REVN"): {
        "title": {
            "kwd": {"Revision number of the table definition"},
            "dmd": {"Revision number"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("OI_WAVELENGTH", "OI_REVN"): {
        "title": {
            "kwd": {"Revision number of the table definition"},
            "dmd": {"Revision number"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("POINTING", "DDCFLDPT"): {
        "path": {
            "kwd": {"meta.guidestar_ext.pointing_ddcfldpt"},
            "dmd": {"meta.ddc_field_point"},
        },
        "title": {
            "kwd": {"Differential Distortion Compensation field pt"},
            "dmd": {"Differential Distortion Compensation field point"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("POINTING", "POINTTIM"): {
        "path": {
            "kwd": {"meta.guidestar_ext.pointing_pointtim"},
            "dmd": {"meta.pointing_time"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("OI_T3", "APERNAME"): {
        "title": {
            "kwd": {"S&OC PRD science aperture used"},
            "dmd": {"PRD science aperture used"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("OI_VIS", "APERNAME"): {
        "title": {
            "kwd": {"S&OC PRD science aperture used"},
            "dmd": {"PRD science aperture used"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("OI_VIS2", "APERNAME"): {
        "title": {
            "kwd": {"S&OC PRD science aperture used"},
            "dmd": {"PRD science aperture used"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "ARRNAME"): {
        "title": {
            "kwd": {"S&OC PRD science aperture used"},
            "dmd": {"PRD science aperture used"},
        },
        "notes": """Minor title difference. No fix needed. This is true for all 4 HDUs
            in which this keyword appears (PRIMARY, OI_T3, OI_VIS, OI_VIS2).""",
    },
    ("PRIMARY", "ASNPOOL"): {
        "path": {
            "kwd": {"meta.association.pool_name"},
            "dmd": {"meta.asn.pool_name"},
        },
        "title": {
            "kwd": {"Name of the Association Pool"},
            "dmd": {"Name of the ASN pool"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "ASNTABLE"): {
        "path": {
            "kwd": {"meta.association.table_name"},
            "dmd": {"meta.asn.table_name"},
        },
        "title": {
            "kwd": {"Name of the Association Generator Table"},
            "dmd": {"Name of the ASN table"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "BKGLEVEL"): {
        "title": {
            "kwd": {"Computed constant background level"},
            "dmd": {"Computed/Matched constant background level"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "BKGSUB"): {
        "title": {
            "kwd": {"Constant background subtracted from data?"},
            "dmd": {"Has background been subtracted from data?"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "CALIB"): {
        "path": {
            "kwd": {"meta.ami.calib"},
            "dmd": {"meta.ami.calibrator_object_id"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "CAL_VCS"): {
        "path": {
            "kwd": {"meta.basic.calibration_software_revision"},
            "dmd": {"meta.calibration_software_revision"},
        },
        "title": {
            "kwd": {"Calibration Software Repository Version"},
            "dmd": {"Calibration software version control sys number"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "CAL_VER"): {
        "path": {
            "kwd": {"meta.basic.calibration_software_version"},
            "dmd": {"meta.calibration_software_version"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "CHANNEL"): {
        "title": {
            "kwd": {"NIRCam channel: long or short", "MIRI MRS (IFU) channel"},
            "dmd": {"Instrument channel"},
        },
        "notes": """These title differences are addressed in Datamodels. No fix needed.""",
    },
    ("PRIMARY", "CMD_TSEL"): {
        "path": {
            "kwd": {"meta.instrument.cmd_tsel"},
            "dmd": {"meta.exposure.cmd_tsel"},
        },
        "notes": """Minor path difference of where the keyword is set
                (in Keyword Dictionary) and where it is stored (in Datamodels).
                No fix needed.""",
    },
    ("PRIMARY", "COMPRESS"): {
        "path": {
            "kwd": {"meta.basic.compress"},
            "dmd": {"meta.compress"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "CONTENT"): {
        "path": {
            "kwd": {"meta.ami.content"},
            "dmd": {"meta.oifits.derived.content"},
        },
        "notes": """Minor path difference of where the keyword is set
                (in Keyword Dictionary) and where it is stored (in Datamodels).
                No fix needed.""",
    },
    ("PRIMARY", "CORONMSK"): {
        "enum": {
            "kwd": {
                "difference": {"MASK210R", "MASKLWB", "MASK430R", "NONE", "MASK335R", "MASKSWB"},
            },
        },
        "notes": """Datamodels contains additional obsolete values for backward
                compatibility. No fix needed.""",
    },
    ("PRIMARY", "DATAMODL"): {
        "path": {
            "kwd": {"meta.basic.model_type"},
            "dmd": {"meta.model_type"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "DATE"): {
        "path": {
            "kwd": {"meta.basic.date"},
            "dmd": {"meta.date"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "DATE-BEG"): {
        "title": {
            "kwd": {"Date-time start of exposure", "Date-time start of data acquisition"},
            "dmd": {"Date-time start of exposure"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "DATE-END"): {
        "title": {
            "kwd": {"Date-time end of data acquisition", "Date-time end of exposure"},
            "dmd": {"Date-time end of exposure"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "DATE-OBS"): {
        "title": {
            "kwd": {"UTC date at start of exposure", "UTC date at start of guiding data"},
            "dmd": {"[yyyy-mm-dd] UTC date at start of exposure"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "DETMODE"): {
        "path": {
            "kwd": {"meta.instrument.detmode"},
            "dmd": {"meta.exposure.detmode"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "DIRIMAGE"): {
        "path": {
            "kwd": {"meta.resample.direct_image"},
            "dmd": {"meta.direct_image"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "DITHPNTS"): {
        "title": {
            "kwd": {"Point indices for SPARSE-CYCLING", "Point indices for sparse cycling"},
            "dmd": {"Sparse cycling dither points"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "DRPFRMS1"): {
        "title": {
            "kwd": {"Number of frames dropped before 1st integration"},
            "dmd": {"Number of frames dropped prior to first integration"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "DURATION"): {
        "title": {
            "kwd": {"[s] Total duration of exposure", "[s] Total duration of guiding data in file"},
            "dmd": {"[s] Total duration of exposure"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "ENG_QUAL"): {
        "path": {
            "kwd": {"meta.observation.engineering_quality", "meta.guidestar.engineering_quality"},
            "dmd": {"meta.visit.engineering_quality"},
        },
        "title": {
            "kwd": {"Engineering DB quality indicator", "engineering DB data quality indicator"},
            "dmd": {"Engineering data quality indicator from EngDB"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "EXPRIPAR"): {
        "title": {
            "kwd": {"prime or parallel exposure indicator"},
            "dmd": {"Prime or parallel exposure"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "EXSEGNUM"): {
        "title": {
            "kwd": {"sequential segment number"},
            "dmd": {"Sequential segment number"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "EXSEGTOT"): {
        "title": {
            "kwd": {"total number segments"},
            "dmd": {"Total number of segments"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "FA1VALUE"): {
        "path": {
            "kwd": {"meta.nircam_fam.fa1value"},
            "dmd": {"meta.nircam_focus.fa1value"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FA2VALUE"): {
        "path": {
            "kwd": {"meta.nircam_fam.fa2value"},
            "dmd": {"meta.nircam_focus.fa2value"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FA3VALUE"): {
        "path": {
            "kwd": {"meta.nircam_fam.fa3value"},
            "dmd": {"meta.nircam_focus.fa3value"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAM_LA1"): {
        "path": {
            "kwd": {"meta.nircam_fam.fam_la1"},
            "dmd": {"meta.nircam_focus.fam_la1"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAM_LA2"): {
        "path": {
            "kwd": {"meta.nircam_fam.fam_la2"},
            "dmd": {"meta.nircam_focus.fam_la2"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAM_LA3"): {
        "path": {
            "kwd": {"meta.nircam_fam.fam_la3"},
            "dmd": {"meta.nircam_focus.fam_la3"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAPHASE1"): {
        "path": {
            "kwd": {"meta.nircam_fam.faphase1"},
            "dmd": {"meta.nircam_focus.faphase1"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAPHASE2"): {
        "path": {
            "kwd": {"meta.nircam_fam.faphase2"},
            "dmd": {"meta.nircam_focus.faphase2"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAPHASE3"): {
        "path": {
            "kwd": {"meta.nircam_fam.faphase3"},
            "dmd": {"meta.nircam_focus.faphase3"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FASTEP1"): {
        "path": {
            "kwd": {"meta.nircam_fam.fastep1"},
            "dmd": {"meta.nircam_focus.fastep1"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FASTEP2"): {
        "path": {
            "kwd": {"meta.nircam_fam.fastep2"},
            "dmd": {"meta.nircam_focus.fastep2"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FASTEP3"): {
        "path": {
            "kwd": {"meta.nircam_fam.fastep3"},
            "dmd": {"meta.nircam_focus.fastep3"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAUNIT1"): {
        "path": {
            "kwd": {"meta.nircam_fam.faunit1"},
            "dmd": {"meta.nircam_focus.faunit1"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAUNIT2"): {
        "path": {
            "kwd": {"meta.nircam_fam.faunit2"},
            "dmd": {"meta.nircam_focus.faunit2"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FAUNIT3"): {
        "path": {
            "kwd": {"meta.nircam_fam.faunit3"},
            "dmd": {"meta.nircam_focus.faunit3"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "FILENAME"): {
        "path": {
            "kwd": {"meta.basic.filename"},
            "dmd": {"meta.filename"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "GF_END"): {
        "title": {
            "kwd": {"UTC time when the guider function ended"},
            "dmd": {"Observatory UTC time at guider function end"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "GF_START"): {
        "title": {
            "kwd": {"UTC time when the guider function started"},
            "dmd": {"Observatory UTC time at guider function start"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "GSC_VER"): {
        "path": {
            "kwd": {"meta.basic.guide_star_catalog_version"},
            "dmd": {"meta.guide_star_catalog_version"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "GSIDL_X"): {
        "title": {
            "kwd": {"guide star X pos in FGS ideal coordinate frame"},
            "dmd": {"Guide star ideal y coordinate"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "GSIDL_Y"): {
        "title": {
            "kwd": {"guide star Y pos in FGS ideal coordinate frame"},
            "dmd": {"Guide star ideal y coordinate"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "GS_MAG"): {
        "title": {
            "kwd": {"guide star magnitude"},
            "dmd": {"guide star magnitude in FGS detector"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "GS_ORDER"): {
        "title": {
            "kwd": {"guide star index w/in selected guide star list"},
            "dmd": {"index of guide star within list of selected guide stars"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "HGA_MOVE"): {
        "path": {
            "kwd": {"meta.basic.hga_move"},
            "dmd": {"meta.hga_move"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "HGA_STOP"): {
        "path": {
            "kwd": {"meta.basic.hga_stop_time"},
            "dmd": {"meta.hga_stop_time"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "HGA_STRT"): {
        "path": {
            "kwd": {"meta.basic.hga_start_time"},
            "dmd": {"meta.hga_start_time"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "INSMODE"): {
        "path": {
            "kwd": {"meta.ami.insmode"},
            "dmd": {"meta.oifits.instrument_mode"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "IS_IMPRT"): {
        "path": {
            "kwd": {"meta.instrument.imprint"},
            "dmd": {"meta.exposure.imprint"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "IS_PSF"): {
        "path": {
            "kwd": {
                "meta.observation.psf_reference",
                "meta.exposure.psf_reference",
                "meta.instrument.psf_reference",
            },
            "dmd": {"meta.exposure.psf_reference"},
        },
        "title": {
            "kwd": {"exposure is PSF Reference"},
            "dmd": {"exposure is PSF reference"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "MIRNFRMS"): {
        "path": {
            "kwd": {"meta.instrument.miri_fsw_nframes"},
            "dmd": {"meta.exposure.miri_fsw_nframes"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "MIRNGRPS"): {
        "path": {
            "kwd": {"meta.instrument.miri_fsw_ngroups"},
            "dmd": {"meta.exposure.miri_fsw_ngroups"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "MSTR_RD1"): {
        "title": {
            "kwd": {"# substripe rows read starting at SUBSTRT1"},
            "dmd": {"Num. substripe rows read starting at SUBSTRT1"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "MSTR_RD2"): {
        "title": {
            "kwd": {"# rows read in subsequent substripes"},
            "dmd": {"Num. rows read in subsequent substripes"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "MSTR_SK1"): {
        "title": {
            "kwd": {"# rows to skip after reading MSTR_RD1 rows"},
            "dmd": {"Num. rows to skip after reading MSTR_RD1 rows"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "MSTR_SK2"): {
        "title": {
            "kwd": {"# rows to skip between subsequent substripes"},
            "dmd": {"Num. rows to skip between subsequent substripes"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "NRS_NORM"): {
        "path": {
            "kwd": {"meta.instrument.nrs_normal"},
            "dmd": {"meta.exposure.nrs_normal"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "NRS_REF"): {
        "path": {
            "kwd": {"meta.instrument.nrs_reference"},
            "dmd": {"meta.exposure.nrs_reference"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "NWFSEST"): {
        "path": {
            "kwd": {"meta.basic.nwfsest"},
            "dmd": {"meta.nwfsest"},
        },
        "title": {
            "kwd": {"[d] next WFS exposure start time in MJD"},
            "dmd": {"[d] Next WFS exposure start time in MJD"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "OBJECT"): {
        "path": {
            "kwd": {"meta.ami.object"},
            "dmd": {"meta.oifits.derived.object"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "OBSERVER"): {
        "path": {
            "kwd": {"meta.ami.observer"},
            "dmd": {"meta.oifits.derived.observer"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "ORIGIN"): {
        "path": {
            "kwd": {"meta.basic.origin"},
            "dmd": {"meta.origin"},
        },
        "title": {
            "kwd": {"institution responsible for creating FITS file"},
            "dmd": {"Organization responsible for creating file"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "OSF_FILE"): {
        "title": {
            "kwd": {"Observatory Status File name"},
            "dmd": {"Observatory Status File name covering this exposure"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "OSS_VER"): {
        "path": {
            "kwd": {"meta.basic.oss_software_version"},
            "dmd": {"meta.oss_software_version"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "PATTNPTS"): {
        "title": {
            "kwd": {"Number of point in CYCLING pattern"},
            "dmd": {"Number of points in CYCLING pattern"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "PATTSTRT"): {
        "path": {
            "kwd": {"meta.dither.starting_point", "meta.dither.pattern_start"},
            "dmd": {"meta.dither.pattern_start"},
        },
        "title": {
            "kwd": {"Starting point in dither pattern", "Starting point in cycling pattern"},
            "dmd": {"Starting point in pattern"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "PILIN"): {
        "title": {
            "kwd": {"Pupil imaging lens in the optical path: T/F"},
            "dmd": {"Pupil imaging lens in the optical path?"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "PRD_VER"): {
        "path": {
            "kwd": {"meta.basic.prd_software_version"},
            "dmd": {"meta.prd_software_version"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "PRIDTPTS"): {
        "path": {
            "kwd": {"meta.dither.primary_points", "meta.dither.nod_points"},
            "dmd": {"meta.dither.primary_points"},
        },
        "title": {
            "kwd": {
                "Number of points in primary dither pattern",
                "Number of points in nod pattern",
            },
            "dmd": {"Number of points in primary dither pattern"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "PWFSEET"): {
        "path": {
            "kwd": {"meta.basic.pwfseet"},
            "dmd": {"meta.pwfseet"},
        },
        "title": {
            "kwd": {"[d] previous WFS exposure end time in MJD"},
            "dmd": {"[d] Previous WFS exposure end time in MJD"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "R_BKG"): {
        "title": {
            "kwd": {"BKG reference file name"},
            "dmd": {"Background reference file name"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "R_FRIFRQ"): {
        "title": {
            "kwd": {"MRS Fringe Frequency reference file name"},
            "dmd": {"Fringe Frequency reference file name"},
        },
        "notes": """Minor title difference. No fix needed since fringe only applies to MIRI.""",
    },
    ("PRIMARY", "R_NRM"): {
        "title": {
            "kwd": {"NRM reference file name"},
            "dmd": {"Non-Redundant mask reference file name"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "R_RESOL"): {
        "title": {
            "kwd": {"MRS Resolution reference file name"},
            "dmd": {"MRS resolution reference file name"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "R_SIRSKL"): {
        "title": {
            "kwd": {"SIRS refpix reference file name"},
            "dmd": {"NIR Simple Improved Reference Subtraction"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "R_WAVCOR"): {
        "title": {
            "kwd": {"Zero-point wavelength correction ref file name"},
            "dmd": {"Zero point wavelength correction reference file name"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "SCATFILE"): {
        "path": {
            "kwd": {"meta.resample.source_catalog"},
            "dmd": {"meta.source_catalog"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "SDP_VER"): {
        "path": {
            "kwd": {"meta.basic.data_processing_software_version"},
            "dmd": {"meta.data_processing_software_version"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "SEGMFILE"): {
        "path": {
            "kwd": {"meta.resample.segmentation_map"},
            "dmd": {"meta.segmentation_map"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "SELFREF"): {
        "path": {
            "kwd": {
                "meta.exposure.self_reference_survey",
                "meta.instrument.self_reference_survey",
                "meta.observation.self_reference_survey",
            },
            "dmd": {"meta.exposure.self_reference_survey"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "SPCOFFST"): {
        "title": {
            "kwd": {"Spectral offset from pattern start (arcsec)"},
            "dmd": {"[arcsec] Spectral offset from pattern start"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "SPTOFFST"): {
        "title": {
            "kwd": {"Spatial offset from pattern start (arcsec)"},
            "dmd": {"[arcsec] Spatial offset from pattern start"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "SSTR_NST"): {
        "title": {
            "kwd": {"# superstripe positions in super-integration"},
            "dmd": {"Num. superstripe positions in super-integration"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "S_BARSHA"): {
        "title": {
            "kwd": {"NIRSpec bar shadow correction"},
            "dmd": {"Bar shadow correction"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "S_BPXSLF"): {
        "title": {
            "kwd": {"Bad Pixel Self Calibration"},
            "dmd": {"Bad Pixel Self-Calibration"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "S_GRPSCL"): {
        "title": {
            "kwd": {"Group scale Correction"},
            "dmd": {"Group Scale Correction"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "S_GUICDS"): {
        "title": {
            "kwd": {"Guide Mode CDS computation"},
            "dmd": {"Guide Mode CDS Computation"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "S_RSCD"): {
        "title": {
            "kwd": {"RSCD correction"},
            "dmd": {"RSCD Correction"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "S_SPLEAK"): {
        "title": {
            "kwd": {"MIRI MRS spectral_leak"},
            "dmd": {"MRS spectral leak"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "TCATFILE"): {
        "path": {
            "kwd": {"meta.resample.tweakreg_catalog"},
            "dmd": {"meta.tweakreg_catalog"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "TELESCOP"): {
        "path": {
            "kwd": {"meta.basic.telescope"},
            "dmd": {"meta.telescope"},
        },
        "title": {
            "kwd": {"telescope used to acquire the data"},
            "dmd": {"Telescope used to acquire the data"},
        },
        "notes": """Minor path and title differences. No fix needed.""",
    },
    ("PRIMARY", "TIME-OBS"): {
        "title": {
            "kwd": {"UTC time at start of exposure", "UTC time at start of guiding data"},
            "dmd": {"[hh:mm:ss.sss] UTC time at start of exposure"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "TIMESYS"): {
        "path": {
            "kwd": {"meta.basic.time_sys"},
            "dmd": {"meta.time_sys"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "TMEASURE"): {
        "title": {
            "kwd": {"[s] Measurement Time"},
            "dmd": {"[s] Measurement time"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "TSOVISIT"): {
        "title": {
            "kwd": {"Timer Series Observation visit indicator"},
            "dmd": {"Time Series Observation visit indicator"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "V2_REF"): {
        "path": {
            "kwd": {"meta.guidestar.v2_ref"},
            "dmd": {"meta.guidestar.fgs_v2_ref"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("SCI", "V3I_YANG"): {
        "title": {
            "kwd": {"[deg] Direction angle in V3 (Y)"},
            "dmd": {"[deg] Angle from V3 axis to Ideal y axis"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("PRIMARY", "V3_REF"): {
        "path": {
            "kwd": {"meta.guidestar.v3_ref"},
            "dmd": {"meta.guidestar.fgs_v3_ref"},
        },
        "notes": """Minor path difference. No fix needed.""",
    },
    ("PRIMARY", "VISITEND"): {
        "title": {
            "kwd": {"UTC time when the visit ended"},
            "dmd": {"Observatory UTC time when the visit ended"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "VPARITY"): {
        "title": {
            "kwd": {"Parity (sense) of aperture settings (1, -1)"},
            "dmd": {"Relative sense of rotation between Ideal xy and V2V3"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PA_APER"): {
        "title": {
            "kwd": {"Position angle of aperture used (deg)"},
            "dmd": {"[deg] Position angle of aperture used"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PA_V3"): {
        "title": {
            "kwd": {"[deg] position angle of V3-axis of JWST"},
            "dmd": {"[deg] Position angle of telescope V3 axis"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC1_1"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC1_2"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC1_3"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC2_1"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC2_2"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC2_3"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC3_1"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC3_2"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "PC3_3"): {
        "title": {
            "kwd": {"Linear transformation matrix"},
            "dmd": {"Linear transformation matrix element"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "ROLL_REF"): {
        "title": {
            "kwd": {"[deg] V3 roll angle at ref point, N over E"},
            "dmd": {"[deg] V3 roll angle at the ref point (N over E)"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "SRCNAME"): {
        "title": {
            "kwd": {"Source Name"},
            "dmd": {"Source name"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("SCI", "STLARITY"): {
        "title": {
            "kwd": {"Advised type of calibration processing for source"},
            "dmd": {"Source stellarity"},
        },
        "notes": """Minor title difference. No fix needed.""",
    },
    ("TARG_ACQ", "V2_REF"): {
        "kwd": {"TARG_ACQ"},
        "dmd": {"PRIMARY"},
        "notes": """This keyword appears in multiple hdus (TARG_ACQ, PRIMARY, SCI).
                No fix needed.""",
    },
    ("TARG_ACQ", "V3_REF"): {
        "kwd": {"TARG_ACQ"},
        "dmd": {"SCI"},
        "notes": """This keyword appears in multiple hdus (TARG_ACQ, PRIMARY, SCI).
                No fix needed.""",
    },
}
