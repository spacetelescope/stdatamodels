Overview of stdatamodels
========================

``stdatamodels`` is a Python package that provides a framework for
defining, creating, loading, and manipulating data models for
astronomical data.  It is designed to work with data from the
James Webb Space Telescope (JWST).  ``stdatamodels`` is maintained
by the Space Telescope Science Institute (STScI).

The purpose of the data model is to abstract away the peculiarities of
the underlying file format.  A data model may be created from scratch in memory,
or loaded from a file in FITS or ASDF format. The datamodel provides
a consistent interface to the data and metadata, regardless of the way it
was created.

The ``jwst`` data processing pipeline makes extensive use of
``stdatamodels`` to represent the data at various stages of processing.
However, ``stdatamodels`` remains a standalone package to allow
the use of JWST data products without needing to
install the entire JWST pipeline infrastructure.

Please note that ``stdatamodels`` is not intended to be a general-purpose
FITS or ASDF file reader/writer.  The available data model schemas correspond
to specific file formats generated or expected by the JWST pipeline.