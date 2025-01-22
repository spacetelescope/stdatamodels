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
  $schema: "http://stsci.edu/schemas/asdf/asdf-schema-1.1.0"
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
  $schema: "http://stsci.edu/schemas/asdf/asdf-schema-1.1.0"
  id: "http://stsci.edu/schemas/jwst_datamodel/dark.schema"
  title: Dark current data model
  allOf:
  - $ref: referencefile.schema
  - $ref: keyword_exptype.schema
  - $ref: keyword_readpatt.schema

Note that reference file schemas ``$ref`` ``referencefile.schema``.

Reference file keywords and use by CRDS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reference file schemas often contain references to ``keyword_*``
schemas (for example ``keyword_exptype.schema`` above). These define
standard keywords that are used for reference file selection
by CRDS. For the above example, the ``exptype`` from a science file
is matched with the CRDS ``parkey`` of the same name to determine
the appropriate reference file. When crafting (or updating) a reference file
schema it's important to make sure that the referenced keyword
schemas match those expected by CRDS.

This can involve adding "pattern" keywords (for example
``keyword_pexptype.schema``) when a reference file might be used
for several keyword values. For example, if a single reference file
matches all filters, it can reference ``keyword_pfilter.schema`` and then
CRDS can use a "pattern" to avoid hosting copies of the same file for every filter.
See the
`CRDS docs <https://hst-crds.stsci.edu/static/users_guide/reference_conventions.html#matching-keyword-patterns>`_
for more details about patterns.
