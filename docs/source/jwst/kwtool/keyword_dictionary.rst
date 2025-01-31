.. _keyword_dictionary:

Keyword Dictionary
==================

The "keyword dictionary" is a collection
of json files that describe FITS keywords used in JWST files.
Although the format is similar to jsonschema it is not compatible
with jsonschema parsers and cannot be treated as any draft of jsonschema.
A brief ADASS proceedings paper is the only public documentation of
the format:

https://www.aspbooks.org/publications/522/165.pdf

and appears to be out of date with private documentation
(available to STScI staff) at:

https://innerspace.stsci.edu/pages/viewpage.action?spaceKey=jwstdms&title=JWST+Keyword+Dictionary

This document will attempt to describe the format from the
perspective of comparing the keyword dictionary and data model
schemas. This documentation is incomplete and based largely
on the usage of the keyword dictionary files by current code.


Availability
------------

The keyword dictionary JSON files are available for download
by using the "Download Keyword Schemas" button at:

https://mast.stsci.edu/portal/Mashup/Clients/jwkeywords/index.html

For STScI users the development JSON files for the keyword dictionary
are available on the private git server.


Top Files
---------

As described in the reference the dictionary has a "top" file
for each instrument and mode. For example "top.miri.coron.schema.json":


.. literalinclude :: top.miri.coron.schema.json
   :language: json


Each top file contains several nested objects but does not contain
FITS keyword definitions directly. Instead, each top file contains
"references" to other JSON files that define the FITS keywords.


References
----------

These "references" are structured as objects with a single key "$ref":


.. code-block:: json

    {"$ref" : "standard.schema.json"}

These function similar to JSON pointers but for this limited use
they always refer to full files located in the same directory.


Combiners
---------

References are sometimes nested under an "allOf" key
in a list of references. Although this shares a name with a
schema combiner used for jsonschema this "allOf" does not
function the same way. For example, items in the "allOf" can
have overlapping keys but items from all keys are included in
the final parsed FITS keywords. For example if an "allOf" contains
2 references with keys "a", "b" and "b", "c" the final set
of FITS keywords will contain "a", "b", "b", "c". The documentation
does not describe how conflicts should be handled. In practice
it appears that conflicts are primarily (if not exclusively)
for keys sharing the "extension_type" key. This key appears
to be special, always referring to the "XTENSION" FITS keyword,
and is not relevant to the keyword tool.

No other jsonschema combiners ("oneOf", "anyOf", etc) are used
and based on the existing parsing code it does not appear that
they would be supported.


Keyword definitions
-------------------

Rather than attempt to describe all entries in the keyword definitions
this section will only describe the key/value pairs used
by the comparison tool. For a more complete description see
the private documentation linked above.

The comparison tool will use the following keys from the
keyword definitions in the keyword dictionary:

- fits_keyword: the FITS keyword name
- fits_hdu: the FITS hdu name
- title: the title of the keyword definition
- type: one of "float", "integer", "string", "boolean"
- enum (optional): list of valid values


Data model paths
----------------

The hierarchical structure in which the keyword dictionary definitions
are nested has in practice been considered the "data model path" (or sometimes
referred to as the "data model name'). Practically this is used for:

- constructing filenames for the keyword dictionary GUI
- entry into the archive database to allow triggering reprocessing based
  on reference file updates

This is easiest to explain with an example. For "top.miri.coron.schema.json" a
reference exists at the "path"
`properties.meta.properties.coordinates.properties`
(constructed by '.' combining the keys needed to get to the reference starting
at the root object). This reference points to the "core.coordinates.schema.json"
file:

.. literalinclude :: core.coordinates.schema.json
   :language: json

Which contains a keyword definition "reference_frame" for FITS keyword
"RADESYS". The resulting "data model path" (or "data model name") for this
keyword definition includes the final key and is then stripped of all
"properties" (and "allOf") keys resulting in `meta.coordinates.reference_frame`
for the final "data model path".

It is also possible for referenced files to contain additional
hierarchical structure (objects with "properties", "allOf", etc).


Parsing
-------

There is no specification for how these files should be parsed. This
section will attempt to describe the parsing performed by the general
code used for SDP, constructing the keyword dictionary GUI and for
checking the keyword dictionary for archive database maintenance. For
each of these uses a version of a "keyword_dict.py" file is used.
Unfortunately there are 4 slightly different versions of the same file
and all are private.

Generally the code appears to:

- "walk" the schema (more on this below)
- ignore all nodes that aren't a dict and don't contain "fits_keyword"
- store the node as a keyword definition (keyed by top file name and "data model name")
- strip the "path" of all "properties" and "allOf" keys

The schema "walk" is a post-order depth-first traversal that steps
into every dict, list and tuple. Note that traversal of "allOf"
contents is not handled in any special way.
