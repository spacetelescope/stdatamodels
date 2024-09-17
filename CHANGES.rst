2.1.0 (2024-09-17)
==================

Bug Fixes
---------

- Fix invalid ``abvegaoffset`` and ``coords`` schemas. (`#327
  <https://github.com/spacetelescope/stdatamodels/issues/327>`_)


Documentation
-------------

- use ``towncrier`` to handle change log entries (`#326
  <https://github.com/spacetelescope/stdatamodels/issues/326>`_)


New Features
------------

- Add ``mt_v2`` and ``mt_v3`` keywords to ``moving_target`` schema (`#263
  <https://github.com/spacetelescope/stdatamodels/issues/263>`_)
- Added ``MEDIUMDEEP2`` and ``MEDIUMDEEP8`` to allowed readout patterns in JWST
  core schema, ``READPATT``, and ``PREADPATT``. (`#315
  <https://github.com/spacetelescope/stdatamodels/issues/315>`_)
- add grating keyword to dark and superbias schemas (`#317
  <https://github.com/spacetelescope/stdatamodels/issues/317>`_)
- Update JWST datamodel ``irs2`` datatype to provide ``numpy>=2.0``
  compatibility. (`#319
  <https://github.com/spacetelescope/stdatamodels/issues/319>`_)
- Add datamodel and schema for ``PastasossModel``, a new reference file type
  for JWST NIRISS SOSS exposures. (`#320
  <https://github.com/spacetelescope/stdatamodels/issues/320>`_)
- Add keyword to JWST core schema to track status of new step
  ``clean_flicker_noise``. (`#328
  <https://github.com/spacetelescope/stdatamodels/issues/328>`_)


Deprecations and Removals
-------------------------

- replace usages of ``copy_arrays`` with ``memmap`` (`#306
  <https://github.com/spacetelescope/stdatamodels/issues/306>`_)
- remove uses of now unused ``ignore_version_mismatch`` (`#313
  <https://github.com/spacetelescope/stdatamodels/issues/313>`_)
- Remove deprecated ``R_DRIZPAR`` keyword from core schema as well as
  ``jwst.datamodels.DrizParsModel``. (`#316
  <https://github.com/spacetelescope/stdatamodels/issues/316>`_)


2.0.0 (2024-06-24)
===================

- Remove deprecated jwst.datamodels models: DataModel, DrizProductModel,
  MIRIRampModel, MultiProductModel [#171]

- Increase CRDS minimum version to 11.17.1 [#171]

- Removed deprecated ``deprecate_class``, ``cast_arrays`` and
  ``jwst.datamodels.util`` [#298]

- Remove ``stdatamodels.jwst.datamodels.schema`` which is an out-of-date
  duplicate of ``stdatamodels.schema`` [#175]

- Remove unnecessary references to overwritten datamodel
  attributes to free up memory [#301]

- Remove unused ``deprecated_properties`` [#303]


1.10.1 (2024-03-25)
===================

- Added ALL_MRS to allowed values for keyword MRSPRCHN in core
  schema. [#285]

- Provide existing ``AsdfFile`` instance to ``validate`` to
  speed up assignment validation ``check_value``. [#276]

- Deprecate ``deprecate_class`` unused by downstream. [#274] 

- Add cache to hdu accesses during ``_load_from_schema``
  to speed up file opening. [#278]

- Remove ``TEXPTIME`` keyword from the JWST core datamodel schema
  because it duplicates the information of ``XPOSURE``. [#277]

- Deprecate ``check_memory_allocation``. This function did not
  work as intended. [#273]

- Decrease size of ``SPECTYP`` and ``TARGET`` columns in
  ``OI_TARGET`` table of oifits schema to 16 characters. [#281]

- Change ``integration_number`` from int16 to int32 in ``group``
  schema. [#283]

- Fix datamodel schema ids for abvegaoffset, keyword_lampmode, nrsfs_apcorr [#258]

- Drop support for python 3.9 [#287]

- Convert ``FITS_rec`` instances read from old files where a
  hdu was linked in the old schema (but is no longer linked)
  when rewriting files. [#268]

- Deprecate ``skip_fits_update`` and environment variable
  ``SKIP_FITS_UPDATE``. Future behavior will be as if
  ``skip_fits_update`` was ``False`` and the FITS headers
  will always be read [#270]

- Increase minimum required asdf version [#288]

- Add ``S_BPXSLF`` keyword to the JWST core schema to reflect the addition
  of the ``badpix_selfcal`` step. [#305]


1.10.0 (2024-02-29)
===================

Bug Fixes
---------

- Adding "IMAGER" as another allowed value for the "MRSPRCHN"
  keyword, in order to support proper handling of MIRI MRS
  and Imager exposures done in parallel. [#259]

- Fix mask schema to allow for non-integer ngroups selectors [#256]

Changes to API
--------------

- Add ``NRMModel`` for new NIRISS NRM reference file [#253]

Other
-----

- Add ``grating`` keyword to JWST ``barshadow`` ref file schema to match
  parkeys on crds [#260]

- Add ``average_dark_current`` in both scalar keyword and array extension
  options to ``DarkModel`` and ``MIRIDarkModel``. Add the array extension
  to the ``RampModel``, for tracking the average dark current. [#265]

- Add ``EXTRXSTR``, ``EXTRXSTP``, ``EXTRYSTR``, and ``EXTRYSTP`` keywords
  to the jwst ``MultiSpec`` schema. [#264]


1.9.1 (2024-01-25)
==================

Bug Fixes
---------

-

Changes to API
--------------

- Remove ``json_id`` argument use for callbacks passed
  to ``asdf.treeutil.walk_and_modify`` [#244]

Other
-----

- Add ``ngroups`` keyword to JWST ``mask`` ref file schema to match
  parkeys on crds [#249]

- Added keywords ``noutputs`` and ``bunit`` to the JWST
  readnoise and superbias datamodel schemas. [#250]

- Updated JWST core datamodel schema to include the new
  ``TMEASURE`` keyword for measurement time. [#248]


1.9.0 (2023-12-11)
==================

Bug Fixes
---------

- Fix search in documentation [#241] 

Changes to API
--------------

- Deprecate ``cast_arrays`` argument to ``from_fits_hdu`` and
  ``cast_fits_arrays`` argument to ``Datamodel.__init__`` [#214]

- Use ``DataModel.__init__`` ``memmap`` argument when opening ASDF
  files [#232]

Other
-----

- Updated JWST core datamodel schema to include the new step status keyword
  "S_NSCLEN" for the new "nsclean" calibration step. [#237]

- Adding emicorr datamodel and schema, as well as
  corresponding completion and reference file keywords [#200]

1.8.4 (2023-12-04)
==================

Bug Fixes
---------

- Fixed ``ValidationError`` during ``AmiOIModel.update`` [#234]

- Fix ``rebuild_fits_rec_dtype`` handling of unsigned integer columns
  with shapes [#213]

- Fix unit roundtripping when writing to a datamodel with a table
  to a FITS file [#242]

Changes to API
--------------

- Sort keyword files used for schema_editor to make output non-arbitrary
  copy schema before merging to avoid schema modification [#227]

Other
-----

- Add mrsptcorr ref_file to core.schema [#228]

- Avoid unnecessary validation during ``DataModel.clone`` [#230] 

- Replace uses of ``utcnow`` (deprecated in python 3.12) [#231] 

- Updated JWST MIRI imager photom model to include time-dependent correction
  coeffs. [#235]

  
1.8.3 (2023-10-02)
==================

Other
-----

- Add ``channel`` keyword to MIRI MRS Apcorr schema [#224]

1.8.2 (2023-09-26)
==================

Other
-----

- Update ``RefractionIndexFromPrism`` converting single element ndarrays
  to scalar values before use to avoid ``DeprecationWarning``s introduced
  in numpy 1.25 [#210]

- Add band to ``GainModel`` schema to account for miri crds file updates
  [#219]


1.8.1 (2023-09-13)
==================

Bug Fixes
---------

-

Changes to API
--------------

-

Other
-----

- Add ``AmiLgFitModel`` class and schema [#199]

- Switch schema refs from tags to equivalent uris [#201]

- Add ``DITH_RA`` and ``DITH_DEC`` to JWST core schema metadata,
  to be used in spectral extraction window centering. [#203]

- Change format of the MirMrsPtCorrModel to use a 1d reference table
  instead of 2d FITS image extensions [#196]

- Convert ``FITS_rec`` instances to arrays before serializing or
  validating with asdf [#205]


1.8.0 (2023-08-24)
==================

Other
-----

- Remove ignored V23ToSkyConverter from jwst.transforms version 1.0.0
  asdf extension [#184]

- Use ValidationError and type validator from asdf instead of from jsonschema
  directly, remove jsonschema as a direct dependency, increase asdf minimum
  version to 2.15.0.  [#177]

- Use binary masks for DQ calculations in dynamicdq [#185]

- Add keyword_filter.schema reference to gain schema to accomodate
  addition of FILTER as a CRDS selector for GAIN ref files. [#197]

- Add charge_migration (new name for undersampling_correction) with keyword
  S_CHGMIG to cal_step section of core schema.  Change UNDERSAMP DQ flag to
  CHARGELOSS. [#194]

- Add option to ``allow_extra_columns`` in datamodel schema that defines
  structured arrays (tables) and allow extra columns in tables [#189]

- Fix typo in ``outlierifuoutput`` schema for ``kernel_ysize`` [#191]


1.7.2 (2023-08-14)
==================

- Added the new keyword "GSC_VER" to the JWST core datamodels schema. [#190]


1.7.1 (2023-07-11)
==================

Other
-----

- Added two new header keywords to the JWST core schema target section:
  TARGCAT and TARGDESC, which record the target category and description
  as given by the user in the APT. [#179]

- Enable searching docs directory for doctests and fix failing doctest. [#182]

- Add error column to NIRSpec flat schema's ``flat_table`` definition,
  and remove fixed shape definition for other table columns. [#183]

Bug Fixes
---------

- Link FITS_rec instances to created HDU on save to avoid data duplication. [#178]


1.7.0 (2023-06-29)
==================

Other
-----

- Update the allocation of the ZEROFRAME array for the RampModel. [#176]

- Added two new header keywords to the JWST core schema exposure section: PRIMECRS and
  EXTNCRS, which are used to record the rate of primary cosmic rays and extended cosmic
  rays (Snowballs and Showers). [#173]

- Add OIFITS compatible schema and ``AmiOIModel`` [#174] 


1.6.0 (2023-06-15)
==================

Other
-----

- Update jwst outlierpars schema to support new IFU outlier detection algorithm
  and add new ``OutlierIFUOutputModel`` data model. [#164]

- Reduce interpolation vector length in NIRCam backwards transform
  to improve computation times [#165]

- Update of JWST/MIRI MRS photom datamodel to include the time dependent correction. [#166]

- Add a parameter to jwst outlierpars schema to support a second level of
  flagging outliers for JWST MIRI/MRS and NIRSpec IFU data. [#167]

- Close for opened files [#169]

1.5.0 (2023-05-16)
==================

Other
-----

- Provide second-order polynomial transforms for NIRCam WFSS grisms. [#124]

- Deprecate ``stdatamodels.jwst.datamodels.DataModel`` in favor of
  ``stdatamodels.jwst.datamodels.JwstDataModel``. [#160]

- Provide backwards compatibility for grism transform schemas; remove inverse
  models from required properties of transform schemas. [#161]

- Add wavelength tables for NIRSpec Drizzle cubepars reference file model. [#162]

1.4.0 (2023-04-19)
==================

Other
-----

- Add pixel replacement step keyword to jwst.datamodels core schema, and change
  DQ bit 28 from ``UNRELIABLE_RESET`` to ``FLUX_ESTIMATED``. [#149]

- drop support for Python 3.8 [#143]

- use Mamba to build docs [#155]

- Remove the defunct ``s3_utils`` module, so that ``stpipe`` no longer needs to depend
  on this package. This also removes the ``aws`` install option as this is no longer need. [#154]

- Remove use of deprecated ``pytest-openfiles`` ``pytest`` plugin. This has been replaced by
  catching ``ResourceWarning``s. [#152]

- Fix open file handles, which were previously ignored by ``pytest-openfiles``, but which raise
  blocked ``ResourceWarning`` errors. [#153]

1.3.1 (2023-03-31)
==================

Other
-----

- Add units to BARTDELT and HELIDELT jwst keywords in datamodels schema. [#147]

1.3.0 (2023-03-13)
==================

Other
-----

- Added inverse functionality to ``dynamic_mask``, which allows for
  properly saving of datamodels with ``dq_def`` defined. [#132]

- Move the ``dqflags`` and related code from ``stcal`` to this package
  so that the ``stcal`` dependency can be dropped. [#134]

- increase ``requires-python`` to ``3.8`` [#144]

- Add R_MRSXAR as the keyword for the jwst straylight mrsxartcorr reference filename in core schema in stdatamodels.jwst.datamodels [#145]

Bug Fixes
---------

- Add support for reading from already open HDUList to asdf_in_fits.open [#136]

1.2.0 (2023-03-02)
==================

Other
-----
- Add UNDERSAMP flag to dqflags and undersample correction metadata to core schema
  in stdatamodels.jwst.datamodels [#127]

1.1.0 (2023-02-16)
==================

Other
-----

- Add helper functions to aid in migration of ASDF-in-FITS
  uses from asdf to this package [#114]

1.0.0 (2023-02-14)
==================

Bug Fixes
---------

Other
-----

- Reimplement support for ASDF-in-FITS in this package. [#110]
- Move ``jwst.datamodels`` from the ``jwst`` package into this package. [#112]
- Move ``jwst.transforms`` from the ``jwst`` package into this package. [#113]

0.4.5 (2023-01-12)
==================

Bug Fixes
---------

- improve datamodels memory usage [#109]

Other
-----

- added environments in ``tox.ini`` to support Tox 4 [#108]

0.4.4 (2022-12-27)
==================

Bug Fixes
---------

- Increase asdf version to >=2.14.1 to fix hdu data duplication [#105]
- Remove use of deprecated ``override__dir__`` [#103]
- Add requirement of asdf-astropy >= 0.3.0 to prevent future issues with using deprecated
  astropy serialization methods [#104]

0.4.3 (2022-06-03)
==================

- Pin astropy min version to 5.0.4. [#94]

0.4.2 (2022-03-15)
==================

- Fix FITS writing validators with jsonschema 4.x. [#92]

0.4.1 (2022-03-07)
==================

- Changed the way NDArrayType wrappers are handled on write. [#89]
- Bugfix for JWST failing with latest asdf-transform-schemas. [#90]

0.4.0 (2021-11-18)
==================

- Add schema feature to forward deprecated model attributes to
  a new location. [#86]

- Support casting of FITS_rec tables with unsigned integer columns. [#87]

0.3.0 (2021-09-03)
==================

- Remove NDData interface from DataModel. [#77]

- Add cast_fits_arrays and validate_arrays options for controlling
  array validation behavior. [#79]

- Prevent data corruption by raising an error when asked to cast a
  table with a pseudo-unsigned integer column. [#82]

- Remove DataModel.my_attribute function. [#72]

0.2.4 (2021-08-26)
==================

- Workaround for setuptools_scm issues with recent versions of pip. [#83]

0.2.3 (2021-06-15)
==================

- Don't allow ASDF hdus to get passed through ``extra_fits``, and don't
  write out any ASDF extension if ``self._no_asdf_extension=True`` [#71]

0.2.2 (2021-06-09)
==================

- Make arrays contiguous on save to prevent issue with duplicate
  array data between ASDF and FITS. [#70]

0.2.1 (2021-03-08)
==================

- Stop setting level of package loggers. [#64]

0.2.0 (2021-02-15)
==================

- Remove automatic management of meta.date attribute and create
  on_init hook. [#44]

- Fix bug where asdf.tags.core.NDArrayType instances remain
  in flat dict when include_arrays=False. [#58]

- Improve handling of open files among shallow copies
  of a DataModel. [#59, #60]

0.1.0 (2020-12-04)
==================

- Create package and import code from jwst.datamodels. [#1, #27]

- Remove stdatamodels.open. [#2]

- Fix validation behavior when an object with nested None values is
  assigned to a DataModel attribute. [#45]

- Rename is_builtin_fits_keyword to make clear that it is
  used outside of this package. [#47]

- Add flag to disable validation on DataModel attribute
  assignment. [#36]
