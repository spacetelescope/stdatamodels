.. _kwtool:

============
Keyword Tool
============

The "keyword tool" (kwtool) compares the FITS keyword
definitions in the data model schemas with the
:ref:`keyword_dictionary`.

This tool is only useful for data model schema developers
and possibly maintainers of the keyword dictionary. As
such it's not considered part of the public API for this
package and is subject to breaking changes at any point.

If a stable API is preferred please open an issue.


Usage
-----

The primary interface is via the command line interface:

.. code-block:: bash

    python -m stdatamodels.jwst._kwtool path_to_keyword_dictionary

This will generate a HTML report in the working directory
that describes the differences.


Parsing
-------

To make comparisons easier both keyword dictionary and
data model schema FITS keyword descriptions are first parsed
and converted to a common structure, a "keyword definition".


Keyword definitions
^^^^^^^^^^^^^^^^^^^

Each FITS keyword is defined by a dictionary containing
keys:

- "scope": The keyword dictionary top file or data model class name.
- "path": The "data model path"
- "keyword": The dictionary taken from either the keyword dictionary or data model schema

These definitions are collected from each source (described below)
and stored in a dictionary with:

- key: 2-length tuple of (FITS hdu, FITS keyword) (in upper case)
- value: list of definitions

Value is a list since each source will list the same (FITS hdu, FITS keyword)
multiple times (for each scope).


Keyword dictionary parsing
^^^^^^^^^^^^^^^^^^^^^^^^^^

See :ref:`keyword_dictionary` for an overview and the
code for complete details.


Data model schema parsing
^^^^^^^^^^^^^^^^^^^^^^^^^

Datamodel schemas are parsed by:

- Finding all subclasses of JwstDataModel (recursively)
- Ignore some subclasses (for example ReferenceFileModel, see code full list).
- For each subclass load the corresponding schema
- Walk each schema using ``stdatamodels.schema.walk_schema``
- Construct a "keyword definition" for each dict node with a "fits_keyword" key


Comparison
----------

After both sources are parsed the comparison code will
check if the (FITS hdu, FITS keyword) keys match for the
two sources. Keys missing from one source (but found in the other)
will be reported as a difference.


Ignored keywords
^^^^^^^^^^^^^^^^

However, some (FITS hdu, FITS keyword) keys are ignored.


Standard keywords
"""""""""""""""""

Keywords defined in the FITS standard (BITPIX, BUNIT, etc) are defined
in the keyword dictionary but do not need to be defined in the data
model schemas. These standard keywords will be removed from both sources
prior to comparison (see the code for the corresponding regex).


Pattern keywords
""""""""""""""""

Data model schemas contain "pattern" keywords. These are identified
by searching for keywords starting with ``P_``. These are not compared
as they are only needed for reference files (to aid in generating rmaps
for CRDS) and don't need to be defined in the keyword dictionary.


Matching keys
^^^^^^^^^^^^^

If a (FITS hdu, FITS keyword) key is found in both sources the contents
of the definitions will be compared. The following comparisons will
be performed.

For all comparisons except "path" if a source is missing
a required sub-definition (for example if the keyword definition
does not have a "title") then a MISSING_VALUE singleton will be
added in place. If both sources are missing an item, both will have
MISSING_VALUE and no difference will be reported.


Type
""""

Both the keyword dictionary and data model schemas allow defining a
keyword type. There are slight differences between how this is defined
in each source (the keyword dictionary uses "float" whereas the data model
schemas use "number").


Enum
""""

Comparison of "enum" definitions involves generating a set of possible
values from each source and comparing the sets (so order is not compared).
The generated sets include all found "scopes" (so the possible values
from the keyword dictionary include possible enum values taken from
all top files combined). This combination is done due to the data model
schemas using a combined enum for all instruments and modes.


Title
"""""

The tool will report differences in "title" definitions between the
two sources.


Path ("data model name")
""""""""""""""""""""""""

The paths at which each keyword definition is found is compared by
constructing a set of paths for each source then comparing these sets.
Sets are used here since each key might appear in multiple top
files in the keyword dictionary and in multiple data model schemas.

There are a few instances where "path" won't be compared. These are:

- if the keyword dictionary entry does not have an archive destination
- if the datamodel schema keyword definition is nested in an "items" array


Report format
-------------

The report has 3 sections:

- Keywords in the keyword dictionary but NOT in the datamodel schemas
- Keywords in the datamodel schemas but NOT in the keyword dictionary
- Keywords in both with definition differences

Keywords that match (and report no difference) won't be included
in the report.

In each section, click an item to see details about the difference.
A short-hand is used in the difference descriptions:

- kwd: Keyword dictionary
- dmd: Data model dictionary (derived from the data model schemas)
