"""Data models for JWST."""

from . import _version
from .model_base import JwstDataModel

__all__ = ["JwstDataModel", "__version__"]


__version__ = _version.version
