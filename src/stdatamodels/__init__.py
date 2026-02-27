"""Data models for JWST."""

from . import _version
from .model_base import DataModel, JwstDataModel

__all__ = ["DataModel", "JwstDataModel", "__version__"]


__version__ = _version.version
