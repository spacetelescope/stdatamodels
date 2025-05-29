from pathlib import Path


def check(init):
    """
    Determine the type of a file and return it as a string.

    Parameters
    ----------
    init : str or Path
        The input file path.

    Returns
    -------
    file_type : str
        A string representing the file type ("asdf", "asn", or "fits")
    """
    if isinstance(init, str):
        init = Path(init)
    if not isinstance(init, Path):
        raise TypeError(f"Input must be a str or Path, not {type(init)}")

    # Could be the file is zipped; consider last 2 suffixes
    suffixes = init.suffixes[-2:]
    if not suffixes:
        raise ValueError(f"Input file path does not have an extension: {init}")

    for suffix in suffixes[::-1]:
        ext = suffix.strip(".")
        if ext in ["asdf", "fits"]:
            return ext
        if ext == "json":
            return "asn"
    raise ValueError(f"Unrecognized file type for: {init}")
