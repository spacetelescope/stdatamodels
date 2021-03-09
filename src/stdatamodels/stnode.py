"""
Proof of concept of using tags with the data model framework
"""

from asdf.extension import Converter
from collections import UserList
from .stuserdict import STUserDict as UserDict

class DNode(UserDict):

    _tag = None
    def __init__(self, node=None):

        if node is None:
            self.__dict__['_data']= {}
        elif isinstance(node, dict):
            self.__dict__['_data'] = node
        else:
            raise ValueError("Initializer only accepts dicts")
        # else:
        #     self.data = node.data
    
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
        if key in self._data:
            self.__dict__['_data'][key] = value
        else:
            raise KeyError(f"No such key ({key}) found in node")

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


