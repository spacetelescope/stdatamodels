# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Models used by the JWST pipeline.

The models are written using the astropy.modeling framework.
Since they are specific to JWST, the models and their ASDF schemas
are kept here separately from astropy. An ASDF extension for this package is
registered with ASDF through entry points.
"""

import math
import warnings
from collections import namedtuple
from functools import partial

import numpy as np
from astropy.modeling.core import Model
from astropy.modeling.models import Const1D, Mapping, Rotation2D, Tabular1D
from astropy.modeling.models import math as astmath
from astropy.modeling.parameters import InputParameterError, Parameter
from gwcs.spectroscopy import SellmeierGlass, SellmeierZemax, Snell3D

from stdatamodels.properties import ListNode

__all__ = [
    "Gwa2Slit",
    "Slit2Msa",
    "Slit2MsaLegacy",
    "Logical",
    "NirissSOSSModel",
    "Slit",
    "NIRCAMForwardRowGrismDispersion",
    "NIRCAMForwardColumnGrismDispersion",
    "NIRCAMBackwardGrismDispersion",
    "MIRI_AB2Slice",
    "GrismObject",
    "NIRISSForwardRowGrismDispersion",
    "NIRISSForwardColumnGrismDispersion",
    "NIRISSBackwardGrismDispersion",
    "MIRIWFSSBackwardDispersion",
    "MIRIWFSSForwardDispersion",
    "V2V3ToIdeal",
    "IdealToV2V3",
    "RefractionIndexFromPrism",
    "Snell",
    "Rotation3DToGWA",
    "AngleFromGratingEquation",
    "WavelengthFromGratingEquation",
]


N_SHUTTERS_QUADRANT = 62415
""" Number of shutters per quadrant in the NIRSPEC MSA shutter array"""


Slit = namedtuple(
    "Slit",
    [
        "name",
        "shutter_id",
        "dither_position",
        "xcen",
        "ycen",
        "ymin",
        "ymax",
        "quadrant",
        "source_id",
        "shutter_state",
        "source_name",
        "source_alias",
        "stellarity",
        "source_xpos",
        "source_ypos",
        "source_ra",
        "source_dec",
        "slit_xscale",
        "slit_yscale",
        "slit_id",
    ],
)
""" Nirspec Slit structure definition"""


Slit.__new__.__defaults__ = (
    "",
    0,
    0,
    0.0,
    0.0,
    0.0,
    0.0,
    0,
    0,
    "",
    "",
    "",
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    1.0,
    -9999,
)


class GrismObject(
    namedtuple(
        "GrismObject",
        (
            "sid",
            "order_bounding",
            "sky_centroid",
            "partial_order",
            "waverange",
            "sky_bbox_ll",
            "sky_bbox_lr",
            "sky_bbox_ur",
            "sky_bbox_ul",
            "xcentroid",
            "ycentroid",
            "is_extended",
            "isophotal_abmag",
        ),
        rename=False,
    )
):
    """
    Grism Objects identified from a direct image catalog and segment map.

    Notes
    -----
    The object bounding box is computed from the segmentation map,
    using the min and max wavelength for each of the orders that
    are available. The order_bounding member is a dictionary of
    bounding boxes for the object keyed by order

    ra and dec are the sky ra and dec of the center of the object as measured
    from the non-dispersed image.

    order_bounding is stored as a lookup dictionary per order and contains
    the object x,y bounding location on the grism image
    GrismObject(order_bounding={"+1":((xmin,xmax),(ymin,ymax)),"+2":((2,3),(2,3))})
    """

    __slots__ = ()  # prevent instance dictionary for lower memory

    def __new__(
        cls,
        sid=None,
        order_bounding=None,
        sky_centroid=None,
        partial_order=None,
        waverange=None,
        sky_bbox_ll=None,
        sky_bbox_lr=None,
        sky_bbox_ur=None,
        sky_bbox_ul=None,
        xcentroid=None,
        ycentroid=None,
        is_extended=None,
        isophotal_abmag=None,
    ):
        """
        Create a new GrismObject.

        Parameters
        ----------
        sid : int
            Source identified
        order_bounding : dict{order: tuple}
            Contains the object x,y bounding locations on the image
            keyed on spectral order
        sky_centroid : :class:`astropy.coordinates.SkyCoord`
            RA and Dec of the center of the object
        partial_order : bool
            True if the order is only partially contained on the image
        waverange : list
            Wavelength range for the order
        sky_bbox_ll : :class:`astropy.coordinates.SkyCoord`
            Lower left corner of the minimum bounding box
        sky_bbox_lr : :class:`astropy.coordinates.SkyCoord`
            Lower right corder of the minimum bounding box
        sky_bbox_ur : :class:`astropy.coordinates.SkyCoord`
            Upper right corner of the minimum bounding box
        sky_bbox_ul : :class:`astropy.coordinates.SkyCoord`
            Upper left corner of the minimum bounding box
        xcentroid, ycentroid : float
            The x, y center of object in pixels
        is_extended : bool
            True if marked as extended in the source catalog
        isophotal_abmag : float
            The isophotal_abmag from the source catalog

        Returns
        -------
        GrismObject
            A new GrismObject instance.
        """
        if order_bounding is None:
            order_bounding = {}
        if partial_order is None:
            partial_order = {}
        return super(GrismObject, cls).__new__(
            cls,
            sid=sid,
            order_bounding=order_bounding,
            sky_centroid=sky_centroid,
            partial_order=partial_order,
            waverange=waverange,
            sky_bbox_ll=sky_bbox_ll,
            sky_bbox_lr=sky_bbox_lr,
            sky_bbox_ur=sky_bbox_ur,
            sky_bbox_ul=sky_bbox_ul,
            xcentroid=xcentroid,
            ycentroid=ycentroid,
            is_extended=is_extended,
            isophotal_abmag=isophotal_abmag,
        )

    def __str__(self):
        """Return a pretty print for the object information."""
        return (
            f"id: {self.sid}\n"
            f"order_bounding {str(self.order_bounding)}\n"
            f"sky_centroid: {str(self.sky_centroid)}\n"
            f"sky_bbox_ll: {str(self.sky_bbox_ll)}\n"
            f"sky_bbox_lr: {str(self.sky_bbox_lr)}\n"
            f"sky_bbox_ur: {str(self.sky_bbox_ur)}\n"
            f"sky_bbox_ul:{str(self.sky_bbox_ul)}\n"
            f"xcentroid: {self.xcentroid}\n"
            f"ycentroid: {self.ycentroid}\n"
            f"partial_order: {str(self.partial_order)}\n"
            f"waverange: {str(self.waverange)}\n"
            f"is_extended: {str(self.is_extended)}\n"
            f"isophotal_abmag: {str(self.isophotal_abmag)}\n"
        )


class MIRI_AB2Slice(Model):  # noqa: N801
    """MIRI MRS alpha, beta to slice transform."""

    standard_broadcasting = False
    _separable = False
    fittable = False

    n_inputs = 1
    n_outputs = 1

    beta_zero = Parameter("beta_zero", default=0)
    """ Beta_zero parameter"""
    beta_del = Parameter("beta_del", default=1)
    """ Beta_del parameter"""
    channel = Parameter("channel", default=1)
    """ MIRI MRS channel: one of 1, 2, 3, 4"""

    def __init__(self, beta_zero=beta_zero, beta_del=beta_del, channel=channel, **kwargs):
        """
        Initialize the model.

        Parameters
        ----------
        beta_zero : float
            Beta coordinate of the center of slice 1 in the MIRI MRS.
        beta_del : float
            Slice width.
        channel : int
            MIRI MRS channel number. Valid values are 1, 2, 3, 4.
        **kwargs
            Additional keyword arguments to pass to Model.
        """
        super().__init__(beta_zero=beta_zero, beta_del=beta_del, channel=channel, **kwargs)
        self.inputs = ("beta",)
        """ "beta": the beta angle """
        self.outputs = ("slice",)
        """ "slice": Slice number"""

    @staticmethod
    def evaluate(beta, beta_zero, beta_del, channel):
        """
        Convert beta to slice number.

        Parameters
        ----------
        beta : float or np.ndarray
            The beta angle.
        beta_zero : float or np.ndarray
            Beta coordinate of the center of slice 1 in the MIRI MRS.
        beta_del : float or np.ndarray
            Slice width.
        channel : int or np.ndarray
            MIRI MRS channel number. Valid values are 1, 2, 3, 4.

        Returns
        -------
        int or np.ndarray
            The slice number.
        """
        s = channel * 100 + (beta - beta_zero) / beta_del + 1
        return _toindex(s)


class RefractionIndexFromPrism(Model):
    """Compute the refraction index of a prism (NIRSpec)."""

    standard_broadcasting = False
    _separable = False

    n_inputs = 3
    n_outputs = 1

    prism_angle = Parameter(setter=np.deg2rad, getter=np.rad2deg)

    def __init__(self, prism_angle, name=None):
        """
        Initialize the model.

        Parameters
        ----------
        prism_angle : float
            Prism angle in degrees.
        name : str, optional
            Name of the model
        """
        super(RefractionIndexFromPrism, self).__init__(prism_angle=prism_angle, name=name)
        self.inputs = (
            "alpha_in",
            "beta_in",
            "alpha_out",
        )
        self.outputs = ("n",)

    def evaluate(self, alpha_in, beta_in, alpha_out, prism_angle):
        """
        Compute the refraction index of a prism.

        Parameters
        ----------
        alpha_in, beta_in : float or np.ndarray
            Angle of incidence in radians.
        alpha_out : float or np.ndarray
            Angle of emergence in radians.
        prism_angle : float or np.ndarray
            Prism angle in radians.

        Returns
        -------
        float
            Refraction index of the prism.
        """
        # prism_angle is always a 1 element numpy array
        sangle = math.sin(prism_angle.item())
        cangle = math.cos(prism_angle.item())
        nsq = (
            ((alpha_out + alpha_in * (1 - 2 * sangle**2)) / (2 * sangle * cangle)) ** 2
            + alpha_in**2
            + beta_in**2
        )
        return np.sqrt(nsq)


class Gwa2Slit(Model):
    """
    NIRSpec GWA to slit transform.

    Parameters
    ----------
    slits : list
        A list of open slits.
        A slit is a namedtuple of type `~stdatamodels.jwst.transforms.models.Slit`
        Slit("name", "shutter_id", "dither_position", "xcen", "ycen", "ymin", "ymax",
        "quadrant", "source_id", "shutter_state", "source_name",
        "source_alias", "stellarity", "source_xpos", "source_ypos",
        "source_ra", "source_dec"])
    models : list
        List of models (:class:`astropy.modeling.core.Model`) corresponding to the
        list of slits.
    """

    _separable = False

    n_inputs = 4
    n_outputs = 4

    def __init__(self, slits, models):
        if np.iterable(slits[0]):
            self.slit_ids = []
            self._slits = []
            for slit in slits:
                slit_tuple = Slit(*slit)
                if slit_tuple.slit_id == -9999:
                    self.slit_ids.append(slit_tuple.name)
                else:
                    self.slit_ids.append(slit_tuple.slit_id)
                self._slits.append(tuple(slit_tuple))
        else:
            self._slits = list(slits)
            self.slit_ids = self._slits

        self.models = models
        super(Gwa2Slit, self).__init__()
        self.inputs = ("name", "angle1", "angle2", "angle3")
        """
        Name of the slit and the three angle coordinates at
        the GWA going from detector to sky."""
        self.outputs = ("name", "x_slit", "y_slit", "lam")
        """ Name of the slit, x and y coordinates within the virtual slit and wavelength."""

    @property
    def slits(self):
        """
        Return the slits.

        Returns
        -------
        list
            List of `~stdatamodels.jwst.transforms.models.Slit` objects.
        """
        if np.iterable(self._slits[0]):
            return [Slit(*row) for row in self._slits]
        else:
            return self.slit_ids

    def get_model(self, name):
        """
        Retrieve the model for a given slit.

        Parameters
        ----------
        name : str
            Name of the slit.

        Returns
        -------
        :class:`astropy.modeling.core.Model`
            Model for the given slit.
        """
        index = self.slit_ids.index(name)
        return self.models[index]

    def evaluate(self, name, x, y, z):
        """
        Compute the x and y coordinates in the MSA frame for a given slit.

        Parameters
        ----------
        name : str
            Name of the slit.
        x, y, z : float or np.ndarray
            The three angle coordinates at the GWA going from detector to sky.

        Returns
        -------
        name : str
            Name of the slit.
        x_slit, y_slit : float or np.ndarray
            The x and y coordinates within the virtual slit.
        lam : float or np.ndarray
            Wavelength.
        """
        index = self.slit_ids.index(name)
        return (name,) + self.models[index](x, y, z)

    def inverse(self):
        """Create an inverse model."""
        inv_models = [m.inverse for m in self.models]
        return Slit2Gwa(self.slits, inv_models)


class Slit2Gwa(Model):
    """
    NIRSpec slit to GWA transform.

    Parameters
    ----------
    slits : list
        A list of open slits.
        A slit is a namedtuple of type `~stdatamodels.jwst.transforms.models.Slit`
        Slit("name", "shutter_id", "dither_position", "xcen", "ycen", "ymin", "ymax",
        "quadrant", "source_id", "shutter_state", "source_name",
        "source_alias", "stellarity", "source_xpos", "source_ypos",
        "source_ra", "source_dec"])
    models : list
        List of models (:class:`astropy.modeling.core.Model`) corresponding to the
        list of slits.
    """

    _separable = False

    n_inputs = 4
    n_outputs = 4

    def __init__(self, slits, models):
        if np.iterable(slits[0]):
            self.slit_ids = []
            self._slits = []
            for slit in slits:
                slit_tuple = Slit(*slit)
                if slit_tuple.slit_id == -9999:
                    self.slit_ids.append(slit_tuple.name)
                else:
                    self.slit_ids.append(slit_tuple.slit_id)
                self._slits.append(tuple(slit_tuple))
        else:
            self._slits = list(slits)
            self.slit_ids = self._slits

        self.models = models
        super(Slit2Gwa, self).__init__()
        self.outputs = ("name", "angle1", "angle2", "angle3")
        """Slit name and the three angle coordinates at the GWA going from detector to sky."""
        self.inputs = ("name", "x_slit", "y_slit", "lam")
        """Slit name, x and y coordinates within the virtual slit and wavelength."""

    @property
    def slits(self):
        if np.iterable(self._slits[0]):
            return [Slit(*row) for row in self._slits]
        else:
            return self.slit_ids

    def get_model(self, name):
        index = self.slit_ids.index(name)
        return self.models[index]

    def evaluate(self, name, x, y, z):
        index = self.slit_ids.index(name)
        return (name,) + self.models[index](x, y, z)


class Slit2MsaLegacy(Model):
    """Transform from Nirspec ``slit_frame`` to ``msa_frame`` without passing slit name."""

    _separable = False

    n_inputs = 3
    n_outputs = 2

    def __init__(self, slits, models):
        """
        Initialize the model.

        Parameters
        ----------
        slits : list
            A list of open slits.
            A slit is a namedtuple, `~stdatamodels.jwst.transforms.models.Slit`
            Slit("name", "shutter_id", "dither_position", "xcen", "ycen", "ymin", "ymax",
            "quadrant", "source_id", "shutter_state", "source_name",
            "source_alias", "stellarity", "source_xpos", "source_ypos",
            "source_ra", "source_dec")
        models : list
            List of models (:class:`astropy.modeling.core.Model`) corresponding to the
            list of slits.
        """
        super(Slit2MsaLegacy, self).__init__()
        self.inputs = ("name", "x_slit", "y_slit")
        """ Name of the slit, x and y coordinates within the virtual slit."""
        self.outputs = ("x_msa", "y_msa")
        """ x and y coordinates in the MSA frame."""
        if np.iterable(slits[0]):
            self._slits = [tuple(s) for s in slits]
            self.slit_ids = [s[0] for s in self._slits]
        else:
            self._slits = list(slits)
            self.slit_ids = self._slits
        self.models = models

        warnings.warn(
            "This model contains a deprecated Slit2Msa transform. "
            "The WCS pipeline may be incomplete.",
            DeprecationWarning,
            stacklevel=2,
        )

    @property
    def slits(self):
        """
        Return the slits.

        Returns
        -------
        list
            List of `~stdatamodels.jwst.transforms.models.Slit` objects.
        """
        if np.iterable(self._slits[0]):
            return [Slit(*row) for row in self._slits]
        else:
            return self.slit_ids

    def get_model(self, name):
        """
        Retrieve the model for a given slit.

        Parameters
        ----------
        name : str
            Name of the slit.

        Returns
        -------
        :class:`astropy.modeling.core.Model`
            Model for the given slit.
        """
        index = self.slit_ids.index(name)
        return self.models[index]

    def evaluate(self, name, x, y):
        """
        Compute the x and y coordinates in the MSA frame for a given slit.

        Parameters
        ----------
        name : str
            Name of the slit.
        x, y : float
            The x and y coordinates within the virtual slit.

        Returns
        -------
        x_msa, y_msa : float
            The x and y coordinates in the MSA frame.
        """
        index = self.slit_ids.index(name)
        return self.models[index](x, y)


class Slit2Msa(Model):
    """Transform from Nirspec ``slit_frame`` to ``msa_frame``."""

    _separable = False

    n_inputs = 3
    n_outputs = 3

    def __init__(self, slits, models):
        """
        Initialize the model.

        Parameters
        ----------
        slits : list
            A list of open slits.
            A slit is a namedtuple, `~stdatamodels.jwst.transforms.models.Slit`
            Slit("name", "shutter_id", "dither_position", "xcen", "ycen", "ymin", "ymax",
            "quadrant", "source_id", "shutter_state", "source_name",
            "source_alias", "stellarity", "source_xpos", "source_ypos",
            "source_ra", "source_dec")
        models : list
            List of models (:class:`astropy.modeling.core.Model`) corresponding to the
            list of slits.
        """
        super(Slit2Msa, self).__init__()
        self.inputs = ("name", "x_slit", "y_slit")
        """ Name of the slit, x and y coordinates within the virtual slit."""
        self.outputs = ("x_msa", "y_msa", "name")
        """ x and y coordinates in the MSA frame."""
        if np.iterable(slits[0]):
            self.slit_ids = []
            self._slits = []
            for slit in slits:
                slit_tuple = Slit(*slit)
                if slit_tuple.slit_id == -9999:
                    self.slit_ids.append(slit_tuple.name)
                else:
                    self.slit_ids.append(slit_tuple.slit_id)
                self._slits.append(tuple(slit_tuple))
        else:
            self._slits = list(slits)
            self.slit_ids = self._slits
        self.models = models

    @property
    def slits(self):
        """
        Return the slits.

        Returns
        -------
        list
            List of `~stdatamodels.jwst.transforms.models.Slit` objects.
        """
        if np.iterable(self._slits[0]):
            return [Slit(*row) for row in self._slits]
        else:
            return self.slit_ids

    def get_model(self, name):
        """
        Retrieve the model for a given slit.

        Parameters
        ----------
        name : str
            Name of the slit.

        Returns
        -------
        :class:`astropy.modeling.core.Model`
            Model for the given slit.
        """
        index = self.slit_ids.index(name)
        return self.models[index]

    def evaluate(self, name, x, y):
        """
        Compute the x and y coordinates in the MSA frame for a given slit.

        Parameters
        ----------
        name : str
            Name of the slit.
        x, y : float or np.ndarray
            The x and y coordinates within the virtual slit.

        Returns
        -------
        x_msa, y_msa : float or np.ndarray
            The x and y coordinates in the MSA frame.
        """
        index = self.slit_ids.index(name)
        return self.models[index](x, y) + (name,)

    def inverse(self):
        """Create an inverse model."""
        models = [m.inverse for m in self.models]
        inv_model = Msa2Slit(self.slits, models)
        return inv_model


class Msa2Slit(Model):
    """
    Transform from Nirspec ``slit_frame`` to ``msa_frame``.

    Parameters
    ----------
    slits : list
        A list of open slits.
        A slit is a namedtuple, `~stdatamodels.jwst.transforms.models.Slit`
        Slit("name", "shutter_id", "dither_position", "xcen", "ycen", "ymin", "ymax",
        "quadrant", "source_id", "shutter_state", "source_name",
        "source_alias", "stellarity", "source_xpos", "source_ypos",
        "source_ra", "source_dec")
    models : list
        List of models (`:class:`astropy.modeling.core.Model`) corresponding to the
        list of slits.
    """

    _separable = False

    n_inputs = 3
    n_outputs = 3

    def __init__(self, slits, models):
        super(Msa2Slit, self).__init__()
        self.inputs = ("x_msa", "y_msa", "name")
        """ Name of the slit, x and y coordinates within the virtual slit."""
        self.outputs = ("name", "x_slit", "y_slit")
        """ x and y coordinates in the MSA frame."""
        if np.iterable(slits[0]):
            self.slit_ids = []
            self._slits = []
            for slit in slits:
                slit_tuple = Slit(*slit)
                if slit_tuple.slit_id == -9999:
                    self.slit_ids.append(slit_tuple.name)
                else:
                    self.slit_ids.append(slit_tuple.slit_id)
                self._slits.append(tuple(slit_tuple))
        else:
            self._slits = list(slits)
            self.slit_ids = self._slits
        self.models = models

    @property
    def slits(self):
        if np.iterable(self._slits[0]):
            return [Slit(*row) for row in self._slits]
        else:
            return self.slit_ids

    def get_model(self, name):
        index = self.slit_ids.index(name)
        return self.models[index]

    def evaluate(self, x, y, name):
        index = self.slit_ids.index(name)
        return (name,) + self.models[index](x, y)


class NirissSOSSModel(Model):
    """NIRISS SOSS wavelength solution model."""

    _separable = False

    n_inputs = 3
    n_outputs = 3

    def __init__(self, spectral_orders, models):
        """
        Initialize the model.

        Parameters
        ----------
        spectral_orders : list of int
            Spectral orders for which there is a wavelength solution.
        models : list of :class:`astropy.modeling.core.Model`
            A list of transforms representing the wavelength solution for
            each order in spectral orders. It should match the order in
            ``spectral_orders``.
        """
        super(NirissSOSSModel, self).__init__()
        self.inputs = ("x", "y", "spectral_order")
        """ x and y pixel coordinates and spectral order"""
        self.outputs = ("ra", "dec", "lam")
        """ RA and DEC coordinates and wavelength"""

        self.spectral_orders = spectral_orders
        self.models = dict(zip(spectral_orders, models, strict=False))

    def get_model(self, spectral_order):
        """
        Retrieve model for a given spectral order.

        Parameters
        ----------
        spectral_order : int
            Spectral order for which to retrieve the model.

        Returns
        -------
        model : :class:`astropy.modeling.core.Model`
            Model for the given spectral order.
        """
        return self.models[spectral_order]

    def evaluate(self, x, y, spectral_order):
        """
        Compute the RA, Dec, and wavelength for a given pixel coordinate and spectral order.

        Parameters
        ----------
        x, y : float or np.ndarray
            Pixel coordinates.
        spectral_order : int
            The input spectral order.

        Returns
        -------
        ra, dec : float or np.ndarray
            RA and Dec coordinates.
        lam : float or np.ndarray
            Wavelength.
        """
        # The spectral_order variable is coming in as an array/list of one element.
        # So, we are going to just take the 0'th element and use that as the index.
        try:
            order_number = int(spectral_order[0])
        except Exception as err:
            raise ValueError(f"Spectral order is not between 1 and 3, {spectral_order}") from err

        return self.models[order_number](x, y)


class Logical(Model):
    """
    Substitute values in an array where the condition is evaluated to True.

    Similar to numpy's where function.
    """

    n_inputs = 1
    n_outputs = 1
    _separable = False

    conditions = {"GT": np.greater, "LT": np.less, "EQ": np.equal, "NE": np.not_equal}

    def __init__(self, condition, compareto, value, **kwargs):
        """
        Initialize the model.

        Parameters
        ----------
        condition : str
            A string representing the logical, one of GT, LT, NE, EQ
        compareto : float, np.ndarray
            A number to compare to using the condition
            If ndarray then the input array, compareto and value should have the
            same shape.
        value : float, np.ndarray
            Value to substitute where condition is True.
        **kwargs
            Additional keyword arguments to pass to Model.
        """
        self.condition = condition.upper()
        self.compareto = compareto
        self.value = value
        super(Logical, self).__init__(**kwargs)
        self.inputs = ("x",)
        self.outputs = ("x",)

    def evaluate(self, x):
        """
        Compare x to ``compareto`` and substitute value where condition is True.

        Parameters
        ----------
        x : np.ndarray
            Input array.

        Returns
        -------
        array-like
            The input array with values substituted where the condition is True.
        """
        x = x.copy()
        m = ~np.isnan(x)
        m_ind = np.flatnonzero(m)
        if isinstance(self.compareto, np.ndarray):
            cond = self.conditions[self.condition](x[m], self.compareto[m])
            x.flat[m_ind[cond]] = self.value.flat[m_ind[cond]]
        else:
            cond = self.conditions[self.condition](x[m], self.compareto)
            x.flat[m_ind[cond]] = self.value
        return x

    def __repr__(self):
        txt = "{0}(condition={1}, compareto={2}, value={3})"
        return txt.format(self.__class__.__name__, self.condition, self.compareto, self.value)


class IdealToV2V3(Model):
    """
    Perform the transform from Ideal to telescope V2,V3 coordinate system.

    The two systems have the same origin: V2_REF, V3_REF.

    Note that this model has no schema implemented.
    """

    _separable = False
    n_inputs = 2
    n_outputs = 2

    v3idlyangle = Parameter()  # in deg
    v2ref = Parameter()  # in arcsec
    v3ref = Parameter()  # in arcsec
    vparity = Parameter()

    def __init__(self, v3idlyangle, v2ref, v3ref, vparity, name="idl2V", **kwargs):
        super(IdealToV2V3, self).__init__(
            v3idlyangle=v3idlyangle, v2ref=v2ref, v3ref=v3ref, vparity=vparity, name=name, **kwargs
        )
        self.inputs = ("xidl", "yidl")
        """ x and y coordinates in the telescope Ideal frame."""
        self.outputs = ("v2", "v3")
        """ coordinates in the telescope (V2,V3) frame."""

    @staticmethod
    def evaluate(xidl, yidl, v3idlyangle, v2ref, v3ref, vparity):
        """
        Transform from Ideal to V2, V3 telescope system.

        Parameters
        ----------
        xidl, yidl : ndarray-like
            Coordinates in Ideal System [in arcsec]
        v3idlyangle : float
            Angle between Ideal Y-axis and V3 [ in deg]
        v2ref, v3ref : ndarray-like
            Coordinates in V2, V3 [in arcsec]
        vparity : int
            Parity.

        Returns
        -------
        v2, v3 : ndarray-like
            Coordinates in the (V2, V3) telescope system [in arcsec].
        """
        v3idlyangle = np.deg2rad(v3idlyangle)

        v2 = v2ref + vparity * xidl * np.cos(v3idlyangle) + yidl * np.sin(v3idlyangle)
        v3 = v3ref - vparity * xidl * np.sin(v3idlyangle) + yidl * np.cos(v3idlyangle)
        return v2, v3

    def inverse(self):  # noqa: D102
        return V2V3ToIdeal(self.v3idlyangle, self.v2ref, self.v3ref, self.vparity)


class V2V3ToIdeal(Model):
    """
    Perform the transform from telescope V2,V3 to Ideal coordinate system.

    The two systems have the same origin - V2_REF, V3_REF.

    Note that this model has no schema implemented.
    """

    _separable = False

    n_inputs = 2
    n_outputs = 2

    v3idlyangle = Parameter()  # in deg
    v2ref = Parameter()  # in arcsec
    v3ref = Parameter()  # in arcsec
    vparity = Parameter()

    def __init__(self, v3idlyangle, v2ref, v3ref, vparity, name="V2idl", **kwargs):
        super(V2V3ToIdeal, self).__init__(
            v3idlyangle=v3idlyangle, v2ref=v2ref, v3ref=v3ref, vparity=vparity, name=name, **kwargs
        )
        self.inputs = ("v2", "v3")
        """ ('v2', 'v3'): coordinates in the telescope (V2,V3) frame."""
        self.outputs = ("xidl", "yidl")
        """ ('xidl', 'yidl'): x and y coordinates in the telescope Ideal frame."""

    @staticmethod
    def evaluate(v2, v3, v3idlyangle, v2ref, v3ref, vparity):
        """
        Transform from V2, V3 to Ideal telescope system.

        Parameters
        ----------
        v2, v3 : ndarray-like
            Coordinates in the telescope (V2, V3) frame [in arcsec].
        v3idlyangle : float
            Angle between Ideal Y-axis and V3 [in deg]
        v2ref, v3ref : ndarray-like
            Reference coordinates in V2, V3 [in arcsec]
        vparity : int
            Parity.

        Returns
        -------
        xidl, yidl : ndarray-like
            Coordinates in the Ideal telescope system [in arcsec].
        """
        v3idlyangle = np.deg2rad(v3idlyangle)

        xidl = vparity * ((v2 - v2ref) * np.cos(v3idlyangle) - (v3 - v3ref) * np.sin(v3idlyangle))
        yidl = (v2 - v2ref) * np.sin(v3idlyangle) + (v3 - v3ref) * np.cos(v3idlyangle)

        return xidl, yidl

    def inverse(self):  # noqa: D102
        return IdealToV2V3(self.v3idlyangle, self.v2ref, self.v3ref, self.vparity)


def _toindex(value):
    """
    Convert value to an int or an int array.

    Input coordinates converted to integers
    corresponding to the center of the pixel.
    The convention is that the center of the pixel is
    (0, 0), while the lower left corner is (-0.5, -0.5).

    Parameters
    ----------
    value : ndarray
        Input coordinates.

    Returns
    -------
    ndarray
        Integer coordinates representing pixel centers.

    Examples
    --------
    >>> from stdatamodels.jwst.transforms.models import _toindex
    >>> _toindex(np.array([-0.5, 0.49999]))
    array([0, 0])
    >>> _toindex(np.array([0.5, 1.49999]))
    array([1, 1])
    >>> _toindex(np.array([1.5, 2.49999]))
    array([2, 2])
    """
    indx = np.asarray(np.floor(np.asarray(value) + 0.5), dtype=int)
    return indx


class _GrismDispersionBase(Model):
    """Base class for grism dispersion models."""

    standard_broadcasting = False
    _separable = False
    fittable = False
    linear = False

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        inv_lmodels=None,
        inv_xmodels=None,
        inv_ymodels=None,
        name=None,
        sampling=40,
    ):
        self.orders = orders
        self.lmodels = lmodels
        self.xmodels = xmodels
        self.ymodels = ymodels
        self.inv_lmodels = inv_lmodels
        self.inv_xmodels = inv_xmodels
        self.inv_ymodels = inv_ymodels
        self._order_mapping = {int(k): v for v, k in enumerate(orders)}
        self.sampling = sampling
        meta = {"orders": orders}  # informational for users
        super().__init__(name=name, meta=meta)


class _ForwardGrismDispersionBase(_GrismDispersionBase):
    """Base class for forward grism dispersion models."""

    n_inputs = 5
    n_outputs = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("x", "y", "x0", "y0", "order")
        self.outputs = ("x", "y", "wavelength", "order")


class _BackwardGrismDispersionBase(_GrismDispersionBase):
    """Base class for backward grism dispersion models."""

    n_inputs = 4
    n_outputs = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inputs = ("x", "y", "wavelength", "order")
        self.outputs = ("x", "y", "x0", "y0", "order")


class _NIRCAMForwardGrismDispersion(_ForwardGrismDispersionBase):
    """Return the transform from grism to image for the given spectral order."""

    def __init__(self, dispaxis, *args, **kwargs):
        self.dispaxis = dispaxis
        super().__init__(*args, **kwargs)
        if self.dispaxis == "row":
            self.alongdisp_models = self.xmodels
            self.acrossdisp_models = self.ymodels
            self.inv_alongdisp_models = self.inv_xmodels
            self.inv_acrossdisp_models = self.inv_ymodels
        elif self.dispaxis == "column":
            self.alongdisp_models = self.ymodels
            self.acrossdisp_models = self.xmodels
            self.inv_alongdisp_models = self.inv_ymodels
            self.inv_acrossdisp_models = self.inv_xmodels
        else:
            raise ValueError(f"Invalid dispaxis: {dispaxis}. Must be 'row' or 'column'.")

    def evaluate(self, x, y, x0, y0, order):
        """
        Transform from the grism plane to the image plane.

        Parameters
        ----------
        x, y :  float or np.ndarray
            Input x, y location
        x0, y0 : float or np.ndarray
            Source object x-center, y-center
        order : int
            Input spectral order

        Returns
        -------
        x0, y0 : float or np.ndarray
            Coordinates of image plane x-center, y-center, same as input.
        l_poly : float or np.ndarray
            Wavelength solution for the given spectral order.
        order : int
            The spectral order, same as input.
        """
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        if self.dispaxis == "row":
            dist = x - x0
        elif self.dispaxis == "column":
            dist = y - y0

        if not self.inv_alongdisp_models:
            t = self.invdisp_interp(iorder, x0, y0, dist)
        else:
            t = self.inv_alongdisp_models[iorder](dist)

        lmodel = self.lmodels[iorder]
        l_poly = _evaluate_transform_guess_form(lmodel, x=x0, y=y0, t=t)

        return x0, y0, l_poly, order

    def invdisp_interp(self, order, x0, y0, dx):
        """
        Make a polynomial fit to xmodel and interpolate to find the wavelength.

        Parameters
        ----------
        order : int
            The input spectral order
        x0, y0 : float or np.ndarray
            Source object x-center, y-center.
        dx : float or np.ndarray
            The offset from x0 in the dispersion direction

        Returns
        -------
        f : float or np.ndarray
            The wavelength solution for the given dx
        """
        model = self.alongdisp_models[order]
        dx = np.atleast_1d(dx)
        if len(dx.shape) == 2:
            dx = dx[0, :]

        t0 = np.linspace(0.0, 1.0, self.sampling)

        # handle multiple inverse model types
        if isinstance(model, (ListNode, list, tuple)):
            if len(model[0].inputs) == 2:
                xr = _poly_with_spatial_dependence(t0, x0, y0, model)
            elif len(model[0].inputs) == 1:
                xr = (dx - model[0].c0.value) / model[0].c1.value
                return xr
            else:
                raise ValueError(f"Unexpected model coefficients: {model}")
        else:
            xr = (dx - model.c0.value) / model.c1.value
            return xr

        if len(xr.shape) > 1:
            xr = xr[0, :]

        so = np.argsort(xr)
        f = np.interp(dx, xr[so], t0[so])

        f = np.broadcast_to(f, dx.shape)
        return f


class NIRCAMForwardRowGrismDispersion(_NIRCAMForwardGrismDispersion):
    """Forward grism dispersion model for NIRCAM (row-wise)."""

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        inv_lmodels=None,
        inv_xmodels=None,
        inv_ymodels=None,
        sampling=40,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
        lmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The forward dispersion polynomial models, one per order, such that
            wavelength = lmodel(t) computes the wavelength from the trace parameter.
        xmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`] or \
            list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the x-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dx = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
            Legacy calibrations of the trace did not encode the x0, y0 dependence;
            models of the form dx = xmodel(t) were used instead, and are also supported here.
        ymodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`] or \
            list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            Not used for row-wise dispersion, since y is the cross-dispersion direction.
        inv_lmodels : list[:class:`astropy.modeling.core.Model`]
            Not used for the forward transform.
        inv_xmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The inverse dispersion polynomial models, one per order, such that
            t = inv_xmodel(dx) computes the trace parameter from the x-position.
            The inverse models are no longer used for newer calibrations because the field
            dependence of the trace shape is not easily invertible.
            The use of inverse models is still supported for use by legacy trace calibrations.
        inv_ymodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            Not used for row-wise dispersion, since y is the cross-dispersion direction.
        sampling : int, optional
            Number of sampling points in t to use; these will be linearly interpolated.
        """
        dispaxis = "row"
        name = "nircam_forward_row_grism_dispersion"
        super().__init__(
            dispaxis,
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            inv_xmodels=inv_xmodels,
            inv_ymodels=inv_ymodels,
            name=name,
            sampling=sampling,
        )


class NIRCAMForwardColumnGrismDispersion(_NIRCAMForwardGrismDispersion):
    """Forward grism dispersion model for NIRCAM (column-wise)."""

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        inv_lmodels=None,
        inv_xmodels=None,
        inv_ymodels=None,
        sampling=40,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
        lmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The forward dispersion polynomial models, one per order, such that
            wavelength = lmodel(t) computes the wavelength from the trace parameter.
        xmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`] or \
            list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            Not used for column-wise dispersion, since x is the cross-dispersion direction.
        ymodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`] or \
            list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the y-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dy = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner tuple corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
            Legacy calibrations of the trace did not encode the x0, y0 dependence;
            models of the form dy = ymodel(t) were used instead, and are also supported here.
        inv_lmodels : list[:class:`astropy.modeling.core.Model`]
            Not used for the forward transform.
        inv_xmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            Not used for column-wise dispersion, since x is the cross-dispersion direction.
        inv_ymodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The inverse dispersion polynomial models, one per order, such that
            t = inv_ymodel(dy) computes the trace parameter from the y-position.
            The inverse models are no longer used for newer calibrations because the field
            dependence of the trace shape is not easily invertible.
            The use of inverse models is still supported for use by legacy trace calibrations.
        sampling : int, optional
            Number of sampling points in t to use; these will be linearly interpolated.
        """
        dispaxis = "column"
        name = "nircam_forward_column_grism_dispersion"
        super().__init__(
            dispaxis,
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            inv_xmodels=inv_xmodels,
            inv_ymodels=inv_ymodels,
            name=name,
            sampling=sampling,
        )


class NIRCAMBackwardGrismDispersion(_BackwardGrismDispersionBase):
    """Calculate the dispersion extent of NIRCAM pixels."""

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        inv_lmodels=None,
        inv_xmodels=None,
        inv_ymodels=None,
        sampling=40,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
        lmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The forward dispersion polynomial models, one per order, such that
            wavelength = lmodel(t) computes the wavelength from the trace parameter.
            Only used if inv_lmodels is not set.
        xmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`] or \
            list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the x-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dx = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
            Legacy calibrations of the trace did not encode the x0, y0 dependence;
            models of the form dx = xmodel(t) were used instead, and are also supported here.
        ymodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`] or \
            list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the y-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dy = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
            Legacy calibrations of the trace did not encode the x0, y0 dependence;
            models of the form dy = ymodel(t) were used instead, and are also supported here.
        inv_lmodels : list[:class:`astropy.modeling.core.Model`]
            The inverse dispersion polynomial models, one per order,
            such that t = lmodel(wavelength) computes the trace parameter
            from the wavelength.
        inv_xmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            Not used for the backward transform.
        inv_ymodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            Not used for the backward transform.
        sampling : int, optional
            Number of sampling points in t to use; these will be linearly interpolated.
        """
        name = "nircam_backward_grism_dispersion"
        super().__init__(
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            inv_lmodels=inv_lmodels,
            name=name,
            sampling=sampling,
        )

    def evaluate(self, x, y, wavelength, order):
        """
        Transform from the direct image plane to the dispersed plane.

        Parameters
        ----------
        x, y : float
            Input x, y pixel(s). If a 2-D array, it is assumed that the model
            is being called on a grid where all wavelengths are the same along the first axis,
            and all the x,y coordinates are the same along the second axis. In this case,
            x0, y0, and wavelength must all have the same shape.
        wavelength : float
            Wavelength(s) in microns. If a 2-D array, it is assumed that the model
            is being called on a grid where all wavelengths are the same along the first axis,
            and all the x,y coordinates are the same along the second axis. In this case,
            x0, y0, and wavelength must all have the same shape.
        order : int
            Input spectral order

        Returns
        -------
        x, y : float or np.ndarray
            The x, y values in the dispersed plane.
        x0, y0 : float or np.ndarray
            Source object x-center, y-center. Same as input x, y.
        order : int
            Output spectral order, same as input
        """
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)
        wavelength = np.atleast_1d(wavelength)

        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        if (wavelength < 0).any():
            raise ValueError("Wavelength should be greater than zero")

        if not self.inv_lmodels:
            t = self.invdisp_interp(self.lmodels[iorder], x, y, wavelength)
        else:
            lmodel = self.inv_lmodels[iorder]
            t = _evaluate_transform_guess_form(lmodel, x=x, y=y, t=wavelength)
        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]

        dx = _evaluate_transform_guess_form(xmodel, x=x, y=y, t=t)
        dy = _evaluate_transform_guess_form(ymodel, x=x, y=y, t=t)

        return x + dx, y + dy, x, y, order

    def invdisp_interp(self, model, x0, y0, wavelength):
        """
        Make a polynomial fit to lmodel and interpolate to find the inverse dispersion.

        Parameters
        ----------
        model : tuple[:class:`astropy.modeling.polynomial.Polynomial2D`]
            The models encoding the x, y dependence of the trace model's
            polynomial coefficients.
        x0, y0 : float or np.ndarray
            Source object x-center, y-center. If a 2-D array, it is assumed that the model
            is being called on a grid where all wavelengths are the same along the first axis,
            and all the x,y coordinates are the same along the second axis. In this case,
            x0, y0, and wavelength must all have the same shape.
        wavelength : float or np.ndarray
            Wavelength(s) in microns. If a 2-D array, it is assumed that the model
            is being called on a grid where all wavelengths are the same along the first axis,
            and all the x,y coordinates are the same along the second axis. In this case,
            x0, y0, and wavelength must all have the same shape.

        Returns
        -------
        t_out : float
            The inverse dispersion value for the given wavelength
        """
        t0 = np.linspace(0.0, 1.0, int(self.sampling))

        if len(model) < 2:
            # Handle legacy versions of the trace model
            xr = _evaluate_transform_guess_form(model, x=x0, y=y0, t=t0)
            f = np.zeros_like(wavelength)
            for i, w in enumerate(wavelength):
                f[i] = np.interp(w, xr, t0)
            return f

        if x0.ndim == 2:
            # Assume we're calling this on a grid where all wavelengths are the same
            # in one dimension, and all the x,y coordinates are the same in the other dimension.
            x0 = x0[0].flatten()
            y0 = y0[0].flatten()
            wavelength = wavelength[:, 0].flatten()

        trace_function = partial(_poly_with_spatial_dependence, model=model)

        # Create a grid of t0, x0, and y0 values
        tt, yy = np.meshgrid(t0, y0, indexing="ij")
        xx = np.meshgrid(t0, x0, indexing="ij")[1]
        wave_grid = trace_function(tt, xx, yy)
        t_out = np.empty((len(wavelength), len(x0)))
        for i, w in enumerate(wavelength):
            # do a first order interpolation to find the t0 where residuals are minimized
            # at each x,y location
            resid = (wave_grid - w) ** 2
            t_out[i, :] = _find_min_with_linear_interpolation(resid, t0)

        if t_out.shape[0] == 1:
            t_out = t_out[0, :]
        return t_out


def _find_min_with_linear_interpolation(resid, t0):
    """
    Vectorize linear interpolation over the 0th axis to find the minimum value.

    Parameters
    ----------
    resid : np.ndarray
        The residuals to minimize along the 0th axis, shape (n_t, n_points)
    t0 : np.ndarray
        The t-values corresponding to the first axis of resid, shape (n_t,)

    Returns
    -------
    this_t : ndarray
        The t-values that minimize the residuals at each pixel, shape (n_points,)
    """
    min_ind = np.argmin(resid, axis=0, keepdims=True)[0]

    # When the residuals are minimized near t=0 or t=1, just use those values
    # instead of doing a linear interpolation
    this_t = np.empty(resid.shape[1], dtype=float)
    this_t[min_ind == 0] = 0.0
    this_t[min_ind == resid.shape[0] - 1] = 1.0

    # for all other indices, calculate the t value based on
    # linearly interpolating the derivative to guess where it should cross zero
    good = (min_ind > 0) & (min_ind < resid.shape[0] - 1)
    good_ind = np.expand_dims(min_ind[good], axis=0)
    resid_good = resid[:, good]
    grad_good = np.gradient(resid_good, axis=0)
    grad_left = np.take_along_axis(grad_good, good_ind - 1, axis=0)[0]
    grad_right = np.take_along_axis(grad_good, good_ind + 1, axis=0)[0]
    grad_center = np.take_along_axis(grad_good, good_ind, axis=0)[0]

    # if the gradient is positive, then the minimum is to the left
    # if the gradient is negative, then the minimum is to the right
    grad_right[grad_center < 0] = grad_center[grad_center < 0]
    grad_left[grad_center > 0] = grad_center[grad_center > 0]

    t_left = t0[good_ind - 1][0]
    t_right = t0[good_ind + 1][0]
    t_center = t0[good_ind][0]
    t_right[grad_center < 0] = t_center[grad_center < 0]
    t_left[grad_center > 0] = t_center[grad_center > 0]

    # given points (t_left, grad_left) and (t_right, grad_right),
    # find the x-intercept, which is the value of t where the gradient
    # is identically zero under the linear approximation
    m = (grad_right - grad_left) / (t_right - t_left)
    b = grad_right - m * t_right
    x_intercept = -b / m

    # make grad_center == 0 case exact
    x_intercept[grad_center == 0] = t_center[grad_center == 0]

    this_t[good] = x_intercept
    return this_t


class NIRISSBackwardGrismDispersion(_BackwardGrismDispersionBase):
    """Calculate the dispersion extent of NIRISS pixels."""

    def __init__(self, orders, lmodels=None, xmodels=None, ymodels=None, theta=0.0):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
        lmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The inverse dispersion polynomial models, one per order,
            such that t = lmodel(wavelength) computes the wavelength
            from the trace parameter.
        xmodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the x-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dx = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
        ymodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the y-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dy = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
        theta : float
            Angle [deg] - defines the NIRISS filter wheel position
        """
        self.theta = theta
        name = "niriss_backward_grism_dispersion"
        super().__init__(
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            name=name,
        )

    def evaluate(self, x, y, wavelength, order):
        """
        Transform from the direct image plane to the dispersed plane.

        Parameters
        ----------
        x, y : float or np.ndarray
            Input x, y location
        wavelength : float or np.ndarray
            Wavelength in angstroms
        order : int
            Input spectral order

        Returns
        -------
        x, y : float or np.ndarray
            The x, y values in the dispersed plane.
        x0, y0 : float or np.ndarray
            Source object x-center, y-center. Same as input x, y.
        order : int
            Output spectral order, same as input

        Notes
        -----
        There's spatial dependence for NIRISS so the forward transform
        depends on x,y as well as the filter wheel rotation. Theta is
        usu. taken to be the different between fwcpos_ref in the specwcs
        reference file and fwcpos from the input image.
        """
        wavelength = np.atleast_1d(wavelength)
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)
        if (wavelength < 0).any():
            raise ValueError("Wavelength should be greater than zero")
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        t = self.lmodels[iorder](wavelength)
        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]

        dx = _poly_with_spatial_dependence(t, x, y, xmodel)
        dy = _poly_with_spatial_dependence(t, x, y, ymodel)

        # rotate by theta
        if self.theta != 0.0:
            rotate = Rotation2D(self.theta)
            dx, dy = rotate(dx, dy)

        return x + dx, y + dy, x, y, order


class _WFSSForwardGrismDispersion(_ForwardGrismDispersionBase):
    def __init__(self, dispaxis, *args, **kwargs):
        self.dispaxis = dispaxis
        super().__init__(*args, **kwargs)
        if self.dispaxis == "row":
            self.alongdisp_models = self.xmodels
            self.acrossdisp_models = self.ymodels
        elif self.dispaxis == "column":
            self.alongdisp_models = self.ymodels
            self.acrossdisp_models = self.xmodels
        else:
            raise ValueError(f"Invalid dispaxis: {dispaxis}. Must be 'row' or 'column'.")

    def evaluate(self, x, y, x0, y0, order):
        """
        Transform from the dispersed plane into the direct image plane.

        This code is used for both NIRISS and MIRI WFSS.

        Parameters
        ----------
        x, y :  float or np.ndarray
            Input x, y location
        x0, y0 : float or np.ndarray
            Source object x-center, y-center
        order : int
            Input spectral order

        Returns
        -------
        x0, y0 : float or np.ndarray
            The x0, y0 values in the direct image
        lambda : float or np.ndarray
            Wavelength in angstroms
        order : int
            Output spectral order, same as input

        Notes
        -----
        There's spatial dependence for NIRISS as well as dependence on the
        filter wheel rotation during the exposure.
        """
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        # The next two lines are to get around the fact that
        # modeling.standard_broadcasting=False does not work.
        x00 = x0.flatten()[0]
        y00 = y0.flatten()[0]

        t = np.linspace(0, 1, self.sampling)  # sample t
        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]
        lmodel = self.lmodels[iorder]

        dx = _poly_with_spatial_dependence(t, x00, y00, xmodel)
        dy = _poly_with_spatial_dependence(t, x00, y00, ymodel)

        if self.theta != 0.0:
            rotate = Rotation2D(self.theta)
            dx, dy = rotate(dx, dy)

        if self.dispaxis == "row":
            alongdisp = dx
            mapping = Mapping((2, 3, 0, 2, 4))
        elif self.dispaxis == "column":
            alongdisp = dy
            mapping = Mapping((2, 3, 1, 3, 4))

        # make a lookup table for t as a function of dx
        so = np.argsort(alongdisp)
        tab = Tabular1D(alongdisp[so], t[so], bounds_error=False, fill_value=None)

        # wavelength model takes in x, x0.
        # it then subtracts them to get dx; that's what SubtractUfunc does
        # next it finds the t value for that dx from the lookup table, interpolating linearly
        # finally it applies the lmodel of t to get the wavelength
        dxr = astmath.SubtractUfunc()
        wavelength = dxr | tab | lmodel
        model = mapping | Const1D(x00) & Const1D(y00) & wavelength & Const1D(order)

        return model(x, y, x0, y0, order)  # returns x0, y0, lambda, order


class NIRISSForwardRowGrismDispersion(_WFSSForwardGrismDispersion):
    """
    Calculate the wavelengths of vertically dispersed NIRISS grism data.

    The dispersion polynomial is relative to the input x,y pixels
    in the direct image for a given wavelength.
    """

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        theta=0.0,
        sampling=10,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
        lmodels : list[:class:`astropy.modeling.core.Model`]
            The forward dispersion polynomial models, one per order,
            such that wavelength = lmodel(t) computes the trace parameter
            from the wavelength.
        xmodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the x-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dx = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
        ymodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the y-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dy = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
        theta : float
            Angle [deg] - defines the NIRISS filter wheel position
        sampling : int, optional
            Number of sampling points in t to use; these will be linearly interpolated.
        """
        self.theta = theta
        dispaxis = "row"
        name = "niriss_forward_row_grism_dispersion"
        super().__init__(
            dispaxis,
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            name=name,
            sampling=sampling,
        )


class NIRISSForwardColumnGrismDispersion(_WFSSForwardGrismDispersion):
    """
    Calculate the wavelengths for horizontally dispersed NIRISS grism data.

    The dispersion polynomial is relative to the input x,y pixels
    in the direct image for a given wavelength. The transform also requires
    FWCPOS from the image header, this is the filter wheel position
    in degrees.
    """

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        theta=None,
        sampling=10,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
        lmodels : list[:class:`astropy.modeling.core.Model`]
            The forward dispersion polynomial models, one per order,
            such that wavelength = lmodel(t) computes the trace parameter
            from the wavelength.
        xmodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the x-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dx = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
        ymodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the y-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dy = C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2).
            The outer list corresponds to the different spectral orders.
        theta : float
            Angle [deg] - defines the NIRISS filter wheel position
        sampling : int, optional
            Number of sampling points in t to use; these will be linearly interpolated.
        """
        self.theta = theta
        dispaxis = "column"
        name = "niriss_forward_column_grism_dispersion"
        super().__init__(
            dispaxis,
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            name=name,
            sampling=sampling,
        )


def _poly_with_spatial_dependence(t, x0, y0, model):
    """
    Evaluate a polynomial of any order with model coefficients that depend on x0, y0.

    Parameters
    ----------
    t : float or np.ndarray
        The trace parameter(s).
    x0, y0 : float or np.ndarray
        The x, y coordinates at which to evaluate the polynomial.
    model : list[:class:`astropy.modeling.polynomial.Polynomial2D`]
        The models encoding the x, y dependence of the polynomial coefficients.

    Returns
    -------
    float or np.ndarray
        The evaluated polynomial at the given x0, y0, and t.
    """
    return sum(c(x0, y0) * t**i for i, c in enumerate(model))


def _evaluate_transform_guess_form(model, x=None, y=None, t=None):
    """
    Evaluate the transform model at the given x, y, and t coordinates.

    If a list of models of length >1 is provided, it is assumed that the trace function
    is a polynomial of arbitrary order, where each model in the list represents
    a polynomial coefficient (0th order first) with spatial dependence on x, y.
    Therefore each model in the list should have two inputs (x, y).

    If a single model (or length-1 list) is provided,
    it is assumed to depend only on t, and the model is evaluated directly on t.

    Parameters
    ----------
    model : :class:`astropy.modeling.core.Model` or list[:class:`astropy.modeling.core.Model`]
        The transform model(s) to evaluate.
    x : float or np.ndarray
        The x coordinate(s) at which to evaluate the model.
    y : float or np.ndarray
        The y coordinate(s) at which to evaluate the model.
    t : float or np.ndarray
        The trace parameter(s) at which to evaluate the model.

    Returns
    -------
    float or np.ndarray
        The evaluated transform at the given x, y, and t coordinates.
        For typical use, this corresponds to wavelength values.
    """
    if isinstance(model, (ListNode, list, tuple)) and len(model) == 1:
        model = model[0]

    if isinstance(model, Model):
        # model that depends only on t
        # e.g. NIRCam dispx, NIRISS displ, invdispl
        ninputs = len(model.inputs)
        if ninputs != 1:
            raise ValueError(
                f"Received a transform with an unexpected number of inputs ({ninputs}); "
                "expected 1 input for models depending only on t, or 2 inputs per coefficient "
                "for models depending on x, y, and t."
            )
        return model(t)

    if isinstance(model, (ListNode, list, tuple)):
        # model with coefficients that depend on x, y
        # e.g. NIRCam dispy, displ, NIRISS dispx, dispy
        if any(not isinstance(m, Model) for m in model):
            raise TypeError(
                "Expected a model or list of models, but got a list containing non-model elements."
            )

        ninputs = len(model[0].inputs)
        if ninputs == 2:
            return _poly_with_spatial_dependence(t, x, y, model)

        raise ValueError(
            f"Received a transform with an unexpected number of inputs ({ninputs}); "
            "expected 1 input for models depending only on t, or 2 inputs per coefficient "
            "for models depending on x, y, and t."
        )
    raise TypeError(f"Expected a model or list of models, but got {type(model)}. ")


class MIRIWFSSBackwardDispersion(_BackwardGrismDispersionBase):
    """Calculate the dispersion extent of MIRI WFSS pixels."""

    def __init__(self, orders, lmodels=None, xmodels=None, ymodels=None):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
            For MIRI WFSS we only have order = 1, so the orders is expected to equal [1,]
        lmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The inverse dispersion polynomial trace models, such that t = lmodel(wavelength)
            computes the trace parameter from the wavelength.
        xmodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the x-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dx =
            C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2 + C3(x0,y0) * t^3.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2, C3).
            The outer list corresponds to the different spectral orders.
        ymodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the y-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dy =
            C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2 + C3(x0,y0) * t^3.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2, C3).
            The outer list corresponds to the different spectral orders.
        """
        name = "miri_wfss_backward_dispersion"
        super().__init__(
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            name=name,
        )

    def evaluate(self, x0, y0, wavelength, order):
        """
        Transform from the direct image plane to the dispersed plane.

        Parameters
        ----------
        x0, y0 : float or np.ndarray
            Input x, y location in the direct image
        wavelength : float or np.ndarray
            Wavelength in microns
        order : int
            Input spectral order

        Returns
        -------
        x, y : float or np.ndarray
            The x = (dx + x0), y = (dy + y0) values in the dispersed plane.
        x0, y0 : float or np.ndarray
            Source object x-center, y-center in the direct image.
        order : int
            Output spectral order, same as input
        """
        wavelength = np.atleast_1d(wavelength)
        x0 = np.atleast_1d(x0)
        y0 = np.atleast_1d(y0)

        if (wavelength < 0).any():
            raise ValueError("Wavelength should be greater than zero")
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err
        # t is trace normalization parameters (it has values of 0 to 1)
        t = self.lmodels[iorder](wavelength)

        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]

        dx = _poly_with_spatial_dependence(t, x0, y0, xmodel)
        dy = _poly_with_spatial_dependence(t, x0, y0, ymodel)

        return x0 + dx, y0 + dy, x0, y0, order


class MIRIWFSSForwardDispersion(_WFSSForwardGrismDispersion):
    """
    Calculate the wavelengths of the dispersed MIRI WFSS data.

    The dispersion polynomial is relative to the input x,y pixels
    in the direct image for a given wavelength. This transform uses
    a generic method for both MIRI and NIRISS. For MIRI the theta
    parameter = 0,
    """

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        theta=None,
        sampling=10,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list[int]
            List of spectral orders corresponding to the dispersion models
            given by the `lmodels`, `xmodels`, and `ymodels` parameters.
            For MIRI WFSS we only have order = 1, so the orders is expected to equal [1,]
        lmodels : list[:class:`astropy.modeling.polynomial.Polynomial1D`]
            The forward dispersion polynomial model, such that wavelength = lmodel(t)
            computes the wavelength from the trace parameter.
        xmodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the x-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dx =
            C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2 + C3(x0,y0) * t^3.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2, C3).
            The outer list corresponds to the different spectral orders.
        ymodels : list[list[:class:`astropy.modeling.polynomial.Polynomial2D`]]
            The models encoding the y-position of the spectral trace.
            Because the shape of the trace depends on the direct-image x0, y0 position,
            this takes the form dy =
            C0(x0, y0) + C1(x0, y0) * t + C2(x0, y0) * t^2 + C3(x0,y0) * t^3.
            The inner list corresponds to the 2-D polynomials (C0, C1, C2, C3).
            The outer list corresponds to the different spectral orders.
        theta : float
            Set = 0 for MIRI.
        sampling : int, optional
            Number of sampling points in t to use; these will be linearly interpolated.
        """
        self.theta = 0.0
        dispaxis = "column"
        name = "miri_wfss_forward_dispersion"
        super().__init__(
            dispaxis,
            orders,
            lmodels=lmodels,
            xmodels=xmodels,
            ymodels=ymodels,
            name=name,
            sampling=sampling,
        )


class Rotation3DToGWA(Model):
    """
    Perform a 3D rotation given an angle in degrees.

    Positive angles represent a counter-clockwise rotation and vice-versa.
    """

    standard_broadcasting = False
    _separable = False

    separable = False

    n_inputs = 3
    n_outputs = 3

    angles = Parameter(getter=np.rad2deg, setter=np.deg2rad)

    def __init__(self, angles, axes_order, name=None):
        """
        Initialize the model.

        Parameters
        ----------
        angles : array-like
            Angles of rotation in deg in the order of axes_order.
        axes_order : str
            A sequence of 'x', 'y', 'z' corresponding to axis of rotation
        """
        if len(angles) != len(axes_order):
            raise InputParameterError("Number of angles must equal number of axes in axes_order.")

        self.axes = ["x", "y", "z"]
        unrecognized = set(axes_order).difference(self.axes)
        if unrecognized:
            raise ValueError(
                f"Unrecognized axis label {unrecognized}; should be one of {self.axes} "
            )
        self.axes_order = axes_order

        self._func_map = {"x": self._xrot, "y": self._yrot, "z": self._zrot}
        super(Rotation3DToGWA, self).__init__(angles, name=name)
        self.inputs = ("x", "y", "z")
        self.outputs = ("x", "y", "z")

    @property
    def inverse(self):
        """Inverse rotation."""
        angles = self.angles.value[::-1] * -1
        return self.__class__(angles, self.axes_order[::-1])

    def _xrot(self, x, y, z, theta):
        xout = x
        yout = y * np.cos(theta) + z * np.sin(theta)
        zout = np.sqrt(1 - xout**2 - yout**2)
        return [xout, yout, zout]

    def _yrot(self, x, y, z, theta):
        xout = x * np.cos(theta) - z * np.sin(theta)
        yout = y
        zout = np.sqrt(1 - xout**2 - yout**2)
        return [xout, yout, zout]

    def _zrot(self, x, y, z, theta):
        xout = x * np.cos(theta) + y * np.sin(theta)
        yout = -x * np.sin(theta) + y * np.cos(theta)
        zout = np.sqrt(1 - xout**2 - yout**2)
        return [xout, yout, zout]

    def evaluate(self, x, y, z, angles):
        """
        Apply the rotation to a set of 3D Cartesian coordinates.

        Parameters
        ----------
        x, y, z : array-like
            Cartesian coordinates
        angles : array-like
            Angles of rotation in deg in the order of axes_order.

        Returns
        -------
        x, y, z : array-like
            Rotated Cartesian coordinates
        """
        if x.shape != y.shape != z.shape:
            raise ValueError("Expected input arrays to have the same shape")

        #  Note: If the original shape was () (an array scalar) convert to a
        #  1-element 1-D array on output for consistency with most other models
        orig_shape = x.shape or (1,)
        for ang, ax in zip(angles[0], self.axes_order, strict=False):
            x, y, z = self._func_map[ax](x, y, z, theta=ang)
        x.shape = y.shape = z.shape = orig_shape

        return x, y, z


class Snell(Model):
    """Apply transforms, including Snell's law, through the NIRSpec prism."""

    standard_broadcasting = False
    _separable = False

    n_inputs = 4
    n_outputs = 3

    def __init__(self, angle, kcoef, lcoef, tcoef, tref, pref, temperature, pressure, name=None):
        """
        Initialize the model of the NIRSpec prism.

        Parameters
        ----------
        angle : float
            Prism angle in deg.
        kcoef : list
            K coefficients in Sellmeier equation.
        lcoef : list
            L coefficients in Sellmeier equation.
        tcoef : list
            Thermal coefficients of glass.
        tref : float
            Reference temperature in K.
        pref : float
            Reference pressure in ATM.
        temperature : float
            System temperature during observation in K
        pressure : float
            System pressure during observation in ATM.
        name : str, optional
            Name of the model
        """
        self.prism_angle = angle
        self.kcoef = np.array(kcoef, dtype=float)
        self.lcoef = np.array(lcoef, dtype=float)
        self.tcoef = np.array(tcoef, dtype=float)
        self.tref = tref
        self.pref = pref
        self.temp = temperature
        self.pressure = pref
        super(Snell, self).__init__(name=name)
        self.inputs = ("lam", "alpha_in", "beta_in", "zin")
        self.outputs = ("alpha_out", "beta_out", "zout")

    @staticmethod
    def compute_refraction_index(lam, temp, tref, pref, pressure, kcoef, lcoef, tcoef):
        """
        Calculate and return the refraction index.

        Use the simpler SellmeierGlass equation if the temperature difference
        is small (<20K), otherwise use the more complex SellmeierZemax equation.

        Parameters
        ----------
        lam : float or np.ndarray
            Wavelength in microns.
        temp : float
            System temperature during observation in K.
        tref : float
            Reference temperature in K.
        pref : float
            Reference pressure in ATM.
        pressure : float
            System pressure during observation in ATM.
        kcoef : list
            K coefficients in Sellmeier equation.
        lcoef : list
            L coefficients in Sellmeier equation.
        tcoef : list
            Thermal coefficients of glass.

        Returns
        -------
        n : float
            Refraction index.
        """
        delt = temp - tref
        if delt < 20:
            return SellmeierGlass.evaluate(lam * 1.0e6, B_coef=[kcoef], C_coef=[lcoef])
        else:
            return SellmeierZemax().evaluate(
                wavelength=lam * 1.0e6,
                temp=temp,
                ref_temp=tref,
                ref_pressure=pref,
                pressure=pressure,
                B_coef=[kcoef],
                C_coef=[lcoef],
                D_coef=[tcoef[:3]],
                E_coef=[tcoef[3:]],
            )

    def evaluate(self, lam, alpha_in, beta_in, zin):
        """
        Go through the prism, evaluating refraction and reflection of each surface.

        Parameters
        ----------
        lam : float or np.ndarray
            Wavelength.
        alpha_in, beta_in : float or np.ndarray
            Incident angles.
        zin : float or np.ndarray
            Incoming z coordinate. Not used for the calculation.

        Returns
        -------
        xout, yout, zout : float
            Outgoing x, y, z coordinates.
        """
        n = self.compute_refraction_index(
            lam, self.temp, self.tref, self.pref, self.pressure, self.kcoef, self.lcoef, self.tcoef
        )
        # Apply Snell's law through front surface, eq 5.3.3 II
        xout, yout, zout = Snell3D.evaluate(n, alpha_in, beta_in, zin)

        # Go to back surface frame # eq 5.3.3 III
        y_rotation = Rotation3DToGWA([self.prism_angle], "y")
        xout, yout, zout = y_rotation(xout, yout, zout)

        # Reflection on back surface
        xout = -1 * xout
        yout = -1 * yout

        # Back to front surface
        y_rotation = Rotation3DToGWA([-self.prism_angle], "y")
        xout, yout, zout = y_rotation(xout, yout, zout)

        # Snell's refraction law through front surface
        return Snell3D.evaluate(1.0 / n, xout, yout, zout)


class AngleFromGratingEquation(Model):
    """Solve the 3D Grating Dispersion Law for the refracted angle."""

    _separable = False
    n_inputs = 4
    n_outputs = 3

    groove_density = Parameter()
    """ Grating ruling density."""

    order = Parameter(default=-1)
    """ Spectral order."""

    def __init__(self, groove_density, order, **kwargs):
        """
        Initialize the model.

        Parameters
        ----------
        groove_density : float
            Grating ruling density.
        order : int
            Spectral order.
        **kwargs
            Additional keyword arguments to pass to Model base class.
        """
        super().__init__(groove_density=groove_density, order=order, **kwargs)
        self.inputs = ("lam", "alpha_in", "beta_in", "z")
        """ Wavelength and 3 angle coordinates going into the grating."""

        self.outputs = ("alpha_out", "beta_out", "zout")
        """ Three angles coming out of the grating. """

    def evaluate(self, lam, alpha_in, beta_in, z, groove_density, order):
        """
        Solve the 3D Grating Dispersion Law for the refracted angle.

        Parameters
        ----------
        lam : float
            The wavelength.
        alpha_in, beta_in : float or np.ndarray
            The 3-D incident angle(s).
        z : float or np.ndarray
            The incident z coordinate.
            Unused except to match the interface, but must have same shape as alpha_in and beta_in.
        groove_density : float
            The grating ruling density.
        order : int
            The spectral order.

        Returns
        -------
        x, y, z : float
            The refracted x,y, and z angles.
        """
        if alpha_in.shape != beta_in.shape != z.shape:
            raise ValueError("Expected input arrays to have the same shape")
        orig_shape = alpha_in.shape or (1,)
        xout = -alpha_in - groove_density * order * lam
        yout = -beta_in
        zout = np.sqrt(1 - xout**2 - yout**2)
        xout.shape = yout.shape = zout.shape = orig_shape
        return xout, yout, zout


class WavelengthFromGratingEquation(Model):
    """Solve the 3D Grating Dispersion Law for the wavelength."""

    _separable = False
    n_inputs = 3
    n_outputs = 1

    groove_density = Parameter()
    """ Grating ruling density."""
    order = Parameter(default=1)
    """ Spectral order."""

    def __init__(self, groove_density, order, **kwargs):
        """
        Initialize the model.

        Parameters
        ----------
        groove_density : int
            Grating ruling density.
        order : int
            Spectral order.
        **kwargs
            Additional keyword arguments to pass to Model base class.
        """
        super().__init__(groove_density=groove_density, order=order, **kwargs)
        self.inputs = ("alpha_in", "beta_in", "alpha_out")
        """
        three angle - alpha_in and beta_in going into the grating
        and alpha_out coming out of the grating."""
        self.outputs = ("lam",)
        """ Wavelength."""

    def evaluate(self, alpha_in, beta_in, alpha_out, groove_density, order):
        """
        Solve the 3D Grating Dispersion Law for the wavelength.

        Parameters
        ----------
        alpha_in : float
            The incident angle.
        beta_in : float
            Not used; see Notes.
        alpha_out : float
            The refracted angle.
        groove_density : float
            The grating ruling density.
        order : int
            The spectral order.

        Returns
        -------
        float
            The wavelength

        Notes
        -----
        beta_in is not used in this equation but is here because it's
        needed for the prism computation. Currently these two computations
        need to have the same interface.
        """
        return -(alpha_in + alpha_out) / (groove_density * order)


class Unitless2DirCos(Model):
    """Transform a vector to directional cosines."""

    _separable = False
    n_inputs = 2
    n_outputs = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inputs = ("x", "y")
        self.outputs = ("x", "y", "z")

    def evaluate(self, x, y):
        """
        Find the direction cosines of a vector of unit length specified by (x,y,1).

        Parameters
        ----------
        x : float or np.ndarray
            The vector x-component.
        y : float or np.ndarray
            The vector y-component.

        Returns
        -------
        cosa, cosb, cosc : float or np.ndarray
            The direction cosines alpha, beta, and gamma of the vector.
        """
        vabs = np.sqrt(1.0 + x**2 + y**2)
        cosa = x / vabs
        cosb = y / vabs
        cosc = 1.0 / vabs
        return cosa, cosb, cosc

    def inverse(self):
        return DirCos2Unitless()


class DirCos2Unitless(Model):
    """Transform directional cosines to vector."""

    _separable = False
    n_inputs = 3
    n_outputs = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inputs = ("x", "y", "z")
        self.outputs = ("x", "y")

    def evaluate(self, x, y, z):
        return x / z, y / z

    def inverse(self):
        return Unitless2DirCos()
