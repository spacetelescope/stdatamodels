from asdf.extension import ManifestExtension
from .bozo import BozoConverter


DATAMODEL_CONVERTERS = [
    BozoConverter()
]

DATAMODEL_EXTENSIONS = [
    ManifestExtension.from_uri("http://stsci.edu/asdf/datamodels/manifests/datamodels-1.0", 
    	converters=DATAMODEL_CONVERTERS)
]