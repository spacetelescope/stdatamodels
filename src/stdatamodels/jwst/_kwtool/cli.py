from pprint import pformat

from .compare import compare_keywords


def _make_template(tag):
    return f"<{tag}>" + "{0}" + f"</{tag}>"


def _render(tag, txt):
    return _make_template(tag).format(txt)


R = _render


def _keyword_to_str(k):
    hdu, kw = k
    return f"HDU: {hdu} KEYWORD: {kw}"


def _entry_to_str(entry):
    return R(
        "div",
        R(
            "dl",
            R("dt", "path") + R("dd", entry["path"]) +
            R("dt", "scope") + R("dd", entry["scope"]) +
            R("dt", "keyword") + R("dd", R("pre", R("code", pformat(entry["keyword"], indent=2)))),
        ),
    )


def _keyword_details(kwd, dmd, k):
    s = ""
    for d, h in [(kwd, "Keyword Dictionary"), (dmd, "Datamodel Schemas")]:
        s += R("h3", h)
        if k not in d:
            s += "Missing"
        else:
            ss = ""
            for entry in d[k]:
                ss += R("li", _entry_to_str(entry))
            s += R("ul", ss)
    return s


def _def_diff_details(d):
    s = ""
    for diff_name, diff in d.items():
        f = pformat(diff)
        s += R(
            "dl",
            R("dt", diff_name) + R("dd", R("pre", R("code", pformat(diff, indent=2)))),
        )
    return R("div", s)


def generate_report(kwd_path):
    in_k, in_d, in_both, def_diff, kwd, dmd = compare_keywords(kwd_path)
    body = ""

    body += R("h1", "Keywords in the keyword dictionary but NOT in the datamodel schemas")
    for k in sorted(in_k):
        body += R("details", R("summary", _keyword_to_str(k)) + _keyword_details(kwd, dmd, k))

    body += R("h1", "Keywords in the datamodel schemas but NOT in the keyword dictionary")
    for k in sorted(in_d):
        body += R("details", R("summary", _keyword_to_str(k)) + _keyword_details(kwd, dmd, k))

    body += R("h1", "Keywords in both with definition differences")
    for k in sorted(def_diff):
        body += R("details", R("summary", _keyword_to_str(k)) + _def_diff_details(def_diff[k]))

    return R("html", R("body", body))


if __name__ == '__main__':
    import sys

    kwd_path = sys.argv[1]
    output_path = "report.html"

    report = generate_report(kwd_path)
    with open(output_path, "w") as f:
        f.write(report)
