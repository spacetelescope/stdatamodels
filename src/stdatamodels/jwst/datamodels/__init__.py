"""Datamodels for JWST pipeline."""

from .abvega_offset import ABVegaOffsetModel
from .amilg import AmiLgModel
from .amilgfitmodel import AmiLgFitModel
from .amioi import AmiOIModel
from .apcorr import (
    FgsImgApcorrModel,
    MirImgApcorrModel,
    MirLrsApcorrModel,
    MirMrsApcorrModel,
    NisImgApcorrModel,
    NisWfssApcorrModel,
    NrcImgApcorrModel,
    NrcWfssApcorrModel,
    NrsFsApcorrModel,
    NrsIfuApcorrModel,
    NrsMosApcorrModel,
)
from .asn import AsnModel
from .background import SossBkgModel, WfssBkgModel
from .barshadow import BarshadowModel
from .combinedspec import CombinedSpecModel, WFSSCombinedSpecModel
from .contrast import ContrastModel
from .cube import CubeModel
from .dark import DarkMIRIModel, DarkModel, DarkNirspecModel
from .emi import EmiModel
from .extract1d_spec import Extract1dIFUModel
from .flat import FlatModel
from .fringe import FringeModel
from .fringefreq import FringeFreqModel
from .gain import GainModel
from .guider import GuiderCalModel, GuiderRawModel
from .ifucube import IFUCubeModel
from .ifucubepars import MiriIFUCubeParsModel, NirspecIFUCubeParsModel
from .ifuimage import IFUImageModel
from .image import ImageModel
from .ipc import IPCModel
from .irs2 import IRS2Model
from .lastframe import LastFrameModel
from .level1b import Level1bModel
from .linearity import LinearityModel
from .mask import MaskModel
from .model_base import JwstDataModel
from .mrsptcorr import MirMrsPtCorrModel
from .mrsxartcorr import MirMrsXArtCorrModel
from .multicombinedspec import MultiCombinedSpecModel, WFSSMultiCombinedSpecModel
from .multiexposure import MultiExposureModel
from .multislit import MultiSlitModel
from .multispec import MRSMultiSpecModel, MultiSpecModel, TSOMultiSpecModel, WFSSMultiSpecModel
from .nirspec_flat import NirspecFlatModel, NirspecQuadFlatModel
from .nrm import NRMModel
from .outlierifuoutput import OutlierIFUOutputModel
from .pastasossmodel import PastasossModel
from .pathloss import MirLrsPathlossModel, PathlossModel
from .persat import PersistenceSatModel
from .photom import (
    FgsImgPhotomModel,
    MirImgPhotomModel,
    MirLrsPhotomModel,
    MirMrsPhotomModel,
    NisImgPhotomModel,
    NisSossPhotomModel,
    NisWfssPhotomModel,
    NrcImgPhotomModel,
    NrcWfssPhotomModel,
    NrsFsPhotomModel,
    NrsMosPhotomModel,
)
from .pictureframe import PictureFrameModel
from .pixelarea import (
    NirspecIfuAreaModel,
    NirspecMosAreaModel,
    NirspecSlitAreaModel,
    PixelAreaModel,
)
from .psfmask import PsfMaskModel
from .quad import QuadModel
from .ramp import RampModel
from .rampfitoutput import RampFitOutputModel
from .readnoise import ReadnoiseModel
from .reference import (
    ReferenceCubeModel,
    ReferenceFileModel,
    ReferenceImageModel,
    ReferenceQuadModel,
)
from .reset import ResetModel
from .resolution import MiriResolutionModel, ResolutionModel
from .rscd import RSCDModel
from .saturation import SaturationModel
from .segmap import SegmentationMapModel
from .sirs_kernel import SIRSKernelModel
from .slit import SlitDataModel, SlitModel
from .sossextractmodel import SossExtractModel
from .sosswavegrid import SossWaveGridModel
from .spec import MRSSpecModel, SpecModel, TSOSpecModel, WFSSSpecModel
from .speckernel import SpecKernelModel
from .specprofile import SpecProfileModel, SpecProfileSingleModel
from .specpsf import SpecPsfModel
from .spectrace import SpecTraceModel, SpecTraceSingleModel
from .straylight import StrayLightModel
from .superbias import SuperBiasModel
from .throughput import ThroughputModel
from .trapdensity import TrapDensityModel
from .trappars import TrapParsModel
from .trapsfilled import TrapsFilledModel
from .tsophot import TsoPhotModel
from .util import open, read_metadata  # noqa: A004
from .wavemap import WaveMapModel, WaveMapSingleModel
from .wcs_ref_models import (
    CameraModel,
    CollimatorModel,
    DisperserModel,
    DistortionModel,
    DistortionMRSModel,
    FilteroffsetModel,
    FOREModel,
    FPAModel,
    IFUFOREModel,
    IFUPostModel,
    IFUSlicerModel,
    MiriLRSSpecwcsModel,
    MiriWFSSSpecwcsModel,
    MSAModel,
    NIRCAMGrismModel,
    NIRISSGrismModel,
    OTEModel,
    RegionsModel,
    SpecwcsModel,
    WaveCorrModel,
    WavelengthrangeModel,
)

__all__ = [
    "ABVegaOffsetModel",
    "AmiLgFitModel",
    "AmiLgModel",
    "AmiOIModel",
    "AsnModel",
    "BarshadowModel",
    "CameraModel",
    "CollimatorModel",
    "CombinedSpecModel",
    "ContrastModel",
    "CubeModel",
    "DarkMIRIModel",
    "DarkModel",
    "DarkNirspecModel",
    "DisperserModel",
    "DistortionMRSModel",
    "DistortionModel",
    "EmiModel",
    "Extract1dIFUModel",
    "FOREModel",
    "FPAModel",
    "FgsImgApcorrModel",
    "FgsImgPhotomModel",
    "FilteroffsetModel",
    "FlatModel",
    "FringeFreqModel",
    "FringeModel",
    "GainModel",
    "GuiderCalModel",
    "GuiderRawModel",
    "IFUCubeModel",
    "IFUFOREModel",
    "IFUImageModel",
    "IFUPostModel",
    "IFUSlicerModel",
    "IPCModel",
    "IRS2Model",
    "ImageModel",
    "JwstDataModel",
    "LastFrameModel",
    "Level1bModel",
    "LinearityModel",
    "MRSMultiSpecModel",
    "MRSSpecModel",
    "MSAModel",
    "MaskModel",
    "MirImgApcorrModel",
    "MirImgPhotomModel",
    "MirLrsApcorrModel",
    "MirLrsPathlossModel",
    "MirLrsPhotomModel",
    "MirMrsApcorrModel",
    "MirMrsPhotomModel",
    "MirMrsPtCorrModel",
    "MirMrsXArtCorrModel",
    "MiriIFUCubeParsModel",
    "MiriLRSSpecwcsModel",
    "MiriResolutionModel",
    "MiriWFSSSpecwcsModel",
    "MultiCombinedSpecModel",
    "MultiExposureModel",
    "MultiSlitModel",
    "MultiSpecModel",
    "NIRCAMGrismModel",
    "NIRISSGrismModel",
    "NRMModel",
    "NirspecFlatModel",
    "NirspecIFUCubeParsModel",
    "NirspecIfuAreaModel",
    "NirspecMosAreaModel",
    "NirspecQuadFlatModel",
    "NirspecSlitAreaModel",
    "NisImgApcorrModel",
    "NisImgPhotomModel",
    "NisSossPhotomModel",
    "NisWfssApcorrModel",
    "NisWfssPhotomModel",
    "NrcImgApcorrModel",
    "NrcImgPhotomModel",
    "NrcWfssApcorrModel",
    "NrcWfssPhotomModel",
    "NrsFsApcorrModel",
    "NrsFsPhotomModel",
    "NrsIfuApcorrModel",
    "NrsMosApcorrModel",
    "NrsMosPhotomModel",
    "OTEModel",
    "OutlierIFUOutputModel",
    "PastasossModel",
    "PathlossModel",
    "PersistenceSatModel",
    "PictureFrameModel",
    "PixelAreaModel",
    "PsfMaskModel",
    "QuadModel",
    "RSCDModel",
    "RampFitOutputModel",
    "RampModel",
    "ReadnoiseModel",
    "ReferenceCubeModel",
    "ReferenceFileModel",
    "ReferenceImageModel",
    "ReferenceQuadModel",
    "RegionsModel",
    "ResetModel",
    "ResolutionModel",
    "SIRSKernelModel",
    "SaturationModel",
    "SegmentationMapModel",
    "SlitDataModel",
    "SlitModel",
    "SossBkgModel",
    "SossExtractModel",
    "SossWaveGridModel",
    "SpecKernelModel",
    "SpecModel",
    "SpecProfileModel",
    "SpecProfileSingleModel",
    "SpecPsfModel",
    "SpecTraceModel",
    "SpecTraceSingleModel",
    "SpecwcsModel",
    "StrayLightModel",
    "SuperBiasModel",
    "TSOMultiSpecModel",
    "TSOSpecModel",
    "ThroughputModel",
    "TrapDensityModel",
    "TrapParsModel",
    "TrapsFilledModel",
    "TsoPhotModel",
    "WFSSCombinedSpecModel",
    "WFSSMultiCombinedSpecModel",
    "WFSSMultiSpecModel",
    "WFSSSpecModel",
    "WaveCorrModel",
    "WaveMapModel",
    "WaveMapSingleModel",
    "WavelengthrangeModel",
    "WfssBkgModel",
    "open",
    "read_metadata",
]


_all_models = __all__[:-2]
_deprecated_models = ["AmiLgModel"]
_local_dict = locals()
_defined_models = {k: _local_dict[k] for k in _all_models}

# Modules that are not part of public API
_private_modules = ["conftest", "integration"]
