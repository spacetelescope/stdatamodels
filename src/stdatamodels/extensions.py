from asdf.extension import ManifestExtension
from .stnode import WfiImageConverter, ExposureConverter, WfiConverter


DATAMODEL_CONVERTERS = [
    WfiImageConverter(),
    ExposureConverter(),
    WfiConverter(),
]

DATAMODEL_EXTENSIONS = [
    ManifestExtension.from_uri("http://stsci.edu/asdf/datamodels/manifests/datamodels-1.0", 
    	converters=DATAMODEL_CONVERTERS)
]