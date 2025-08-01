"""Data models for JWST."""

from . import _version
from .model_base import DataModel

__all__ = ["DataModel", "__version__"]


__version__ = _version.version
