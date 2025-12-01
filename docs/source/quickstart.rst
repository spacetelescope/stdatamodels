Quickstart
==========

Installation
------------

Install via pip:

.. code-block:: bash

    pip install stdatamodels

Loading and Saving Datamodels
-----------------------------

The primary entry point for loading and saving datamodels is the
``stdatamodels.jwst.datamodels`` module.  To load a datamodel from a file, use
the ``open`` function.  For example, to load a file called ``example.fits``::

    import stdatamodels.jwst.datamodels as dm

    model = dm.open("example.fits")

To save the datamodel back to a file, use the ``save`` method of the model
instance.  For example, to save the model to a file called ``output.fits``::

    model.save("output.fits")

Accessing Data and Metadata
---------------------------
Once a datamodel is loaded, the data and metadata may be accessed via
attributes of the model instance. Datamodels are structured as a nested tree,
similar to the ASDF file format. For example, to access the data array and
the ``observation.date`` metadata element::

    data = model.data
    date = model.meta.observation.date

Inspect the Datamodel
---------------------
To see basic information about the datamodel, including its type,
schema version, and available metadata elements, use the ``info`` method of
the model instance. For example::

    model.info()
    # prints information about the model

Each metadata element is mapped to a FITS keyword.  To find the metadata element
corresponding to a FITS keyword, use the ``find_fits_keyword`` method of
the model instance.  For example, to find the FITS keyword for the
``observation.date`` metadata element::

    keyword = model.find_fits_keyword("DATE-OBS")
    print(keyword)  # prints ['meta.observation.date']
