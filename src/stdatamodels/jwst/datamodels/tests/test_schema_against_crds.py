import os
import logging
from collections.abc import Iterable
import warnings
from pathlib import Path

import asdf
import pytest

from stdatamodels.jwst import datamodels as dm
from stdatamodels.exceptions import NoTypeWarning

os.environ["CRDS_SERVER_URL"] = "https://jwst-crds.stsci.edu"

# the CRDS_SERVER_URL environment variable must be set before
# crds is imported
import crds  # noqa: E402
from crds.client.api import cache_references, dump_files  # noqa: E402
from crds.core.exceptions import IrrelevantReferenceTypeError  # noqa: E402


log = logging.getLogger(__name__)


def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


ignored_parkeys = [
    "META.OBSERVATION.DATE",
    "META.OBSERVATION.TIME",
]

# Ignore pars files and deprecated files
ignored_stems = ("pars-", "drizpars")

apcorr_model_map = {
    "MIR_LRS-FIXEDSLIT": dm.MirLrsApcorrModel,
    "MIR_LRS-SLITLESS": dm.MirLrsApcorrModel,
    "MIR_MRS": dm.MirMrsApcorrModel,
    "MIR_IMAGE": dm.MirImgApcorrModel,
    "NRC_GRISM": dm.NrcWfssApcorrModel,
    "NRC_WFSS": dm.NrcWfssApcorrModel,
    "NRC_IMAGE": dm.NrcImgApcorrModel,
    "NIS_WFSS": dm.NisWfssApcorrModel,
    "NIS_IMAGE": dm.NisImgApcorrModel,
    "NRS_BRIGHTOBJ": dm.NrsFsApcorrModel,
    "NRS_FIXEDSLIT": dm.NrsFsApcorrModel,
    "NRS_IFU": dm.NrsIfuApcorrModel,
    "NRS_MSASPEC": dm.NrsMosApcorrModel,
    "FGS_IMAGE": dm.FgsImgApcorrModel,
    "FGS": dm.FgsImgApcorrModel,
    "NIRCAM": dm.NrcImgApcorrModel,
    "NIRISS": dm.NisWfssApcorrModel,
}

area_model_map = {
    "NRS_MSASPEC": dm.NirspecMosAreaModel,
    "NRS_FIXEDSLIT": dm.NirspecSlitAreaModel,
    "NRS_IFU": dm.NirspecIfuAreaModel,
    "other": dm.PixelAreaModel,
}

bkg_model_map = {
    "NRC_WFSS": dm.WfssBkgModel,
    "NIS_WFSS": dm.WfssBkgModel,
    "NIS_SOSS": dm.SossBkgModel,
}

cubepar_model_map = {
    "NIRSPEC": dm.NirspecIFUCubeParsModel,
    "MIRI": dm.MiriIFUCubeParsModel,
}

distortion_model_map = {
    "MIR_MRS": dm.DistortionMRSModel,
    "other": dm.DistortionModel,
}

flat_model_map = {
    "NIRSPEC": dm.NirspecFlatModel,
    "other": dm.FlatModel,
}

pathloss_model_map = {
    "MIR_LRS": dm.MirLrsPathlossModel,
    "other": dm.PathlossModel,
}

photom_model_map = {
    "MIR_LRS-FIXEDSLIT": dm.MirLrsPhotomModel,
    "MIR_LRS-SLITLESS": dm.MirLrsPhotomModel,
    "MIR_MRS": dm.MirMrsPhotomModel,
    "MIR_IMAGE": dm.MirImgPhotomModel,
    "NRC_GRISM": dm.NrcWfssPhotomModel,
    "NRC_WFSS": dm.NrcWfssPhotomModel,
    "NRC_IMAGE": dm.NrcImgPhotomModel,
    "NIS_WFSS": dm.NisWfssPhotomModel,
    "NIS_SOSS": dm.NisSossPhotomModel,
    "NIS_IMAGE": dm.NisImgPhotomModel,
    "NRS_BRIGHTOBJ": dm.NrsFsPhotomModel,
    "NRS_FIXEDSLIT": dm.NrsFsPhotomModel,
    "NRS_IFU": dm.NrsMosPhotomModel,
    "NRS_MSASPEC": dm.NrsMosPhotomModel,
    "FGS_IMAGE": dm.FgsImgPhotomModel,
    "FGS": dm.FgsImgPhotomModel,
    "NIRCAM": dm.NrcImgPhotomModel,
    "MIRI": dm.MirImgPhotomModel,
    "NIRISS": dm.NisWfssPhotomModel,
}

resol_model_map = {
    "MIRI": dm.MiriResolutionModel,
    "other": dm.ResolutionModel,
}

specwcs_model_map = {
    "MIR_LRS-FIXEDSLIT": dm.MiriLRSSpecwcsModel,
    "MIR_LRS-SLITLESS": dm.MiriLRSSpecwcsModel,
    "NRC_WFSS": dm.NIRCAMGrismModel,
    "NIS_WFSS": dm.NIRISSGrismModel,
    "other": dm.SpecwcsModel,
}

ref_to_multiples_dict = {
    "apcorr": apcorr_model_map,
    "area": area_model_map,
    "bkg": bkg_model_map,
    "cubepar": cubepar_model_map,
    "distortion": distortion_model_map,
    "flat": flat_model_map,
    "pathloss": pathloss_model_map,
    "photom": photom_model_map,
    "resol": resol_model_map,
    "specwcs": specwcs_model_map,
}

ref_to_datamodel_dict = {
    "abvegaoffset": dm.ABVegaOffsetModel,
    "barshadow": dm.BarshadowModel,
    "camera": dm.CameraModel,
    "collimator": dm.CollimatorModel,
    "dark": dm.DarkModel,
    "dflat": dm.NirspecFlatModel,
    "disperser": dm.DisperserModel,
    "emicorr": dm.EmiModel,
    "extract1d": dm.Extract1dIFUModel,
    "fflat": dm.NirspecFlatModel,
    "filteroffset": dm.FilteroffsetModel,
    "fore": dm.FOREModel,
    "fpa": dm.FPAModel,
    "fringe": dm.FringeModel,
    "fringefreq": dm.FringeFreqModel,
    "gain": dm.GainModel,
    "ifufore": dm.IFUFOREModel,
    "ifupost": dm.IFUPostModel,
    "ifuslicer": dm.IFUSlicerModel,
    "ipc": dm.IPCModel,
    "lastframe": dm.LastFrameModel,
    "linearity": dm.LinearityModel,
    "mask": dm.MaskModel,
    "mrsxartcorr": dm.MirMrsXArtCorrModel,
    "mrsptcorr": dm.MirMrsPtCorrModel,
    "msa": dm.MSAModel,
    "msaoper": None,
    "nrm": dm.NRMModel,
    "ote": dm.OTEModel,
    "pastasoss": dm.PastasossModel,
    "persat": dm.PersistenceSatModel,
    "psf": dm.SpecPsfModel,
    "psfmask": dm.PsfMaskModel,
    "readnoise": dm.ReadnoiseModel,
    "refpix": dm.IRS2Model,
    "regions": dm.RegionsModel,
    "reset": dm.ResetModel,
    "rscd": dm.RSCDModel,
    "saturation": dm.SaturationModel,
    "sflat": dm.NirspecFlatModel,
    "sirskernel": dm.SIRSKernelModel,
    "speckernel": dm.SpecKernelModel,
    "specprofile": dm.SpecProfileModel,
    "spectrace": dm.SpecTraceModel,
    "straymask": dm.StrayLightModel,
    "superbias": dm.SuperBiasModel,
    "throughput": dm.ThroughputModel,
    "trapdensity": dm.TrapDensityModel,
    "trappars": dm.TrapParsModel,
    "tsophot": dm.TsoPhotModel,
    "wavecorr": dm.WaveCorrModel,
    "wavelengthrange": dm.WavelengthrangeModel,
    "wavemap": dm.WaveMapModel,
    "wcsregions": None,
    "wfssbkg": dm.WfssBkgModel,
}


@pytest.mark.skipif(
    "config.getoption('--no-crds', True)",
    reason="no_crds option was enabled",
)
@pytest.mark.parametrize("instrument", ["fgs", "miri", "nircam", "niriss", "nirspec"])
def test_crds_selectors_vs_datamodel(jail_environ, instrument):
    log.info(f"crds_path: {crds.config.get_crds_path()}")
    log.info(f"crds_server: {crds.config.get_server_url('jwst')}")

    context = crds.get_context_name("jwst")
    dump_files(context)
    pmap = crds.get_cached_mapping(context)

    imap = pmap.get_imap(instrument)
    log.info(f"Beginning tests for {instrument}")

    # get the reftypes
    reftypes = imap.get_filekinds()

    # remove pars- files
    _ = [reftypes.remove(name) for name in reftypes[::-1] if name.startswith(ignored_stems)]

    # iterate over reftypes for this instrument
    for reftype in reftypes:
        try:
            r = imap.get_rmap(reftype)
            parkeys = [p for p in list(flatten(list(r.parkey))) if p not in ignored_parkeys]
            log.debug(f"Parkeys for {reftype}: {parkeys}")
            for f in r.reference_names():
                # Ensure filetype is kind to be loaded into datamodel
                if "fits" in f or "asdf" in f:
                    # Find datamodel appropriate for this reference file
                    # If reftype has multiple datamodels possible, do some guesswork
                    if reftype in ref_to_multiples_dict.keys():
                        model_map = ref_to_multiples_dict[reftype]
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", NoTypeWarning)
                            refs = cache_references(context, {reftype: f})
                            if Path(refs[reftype]).name == "jwst_fgs_distortion_0003.asdf":
                                # jwst_fgs_distortion_0003.asdf contains an invalid set of ASDF
                                # tags and will load with a warning for asdf >= 3.0. This is a known
                                # issue and doesn't affect the use of the file in this test.
                                warnings.simplefilter(
                                    "ignore", asdf.exceptions.AsdfConversionWarning
                                )

                            with dm.open(refs[reftype]) as model:
                                try:
                                    ref_exptype = model.meta.exposure.type
                                except AttributeError:
                                    ref_exptype = None
                                ref_instrument = model.meta.instrument.name
                        if ref_exptype in model_map.keys():
                            ref_model = model_map[ref_exptype]
                        elif ref_instrument in model_map.keys():
                            ref_model = model_map[ref_instrument]
                        else:
                            ref_model = model_map["other"]
                    # Simple one to one translation of reftype to datamodel
                    else:
                        ref_model = ref_to_datamodel_dict[reftype]

                    log.debug(f"Loading {reftype} reference for {instrument} as {ref_model}")

                    if ref_model is None:
                        log.warning(f"No datamodel found for {reftype}: skipping...")
                        break

                    # No need to actually load the reference file into the datamodel!
                    with ref_model() as m:
                        for key in parkeys:
                            assert len(m.search_schema(key.lower())) > 0, (
                                f"{f} missing {key} required by {r.basename}"
                            )
                    break
        except IrrelevantReferenceTypeError as e:
            log.debug(e)
            pass
