from asdf.extension import ManifestExtension

from .converters.jwst_models import (
    Gwa2SlitConverter,
    Slit2MsaConverter,
    LogicalConverter,
    NirissSOSSConverter,
    RefractionIndexConverter,
    MIRI_AB2SliceConverter,
    NIRCAMGrismDispersionConverter,
    NIRISSGrismDispersionConverter,
    GratingEquationConverter,
    SnellConverter,
    Rotation3DToGWAConverter,
    CoordsConverter,
    V23ToSkyConverter,
    Msa2SlitConverter,
    Slit2GwaConverter,
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
    GratingEquationConverter(),
    SnellConverter(),
]

# The order here is important; asdf will prefer to use extensions
# that occur earlier in the list.
TRANSFORM_EXTENSIONS = [
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
        # 0.7.0 support v23tosky, register it's converter
        converters=_CONVERTERS
        + [
            V23ToSkyConverter(),
        ],
    ),
]
