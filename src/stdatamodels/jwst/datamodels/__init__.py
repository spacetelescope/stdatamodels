"""Datamodels for JWST pipeline."""

from .model_base import JwstDataModel
from .abvega_offset import ABVegaOffsetModel
from .amilg import AmiLgModel
from .amilgfitmodel import AmiLgFitModel
from .amioi import AmiOIModel
from .apcorr import FgsImgApcorrModel, MirImgApcorrModel
from .apcorr import NrcImgApcorrModel, NisImgApcorrModel
from .apcorr import MirLrsApcorrModel, MirMrsApcorrModel
from .apcorr import NrcWfssApcorrModel, NisWfssApcorrModel
from .apcorr import NrsMosApcorrModel, NrsIfuApcorrModel, NrsFsApcorrModel
from .asn import AsnModel
from .background import SossBkgModel, WfssBkgModel
from .barshadow import BarshadowModel
from .combinedspec import CombinedSpecModel, WFSSCombinedSpecModel
from .contrast import ContrastModel
from .cube import CubeModel
from .dark import DarkModel, DarkMIRIModel, DarkNirspecModel
from .emi import EmiModel
from .extract1d_spec import Extract1dIFUModel
from .flat import FlatModel
from .fringe import FringeModel
from .fringefreq import FringeFreqModel
from .gain import GainModel
from .guider import GuiderRawModel, GuiderCalModel
from .ifucube import IFUCubeModel
from .ifucubepars import NirspecIFUCubeParsModel, MiriIFUCubeParsModel
from .ifuimage import IFUImageModel
from .mrsptcorr import MirMrsPtCorrModel
from .image import ImageModel
from .ipc import IPCModel
from .irs2 import IRS2Model
from .lastframe import LastFrameModel
from .level1b import Level1bModel
from .linearity import LinearityModel
from .mask import MaskModel
from .mrsxartcorr import MirMrsXArtCorrModel
from .multicombinedspec import MultiCombinedSpecModel, WFSSMultiCombinedSpecModel
from .multiexposure import MultiExposureModel
from .multislit import MultiSlitModel
from .multispec import MultiSpecModel, MRSMultiSpecModel, TSOMultiSpecModel, WFSSMultiSpecModel
from .nirspec_flat import NirspecFlatModel, NirspecQuadFlatModel
from .nrm import NRMModel
from .outlierifuoutput import OutlierIFUOutputModel
from .pathloss import PathlossModel, MirLrsPathlossModel
from .persat import PersistenceSatModel
from .photom import FgsImgPhotomModel
from .photom import MirImgPhotomModel, MirLrsPhotomModel, MirMrsPhotomModel
from .photom import NrcImgPhotomModel, NrcWfssPhotomModel
from .photom import NisImgPhotomModel, NisSossPhotomModel, NisWfssPhotomModel
from .photom import NrsFsPhotomModel, NrsMosPhotomModel
from .pixelarea import (
    PixelAreaModel,
    NirspecSlitAreaModel,
    NirspecMosAreaModel,
    NirspecIfuAreaModel,
)
from .psfmask import PsfMaskModel
from .quad import QuadModel
from .ramp import RampModel
from .rampfitoutput import RampFitOutputModel
from .readnoise import ReadnoiseModel
from .reference import (
    ReferenceFileModel,
    ReferenceImageModel,
    ReferenceCubeModel,
    ReferenceQuadModel,
)
from .reset import ResetModel
from .resolution import ResolutionModel, MiriResolutionModel
from .rscd import RSCDModel
from .saturation import SaturationModel
from .segmap import SegmentationMapModel
from .sirs_kernel import SIRSKernelModel
from .slit import SlitModel, SlitDataModel
from .pastasossmodel import PastasossModel
from .sossextractmodel import SossExtractModel
from .sosswavegrid import SossWaveGridModel
from .spec import SpecModel, MRSSpecModel, TSOSpecModel, WFSSSpecModel
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
from .wavemap import WaveMapModel, WaveMapSingleModel
from .wcs_ref_models import (
    DistortionModel,
    DistortionMRSModel,
    SpecwcsModel,
    RegionsModel,
    WavelengthrangeModel,
    CameraModel,
    CollimatorModel,
    OTEModel,
    FOREModel,
    FPAModel,
    IFUPostModel,
    IFUFOREModel,
    IFUSlicerModel,
    MSAModel,
    FilteroffsetModel,
    DisperserModel,
    NIRCAMGrismModel,
    NIRISSGrismModel,
    MiriLRSSpecwcsModel,
    WaveCorrModel,
)
from .util import open, read_metadata  # noqa: A004


__all__ = [
    "open",
    "read_metadata",
    "JwstDataModel",
    "ABVegaOffsetModel",
    "AmiLgModel",
    "AmiLgFitModel",
    "AmiOIModel",
    "NRMModel",
    "FgsImgApcorrModel",
    "MirImgApcorrModel",
    "NrcImgApcorrModel",
    "NisImgApcorrModel",
    "MirLrsApcorrModel",
    "MirMrsApcorrModel",
    "NrcWfssApcorrModel",
    "NisWfssApcorrModel",
    "NrsMosApcorrModel",
    "NrsFsApcorrModel",
    "NrsIfuApcorrModel",
    "AsnModel",
    "BarshadowModel",
    "CameraModel",
    "CollimatorModel",
    "CombinedSpecModel",
    "ContrastModel",
    "CubeModel",
    "DarkModel",
    "DarkMIRIModel",
    "DarkNirspecModel",
    "DisperserModel",
    "DistortionModel",
    "DistortionMRSModel",
    "EmiModel",
    "Extract1dIFUModel",
    "FilteroffsetModel",
    "FlatModel",
    "NirspecFlatModel",
    "NirspecQuadFlatModel",
    "FOREModel",
    "FPAModel",
    "FringeModel",
    "FringeFreqModel",
    "GainModel",
    "GuiderRawModel",
    "GuiderCalModel",
    "IFUCubeModel",
    "NirspecIFUCubeParsModel",
    "MiriIFUCubeParsModel",
    "MirMrsPtCorrModel",
    "MirMrsXArtCorrModel",
    "IFUFOREModel",
    "IFUImageModel",
    "IFUPostModel",
    "IFUSlicerModel",
    "ImageModel",
    "IPCModel",
    "IRS2Model",
    "LastFrameModel",
    "Level1bModel",
    "LinearityModel",
    "MaskModel",
    "MiriLRSSpecwcsModel",
    "MSAModel",
    "MultiCombinedSpecModel",
    "MultiExposureModel",
    "MultiSlitModel",
    "MultiSpecModel",
    "MRSMultiSpecModel",
    "TSOMultiSpecModel",
    "NIRCAMGrismModel",
    "NIRISSGrismModel",
    "OTEModel",
    "OutlierIFUOutputModel",
    "PathlossModel",
    "MirLrsPathlossModel",
    "PersistenceSatModel",
    "PixelAreaModel",
    "NirspecSlitAreaModel",
    "NirspecMosAreaModel",
    "NirspecIfuAreaModel",
    "FgsImgPhotomModel",
    "MirImgPhotomModel",
    "MirLrsPhotomModel",
    "MirMrsPhotomModel",
    "NrcImgPhotomModel",
    "NrcWfssPhotomModel",
    "NisImgPhotomModel",
    "NisSossPhotomModel",
    "NisWfssPhotomModel",
    "NrsFsPhotomModel",
    "NrsMosPhotomModel",
    "PastasossModel",
    "PsfMaskModel",
    "QuadModel",
    "RampModel",
    "RampFitOutputModel",
    "ReadnoiseModel",
    "ReferenceFileModel",
    "ReferenceCubeModel",
    "ReferenceImageModel",
    "ReferenceQuadModel",
    "RegionsModel",
    "ResetModel",
    "ResolutionModel",
    "MiriResolutionModel",
    "RSCDModel",
    "SaturationModel",
    "SIRSKernelModel",
    "SlitDataModel",
    "SlitModel",
    "SpecModel",
    "MRSSpecModel",
    "TSOSpecModel",
    "SegmentationMapModel",
    "SossBkgModel",
    "SossExtractModel",
    "SossWaveGridModel",
    "SpecKernelModel",
    "SpecProfileModel",
    "SpecProfileSingleModel",
    "SpecTraceModel",
    "SpecTraceSingleModel",
    "SpecPsfModel",
    "SpecwcsModel",
    "StrayLightModel",
    "SuperBiasModel",
    "ThroughputModel",
    "TrapDensityModel",
    "TrapParsModel",
    "TrapsFilledModel",
    "TsoPhotModel",
    "WavelengthrangeModel",
    "WaveCorrModel",
    "WaveMapModel",
    "WaveMapSingleModel",
    "WfssBkgModel",
    "WFSSCombinedSpecModel",
    "WFSSMultiCombinedSpecModel",
    "WFSSMultiSpecModel",
    "WFSSSpecModel",
]


_all_models = __all__[2:]
_local_dict = locals()
_defined_models = {k: _local_dict[k] for k in _all_models}

# Modules that are not part of public API
_private_modules = ["conftest", "integration"]
