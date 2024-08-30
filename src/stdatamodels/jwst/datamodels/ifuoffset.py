import traceback
import warnings

#from asdf.tags.core import NDArrayType
import numpy as np
from astropy import units as u
from stdatamodels.validate import ValidationWarning

from .reference import ReferenceFileModel

__all__ = ['IFUOffsetModel']

class IFUOffsetModel(ReferenceFileModel):
    """
    A model a list of offsets of type "ifuoffset" for the the IFU detectors.

    Parameters
    ----------

    offsets : dictionary
        Dictionary holding offset infomration

    offsets['Filename'] : list
        List of filenames

    offsets['raoffset'] : list
        List of ra offsets

    offsets['decoffset'] : list
        List of dec offsets
    """

    
    def __init__(self, init=None, model=None, input_units=None, **kwargs):


        super().__init__(init=init, **kwargs)
        if model is not None:
            self.model = model
        if input_units is not None:
            self.meta.input_units = input_units
        self.meta.reftype = None
        self.meta.pedigree = 'Flight'
        self.meta.author = 'NA'
        self.meta.useafter = '2022-04-01T00.00.00'
        self.meta.instrument.name = None
        self.meta.description = 'A list of ra and dec offsets'

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/ifuoffset.schema"


