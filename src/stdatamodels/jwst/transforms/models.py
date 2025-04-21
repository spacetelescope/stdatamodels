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

import numpy as np
from astropy.modeling.core import Model
from astropy.modeling.parameters import Parameter, InputParameterError
from astropy.modeling.models import Rotation2D, Mapping, Tabular1D, Const1D
from astropy.modeling.models import math as astmath
from ...properties import ListNode


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
    "V2V3ToIdeal",
    "IdealToV2V3",
    "RefractionIndexFromPrism",
    "Snell",
    "V23ToSky",
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
        order_bounding={},  # noqa: B006
        sky_centroid=None,
        partial_order={},  # noqa: B006
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
        sky_centroid : `~astropy.coordinates.SkyCoord`
            RA and Dec of the center of the object
        partial_order : bool
            True if the order is only partially contained on the image
        waverange : list
            Wavelength range for the order
        sky_bbox_ll : `~astropy.coordinates.SkyCoord`
            Lower left corner of the minimum bounding box
        sky_bbox_lr : `~astropy.coordinates.SkyCoord`
            Lower right corder of the minimum bounding box
        sky_bbox_ur : `~astropy.coordinates.SkyCoord`
            Upper right corner of the minimum bounding box
        sky_bbox_ul : `~astropy.coordinates.SkyCoord`
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
        beta : float
            The beta angle.
        beta_zero : float
            Beta coordinate of the center of slice 1 in the MIRI MRS.
        beta_del : float
            Slice width.
        channel : int
            MIRI MRS channel number. Valid values are 1, 2, 3, 4.

        Returns
        -------
        int
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
        alpha_in, beta_in : float
            Angle of incidence in radians.
        alpha_out : float
            Angle of emergence in radians.
        prism_angle : float
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
        List of models (`~astropy.modeling.core.Model`) corresponding to the
        list of slits.
    """

    _separable = False

    n_inputs = 4
    n_outputs = 4

    def __init__(self, slits, models):
        if np.iterable(slits[0]):
            self._slits = [tuple(s) for s in slits]
            self.slit_ids = [s[0] for s in self._slits]
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
        `~astropy.modeling.core.Model`
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
        x, y, z : float
            The three angle coordinates at the GWA going from detector to sky.

        Returns
        -------
        name : str
            Name of the slit.
        x_slit, y_slit : float
            The x and y coordinates within the virtual slit.
        lam : float
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
        List of models (`~astropy.modeling.core.Model`) corresponding to the
        list of slits.
    """

    _separable = False

    n_inputs = 4
    n_outputs = 4

    def __init__(self, slits, models):
        if isiterable(slits[0]):
            self._slits = [tuple(s) for s in slits]
            self.slit_ids = [s[0] for s in self._slits]
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
        if isiterable(self._slits[0]):
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
            List of models (`~astropy.modeling.core.Model`) corresponding to the
            list of slits.
        """
        super(Slit2MsaLegacy, self).__init__()
        self.inputs = ("name", "x_slit", "y_slit")
        """ Name of the slit, x and y coordinates within the virtual slit."""
        self.outputs = ("x_msa", "y_msa")
        """ x and y coordinates in the MSA frame."""
        if isiterable(slits[0]):
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
        if isiterable(self._slits[0]):
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
        `~astropy.modeling.core.Model`
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
            List of models (`~astropy.modeling.core.Model`) corresponding to the
            list of slits.
        """
        super(Slit2Msa, self).__init__()
        self.inputs = ("name", "x_slit", "y_slit")
        """ Name of the slit, x and y coordinates within the virtual slit."""
        self.outputs = ("x_msa", "y_msa", "name")
        """ x and y coordinates in the MSA frame."""
        if np.iterable(slits[0]):
            self._slits = [tuple(s) for s in slits]
            self.slit_ids = [s[0] for s in self._slits]
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
        `~astropy.modeling.core.Model`
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
        List of models (`~astropy.modeling.core.Model`) corresponding to the
        list of slits.
    """

    _separable = False

    n_inputs = 3
    n_outputs = 3

    def __init__(self, slits, models):
        super(Msa2Slit, self).__init__()
        self.inputs = ("name", "x_slit", "y_slit")
        """ Name of the slit, x and y coordinates within the virtual slit."""
        self.outputs = ("name", "x_msa", "y_msa")
        """ x and y coordinates in the MSA frame."""
        if isiterable(slits[0]):
            self._slits = [tuple(s) for s in slits]
            self.slit_ids = [s[0] for s in self._slits]
        else:
            self._slits = list(slits)
            self.slit_ids = self._slits
        self.models = models

    @property
    def slits(self):
        if isiterable(self._slits[0]):
            return [Slit(*row) for row in self._slits]
        else:
            return self.slit_ids

    def get_model(self, name):
        index = self.slit_ids.index(name)
        return self.models[index]

    def evaluate(self, name, x, y):
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
        models : list of `~astropy.modeling.core.Model`
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
        model : `~astropy.modeling.core.Model`
            Model for the given spectral order.
        """
        return self.models[spectral_order]

    def evaluate(self, x, y, spectral_order):
        """
        Compute the RA, Dec, and wavelength for a given pixel coordinate and spectral order.

        Parameters
        ----------
        x, y : float
            Pixel coordinates.
        spectral_order : int
            The input spectral order.

        Returns
        -------
        ra, dec : float
            RA and Dec coordinates.
        lam : float
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
        compareto : float, ndarray
            A number to compare to using the condition
            If ndarray then the input array, compareto and value should have the
            same shape.
        value : float, ndarray
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
        x : array-like
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


class NIRCAMForwardRowGrismDispersion(Model):
    """
    Return the transform from grism to image for the given spectral order.

    Notes
    -----
    The evaluation here is linear currently because higher orders have not yet been
    defined for NIRCAM (NIRCAM polynomials currently do not have any field
    dependence)
    """

    standard_broadcasting = False
    _separable = False
    fittable = False
    linear = False

    n_inputs = 5
    n_outputs = 4

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
        meta=None,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list [int]
            List of orders which are available
        lmodels : list [astropy.modeling.Model]
            List of models which govern the wavelength solutions
        xmodels : list [astropy.modeling.Model]
            List of models which govern the x solutions
        ymodels : list [astropy.modeling.Model]
            List of models which govern the y solutions
        inv_lmodels : list [astropy.modeling.Model]
            List of models which will be used if inverse lmodels cannot be analytically derived
        inv_xmodels : list [astropy.modeling.Model]
            List of models which will be used if inverse xmodels cannot be analytically derived
        inv_ymodels : list [astropy.modeling.Model]
            List of models which will be used if inverse ymodels cannot be analytically derived
        name : str, optional
            Name of the model
        meta : dict, optional
            Unused
        """
        self.orders = orders
        self.lmodels = lmodels
        self.xmodels = xmodels
        self.ymodels = ymodels
        self.inv_lmodels = inv_lmodels
        self.inv_xmodels = inv_xmodels
        self.inv_ymodels = inv_ymodels
        self._order_mapping = {int(k): v for v, k in enumerate(orders)}
        meta = {"orders": orders}  # informational for users
        if name is None:
            name = "nircam_forward_row_grism_dispersion"
        super(NIRCAMForwardRowGrismDispersion, self).__init__(name=name, meta=meta)
        self.inputs = ("x", "y", "x0", "y0", "order")
        self.outputs = ("x", "y", "wavelength", "order")

    def evaluate(self, x, y, x0, y0, order):
        """
        Transform from the grism plane to the image plane.

        Parameters
        ----------
        x, y :  int, float, list
            Input x, y location
        x0, y0 : int, float, list
            Source object x-center, y-center
        order : int
            Input spectral order

        Returns
        -------
        x0, y0 : float
            Coordinates of image plane x-center, y-center, same as input.
        l_poly : float
            Wavelength solution for the given spectral order.
        order : int
            The spectral order, same as input.
        """
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        if not self.inv_xmodels:
            t = self.invdisp_interp(iorder, x0, y0, (x - x0))
        else:
            t = self.inv_xmodels[iorder](x - x0)

        lmodel = self.lmodels[iorder]

        def apply_poly(coeff_model, inputs, t):
            # Determine order of polynomial in t
            ord_t = len(coeff_model)
            if ord_t == 1:
                if isinstance(coeff_model, (ListNode, list)):
                    sumval = coeff_model[0](t)
                else:
                    sumval = coeff_model(t)
            else:
                sumval = 0.0
                for i in range(ord_t):
                    sumval += t**i * coeff_model[i](*inputs[: coeff_model[i].n_inputs])
            return sumval

        l_poly = apply_poly(lmodel, (x0, y0), t)

        return x0, y0, l_poly, order

    def invdisp_interp(self, order, x0, y0, dx):
        """
        Make a polynomial fit to xmodel and interpolate to find the wavelength.

        Parameters
        ----------
        order : int
            The input spectral order
        x0, y0 : float
            Source object x-center, y-center.
        dx : float
            The offset from x0 in the dispersion direction

        Returns
        -------
        f : float
            The wavelength solution for the given dx
        """
        if len(dx.shape) == 2:
            dx = dx[0, :]

        t_len = dx.shape[0]
        t0 = np.linspace(0.0, 1.0, t_len)

        if isinstance(self.xmodels[order], (ListNode, list)):
            if len(self.xmodels[order]) == 2:
                xr = self.xmodels[order][0](x0, y0) + t0 * self.xmodels[order][1](x0, y0)
            elif len(self.xmodels[order]) == 3:
                xr = (
                    self.xmodels[order][0](x0, y0)
                    + t0 * self.xmodels[order][1](x0, y0)
                    + t0**2 * self.xmodels[order][2](x0, y0)
                )
            elif len(self.xmodels[order][0].inputs) == 1:
                xr = (dx - self.xmodels[order][0].c0.value) / self.xmodels[order][0].c1.value
                return xr
            else:
                raise Exception  # noqa: TRY002
        else:
            xr = (dx - self.xmodels[order].c0.value) / self.xmodels[order].c1.value
            return xr

        if len(xr.shape) > 1:
            xr = xr[0, :]

        so = np.argsort(xr)
        f = np.interp(dx, xr[so], t0[so])

        f = np.broadcast_to(f, dx.shape)
        return f


class NIRCAMForwardColumnGrismDispersion(Model):
    """
    Return the transform from grism to image for the given spectral order.

    Notes
    -----
    The evaluation here is linear because higher orders have not yet been
    defined for NIRCAM (NIRCAM polynomials currently do not have any field
    dependence)
    """

    standard_broadcasting = False
    _separable = False
    fittable = False
    linear = False

    n_inputs = 5
    n_outputs = 4

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
        meta=None,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list [int]
            List of orders which are available
        lmodels : list [astropy.modeling.Model]
            List of models which govern the wavelength solutions
        xmodels : list [astropy.modeling.Model]
            List of models which govern the x solutions
        ymodels : list [astropy.modeling.Model]
            List of models which govern the y solutions
        inv_lmodels : list [astropy.modeling.Model]
            List of models which will be used if inverse lmodels cannot be analytically derived
        inv_xmodels : list [astropy.modeling.Model]
            List of models which will be used if inverse xmodels cannot be analytically derived
        inv_ymodels : list [astropy.modeling.Model]
            List of models which will be used if inverse ymodels cannot be analytically derived
        name : str, optional
            Name of the model
        meta : dict, optional
            Unused
        """
        self.orders = orders
        self.lmodels = lmodels
        self.xmodels = xmodels
        self.ymodels = ymodels
        self.inv_lmodels = inv_lmodels
        self.inv_xmodels = inv_xmodels
        self.inv_ymodels = inv_ymodels
        self._order_mapping = {int(k): v for v, k in enumerate(orders)}
        meta = {"orders": orders}  # informational for users
        if name is None:
            name = "nircam_forward_column_grism_dispersion"
        super(NIRCAMForwardColumnGrismDispersion, self).__init__(name=name, meta=meta)
        self.inputs = ("x", "y", "x0", "y0", "order")
        self.outputs = ("x", "y", "wavelength", "order")

    def evaluate(self, x, y, x0, y0, order):
        """
        Transform from the grism plane to the image plane.

        Parameters
        ----------
        x, y :  int, float, list
            Input x, y location
        x0, y0 : int, float, list
            Source object x-center, y-center
        order : int
            Input spectral order

        Returns
        -------
        x0, y0 : float
            Coordinates of image plane x-center, y-center, same as input.
        l_poly : float
            Wavelength solution for the given spectral order.
        order : int
            The spectral order, same as input.
        """

        def apply_poly(coeff_model, inputs, t):
            # Determine order of polynomial in t
            ord_t = len(coeff_model)
            if ord_t == 1:
                if isinstance(coeff_model, (ListNode, list)):
                    sumval = coeff_model[0](t)
                else:
                    sumval = coeff_model(t)
            else:
                sumval = 0.0
                for i in range(ord_t):
                    sumval += t**i * coeff_model[i](*inputs[2 - coeff_model[i].n_inputs :])
            return sumval

        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        lmodel = self.lmodels[iorder]

        if not self.inv_ymodels:
            t = self.invdisp_interp(self.ymodels, iorder, x0, y0, (y - y0))
        else:
            t = self.inv_ymodels[iorder](y - y0)

        l_poly = apply_poly(lmodel, (x0, y0), t)

        return x0, y0, l_poly, order

    def invdisp_interp(self, model, order, x0, y0, dy):
        """
        Make a polynomial fit to ymodel and interpolate to find the wavelength.

        Parameters
        ----------
        model : astropy.modeling.Model
            The model governing the y-solutions, indexable by order.
        order : int
            The input spectral order
        x0, y0 : float
            Source object x-center, y-center.
        dy : float
            The offset from y0 in the dispersion direction

        Returns
        -------
        f : float
            The wavelength solution for the given dy
        """
        if len(dy.shape) == 2:
            dy = dy[0, :]

        t_len = dy.shape[0]
        t0 = np.linspace(0.0, 1.0, t_len)

        if isinstance(model, (ListNode, list)):
            if len(model[order]) == 2:
                xr = model[order][0](x0, y0) + t0 * model[order][1](x0, y0)
            elif len(model[order]) == 3:
                xr = (
                    model[order][0](x0, y0)
                    + t0 * model[order][1](x0, y0)
                    + t0**2 * model[order][2](x0, y0)
                )
            elif len(model[order][0].inputs) == 1:
                xr = (dy - model[order][0].c0.value) / model[order][0].c1.value
                return xr
            else:
                raise Exception  # noqa: TRY002
        else:
            xr = (dy - model[order].c0.value) / model[order].c1.value
            return xr

        if len(xr.shape) > 1:
            xr = xr[0, :]

        so = np.argsort(xr)
        f = np.interp(dy, xr[so], t0[so])

        f = np.broadcast_to(f, dy.shape)
        return f


class NIRCAMBackwardGrismDispersion(Model):
    """
    Calculate the dispersion extent of NIRCAM pixels.

    Notes
    -----
    The evaluation here is linear because higher orders have not yet been defined for NIRCAM
    (NIRCAM polynomials currently do not have any field dependence)
    """

    standard_broadcasting = False
    _separable = False
    fittable = False
    linear = False

    n_inputs = 4
    n_outputs = 5

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
        meta=None,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list [int]
            List of orders which are available
        lmodels : list [astropy.modeling.Model]
            List of models which govern the wavelength solutions
        xmodels : list [astropy.modeling.Model]
            List of models which govern the x solutions
        ymodels : list [astropy.modeling.Model]
            List of models which govern the y solutions
        inv_lmodels : list [astropy.modeling.Model]
            List of models which will be used if inverse lmodels
            cannot be analytically derived
        inv_xmodels : list [astropy.modeling.Model]
            List of models which will be used if inverse xmodels
            cannot be analytically derived
        inv_ymodels : list [astropy.modeling.Model]
            List of models which will be used if inverse ymodels
            cannot be analytically derived
        name : str, optional
            Name of the model
        meta : dict
            Unused
        """
        self._order_mapping = {int(k): v for v, k in enumerate(orders)}
        self.orders = orders
        self.lmodels = lmodels
        self.xmodels = xmodels
        self.ymodels = ymodels
        self.inv_lmodels = inv_lmodels
        self.inv_xmodels = inv_xmodels
        self.inv_ymodels = inv_ymodels
        meta = {"orders": orders}
        if name is None:
            name = "nircam_backward_grism_dispersion"
        super(NIRCAMBackwardGrismDispersion, self).__init__(name=name, meta=meta)
        self.inputs = ("x", "y", "wavelength", "order")
        self.outputs = ("x", "y", "x0", "y0", "order")

    def evaluate(self, x, y, wavelength, order):
        """
        Transform from the direct image plane to the dispersed plane.

        Parameters
        ----------
        x, y : float
            Input x, y pixel
        wavelength : float
            Wavelength in angstroms
        order : int
            Input spectral order

        Returns
        -------
        x, y : float
            The x, y values in the dispersed plane.
        x0, y0 : float
            Source object x-center, y-center. Same as input x, y.
        order : int
            Output spectral order, same as input
        """
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        if (wavelength < 0).any():
            raise ValueError("wavelength should be greater than zero")

        if not self.inv_lmodels:
            t = self.invdisp_interp(self.lmodels[iorder], x, y, wavelength)
        else:
            lmodel = self.inv_lmodels[iorder]
            t = assess_model(lmodel, x=x, y=y, t=wavelength)
        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]

        dx = assess_model(xmodel, x, y, t)
        dy = assess_model(ymodel, x, y, t)
        return x + dx, y + dy, x, y, order

    def invdisp_interp(self, model, x0, y0, wavelength):
        """
        Make a polynomial fit to lmodel and interpolate to find the inverse dispersion.

        Parameters
        ----------
        model : astropy.modeling.Model
            The model governing the wavelength solution for a given order
        x0, y0 : float
            Source object x-center, y-center.
        wavelength : float
            Wavelength in angstroms

        Returns
        -------
        f : float
            The inverse dispersion value for the given wavelength
        """
        t0 = np.linspace(0.0, 1.0, 40)
        t_re = np.reshape(t0, [len(t0), *map(int, np.ones_like(np.shape(x0)))])

        if len(model) == 2:
            xr = (np.ones_like(t_re) * model[0](x0, y0)) + (t_re * model[1](x0, y0))
        elif len(model) == 3:
            xr = (
                (np.ones_like(t_re) * model[0](x0, y0))
                + (t_re * model[1](x0, y0))
                + (t_re**2 * model[2](x0, y0))
            )
        else:
            if isinstance(model, (ListNode, list)):
                xr = model[0](t0)
            else:
                xr = model(t0)
            f = np.zeros_like(wavelength)
            for i, w in enumerate(wavelength):
                f[i] = np.interp(w, xr, t0)
            return f

        so = np.argsort(xr, axis=1)
        f = np.zeros_like(wavelength)
        for i, w in enumerate(wavelength):
            f[i] = np.interp(w, np.take_along_axis(xr, so, axis=1)[:, i], t0)
        return f


class NIRISSBackwardGrismDispersion(Model):
    """
    Calculate the dispersion extent of NIRISS pixels.

    Notes
    -----
    This model needs to be generalized, at the moment it satisfies the
    2t x 6(xy)th order polynomial currently used by NIRISS.
    """

    standard_broadcasting = False
    _separable = False
    fittable = False
    linear = False

    n_inputs = 4
    n_outputs = 5

    def __init__(
        self, orders, lmodels=None, xmodels=None, ymodels=None, theta=0.0, name=None, meta=None
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list
            The list of orders which are available to the model
        lmodels : list
            The list of models for the polynomial model in l
        xmodels : list[tuple]
            The list of tuple(models) for the polynomial model in x
        ymodels : list[tuple]
            The list of tuple(models) for the polynomial model in y
        theta : float
            Angle [deg] - defines the NIRISS filter wheel position
        name : str, optional
            Name of the model
        meta : dict
            Unused
        """
        self._order_mapping = {int(k): v for v, k in enumerate(orders)}
        self.xmodels = xmodels
        self.ymodels = ymodels
        self.lmodels = lmodels
        self.orders = orders
        self.theta = theta
        meta = {"orders": orders}
        if name is None:
            name = "niriss_backward_grism_dispersion"
        super(NIRISSBackwardGrismDispersion, self).__init__(name=name, meta=meta)
        self.inputs = ("x", "y", "wavelength", "order")
        self.outputs = ("x", "y", "x0", "y0", "order")

    def evaluate(self, x, y, wavelength, order):
        """
        Transform from the direct image plane to the dispersed plane.

        Parameters
        ----------
        x, y : float
            Input x, y location
        wavelength : float
            Wavelength in angstroms
        order : int
            Input spectral order

        Returns
        -------
        x, y : float
            The x, y values in the dispersed plane.
        x0, y0 : float
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
        if (wavelength < 0).any():
            raise ValueError("Wavelength should be greater than zero")
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        t = self.lmodels[iorder](wavelength)
        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]

        dx = xmodel[0](x, y) + t * xmodel[1](x, y) + t**2 * xmodel[2](x, y)
        dy = ymodel[0](x, y) + t * ymodel[1](x, y) + t**2 * ymodel[2](x, y)

        # rotate by theta
        if self.theta != 0.0:
            rotate = Rotation2D(self.theta)
            dx, dy = rotate(dx, dy)

        return x + dx, y + dy, x, y, order


class NIRISSForwardRowGrismDispersion(Model):
    """
    Calculate the wavelengths of vertically dispersed NIRISS grism data.

    The dispersion polynomial is relative to the input x,y pixels
    in the direct image for a given wavelength.

    Notes
    -----
    This model needs to be generalized, at the moment it satisfies the
    2t x 6(xy)th order polynomial currently used by NIRISS.
    """

    standard_broadcasting = False
    _separable = False
    fittable = False
    linear = False

    n_inputs = 5
    n_outputs = 4

    def __init__(
        self, orders, lmodels=None, xmodels=None, ymodels=None, theta=0.0, name=None, meta=None
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list
            The list of orders which are available to the model
        lmodels : list
            The list of models for the polynomial model in l
        xmodels : list[tuples]
            The list of tuple(models) for the polynomial model in x
        ymodels : list[tuples]
            The list of tuple(models) for the polynomial model in y
        theta : float
            Angle [deg] - defines the NIRISS filter wheel position
        name : str, optional
            Name of the model
        meta : dict
            Unused
        """
        self._order_mapping = {int(k): v for v, k in enumerate(orders)}
        self.xmodels = xmodels
        self.ymodels = ymodels
        self.lmodels = lmodels
        self.theta = theta
        self.orders = orders
        meta = {"orders": orders}
        if name is None:
            name = "niriss_forward_row_grism_dispersion"
        super(NIRISSForwardRowGrismDispersion, self).__init__(name=name, meta=meta)
        # starts with the backwards pixel and calculates the forward pixel
        self.inputs = ("x", "y", "x0", "y0", "order")
        self.outputs = ("x", "y", "wavelength", "order")

    def evaluate(self, x, y, x0, y0, order):
        """
        Transform from the dispersed plane into the direct image plane.

        Parameters
        ----------
        x, y :  int, float, list
            Input x, y location
        x0, y0 : int, float, list
            Source object x-center, y-center
        order : int
            Input spectral order

        Returns
        -------
        x, y : float
            The x, y values in the direct image, same as x0, y0.
        lambda : float
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

        t = np.linspace(0, 1, 10)  # sample t
        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]
        lmodel = self.lmodels[iorder]

        dx = xmodel[0](x00, y00) + t * xmodel[1](x00, y00) + t**2 * xmodel[2](x00, y00)
        dy = ymodel[0](x00, y00) + t * ymodel[1](x00, y00) + t**2 * ymodel[2](x00, y00)

        if self.theta != 0.0:
            rotate = Rotation2D(self.theta)
            dx, dy = rotate(dx, dy)

        so = np.argsort(dx)
        tab = Tabular1D(dx[so], t[so], bounds_error=False, fill_value=None)

        dxr = astmath.SubtractUfunc()
        wavelength = dxr | tab | lmodel
        model = Mapping((2, 3, 0, 2, 4)) | Const1D(x00) & Const1D(y00) & wavelength & Const1D(order)
        # returns x0, y0, lam, order
        return model(x, y, x0, y0, order)


class NIRISSForwardColumnGrismDispersion(Model):
    """
    Calculate the wavelengths for horizontally dispersed NIRISS grism data.

    The dispersion polynomial is relative to the input x,y pixels
    in the direct image for a given wavelength. The transform also requires
    FWCPOS from the image header, this is the filter wheel position
    in degrees.
    """

    standard_broadcasting = False
    _separable = False
    fittable = False
    linear = False

    n_inputs = 5
    n_outputs = 4

    def __init__(
        self,
        orders,
        lmodels=None,
        xmodels=None,
        ymodels=None,
        theta=None,
        name=None,
        meta=None,
    ):
        """
        Initialize the model.

        Parameters
        ----------
        orders : list
            The list of orders which are available to the model.
        lmodels : list
            The list of models for the polynomial model in wavelength.
        xmodels : list[tuple]
            The list of tuple(models) for the polynomial model in x
        ymodels : list[tuple]
            The list of tuple(models) for the polynomial model in y
        theta : float
            Angle [deg] - defines the NIRISS filter wheel position
        name : str
            The name of the model
        meta : dict
            Unused.
        """
        self._order_mapping = {int(k): v for v, k in enumerate(orders)}
        self.xmodels = xmodels
        self.ymodels = ymodels
        self.lmodels = lmodels
        self.orders = orders
        self.theta = theta
        meta = {"orders": orders}
        if name is None:
            name = "niriss_forward_column_grism_dispersion"
        super(NIRISSForwardColumnGrismDispersion, self).__init__(name=name, meta=meta)
        # starts with the backwards pixel and calculates the forward pixel
        self.inputs = ("x", "y", "x0", "y0", "order")
        self.outputs = ("x", "y", "wavelength", "order")

    def evaluate(self, x, y, x0, y0, order):
        """
        Transform from the dispersed plane into the direct image plane.

        Parameters
        ----------
        x, y :  int, float
            Input x,y location
        x0, y0 : int, float
            Source object x-center, y-center
        order : int
            Input spectral order

        Returns
        -------
        x, y : float
            The x, y values in the direct image, same as x0, y0.
        lambda : float
            Wavelength in angstroms
        order : int
            Output spectral order, same as input.

        Notes
        -----
        There's spatial dependence for NIRISS as well as rotation for the filter wheel
        """
        try:
            iorder = self._order_mapping[int(order.flatten()[0])]
        except KeyError as err:
            raise ValueError("Specified order is not available") from err

        # The next two lines are to get around the fact that
        # modeling.standard_broadcasting=False does not work.
        x00 = x0.flatten()[0]
        y00 = y0.flatten()[0]

        t = np.linspace(0, 1, 10)
        xmodel = self.xmodels[iorder]
        ymodel = self.ymodels[iorder]
        lmodel = self.lmodels[iorder]
        dx = xmodel[0](x00, y00) + t * xmodel[1](x00, y00) + t**2 * xmodel[2](x00, y00)
        dy = ymodel[0](x00, y00) + t * ymodel[1](x00, y00) + t**2 * ymodel[2](x00, y00)

        if self.theta != 0.0:
            rotate = Rotation2D(self.theta)
            dx, dy = rotate(dx, dy)
        so = np.argsort(dy)
        tab = Tabular1D(dy[so], t[so], bounds_error=False, fill_value=None)
        dyr = astmath.SubtractUfunc()
        wavelength = dyr | tab | lmodel
        model = Mapping((2, 3, 1, 3, 4)) | Const1D(x00) & Const1D(y00) & wavelength & Const1D(order)
        return model(x, y, x0, y0, order)


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

        Parameters
        ----------
        lam : float
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
        # Convert to microns
        lam = np.asarray(lam * 1e6)
        KtoC = 273.15  # kelvin to celsius conversion  # noqa: N806
        temp -= KtoC
        tref -= KtoC
        delt = temp - tref

        K1, K2, K3 = kcoef  # noqa: N806
        L1, L2, L3 = lcoef  # noqa: N806
        D0, D1, D2, E0, E1, lam_tk = tcoef  # noqa: N806

        if delt < 20:
            n = np.sqrt(
                1.0
                + K1 * lam**2 / (lam**2 - L1)
                + K2 * lam**2 / (lam**2 - L2)
                + K3 * lam**2 / (lam**2 - L3)
            )
        else:
            # Derive the refractive index of air at the reference temperature and pressure
            # and at the operational system's temperature and pressure.
            nref = (
                1.0
                + (
                    6432.8
                    + 2949810.0 * lam**2 / (146.0 * lam**2 - 1.0)
                    + (5540.0 * lam**2) / (41.0 * lam**2 - 1.0)
                )
                * 1e-8
            )

            # T should be in C, P should be in ATM
            nair_obs = 1.0 + ((nref - 1.0) * pressure) / (1.0 + (temp - 15.0) * 3.4785e-3)
            nair_ref = 1.0 + ((nref - 1.0) * pref) / (1.0 + (tref - 15) * 3.4785e-3)

            # Compute the relative index of the glass at Tref and Pref using Sellmeier equation I.
            lamrel = lam * nair_obs / nair_ref

            nrel = np.sqrt(
                1.0
                + K1 * lamrel**2 / (lamrel**2 - L1)
                + K2 * lamrel**2 / (lamrel**2 - L2)
                + K3 * lamrel**2 / (lamrel**2 - L3)
            )
            # Convert the relative index of refraction at the reference temperature and pressure
            # to absolute.
            nabs_ref = nrel * nair_ref

            # Compute the absolute index of the glass
            delnabs = (0.5 * (nrel**2 - 1.0) / nrel) * (
                D0 * delt
                + D1 * delt**2
                + D2 * delt**3
                + (E0 * delt + E1 * delt**2) / (lamrel**2 - lam_tk**2)
            )
            nabs_obs = nabs_ref + delnabs

            # Define the relative index at the system's operating T and P.
            n = nabs_obs / nair_obs
        return n

    def evaluate(self, lam, alpha_in, beta_in, zin):
        """
        Go through the prism, evaluating refraction and reflection of each surface.

        Parameters
        ----------
        lam : float
            Wavelength.
        alpha_in, beta_in : float
            Incident angles.
        zin : float
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
        xout = alpha_in / n
        yout = beta_in / n
        zout = np.sqrt(1.0 - xout**2 - yout**2)

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
        xout = xout * n
        yout = yout * n
        zout = np.sqrt(1.0 - xout**2 - yout**2)
        return xout, yout, zout


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
        alpha_in, beta_in : float
            The incident angle.
        z : float
            Unused except to match the interface.
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


class Rotation3D(Model):
    """
    Perform a series of rotations about different axis in 3D space.

    Positive angles represent a counter-clockwise rotation.
    """

    standard_broadcasting = False
    _separable = False

    n_inputs = 3
    n_outputs = 3

    angles = Parameter(getter=np.rad2deg, setter=np.deg2rad)

    def __init__(self, angles, axes_order, name=None):
        """
        Initialize the 3D rotation model.

        Parameters
        ----------
        angles : list
            A sequence of angles (in deg).
            The angles are [-V2_REF, V3_REF, -ROLL_REF, -DEC_REF, RA_REF].
        axes_order : str
            A sequence of characters ('x', 'y', or 'z') corresponding to the
            axis of rotation and matching the order in ``angles``.
            The axes are "zyxyz".
        name : str, optional
            The name of the transform
        """
        self.axes = ["x", "y", "z"]
        unrecognized = set(axes_order).difference(self.axes)
        if unrecognized:
            raise ValueError(
                f"Unrecognized axis label {unrecognized}; should be one of {self.axes} "
            )
        self.axes_order = axes_order
        if len(angles) != len(axes_order):
            raise ValueError(
                f"The number of angles {len(angles)} should match the number \
                              of axes {len(axes_order)}."
            )
        super(Rotation3D, self).__init__(angles, name=name)
        self.inputs = ("x", "y", "z")
        self.outputs = ("x", "y", "z")

    @property
    def inverse(self):
        """Inverse rotation."""
        angles = self.angles.value[::-1] * -1
        return self.__class__(angles, axes_order=self.axes_order[::-1])

    @staticmethod
    def _compute_matrix(angles, axes_order):
        if len(angles) != len(axes_order):
            raise InputParameterError("Number of angles must equal number of axes in axes_order.")
        matrices = []
        for angle, axis in zip(angles, axes_order, strict=False):
            matrix = np.zeros((3, 3), dtype=float)
            if axis == "x":
                mat = Rotation3D.rotation_matrix_from_angle(angle)
                matrix[0, 0] = 1
                matrix[1:, 1:] = mat
            elif axis == "y":
                mat = Rotation3D.rotation_matrix_from_angle(-angle)
                matrix[1, 1] = 1
                matrix[0, 0] = mat[0, 0]
                matrix[0, 2] = mat[0, 1]
                matrix[2, 0] = mat[1, 0]
                matrix[2, 2] = mat[1, 1]
            elif axis == "z":
                mat = Rotation3D.rotation_matrix_from_angle(angle)
                matrix[2, 2] = 1
                matrix[:2, :2] = mat
            else:
                raise ValueError(
                    f"""Expected axes_order to be a combination
                                 of characters 'x', 'y' and 'z',
                                 got {set(axes_order).difference(["x", "y", "z"])}"""
                )
            matrices.append(matrix)
        if len(angles) == 1:
            return matrix
        elif len(matrices) == 2:
            return np.dot(matrices[1], matrices[0])
        else:
            prod = np.dot(matrices[1], matrices[0])
            for m in matrices[2:]:
                prod = np.dot(m, prod)
            return prod

    @staticmethod
    def rotation_matrix_from_angle(angle):
        """
        Clockwise rotation matrix.

        Parameters
        ----------
        angle : float
            Angle in radians.

        Returns
        -------
        np.ndarray
            Rotation matrix.
        """
        return np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])

    def evaluate(self, x, y, z, angles):
        """
        Apply the rotation to a set of 3D Cartesian coordinates.

        Parameters
        ----------
        x, y, z : float
            Cartesian coordinates.
        angles : list
            A sequence of angles (in deg).
            The angles are [-V2_REF, V3_REF, -ROLL_REF, -DEC_REF, RA_REF].

        Returns
        -------
        x, y, z : float
            Rotated Cartesian coordinates.
        """
        if x.shape != y.shape != z.shape:
            raise ValueError("Expected input arrays to have the same shape")
        # Note: If the original shape was () (an array scalar) convert to a
        # 1-element 1-D array on output for consistency with most other models
        orig_shape = x.shape or (1,)
        inarr = np.array([x.flatten(), y.flatten(), z.flatten()])
        result = np.dot(self._compute_matrix(angles[0], self.axes_order), inarr)
        x, y, z = result[0], result[1], result[2]
        x.shape = y.shape = z.shape = orig_shape
        return x, y, z


class V23ToSky(Rotation3D):
    """Transform from V2V3 to a standard coordinate system (ICRS)."""

    _separable = False

    n_inputs = 2
    n_outputs = 2

    def __init__(self, angles, axes_order, name=None):
        """
        Initialize the transform from V2V3 to ICRS.

        Parameters
        ----------
        angles : list
            A sequence of angles (in deg).
            The angles are [-V2_REF, V3_REF, -ROLL_REF, -DEC_REF, RA_REF].
        axes_order : str
            A sequence of characters ('x', 'y', or 'z') corresponding to the
            axis of rotation and matching the order in ``angles``.
            The axes are "zyxyz".
        name : str, optional
            The name of the transform
        """
        super(V23ToSky, self).__init__(angles, axes_order=axes_order, name=name)
        self._inputs = ("v2", "v3")
        """ ("v2", "v3"): Coordinates in the (V2, V3) telescope frame."""
        self._outputs = ("ra", "dec")
        """ ("ra", "dec"): RA, DEC coordinates in ICRS."""

    @property
    def inputs(self):  # noqa: D102
        return self._inputs

    @inputs.setter
    def inputs(self, val):
        self._inputs = val

    @property
    def outputs(self):  # noqa: D102
        return self._outputs

    @outputs.setter
    def outputs(self, val):
        self._outputs = val

    @staticmethod
    def spherical2cartesian(alpha, delta):
        """
        Convert spherical coordinates (in deg) to cartesian.

        Parameters
        ----------
        alpha, delta : float
            Spherical coordinates in deg.

        Returns
        -------
        x, y, z : float
            Cartesian coordinates
        """
        alpha = np.deg2rad(alpha)
        delta = np.deg2rad(delta)
        x = np.cos(alpha) * np.cos(delta)
        y = np.cos(delta) * np.sin(alpha)
        z = np.sin(delta)
        return np.array([x, y, z])

    @staticmethod
    def cartesian2spherical(x, y, z):
        """
        Convert cartesian coordinates to spherical coordinates (in deg).

        Parameters
        ----------
        x, y, z : float
            Cartesian coordinates.

        Returns
        -------
        alpha, delta : float
            Spherical coordinates in deg.
        """
        h = np.hypot(x, y)
        alpha = np.rad2deg(np.arctan2(y, x))
        delta = np.rad2deg(np.arctan2(z, h))
        return alpha, delta

    def evaluate(self, v2, v3, angles):
        """
        Apply the rotation to a set of spherical coordinates.

        Parameters
        ----------
        v2, v3 : float
            V2, V3 coordinates in deg.
        angles : list
            A sequence of angles (in deg).
            The angles are [-V2_REF, V3_REF, -ROLL_REF, -DEC_REF, RA_REF].

        Returns
        -------
        ra, dec : float
            ICRS coordinates in deg.
        """
        x, y, z = self.spherical2cartesian(v2, v3)
        x1, y1, z1 = super(V23ToSky, self).evaluate(x, y, z, angles)
        ra, dec = self.cartesian2spherical(x1, y1, z1)

        return ra, dec

    def __call__(self, v2, v3, **kwargs):
        """Override default call to efficiently iterate over an array."""
        from itertools import chain

        inputs, format_info = self.prepare_inputs(v2, v3)
        parameters = self._param_sets(raw=True)

        outputs = self.evaluate(*chain(inputs, parameters))
        if self.n_outputs == 1:
            outputs = (outputs,)

        return self.prepare_outputs(format_info, *outputs)


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
        x : float
            The vector x-component.
        y : float
            The vector y-component.

        Returns
        -------
        cosa, cosb, cosc : float
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


def assess_model(model, x=0, y=0, t=0):
    if isinstance(model, (ListNode, list)):
        ninputs = len(model[0].inputs)
        if ninputs == 2:
            output = model[0](x, y) + t * model[1](x, y) + t**2 * model[2](x, y)
        elif ninputs == 1:
            if len(model) == 1:
                output = model[0](t)
            elif len(model) == 2:
                output = model[0](x) + t * model[1](x)
        else:
            raise ValueError(f"{model} has incorrect number of inputs required.")
    else:
        ninputs = len(model.inputs)
        if ninputs == 2:
            output = model(x, y)
        elif ninputs == 1:
            output = model(t)
        else:
            raise ValueError(f"{model} has incorrect number of inputs required.")
    return output
