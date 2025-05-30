"""
Interpret JWST data quality flags.

The flags are binary-packed structures representing information about a given element
(a bit field): Each flag is assigned a bit position in a 32-bit mask.
If a given bit is set, the flag assigned to that bit is interpreted as being set or active.
"""

import warnings
from astropy.nddata.bitmask import interpret_bit_flags as ap_interpret_bit_flags
from stdatamodels.basic_utils import multiple_replace


__all__ = ["interpret_bit_flags", "dqflags_to_mnemonics"]


def interpret_bit_flags(bit_flags, flip_bits=None, mnemonic_map=None):
    """
    Convert input bit flags to a single integer value (bit mask) or `None`.

    .. deprecated:: 3.0
       Use `astropy.nddata.bitmask.interpret_bit_flags` instead.
       Note that the ``mnemonic_map`` parameter is named ``flag_name_map`` in the astropy version.
       Note also that the astropy version does not support whitespace between flags,
       e.g., "DO_NOT_USE+WARM" will work as expected, but "DO_NOT_USE + WARM" will not.

    Wraps `astropy.nddata.bitmask.interpret_bit_flags`, allowing the
    bit mnemonics to be used in place of integers.

    Parameters
    ----------
    bit_flags : int, str, list, None
        See `astropy.nddata.bitmask.interpret_bit_flags`.
        Also allows strings using Roman mnemonics

    flip_bits : bool, None
        See `astropy.nddata.bitmask.interpret_bit_flags`.

    mnemonic_map : dict
        Dictionary associating the mnemonic string to an integer value
        representing the set bit for that mnemonic.

    Returns
    -------
    bitmask : int or None
        Returns an integer bit mask formed from the input bit value or `None`
        if input ``bit_flags`` parameter is `None` or an empty string.
        If input string value was prepended with '~' (or ``flip_bits`` was set
        to `True`), then returned value will have its bits flipped
        (inverse mask).
    """
    warnings.warn(
        "The interpret_bit_flags function is deprecated and will be removed in a future version. "
        "Use astropy.nddata.bitmask.interpret_bit_flags instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if mnemonic_map is None:
        raise TypeError("`mnemonic_map` is a required argument")
    bit_flags_dm = bit_flags
    if isinstance(bit_flags, str):
        dm_flags = {key: str(val) for key, val in mnemonic_map.items()}
        bit_flags_dm = multiple_replace(bit_flags, dm_flags)

    return ap_interpret_bit_flags(bit_flags_dm, flip_bits=flip_bits)


def dqflags_to_mnemonics(dqflags, mnemonic_map):
    """
    Interpret value as bit flags and return the mnemonics.

    Parameters
    ----------
    dqflags : int-like
        The value to interpret as DQ flags

    mnemonic_map : dict
        Dictionary associating the mnemonic string to an integer value
        representing the set bit for that mnemonic.

    Returns
    -------
    mnemonics : set
        Set of mnemonics represented by the set bit flags

    Examples
    --------
    >>> pixel = {
    ...     "GOOD": 0,  # No bits set, all is good
    ...     "DO_NOT_USE": 2**0,  # Bad pixel. Do not use
    ...     "SATURATED": 2**1,  # Pixel saturated during exposure
    ...     "JUMP_DET": 2**2,  # Jump detected during exposure
    ... }

    >>> group = {
    ...     "GOOD": pixel["GOOD"],
    ...     "DO_NOT_USE": pixel["DO_NOT_USE"],
    ...     "SATURATED": pixel["SATURATED"],
    ... }

    >>> dqflags_to_mnemonics(1, pixel)
    {'DO_NOT_USE'}

    >>> dqflags_to_mnemonics(7, pixel)  # doctest: +SKIP
    {'JUMP_DET', 'DO_NOT_USE', 'SATURATED'}

    >>> dqflags_to_mnemonics(7, pixel) == {"JUMP_DET", "DO_NOT_USE", "SATURATED"}
    True

    >>> dqflags_to_mnemonics(1, mnemonic_map=pixel)
    {'DO_NOT_USE'}

    >>> dqflags_to_mnemonics(1, mnemonic_map=group)
    {'DO_NOT_USE'}
    """
    mnemonics = {mnemonic for mnemonic, value in mnemonic_map.items() if (dqflags & value)}
    return mnemonics
