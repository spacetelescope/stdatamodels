"""
Interpret JWST data quality flags.

The flags are binary-packed structures representing information about a given element
(a bit field): Each flag is assigned a bit position in a 32-bit mask.
If a given bit is set, the flag assigned to that bit is interpreted as being set or active.
"""

__all__ = ["dqflags_to_mnemonics"]


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
