from asdf.extension import ManifestExtension

from .converters.jwst_models import (Gwa2SlitConverter, Slit2MsaConverter, LogicalConverter,
                                     NirissSOSSConverter, RefractionIndexConverter,
                                     MIRI_AB2SliceConverter, NIRCAMGrismDispersionConverter,
                                     NIRISSGrismDispersionConverter, GratingEquationConverter,
                                     SnellConverter, Rotation3DToGWAConverter,
                                     CoordsConverter, V23ToSkyConverter)


# The order here is important; asdf will prefer to use extensions
# that occur earlier in the list.
TRANSFORM_EXTENSIONS = [
    ManifestExtension.from_uri(
        "asdf://stsci.edu/jwst_pipeline/manifests/jwst_transforms-1.0.0",
        legacy_class_names=["jwst.transforms.jwextension.JWSTExtension"],
        converters=[
            CoordsConverter(),
            Gwa2SlitConverter(),
            Slit2MsaConverter(),
            LogicalConverter(),
            NirissSOSSConverter(),
            RefractionIndexConverter(),
            Rotation3DToGWAConverter(),
            MIRI_AB2SliceConverter(),
            NIRCAMGrismDispersionConverter(),
            NIRISSGrismDispersionConverter(),
            GratingEquationConverter(),
            SnellConverter(),
        ],
    ),
    ManifestExtension.from_uri(
        "asdf://stsci.edu/jwst_pipeline/manifests/jwst_transforms-0.7.0",
        legacy_class_names=["jwst.transforms.jwextension.JWSTExtension"],
        converters=[
            CoordsConverter(),
            Gwa2SlitConverter(),
            Slit2MsaConverter(),
            LogicalConverter(),
            NirissSOSSConverter(),
            RefractionIndexConverter(),
            Rotation3DToGWAConverter(),
            MIRI_AB2SliceConverter(),
            NIRCAMGrismDispersionConverter(),
            NIRISSGrismDispersionConverter(),
            GratingEquationConverter(),
            SnellConverter(),
            V23ToSkyConverter(),
        ],
    )
]
