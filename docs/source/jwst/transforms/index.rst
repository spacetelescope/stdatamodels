====================
WCS Transform Models
====================

.. toctree::
   :maxdepth: 2

The :py:mod:`stdatamodels.jwst.transforms` submodule defines
`Astropy-compatible models <https://docs.astropy.org/en/latest/modeling/index.html>`__
that encode WCS transformations specific to JWST.

Grism Transforms
----------------

In support of Wide-Field Slitless Spectroscopy (WFSS) modes, NIRISS, NIRCam, and MIRI 
each have transformations between the dispersed frame (the detector frame with the grism inserted)
and the direct-image frame (what the detector would see if the grism were not inserted)
defined as models. These become part of the WCS objects of datamodels during the ``assign_wcs``
step of the JWST pipeline, and can also be used standalone. For example, to transform from
the direct-image frame to the dispersed frame for NIRISS at a given wavelength
(the "backward" transform), one could use the following code,
assuming appropriate ``lmodels``, ``xmodels``, and ``ymodels`` have been defined::

   from stdatamodels.jwst.transforms import NIRISSBackwardGrismDispersion

   orders = [-1, 1]
   transform = NIRISSBackwardGrismDispersion(
      orders,
      lmodels=lmodels,
      xmodels=xmodels,
      ymodels=ymodels
   )
   x0, y0 = 0, 0
   wl = 2.0
   order = 1
   x, y, xi, yi, order_i = transform.evaluate(x0, y0, wl, order)

Here, ``x`` and ``y`` are the coordinates in the dispersed frame,
while ``xi`` and ``yi`` are the corresponding values in the direct-image frame,
which are equal to ``x0``, ``y0``. ``order`` is also passed through unchanged such that
``order_i`` is equal to ``order``.

The ``lmodels``, ``xmodels``, and ``ymodels`` encode the shape of the spectral trace.
The models used by the JWST pipeline are provided by the specwcs reference files
for each instrument. The expected format of these models is slightly different for
each instrument, so please refer to the documentation of specific transform models
for details.

See :py:mod:`stdatamodels.jwst.transforms` for documentation of all the available transform models,
the expected format of their ``lmodels``, ``xmodels``, and ``ymodels``, implementation details,
and their expected inputs and outputs.

ASDF Schema Definitions
-----------------------

This package defines `ASDF <http://asdf-standard.readthedocs.io>`__ schemas
that are used for validating the representation of the above-mentioned transforms in the ASDF
format. These schemas contain useful documentation about the associated types,
and can also be used by other implementations that wish to interoperate with
these transform definitions.

.. asdf-autoschemas::
   :schema_root: ../../src/stdatamodels/jwst/transforms/resources/schemas
   :standard_prefix: stsci.edu/jwst_pipeline

   grating_equation-1.0.0
   gwa_to_slit-1.0.0
   logical-1.0.0
   miri_ab2slice-1.0.0
   nircam_grism_dispersion-1.0.0
   niriss_grism_dispersion-1.0.0
   niriss_soss-1.0.0
   refraction_index_from_prism-1.0.0
   rotation_sequence-1.0.0
   slit_to_msa-1.0.0
   snell-1.0.0


Legacy Transforms
-----------------
In rare cases, transforms may be removed from this package (following a deprecation period)
when they are no longer needed by the JWST pipeline. A side-effect of this removal is that
files containing serialized versions of these transforms will no longer be readable with
the latest version of the package. This scenario will lead to an ``UnsupportedConverterError``.
If you encounter this error, here are some possible workarounds:

- If this is a file produced by the jwst pipeline, please download the latest version
  of your file from MAST.
- Downgrade to a version of stdatamodels that still contains the needed transform.
  You can check the release notes to see when transforms were removed.
- To bypass the error, the asdf config flag ``warn_on_failed_conversion`` can be set to
  ``True`` (requires asdf>=5.1.0). This will allow the file to be read,
  but the unsupported transform will be represented
  with a dictionary, and the WCS will not be callable. For example:

  .. code-block:: python

     import stdatamodels.jwst.datamodels as dm
     import asdf
     asdf.get_config().warn_on_failed_conversion = True
     model = dm.open("foo.fits")
