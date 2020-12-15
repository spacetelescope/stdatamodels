"""
Proof of concept of using tags with the data model framework
"""

from asdf.extension import Converter
from collections import UserList
from .stuserdict import STUserDict as UserDict
import asdf
import asdf.schema as asdfschema

class DNode(UserDict):

    _tag = None
    _ctx = None

    def __init__(self, node=None):

        if node is None:
            self.__dict__['_data']= {}
        elif isinstance(node, dict):
            self.__dict__['_data'] = node
        else:
            raise ValueError("Initializer only accepts dicts")
        self._x_schema = None
        self._schema_uri = None
        # else:
        #     self.data = node.data

    @property
    def ctx(self):
        if self._ctx is None:
            DNode._ctx = asdf.AsdfFile()
        return self._ctx
    
   
    def __getattr__(self, key):
        """
        Permit accessing dict keys as attributes, assuming they are legal Python
        variable names.
        """
        if key in self._data:
            value = self._data[key]
            if isinstance(value, dict):
                return DNode(value)
            elif isinstance(value, list):
                return LNode(value)
            else:
                return value
        else:
            raise KeyError(f"No such key ({key}) found in node")

    def __setattr__(self, key, value):
        """
        Permit assigning dict keys as attributes.
        """
        if key[0] != '_':
            if key in self._data:
                self.__dict__['_data'][key] = value
            else:
                raise KeyError(f"No such key ({key}) found in node")
        else:
            self.__dict__[key] = value

    # def __getindex__(self, key):
    #     return self.data[key]

    # def __setindex__(self, key, value):
    #     self.data[key] = value

class LNode(UserList):

    _tag = None
    def __init__(self, node=None):
        if node is None:
            self.data = []
        elif isinstance(node, list):
            self.data = node
        else:
            raise ValueError("Initalizer only accepts lists")
        # else:
        #     self.data = node.data

    def __getitem__(self, index):
        value = self.data[index]
        if isinstance(value, dict):
            return DNode(value)
        elif isinstance(value, list):
            return LNode(value)
        else:
            return value

class TaggedObjectNode(DNode):
    """
    Expects subclass to define a class instance of _tag
    """

    @property
    def tag(self):
        return self._tag

    def _schema(self):
        if self._x_schema is None:
            self._x_schema = self.get_schema()
        return self._x_schema



    def get_schema(self):
        """Retrieve the schema associated with this tag"""
        extension_manager = self.ctx.extension_manager
        tag_def = extension_manager.get_tag_definition(self.tag)
        schema_uri = tag_def.schema_uri
        print(schema_uri)
        schema = asdfschema._load_schema_cached(
            schema_uri, self.ctx, False, False)
        return schema

class TaggedListNode(LNode):

    @property
    def tag(self):
        return self._tag


class TaggedObjectNodeConverter(Converter):
    """
    This class is intended to be subclassed for specific tags
    """

    # tags = [
    #     "tag:stsci.edu:datamodels/program-*"
    # ]
    # types = ["stdatamodels.stnode.Program"]

    tags = []
    types = []

    def to_yaml_tree(self, obj, tags, ctx): 
        return obj

    def from_yaml_tree(self, node, tag, ctx):
        return (node)

###################################
#
# Roman section
#
###################################

class WfiImage(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/roman/wfi_image-1.0.0"

class WfiImageConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/roman/wfi_image-*"]
    types = ["stdatamodels.stnode.WfiImage"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return WfiImage(node)


class Exposure(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/roman/exposure-1.0.0"

class ExposureConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/roman/exposure-*"]
    types = ["stdatamodels.stnode.Exposure"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Exposure(node)

class Wfi(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/roman/wfi-1.0.0"

class WfiConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/roman/wfi-*"]
    types = ["stdatamodels.stnode.Wfi"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Wfi(node)


###################################
#
# JWST section
#
###################################

class NircamImage(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam_image-1.0.0"

class NircamImageConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam_image-*"]
    types = ["stdatamodels.stnode.NircamImage"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return NircamImage(node)

class Aperture(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/aperture-1.0.0"

class ApertureConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/aperture-*"]
    types = ["stdatamodels.stnode.Aperture"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Aperture(node)


class Association(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/association-1.0.0"

class AssociationConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/association-*"]
    types = ["stdatamodels.stnode.Association"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Association(node)

class Ephemeris(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/ephemeris-1.0.0"

class EphemerisConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/ephemeris-*"]
    types = ["stdatamodels.stnode.Ephemeris"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Ephemeris(node)

class FitsWcsInfo(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/fits_wcs_info-1.0.0"

class FitsWcsInfoConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/fits_wcs_info-*"]
    types = ["stdatamodels.stnode.FitsWcsInfo"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return FitsWcsInfo(node)


class Guidestar(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/guidestar-1.0.0"

class GuidestarConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/guidestar-*"]
    types = ["stdatamodels.stnode.Guidestar"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Guidestar(node)


class Nircam(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam-1.0.0"

class NircamConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam-*"]
    types = ["stdatamodels.stnode.Nircam"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Nircam(node)

class NircamCalibrationSteps(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam_calibration_steps-1.0.0"

class NircamCalibrationStepsConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam_calibration_steps-*"]
    types = ["stdatamodels.stnode.NircamCalibrationSteps"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return NircamCalibrationSteps(node)


class NircamDither(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam_dither-1.0.0"

class NircamDitherConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam_dither-*"]
    types = ["stdatamodels.stnode.NircamDither"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return NircamDither(node)


class NircamExposure(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam_exposure-1.0.0"

class NircamExposureConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam_exposure-*"]
    types = ["stdatamodels.stnode.NircamExposure"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return NircamExposure(node)

class NircamFocus(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam_focus-1.0.0"

class NircamFocusConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam_focus-*"]
    types = ["stdatamodels.stnode.NircamFocus"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return NircamFocus(node)

class NircamReferenceFiles(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam_reference_files-1.0.0"

class NircamReferenceFilesConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam_reference_files-*"]
    types = ["stdatamodels.stnode.NircamReferenceFiles"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return NircamReferenceFiles(node)

class NircamSubarray(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/nircam_subarray-1.0.0"

class NircamSubarrayConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/nircam_subarray-*"]
    types = ["stdatamodels.stnode.NircamSubarray"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return NircamSubarray(node)


class Observation(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/observation-1.0.0"

class ObservationConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/observation-*"]
    types = ["stdatamodels.stnode.Observation"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Observation(node)

class Photometry(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/photometry-1.0.0"

class PhotometryConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/photometry-*"]
    types = ["stdatamodels.stnode.Photometry"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Photometry(node)


class Program(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/program-1.0.0"

class ProgramConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/program-*"]
    types = ["stdatamodels.stnode.Program"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Program(node)


class Target(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/target-1.0.0"

class TargetConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/target-*"]
    types = ["stdatamodels.stnode.Target"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Target(node)

class Time(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/time-1.0.0"

class TimeConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/time-*"]
    types = ["stdatamodels.stnode.Time"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Time(node)


class VelocityAberration(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/velocity_aberration-1.0.0"

class VelocityAberrationConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/velocity_aberration-*"]
    types = ["stdatamodels.stnode.VelocityAberration"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return VelocityAberration(node)


class Visit(TaggedObjectNode):
    _tag = "tag:stsci.edu:datamodels/jwst/visit-1.0.0"

class VisitConverter(TaggedObjectNodeConverter):
    tags = ["tag:stsci.edu:datamodels/jwst/visit-*"]
    types = ["stdatamodels.stnode.Visit"]

    def to_yaml_tree(self, obj, tags, ctx):
        return obj._data

    def from_yaml_tree(self, node, tag, ctx):
        return Visit(node)
