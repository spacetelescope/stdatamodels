import asdf

import stdatamodels.jwst.datamodels as dm
import stdatamodels.schema


__all__ = ["load"]


def _get_subclasses(klass, skip_models=None):
    if skip_models is None:
        skip_models = set()
    for subclass in klass.__subclasses__():
        if subclass in skip_models:
            continue
        yield subclass
        yield from _get_subclasses(subclass, skip_models)


def _get_schema_keywords_callback(ss, path, combiner, ctx, r):
    if isinstance(ss, dict) and "fits_keyword" in ss:
        ctx.append((path, ss))


def load(skip_models=None):
    datamodel_classes = list(_get_subclasses(dm.JwstDataModel, skip_models))

    keywords_by_datamodel = {}
    for klass in datamodel_classes:
        keywords = []
        if klass.schema_url:
            schema = asdf.schema.load_schema(klass.schema_url, resolve_references=True)
            stdatamodels.schema.walk_schema(schema, _get_schema_keywords_callback, keywords)
        class_path = ".".join([klass.__module__, klass.__name__])
        keywords_by_datamodel[class_path] = keywords

    # consolidate results organizing them by fits_hdu and fits_keyword
    dmd = {}
    for klass, keyword_infos in keywords_by_datamodel.items():
        for keyword_info in keyword_infos:
            path, keyword = keyword_info
            fits_keyword = keyword["fits_keyword"]
            fits_hdu = keyword.get("fits_hdu", "PRIMARY")

            # the schemas sometimes use lowercase
            key = (fits_hdu.upper(), fits_keyword.upper())
            if key not in dmd:
                dmd[key] = []
            dmd[key].append(
                {
                    "scope": klass,
                    "path": path,
                    "keyword": keyword,
                }
            )
    return dmd
