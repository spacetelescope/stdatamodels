"""Data models for JWST."""

from .model_base import DataModel
from .properties import ObjectNode, Node
from . import _version


__all__ = ["DataModel", "ObjectNode", "Node", "__version__"]


__version__ = _version.version
