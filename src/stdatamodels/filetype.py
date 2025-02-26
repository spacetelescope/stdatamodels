from pathlib import Path


def check(init):
    """
    Determine the type of a file and return it as a string

    Parameters
    ----------

    init : file path or file object

    Returns
    -------
    file_type: a string with the file type ("asdf", "asn", or "fits")

    """
    if isinstance(init, str):
        path = Path(init)

        # Could be the file is zipped; consider last 2 suffixes
        suffixes = path.suffixes[-2:]
        if not suffixes:
            raise ValueError(f"Input file path does not have an extension: {init}")

        for suffix in suffixes[::-1]:
            ext = suffix.strip(".")
            if ext in ["asdf", "fits"]:
                return ext
            if ext == "json":
                return "asn"
        raise ValueError(f"Unrecognized file type for: {init}")

    if hasattr(init, "read") and hasattr(init, "seek"):
        magic = init.read(5)
        init.seek(0, 0)

        if not magic or len(magic) < 5:
            raise ValueError(f"Cannot get file type of {str(init)}")

        if magic == b"#ASDF":
            return "asdf"

        if magic == b"SIMPL":
            return "fits"

        return "asn"

    raise ValueError(f"Cannot get file type of {str(init)}")
