"""
allOf exists in weird places
schema_editor says that "standard" and "misc" keyword_name is ignored (for create_dict)
schema_editor ignores all non PRIMARY and SCI fits_hdu (for create_dict)

keyword_dict is:
    key : FITS_KEYWORD (not hdu as it's only PRIMARY or SCI)
    path : in keyword dictionary

keyword_schema is some weird combination of everything in
the keyword dictionary as one sort of but not quite a schema.

Since these aren't schemas the usual tools won't work.
- Start with a "top" schema
- Traverse (keeping track of path, ignore combiners, properties, etc)
- When we hit 'fits_keyword'...
   - sort out the path (removing properties, combiners, etc)
   - sort out 'fits_hdu'
   - title, description, type, units...
This follows the behavior of ``keyword_dict.py`` used by SDP, archive, etc.
"""

from pathlib import Path
import json


__all__ = ["load"]


def _load_kwd_schema(path):
    with open(path) as f:
        return json.load(f)


def _sanitize_path(path):
    return tuple([sub for sub in path if sub not in ("allOf", "properties")])


def _walk_kwd(kwd_path, root, path=None, keywords=None):
    if keywords is None:
        keywords = []
    if path is None:
        path = tuple()
    if not isinstance(root, (dict, list)):
        if not isinstance(root, (int, float, str)):
            raise ValueError(f"Unknown type {type(root)} in keyword dictionary")
        return root
    if isinstance(root, list):
        # ignoring list item index path
        return [_walk_kwd(kwd_path, sub, path, keywords) for sub in root]
    if "$ref" in root:
        assert len(root) == 1
        return _walk_kwd(kwd_path, _load_kwd_schema(kwd_path / root["$ref"]), path, keywords)
    if "fits_keyword" in root:
        assert "fits_hdu" in root
        return keywords.append((_sanitize_path(path), root))
    for key, sub in root.items():
        _walk_kwd(kwd_path, sub, path + (key, ), keywords)


def load(path):
    kwd_path = Path(path)

    # start at each "top" schema
    top_schema_files = list(kwd_path.glob("top*.json"))
    if not top_schema_files:
        raise ValueError("Failed to find any top schema files")

    keyword_infos_per_mode = {}
    for top_schema_file in top_schema_files:
        schema = _load_kwd_schema(top_schema_file)
        mode = '.'.join(top_schema_file.name.split('.')[1:3])
        keyword_infos_per_mode[mode] = []
        _walk_kwd(kwd_path, schema, keywords=keyword_infos_per_mode[mode])

    # consolidate results organizing them by fits_hdu and fits_keyword
    kwd = {}
    for mode, keyword_infos in keyword_infos_per_mode.items():
        for keyword_info in keyword_infos:
            path, keyword = keyword_info
            key = (keyword["fits_hdu"], keyword["fits_keyword"])
            if key not in kwd:
                kwd[key] = []
            kwd[key].append({
                "scope": mode,
                "path": path,
                "keyword": keyword,
            })
    return kwd
