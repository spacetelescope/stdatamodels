from asdf.extension import ManifestExtension

from .converters.jwst_models import (
    CoordsConverter,
    GratingEquationConverter,
    Gwa2SlitConverter,
    LogicalConverter,
    MIRI_AB2SliceConverter,
    MIRIWFSSDispersionConverter,
    Msa2SlitConverter,
    NIRCAMGrismDispersionConverter,
    NIRISSGrismDispersionConverter,
    NirissSOSSConverter,
    RefractionIndexConverter,
    Rotation3DToGWAConverter,
    Slit2GwaConverter,
    Slit2MsaConverter,
    SnellConverter,
    UnsupportedConverter,
)

_CONVERTERS = [
    CoordsConverter(),
    Gwa2SlitConverter(),
    Slit2GwaConverter(),
    Slit2MsaConverter(),
    Msa2SlitConverter(),
    LogicalConverter(),
    NirissSOSSConverter(),
    RefractionIndexConverter(),
    Rotation3DToGWAConverter(),
    MIRI_AB2SliceConverter(),
    NIRCAMGrismDispersionConverter(),
    NIRISSGrismDispersionConverter(),
    MIRIWFSSDispersionConverter(),
    GratingEquationConverter(),
    SnellConverter(),
    UnsupportedConverter(),
]

# The order here is important; asdf will prefer to use extensions
# that occur earlier in the list.
TRANSFORM_EXTENSIONS = [
    ManifestExtension.from_uri(
        "asdf://stsci.edu/jwst_pipeline/manifests/jwst_transforms-1.3.0",
        legacy_class_names=["jwst.transforms.jwextension.JWSTExtension"],
        converters=_CONVERTERS,
    ),
    ManifestExtension.from_uri(
        "asdf://stsci.edu/jwst_pipeline/manifests/jwst_transforms-1.2.0",
        legacy_class_names=["jwst.transforms.jwextension.JWSTExtension"],
        converters=_CONVERTERS,
    ),
    ManifestExtension.from_uri(
        "asdf://stsci.edu/jwst_pipeline/manifests/jwst_transforms-1.1.0",
        legacy_class_names=["jwst.transforms.jwextension.JWSTExtension"],
        converters=_CONVERTERS,
    ),
    ManifestExtension.from_uri(
        "asdf://stsci.edu/jwst_pipeline/manifests/jwst_transforms-1.0.0",
        legacy_class_names=["jwst.transforms.jwextension.JWSTExtension"],
        converters=_CONVERTERS,
    ),
    ManifestExtension.from_uri(
        "asdf://stsci.edu/jwst_pipeline/manifests/jwst_transforms-0.7.0",
        legacy_class_names=["jwst.transforms.jwextension.JWSTExtension"],
        converters=_CONVERTERS,
    ),
]
