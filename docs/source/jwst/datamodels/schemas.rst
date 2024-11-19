JWST schemas
============

This package contains schemas of the following types:

- Data model schemas
- Reference file schemas
- Transform schemas (not covered here)


Data model schemas
------------------

JWST datamodels are in part defined by an ASDF schema.
For example ``RampModel`` uses the schema found in ``ramp.schema.yaml``.
These data model schemas typically contain many references
to other schemas to allow common structures to be shared across
data models. Here is a (partial) example:

.. code-block:: yaml

  %YAML 1.1
  ---
  $schema: "http://stsci.edu/schemas/fits-schema/fits-schema"
  id: "http://stsci.edu/schemas/jwst_datamodel/ramp.schema"
  allOf:
  - $ref: core.schema
  - $ref: bunit.schema
  - $ref: photometry.schema
  - $ref: wcsinfo.schema
  - type: object

Each ``$ref`` above will pull in the common structure defined
in the referenced schema. All data model schemas reference
``core.schema``.


Reference file schemas
----------------------

JWST reference file schemas are similar to the data model schemas
but use a different set of shared schemas.

.. code-block:: yaml

  %YAML 1.1
  ---
  $schema: "http://stsci.edu/schemas/fits-schema/fits-schema"
  id: "http://stsci.edu/schemas/jwst_datamodel/dark.schema"
  title: Dark current data model
  allOf:
  - $ref: referencefile.schema
  - $ref: keyword_exptype.schema
  - $ref: keyword_readpatt.schema

Note that reference file schemas ``$ref`` ``referencefile.schema``.
