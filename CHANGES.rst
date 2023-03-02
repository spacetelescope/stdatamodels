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
