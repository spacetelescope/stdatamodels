from asdf.extension import ManifestExtension
from .stnode import (
	WfiImageConverter,
	ExposureConverter, 
	WfiConverter, 
	NircamImageConverter,
	ApertureConverter,
	AssociationConverter, 
	EphemerisConverter,
	FitsWcsInfoConverter,
	GuidestarConverter,
	NircamConverter,
	NircamCalibrationStepsConverter,
	NircamDitherConverter,
	NircamExposureConverter, 
	NircamFocusConverter,
	NircamReferenceFilesConverter,
	NircamSubarrayConverter,
	ObservationConverter, 
	PhotometryConverter,
	ProgramConverter,
	TargetConverter,
	TimeConverter,
	VelocityAberrationConverter, 
	VisitConverter,)


DATAMODEL_CONVERTERS = [
    WfiImageConverter(),
    ExposureConverter(),
    WfiConverter(),

    NircamImageConverter(),
    ApertureConverter(),
    AssociationConverter(),
    EphemerisConverter(),
    FitsWcsInfoConverter(),
    GuidestarConverter(),
    NircamConverter(),
    NircamCalibrationStepsConverter(),
    NircamDitherConverter(),
    NircamExposureConverter(),
    NircamFocusConverter(),
    NircamReferenceFilesConverter(),
    NircamSubarrayConverter(),
    ObservationConverter(),
    PhotometryConverter(),
    ProgramConverter(),
    TargetConverter(),
    TimeConverter(),
    VelocityAberrationConverter(),
    VisitConverter(),
]

DATAMODEL_EXTENSIONS = [
    ManifestExtension.from_uri("http://stsci.edu/asdf/datamodels/manifests/datamodels-1.0", 
    	converters=DATAMODEL_CONVERTERS)
]